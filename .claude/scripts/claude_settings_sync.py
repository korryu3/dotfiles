#!/usr/bin/env python3
"""Claude Code settings.json 同期スクリプト。

~/.claude/settings.json（実ファイル）と dotfiles の settings.base.json を
settings-contract.json の分類（shared / merged / local）に従って同期する。

  apply    base の共有キーを実ファイルへマージする（base が正）
  check    ドリフト（昇格候補・未分類キー）を報告する
  promote  実ファイルの値を base へ昇格する
"""

import fnmatch
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_BASE = REPO_ROOT / ".claude" / "settings.base.json"
DEFAULT_CONTRACT = REPO_ROOT / ".claude" / "settings-contract.json"
DEFAULT_REAL = Path.home() / ".claude" / "settings.json"


class ContractError(Exception):
    pass


# --- 純粋ロジック層 ----------------------------------------------------------


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
    findings = {"unclassified": [], "drift": [], "promotable": [], "missing_in_base": []}
    classified = (
        set(contract["shared"]) | set(contract["merged"]) | set(contract["local"])
    )
    findings["unclassified"] = sorted(k for k in real if k not in classified)
    for key in contract["shared"]:
        if key in base and key in real and real[key] != base[key]:
            findings["drift"].append(key)
        elif key in real and key not in base:
            findings["missing_in_base"].append(key)
    for key, patterns in contract["merged"].items():
        base_sub = base.get(key) or {}
        real_sub = real.get(key) or {}
        for sub, value in real_sub.items():
            if sub in base_sub:
                if base_sub[sub] != value:
                    findings["drift"].append(f"{key}.{sub}")
            elif any(fnmatch.fnmatch(sub, p) for p in patterns):
                findings["promotable"].append(f"{key}.{sub}")
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
            result.setdefault(key, {})[sub] = real[key][sub]
        elif key in contract["merged"]:
            patterns = contract["merged"][key]
            base_sub = dict(result.get(key) or {})
            for s, v in (real[key] or {}).items():
                if s in base_sub or any(fnmatch.fnmatch(s, p) for p in patterns):
                    base_sub[s] = v
            result[key] = base_sub
        else:
            result[key] = real[key]
    return result
