"""`asgard schedule print` — turn the config's schedule declaration into
copy-paste crontab / launchd snippets. Print only: installing a scheduled
task stays an explicit human (or consented-agent) action, never a side effect.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from .config import Config

_CRON_DOW = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}
_LAUNCHD_DOW = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}


def print_schedule(config_path: str | None = None) -> int:
    cfg = Config.load(config_path)
    problems = cfg.problems()
    if problems:
        sys.exit("config 有问题，先修再生成：\n  - " + "\n  - ".join(problems))

    sch = cfg.schedule
    hour, minute = (int(x) for x in sch.time.split(":"))
    binary = shutil.which("asgard") or str((Path(sys.argv[0]).resolve()))
    weekly = sch.cadence == "weekly"

    dow = _CRON_DOW[sch.weekday] if weekly else "*"
    print(f"# —— crontab（`crontab -e` 加入这行；{'每周' + sch.weekday if weekly else '每天'} {sch.time}）——")
    print(f'{minute} {hour} * * {dow} . "$HOME/.asgard/env" && {binary} daily >> "$HOME/.asgard/asgard.log" 2>&1')

    cal = f"<key>Hour</key><integer>{hour}</integer><key>Minute</key><integer>{minute}</integer>"
    if weekly:
        cal = f"<key>Weekday</key><integer>{_LAUNCHD_DOW[sch.weekday]}</integer>" + cal
    print(f"""
# —— launchd（macOS 推荐，睡眠错过会补跑）——
# 存成 ~/Library/LaunchAgents/com.asgard.daily.plist 然后：
#   launchctl load ~/Library/LaunchAgents/com.asgard.daily.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.asgard.daily</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/sh</string><string>-c</string>
    <string>. "$HOME/.asgard/env" &amp;&amp; {binary} daily</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>{cal}</dict>
  <key>StandardOutPath</key><string>/tmp/asgard-daily.log</string>
  <key>StandardErrorPath</key><string>/tmp/asgard-daily.log</string>
</dict></plist>""")
    return 0
