"""Terminal rendering. Same output for demo and daily use — no demo-only path."""
from __future__ import annotations

import re

from .analyzer import Event, Refraction

try:
    from rich.console import Console
    from rich.panel import Panel

    _console: "Console | None" = Console()
except Exception:  # rich optional
    _console = None

_HUE = {"high": "gold3", "medium": "gold3", "low": "cyan", "skip": "grey50"}


def render_event(event: Event) -> None:
    head = f"[dim]SOURCE · {event.date} · {event.source}[/dim]\n{event.headline}"
    if _console:
        _console.print(Panel(head, title="中立事实 · fact layer", border_style="bright_blue", expand=True))
    else:
        print(f"\n== 中立事实 ({event.date} · {event.source}) ==\n{event.headline}")


def render_card(r: Refraction) -> None:
    if r.relevance == "skip":
        body = f"[跳过] {r.skip_reason or '与你无关，不硬扯。'}"
    else:
        # Arrow glued to the text (no breakable space) so a long Chinese action
        # never orphans the "→" on its own wrapped line.
        actions = "\n".join(f"[cyan]→[/cyan]{a}" for a in r.actions) or "—"
        body = (
            f"[dim]相关性[/dim] [bold]{r.relevance}[/bold]\n\n"
            f"[bold]利害[/bold]\n{r.stakes}\n\n"
            f"[bold]行动[/bold]\n{actions}\n\n"
            f"[dim]依据 {' · '.join(r.used_facts) or '—'}[/dim]"
        )
    if _console:
        _console.print(Panel(body, title=r.persona, border_style=_HUE.get(r.relevance, "white"), expand=True))
    else:
        print(f"\n== {r.persona} ==\n{_strip(body)}")


def _strip(s: str) -> str:
    return re.sub(r"\[/?[a-z0-9 #]+\]", "", s)
