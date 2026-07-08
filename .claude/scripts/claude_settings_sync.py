#!/usr/bin/env python3
"""Claude Code settings.json 同期スクリプト。

~/.claude/settings.json（実ファイル）と dotfiles の settings.base.json を
settings-contract.json の分類（shared / merged / local）に従って同期する。

  apply    base の共有キーを実ファイルへマージする（base が正）
  check    ドリフト（昇格候補・未分類キー）を報告する
  promote  実ファイルの値を base へ昇格する

既知の限界:
  - shared キーのマシン別上書きは表現できない（base が全マシンで勝つ）。
    特定マシンだけ値を変えたい場合の受け皿は無く、実ファイル側の変更は
    drift として警告され続ける。その症状が出たらこの欠落が原因。
"""

import argparse
import datetime
import fnmatch
import json
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_BASE = REPO_ROOT / ".claude" / "settings.base.json"
DEFAULT_CONTRACT = REPO_ROOT / ".claude" / "settings-contract.json"
DEFAULT_REAL = Path.home() / ".claude" / "settings.json"


class ContractError(Exception):
    pass


# --- 純粋ロジック層 ----------------------------------------------------------


def validate_contract(contract):
    """merged の各キーが {"share": [...], "local": [...]} 形式であることを確認する。"""
    for key, rules in contract.get("merged", {}).items():
        if (
            not isinstance(rules, dict)
            or set(rules) != {"share", "local"}
            or not all(isinstance(rules[k], list) for k in ("share", "local"))
        ):
            raise ContractError(
                f'merged.{key} は {{"share": [...], "local": [...]}} 形式で'
                "定義してください（settings-contract.json を新書式に移行すること）"
            )
        if "*" in rules["share"]:
            raise ContractError(
                f'merged.{key} の share に "*" は使えません'
                "（全サブキーを共有するなら shared に分類してください）"
            )


def validate_base(base, contract):
    """base のトップレベルキーが契約で shared / merged に分類されていることを確認する。"""
    allowed = set(contract["shared"]) | set(contract["merged"])
    unknown = sorted(k for k in base if k not in allowed)
    if unknown:
        raise ContractError(
            "base に共有分類でないキーがあります: " + ", ".join(unknown)
            + "（settings-contract.json の shared / merged に分類を追加してください）"
        )


def merge(base, real, contract):
    """apply の結果を新しい dict として返す。base が正、real のローカル分は温存する。"""
    result = json.loads(json.dumps(real))  # deep copy
    for key in contract["shared"]:
        if key in base:
            result[key] = base[key]
    for key in contract["merged"]:
        if key in base:
            merged_value = dict(result.get(key) or {})
            merged_value.update(base[key])
            result[key] = merged_value
    return result


def check(base, real, contract):
    """base と実ファイルのドリフトを種別ごとのリストで返す。"""
    findings = {
        "unclassified": [], "unclassified_sub": [], "drift": [], "promotable": [],
        "missing_in_base": [], "apply_needed": [],
    }
    classified = (
        set(contract["shared"]) | set(contract["merged"]) | set(contract["local"])
    )
    findings["unclassified"] = sorted(k for k in real if k not in classified)
    for key in contract["shared"]:
        if key in base and key in real and real[key] != base[key]:
            findings["drift"].append(key)
        elif key in real and key not in base:
            findings["missing_in_base"].append(key)
    for key, rules in contract["merged"].items():
        base_sub = base.get(key) or {}
        real_sub = real.get(key) or {}
        for sub, value in real_sub.items():
            if sub in base_sub:
                if base_sub[sub] != value:
                    findings["drift"].append(f"{key}.{sub}")
            elif any(fnmatch.fnmatch(sub, p) for p in rules["share"]):
                findings["promotable"].append(f"{key}.{sub}")
            elif not any(fnmatch.fnmatch(sub, p) for p in rules["local"]):
                findings["unclassified_sub"].append(f"{key}.{sub}")
    merged = merge(base, real, contract)
    drifted = {d.split(".", 1)[0] for d in findings["drift"]}
    findings["apply_needed"] = sorted(
        k for k in merged if merged.get(k) != real.get(k) and k not in drifted
    )
    return findings


def promote(base, real, contract, keys):
    """指定キーの real 側の値を base に写した新しい base を返す。"""
    result = json.loads(json.dumps(base))  # deep copy
    for dotted in keys:
        key, _, sub = dotted.partition(".")
        if key in contract["local"]:
            raise ContractError(f"{key} は local 分類のため昇格できません")
        if key not in contract["shared"] and key not in contract["merged"]:
            raise ContractError(
                f"{key} は契約で分類されていません。"
                "先に settings-contract.json に分類を追加してください"
            )
        if key not in real:
            raise ContractError(f"実ファイルに {key} がありません")
        if sub:
            if key not in contract["merged"]:
                raise ContractError(f"{key} はサブキー指定に対応していません（merged キーのみ）")
            if sub not in (real[key] or {}):
                raise ContractError(f"実ファイルに {dotted} がありません")
            rules = contract["merged"][key]
            base_sub = base.get(key) or {}
            if sub not in base_sub and not any(
                fnmatch.fnmatch(sub, p) for p in rules["share"]
            ):
                if any(fnmatch.fnmatch(sub, p) for p in rules["local"]):
                    raise ContractError(
                        f"{dotted} は local 分類です。共有するには settings-contract.json の"
                        " local パターンから外して share に追加してください"
                    )
                raise ContractError(
                    f"{dotted} は未分類です。先に settings-contract.json の"
                    " share / local パターンで分類してください"
                )
            result.setdefault(key, {})[sub] = real[key][sub]
        elif key in contract["merged"]:
            patterns = contract["merged"][key]["share"]
            base_sub = dict(result.get(key) or {})
            for s, v in (real[key] or {}).items():
                if s in base_sub or any(fnmatch.fnmatch(s, p) for p in patterns):
                    base_sub[s] = v
            result[key] = base_sub
        else:
            result[key] = real[key]
    return result


# --- IO 層 --------------------------------------------------------------------


def die(message):
    print(f"エラー: {message}", file=sys.stderr)
    sys.exit(1)


def load_json(path, required=True):
    if not path.exists():
        if required:
            die(f"{path} がありません")
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        die(f"{path} の JSON が壊れています（{e}）。何も書き込まずに中断しました。手動で修正してください")


def write_json_atomic(path, data, backup):
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if backup and path.exists():
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        path.with_name(f"{path.name}.bak-{stamp}").write_text(path.read_text())
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load_contract(path):
    contract = load_json(path)
    try:
        validate_contract(contract)
    except ContractError as e:
        die(str(e))
    return contract


FINDING_LABELS = {
    "unclassified": "未分類キー（settings-contract.json で分類してください）",
    "unclassified_sub": "未分類のサブキー（settings-contract.json の share / local パターンで分類してください）",
    "drift": "base と実ファイルで値が異なるキー（promote で昇格 / apply で base に戻す）",
    "promotable": "昇格候補のサブキー（promote <key.sub> で共有）",
    "missing_in_base": "base に無い共有キー（promote <key> で共有）",
    "apply_needed": "apply が未反映のキー（claude_settings_sync.py apply を実行）",
}


def format_findings(findings):
    lines = []
    for kind, label in FINDING_LABELS.items():
        if findings[kind]:
            lines.append(f"[{label}]")
            lines.extend(f"  - {k}" for k in findings[kind])
    return "\n".join(lines)


def cmd_apply(args):
    contract = load_contract(args.contract)
    base = load_json(args.base)
    if args.real.is_symlink():
        die(f"{args.real} が symlink のままです。実ファイル化の移行を先に実施してください")
    real = load_json(args.real, required=False)
    try:
        validate_base(base, contract)
    except ContractError as e:
        die(str(e))
    merged = merge(base, real, contract)
    if args.real.exists() and merged == real:
        print("変更なし（同期済み）")
        return
    changed = sorted(k for k in merged if real.get(k) != merged.get(k))
    write_json_atomic(args.real, merged, backup=args.real.exists())
    print(f"適用しました: {', '.join(changed)}")
    print("反映には Claude Code の再起動が必要です")


def cmd_check(args):
    contract = load_contract(args.contract)
    base = load_json(args.base)
    real = load_json(args.real, required=False)
    report = format_findings(check(base, real, contract))
    if args.hook:
        if report:
            context = (
                "settings.json のドリフトを検出しました。\n" + report
                + "\n扱い（promote で共有 / settings-contract.json で local 化 / "
                "apply で base に戻す）をユーザーに確認すること。"
            )
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }}, ensure_ascii=False))
    else:
        print(report if report else "ドリフトなし")


def cmd_promote(args):
    contract = load_contract(args.contract)
    base = load_json(args.base)
    real = load_json(args.real)
    try:
        new_base = promote(base, real, contract, args.keys)
    except ContractError as e:
        die(str(e))
    if new_base == base:
        print("変更なし（昇格済み）")
        return
    write_json_atomic(args.base, new_base, backup=False)
    print(f"base に昇格しました: {', '.join(args.keys)}")
    print(f"dotfiles をコミットしてください: {args.base}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--real", type=Path, default=DEFAULT_REAL)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("apply")
    p_check = sub.add_parser("check")
    p_check.add_argument("--hook", action="store_true")
    p_promote = sub.add_parser("promote")
    p_promote.add_argument("keys", nargs="+")
    args = parser.parse_args(argv)
    {"apply": cmd_apply, "check": cmd_check, "promote": cmd_promote}[args.command](args)


if __name__ == "__main__":
    main()
