import json
import unittest
from pathlib import Path

from forecast_trust_core.canonical import verify_sealed_object


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "genesis" / "candidate" / "objects" / "candidate_object_set_v0_2.json"
PATCH_V3 = ROOT / "genesis" / "candidate" / "objects" / "candidate_patch_v0_3.json"
PATCH_V4 = ROOT / "genesis" / "candidate" / "objects" / "candidate_patch_v0_4.json"


def full_refs(value):
    if isinstance(value, dict):
        if set(value) == {"object_id", "content_sha256"}:
            yield value
            return
        for member in value.values():
            yield from full_refs(member)
    elif isinstance(value, list):
        for member in value:
            yield from full_refs(member)


def apply_patch(index, patch):
    for retirement in patch.get("retire_objects", []):
        object_id = retirement["object_id"]
        if index[object_id]["content_sha256"] != retirement["retires_content_sha256"]:
            raise AssertionError("candidate retirement predecessor hash mismatch")
        del index[object_id]
    for replacement in patch.get("replace_objects", []):
        object_id = replacement["object_id"]
        if index[object_id]["content_sha256"] != replacement["replaces_content_sha256"]:
            raise AssertionError("candidate patch predecessor hash mismatch")
        index[object_id] = replacement["replacement"]
    for obj in patch.get("add_objects", []):
        if obj["object_id"] in index:
            raise AssertionError("candidate patch add collides with existing object")
        index[obj["object_id"]] = obj
    if len(index) != patch["effective_object_count"]:
        raise AssertionError("candidate patch effective count mismatch")


def effective_objects():
    base = json.loads(BASE.read_text(encoding="utf-8"))
    patch_v3 = json.loads(PATCH_V3.read_text(encoding="utf-8"))
    patch_v4 = json.loads(PATCH_V4.read_text(encoding="utf-8"))
    if patch_v4["predecessor_patch"] != PATCH_V3.name:
        raise AssertionError("candidate v0.4 predecessor patch mismatch")
    index = {obj["object_id"]: obj for obj in base["objects"]}
    apply_patch(index, patch_v3)
    apply_patch(index, patch_v4)
    return patch_v3, patch_v4, index


class GenesisCandidatePatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch_v3, cls.patch_v4, cls.index = effective_objects()

    def test_patch_is_non_prospective(self):
        self.assertEqual(self.patch_v4["status"], "GEN_001_CANDIDATE_ONLY")
        self.assertIs(self.patch_v4["prospective_eligible"], False)

    def test_effective_object_count(self):
        self.assertEqual(self.patch_v4["candidate_version"], "0.4")
        self.assertEqual(self.patch_v4["effective_object_count"], 22)
        self.assertEqual(len(self.index), 22)

    def test_all_effective_objects_are_sealed(self):
        for obj in self.index.values():
            with self.subTest(object_id=obj["object_id"]):
                self.assertTrue(verify_sealed_object(obj))

    def test_all_full_refs_close_exactly(self):
        for obj in self.index.values():
            for ref in full_refs(obj):
                with self.subTest(ref=ref):
                    target = self.index.get(ref["object_id"])
                    self.assertIsNotNone(target)
                    self.assertEqual(target["content_sha256"], ref["content_sha256"])

    def test_schedule_is_one_cycle_per_release_instance(self):
        schedule = self.index["policy:genesis-issuance-schedule:v1"]
        self.assertEqual(schedule["cycle_model"], "ONE_CYCLE_PER_TARGET_RELEASE_INSTANCE")
        self.assertEqual(schedule["plan_commitment_offset_days_before_barrier"], 8)
        self.assertEqual(schedule["information_cutoff_offset_days_before_barrier"], 7)
        self.assertEqual(schedule["execution_window_close_offset_days_before_barrier"], 6)
        self.assertEqual(schedule["external_proof_margin_hours_before_barrier"], 24)

    def test_required_operational_policies_present(self):
        expected = {
            "policy:genesis-retry:v1",
            "policy:genesis-omission:v1",
            "policy:genesis-correction:v1",
            "policy:genesis-retention:v1",
            "policy:genesis-human-review:v1",
            "policy:genesis-acceptance:v1",
        }
        self.assertTrue(expected.issubset(self.index))

    def test_deadline_quorum_is_versioned_without_rewriting_v1(self):
        self.assertNotIn("policy:deadline-receipt-quorum:v1", self.index)
        self.assertIn("policy:deadline-receipt-quorum:v2", self.index)
        retirement = self.patch_v4["retire_objects"][0]
        self.assertEqual(retirement["object_id"], "policy:deadline-receipt-quorum:v1")
        self.assertEqual(
            retirement["retires_content_sha256"],
            "6f8bb3d0c7b57203ea91a1f345b038a86debef976968decdddf11bef00d040ad",
        )

    def test_zero_cost_roughtime_quorum_fails_closed(self):
        quorum = self.index["policy:deadline-receipt-quorum:v2"]
        self.assertEqual(quorum["minimum_independent_provider_groups"], 2)
        self.assertEqual(quorum["frozen_provider_pool_size"], 3)
        self.assertEqual(quorum["threshold_rule"], "two_of_three_frozen_independent_provider_groups")
        self.assertEqual(
            quorum["provider_pool_rule"],
            "exactly_three_frozen_independent_roughtime_provider_groups",
        )
        self.assertEqual(quorum["qualifying_receipt_family"], "ROUGHTIME")
        self.assertEqual(quorum["minimum_rfc3161_provider_groups"], 0)
        self.assertEqual(quorum["rfc3161_role"], "OPTIONAL_AUXILIARY")
        self.assertEqual(quorum["provider_outage_rule"], "never_lower_quorum")
        self.assertEqual(quorum["provider_substitution_rule"], "unlisted_provider_prohibited")
        self.assertEqual(quorum["roughtime_upper_bound_rule"], "midpoint_plus_radius")
        self.assertEqual(
            quorum["subject_binding"],
            "sha512_domain_separated_subject_sha256_and_client_random_nonce",
        )
        self.assertEqual(
            quorum["key_rotation_rule"],
            "new_provider_profile_and_manifest_change_required",
        )
        self.assertEqual(quorum["cost_rule"], "ZERO_RECURRING_CASH_COST")


if __name__ == "__main__":
    unittest.main()
