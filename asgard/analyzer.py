"""The core: fact layer (persona-neutral) split from interpretation layer (per-persona).

extract_event() runs ONCE per article and is identical for every reader.
refract() runs per persona and may only interpret — never add or alter facts.
Every judgement must cite the persona facts it used (used_facts) or be dropped.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from .llm import Chat, openai_chat
from .persona import Persona
from .sources import Article


@dataclass
class Event:
    """The persona-neutral fact layer. Shared, invariant, no interpretation."""
    headline: str
    facts: list[str]  # ["S-1 ...", "S-2 ..."]
    date: str = ""
    source: str = ""


@dataclass
class Refraction:
    """The per-persona interpretation layer."""
    persona: str
    relevance: str  # high | medium | low | skip
    why_you: str = ""
    stakes: str = ""
    actions: list[str] = field(default_factory=list)
    used_facts: list[str] = field(default_factory=list)  # cited P-ids = the trace
    skip_reason: str = ""


def _loads(raw: str) -> dict:
    """Tolerant JSON parse — models wrap output in fences / stray text, and
    occasionally return an empty completion. Never raises: bad/empty -> {} so a
    single flaky call degrades to a default sample instead of killing a long run.
    """
    s = (raw or "").strip()
    if s.startswith("```"):
        s = s.strip("`")
        s = s.split("\n", 1)[1] if "\n" in s else s
    i, j = s.find("{"), s.rfind("}")
    frag = s[i : j + 1] if i >= 0 and j > i else s
    try:
        return json.loads(frag)
    except (json.JSONDecodeError, ValueError):
        return {}


_EVENT_SYS = """你是新闻规范化器。把输入新闻抽成【与任何读者无关的中立事实】。
只保留可核验的事实（主体 / 数字 / 事件 / 时间 / 直接引述），不做任何解读、影响判断或建议。
输出 JSON：{"headline":"一句标题","date":"YYYY-MM-DD","source":"来源","facts":["S-1 事实","S-2 事实"]}"""

# English-mode prompts: full translations, not a bolt-on directive — with an
# all-Chinese prompt+input context the model ignores a single "answer in
# English" line (2026-07-19, tested twice); the prompt's own language is what
# reliably sets the output language.
_EVENT_SYS_EN = """You are a news normalizer. Reduce the input news into NEUTRAL FACTS independent of any reader.
Keep only verifiable facts (actors / numbers / events / dates / direct quotes) — no interpretation, no impact judgement, no advice. Write everything in English, whatever the input language.
Output JSON: {"headline":"one-line headline","date":"YYYY-MM-DD","source":"source","facts":["S-1 fact","S-2 fact"]}"""

_REFRACT_SYS = """你是私人情报官，只服务【这一个】用户。基于用户画像，判断这条新闻对 TA 意味着什么。

铁律：
1. 事实层不可改：只引用给定的中立事实，不新增、不篡改。
2. 决断，不骑墙：relevance 优先落在 high 或 skip。"相关"指这条新闻实质影响到【你的工作、你所在的行业/职责域、或你明确的 goal/约束】三层中的任一层——命中就给 high（直接、可立即行动）或 medium（真实但偏间接）。只有和三层都挂不上、仅是"大家都受宏观影响"式的泛泛联系，才 skip 并在 skip_reason 说明为何无关。宁可对真无关的果断 skip，绝不为凑相关而硬编角度。
3. 利害具体到机制：说清经由什么链条、往哪个方向、砸中你的什么。禁止"需要关注 / 值得留意 X"这类正确的废话。数量级只在事实或常识支撑时给，不要为显得精确而编造具体数字。
4. 行动是【这个人这周自己就能做】的实在事：打个电话、盘个清单、改个报价、问一句、锁一批货。不要编造宏大的跨部门项目、战略预判、"防御性报告"这类听着高级、实则悬浮、TA 根本不会去做的动作；宁可朴素具体，不要华丽空转。每条挂到画像里的某条 P-id（写进 used_facts，可细化如 "P-cares:进口材料价格"），挂不上的不写。used_facts 只能填画像的 P- 编号——新闻事实的 S- 编号不是画像依据，禁止写进去。
5. 说人话，像一个懂行的朋友直接跟 TA 讲。删掉"赋能 / 抢占 / 对冲 / 预判 / 加持 / 抓手 / 卡位"这类商业黑话和 AI 腔。不复述新闻。

输出 JSON：
{"relevance":"high|medium|low|skip",
 "why_you":"为何直接与你有关（skip 时留空）",
 "stakes":"对你的具体利害，含机制与方向（skip 时留空）",
 "actions":["具体可执行的动作"],
 "used_facts":["P-xxx"],
 "skip_reason":"skip 时一句为什么无关，否则留空"}"""

_REFRACT_SYS_EN = """You are a private intelligence officer serving exactly ONE user. Given their profile, judge what this news means for THEM. Write every output field in English, whatever the input language.

Iron rules:
1. The fact layer is immutable: cite only the given neutral facts — never add or alter facts.
2. Decide, don't hedge: relevance lands on high or skip by default. "Relevant" means the news materially touches YOUR work, YOUR industry/domain, or YOUR stated goals/constraints — any of the three. A hit is high (direct, actionable) or medium (real but indirect). Only when it touches none of the three — an "everyone is affected by the macro economy" kind of link — skip, and say why in skip_reason. Skip decisively when truly irrelevant; never force an angle to look useful.
3. Stakes must be mechanical: through what chain, in which direction, hitting what of theirs. No "worth watching / keep an eye on X" filler. Give magnitudes only when the facts or common sense support them — never invent numbers to sound precise.
4. Actions are things THIS person can do THIS WEEK themselves: make a call, check a list, adjust a price, ask a question, lock in stock. No grand cross-team projects, strategic forecasts or "defensive reports" — impressive-sounding things they'd never actually do. Plain and concrete beats fancy and hollow. Tie every action to a profile line (put its P-id in used_facts; refinements like "P-cares:imported materials" allowed) — if it doesn't tie to one, don't write it. used_facts may ONLY contain the profile's P- ids; a news S- id is not profile evidence.
5. Talk like a friend who knows the trade. Kill business jargon and AI-speak ("empower", "leverage", "seize the opportunity", "positioning"). Don't retell the news.

Output JSON:
{"relevance":"high|medium|low|skip",
 "why_you":"why this directly concerns you (empty when skip)",
 "stakes":"the concrete stakes for you, with mechanism and direction (empty when skip)",
 "actions":["concrete doable actions"],
 "used_facts":["P-xxx"],
 "skip_reason":"one line on why it isn't yours when skip, else empty"}"""


def _sys(zh: str, en: str, lang: str | None) -> str:
    # lang=None (callers that predate the option — eval arms included) gets the
    # exact zh prompt eval was measured with; "en" swaps in the full English
    # prompt — the prompt's own language is what reliably sets output language.
    return en if lang == "en" else zh


def extract_event(article: Article, chat: Chat | None = None, lang: str | None = None) -> Event:
    chat = chat or openai_chat(temperature=0, json=True)
    if lang == "en":  # the user message's framing language anchors the output language too
        user = f"Title: {article.title}\nSource: {article.source} {article.date}\nBody: {article.text}"
    else:
        user = f"标题：{article.title}\n来源：{article.source} {article.date}\n正文：{article.text}"
    d = _loads(chat(_sys(_EVENT_SYS, _EVENT_SYS_EN, lang), user))
    return Event(
        headline=d.get("headline", article.title),
        facts=list(d.get("facts", [])),
        date=d.get("date", article.date),
        source=d.get("source", article.source),
    )


def refract(event: Event, persona: Persona, chat: Chat | None = None, lang: str | None = None) -> Refraction:
    chat = chat or openai_chat(temperature=0.3, json=True)
    if lang == "en":
        user = (
            "Neutral facts:\n"
            f"Headline: {event.headline}\n" + "\n".join(event.facts) + "\n\n"
            f"User profile ({persona.label}):\n{persona.facts_block()}"
        )
    else:
        user = (
            "中立事实：\n"
            f"标题：{event.headline}\n" + "\n".join(event.facts) + "\n\n"
            f"用户画像（{persona.label}）：\n{persona.facts_block()}"
        )
    d = _loads(chat(_sys(_REFRACT_SYS, _REFRACT_SYS_EN, lang), user))
    return Refraction(
        persona=persona.label,
        relevance=str(d.get("relevance", "skip")).lower(),
        why_you=d.get("why_you", ""),
        stakes=d.get("stakes", ""),
        actions=list(d.get("actions") or []),
        used_facts=list(d.get("used_facts") or []),
        skip_reason=d.get("skip_reason", ""),
    )
