"""Standalone HTML rendering of a daily brief — same content as the Markdown,
one self-contained file (inline CSS, no external resources), light/dark aware.
"""
from __future__ import annotations

import html as _html
import re

_CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body {
  margin: 0 auto; padding: 3rem 1.4rem 4rem; max-width: 46rem;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
  font-size: 1.02rem; line-height: 1.75;
  color: #24292f; background: #ffffff;
}
header { margin-bottom: 2.2rem; }
h1 { font-size: 1.5rem; margin: 0 0 .4rem; letter-spacing: -.01em; }
.meta { color: #6e7781; font-size: .85rem; font-family: ui-monospace, "SF Mono", Menlo, monospace; }
article { margin: 2.2rem 0; padding-bottom: 2rem; border-bottom: 1px solid #d8dee4; }
article h2 { font-size: 1.15rem; line-height: 1.5; margin: 0 0 .2rem; }
.src { color: #6e7781; font-size: .82rem; margin-bottom: 1rem; }
.label { font-weight: 700; margin-top: 1rem; }
ul { margin: .4rem 0 0; padding-left: 1.3rem; }
li { margin: .35rem 0; }
.cite { color: #6e7781; font-size: .85rem; margin-top: .8rem; }
.cite b { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-weight: 600; }
a { color: #0969da; }
.empty { padding: 1.2rem 1.3rem; border: 1px solid #d8dee4; border-radius: 10px; color: #57606a; }
.skiplist h2, .errlist h2 { font-size: 1.05rem; margin: 2.4rem 0 .6rem; }
.skiplist li, .errlist li { color: #57606a; font-size: .95rem; }
.skiplist li b { color: #24292f; font-weight: 600; }
@media (prefers-color-scheme: dark) {
  body { color: #e6edf3; background: #0d1117; }
  .meta, .src, .cite, .skiplist li, .errlist li { color: #8d96a0; }
  .skiplist li b { color: #e6edf3; }
  article, .empty { border-color: #30363d; }
  .empty { color: #8d96a0; }
  a { color: #58a6ff; }
}
"""


def _e(s: str) -> str:
    return _html.escape(s or "")


def render_brief_html(day: str, results, feed_notes: list[str], is_briefed, lang: str = "zh") -> str:
    from .i18n import t

    s = t(lang)
    briefed = [r for r in results if is_briefed(r)]
    errored = [r for r in results if r.error]
    skipped = [r for r in results if not r.error and not is_briefed(r)]
    meta = s["meta"].format(candidates=len(results), briefed=len(briefed), skipped=len(skipped))

    parts = [
        "<!doctype html>", f'<html lang="{lang}">', "<head>",
        '<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{s['title']} · {_e(day)}</title>", f"<style>{_CSS}</style>", "</head>", "<body>",
        "<header>",
        f"<h1>{s['title']} · {_e(day)}</h1>",
        f'<div class="meta">{meta} · engine: cli</div>',
        "</header>",
    ]

    if not results:
        parts.append(f'<div class="empty">{_e(s["no_news"])}</div>')
    elif not briefed:
        parts.append(f'<div class="empty">{_e(s["all_skip"].format(n=len(results)))}</div>')

    for i, r in enumerate(briefed, 1):
        card, event = r.card, r.event
        facts = s["sep"].join(re.sub(r"^S-\d+\s*", "", f).rstrip("。.;；") for f in event.facts[:4])
        cite = " · ".join(f for f in card.used_facts if f.upper().startswith("P-")) or "—"
        parts += [
            "<article>",
            f"<h2>{i}. {_e(event.headline)}</h2>",
            f'<div class="src">{_e(r.item.source)}'
            + (f' · <a href="{_e(r.item.link)}">{s["original"]}</a>' if r.item.link else "") + "</div>",
            f'<div class="label">{s["facts"]}</div><div>{_e(facts)}{s["stop"]}</div>' if facts else "",
            f'<div class="label">{s["for_you"]}</div><div>{_e(card.stakes or card.why_you)}</div>',
        ]
        if card.actions:
            parts.append(f'<div class="label">{s["this_week"]}</div><ul>'
                         + "".join(f"<li>{_e(a)}</li>" for a in card.actions) + "</ul>")
        parts += [f'<div class="cite">{s["cite"]} <b>{_e(cite)}</b></div>', "</article>"]

    if skipped:
        parts.append(f'<section class="skiplist"><h2>{_e(s["skipped_h"].format(n=len(skipped)))}</h2><ul>')
        for r in skipped:
            reason = (r.card.skip_reason if r.card else "") or s["fallback_skip"]
            parts.append(f"<li><b>{_e(r.item.title)}</b> — {_e(reason)}</li>")
        parts.append("</ul></section>")

    if errored or feed_notes:
        parts.append(f'<section class="errlist"><h2>{s["issues_h"]}</h2><ul>')
        parts += [f"<li>{_e(n)}</li>" for n in feed_notes]
        parts += [f"<li>{_e(r.item.title)} — {_e(s['process_fail'].format(err=r.error))}</li>" for r in errored]
        parts.append("</ul></section>")

    parts += ["</body>", "</html>"]
    return "\n".join(p for p in parts if p)
