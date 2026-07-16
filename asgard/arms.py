"""The three arms under test. All share one base model (injected Chat); only the
scaffolding differs — that isolates the claim to "the structure matters," not
"a stronger model." Each arm emits the same ArmOutput so one judge can score them.

  refraction — structured contract, fact/interp split, forced P-id trace
  keyword    — persona collapsed to a term list; fires on match, no reasoning (floor)
  longprompt — whole persona as prose to a generic assistant (the real rival:
               "an article + custom instructions / a general assistant with memory")
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .analyzer import Event, _loads, refract
from .llm import Chat
from .persona import Persona

RELEVANCES = ("high", "medium", "low", "skip")


@dataclass
class ArmOutput:
    arm: str
    persona: str
    news: str
    relevance: str  # one of RELEVANCES
    body: str  # stakes + actions (or skip reason) — the text the judge inspects
    used_facts: list[str] = field(default_factory=list)  # P-id citations; [] for baselines
    agreement: float = 1.0  # fraction of K samples that agreed on relevance (1.0 = keyword/deterministic)
    fired: bool = field(init=False)

    def __post_init__(self) -> None:
        self.fired = self.relevance != "skip"

    def has_content(self) -> bool:
        """True if body carries an actual stake/reason, not just empty scaffolding."""
        return bool(self.body.replace("利害：", "").replace("行动：", "").replace("—", "").strip())


# --- refraction arm -------------------------------------------------------

def run_refraction(event: Event, persona: Persona, news: str, chat: Chat) -> ArmOutput:
    r = refract(event, persona, chat)
    if r.relevance == "skip":
        body = r.skip_reason or "（判定与你无关）"
    else:
        body = f"利害：{r.stakes}\n行动：" + "；".join(r.actions)
    return ArmOutput("refraction", persona.label, news, r.relevance, body, list(r.used_facts))


# --- keyword arm (floor) --------------------------------------------------

_SPLIT = re.compile(r"[、，,；;／/。\s]+")
_STOP = {"的", "与", "和", "或", "等", "对", "你", "TA", "无关", "影响", "变化", "行业", "身处"}


def _terms(persona: Persona) -> list[str]:
    """Collapse the cares/industry/role facts into a bag of match terms."""
    src = " ".join(persona.facts.get(f, "") for f in ("P-cares", "P-industry", "P-role"))
    terms = {t for t in _SPLIT.split(src) if len(t) >= 2 and t not in _STOP}
    return sorted(terms, key=len, reverse=True)


def run_keyword(event: Event, persona: Persona, news: str) -> ArmOutput:
    text = event.headline + " " + " ".join(event.facts)
    hits = [t for t in _terms(persona) if t in text]
    if hits:
        return ArmOutput("keyword", persona.label, news, "high", "命中关键词：" + "、".join(hits))
    return ArmOutput("keyword", persona.label, news, "skip", "无关键词命中")


# --- longprompt arm (the real rival) --------------------------------------

_LONG_SYS = """你是用户的私人助理，很懂 TA。下面给你 TA 的一段自我描述，和今天的一条新闻。
用中文告诉 TA 这条新闻对 TA 具体意味着什么、值不值得关注、该做什么。若确实与 TA 无关，就直说无关，别硬找角度。
输出 JSON：{"relevance":"high|medium|low|skip","text":"给 TA 的利害与行动；skip 时一句为什么无关"}"""


def _prose(persona: Persona) -> str:
    return f"我是{persona.label}。" + "".join(v.rstrip("。") + "。" for v in persona.facts.values())


def run_longprompt(event: Event, persona: Persona, news: str, chat: Chat) -> ArmOutput:
    user = (
        f"【我是谁】\n{_prose(persona)}\n\n"
        f"【今天的新闻】\n标题：{event.headline}\n" + "\n".join(event.facts)
    )
    d = _loads(chat(_LONG_SYS, user))
    rel = str(d.get("relevance", "skip")).lower()
    rel = rel if rel in RELEVANCES else "skip"
    return ArmOutput("longprompt", persona.label, news, rel, d.get("text", ""))
