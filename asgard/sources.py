"""Input adapters: an Article is the raw material, before any persona touches it."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@dataclass
class Article:
    title: str
    text: str
    source: str
    date: str = ""
    url: str = ""


def from_fixture(name: str) -> Article:
    data = json.loads((FIXTURE_DIR / f"{name}.json").read_text(encoding="utf-8"))
    return Article(**data)


def from_url(url: str) -> Article:
    """Best-effort fetch + readable-text extraction (optional `fetch` extra)."""
    req = Request(url, headers={"User-Agent": "asgard/0.0.1"})
    html = urlopen(req, timeout=20).read().decode("utf-8", "ignore")  # noqa: S310
    try:
        from readability import Document  # type: ignore

        doc = Document(html)
        title, body_html = doc.title(), doc.summary()
    except Exception:
        title, body_html = "", html
    text = re.sub(r"<[^>]+>", " ", body_html)
    text = re.sub(r"\s+", " ", text).strip()[:6000]
    host = re.sub(r"^https?://([^/]+)/?.*$", r"\1", url)
    return Article(title=title, text=text, source=host, url=url)


def load(target: str) -> Article:
    if target.startswith("fixture:"):
        return from_fixture(target.split(":", 1)[1])
    return from_url(target)
