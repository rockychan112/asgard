"""`asgard daily`: feeds -> per-item refraction -> one briefs/YYYY-MM-DD.md.

Failure contract: one dead feed never kills the batch; a day where every feed
fails, or every item errors, still writes an honest brief saying so (exit code
2 in that case so cron/launchd can flag it). An all-SKIP day is the product
working, not failing.
"""
from __future__ import annotations

import re
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .analyzer import Event, Refraction, extract_event, refract
from .config import SEARCH_BASES, Config
from .feeds import FeedConfig, Item, collect
from .i18n import t
from .persona import Persona
from .render_html import render_brief_html
from .sources import Article, from_url


def resolve_config(explicit: str | None, filename: str) -> Path | None:
    """First match wins: explicit path -> ./.asgard/<name> -> ~/.asgard/<name>."""
    if explicit:
        p = Path(explicit).expanduser()
        return p if p.exists() else None
    for base in SEARCH_BASES:
        p = base / filename
        if p.exists():
            return p
    return None


def _article(item: Item) -> Article:
    text = item.summary
    if len(text) < 200 and item.link:  # headline-only feed: try the article itself
        try:
            fetched = from_url(item.link)
            if len(fetched.text) > len(text):
                text = fetched.text
        except Exception:  # noqa: BLE001 — a thin summary still supports a relevance call
            pass
    return Article(
        title=item.title, text=text or item.title, source=item.source,
        date=item.date.date().isoformat() if item.date else "", url=item.link,
    )


@dataclass
class _Result:
    item: Item
    event: Event | None = None
    card: Refraction | None = None
    error: str = ""


def _process(item: Item, persona: Persona, lang: str) -> _Result:
    try:
        event = extract_event(_article(item), lang=lang)
        return _Result(item, event, refract(event, persona, lang=lang))
    except Exception as e:  # noqa: BLE001 — one bad item must not kill the day
        return _Result(item, error=f"{type(e).__name__}: {e}")


def _facts_prose(event: Event, lang: str = "zh") -> str:
    s = t(lang)
    cleaned = [re.sub(r"^S-\d+\s*", "", f).rstrip("。.;；") for f in event.facts[:4]]
    return s["sep"].join(c for c in cleaned if c) + s["stop"] if any(cleaned) else "—"


def _is_briefed(r: _Result) -> bool:
    return bool(r.card and r.card.relevance in ("high", "medium"))


def render_brief(
    day: str, profile_path: str, results: list[_Result], feed_notes: list[str],
    lang: str = "zh",
) -> str:
    s = t(lang)
    briefed = [r for r in results if _is_briefed(r)]
    errored = [r for r in results if r.error]
    skipped = [r for r in results if not r.error and not _is_briefed(r)]

    lines = [
        "---",
        f"date: {day}",
        "engine: cli",
        f"lang: {lang}",
        f"profile: {profile_path}",
        f"candidates: {len(results)}",
        f"briefed: {len(briefed)}",
        f"skipped: {len(skipped)}",
        "---",
        "",
        f"# {s['title']} · {day}",
        "",
    ]

    if not results:
        lines += [s["no_news"], ""]
    elif not briefed:
        lines += [s["all_skip"].format(n=len(results)), ""]

    for i, r in enumerate(briefed, 1):
        card, event = r.card, r.event
        assert card and event
        # cite-or-drop applies to profile lines only: an S- id is a news fact,
        # not a profile citation, and must not masquerade as one
        cite = " · ".join(f for f in card.used_facts if f.upper().startswith("P-")) or "—"
        lines += [
            f"## {i}. {event.headline}  ·  {r.item.source}",
            "",
            f"**{s['facts']}**{s['colon']}{_facts_prose(event, lang)}",
            "",
            f"**{s['for_you']}**{s['colon']}{card.stakes or card.why_you}{s['pl']}{s['cite']} {cite}{s['pr']}",
            "",
            f"**{s['this_week']}**{s['colon']}",
            *[f"- {a}" for a in card.actions],
        ]
        if r.item.link:
            lines += ["", f"<sub>[{s['original']}]({r.item.link})</sub>"]
        lines += [""]

    if skipped:
        lines += [f"## {s['skipped_h'].format(n=len(skipped))}", ""]
        for r in skipped:
            reason = (r.card.skip_reason if r.card else "") or s["fallback_skip"]
            lines += [f"- {r.item.title} — {reason}"]
        lines += [""]

    if errored or feed_notes:
        lines += [f"## {s['issues_h']}", ""]
        lines += [f"- {note}" for note in feed_notes]
        lines += [f"- {r.item.title} — {s['process_fail'].format(err=r.error)}" for r in errored]
        lines += [""]

    return "\n".join(lines)


def run(
    profile: str | None, feeds: str | None, out: str | None,
    max_items: int | None = None, workers: int = 4,
    config: str | None = None, formats: list[str] | None = None,
    lang: str | None = None,
) -> int:
    conf = Config.load(config)
    if conf.source and conf.problems():
        sys.exit(f"{conf.source} 有问题：\n  - " + "\n  - ".join(conf.problems()))
    formats = formats or conf.output.formats
    lang = lang or conf.lang
    s = t(lang)

    profile_path = resolve_config(profile or conf.profile, "profile.yaml")
    if not profile_path:
        sys.exit(
            "找不到你的资料文件。放一份到 ~/.asgard/profile.yaml（或用 --profile 指定），"
            "样例见 examples/profile.sample.yaml"
        )
    feeds_path = resolve_config(feeds or conf.feeds, "feeds.yaml")
    if not feeds_path:
        sys.exit(
            "找不到信源列表。放一份到 ~/.asgard/feeds.yaml（或用 --feeds 指定），"
            "样例见 examples/feeds.example.yaml"
        )

    persona = Persona.load(profile_path)
    cfg = FeedConfig.load(feeds_path)
    if max_items:
        cfg.max_items_per_day = max_items

    print(f"[asgard] {s['p_fetch'].format(n=len(cfg.feeds))}", file=sys.stderr)
    items, feed_notes = collect(cfg, lang=lang)
    for note in feed_notes:
        print(f"[asgard] ⚠ {note}", file=sys.stderr)
    print(f"[asgard] {s['p_refract'].format(n=len(items))}", file=sys.stderr)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda it: _process(it, persona, lang), items))

    day = date.today().isoformat()
    if out:
        out_path = Path(out).expanduser()
    elif conf.output.dir:
        out_path = Path(conf.output.dir).expanduser() / f"{day}.md"
    else:
        base = Path("briefs") if Path("briefs").is_dir() else Path.home() / ".asgard" / "briefs"
        out_path = base / f"{day}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    written = []
    if "md" in formats:
        out_path.write_text(render_brief(day, str(profile_path), results, feed_notes, lang=lang), encoding="utf-8")
        written.append(out_path)
    if "html" in formats:
        html_path = out_path.with_suffix(".html")
        html_path.write_text(render_brief_html(day, results, feed_notes, _is_briefed, lang=lang), encoding="utf-8")
        written.append(html_path)

    briefed = sum(1 for r in results if _is_briefed(r))
    ok = sum(1 for r in results if not r.error)
    print("[asgard] " + s["p_written"].format(
        paths=" + ".join(map(str, written)), candidates=len(results), briefed=briefed, skipped=ok - briefed))
    return 2 if not ok else 0  # nothing processed at all -> flag for cron, files still written
