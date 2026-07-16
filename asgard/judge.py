"""The semantic judge, behind an interface so the harness stays judge-agnostic.

Two calls the structural checks can't make:
  stake_present   — is a specific stake/action present in an output? (targeted vanish)
  materially_same — are two outputs materially the same? (collateral stability)

Each returns True/False, or None for "unjudged". StubJudge returns None for
everything (used in --dry-run and before the real judge is wired in S3). The real
LLMJudge lands in S3: a non-Claude model, blind to which arm produced an output,
its prompt published in this repo.
"""
from __future__ import annotations

from typing import Protocol

from .analyzer import _loads
from .llm import Chat


class Judge(Protocol):
    def stake_present(self, body: str, stake: str) -> bool | None: ...
    def materially_same(self, before: str, after: str) -> bool | None: ...


class StubJudge:
    """No-op judge — every semantic verdict is None (UNJUDGED)."""

    def stake_present(self, body: str, stake: str) -> bool | None:
        return None

    def materially_same(self, before: str, after: str) -> bool | None:
        return None


# The two judge prompts are published here on purpose — the eval is only as honest
# as its rubric is inspectable. The judge is given no hint of which arm produced an
# output. A malformed reply returns None (unjudged) rather than crashing the run.

_PRESENT_SYS = """你是严格中立的评审。给你一段【给某用户的资讯解读】和一条【待查论点】。
只判断这段解读里是否明确表达了该论点（某条利害或某个行动），不评价它对不对、不要求措辞一致。
输出 JSON：{"present": true 或 false}"""

_SAME_SYS = """你是严格中立的评审。给你同一情境下先后两段解读 BEFORE 与 AFTER。
判断 AFTER 相对 BEFORE 是否【实质结论基本未变】：措辞、顺序、详略不同但没有增加、删除或反转任何一条实质利害或行动 = true；
只要有一条实质利害/行动出现、消失或反转 = false。输出 JSON：{"same": true 或 false}"""


class LLMJudge:
    """Semantic judge on a non-Claude model, kept blind to which arm it is scoring."""

    def __init__(self, chat: Chat) -> None:
        self.chat = chat

    def stake_present(self, body: str, stake: str) -> bool | None:
        try:
            d = _loads(self.chat(_PRESENT_SYS, f"【解读】\n{body}\n\n【待查论点】\n{stake}"))
            return bool(d["present"])
        except Exception:
            return None

    def materially_same(self, before: str, after: str) -> bool | None:
        try:
            d = _loads(self.chat(_SAME_SYS, f"BEFORE：\n{before}\n\nAFTER：\n{after}"))
            return bool(d["same"])
        except Exception:
            return None
