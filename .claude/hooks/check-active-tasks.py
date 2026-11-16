#!/usr/bin/env python3
"""SessionStart hook: notes/active-tasks.md の節のうち、整理の候補を知らせる。

検出だけを行い、ファイルは書き換えない。整理するかはClaudeがユーザーに確認する。
"""
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

STALE_DAYS = 30
LARGE_BYTES = 10_000
DONE_WORDS = ("完了",)

sys.stdin.read()

try:
    project_id = subprocess.run(
        [str(Path.home() / ".claude/scripts/project-id.sh")],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
except (OSError, subprocess.CalledProcessError):
    sys.exit(0)

path = Path.home() / ".claude/context" / project_id / "notes/active-tasks.md"
if not path.is_file():
    sys.exit(0)

# 節 = "## " で始まる見出しから次の "## " まで
sections: list[tuple[str, str]] = []
current = None
body: list[str] = []
for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
    if line.startswith("## "):
        if current is not None:
            sections.append((current, "\n".join(body)))
        current, body = line[3:].strip(), []
    elif current is not None:
        body.append(line)
if current is not None:
    sections.append((current, "\n".join(body)))

today = datetime.date.today()
rows = []
for title, text in sections:
    reasons = []
    # 見出しの中で最も新しい日付をその節の更新日とみなす
    dates = []
    for y, m, d in re.findall(r"(\d{4})-(\d{2})-(\d{2})", title):
        try:
            dates.append(datetime.date(int(y), int(m), int(d)))
        except ValueError:
            pass
    if dates:
        age = (today - max(dates)).days
        if age >= STALE_DAYS:
            reasons.append(f"{age}日更新なし")
    size = len(text.encode("utf-8"))
    if size >= LARGE_BYTES:
        reasons.append(f"{size // 1000}KB")
    if any(w in title for w in DONE_WORDS):
        reasons.append("見出しに完了")
    if reasons:
        rows.append(f"- {title[:60]}: {'、'.join(reasons)}")

if not rows:
    sys.exit(0)

message = (
    f"[active-tasks整理候補] {path} に整理候補の節が{len(rows)}件あります"
    f"（基準: 見出しの日付から{STALE_DAYS}日以上／{LARGE_BYTES // 1000}KB以上／見出しに完了）。\n"
    + "\n".join(rows)
)
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": message,
    }
}, ensure_ascii=False))
