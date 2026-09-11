import copy
import unittest

from forecast_trust_core import CanonicalizationError, Result, canonical_json, require_decimal_string, seal_object, validate_cycle_manifest, validate_cycle_plan, validate_external_deadline, validate_point_in_time, validate_probability, validate_selection_control, verify_sealed_object


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


class CanonicalTests(unittest.TestCase):
    def test_key_order_is_deterministic(self):
        self.assertEqual(canonical_json({"b": 1, "a": "x"}), b'{"a":"x","b":1}')

    def test_float_null_and_non_ascii_keys_rejected(self):
        for value in ({"p": 0.5}, {"x": None}, {"é": "x"}):
            with self.assertRaises(CanonicalizationError):
                canonical_json(value)

    def test_decimal_rules(self):
        self.assertEqual(require_decimal_string("0.125", probability=True), "0.125")
        for invalid in ("1.0", "+1", "1e-3", "-0", "1.1"):
            with self.assertRaises(CanonicalizationError):
                require_decimal_string(invalid, probability=True)

    def test_two_stage_seal_detects_mutation(self):
        obj = seal_object({"schema_version": "0.4", "value": "alpha"}, object_type="SyntheticEvent", stable_context="alpha")
        self.assertTrue(verify_sealed_object(obj))
        mutated = dict(obj)
        mutated["value"] = "beta"
        self.assertFalse(verify_sealed_object(mutated))


class TrustCoreTests(unittest.TestCase):
    def _slot(self, name):
        return seal_object({"schema_version": "0.4", "target": name}, object_type="Slot", stable_context=name)

    def _plan(self, slots):
        return seal_object({
            "schema_version": "0.4",
            "plan_commitment_deadline": "2026-09-11T01:00:00Z",
            "execution_window_open": "2026-09-11T02:00:00Z",
            "execution_window_close": "2026-09-11T03:00:00Z",
            "expected_slots": sorted([ref(s) for s in slots], key=lambda r: (r["object_id"], r["content_sha256"])),
        }, object_type="IssuanceCyclePlan", stable_context="cycle1")

    def test_point_in_time(self):
        self.assertEqual(validate_point_in_time([{"available_at": "2026-09-10T00:00:00Z"}], "2026-09-11T00:00:00Z").result, Result.VALID)
        self.assertEqual(validate_point_in_time([{"available_at": "2026-09-12T00:00:00Z"}], "2026-09-11T00:00:00Z").result, Result.INVALID)
        self.assertEqual(validate_point_in_time([{}], "2026-09-11T00:00:00Z").result, Result.INELIGIBLE_TRUST_UNKNOWN)

    def test_probability(self):
        self.assertEqual(validate_probability("0.2").status, "PASS")
        self.assertEqual(validate_probability(0.2).status, "FAIL")

    def test_cycle_plan_requires_external_precommitment(self):
        slots = [self._slot("a"), self._slot("b")]
        plan = self._plan(slots)
        required = [ref(s) for s in slots]
        self.assertEqual(validate_cycle_plan(plan, verified_plan_existence_bound="2026-09-11T00:30:00Z", required_slots=required).result, Result.VALID)
        self.assertEqual(validate_cycle_plan(plan, verified_plan_existence_bound="2026-09-11T01:30:00Z", required_slots=required).result, Result.INVALID)

    def test_cycle_manifest_complete(self):
        slots = [self._slot("a"), self._slot("b")]
        plan = self._plan(slots)
        manifest = seal_object({
            "schema_version": "0.4",
            "cycle_plan_ref": ref(plan),
            "slot_accounting": [
                {"slot_ref": ref(slots[0]), "outcome": "ISSUED", "issued_forecast_refs": [ref(slots[0])]},
                {"slot_ref": ref(slots[1]), "outcome": "FAILED"}
            ]
        }, object_type="IssuanceCycleManifest", stable_context="cycle1")
        self.assertEqual(validate_cycle_manifest(plan, manifest).result, Result.VALID)
        bad_payload = {k: copy.deepcopy(v) for k, v in manifest.items() if k not in {"object_id", "payload_sha256", "content_sha256"}}
        bad_payload["slot_accounting"] = bad_payload["slot_accounting"][:1]
        bad = seal_object(bad_payload, object_type="IssuanceCycleManifest", stable_context="cycle1bad")
        self.assertEqual(validate_cycle_manifest(plan, bad).result, Result.INVALID)

    def test_selection_control(self):
        self.assertEqual(validate_selection_control({"selection_control_class": "DETERMINISTIC_REPLAY"}, {"replay_verified": True}).result, Result.VALID)
        self.assertEqual(validate_selection_control({"selection_control_class": "UNCONTROLLED_NONDETERMINISM"}, {}).result, Result.INVALID)

    def test_external_deadline(self):
        self.assertEqual(validate_external_deadline(None, "2026-09-11T10:00:00Z").result, Result.PENDING_EXTERNAL_ANCHOR)
        self.assertEqual(validate_external_deadline("2026-09-11T09:00:00Z", "2026-09-11T10:00:00Z").result, Result.VALID)
        self.assertEqual(validate_external_deadline("2026-09-11T11:00:00Z", "2026-09-11T10:00:00Z").result, Result.LATE_OR_INELIGIBLE)


if __name__ == "__main__":
    unittest.main()
