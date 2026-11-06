"""Keyless SYNTHETIC_TEST_ONLY local contracts; no protocol or authentication.

Run directly with Python/unittest: this deliberately avoids package __init__,
pytest conftest, historical fixtures, resolvers, keys, signatures and carriers.
The ordinary object seals below are software test data, never signed messages.
"""

from copy import deepcopy
import importlib.util
import inspect
from pathlib import Path
import sys
import types
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "src" / "forecast_trust_core"
NAMESPACE = "_ma3_keyless_contract_tests"
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
gate = load_component("claim_authority_contract_gate_v1")


def ref(name, digest="a" * 64):
    return {"object_id": f"synthetic-test-only:{name}", "content_sha256": digest}


def payload():
    return {
        "schema_version": "3.0",
        "candidate_manifest_ref": ref("manifest"),
        "bootstrap_governance_root_ref": ref("root"),
        "acceptance_rule_ref": ref("rule"),
        "required_validation_report_refs": [ref(f"report-{i}") for i in range(5)],
        "authority_ref": ref("root"),
        "decision": "ACCEPT",
        "reason_codes": [],
        "blocking_finding_refs": [],
        "signature_ref": ref("unresolved-reference-only"),
    }


def sealed(data=None, object_type="ManifestAcceptance"):
    return canonical.seal_object(
        payload() if data is None else data,
        object_type=object_type,
        stable_context="SYNTHETIC_TEST_ONLY",
    )


class ManifestAcceptanceV3ContractTests(unittest.TestCase):
    def validate(self, obj):
        return gate.validate_manifest_acceptance_v3_contract(obj)

    def assert_rejected(self, obj, reason):
        before = deepcopy(obj)
        with self.assertRaisesRegex(ValueError, reason):
            self.validate(obj)
        self.assertEqual(obj, before)

    def test_accept_and_reject_records_pass_without_mutation(self):
        for decision, blockers in [("ACCEPT", []), ("REJECT", []), ("REJECT", [ref("b0"), ref("b1")])]:
            with self.subTest(decision=decision, blockers=len(blockers)):
                data = payload()
                data.update(decision=decision, blocking_finding_refs=blockers, reason_codes=["A", "Z"])
                obj = sealed(data)
                before = deepcopy(obj)
                self.assertIsNone(self.validate(obj))
                self.assertEqual(obj, before)

    def test_strict_schema_versions(self):
        for version in ["1.0", "2.0", "3.1", 3, [], {}]:
            with self.subTest(version=version):
                data = payload()
                data["schema_version"] = version
                self.assert_rejected(sealed(data), "schema_version mismatch")

    def test_exact_top_level_fields(self):
        for field in gate.MANIFEST_ACCEPTANCE_V2_KEYS:
            with self.subTest(missing=field):
                obj = sealed()
                del obj[field]
                self.assert_rejected(obj, "field set mismatch")
        data = payload()
        data["extra"] = "SYNTHETIC_TEST_ONLY"
        self.assert_rejected(sealed(data), "field set mismatch")
        for obj in [[], "synthetic-test-only", 1, None]:
            with self.subTest(non_object=obj):
                self.assert_rejected(obj, "must be an object")

    def test_wrong_type_and_invalid_seals(self):
        self.assert_rejected(sealed(object_type="SyntheticOtherType"), "object_type mismatch")
        for field in ["payload_sha256", "content_sha256"]:
            with self.subTest(field=field):
                obj = sealed()
                obj[field] = "0" * 64
                self.assert_rejected(obj, "seal invalid")
        obj = sealed()
        obj["reason_codes"] = ["TAMPERED"]
        self.assert_rejected(obj, "seal invalid")

    def test_malformed_single_and_array_references(self):
        bad_refs = [
            {}, {"object_id": "synthetic-test-only:x"},
            {**ref("x"), "extra": "bad"}, ref("bad id"),
            {"object_id": "非ASCII", "content_sha256": "a" * 64},
            {"object_id": "", "content_sha256": "a" * 64},
            ref("x", "A" * 64), ref("x", "g" * 64), ref("x", "a" * 63),
            ref("x", "a" * 65), ref("x", 5), [], "bad", 7,
            ["object_id", "content_sha256"],
        ]
        fields = ["candidate_manifest_ref", "bootstrap_governance_root_ref", "acceptance_rule_ref", "authority_ref", "signature_ref", "required_validation_report_refs", "blocking_finding_refs"]
        for field in fields:
            for bad in bad_refs:
                with self.subTest(field=field, bad=bad):
                    data = payload()
                    if field in {"required_validation_report_refs", "blocking_finding_refs"}:
                        data["decision"] = "REJECT"
                        data[field] = [bad, *data[field][1:]] if data[field] else [bad]
                    else:
                        data[field] = bad
                    self.assert_rejected(sealed(data), f"{field}.*reference malformed")

    def test_reports_are_exactly_five(self):
        for size in [0, 4, 6]:
            with self.subTest(size=size):
                data = payload()
                data["required_validation_report_refs"] = [ref(f"r{i}") for i in range(size)]
                self.assert_rejected(sealed(data), "required_validation_report_refs cardinality")
        for wrong in [{}, "bad", 5]:
            data = payload()
            data["required_validation_report_refs"] = wrong
            self.assert_rejected(sealed(data), "required_validation_report_refs cardinality")

    def test_reports_unique_and_sorted_by_full_pair(self):
        data = payload()
        data["required_validation_report_refs"][1] = deepcopy(data["required_validation_report_refs"][0])
        self.assert_rejected(sealed(data), "required_validation_report_refs contains duplicate")
        data = payload()
        data["required_validation_report_refs"].reverse()
        self.assert_rejected(sealed(data), "required_validation_report_refs.*sorted")
        data = payload()
        data["required_validation_report_refs"] = [ref("same-id", c * 64) for c in "abcde"]
        self.assertIsNone(self.validate(sealed(data)))
        data["required_validation_report_refs"].reverse()
        self.assert_rejected(sealed(data), "required_validation_report_refs.*sorted")

    def test_authority_and_root_must_match_both_fields(self):
        for authority in [ref("different-root"), ref("root", "b" * 64)]:
            with self.subTest(authority=authority):
                data = payload()
                data["authority_ref"] = authority
                self.assert_rejected(sealed(data), "authority_ref.*bootstrap_governance_root_ref")
        fn = gate.validate_manifest_acceptance_v3_contract
        self.assertEqual(list(inspect.signature(fn).parameters), ["acceptance"])

    def test_reason_codes_are_valid_sorted_unique_tokens(self):
        for reasons in ["A", {}, 3, [""], ["中文"], ["bad token"], ["A\n"], [5]]:
            with self.subTest(reasons=reasons):
                data = payload()
                data["reason_codes"] = reasons
                self.assert_rejected(sealed(data), "reason_codes")
        for reasons in [["A", "A"], ["Z", "A"]]:
            data = payload()
            data["reason_codes"] = reasons
            self.assert_rejected(sealed(data), "reason_codes.*sorted.*unique")
        for reasons in [[], ["A", "Z", "a"]]:
            data = payload()
            data["reason_codes"] = reasons
            self.assertIsNone(self.validate(sealed(data)))

    def test_blockers_are_sorted_unique_full_pairs(self):
        for blockers, reason in [
            ([ref("b"), ref("b")], "duplicate"),
            ([ref("b1"), ref("b0")], "sorted"),
            ([ref("b", "b" * 64), ref("b", "a" * 64)], "sorted"),
            ({}, "must be an array"), ("bad", "must be an array"),
        ]:
            with self.subTest(blockers=blockers):
                data = payload()
                data.update(decision="REJECT", blocking_finding_refs=blockers)
                self.assert_rejected(sealed(data), f"blocking_finding_refs.*{reason}")
        data = payload()
        data.update(decision="REJECT", blocking_finding_refs=[ref("b", "a" * 64), ref("b", "b" * 64)])
        self.assertIsNone(self.validate(sealed(data)))

    def test_accept_requires_empty_blockers(self):
        data = payload()
        data["blocking_finding_refs"] = [ref("blocker")]
        self.assert_rejected(sealed(data), "ACCEPT.*blocking_finding_refs")

    def test_invalid_decisions_raise_value_error(self):
        for decision in ["", "ADOPT", "accept", [], {}, ["ACCEPT"], 0, 1, True, False]:
            with self.subTest(decision=decision):
                data = payload()
                data["decision"] = decision
                self.assert_rejected(sealed(data), "decision invalid")
        # Null cannot have a valid canonical seal; it fails at that earlier gate.
        obj = sealed()
        obj["decision"] = None
        self.assert_rejected(obj, "seal invalid")

    def test_v2_still_accepts_its_own_contract_only(self):
        data = payload()
        data.update(schema_version="2.0", authority_ref=ref("separate-legacy-authority"))
        data["required_validation_report_refs"] = [ref("legacy-report")]
        data["reason_codes"] = ["Z", "A", "A"]
        obj = sealed(data)
        self.assertIsNone(gate.validate_manifest_acceptance_v2_contract(obj))
        before = deepcopy(obj)
        with self.assertRaisesRegex(ValueError, "schema_version mismatch"):
            gate.validate_manifest_acceptance_v2_contract(sealed())
        self.assertEqual(obj, before)


if __name__ == "__main__":
    unittest.main()
