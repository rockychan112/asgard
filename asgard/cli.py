from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analyzer import extract_event, refract
from .persona import Persona
from .render import render_card, render_event
from .sources import load

PERSONA_DIR = Path(__file__).resolve().parent.parent / "personas"


def _personas(slug: str | None) -> list[Persona]:
    if slug:
        # a slug of a built-in persona, or a path to the user's own profile file
        path = Path(slug).expanduser()
        if not (path.suffix in (".yaml", ".yml") and path.exists()):
            path = PERSONA_DIR / f"{slug}.yaml"
        if not path.exists():
            sys.exit(f"未知 persona：{slug}（不是文件路径，{PERSONA_DIR} 下也没有 {slug}.yaml）")
        return [Persona.load(path)]
    return [Persona.load(p) for p in sorted(PERSONA_DIR.glob("*.yaml"))]


def _cmd_brief(args: argparse.Namespace) -> None:
    import dataclasses
    import json

    article = load(args.target)
    event = extract_event(article)
    cards = [refract(event, persona) for persona in _personas(args.persona)]
    if args.json:  # machine-readable: the skill/orchestrator path (engine: cli)
        print(json.dumps(
            {"event": dataclasses.asdict(event), "cards": [dataclasses.asdict(c) for c in cards]},
            ensure_ascii=False, indent=2,
        ))
        return
    render_event(event)
    for card in cards:
        render_card(card)


def _cmd_daily(args: argparse.Namespace) -> None:
    from .daily import run

    sys.exit(run(args.profile, args.feeds, args.out, max_items=args.max_items))


def _cmd_eval(args: argparse.Namespace) -> None:
    from .eval import mock_chat, render, run_eval
    from .judge import LLMJudge, StubJudge
    from .llm import openai_chat

    if args.dry_run:
        chat, judge, mode = mock_chat, StubJudge(), "dry-run"
    else:
        # arms run at temperature=0 so any output change traces to the fact change,
        # not sampling. Judge is a different-source non-Claude model (GLM_* env),
        # kept blind to which arm it scores.
        chat = openai_chat(temperature=0, json=True)  # arms: OPENAI_*/REFRACTION_MODEL
        judge = LLMJudge(
            openai_chat(
                temperature=0, json=True,
                base_url_env="GLM_BASE_URL", key_env="GLM_API_KEY",
                model_env="GLM_MODEL", default_model="glm-4",
            )
        )
        mode = "arms=DeepSeek · judge=GLM"

    k = 1 if args.dry_run else args.k  # mock is deterministic; real arms need K-sample majority
    report = render(run_eval(chat, judge, mode=mode, k=k))
    print(report)
    if args.report:
        Path(args.report).write_text(report + "\n", encoding="utf-8")
        print(f"\n[写入 {args.report}]", file=sys.stderr)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        prog="asgard",
        description="你的私人情报官：洞察每一条资讯背后，只对『你』成立的利害关系与行动指引。",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("brief", help="把一条新闻按你的 persona 折射")
    b.add_argument("target", help="URL 或 fixture:NAME（如 fixture:hormuz）")
    b.add_argument("--persona", help="persona slug 或你自己的资料文件路径（默认：跑全部内置 persona 做对照）")
    b.add_argument("--json", action="store_true", help="输出机器可读 JSON（skill/编排器用，engine: cli）")
    b.set_defaults(func=_cmd_brief)

    d = sub.add_parser("daily", help="按你的信源列表拉当日新闻，逐条折射，落一份日报到 briefs/")
    d.add_argument("--profile", help="你的资料文件（默认依次找 ./asgard/profile.yaml、~/.asgard/profile.yaml）")
    d.add_argument("--feeds", help="信源列表（默认同上顺序找 feeds.yaml，样例见 examples/feeds.example.yaml）")
    d.add_argument("--out", help="日报输出路径（默认 ./briefs/YYYY-MM-DD.md，没有 ./briefs 时写 ~/.asgard/briefs/）")
    d.add_argument("--max-items", type=int, help="覆盖 feeds.yaml 里的 max_items_per_day")
    d.set_defaults(func=_cmd_daily)

    e = sub.add_parser("eval", help="跑预登记反事实 eval（三臂对比 + trace + SKIP 纪律）")
    e.add_argument("--dry-run", action="store_true", help="用 mock 模型离线验证管线，不花模型调用")
    e.add_argument("--k", type=int, default=3, help="每个模型臂格采样次数，取多数去 temp=0 抖动（默认 3）")
    e.add_argument("--report", help="把报告写到该路径（如 eval/report.md）")
    e.set_defaults(func=_cmd_eval)

    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
