#!/usr/bin/env python3
"""history.jsonl + session JSONLから指定日のテキストのみを抽出する前処理。

/reflect skillのcollect-sessions agentが使用する。
使い方: python3 filter-sessions.py --date YYYY-MM-DD
"""

import json
from datetime import datetime
from pathlib import Path

# ハーネスが注入するシステムテキスト。これを含むuserメッセージは本人の発言ではない
_INJECTED_TAGS = (
    "<command-name>",
    "<command-message>",
    "<local-command-caveat>",
    "<local-command-stdout>",
)


class SchemaError(Exception):
    """データソースのスキーマが想定と一致しない（空データとは区別する真の異常）。"""


def session_ids_for_date(history_path: Path, date_str: str) -> list[str]:
    """history.jsonlから指定日（ローカルTZ）のsessionIdを出現順・重複なしで返す。"""
    ids: list[str] = []
    with open(history_path) as f:
        for lineno, line in enumerate(f, 1):
            entry = json.loads(line)
            if "timestamp" not in entry or "sessionId" not in entry:
                raise SchemaError(
                    f"history.jsonl:{lineno} にtimestamp/sessionIdキーがない。"
                    f"スキーマが変わった可能性: keys={sorted(entry.keys())}"
                )
            local_day = datetime.fromtimestamp(entry["timestamp"] / 1000).strftime("%Y-%m-%d")
            if local_day == date_str and entry["sessionId"] not in ids:
                ids.append(entry["sessionId"])
    return ids


def extract_messages(session_path: Path, max_messages: int | None = None) -> list[dict]:
    """session JSONLからuser/assistantのテキスト発言のみを抽出する。"""
    messages: list[dict] = []
    with open(session_path) as f:
        for line in f:
            if max_messages is not None and len(messages) >= max_messages:
                break
            entry = json.loads(line)
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


def build_report(date_str: str, history_path: Path, projects_dir: Path) -> str:
    """指定日のセッション統計と発言テキストを1つのレポート文字列にまとめる。"""
    session_ids = session_ids_for_date(history_path, date_str)
    found = 0
    sections = []
    for sid in session_ids:
        matches = list(projects_dir.glob(f"*/{sid}.jsonl"))
        if not matches:
            continue
        found += 1
        session_path = matches[0]
        project = session_path.parent.name
        # 上限+1件読み、上限を超えていたら切り捨てが起きたと判定する
        messages = extract_messages(session_path, max_messages=MAX_MESSAGES_PER_SESSION + 1)
        truncated = len(messages) > MAX_MESSAGES_PER_SESSION
        messages = messages[:MAX_MESSAGES_PER_SESSION]
        body = "\n".join(f"[{m['role']}] {m['text']}" for m in messages)
        if truncated:
            body += f"\n（{MAX_MESSAGES_PER_SESSION}メッセージ上限、以降省略）"
        sections.append(f"### session {sid}（project: {project}）\n{body}")
    header = f"当日{len(session_ids)} session中、jsonl現存{found}件"
    if found == 0:
        return f"{header}\n\n## Sessions\n該当なし\n"
    return f"{header}\n\n" + "\n\n".join(sections) + "\n"


def main() -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                        help="対象日 YYYY-MM-DD（デフォルト: 今日。ローカルTZ基準）")
    parser.add_argument("--history-path", type=Path,
                        default=Path.home() / ".claude" / "history.jsonl")
    parser.add_argument("--projects-dir", type=Path,
                        default=Path.home() / ".claude" / "projects")
    args = parser.parse_args()

    try:
        print(build_report(args.date, args.history_path, args.projects_dir))
    except SchemaError as e:
        print(f"スキーマ不一致: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
