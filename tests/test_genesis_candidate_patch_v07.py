import json
import unittest
from pathlib import Path

from forecast_trust_core.canonical import verify_sealed_object

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "genesis" / "candidate" / "objects" / "candidate_object_set_v0_2.json"
PATCHES = [
    ROOT / "genesis" / "candidate" / "objects" / "candidate_patch_v0_3.json",
    ROOT / "genesis" / "candidate" / "objects" / "candidate_patch_v0_4.json",
    ROOT / "genesis" / "candidate" / "objects" / "candidate_patch_v0_5.json",
    ROOT / "genesis" / "candidate" / "objects" / "candidate_patch_v0_6.json",
    ROOT / "genesis" / "candidate" / "objects" / "candidate_patch_v0_7.json",
]


def apply_patch(index, patch):
    for retirement in patch.get("retire_objects", []):
        object_id = retirement["object_id"]
        if index[object_id]["content_sha256"] != retirement["retires_content_sha256"]:
            raise AssertionError("candidate retirement predecessor hash mismatch")
        del index[object_id]
    for replacement in patch.get("replace_objects", []):
        object_id = replacement["object_id"]
        if index[object_id]["content_sha256"] != replacement["replaces_content_sha256"]:
            raise AssertionError("candidate replacement predecessor hash mismatch")
        index[object_id] = replacement["replacement"]
    for obj in patch.get("add_objects", []):
        if obj["object_id"] in index:
            raise AssertionError("candidate add collides")
        index[obj["object_id"]] = obj
    if len(index) != patch["effective_object_count"]:
        raise AssertionError("effective count mismatch")


class GenesisCandidatePatchV07Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = json.loads(BASE.read_text(encoding="utf-8"))
        cls.index = {obj["object_id"]: obj for obj in base["objects"]}
        cls.patches = [json.loads(path.read_text(encoding="utf-8")) for path in PATCHES]
        expected_predecessors = [
            None,
            "candidate_patch_v0_3.json",
            "candidate_patch_v0_4.json",
            "candidate_patch_v0_5.json",
            "candidate_patch_v0_6.json",
        ]
        for patch, expected in zip(cls.patches, expected_predecessors):
            if expected is not None:
                assert patch["predecessor_patch"] == expected
            apply_patch(cls.index, patch)

    def test_v07_is_non_prospective_and_count_is_21(self):
        patch = self.patches[-1]
        self.assertEqual(patch["candidate_version"], "0.7")
        self.assertEqual(patch["status"], "GEN_001_CANDIDATE_ONLY")
        self.assertIs(patch["prospective_eligible"], False)
        self.assertEqual(patch["effective_object_count"], 21)
        self.assertEqual(len(self.index), 21)

    def test_v07_retires_v3_quorum_policy_by_exact_hash(self):
        retirement = self.patches[-1]["retire_objects"][0]
        self.assertEqual(retirement["object_id"], "policy:deadline-receipt-quorum:v3")
        self.assertEqual(
            retirement["retires_content_sha256"],
            "4e06b92306f618240d3d9114d2e2eceeb1265e1cf6fb0555dac651697863fe0b",
        )
        self.assertNotIn("policy:deadline-receipt-quorum:v3", self.index)
        self.assertIn("policy:deadline-receipt-quorum:v4", self.index)

    def test_v4_quorum_policy_is_sealed(self):
        policy = self.index["policy:deadline-receipt-quorum:v4"]
        self.assertTrue(verify_sealed_object(policy))
        self.assertEqual(
            policy["content_sha256"],
            "ad86c599ab574d50c1e7854244c6dce01b9a0275632e24c2a4f0957ade3d6c87",
        )

    def test_v4_keeps_security_relevant_receipt_quorum_semantics(self):
        policy = self.index["policy:deadline-receipt-quorum:v4"]
        self.assertEqual(policy["frozen_provider_pool_size"], 3)
        self.assertEqual(policy["minimum_independent_provider_groups"], 2)
        self.assertEqual(
            policy["threshold_rule"],
            "at_least_two_of_three_frozen_independent_provider_groups",
        )
        self.assertEqual(
            policy["qualifying_receipt_set_rule"],
            "two_or_three_distinct_frozen_provider_receipts",
        )
        self.assertEqual(policy["provider_outage_rule"], "never_lower_quorum")
        self.assertEqual(policy["provider_substitution_rule"], "unlisted_provider_prohibited")
        self.assertEqual(
            policy["roughtime_upper_bound_rule"],
            "maximum_of_counted_midpoint_plus_radius_upper_bounds",
        )
        self.assertIn("raw_request_response", policy["cryptographic_replay_rule"])

    def test_v4_removes_provider_network_orchestration_from_claim_boundary(self):
        policy = self.index["policy:deadline-receipt-quorum:v4"]
        self.assertEqual(
            policy["provider_attempt_accounting_role"],
            "OPERATIONAL_DIAGNOSTIC_NOT_CLAIM_PREREQUISITE",
        )
        for obsolete in (
            "backoff_block_rule",
            "execution_transcript_rule",
            "provider_attempt_rule",
            "provider_order_rule",
            "request_retry_rule",
            "retry_backoff_factor",
            "retry_backoff_initial_seconds",
            "retry_backoff_max_seconds",
            "retry_state_binding_rule",
            "retry_state_output_rule",
            "retry_state_rule",
            "success_retry_rule",
            "timeout_per_attempt_seconds",
            "verification_transcript_rule",
            "verified_nonqualifying_response_rule",
        ):
            self.assertNotIn(obsolete, policy)

    def test_v06_compression_objects_remain_active(self):
        self.assertIn("policy:genesis-evaluation:v2", self.index)
        self.assertIn("policy:genesis-acceptance:v2", self.index)
        self.assertNotIn("policy:genesis-human-review:v1", self.index)


if __name__ == "__main__":
    unittest.main()
