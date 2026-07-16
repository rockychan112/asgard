"""Persona = a structured, editable contract (not a free-text prompt).

Each fact carries a stable id (P-role, P-goal, ...) so the analyzer can cite
exactly which facts it used — that citation is the auditable trace.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Persona:
    slug: str
    label: str
    facts: dict[str, str]  # id -> statement, e.g. {"P-role": "OTA 设计负责人"}

    @classmethod
    def load(cls, path: str | Path) -> "Persona":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return cls(
            slug=data["slug"],
            label=data["label"],
            facts={str(k): str(v) for k, v in data["facts"].items()},
        )

    def facts_block(self) -> str:
        return "\n".join(f"{fid}: {text}" for fid, text in self.facts.items())

    def with_fact(self, fid: str, text: str) -> "Persona":
        """Copy with one fact replaced — the counterfactual perturbation."""
        return Persona(self.slug, self.label, {**self.facts, fid: text})

    def without_fact(self, fid: str) -> "Persona":
        """Copy with one fact removed — the trace-validity ablation."""
        return Persona(self.slug, self.label, {k: v for k, v in self.facts.items() if k != fid})
