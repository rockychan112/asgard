# 定时出日报（不依赖任何 agent）

`asgard daily` 加上系统自带的定时器（crontab / launchd），就能每天自动收到一份日报。
这条路不需要 Claude Code / Codex / Cursor，任何一台能跑 Python 的机器都行。

## 前提

1. 装好命令行：`uv venv && uv pip install -e .`，确认 `asgard daily --help` 能跑
2. 资料和信源就位：`~/.asgard/profile.yaml`、`~/.asgard/feeds.yaml`（样例见 [`examples/`](../examples/)）
3. 模型端点的三个环境变量：`OPENAI_BASE_URL` / `OPENAI_API_KEY` / `ASGARD_MODEL`

定时器**不会加载你的 shell 配置**——`.zshrc` 里 export 的变量在 cron 里全都不存在。
把三个变量单独放一个文件，比如 `~/.asgard/env`：

```sh
export OPENAI_BASE_URL=https://api.deepseek.com
export OPENAI_API_KEY=sk-...
export ASGARD_MODEL=deepseek-chat
```

记得 `chmod 600 ~/.asgard/env`，并且别把它提交进任何仓库。

## crontab（Linux / macOS 通用）

`crontab -e`，加一行（每天早上 8 点）：

```cron
0 8 * * * . "$HOME/.asgard/env" && /绝对路径/到/asgard daily >> "$HOME/.asgard/asgard.log" 2>&1
```

- `asgard` 要写绝对路径（`which asgard` 查），cron 的 PATH 很短
- 日报默认落在 `~/.asgard/briefs/YYYY-MM-DD.md`（当前目录没有 `briefs/` 时）
- 退出码 `2` 表示当天什么都没处理成（信源全挂、或逐条全部失败）——日报文件仍然会写，
  里面写明了原因；想收到告警可以在命令后接 `|| 你的通知命令`

## launchd（macOS 推荐）

macOS 上 cron 在机器睡眠时会直接错过，launchd 会在唤醒后补跑。
存成 `~/Library/LaunchAgents/com.asgard.daily.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.asgard.daily</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/sh</string><string>-c</string>
    <string>. "$HOME/.asgard/env" &amp;&amp; /绝对路径/到/asgard daily</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>/tmp/asgard-daily.log</string>
  <key>StandardErrorPath</key><string>/tmp/asgard-daily.log</string>
</dict></plist>
```

```sh
launchctl load ~/Library/LaunchAgents/com.asgard.daily.plist
launchctl start com.asgard.daily   # 不等明早，立刻试跑一次
```

## 变体：定时让 agent 跑 skill

装了 [asgard-daily skill](../skills/asgard-daily/SKILL.md) 的话，也可以定时叫 headless agent
（agent 检测到本机有 CLI 时会优先调用它）：

```cron
0 8 * * * cd 你的工作区 && claude -p "运行 asgard-daily skill 生成今日简报" >> "$HOME/.asgard/asgard.log" 2>&1
```

宿主 agent 自带定时功能时（T1），优先用宿主的，配置更简单也更可见。

无论哪条路：没有遥测，没有云端，一切都在你机器上。

---

## English (short)

`asgard daily` + your OS scheduler = a daily brief, no agent involved.

1. Install the CLI; put `profile.yaml` and `feeds.yaml` under `~/.asgard/` (samples in `examples/`)
2. Put `OPENAI_BASE_URL` / `OPENAI_API_KEY` / `ASGARD_MODEL` in `~/.asgard/env` — cron does **not** load your shell rc; `chmod 600` it
3. crontab: `0 8 * * * . "$HOME/.asgard/env" && /abs/path/to/asgard daily >> "$HOME/.asgard/asgard.log" 2>&1`
4. On macOS prefer launchd (it catches up after sleep) — plist above
5. Exit code `2` = nothing could be processed today (all feeds or all items failed); the brief file is still written and says why. No telemetry either way.
