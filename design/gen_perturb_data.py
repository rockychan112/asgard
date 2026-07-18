"""Extend design/demo_data.json with the perturbation replay matrix.

For every fired card, re-run the REAL pipeline once per cited profile line
(persona minus that one fact) against the item's already-frozen fact layer.
The demo page replays these outputs when a visitor toggles a line off — so
every change on the page is a real engine run, baked offline, never invented
client-side. Needs the same env as `asgard brief` (OPENAI_* / ASGARD_MODEL).

    python design/gen_perturb_data.py            # all items
    python design/gen_perturb_data.py hormuz xhs # just these ids
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from asgard.analyzer import Event, refract  # noqa: E402
from asgard.persona import Persona  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "design" / "demo_data.json"


def base_pids(card: dict, persona: Persona) -> list[str]:
    """Unique cited P-ids that actually exist in the persona ("P-cares:细化" -> P-cares)."""
    out, seen = [], set()
    for f in card.get("used_facts") or []:
        pid = str(f).split(":")[0].strip()
        if pid.startswith("P-") and pid in persona.facts and pid not in seen:
            seen.add(pid)
            out.append(pid)
    return out


def main() -> None:
    only = set(sys.argv[1:])
    doc = json.loads(DATA.read_text(encoding="utf-8"))
    personas = {p.slug: p for p in (Persona.load(f) for f in sorted((ROOT / "personas").glob("*.yaml")))}

    jobs = []  # (item, card, pid, persona)
    for item in doc["items"]:
        if only and item["id"] not in only:
            continue
        event = Event(headline=item["headline"], facts=item["facts"],
                      date=item.get("date", ""), source=item.get("source", ""))
        for card in item["cards"]:
            persona = personas[card["slug"]]
            if card["relevance"] == "skip":
                card["perturb"] = {}
                continue
            for pid in base_pids(card, persona):
                jobs.append((item, card, pid, event, persona))

    print(f"[perturb] {len(jobs)} ablation runs…", file=sys.stderr)

    def run(job):
        item, card, pid, event, persona = job
        r = asdict(refract(event, persona.without_fact(pid)))
        r.pop("persona", None)
        print(f"[perturb] {item['id']} · {card['slug']} − {pid} → {r['relevance']}", file=sys.stderr)
        return card, pid, r

    with ThreadPoolExecutor(max_workers=6) as ex:
        for card, pid, r in ex.map(run, jobs):
            card.setdefault("perturb", {})[pid] = r

    # the page needs each identity's full fact list to render the toggle panel
    doc["identities"] = {
        slug: {"label": p.label, "facts": p.facts} for slug, p in personas.items()
    }
    DATA.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[perturb] wrote {DATA}", file=sys.stderr)


if __name__ == "__main__":
    main()
