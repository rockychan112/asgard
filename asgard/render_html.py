"""Standalone HTML rendering of a daily brief — same content as the Markdown,
one self-contained file (inline CSS, no external resources), light/dark aware.
"""
from __future__ import annotations

import html as _html
import re

_CSS = """
:root {
  color-scheme: light dark;
  --bg: #fbfbfd; --panel: #ffffff; --panel-2: #f5f6f9;
  --line: #e7e9f0; --line-soft: #eef0f5;
  --fg: #1b2030; --muted: #56607a; --faint: #8b93a8;
  --accent: #6d5bd0; --accent-soft: rgba(109,91,208,.10);
  --shadow: 0 1px 2px rgba(20,24,40,.04), 0 8px 24px -18px rgba(20,24,40,.22);
  --mono: ui-monospace, "SF Mono", "JetBrains Mono", Menlo, monospace;
  --body: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0a0c12; --panel: #12151e; --panel-2: #0e111a;
    --line: #242b3a; --line-soft: #1b2130;
    --fg: #e9edf6; --muted: #9aa3b7; --faint: #626b80;
    --accent: #a596f2; --accent-soft: rgba(154,134,240,.12);
    --shadow: 0 1px 0 rgba(255,255,255,.02), 0 18px 40px -26px rgba(0,0,0,.7);
  }
}
* { box-sizing: border-box; }
body {
  margin: 0 auto; padding: 3.2rem 1.4rem 5rem; max-width: 44rem;
  font-family: var(--body); font-size: 1.02rem; line-height: 1.78;
  color: var(--fg); background:
    radial-gradient(1100px 480px at 50% -8%, var(--accent-soft), transparent 60%),
    var(--bg);
  -webkit-font-smoothing: antialiased;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ---- masthead ---- */
.mast { margin-bottom: 2.6rem; text-align: center; }
.brand {
  font-family: var(--mono); font-size: .72rem; letter-spacing: .18em; text-transform: uppercase;
  color: var(--faint); display: inline-flex; align-items: center; gap: .5rem;
}
.brand .glyph { color: var(--accent); font-size: .9rem; }
.prism { display: block; width: min(320px, 78%); height: auto; margin: .5rem auto .1rem; }
.prism .edge { stroke: var(--faint); stroke-width: 1.1; fill: none; opacity: .8; }
.prism .face { fill: var(--accent-soft); stroke: var(--faint); stroke-width: 1; opacity: .9; }
.prism .beam { fill: var(--faint); opacity: .5; }
h1 { font-size: 1.7rem; line-height: 1.2; letter-spacing: -.02em; margin: .35rem 0 1.2rem; font-weight: 700; }
.stats { display: flex; gap: .5rem; flex-wrap: wrap; justify-content: center; }
.stat {
  font-family: var(--mono); font-size: .74rem; color: var(--muted);
  border: 1px solid var(--line); border-radius: 999px; padding: .28rem .7rem;
  background: var(--panel);
}
.stat b { color: var(--fg); font-weight: 600; }
.stat.hit { border-color: color-mix(in srgb, var(--accent) 45%, transparent); color: var(--accent); }
.stat.hit b { color: var(--accent); }

/* ---- briefed cards ---- */
article {
  position: relative; margin: 1.15rem 0; padding: 1.5rem 1.5rem 1.6rem;
  background: var(--panel); border: 1px solid var(--line); border-radius: 15px;
  box-shadow: var(--shadow); overflow: hidden;
}
article::before {
  content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: var(--hue); box-shadow: 0 0 18px -2px var(--hue);
}
.chead { display: flex; gap: .9rem; align-items: flex-start; }
.num {
  font-family: var(--mono); font-size: 1.5rem; font-weight: 600; line-height: 1;
  color: var(--hue); opacity: .85; flex: none; margin-top: .1rem; letter-spacing: -.02em;
}
.chead h2 { font-size: 1.16rem; line-height: 1.45; letter-spacing: -.01em; margin: 0; font-weight: 650; }
.src { font-family: var(--mono); font-size: .72rem; color: var(--faint); margin-top: .45rem; }
.src a { color: var(--faint); text-decoration: underline; text-underline-offset: 2px; }
.src a:hover { color: var(--accent); }

.eyebrow {
  font-family: var(--mono); font-size: .64rem; letter-spacing: .13em; text-transform: uppercase;
  color: var(--faint); display: block; margin-bottom: .3rem;
}
.facts {
  margin-top: 1.3rem; padding: .85rem 1rem; border-radius: 10px;
  background: var(--panel-2); border: 1px solid var(--line-soft);
  font-size: .93rem; line-height: 1.7; color: var(--muted);
}
.foryou { margin-top: 1.25rem; }
.foryou p { margin: 0; }
.actions { margin-top: 1.3rem; }
.actions ul { list-style: none; margin: 0; padding: 0; display: grid; gap: .55rem; }
.actions li { position: relative; padding-left: 1.3rem; line-height: 1.65; }
.actions li::before { content: "→"; position: absolute; left: 0; top: 0; color: var(--hue); font-family: var(--mono); }
.chips { margin-top: 1.4rem; padding-top: 1.1rem; border-top: 1px solid var(--line-soft); display: flex; flex-wrap: wrap; align-items: center; gap: .4rem; }
.chips .lbl { font-family: var(--mono); font-size: .64rem; letter-spacing: .1em; text-transform: uppercase; color: var(--faint); margin-right: .2rem; }
.chip {
  font-family: var(--mono); font-size: .7rem; color: var(--accent);
  border: 1px solid color-mix(in srgb, var(--accent) 40%, transparent);
  background: var(--accent-soft); border-radius: 6px; padding: .12rem .48rem;
}

/* ---- empty / all-skip ---- */
.empty {
  margin-top: 1rem; padding: 1.6rem 1.5rem; text-align: center;
  border: 1px dashed var(--line); border-radius: 14px; color: var(--muted); background: var(--panel);
}

/* ---- skip + issues (secondary) ---- */
.sec { margin-top: 2.6rem; }
.sec > h2 {
  font-family: var(--mono); font-size: .72rem; letter-spacing: .12em; text-transform: uppercase;
  color: var(--faint); font-weight: 600; margin: 0 0 .9rem; padding-bottom: .55rem; border-bottom: 1px solid var(--line);
}
.sec ul { list-style: none; margin: 0; padding: 0; display: grid; gap: .7rem; }
.skiplist li { font-size: .9rem; line-height: 1.6; color: var(--muted); padding-left: 1rem; position: relative; }
.skiplist li::before { content: ""; position: absolute; left: 0; top: .62em; width: 4px; height: 4px; border-radius: 50%; background: var(--faint); }
.skiplist li b { color: var(--fg); font-weight: 600; }
.errlist li { font-family: var(--mono); font-size: .78rem; line-height: 1.55; color: var(--faint); }

/* ---- footer ---- */
footer { margin-top: 3.2rem; text-align: center; font-family: var(--mono); font-size: .68rem; letter-spacing: .1em; color: var(--faint); }
footer .glyph { color: var(--accent); }
"""

# Decorative accent rotation for card hairlines/numbers — no contrast requirement.
_HUES = ("#e6b450", "#43c6b8", "#9a86f0", "#e08bb0")

# The masthead prism: one beam of news enters, splits into the four accent
# beams that then rotate through the cards below — the fact/interpretation
# split made visual, once, not repeated per card. Fills adapt to theme via CSS
# vars; ray gradients (soft, no blend mode) read on both light and dark.
_PRISM = """<svg class="prism" viewBox="0 0 360 116" role="presentation" aria-hidden="true">
  <defs>
    <linearGradient id="r0" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e6b450" stop-opacity=".55"/><stop offset="1" stop-color="#e6b450" stop-opacity="0"/></linearGradient>
    <linearGradient id="r1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#43c6b8" stop-opacity=".55"/><stop offset="1" stop-color="#43c6b8" stop-opacity="0"/></linearGradient>
    <linearGradient id="r2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9a86f0" stop-opacity=".55"/><stop offset="1" stop-color="#9a86f0" stop-opacity="0"/></linearGradient>
    <linearGradient id="r3" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e08bb0" stop-opacity=".55"/><stop offset="1" stop-color="#e08bb0" stop-opacity="0"/></linearGradient>
  </defs>
  <rect class="beam" x="178" y="0" width="4" height="46"/>
  <polygon class="ray" fill="url(#r0)" points="178,84 182,84 92,116 58,116"/>
  <polygon class="ray" fill="url(#r1)" points="178,84 182,84 168,116 132,116"/>
  <polygon class="ray" fill="url(#r2)" points="178,84 182,84 238,116 202,116"/>
  <polygon class="ray" fill="url(#r3)" points="178,84 182,84 312,116 276,116"/>
  <polygon class="face" points="180,44 202,84 158,84"/>
  <line class="edge" x1="180" y1="50" x2="192" y2="80"/>
</svg>"""


def _e(s: str) -> str:
    return _html.escape(s or "")


def render_brief_html(day: str, results, feed_notes: list[str], is_briefed, lang: str = "zh") -> str:
    from .i18n import t

    s = t(lang)
    briefed = [r for r in results if is_briefed(r)]
    errored = [r for r in results if r.error]
    skipped = [r for r in results if not r.error and not is_briefed(r)]

    stat_hit = f'<span class="stat hit"><b>{len(briefed)}</b> {s["st_briefed"]}</span>'
    stat_row = (
        f'<span class="stat"><b>{len(results)}</b> {s["st_candidates"]}</span>'
        + stat_hit
        + f'<span class="stat"><b>{len(skipped)}</b> {s["st_skipped"]}</span>'
    )

    parts = [
        "<!doctype html>", f'<html lang="{lang}">', "<head>",
        '<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{s['title']} · {_e(day)}</title>", f"<style>{_CSS}</style>", "</head>", "<body>",
        '<div class="mast">',
        f'<div class="brand"><span class="glyph">◭</span> {s["title"]}</div>',
        _PRISM,
        f"<h1>{_e(day)}</h1>",
        f'<div class="stats">{stat_row}</div>',
        "</div>",
    ]

    if not results:
        parts.append(f'<div class="empty">{_e(s["no_news"])}</div>')
    elif not briefed:
        parts.append(f'<div class="empty">{_e(s["all_skip"].format(n=len(results)))}</div>')

    for i, r in enumerate(briefed, 1):
        card, event = r.card, r.event
        hue = _HUES[(i - 1) % len(_HUES)]
        facts = s["sep"].join(re.sub(r"^S-\d+\s*", "", f).rstrip("。.;；") for f in event.facts[:4])
        pids = [f for f in card.used_facts if f.upper().startswith("P-")]
        link = f' · <a href="{_e(r.item.link)}">{s["original"]}</a>' if r.item.link else ""
        parts += [
            f'<article style="--hue:{hue}">',
            '<div class="chead">',
            f'<span class="num">{i:02d}</span>',
            f'<div><h2>{_e(event.headline)}</h2><div class="src">{_e(r.item.source)}{link}</div></div>',
            "</div>",
        ]
        if facts:
            parts.append(f'<div class="facts"><span class="eyebrow">{s["facts"]}</span>{_e(facts)}{s["stop"]}</div>')
        parts.append(
            f'<div class="foryou"><span class="eyebrow">{s["for_you"]}</span>'
            f"<p>{_e(card.stakes or card.why_you)}</p></div>"
        )
        if card.actions:
            parts.append(f'<div class="actions"><span class="eyebrow">{s["this_week"]}</span><ul>'
                         + "".join(f"<li>{_e(a)}</li>" for a in card.actions) + "</ul></div>")
        if pids:
            chips = "".join(f'<span class="chip">{_e(p)}</span>' for p in pids)
            parts.append(f'<div class="chips"><span class="lbl">{s["cite"]}</span>{chips}</div>')
        parts.append("</article>")

    if skipped:
        parts.append(f'<section class="sec skiplist"><h2>{_e(s["skipped_h"].format(n=len(skipped)))}</h2><ul>')
        for r in skipped:
            reason = (r.card.skip_reason if r.card else "") or s["fallback_skip"]
            parts.append(f"<li><b>{_e(r.item.title)}</b> — {_e(reason)}</li>")
        parts.append("</ul></section>")

    if errored or feed_notes:
        parts.append(f'<section class="sec errlist"><h2>{s["issues_h"]}</h2><ul>')
        parts += [f"<li>{_e(n)}</li>" for n in feed_notes]
        parts += [f"<li>{_e(r.item.title)} — {_e(s['process_fail'].format(err=r.error))}</li>" for r in errored]
        parts.append("</ul></section>")

    parts.append(f'<footer><span class="glyph">◭</span> {s["title"]} · {s["foot"]}</footer>')
    parts += ["</body>", "</html>"]
    return "\n".join(p for p in parts if p)
