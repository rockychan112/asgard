"""`asgard doctor` — the machine-checkable completion bar for setup.

An agent (or a human) is configured when every check here is green; nothing
else counts as "done". `--json` is for agents, `--ping` spends one tiny model
call to prove the endpoint round-trips. Secret values are never printed.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from .config import Config
from .feeds import FeedConfig
from .persona import Persona

ENV_VARS = ("OPENAI_BASE_URL", "OPENAI_API_KEY", "ASGARD_MODEL")


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def _resolve(explicit: str, filename: str) -> Path | None:
    from .daily import resolve_config

    return resolve_config(explicit or None, filename)


def run_doctor(config_path: str | None = None, ping: bool = False, as_json: bool = False) -> int:
    checks: list[Check] = []

    try:
        cfg = Config.load(config_path)
    except FileNotFoundError as e:
        cfg = Config()
        checks.append(Check("config", False, str(e)))
    else:
        problems = cfg.problems()
        where = str(cfg.source) if cfg.source else "未找到 config 文件，用默认值（样例见 examples/config.sample.yaml）"
        checks.append(Check("config", not problems, "；".join(problems) or where))

    profile = _resolve(cfg.profile, "profile.yaml")
    if not profile:
        checks.append(Check("profile", False, "找不到资料文件（.asgard/profile.yaml 或 ~/.asgard/profile.yaml）"))
    else:
        try:
            p = Persona.load(profile)
            n = sum(1 for k in p.facts if k.startswith("P-"))
            checks.append(Check("profile", n >= 3, f"{profile} · {n} 条 P- 事实" + ("" if n >= 3 else "（太少，判断没得引用）")))
        except Exception as e:  # noqa: BLE001
            checks.append(Check("profile", False, f"{profile} 解析失败：{e}"))

    feeds = _resolve(cfg.feeds, "feeds.yaml")
    if not feeds:
        checks.append(Check("feeds", False, "找不到信源列表（样例见 examples/feeds.example.yaml）"))
    else:
        try:
            fc = FeedConfig.load(feeds)
            checks.append(Check("feeds", bool(fc.feeds), f"{feeds} · {len(fc.feeds)} 个源"))
        except Exception as e:  # noqa: BLE001
            checks.append(Check("feeds", False, f"{feeds} 解析失败：{e}"))

    missing = [v for v in ENV_VARS if not os.environ.get(v)]
    checks.append(Check("env", not missing,
                        "三个变量都在（值不显示）" if not missing else f"缺 {' '.join(missing)}（放 ~/.asgard/env 并 source）"))

    out_dir = Path(cfg.output.dir).expanduser() if cfg.output.dir else (
        Path("briefs") if Path("briefs").is_dir() else Path.home() / ".asgard" / "briefs")
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        probe = out_dir / ".doctor-probe"
        probe.write_text("", encoding="utf-8")
        probe.unlink()
        checks.append(Check("output", True, str(out_dir)))
    except Exception as e:  # noqa: BLE001
        checks.append(Check("output", False, f"{out_dir} 不可写：{e}"))

    if ping:
        if missing:
            checks.append(Check("ping", False, "env 不全，跳过"))
        else:
            try:
                from .llm import openai_chat

                raw = openai_chat(temperature=0, json=False)("只回一个词：OK", "ping")
                checks.append(Check("ping", bool(raw.strip()), "端点有响应" if raw.strip() else "端点返回空响应"))
            except Exception as e:  # noqa: BLE001
                checks.append(Check("ping", False, f"端点调用失败：{e}"))

    all_ok = all(c.ok for c in checks)
    if as_json:
        print(json.dumps({"ok": all_ok, "checks": [c.__dict__ for c in checks]}, ensure_ascii=False, indent=2))
    else:
        for c in checks:
            print(f"  {'✓' if c.ok else '✗'} {c.name:<8} {c.detail}")
        print(f"\n{'全部通过——配置完成。' if all_ok else '有未通过项，逐条修完再跑一次。'}")
    return 0 if all_ok else 1
