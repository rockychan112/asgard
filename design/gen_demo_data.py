"""Regenerate design/demo_data.json — the demo news pool.

Runs the REAL pipeline (extract_event + refract, no hand-editing) for every
news fixture below × the four demo identities, and dumps the pool the demo
page renders. Needs the same env as `asgard brief` (OPENAI_* / ASGARD_MODEL).

    python design/gen_demo_data.py            # all news
    python design/gen_demo_data.py hormuz xhs # regenerate just these ids
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from asgard.analyzer import extract_event, refract  # noqa: E402
from asgard.persona import Persona  # noqa: E402
from asgard.sources import load  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "design" / "demo_data.json"

NEWS = ["hormuz", "redsea", "boeing", "oilcrash", "tariff", "ratecut",
        "fx", "camera", "xhs", "ai-render", "airesearch", "graham"]
IDENTITIES = ["travel-lead", "ecommerce-seller", "interior-designer", "wedding-photographer"]


def build_item(news: str) -> dict:
    event = extract_event(load(f"fixture:{news}"))
    personas = [Persona.load(ROOT / "personas" / f"{slug}.yaml") for slug in IDENTITIES]
    with ThreadPoolExecutor(max_workers=4) as ex:
        cards = list(ex.map(lambda p: asdict(refract(event, p)), personas))
    for slug, card in zip(IDENTITIES, cards):
        card["slug"] = slug
        card["label"] = card.pop("persona")  # the page renders `label`
    print(f"[demo] {news}: " + " ".join(f"{c['slug']}={c['relevance']}" for c in cards), file=sys.stderr)
    return {"id": news, "headline": event.headline, "date": event.date,
            "source": event.source, "facts": event.facts, "cards": cards}


def main() -> None:
    only = set(sys.argv[1:])
    pool: dict[str, dict] = {}
    if OUT.exists():  # partial regeneration keeps the untouched items
        pool = {i["id"]: i for i in json.loads(OUT.read_text(encoding="utf-8")).get("items", [])}
    todo = [n for n in NEWS if not only or n in only]
    with ThreadPoolExecutor(max_workers=3) as ex:
        for item in ex.map(build_item, todo):
            pool[item["id"]] = item
    items = [pool[n] for n in NEWS if n in pool]
    OUT.write_text(json.dumps({"items": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[demo] wrote {len(items)} items -> {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
