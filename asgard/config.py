"""One config file is the single source of truth for "what to produce, when".

Search order (first match wins): --config flag -> ./.asgard/config.yaml ->
~/.asgard/config.yaml -> built-in defaults. Secrets never live here — the
model endpoint stays in env vars (OPENAI_* / ASGARD_MODEL).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

SEARCH_BASES = (Path(".asgard"), Path.home() / ".asgard")

FORMATS = ("md", "html")
CADENCES = ("daily", "weekly")
WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


@dataclass
class Output:
    formats: list[str] = field(default_factory=lambda: ["md"])
    dir: str = ""


@dataclass
class Schedule:
    cadence: str = "daily"
    time: str = "08:00"
    weekday: str = "mon"


@dataclass
class Config:
    lang: str = "zh"  # brief language — the user's explicit upfront choice
    profile: str = ""
    feeds: str = ""
    output: Output = field(default_factory=Output)
    schedule: Schedule = field(default_factory=Schedule)
    source: Path | None = None  # which file this came from (None = defaults)

    @classmethod
    def load(cls, explicit: str | None = None) -> "Config":
        path: Path | None = None
        if explicit:
            path = Path(explicit).expanduser()
            if not path.exists():
                raise FileNotFoundError(f"配置文件不存在：{path}")
        else:
            for base in SEARCH_BASES:
                p = base / "config.yaml"
                if p.exists():
                    path = p
                    break
        if path is None:
            return cls()

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        out, sch = data.get("output") or {}, data.get("schedule") or {}
        return cls(
            lang=str(data.get("lang") or "zh").lower(),
            profile=str(data.get("profile") or ""),
            feeds=str(data.get("feeds") or ""),
            output=Output(
                formats=[str(f).lower() for f in (out.get("formats") or ["md"])],
                dir=str(out.get("dir") or ""),
            ),
            schedule=Schedule(
                cadence=str(sch.get("cadence") or "daily").lower(),
                time=str(sch.get("time") or "08:00"),
                weekday=str(sch.get("weekday") or "mon").lower(),
            ),
            source=path,
        )

    def problems(self) -> list[str]:
        out = []
        if self.lang not in ("zh", "en"):
            out.append(f"lang 应为 zh 或 en，现在是 {self.lang!r}")
        for f in self.output.formats:
            if f not in FORMATS:
                out.append(f"output.formats 含未知格式 {f!r}（可选：{'/'.join(FORMATS)}）")
        if not self.output.formats:
            out.append("output.formats 为空——至少留一种格式")
        if self.schedule.cadence not in CADENCES:
            out.append(f"schedule.cadence 应为 {'/'.join(CADENCES)}，现在是 {self.schedule.cadence!r}")
        if not re.fullmatch(r"([01]?\d|2[0-3]):[0-5]\d", self.schedule.time):
            out.append(f"schedule.time 应为 HH:MM，现在是 {self.schedule.time!r}")
        if self.schedule.cadence == "weekly" and self.schedule.weekday not in WEEKDAYS:
            out.append(f"schedule.weekday 应为 {'/'.join(WEEKDAYS)}，现在是 {self.schedule.weekday!r}")
        return out
