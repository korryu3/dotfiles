#!/usr/bin/env python3
"""session JSONLから指定日のテキストのみを抽出する前処理。

~/.claude/projects/配下のセッションJSONLを直接スキャンし、
エントリのtimestamp（UTC）をローカルTZに変換して当日判定する。
（history.jsonlはCLI専用でDesktop版が書き込まないため、インデックスとして使わない）

/reflect skillのcollect-sessions agentが使用する。
使い方: python3 filter-sessions.py --date YYYY-MM-DD
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ハーネスが注入するシステムテキスト。これを含むuserメッセージは本人の発言ではない
_INJECTED_TAGS = (
    "<command-name>",
    "<command-message>",
    "<local-command-caveat>",
    "<local-command-stdout>",
)

_TS_KEY = '"timestamp":"'


def _first_local_ts_for_date(session_path: Path, date_str: str) -> datetime | None:
    """セッション内で指定日（ローカルTZ）に属する最初のtimestampを返す。なければNone。

    行全体のjson.loadsを避け、timestamp部分だけを文字列で切り出して判定する
    （セッションJSONLは1行が大きいことがあるため）。
    """
    with open(session_path, errors="replace") as f:
        for line in f:
            idx = line.find(_TS_KEY)
            if idx < 0:
                continue
            raw = line[idx + len(_TS_KEY) : idx + len(_TS_KEY) + 32]
            end = raw.find('"')
            if end < 0:
                continue
            try:
                ts = datetime.fromisoformat(raw[:end].replace("Z", "+00:00"))
            except ValueError:
                continue
            local_ts = ts.astimezone()
            if local_ts.strftime("%Y-%m-%d") == date_str:
                return local_ts
    return None


def session_files_for_date(projects_dir: Path, date_str: str) -> list[Path]:
    """指定日（ローカルTZ）の発言を含むセッションJSONLを、当日最初の発言時刻順で返す。"""
    day_start = datetime.strptime(date_str, "%Y-%m-%d").astimezone()
    hits: list[tuple[datetime, Path]] = []
    for session_path in projects_dir.glob("*/*.jsonl"):
        # 当日開始より前に最終更新されたファイルは当日のエントリを含み得ない
        mtime = datetime.fromtimestamp(session_path.stat().st_mtime, tz=timezone.utc)
        if mtime.astimezone() < day_start:
            continue
        first_ts = _first_local_ts_for_date(session_path, date_str)
        if first_ts is not None:
            hits.append((first_ts, session_path))
    hits.sort(key=lambda pair: pair[0])
    return [path for _, path in hits]


def extract_messages(session_path: Path, max_messages: int | None = None) -> list[dict]:
    """session JSONLからuser/assistantのテキスト発言のみを抽出する。"""
    messages: list[dict] = []
    with open(session_path, errors="replace") as f:
        for line in f:
            if max_messages is not None and len(messages) >= max_messages:
                break
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            entry_type = entry.get("type")
            if entry_type not in ("user", "assistant"):
                continue
            if entry.get("isMeta"):
                continue
            content = entry.get("message", {}).get("content")
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                text = "\n".join(
                    item.get("text", "")
                    for item in content
                    if item.get("type") == "text"
                )
            else:
                text = ""
            if entry_type == "user" and any(tag in text for tag in _INJECTED_TAGS):
                continue
            if not text.strip():
                continue
            messages.append({"role": entry_type, "text": text})
    return messages


MAX_MESSAGES_PER_SESSION = 100


def build_report(date_str: str, projects_dir: Path) -> str:
    """指定日のセッション統計と発言テキストを1つのレポート文字列にまとめる。"""
    session_paths = session_files_for_date(projects_dir, date_str)
    sections = []
    for session_path in session_paths:
        sid = session_path.stem
        project = session_path.parent.name
        # 上限+1件読み、上限を超えていたら切り捨てが起きたと判定する
        messages = extract_messages(session_path, max_messages=MAX_MESSAGES_PER_SESSION + 1)
        truncated = len(messages) > MAX_MESSAGES_PER_SESSION
        messages = messages[:MAX_MESSAGES_PER_SESSION]
        if not messages:
            continue
        body = "\n".join(f"[{m['role']}] {m['text']}" for m in messages)
        if truncated:
            body += f"\n（{MAX_MESSAGES_PER_SESSION}メッセージ上限、以降省略）"
        sections.append(f"### session {sid}（project: {project}）\n{body}")
    header = f"当日{len(session_paths)} session中、jsonl現存{len(sections)}件"
    if not sections:
        return f"{header}\n\n## Sessions\n該当なし\n"
    return f"{header}\n\n" + "\n\n".join(sections) + "\n"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                        help="対象日 YYYY-MM-DD（デフォルト: 今日。ローカルTZ基準）")
    parser.add_argument("--projects-dir", type=Path,
                        default=Path.home() / ".claude" / "projects")
    args = parser.parse_args()

    print(build_report(args.date, args.projects_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
