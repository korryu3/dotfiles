#!/usr/bin/env python3
"""PRレビューコメントのアンカーがunified diff上でコメント可能な位置かを検証する。

Usage:
    python3 validate_anchors.py <diff-file> < anchors.json

anchors.json: JSON配列 [{"path": str, "line": int?, "side": ("RIGHT"|"LEFT")?}]
    - side省略時はRIGHT扱い
    - line省略時はFILEレベルスレッド用として「pathがdiffに含まれるか」のみ判定

判定ルール:
    - RIGHT: pathをdiffのb/側と照合し、lineが新ファイル行番号でハンク範囲内にあること。
      削除ファイルへのRIGHTアンカーは常にinvalid
    - LEFT: pathをdiffのa/側と照合し、lineが旧ファイル行番号でハンク範囲内にあること。
      新規追加ファイルへのLEFTアンカーは常にinvalid

出力: 1アンカー1行の判定結果（valid/invalidと理由）をstdoutへ
Exit code: 全valid=0 / invalid含む=1 / 入力不正（diffファイル不読・JSONパース不能等）=2
"""

import json
import re
import sys

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
DIFF_GIT_RE = re.compile(r"^diff --git a/(.*) b/(.*)$")


def parse_diff(text):
    """diffテキストをファイル単位のレコードにパースする。

    Returns: list of {
        "old_path": str|None,  # a/側パス（新規ファイルはNone）
        "new_path": str|None,  # b/側パス（削除ファイルはNone）
        "left_ranges": [(start, end)],   # 旧ファイル行番号のハンク範囲（両端含む）
        "right_ranges": [(start, end)],  # 新ファイル行番号のハンク範囲（両端含む）
    }
    """
    files = []
    current = None
    for line in text.splitlines():
        m = DIFF_GIT_RE.match(line)
        if m:
            current = {
                "old_path": m.group(1),
                "new_path": m.group(2),
                "left_ranges": [],
                "right_ranges": [],
            }
            files.append(current)
            continue
        if current is None:
            continue
        if line.startswith("--- "):
            target = line[4:].split("\t")[0]
            current["old_path"] = None if target == "/dev/null" else target.removeprefix("a/")
            continue
        if line.startswith("+++ "):
            target = line[4:].split("\t")[0]
            current["new_path"] = None if target == "/dev/null" else target.removeprefix("b/")
            continue
        m = HUNK_RE.match(line)
        if m:
            old_start = int(m.group(1))
            old_count = int(m.group(2)) if m.group(2) is not None else 1
            new_start = int(m.group(3))
            new_count = int(m.group(4)) if m.group(4) is not None else 1
            if old_count > 0:
                current["left_ranges"].append((old_start, old_start + old_count - 1))
            if new_count > 0:
                current["right_ranges"].append((new_start, new_start + new_count - 1))
    return files


def find_file(files, path, side):
    key = "new_path" if side == "RIGHT" else "old_path"
    for f in files:
        if f[key] == path:
            return f
    return None


def validate_anchor(files, anchor):
    """1アンカーを検証し、(is_valid, label, reason) を返す。"""
    path = anchor["path"]
    line = anchor.get("line")
    side = anchor.get("side", "RIGHT")

    if line is None:
        # FILEレベルスレッド: pathがdiffに含まれるか（どちらの側でも）のみ判定
        label = f"{path} (FILE)"
        for f in files:
            if path in (f["old_path"], f["new_path"]):
                return True, label, ""
        return False, label, "pathがdiffに含まれない"

    label = f"{path}:{line} ({side})"
    f = find_file(files, path, side)
    if f is None:
        # 反対側にだけ存在する場合は新規/削除ファイルとして具体的な理由を返す
        other = find_file(files, path, "LEFT" if side == "RIGHT" else "RIGHT")
        if other is not None:
            if side == "RIGHT":
                return False, label, "削除ファイルへのRIGHTアンカーは不可"
            return False, label, "新規追加ファイルへのLEFTアンカーは不可"
        side_desc = "b/側" if side == "RIGHT" else "a/側"
        return False, label, f"pathがdiffの{side_desc}に含まれない"

    ranges = f["right_ranges"] if side == "RIGHT" else f["left_ranges"]
    for start, end in ranges:
        if start <= line <= end:
            return True, label, ""
    ranges_str = ", ".join(f"{s}..{e}" for s, e in ranges) or "なし"
    return False, label, f"lineがハンク範囲外（{side}側の範囲: {ranges_str}）"


def main():
    if len(sys.argv) != 2:
        print("usage: validate_anchors.py <diff-file> < anchors.json", file=sys.stderr)
        return 2
    try:
        with open(sys.argv[1], encoding="utf-8") as fp:
            diff_text = fp.read()
    except OSError as e:
        print(f"input error: diffファイルを読めない: {e}", file=sys.stderr)
        return 2
    try:
        anchors = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"input error: anchors JSONをパースできない: {e}", file=sys.stderr)
        return 2
    if not isinstance(anchors, list):
        print("input error: anchorsはJSON配列であること", file=sys.stderr)
        return 2
    for i, anchor in enumerate(anchors):
        if not isinstance(anchor, dict) or not isinstance(anchor.get("path"), str):
            print(f"input error: anchors[{i}]に文字列のpathがない", file=sys.stderr)
            return 2
        if "line" in anchor and not isinstance(anchor["line"], int):
            print(f"input error: anchors[{i}].lineは整数であること", file=sys.stderr)
            return 2
        if anchor.get("side", "RIGHT") not in ("RIGHT", "LEFT"):
            print(f"input error: anchors[{i}].sideはRIGHTかLEFTであること", file=sys.stderr)
            return 2

    files = parse_diff(diff_text)
    has_invalid = False
    for anchor in anchors:
        is_valid, label, reason = validate_anchor(files, anchor)
        if is_valid:
            print(f"valid: {label}")
        else:
            has_invalid = True
            print(f"invalid: {label} — {reason}")
    return 1 if has_invalid else 0


if __name__ == "__main__":
    sys.exit(main())
