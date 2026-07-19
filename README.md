<div align="center">

# Asgard —— 你的私人「情报」官

**每条资讯，只解读与「你」有关的利害关系和行动指引。**

<a href="https://rockychan112.github.io/asgard/"><b>在线 Demo</b></a> · <a href="./README.en.md">English</a>

<img alt="status: pre-alpha" src="https://img.shields.io/badge/status-pre--alpha-d97706"> <img alt="python 3.11+" src="https://img.shields.io/badge/python-3.11+-3b82f6"> <img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-10b981">

</div>

每天的资讯都在讲“世界发生了什么”，没有一条告诉你“这跟你有什么关系、你该干嘛”。Asgard 读你的资料，把一条新闻折射成你的利害和这周能做的动作；跟你无关的，直接跳过。

同一条新闻，四个人，四种结果：

[![同一条新闻折射给四个身份：三条各自的利害与行动，第四条诚实跳过](design/hero.png)](https://rockychan112.github.io/asgard/)

<p align="center"><sub>三张卡各有各的利害和动作，每条都标注依据；第四张，跳过　·　<a href="https://rockychan112.github.io/asgard/">▶ 可交互版：12 条新闻随机换，还能点掉一行资料，看真实引擎怎么重判</a></sub></p>

## 跟其它工具的差别

| | 新闻 App | ChatGPT+人设 | Asgard |
|---|---|---|---|
| 同一条新闻给你什么 | 人人一份摘要 | 一段泛泛分析 | 你的利害+能做的事 |
| 和你无关时 | 照样推给你 | 硬找角度 | 直说跳过 |
| 判断依据 | 黑盒 | 说不清 | 每条标出处，可查 |
| 你的资料 | 平台猜的 | 一段散文 | 一个文件，逐条可改 |
| 数据在哪 | 平台服务器 | 聊天记录 | 全在本地 |

## 装进你的 agent，每天收一份

Asgard 可以当作 skill 装进 Claude Code / Codex / Cursor 这类 agent：每天自动读你订阅的新闻源，把一份日报落到 `briefs/2026-07-15.md`。

```bash
npx skills add https://github.com/rockychan112/asgard
```

三步：装 skill → 对 agent 说一句「asgard 今日简报」——首次运行它会自动引导你完成安装（clone 仓库、访谈式建资料、配模型端点，真跑通一次才算装好）→ 给 agent 设一个每日任务（宿主没有定时功能，就每天说一句，一样能用）。

skill 装进去的是**协议**——资料契约、引用纪律、跳过规则——不是一段魔法提示词。

两点说在前面：

- 本机装了 `asgard` 命令行时，skill 会优先调用它（引用校验硬执行）；没装就由你的 agent 直接按协议跑，日报头部会标 `engine: llm`——诚实降级，仓库里的考卷只为命令行路径背书。
- 当天全部无关时也会生成日报，内容是「今天没有值得你看的，检查了 N 条」。这是它在干活，不是坏了。

不想经过 agent？`asgard daily` 一条命令做同一件事（拉信源 → 逐条折射 → 落日报），配上系统定时就是纯本地方案：见 [docs/cron.md](docs/cron.md)。

## 上手

```bash
git clone https://github.com/rockychan112/asgard && cd asgard
uv venv && uv pip install -e .   # 没有 uv：python3 -m venv .venv && .venv/bin/pip install -e .

# 任何 OpenAI 兼容端点都行：DeepSeek / 本地 Ollama / OpenAI …
export OPENAI_BASE_URL=...
export OPENAI_API_KEY=...
export ASGARD_MODEL=...
```

```bash
# 内置新闻 × 全部内置身份（其中有人会跳过）
asgard brief fixture:hormuz

# 只看某一个人，或直接喂一条新闻链接
asgard brief fixture:hormuz --persona travel-lead
asgard brief https://example.com/some-news

# 整份日报：按信源列表拉当日新闻，逐条折射，落到 briefs/
asgard daily --profile examples/profile.sample.yaml --feeds examples/feeds.example.yaml

# 每天自动收：写一份 config（语言 zh/en + 格式 md/html + 几点跑，样例 examples/config.sample.yaml）
asgard doctor           # 体检到全绿 = 配置完成
asgard schedule print   # 生成 crontab / launchd 片段，复制安装
```

## 换成你自己的资料

Asgard 认识你的方式，是一份资料文件：一行一条信息，行首是编号。

```yaml
# personas/travel-lead.yaml
label: 在线旅游平台 · 商业分析师
facts:
  P-role: 在线旅游(OTA)平台商业分析师，做机票业务的经营与数据分析
  P-fuel: 平台主营机票预订，业务营收与出行需求、航空燃油成本高度绑定
  P-cares: AI 数据分析/用户研究工具、出行与消费趋势
  P-ignores: 与旅游、机票经营、数据分析都无关的资讯
```

复制一份，把每行换成你的情况。输出里的每条判断都会标注它用了哪几行（就是 `P-` 开头的编号）；删掉某一行，靠它撑着的判断就会消失。

## 常见问题

**跟“给 ChatGPT 写一段自我介绍”有什么区别？**

- 新闻事实所有人共用同一份，它只解读、不改写，不会为了讨好你扭曲事情本身
- 每条判断必须标注用了你资料里的哪几行，标不出来就不写
- 判断你无关时直接跳过，不硬找角度

**你们说“测过”，是怎么测的？**

给它出了一份公开考卷：改掉资料里的一行，只有靠这行撑着的判断应该跟着变——变多了是瞎编，不变是没在用你的资料。判分标准在动手前就定死并公开，防止事后挑好看的说。

结果也如实公布：跟“把资料整段贴给 ChatGPT”比，个性化的准头**打平，没赢**；稳定赢的是两件事——该跳过时更少硬凑（误报 2/13 对 4/13），以及每条判断有出处可查。全部数字在 [`eval/`](eval/README.md)。

**它会不会为了显得有用，硬编一个角度？**

这正是上面考卷盯着测的。demo 里的跳过卡都是真实输出，谁跳过随新闻换：地缘冲突时是婚礼摄影师，相机降价时换成另外三个人。

**我的数据去哪了？**

- 资料是你电脑上的一个文件
- 模型用你自己配的端点
- 没有任何遥测上报

**现在能用到什么程度？**

`brief`（折射单条新闻）、`daily`（按信源列表出整份日报，md/html 可选、可配 cron 定时）、`doctor`（配置体检）、`eval`（跑考卷）、skill 每日简报（见上）能用；推送到 IM 和长期记忆还没做。

## License

[MIT](LICENSE) · Copyright (c) 2026 rockychan112
