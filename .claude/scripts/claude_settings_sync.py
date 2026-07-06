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
