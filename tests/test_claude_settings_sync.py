import glob
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / ".claude" / "scripts" / "claude_settings_sync.py"
spec = importlib.util.spec_from_file_location("claude_settings_sync", SCRIPT)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

CONTRACT = {
    "shared": ["model", "hooks"],
    "merged": {
        "env": [],
        "enabledPlugins": ["*@claude-plugins-official"],
        "extraKnownMarketplaces": [],
    },
    # 実在キーと混同しないよう、テスト用の合成キー名を使う
    # （実際の分類は .claude/settings-contract.json が真実源）
    "local": ["localOnlyKey"],
}


class TestValidateBase(unittest.TestCase):
    def test_accepts_base_with_only_classified_keys(self):
        base = {"model": "m1", "env": {"A": "1"}}
        sync.validate_base(base, CONTRACT)  # 例外が出なければOK

    def test_rejects_unknown_base_key(self):
        base = {"model": "m1", "mysteryKey": True}
        with self.assertRaises(sync.ContractError):
            sync.validate_base(base, CONTRACT)

    def test_rejects_local_key_in_base(self):
        # local分類のキーはbaseに置いてはいけない（baseは共有物のみ）
        base = {"localOnlyKey": "on"}
        with self.assertRaises(sync.ContractError):
            sync.validate_base(base, CONTRACT)


class TestMerge(unittest.TestCase):
    def test_shared_key_is_overwritten_by_base(self):
        base = {"model": "base-model"}
        real = {"model": "real-model"}
        result = sync.merge(base, real, CONTRACT)
        self.assertEqual(result["model"], "base-model")

    def test_local_and_unclassified_keys_are_preserved(self):
        base = {"model": "m1"}
        real = {"model": "m1", "localOnlyKey": "on", "newRuntimeKey": True}
        result = sync.merge(base, real, CONTRACT)
        self.assertEqual(result["localOnlyKey"], "on")
        self.assertTrue(result["newRuntimeKey"])

    def test_merged_key_preserves_real_only_subkeys(self):
        base = {"enabledPlugins": {"a@claude-plugins-official": True}}
        real = {"enabledPlugins": {"x@company-market": True}}
        result = sync.merge(base, real, CONTRACT)
        self.assertEqual(
            result["enabledPlugins"],
            {"x@company-market": True, "a@claude-plugins-official": True},
        )

    def test_merged_key_base_wins_for_common_subkeys(self):
        base = {"env": {"FLAG": "base"}}
        real = {"env": {"FLAG": "real", "OTEL_X": "local"}}
        result = sync.merge(base, real, CONTRACT)
        self.assertEqual(result["env"], {"FLAG": "base", "OTEL_X": "local"})

    def test_merged_key_absent_in_base_leaves_real_untouched(self):
        base = {}
        real = {"extraKnownMarketplaces": {"company-market": {"source": {}}}}
        result = sync.merge(base, real, CONTRACT)
        self.assertEqual(result["extraKnownMarketplaces"], real["extraKnownMarketplaces"])

    def test_merge_does_not_mutate_inputs(self):
        base = {"env": {"FLAG": "base"}}
        real = {"env": {"OTEL_X": "local"}}
        sync.merge(base, real, CONTRACT)
        self.assertEqual(real, {"env": {"OTEL_X": "local"}})
        self.assertEqual(base, {"env": {"FLAG": "base"}})


class TestCheck(unittest.TestCase):
    def test_no_findings_when_synced(self):
        base = {"model": "m1", "env": {"FLAG": "1"}}
        real = {"model": "m1", "env": {"FLAG": "1"}, "localOnlyKey": "on"}
        findings = sync.check(base, real, CONTRACT)
        self.assertEqual(
            findings,
            {"unclassified": [], "drift": [], "promotable": [], "missing_in_base": [],
             "apply_needed": []},
        )

    def test_reports_unclassified_top_level_key(self):
        findings = sync.check({}, {"newRuntimeKey": True}, CONTRACT)
        self.assertEqual(findings["unclassified"], ["newRuntimeKey"])

    def test_reports_drift_on_shared_key(self):
        findings = sync.check({"model": "base-m"}, {"model": "real-m"}, CONTRACT)
        self.assertEqual(findings["drift"], ["model"])

    def test_reports_shared_key_missing_in_base(self):
        findings = sync.check({}, {"model": "real-m"}, CONTRACT)
        self.assertEqual(findings["missing_in_base"], ["model"])

    def test_reports_promotable_subkey_matching_pattern(self):
        base = {"enabledPlugins": {"a@claude-plugins-official": True}}
        real = {"enabledPlugins": {
            "a@claude-plugins-official": True,
            "b@claude-plugins-official": True,
        }}
        findings = sync.check(base, real, CONTRACT)
        self.assertEqual(findings["promotable"], ["enabledPlugins.b@claude-plugins-official"])

    def test_silent_on_subkey_not_matching_pattern(self):
        # パターンに一致しないサブキーは報告されない（静かにローカルに留まる）
        base = {"enabledPlugins": {"a@claude-plugins-official": True}}
        real = {
            "enabledPlugins": {"a@claude-plugins-official": True, "x@company-market": True},
            "extraKnownMarketplaces": {"company-market": {"source": {}}},
            "env": {"OTEL_EXPORTER_OTLP_ENDPOINT": "https://example.com"},
        }
        findings = sync.check(base, real, CONTRACT)
        self.assertEqual(findings["promotable"], [])
        self.assertEqual(findings["unclassified"], [])

    def test_reports_drift_on_merged_subkey(self):
        base = {"env": {"FLAG": "base"}}
        real = {"env": {"FLAG": "real"}}
        findings = sync.check(base, real, CONTRACT)
        self.assertEqual(findings["drift"], ["env.FLAG"])

    def test_reports_apply_needed_for_new_base_key(self):
        findings = sync.check({"model": "m1"}, {}, CONTRACT)
        self.assertEqual(findings["apply_needed"], ["model"])

    def test_reports_apply_needed_for_new_base_merged_subkey(self):
        base = {"env": {"A": "1", "B": "2"}}
        real = {"env": {"A": "1"}}
        findings = sync.check(base, real, CONTRACT)
        self.assertEqual(findings["apply_needed"], ["env"])

    def test_apply_needed_empty_when_real_has_extra_local_data(self):
        # real側だけにあるローカルデータはapplyで変化しないので対象外
        base = {"model": "m1"}
        real = {"model": "m1", "localOnlyKey": "on",
                "enabledPlugins": {"x@company-market": True}}
        findings = sync.check(base, real, CONTRACT)
        self.assertEqual(findings["apply_needed"], [])


class TestPromote(unittest.TestCase):
    def test_promote_shared_key(self):
        new_base = sync.promote({}, {"model": "real-m"}, CONTRACT, ["model"])
        self.assertEqual(new_base["model"], "real-m")

    def test_promote_merged_subkey(self):
        new_base = sync.promote(
            {"env": {"A": "1"}}, {"env": {"A": "1", "B": "2"}}, CONTRACT, ["env.B"]
        )
        self.assertEqual(new_base["env"], {"A": "1", "B": "2"})

    def test_promote_merged_whole_key_copies_only_shared_subkeys(self):
        # merged キー丸ごと昇格では、パターン一致とbase既存サブキーのみコピーし、
        # パターン不一致のサブキーはbaseにコピーされない
        base = {"enabledPlugins": {"a@claude-plugins-official": True}}
        real = {"enabledPlugins": {
            "a@claude-plugins-official": True,
            "b@claude-plugins-official": True,
            "x@company-market": True,
        }}
        new_base = sync.promote(base, real, CONTRACT, ["enabledPlugins"])
        self.assertEqual(new_base["enabledPlugins"], {
            "a@claude-plugins-official": True,
            "b@claude-plugins-official": True,
        })

    def test_promote_rejects_local_key(self):
        with self.assertRaises(sync.ContractError):
            sync.promote({}, {"localOnlyKey": "on"}, CONTRACT, ["localOnlyKey"])

    def test_promote_rejects_unclassified_key(self):
        with self.assertRaises(sync.ContractError):
            sync.promote({}, {"newRuntimeKey": True}, CONTRACT, ["newRuntimeKey"])

    def test_promote_rejects_missing_key_in_real(self):
        with self.assertRaises(sync.ContractError):
            sync.promote({}, {}, CONTRACT, ["model"])

    def test_promote_rejects_subkey_on_shared_key(self):
        with self.assertRaises(sync.ContractError):
            sync.promote({}, {"model": "m"}, CONTRACT, ["model.sub"])

    def test_promote_does_not_mutate_inputs(self):
        base = {"env": {"A": "1"}}
        real = {"env": {"A": "1", "B": "2"}}
        sync.promote(base, real, CONTRACT, ["env.B"])
        self.assertEqual(base, {"env": {"A": "1"}})

    def test_promote_dotted_subkey_matching_pattern_is_allowed(self):
        base = {"enabledPlugins": {"a@claude-plugins-official": True}}
        real = {"enabledPlugins": {
            "a@claude-plugins-official": True,
            "b@claude-plugins-official": True,
        }}
        new_base = sync.promote(base, real, CONTRACT, ["enabledPlugins.b@claude-plugins-official"])
        self.assertTrue(new_base["enabledPlugins"]["b@claude-plugins-official"])

    def test_promote_dotted_subkey_not_matching_pattern_is_rejected(self):
        base = {"enabledPlugins": {"a@claude-plugins-official": True}}
        real = {"enabledPlugins": {
            "a@claude-plugins-official": True,
            "x@company-market": True,
        }}
        with self.assertRaises(sync.ContractError):
            sync.promote(base, real, CONTRACT, ["enabledPlugins.x@company-market"])

    def test_promote_dotted_subkey_with_empty_patterns_is_allowed(self):
        # パターンリストが空のmergedキー（env）は従来どおり昇格できる
        new_base = sync.promote({"env": {"A": "1"}}, {"env": {"A": "1", "B": "2"}}, CONTRACT, ["env.B"])
        self.assertEqual(new_base["env"], {"A": "1", "B": "2"})

    def test_promote_dotted_subkey_already_in_base_is_allowed(self):
        # base所有済みサブキーはパターン不一致でも値更新できる
        base = {"enabledPlugins": {"legacy@old-market": False}}
        real = {"enabledPlugins": {"legacy@old-market": True}}
        new_base = sync.promote(base, real, CONTRACT, ["enabledPlugins.legacy@old-market"])
        self.assertTrue(new_base["enabledPlugins"]["legacy@old-market"])


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.base_p = self.dir / "base.json"
        self.contract_p = self.dir / "contract.json"
        self.real_p = self.dir / "real.json"
        self.contract_p.write_text(json.dumps(CONTRACT))

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *argv):
        return subprocess.run(
            [sys.executable, str(SCRIPT),
             "--base", str(self.base_p),
             "--contract", str(self.contract_p),
             "--real", str(self.real_p), *argv],
            capture_output=True, text=True)

    def backups(self):
        return glob.glob(str(self.dir / "real.json.bak-*"))

    def test_apply_creates_real_from_base_when_missing(self):
        self.base_p.write_text(json.dumps({"model": "m1"}))
        result = self.run_cli("apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.real_p.read_text()), {"model": "m1"})
        self.assertEqual(self.backups(), [])  # 新規作成時はバックアップ不要

    def test_apply_is_idempotent_and_skips_backup_when_no_change(self):
        self.base_p.write_text(json.dumps({"model": "m1"}))
        self.real_p.write_text(json.dumps({"model": "m1"}))
        result = self.run_cli("apply")
        self.assertEqual(result.returncode, 0)
        self.assertIn("変更なし", result.stdout)
        self.assertEqual(self.backups(), [])

    def test_apply_creates_backup_when_changing(self):
        self.base_p.write_text(json.dumps({"model": "new"}))
        self.real_p.write_text(json.dumps({"model": "old"}))
        result = self.run_cli("apply")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(self.real_p.read_text())["model"], "new")
        self.assertEqual(len(self.backups()), 1)

    def test_apply_refuses_symlink_real(self):
        self.base_p.write_text(json.dumps({"model": "m1"}))
        target = self.dir / "target.json"
        target.write_text(json.dumps({"model": "old"}))
        self.real_p.symlink_to(target)
        result = self.run_cli("apply")
        self.assertEqual(result.returncode, 1)
        self.assertIn("symlink", result.stderr)
        self.assertEqual(json.loads(target.read_text())["model"], "old")  # 未変更

    def test_apply_aborts_on_broken_json_without_write(self):
        self.base_p.write_text(json.dumps({"model": "m1"}))
        self.real_p.write_text("{broken")
        result = self.run_cli("apply")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.real_p.read_text(), "{broken")  # 未変更
        self.assertEqual(self.backups(), [])

    def test_apply_rejects_contract_violation_in_base(self):
        self.base_p.write_text(json.dumps({"mysteryKey": True}))
        self.real_p.write_text(json.dumps({}))
        result = self.run_cli("apply")
        self.assertEqual(result.returncode, 1)
        self.assertIn("mysteryKey", result.stderr)

    def test_check_hook_is_silent_when_synced(self):
        self.base_p.write_text(json.dumps({"model": "m1"}))
        self.real_p.write_text(json.dumps({"model": "m1"}))
        result = self.run_cli("check", "--hook")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_check_hook_emits_session_start_json_on_findings(self):
        self.base_p.write_text(json.dumps({"model": "base-m"}))
        self.real_p.write_text(json.dumps({"model": "real-m"}))
        result = self.run_cli("check", "--hook")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(
            payload["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn("model", payload["hookSpecificOutput"]["additionalContext"])

    def test_check_human_output(self):
        self.base_p.write_text(json.dumps({}))
        self.real_p.write_text(json.dumps({"newRuntimeKey": True}))
        result = self.run_cli("check")
        self.assertEqual(result.returncode, 0)
        self.assertIn("newRuntimeKey", result.stdout)

    def test_promote_writes_base_without_backup(self):
        self.base_p.write_text(json.dumps({}))
        self.real_p.write_text(json.dumps({"model": "real-m"}))
        result = self.run_cli("promote", "model")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(self.base_p.read_text())["model"], "real-m")
        self.assertEqual(glob.glob(str(self.dir / "base.json.bak-*")), [])

    def test_promote_contract_error_exits_1(self):
        self.base_p.write_text(json.dumps({}))
        self.real_p.write_text(json.dumps({"localOnlyKey": "on"}))
        result = self.run_cli("promote", "localOnlyKey")
        self.assertEqual(result.returncode, 1)
        self.assertIn("local", result.stderr)

    def test_check_hook_emits_json_when_apply_needed(self):
        self.base_p.write_text(json.dumps({"model": "m1"}))
        self.real_p.write_text(json.dumps({}))
        result = self.run_cli("check", "--hook")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn("apply", payload["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
