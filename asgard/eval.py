"""The counterfactual eval harness — runs the pre-registered grid (eval/cases.yaml)
across the three arms, applies single-fact perturbations and trace ablations, scores
what structure can score, and hands the semantic calls to a Judge.

Structural verdicts (relevance drops, citation presence, ablation) are live here.
Semantic verdicts (did this stake vanish? are these two outputs the same?) come from
the Judge — StubJudge in --dry-run, the real non-Claude judge in S3.
"""
from __future__ import annotations

import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .arms import ArmOutput, run_keyword, run_longprompt, run_refraction
from .analyzer import Event, extract_event
from .judge import Judge, StubJudge
from .llm import Chat, openai_chat
from .persona import Persona
from .sources import load

ROOT = Path(__file__).resolve().parent.parent
PERSONA_DIR = ROOT / "personas"
CASES = ROOT / "eval" / "cases.yaml"
ARMS = ("refraction", "keyword", "longprompt")
_WORKERS = 8  # the run is I/O-bound (hundreds of API calls); fan out per independent cell


def _pmap(fn, items: list) -> list:
    """Map fn over items concurrently, preserving order. Empty-safe."""
    if not items:
        return []
    with ThreadPoolExecutor(max_workers=_WORKERS) as ex:
        return list(ex.map(fn, items))


# --- one place that dispatches an arm by name -----------------------------

def _run(arm: str, event: Event, persona: Persona, news: str, chat: Chat) -> ArmOutput:
    if arm == "refraction":
        return run_refraction(event, persona, news, chat)
    if arm == "keyword":
        return run_keyword(event, persona, news)
    return run_longprompt(event, persona, news, chat)


def _sample(arm: str, event: Event, persona: Persona, news: str, chat: Chat, k: int) -> ArmOutput:
    """Run a model arm K times and collapse to a majority verdict — the arms are
    NOT deterministic at temperature=0 (MoE routing), so a single shot measures
    sampling noise. keyword is deterministic, so K=1. agreement records the vote
    split; a low agreement flags a cell sitting on the model's decision boundary.
    """
    if arm == "keyword" or k <= 1:
        return _run(arm, event, persona, news, chat)
    outs = [_run(arm, event, persona, news, chat) for _ in range(k)]
    maj_rel, n = Counter(o.relevance for o in outs).most_common(1)[0]
    reps = [o for o in outs if o.relevance == maj_rel]
    body = next((o.body for o in reps if o.has_content()), reps[0].body)
    return ArmOutput(arm, persona.label, news, maj_rel, body, reps[0].used_facts, agreement=n / len(outs))


# --- result records -------------------------------------------------------

@dataclass
class SkipResult:
    arm: str
    false_fire: int = 0  # expect skip, but fired
    skip_n: int = 0
    miss: int = 0  # expect fire, but skipped
    fire_n: int = 0


@dataclass
class CFResult:
    case: str
    arm: str
    base_rel: str
    targeted_rel: str
    drop_ok: bool | None  # structural: relevance fell to skip (only when drop_relevance)
    vanish_ok: bool | None  # semantic: stake present at base AND absent after the change
    stable_ok: bool | None  # semantic: collateral output unchanged
    agree: float = 1.0  # min K-agreement across the base/targeted/collateral cells


@dataclass
class TraceResult:
    persona: str
    news: str
    pid: str
    collapse_rel: bool  # structural: relevance changed after ablating the cited fact
    collapse_stake: bool | None  # semantic: the supported stake collapsed


@dataclass
class Report:
    mode: str
    judge: str
    skip: list[SkipResult] = field(default_factory=list)
    cf: list[CFResult] = field(default_factory=list)
    trace: list[TraceResult] = field(default_factory=list)


# --- the run --------------------------------------------------------------

def run_eval(chat: Chat, judge: Judge, *, mode: str, k: int = 3) -> Report:
    spec = yaml.safe_load(CASES.read_text(encoding="utf-8"))
    personas = {p.slug: p for p in (Persona.load(x) for x in PERSONA_DIR.glob("*.yaml"))}
    # each event is extracted once and shared, so its own noise is common-mode and
    # cancels in every base-vs-perturbed comparison (both read the same cached event).
    events: dict[str, Event] = dict(
        _pmap(lambda n: (n, extract_event(load(f"fixture:{n}"), chat)), spec["news"])
    )

    rep = Report(mode=mode, judge=judge.__class__.__name__)

    # base grid: (arm, persona, news) -> majority-of-K ArmOutput
    cells = [(arm, slug, news) for news in spec["news"] for slug in personas for arm in ARMS]
    base: dict[tuple[str, str, str], ArmOutput] = dict(
        _pmap(lambda c: (c, _sample(c[0], events[c[2]], personas[c[1]], c[2], chat, k)), cells)
    )

    # 1. SKIP discipline (structural, judged against B via the expect map)
    for arm in ARMS:
        sr = SkipResult(arm)
        for slug, per_news in spec["expect"].items():
            for news, want in per_news.items():
                out = base[(arm, slug, news)]
                if want == "skip":
                    sr.skip_n += 1
                    sr.false_fire += int(out.fired)
                else:
                    sr.fire_n += 1
                    sr.miss += int(not out.fired)
        rep.skip.append(sr)

    # 2. counterfactual specificity — one work item per (case, arm)
    def _cf(item: tuple) -> CFResult:
        case, arm = item
        slug, news = case["persona"], case["news"]
        tgt, col = case["targeted"], case["collateral"]
        p_tgt = _perturb(personas[slug], tgt["change"])
        p_col = _perturb(personas[slug], col["change"])
        b = base[(arm, slug, news)]
        o_tgt = _sample(arm, events[news], p_tgt, news, chat, k)
        o_col = _sample(arm, events[news], p_col, news, chat, k)
        drop_ok = (b.fired and not o_tgt.fired) if tgt.get("drop_relevance") else None
        # Everything is measured by stake PRESENCE, not text-sameness: the judge calls
        # two samples of the identical input "materially different", so a text-sameness
        # metric just measures paraphrase noise. Stake presence is robust to paraphrase.
        stake = tgt["vanish_stake"]
        base_has = judge.stake_present(b.body, stake) if b.has_content() else None
        tgt_has = judge.stake_present(o_tgt.body, stake)
        col_has = judge.stake_present(o_col.body, stake)
        vanish_ok = (base_has and not tgt_has) if None not in (base_has, tgt_has) else None  # stake gone
        stable_ok = (base_has and col_has) if None not in (base_has, col_has) else None  # stake survives
        agree = min(b.agreement, o_tgt.agreement, o_col.agreement)
        return CFResult(case["id"], arm, b.relevance, o_tgt.relevance, drop_ok, vanish_ok, stable_ok, agree)

    rep.cf = _pmap(_cf, [(case, arm) for case in spec["counterfactuals"] for arm in ARMS])

    # 3. trace validity (refraction arm only — the others cite nothing)
    def _tr(item: tuple) -> TraceResult:
        slug, news, pid, b = item
        bare = pid.split(":", 1)[0]  # "P-cares:进口" -> "P-cares"
        ablated = _sample("refraction", events[news], personas[slug].without_fact(bare), news, chat, k)
        collapse_rel = ablated.relevance != b.relevance
        # a citation is real if removing the fact removes its concern from the output.
        # Probe with the fact's own text (stake_present). Conservative: adjacent talk may keep it.
        concern = personas[slug].facts.get(bare, "")
        still = judge.stake_present(ablated.body, concern) if concern else None
        collapse_stake = (not still) if still is not None else None
        return TraceResult(personas[slug].label, news, pid, collapse_rel, collapse_stake)

    trace_items = [
        (slug, news, pid, base[("refraction", slug, news)])
        for slug, per_news in spec["expect"].items()
        for news in per_news
        if base[("refraction", slug, news)].fired and base[("refraction", slug, news)].used_facts
        for pid in base[("refraction", slug, news)].used_facts
    ]
    rep.trace = _pmap(_tr, trace_items)

    return rep


def _perturb(persona: Persona, change: dict) -> Persona:
    if len(change) != 1:
        raise ValueError(f"counterfactual change must touch exactly one P-id, got {list(change)}")
    (fid, text), = change.items()
    return persona.with_fact(fid, text)


# --- mock provider for --dry-run ------------------------------------------

def mock_chat(system: str, user: str) -> str:
    if "新闻规范化器" in system:  # echo the real title/body so downstream skip logic has signal
        title = next((ln[3:] for ln in user.splitlines() if ln.startswith("标题：")), "（mock）")
        body = user.split("正文：", 1)[-1][:200]
        return json.dumps(
            {"headline": title, "date": "2026-07-15", "source": "mock", "facts": [f"S-1 {title}", f"S-2 {body}"]},
            ensure_ascii=False,
        )
    skip = "格雷厄姆" in user or "病逝" in user
    if "私人情报官" in system:
        if skip:
            return '{"relevance":"skip","skip_reason":"mock 无关","used_facts":[]}'
        return '{"relevance":"high","stakes":"mock 利害","actions":["mock 行动"],"used_facts":["P-role"]}'
    if "私人助理" in system:
        return '{"relevance":"skip","text":"mock 无关"}' if skip else '{"relevance":"high","text":"mock 利害与行动"}'
    return "{}"


# --- rendering ------------------------------------------------------------

def _mark(v: bool | None) -> str:
    return "UNJUDGED" if v is None else ("✓" if v else "✗")


@dataclass
class ArmScore:
    arm: str
    targeted: float | None  # fraction of cases where the load-bearing change moved the right thing
    collateral: float | None  # fraction where the inert change left output stable
    specificity: float | None  # min(targeted, collateral) — can't win by all-move or all-stay
    trace: float | None  # fraction of citations that demonstrably drive their claim (refraction only)
    false_fire: str
    miss: str
    n_robust: int = 0  # cf cells that were K-unanimous (scored)
    n_total: int = 0  # cf cells total


def _rate(vals: list[bool | None]) -> float | None:
    judged = [v for v in vals if v is not None]
    return sum(judged) / len(judged) if judged else None


def _targeted_ok(c: CFResult) -> bool | None:
    comps = ([c.drop_ok] if c.drop_ok is not None else []) + [c.vanish_ok]
    if any(x is False for x in comps):
        return False
    return None if any(x is None for x in comps) else True


def summarize(rep: Report) -> list[ArmScore]:
    skip = {s.arm: s for s in rep.skip}
    out = []
    for arm in ARMS:
        s = skip[arm]
        ff, ms = f"{s.false_fire}/{s.skip_n}", f"{s.miss}/{s.fire_n}"
        allcf = [c for c in rep.cf if c.arm == arm]
        if arm == "keyword":  # no interpretation layer — counterfactual specificity is undefined
            out.append(ArmScore(arm, None, None, None, None, ff, ms, 0, len(allcf)))
            continue
        cfs = [c for c in allcf if c.agree >= 1.0]  # score only model-stable (K-unanimous) cells
        t = _rate([_targeted_ok(c) for c in cfs])
        col = _rate([c.stable_ok for c in cfs])
        spec = min(t, col) if t is not None and col is not None else None
        # a citation is valid only if ablating it demonstrably moves the output (relevance or stake)
        trace = _rate([tr.collapse_rel or (tr.collapse_stake is True) for tr in rep.trace]) if arm == "refraction" else None
        out.append(ArmScore(arm, t, col, spec, trace, ff, ms, len(cfs), len(allcf)))
    return out


def verdict(scores: list[ArmScore]) -> str:
    d = {s.arm: s for s in scores}
    ref, lp = d["refraction"], d["longprompt"]
    power = f"（稳定格 refraction {ref.n_robust}/{ref.n_total}、longprompt {lp.n_robust}/{lp.n_total}）"
    weak = min(ref.n_robust, lp.n_robust) < 3
    if ref.specificity is None or lp.specificity is None:
        return f"UNKNOWN — 特异性判分不足{power}，补样本或升 K 再裁决。"
    margin = ref.specificity - lp.specificity
    trace_real = ref.trace is not None and ref.trace >= 0.5
    caveat = "（⚠ 稳定格 <3，欠功率，结论待更高 K / pro 复核）" if weak else ""
    if margin >= 0.15 and trace_real:
        return (f"倾向 PASS：特异性 {ref.specificity:.2f} vs longprompt {lp.specificity:.2f}（+{margin:.2f}）"
                f"{power}{caveat}。")
    return (f"倾向 Plan B：特异性 {ref.specificity:.2f} vs longprompt {lp.specificity:.2f}（{margin:+.2f}）"
            f"{power}{caveat} → 特异性未赢，按预登记收缩成协议+harness。")


def _pct(v: float | None) -> str:
    return "N/A" if v is None else f"{v:.2f}"


def _ag(a: float) -> str:
    return "" if a >= 1.0 else f" ⚠{a:.2f}"


def render(rep: Report) -> str:
    scores = summarize(rep)
    L = [f"# Asgard eval · {rep.mode}", f"预登记网格 eval/cases.yaml · judge={rep.judge}", ""]

    L += ["## 0. 汇总与裁决（对预登记 bar）", "",
          "| arm | 特异性=min(targeted,collateral) | targeted | collateral | trace 有效率 | 稳定格 |",
          "|---|---|---|---|---|---|"]
    for s in scores:
        L.append(f"| {s.arm} | {_pct(s.specificity)} | {_pct(s.targeted)} | {_pct(s.collateral)} "
                 f"| {_pct(s.trace)} | {s.n_robust}/{s.n_total} |")
    L += ["", "**裁决**：" + verdict(scores),
          "", "> 特异性只在 K 采样一致（agreement=1）的稳定格上计。keyword 无解释层，特异性记 N/A、只看 SKIP 纪律。", ""]

    L += ["## 1. SKIP 纪律（按 B）", "", "| arm | 误报 该skip却fire | 漏报 该fire却skip |", "|---|---|---|"]
    for s in rep.skip:
        L.append(f"| {s.arm} | {s.false_fire}/{s.skip_n} | {s.miss}/{s.fire_n} |")

    L += ["", "## 2. 反事实特异性（⚠=该格仍在模型决策边界抖动，不计入分）", "",
          "| case | arm | base→改后 | targeted(该变) | collateral(该稳) | agreement |", "|---|---|---|---|---|---|"]
    for c in rep.cf:
        tgt = _mark(c.drop_ok) if c.drop_ok is not None else _mark(c.vanish_ok)
        L.append(f"| {c.case} | {c.arm} | {c.base_rel}→{c.targeted_rel} | {tgt} | {_mark(c.stable_ok)} |{_ag(c.agree) or ' 1.00'} |")

    L += ["", "## 3. Trace 有效性（仅 refraction；baseline 无引用=N/A）", "",
          "| persona · news | 引用 P-id | 消融后 relevance 变 | stake 塌陷 |", "|---|---|---|---|"]
    for t in rep.trace:
        L.append(f"| {t.persona} · {t.news} | {t.pid} | {'✓' if t.collapse_rel else '✗'} | {_mark(t.collapse_stake)} |")
    if not rep.trace:
        L.append("| （无 fired refraction 或无引用） | — | — | — |")
    return "\n".join(L)
