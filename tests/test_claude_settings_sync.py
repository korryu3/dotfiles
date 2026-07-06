import importlib.util
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
            {"unclassified": [], "drift": [], "promotable": [], "missing_in_base": []},
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


if __name__ == "__main__":
    unittest.main()
