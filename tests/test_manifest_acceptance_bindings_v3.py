"""Keyless SYNTHETIC_TEST_ONLY binding checks, not acceptance/authentication.

Run directly with unittest to avoid package __init__, conftest and historical
fixtures. All seals are ordinary software data; no signed message or carrier.
"""

from copy import deepcopy
import importlib.util
import inspect
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / "src" / "forecast_trust_core"
NAMESPACE = "_ma3_keyless_binding_tests"
package = types.ModuleType(NAMESPACE)
package.__path__ = [str(SOURCE)]
sys.modules[NAMESPACE] = package


def load_component(name):
    spec = importlib.util.spec_from_file_location(f"{NAMESPACE}.{name}", SOURCE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


canonical = load_component("canonical")
core = load_component("core")
load_component("_checks")
gate = load_component("claim_authority_contract_gate_v1")
component = load_component("architecture_compression_v1")


def ref(name, digest="a" * 64):
    return {"object_id": f"synthetic-test-only:{name}", "content_sha256": digest}


def object_ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def subject(value="test-value", semantic_id=None):
    return canonical.seal_object(
        {"schema_version": "SYNTHETIC_TEST_ONLY", "value": value},
        object_type="SyntheticBindingSubject",
        stable_context="SYNTHETIC_TEST_ONLY",
        semantic_id=semantic_id,
    )


def reseal(obj):
    return canonical.seal_object(
        {k: deepcopy(v) for k, v in obj.items() if k not in {"object_type", "object_id", "payload_sha256", "content_sha256"}},
        object_type="ManifestAcceptance",
        stable_context="SYNTHETIC_TEST_ONLY",
    )


def inputs():
    manifest = subject()
    root, rule = ref("root"), ref("rule")
    reports = [ref(f"report-{i}") for i in range(5)]
    acceptance = canonical.seal_object(
        {
            "schema_version": "3.0",
            "candidate_manifest_ref": object_ref(manifest),
            "bootstrap_governance_root_ref": deepcopy(root),
            "acceptance_rule_ref": deepcopy(rule),
            "authority_ref": deepcopy(root),
            "required_validation_report_refs": deepcopy(reports),
            "decision": "ACCEPT", "reason_codes": [], "blocking_finding_refs": [],
            "signature_ref": ref("unresolved-reference-only"),
        },
        object_type="ManifestAcceptance",
        stable_context="SYNTHETIC_TEST_ONLY",
    )
    return {
        "manifest": manifest, "acceptance": acceptance,
        "bootstrap_root_ref": root, "acceptance_rule_ref": rule,
        "required_validation_report_refs": reports,
    }


class ManifestAcceptanceV3BindingTests(unittest.TestCase):
    def run_check(self, data):
        before = deepcopy(data)
        rows = component.check_manifest_acceptance_v3_bindings(**data)
        self.assertEqual(data, before)
        self.assertIsInstance(rows, tuple)
        self.assertTrue(all(isinstance(row, core.Check) for row in rows))
        self.assertFalse(isinstance(rows, core.Validation))
        self.assertFalse(hasattr(rows, "valid"))
        return rows

    def assert_single_fail(self, data, check_id, reason):
        self.assertEqual(self.run_check(data), (core.Check(f"acceptance_v3.{check_id}", "FAIL", reason),))

    def assert_relation_failure(self, data, check_id, reason):
        rows = self.run_check(data)
        self.assertEqual(len(rows), 5)
        self.assertEqual([row for row in rows if row.status != "PASS"], [core.Check(f"acceptance_v3.{check_id}", "FAIL", reason)])
        self.assertTrue(all(row.reason_code == "OK" for row in rows if row.status == "PASS"))

    def test_matching_inputs_produce_five_raw_checks(self):
        expected = tuple(core.Check(f"acceptance_v3.{name}", "PASS", "OK") for name in ["manifest", "bootstrap", "rule", "reports", "decision"])
        for container in [list, tuple]:
            with self.subTest(container=container):
                data = inputs()
                data["required_validation_report_refs"] = container(data["required_validation_report_refs"])
                self.assertEqual(self.run_check(data), expected)
        signature = inspect.signature(component.check_manifest_acceptance_v3_bindings)
        self.assertEqual(list(signature.parameters), ["manifest", "acceptance", "bootstrap_root_ref", "acceptance_rule_ref", "required_validation_report_refs"])
        self.assertTrue(all(p.kind == inspect.Parameter.KEYWORD_ONLY for p in list(signature.parameters.values())[2:]))

    def test_d137_contract_failures_stop_before_binding(self):
        variants = []
        for version in ["2.0", "3.1"]:
            a = inputs()["acceptance"]
            a["schema_version"] = version
            variants.append(reseal(a))
        a = inputs()["acceptance"]
        a["content_sha256"] = "0" * 64
        variants.append(a)
        for field, value in [
            ("signature_ref", {**ref("bad"), "extra": "bad"}),
            ("authority_ref", ref("wrong-root")),
            ("decision", []), ("reason_codes", ["Z", "A"]),
            ("blocking_finding_refs", [ref("blocker")]),
            ("required_validation_report_refs", list(reversed(inputs()["required_validation_report_refs"]))),
        ]:
            a = inputs()["acceptance"]
            a[field] = value
            variants.append(reseal(a))
        variants.extend([None, [], {}, "bad", 3])
        for acceptance in variants:
            with self.subTest(acceptance=acceptance):
                data = inputs()
                # Bad later inputs must not replace the first contract failure.
                data.update(acceptance=acceptance, manifest=None, bootstrap_root_ref={})
                self.assert_single_fail(data, "contract", "ACCEPTANCE_CONTRACT_INVALID")

    def test_invalid_manifest_is_one_failure_not_key_error(self):
        variants = [None, [], "bad", 1, {}, {"value": "no-identity"}]
        obj = subject()
        del obj["object_id"]
        variants.append(obj)
        obj = subject()
        obj["value"] = "tampered"
        variants.append(obj)
        for manifest in variants:
            with self.subTest(manifest=manifest):
                data = inputs()
                data.update(manifest=manifest, bootstrap_root_ref={})
                self.assert_single_fail(data, "manifest_seal", "INVALID_MANIFEST_SEAL")

    def test_actual_manifest_identity_and_content_are_bound(self):
        data = inputs()
        data["manifest"] = subject(semantic_id="synthetic-test-only:other-subject")
        self.assert_relation_failure(data, "manifest", "MANIFEST_HASH_MISMATCH")
        data = inputs()
        original_id = data["manifest"]["object_id"]
        data["manifest"] = subject("changed-value", semantic_id=original_id)
        self.assert_relation_failure(data, "manifest", "MANIFEST_HASH_MISMATCH")

    def test_root_and_rule_full_pair_mismatches(self):
        for field, check_id, reason in [
            ("bootstrap_root_ref", "bootstrap", "BOOTSTRAP_ROOT_MISMATCH"),
            ("acceptance_rule_ref", "rule", "ACCEPTANCE_RULE_MISMATCH"),
        ]:
            for part, value in [("object_id", "synthetic-test-only:other"), ("content_sha256", "b" * 64)]:
                with self.subTest(field=field, part=part):
                    data = inputs()
                    data[field][part] = value
                    self.assert_relation_failure(data, check_id, reason)

    def test_malformed_root_and_rule_controls(self):
        bad_refs = [None, [], "bad", 3, {}, {"object_id": "missing-hash"}, {**ref("x"), "extra": "bad"}, ref("bad id"), ref("x", "A" * 64), ref("x", 3)]
        for field in ["bootstrap_root_ref", "acceptance_rule_ref"]:
            for bad in bad_refs:
                with self.subTest(field=field, bad=bad):
                    data = inputs()
                    data[field] = bad
                    self.assert_single_fail(data, "inputs", "MALFORMED_ACCEPTANCE_BINDING_INPUTS")

    def test_report_controls_are_exactly_five_ordered_unique_pairs(self):
        valid = inputs()["required_validation_report_refs"]
        variants = [[], valid[:4], [*valid, ref("report-5")], [valid[0], valid[0], *valid[2:]], list(reversed(valid))]
        for bad_member in [None, {}, [], "bad", 5, {**ref("x"), "extra": "bad"}, ref("x", "g" * 64)]:
            variants.append([bad_member, *valid[1:]])
        variants.extend([None, "bad", b"bad", {}, 5, set()])
        for reports in variants:
            with self.subTest(reports=reports):
                data = inputs()
                data["required_validation_report_refs"] = reports
                self.assert_single_fail(data, "inputs", "MALFORMED_ACCEPTANCE_BINDING_INPUTS")

    def test_report_generator_is_rejected_without_consumption(self):
        consumed = []
        def stream():
            consumed.append(True)
            yield from inputs()["required_validation_report_refs"]
        data = inputs()
        data["required_validation_report_refs"] = stream()
        rows = component.check_manifest_acceptance_v3_bindings(**data)
        self.assertEqual(rows, (core.Check("acceptance_v3.inputs", "FAIL", "MALFORMED_ACCEPTANCE_BINDING_INPUTS"),))
        self.assertEqual(consumed, [])

    def test_report_binding_detects_both_sides_of_substitution(self):
        for side in ["controls", "acceptance"]:
            for part, value in [("object_id", "synthetic-test-only:report-0-alternative"), ("content_sha256", "b" * 64)]:
                with self.subTest(side=side, part=part):
                    data = inputs()
                    if side == "controls":
                        data["required_validation_report_refs"][0][part] = value
                    else:
                        data["acceptance"]["required_validation_report_refs"][0][part] = value
                        data["acceptance"] = reseal(data["acceptance"])
                    self.assert_relation_failure(data, "reports", "VALIDATION_REPORT_SET_MISMATCH")

    def test_same_report_id_different_hash_uses_full_pair_order(self):
        data = inputs()
        reports = [ref("same-report-id", c * 64) for c in "abcde"]
        data["required_validation_report_refs"] = deepcopy(reports)
        data["acceptance"]["required_validation_report_refs"] = deepcopy(reports)
        data["acceptance"] = reseal(data["acceptance"])
        self.assertTrue(all(row.status == "PASS" for row in self.run_check(data)))
        data["required_validation_report_refs"].reverse()
        self.assert_single_fail(data, "inputs", "MALFORMED_ACCEPTANCE_BINDING_INPUTS")

    def test_reject_record_never_passes_accept_decision_binding(self):
        for blockers in [[], [ref("blocker")]]:
            with self.subTest(blockers=blockers):
                data = inputs()
                data["acceptance"].update(decision="REJECT", blocking_finding_refs=blockers)
                data["acceptance"] = reseal(data["acceptance"])
                self.assertIsNone(gate.validate_manifest_acceptance_v3_contract(data["acceptance"]))
                self.assert_relation_failure(data, "decision", "MANIFEST_NOT_ACCEPTED")

    def test_self_consistency_does_not_emit_authority_or_overall_result(self):
        data = inputs()
        for control, field in [("bootstrap_root_ref", "bootstrap_governance_root_ref"), ("acceptance_rule_ref", "acceptance_rule_ref")]:
            data[control] = ref(f"replacement-{control}")
            data["acceptance"][field] = deepcopy(data[control])
        data["acceptance"]["authority_ref"] = deepcopy(data["bootstrap_root_ref"])
        data["acceptance"] = reseal(data["acceptance"])
        rows = self.run_check(data)
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(row.status == "PASS" and row.reason_code == "OK" for row in rows))
        self.assertFalse(hasattr(rows, "result"))

    def test_never_aggregates_or_falls_back_to_legacy_helper(self):
        with patch.object(component, "aggregate", side_effect=AssertionError("must not aggregate")), patch.object(component, "validate_manifest_acceptance_v2", side_effect=AssertionError("no v2 fallback")):
            self.assertEqual(len(self.run_check(inputs())), 5)
            data = inputs()
            data["acceptance"]["schema_version"] = "2.0"
            data["acceptance"] = reseal(data["acceptance"])
            self.assert_single_fail(data, "contract", "ACCEPTANCE_CONTRACT_INVALID")


if __name__ == "__main__":
    unittest.main()
