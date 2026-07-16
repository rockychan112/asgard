# Asgard — counterfactual eval

The honest test of whether Asgard is *structured personalization* and not a persona-prompt
wrapper: **change one fact in a persona, and only the consequence that depends on it should move.**
This harness runs that test on a **frozen, pre-registered grid** (`cases.yaml`) and compares Asgard
against two baselines on the same base model — so the only variable is the scaffolding, not the model.

It is built to be able to **falsify its own tool**. It did. See the result below.

## The three arms

| arm | the persona becomes | trace? |
|-----|--------------------|--------|
| `refraction` | structured contract: shared neutral facts split from per-persona interpretation; every claim cites a `P-id` | yes |
| `keyword` | a term list; fires on a match, no consequence layer (floor) | no |
| `longprompt` | the whole persona as free text to a generic assistant with the article — i.e. "an article + custom instructions" | no |

## Method (and two things the first runs taught us)

- **The arms are non-deterministic at temperature 0.** The same (persona, news) returns `high` on one
  sample and `skip` on the next — MoE routing, and `seed` does not fix it on the endpoints we tried. A
  single-shot counterfactual delta therefore measures sampling noise, not the fact change. So the harness
  takes a **K-sample majority** per cell and scores only **K-unanimous** cells; split cells are flagged
  and excluded.
- **"Are two outputs the same?" is the wrong primitive.** The judge calls two samples of the *identical*
  input "materially different" (paraphrase ≠ same, to it). So the metric is **stake presence**, not
  text-sameness: *targeted* = the load-bearing stake was present at base and is gone after the change;
  *collateral* = the same stake survives an inert change. Robust to paraphrase.
- Personas keep **orthogonal single-exposure facts** (`P-market` / `P-logistics` / `P-fx` / `P-fuel` /
  `P-import`) so each news hits a **sole-carrier** fact.
- Judge: a **non-Claude** model (GLM), blind to which arm it scores, prompts published in `judge.py`.
- Grid + oracles are committed **before** running (pre-registration).

## The pre-registered bar

> Asgard must beat `longprompt` on **both** counterfactual specificity **and** trace validity.
> A tie on either → **Plan B**: ship as a reproducible *personalization-memory protocol + this harness*,
> not as a tool that claims to beat a well-prompted assistant.

## What we found (N=8 anchors, arms=DeepSeek-flash, K=3, judge=GLM)

**Specificity is a tie — Asgard does not beat `longprompt`.** Raw targeted: refraction 4/8,
longprompt 5/8. On the K-unanimous cells both score 1.00. The counterfactual anchors that failed were
over-determined (removing "international shipping" still leaves "sells to the US" implying oil exposure) —
a structural limit, not just noise. **Per the pre-registered bar, this triggers Plan B.**

What Asgard **does** win, robustly:

- **SKIP discipline** — false-fires refraction **2/13** vs longprompt **4/13**, both zero misses. The
  structured contract says "not yours" more reliably.
- **Auditability** — every judgment cites a `P-id` you can inspect and ablate; the baselines cite nothing.
  (Trace validity ~0.72 by a conservative concern-probe; citation discipline is imperfect — the model
  occasionally cites source `S-x` ids. Treat trace as supporting, not headline.)

The "structured personas are more *stable* than a prompt blob" edge seen at N=4 did **not** survive at
N=8 (both 2/8 unanimous) — it was small-sample noise.

**Caveat / reproduce.** flash + K=3 is underpowered here: only 2/8 cells were K-unanimous. A
`pro` run at K≥5 with the over-determined logistics anchors fixed would firm the specificity number up —
but raw already ties, and over-determination is structural, so more power is unlikely to overturn it.

## Run it

```bash
export OPENAI_BASE_URL=... OPENAI_API_KEY=... ASGARD_MODEL=...   # arms
export GLM_BASE_URL=... GLM_API_KEY=... GLM_MODEL=...            # judge (non-Claude)
asgard eval --k 3 --report eval/report.md      # or --dry-run to validate the pipeline offline
```

The honest result is the point: a personalization tool that publishes the eval that could sink it,
runs it, and reports that its edge is discipline and auditability — not a magic specificity win.
