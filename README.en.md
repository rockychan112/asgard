<div align="center">

# Asgard

**One news item, cut to the part that concerns you — and when none of it does, it says so.**

<a href="https://rockychan112.github.io/asgard/"><b>Live demo</b></a> · <a href="./eval/README.md">Eval report</a> · <a href="./README.md">简体中文</a>

<img alt="status: pre-alpha" src="https://img.shields.io/badge/status-pre--alpha-d97706"> <img alt="python 3.11+" src="https://img.shields.io/badge/python-3.11+-3b82f6"> <img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-10b981">

</div>

The news tells you what happened in the world. None of it tells you what it means for you, or what to do. Asgard reads your profile and refracts a news item into your stakes and the moves you can make this week — and skips what isn't yours.

Same news, four people, four different results:

[![One news item refracted to four identities: three get their own stakes and actions, the fourth is an honest skip](design/hero.png)](https://rockychan112.github.io/asgard/)

<p align="center"><sub>Three cards get their own stakes and moves, every claim cites its source; the fourth — skip　·　<a href="https://rockychan112.github.io/asgard/">▶ interactive version</a></sub></p>

## How it compares

| | News apps / aggregators | ChatGPT + a persona blurb | Asgard |
|---|---|---|---|
| What you get from one news item | The same summary as everyone | An "analysis for you" | Your stakes + moves you can make this week |
| When it's not relevant to you | Pushed anyway | Often invents an angle | Says "skip", with a reason |
| Why it says what it says | Black-box ranking | Can't tell | Every claim cites the exact fact in your profile (`P-id`) |
| Your profile | Guessed by the platform | A paragraph of prose | A YAML file, one fact per line — edit it, version it |
| Where your data lives | Their servers | In chat logs | Local files + your own model endpoint, zero telemetry |

## Quickstart

```bash
git clone https://github.com/rockychan112/asgard && cd asgard
uv venv && uv pip install -e .

# any OpenAI-compatible endpoint: DeepSeek / local Ollama / OpenAI …
export OPENAI_BASE_URL=...
export OPENAI_API_KEY=...
export ASGARD_MODEL=...
```

```bash
# built-in news × every built-in persona (one of them skips)
asgard brief fixture:hormuz

# one person only, or feed it a news URL
asgard brief fixture:hormuz --persona travel-lead
asgard brief https://example.com/some-news
```

## Make the persona yours

A persona is a YAML file, one fact per line:

```yaml
# personas/travel-lead.yaml
label: Online travel platform · business analyst
facts:
  P-role: Business analyst at an online travel platform, working on flight-business analytics
  P-fuel: The platform's revenue is tied to travel demand and jet-fuel costs
  P-cares: AI analytics / user-research tools, travel and consumer trends
  P-ignores: Anything unrelated to travel, flights, or analytics
```

Copy one, swap in your facts. Every judgment in the output cites which facts it used (`P-id`) — delete a fact, and the judgment that depends on it disappears.

## FAQ

**How is this different from writing ChatGPT a paragraph about myself?**
Three ways: facts and interpretation are separate layers — everyone shares the same neutral facts, personalization never rewrites the news; every claim must cite a specific fact in your profile, or it doesn't ship; and when it's not yours, it skips instead of stretching.

**Is it actually better at "getting me" than a general assistant with a persona prompt?**
Not necessarily. We tested it with a public counterfactual eval (criteria pre-registered before running): on specificity it tied — no win. What it wins reliably: it skips instead of stretching (false fires 2/13 vs 4/13), and every judgment carries a citation you can check. Method and all numbers in [`eval/`](eval/README.md).

**Will it invent an angle just to look useful?**
That's exactly what the eval watches (skip discipline). The fourth card in the demo is real output: the model plainly says "this isn't yours."

**Where does my data go?**
Nowhere. Your profile is local YAML, the model is whatever endpoint you configure, and there's no telemetry.

**How usable is it today?**
`brief` (refract a news item) and `eval` (run the test) work. Interactive persona setup and long-term memory aren't built yet — edit the YAML by hand for now.

## License

[MIT](LICENSE) · Copyright (c) 2026 rockychan112
