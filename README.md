<div align="center">

# Asgard

**同一条新闻，只告诉你跟你有关的部分；无关，就直说无关。**

<a href="https://rockychan112.github.io/asgard/"><b>在线 Demo</b></a> · <a href="./eval/README.md">Eval 报告</a> · <a href="./README.en.md">English</a>

<img alt="status: pre-alpha" src="https://img.shields.io/badge/status-pre--alpha-d97706"> <img alt="python 3.11+" src="https://img.shields.io/badge/python-3.11+-3b82f6"> <img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-10b981">

</div>

每天的资讯都在讲"世界发生了什么"，没有一条告诉你"这跟你有什么关系、你该干嘛"。Asgard 读你的画像，把一条新闻折射成你的利害和这周能做的动作；跟你无关的，直接跳过。

同一条新闻，四个人，四种结果：

[![同一条新闻折射给四个身份：三条各自的利害与行动，第四条诚实跳过](design/hero.png)](https://rockychan112.github.io/asgard/)

<p align="center"><sub>三张卡各有各的利害和动作，每条都标注依据；第四张，跳过　·　<a href="https://rockychan112.github.io/asgard/">▶ 可交互版</a></sub></p>

## 跟其它工具的差别

| | 新闻 App / 聚合器 | ChatGPT + 一段人设 | Asgard |
|---|---|---|---|
| 同一条新闻你拿到什么 | 人人同一份摘要 | 一段"对你的分析" | 你的利害 + 这周能做的动作 |
| 和你无关时 | 照样推给你 | 常硬找一个角度 | 直说"跳过"，给理由 |
| 它凭什么这么判断 | 黑盒推荐 | 说不清 | 每条标注引用了你画像里哪条事实（`P-id`），可查 |
| 你的画像 | 平台算法猜的 | 一段散文 | 一个 YAML 文件，逐条事实，自己改、可版本化 |
| 数据在哪 | 平台服务器 | 对话记录里 | 本地文件 + 你自己的模型端点，零遥测 |

## 上手

```bash
git clone https://github.com/rockychan112/asgard && cd asgard
uv venv && uv pip install -e .

# 任何 OpenAI 兼容端点都行：DeepSeek / 本地 Ollama / OpenAI …
export OPENAI_BASE_URL=...
export OPENAI_API_KEY=...
export ASGARD_MODEL=...
```

```bash
# 内置新闻 × 全部内置 persona（其中一个会跳过）
asgard brief fixture:hormuz

# 只看某一个人，或直接喂一条新闻链接
asgard brief fixture:hormuz --persona travel-lead
asgard brief https://example.com/some-news
```

## 把 persona 换成你自己

persona 就是一个 YAML 文件，一条事实一行：

```yaml
# personas/travel-lead.yaml
label: 在线旅游平台 · 商业分析师
facts:
  P-role: 在线旅游(OTA)平台商业分析师，做机票业务的经营与数据分析
  P-fuel: 平台主营机票预订，业务营收与出行需求、航空燃油成本高度绑定
  P-cares: AI 数据分析/用户研究工具、出行与消费趋势
  P-ignores: 与旅游、机票经营、数据分析都无关的资讯
```

复制一份，把事实换成你的。输出里的每条判断会标注它用了哪几条（`P-id`），删掉那条事实，相应的判断就消失。

## 常见问题

**和"给 ChatGPT 写一段自我介绍"有什么区别？**
三点：事实和解读分两层，所有人共享同一份中立事实，个性化不会改写新闻本身；每条判断必须引用画像里的具体事实，引不到就不写；无关时跳过，不硬凑。

**它真的比"通用助手 + 人设 prompt"更懂我吗？**
不一定。我们拿公开的反事实 eval 测过（判据发布前登记死）：特异性打平，没赢。稳定赢的是两件事——该跳过时更少硬凑（误报 2/13 vs 4/13），以及每条判断有可查的依据。方法和全部数字在 [`eval/`](eval/README.md)。

**会不会为了显得有用，硬编一个角度？**
这正是 eval 盯着测的（SKIP 纪律）。demo 里第四个人就是真实输出：模型明确说"这跟你无关"。

**我的数据去哪了？**
哪也不去。画像是本地 YAML，模型用你自己配的端点，没有遥测。

**现在能用到什么程度？**
`brief`（折射新闻）和 `eval`（跑测试）能用。交互式建 persona 和长期记忆还没做，画像先手编。

## License

[MIT](LICENSE) · Copyright (c) 2026 rockychan112
