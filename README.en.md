<!-- lang-switch --> [简体中文](./README.md)　·　**English**

# Asgard

**One piece of news, cut down to what's actually at stake for you and what you can do about it this week — and when it isn't yours, it says so.**

Asgard rewrites a news item into the part that's yours — given who you are, what you do, what you care about: how it hits you, what you can do this week. When it doesn't touch you, it says "not yours" instead of inventing an angle.

Below is one real news item sent to four different people: three get their own stakes and moves; the fourth — skip.

[![One high-stakes news item refracted to four identities: three get their own stakes and actions, the fourth is an honest SKIP](design/hero.png)](https://rockychan112.github.io/asgard/)

<p align="center"><sub>One news item (a fixed sample), one shared set of neutral facts — only what it means per person changes. The last card is an honest SKIP.　·　<a href="https://rockychan112.github.io/asgard/">▶ Open the interactive demo</a></sub></p>

`pre-alpha` — an open exploration, not a finished product. What runs today: `brief` (refract one news item per person) and `eval` (the test below).

## Why this isn't a persona-prompt wrapper

Three deliberate choices separate Asgard from "hand a general assistant a character sheet":

1. **Facts and reading are separate layers** — every persona shares one neutral set of facts (`Event`); only the consequences, priorities, and actions change. Personalization never rewrites what happened, and never builds an echo chamber.
2. **No claim without a citation** — every stake and every action must cite a `P-id` from your profile, or it doesn't ship. You can see *why* it says what it says.
3. **An honest SKIP** — when it isn't yours, it says so. (Saying "this one isn't for you" is the one thing a wrapper can't fake.)

## It does what similar tools won't: it tests itself, in public, for faking it

Most "personalized" tools work by getting you to *believe* they understand you. Asgard does the opposite — it ships a public experiment built to falsify itself: if the personalization were just a reskin, this test should catch it.

How: change one fact in your profile, and only the conclusion that depends on it should move. Run that against "paste the whole profile as a prompt to a general assistant" on the same model — the only variable is the scaffolding. The bar was pre-registered before running: Asgard had to win on *both* metrics; a tie on either triggers Plan B. **It ran. One metric tied — no win.** So Plan B it is, said plainly.

What it *does* win is two humbler things: it's more reliable at saying "this one isn't yours" (SKIP discipline), and every judgment carries a citation you can pull up and check (auditability). Not an "understands you better" magic trick — just more discipline and more transparency.

> It is built to be able to falsify its own tool. It did.

Full method, numbers, where it failed, the limits → [`eval/`](eval/README.md)

## Quickstart

```bash
uv venv && uv pip install -e .

# any OpenAI-compatible endpoint: DeepSeek / local Ollama / OpenAI …
export OPENAI_BASE_URL=...
export OPENAI_API_KEY=...
export ASGARD_MODEL=...

# refract one built-in news item across every built-in persona (one of them SKIPs)
asgard brief fixture:hormuz

# just one person
asgard brief fixture:hormuz --persona travel-lead
```

Run the eval that can falsify itself (the judge is a non-Claude model, blind to which arm it's scoring):

```bash
export GLM_BASE_URL=... GLM_API_KEY=... GLM_MODEL=...   # judge
asgard eval --k 3 --report eval/report.md              # or --dry-run to validate the pipeline offline
```

## A persona is a contract, not a paragraph

Each persona in `personas/*.yaml` is a **structured contract** — id'd facts you can open, edit, and version, not a prose prompt. It's what every refraction cites, and the ground the "gets to know you over time" loop grows on.

## Roadmap

- ✅ **W0 · `brief`** — persona → neutral facts → per-person refraction + trace + honest SKIP. Working (tested on DeepSeek / any OpenAI-compatible endpoint).
- ✅ **W1 · `eval`** — pre-registered counterfactual eval: three arms + trace + SKIP discipline. Working; result above.
- ⬜ `init` — build a persona interactively.
- ⬜ `feedback` + long-term memory — gets to know you over time (up / down / correct / …; evolution only ever *suggests → you confirm*, never silently rewrites who you are).
- ⬜ local embeddings / fully local / zero telemetry.

Honestly, today Asgard is this: **a reproducible personalization-memory protocol, a harness that can sink its own claims, and a more restrained, auditable brief tool.** Whether it grows into more gets decided in the open.

---
<sub>Local-first · bring your own model · zero telemetry</sub>
