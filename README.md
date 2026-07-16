<div align="center">

# Asgard

**同一条新闻，只挑出跟你有关的利害，和你这周真能做的事；跟你无关，就直说无关。**

<a href="https://rockychan112.github.io/asgard/"><b>在线 Demo</b></a> · <a href="./eval/README.md">Eval 报告</a> · <a href="./README.en.md">English</a>

<img alt="status: pre-alpha" src="https://img.shields.io/badge/status-pre--alpha-d97706"> <img alt="python 3.11+" src="https://img.shields.io/badge/python-3.11+-3b82f6">

</div>

Asgard 按你是谁、在做什么、在意什么，把一条新闻重写成只对你成立的那部分——它怎么影响你，你这周能做什么。跟你没关系时，它直说无关，不硬凑一个角度。

同一条真实新闻，发给四个不同的人——三个人各有各的利害和动作，第四个，跳过：

[![同一条高 stakes 新闻，折射给四个身份：三条给出各自的利害与行动，第四条诚实 SKIP](design/hero.png)](https://rockychan112.github.io/asgard/)

<p align="center"><sub>人人拿到同一份中立事实，变的只是它对谁意味着什么；最后一张是诚实 SKIP　·　<a href="https://rockychan112.github.io/asgard/">▶ 可交互版</a></sub></p>

## 为什么这不是"套一段 prompt"

三个刻意的设计，把 Asgard 和"给通用助手套一段人设"分开：

1. **事实层 / 解释层分离** — 所有身份共享同一份中立事实（`Event`）；变的只有后果、优先级和行动。个性化不改写发生了什么，也不制造信息茧房。
2. **引得到依据才写** — 每条利害、每个行动，都必须引用你画像里的某条 `P-id`，引不到就不写。你看得见它"凭什么这么说"。
3. **诚实 SKIP** — 与你无关就直说无关。敢说"这条不是你的"，是套壳系统最难装出来的能力。

## 它做了件同类工具不会做的事：公开测试自己会不会翻车

大部分"个性化"工具，靠的是让你自己相信它懂你。Asgard 反过来——它附带一套公开的实验，专门用来证伪自己：要是它的个性化只是"换皮"，这套测试就该抓到。

做法：改你画像里的一个事实，理论上只有依赖它的那条结论该跟着变。拿它跟"把整份画像当 prompt 丢给通用助手"在同一个模型上比，唯一的变量是脚手架。判据发布前就登记死：两项指标都得赢，任一打平就走 Plan B。**跑完，一项打平了，没赢。** 那就走 Plan B，如实说，不藏。

真正赢的是两件更朴素的事：它更可靠地说出"这条不是你的"（SKIP 纪律），每条判断都挂着一条你能翻出来核对的依据（可审计）。不是"更懂你"的魔法——是更有纪律、更透明。

> It is built to be able to falsify its own tool. It did.

完整方法、数字、失败卡在哪、局限在哪 → [`eval/`](eval/README.md)

## 上手

```bash
uv venv && uv pip install -e .

# 任何 OpenAI 兼容端点：DeepSeek / 本地 Ollama / OpenAI …
export OPENAI_BASE_URL=...
export OPENAI_API_KEY=...
export ASGARD_MODEL=...

# 把一条内置新闻折射给全部内置 persona（其中有人会 SKIP）
asgard brief fixture:hormuz

# 只看某一个人
asgard brief fixture:hormuz --persona travel-lead
```

跑那套会证伪自己的 eval（裁判用一个非 Claude 的模型，且盲于自己在评哪一臂）：

```bash
export GLM_BASE_URL=... GLM_API_KEY=... GLM_MODEL=...   # 裁判 / judge
asgard eval --k 3 --report eval/report.md              # 或 --dry-run 离线验管线
```

## persona 是一份契约，不是一段话

`personas/*.yaml` 里每个 persona 是一份**结构化契约**——一条条带 `P-id` 的事实，不是一段自然语言 prompt。你能打开它、改它、给它记版本；每条折射引用的，就是这里的某几条。它是可审计 trace 的地基，也是"越用越懂你"要长在上面的东西。

## Roadmap

- ✅ **W0 · `brief`** — persona → 中立事实 → 按人折射 + trace + 诚实 SKIP。已跑通（DeepSeek / 任意 OpenAI 兼容端点实测）。
- ✅ **W1 · `eval`** — 预登记反事实 eval：三臂对比 + trace + SKIP 纪律。已跑通，结论见上。
- ⬜ `init` — 交互式建 persona。
- ⬜ `feedback` + 长期记忆 — 越用越懂你（up / down / correct / …；演进只走"建议 → 你确认"，绝不静默改你的身份）。
- ⬜ 本地 embedding / 全本地 / 零遥测。

诚实地说，今天的 Asgard 是这么个东西：**一套可复现的个性化记忆协议 + 一套能弄死自己的 eval + 一个更克制、可审计的 brief 工具。** 它会不会长成更大的东西，公开地做、公开地验。

---

<div align="center"><sub>Local-first · bring your own model · zero telemetry</sub></div>
