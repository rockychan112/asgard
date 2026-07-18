"""Feed layer: feeds.yaml -> deduped, newest-first candidate items.

Parsing is stdlib-only on purpose — tolerant localname matching over RSS 2.0 /
Atom covers real-world feeds well enough for a daily brief, and keeps
`pip install` dependency-free. One dead feed never kills the batch: collect()
returns per-feed failure notes alongside whatever it did get.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree

import yaml


@dataclass
class Feed:
    name: str
    url: str


@dataclass
class FeedConfig:
    feeds: list[Feed]
    max_items_per_day: int = 20

    @classmethod
    def load(cls, path: str | Path) -> "FeedConfig":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        feeds = [
            Feed(name=str(f.get("name") or f["url"]), url=str(f["url"]))
            for f in data.get("feeds", [])
        ]
        return cls(feeds=feeds, max_items_per_day=int(data.get("max_items_per_day", 20)))


@dataclass
class Item:
    title: str
    link: str
    summary: str
    date: datetime | None
    source: str


def _strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", html.unescape(s or ""))
    return re.sub(r"\s+", " ", s).strip()


def _parse_date(s: str) -> datetime | None:
    s = re.sub(r"\s+", " ", (s or "").strip())
    # near-ISO variants in the wild (36kr etc.): "2026-07-18 09:05:45  +0800"
    iso = re.sub(r" ?([+-]\d{2}):?(\d{2})$", r"\1:\2", s)
    for parse, text in ((parsedate_to_datetime, s), (datetime.fromisoformat, iso)):
        try:
            dt = parse(text)
        except Exception:
            continue
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return None


def parse_feed(raw: bytes, source: str) -> list[Item]:
    root = ElementTree.fromstring(raw)
    items: list[Item] = []
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1].lower() not in ("item", "entry"):
            continue
        title = link = summary = date_s = ""
        for child in node:
            tag = child.tag.rsplit("}", 1)[-1].lower()
            text = "".join(child.itertext()).strip()
            if tag == "title":
                title = text
            elif tag == "link":
                # Atom carries the URL in href and may list several rels;
                # prefer rel="alternate" (the article itself) over enclosures.
                href = text or child.get("href", "")
                if href and (not link or child.get("rel", "alternate") == "alternate"):
                    link = href
            elif tag in ("description", "summary", "content", "encoded"):
                summary = summary or text
            elif tag in ("pubdate", "published", "updated", "date"):
                date_s = date_s or text
        if title or link:
            items.append(Item(
                title=_strip_html(title), link=link.strip(),
                summary=_strip_html(summary)[:2000],
                date=_parse_date(date_s), source=source,
            ))
    return items


def fetch_feed(feed: Feed, timeout: int = 20) -> list[Item]:
    req = Request(feed.url, headers={"User-Agent": "asgard/0.0.1"})
    return parse_feed(urlopen(req, timeout=timeout).read(), source=feed.name)  # noqa: S310


def collect(cfg: FeedConfig) -> tuple[list[Item], list[str]]:
    """All feeds -> capped newest-first candidates + human-readable failure notes."""
    items, notes = [], []
    for feed in cfg.feeds:
        try:
            got = fetch_feed(feed)
        except Exception as e:  # noqa: BLE001 — any single-feed failure becomes a note
            notes.append(f"{feed.name}: 拉取失败（{type(e).__name__}: {e}）")
            continue
        if not got:
            notes.append(f"{feed.name}: 解析到 0 条（该源格式可能不受支持）")
        items.extend(got)

    seen: set[str] = set()
    unique: list[Item] = []
    for it in items:  # feeds overlap: same story via different feeds
        keys = {k for k in (it.link, re.sub(r"\s+", "", it.title.lower())) if k}
        if keys & seen:
            continue
        seen |= keys
        unique.append(it)

    epoch = datetime.min.replace(tzinfo=timezone.utc)
    unique.sort(key=lambda it: it.date or epoch, reverse=True)
    return unique[: cfg.max_items_per_day], notes
