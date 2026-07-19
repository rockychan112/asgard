<div align="center">

# Asgard — your private intelligence officer

**Every news item, interpreted only for the stakes and actions that concern you.**

<a href="https://rockychan112.github.io/asgard/"><b>Live demo</b></a> · <a href="./README.md">简体中文</a>

<img alt="status: pre-alpha" src="https://img.shields.io/badge/status-pre--alpha-d97706"> <img alt="python 3.11+" src="https://img.shields.io/badge/python-3.11+-3b82f6"> <img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-10b981">

</div>

The news tells you what happened in the world. None of it tells you what it means for you, or what to do. Asgard reads your profile file and refracts a news item into your stakes and this week's moves — and skips what isn't yours.

Same news, four people, four different results:

[![One news item refracted to four identities: three get their own stakes and actions, the fourth honestly skips](design/hero.png)](https://rockychan112.github.io/asgard/)

<p align="center"><sub>Three cards get their own stakes and moves, every claim shows its source; the fourth — skip　·　<a href="https://rockychan112.github.io/asgard/">▶ interactive: shuffle 12 news items, or knock out a profile line and watch the real engine re-judge</a></sub></p>

## How it compares

| | News apps | ChatGPT + a bio | Asgard |
|---|---|---|---|
| From one news item | Same summary for everyone | A generic "analysis" | Your stakes + your moves |
| When it's not yours | Pushed anyway | Invents an angle | Says "skip" |
| Why it says so | Black box | Can't tell | Every claim cites its source |
| Your profile | Guessed by the platform | A paragraph | A file, one fact per line |
| Your data | Their servers | Chat logs | All local |

## Install into your agent, get one brief a day

Asgard also ships as a skill for agents like Claude Code / Codex / Cursor: every day it reads your feeds and drops a brief at `briefs/2026-07-15.md`.

```bash
npx skills add https://github.com/rockychan112/asgard
```

Three steps: install the skill → say "asgard daily brief" once — on first run it walks you through setup itself (clones the repo, interviews your profile, wires your model endpoint, and doesn't call it done until a real run works) → have the agent schedule a daily job (no scheduler? just say it whenever — it still works).

What the skill installs is a **protocol** — the fact contract, the citation rule, the skip rule — not a magic prompt.

Two things up front:

- With the `asgard` CLI installed, the skill calls it (citation checks enforced in code); without it, your agent runs the protocol itself and the brief is honestly tagged `engine: llm` — the repo's eval only vouches for the CLI path.
- On a day when nothing concerns you, the brief still arrives: "Nothing worth your time today, checked N items." That's the product working, not failing.

Rather not go through an agent? `asgard daily` does the same thing in one command (fetch feeds → refract each item → write the brief); add your OS scheduler and it's fully local: see [docs/cron.md](docs/cron.md).

## Quickstart

```bash
git clone https://github.com/rockychan112/asgard && cd asgard
uv venv && uv pip install -e .   # no uv: python3 -m venv .venv && .venv/bin/pip install -e .

# any OpenAI-compatible endpoint: DeepSeek / local Ollama / OpenAI …
export OPENAI_BASE_URL=...
export OPENAI_API_KEY=...
export ASGARD_MODEL=...
```

```bash
# built-in news × every built-in identity (someone skips)
asgard brief fixture:hormuz

# one person only, or feed it a news URL
asgard brief fixture:hormuz --persona travel-lead
asgard brief https://example.com/some-news

# a full daily brief: fetch your feeds, refract each item, write briefs/YYYY-MM-DD.md
asgard daily --profile examples/profile.sample.yaml --feeds examples/feeds.example.yaml

# get one every day: write a config (lang zh/en + md/html + when to run, see examples/config.sample.yaml)
asgard doctor           # all checks green = configured
asgard schedule print   # emits crontab / launchd snippets to copy-paste
```

## Make the profile yours

Asgard knows you through one profile file: one fact per line, each line numbered.

```yaml
# personas/travel-lead.yaml
label: Online travel platform · business analyst
facts:
  P-role: Business analyst at an online travel platform, working on flight-business analytics
  P-fuel: The platform's revenue is tied to travel demand and jet-fuel costs
  P-cares: AI analytics / user-research tools, travel and consumer trends
  P-ignores: Anything unrelated to travel, flights, or analytics
```

Copy one and swap in your facts. Every judgment in the output shows which lines it used (the `P-` ids); delete a line, and the judgment that leans on it disappears.

## FAQ

**How is this different from writing ChatGPT a paragraph about myself?**

- The news facts are shared by everyone — it interprets, never rewrites, so it won't bend the story to please you
- Every judgment must cite which lines of your profile it used, or it doesn't ship
- When it's not yours, it skips instead of stretching

**You say you "tested it" — tested how?**

We set it a public exam: change one line in the profile, and only the judgment that leans on that line should change — more changes means it's making things up, no change means it isn't using your profile. The grading criteria were fixed and published before running, so no cherry-picking afterwards.

The result is published as-is: against "paste the whole profile into ChatGPT", on precision of personalization it **tied — no win**. What it wins reliably: it skips instead of stretching (false fires 2/13 vs 4/13), and every judgment shows a source you can check. All numbers in [`eval/`](eval/README.md).

**Will it invent an angle just to look useful?**

That's exactly what the exam watches. The skip cards in the demo are real output, and who skips changes with the news: a geopolitical crisis skips the wedding photographer; a camera price drop skips the other three.

**Where does my data go?**

- Your profile is a file on your machine
- The model is whatever endpoint you configure
- No telemetry, nothing reported anywhere

**How usable is it today?**

`brief` (refract one news item), `daily` (a full brief from your feed list — md/html, cron-schedulable), `doctor` (config health check), `eval` (run the exam), and the daily-brief skill (above) work. IM delivery and long-term memory aren't built yet.

## License

[MIT](LICENSE) · Copyright (c) 2026 rockychan112
