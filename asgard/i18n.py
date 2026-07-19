"""Brief-facing strings in the user's chosen language (config `lang: zh | en`).

The language is an explicit upfront choice, not detection — the whole brief
(section labels, empty-day lines, feed-issue notes) follows it, and the model
is instructed to write its judgement fields in the same language.
"""
from __future__ import annotations

STR = {
    "zh": {
        "title": "Asgard 日报",
        "meta": "候选 {candidates} · 入报 {briefed} · 跳过 {skipped}",
        "facts": "事实",
        "for_you": "对你",
        "this_week": "这周能做",
        "cite": "依据",
        "original": "原文",
        "skipped_h": "跳过（{n} 条）",
        "issues_h": "信源异常",
        "no_news": "今天没有可用的新闻。所有信源都拉取失败，详见下方「信源异常」。",
        "all_skip": "今天没有值得你看的。检查了 {n} 条，全部与你的资料无关。",
        "fallback_skip": "间接相关，未到需要你看的程度",
        "process_fail": "处理失败（{err}）",
        "fetch_fail": "{name}: 拉取失败（{err}）",
        "parse_zero": "{name}: 解析到 0 条（该源格式可能不受支持）",
        "p_fetch": "拉取 {n} 个信源…",
        "p_refract": "{n} 条候选，逐条折射…",
        "p_written": "日报已写入 {paths}（候选 {candidates} · 入报 {briefed} · 跳过 {skipped}）",
        "sep": "；",
        "stop": "。",
        "colon": "：",
        "pl": "（",
        "pr": "）",
    },
    "en": {
        "title": "Asgard Daily Brief",
        "meta": "candidates {candidates} · briefed {briefed} · skipped {skipped}",
        "facts": "Facts",
        "for_you": "For you",
        "this_week": "This week",
        "cite": "Based on",
        "original": "original",
        "skipped_h": "Skipped ({n})",
        "issues_h": "Feed issues",
        "no_news": "No news available today — every feed failed to fetch. See “Feed issues” below.",
        "all_skip": "Nothing worth your time today. Checked {n} items; none of them touch your profile.",
        "fallback_skip": "Indirectly related — below the bar for your attention",
        "process_fail": "processing failed ({err})",
        "fetch_fail": "{name}: fetch failed ({err})",
        "parse_zero": "{name}: parsed 0 items (the feed format may be unsupported)",
        "p_fetch": "fetching {n} feeds…",
        "p_refract": "{n} candidates, refracting each…",
        "p_written": "brief written to {paths} (candidates {candidates} · briefed {briefed} · skipped {skipped})",
        "sep": "; ",
        "stop": ".",
        "colon": ": ",
        "pl": " (",
        "pr": ")",
    },
}


def t(lang: str | None) -> dict[str, str]:
    return STR["en" if lang == "en" else "zh"]
