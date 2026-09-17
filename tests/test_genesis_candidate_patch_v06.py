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
        predecessors = [
            None,
            "candidate_patch_v0_3.json",
            "candidate_patch_v0_4.json",
            "candidate_patch_v0_5.json",
            "candidate_patch_v0_6.json",
        ]
        for patch, expected in zip(cls.patches, predecessors):
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

    def test_v07_preserves_architecture_compression_successors(self):
        self.assertNotIn("policy:genesis-human-review:v1", self.index)
        self.assertNotIn("policy:genesis-evaluation:v1", self.index)
        self.assertNotIn("policy:genesis-acceptance:v1", self.index)
        self.assertIn("policy:genesis-evaluation:v2", self.index)
        self.assertIn("policy:genesis-acceptance:v2", self.index)

    def test_v07_retires_v3_by_exact_hash_and_adds_sealed_v4(self):
        patch = self.patches[-1]
        retirement = patch["retire_objects"][0]
        self.assertEqual(retirement["object_id"], "policy:deadline-receipt-quorum:v3")
        self.assertEqual(
            retirement["retires_content_sha256"],
            "4e06b92306f618240d3d9114d2e2eceeb1265e1cf6fb0555dac651697863fe0b",
        )
        self.assertNotIn("policy:deadline-receipt-quorum:v3", self.index)
        self.assertIn("policy:deadline-receipt-quorum:v4", self.index)
        quorum = self.index["policy:deadline-receipt-quorum:v4"]
        self.assertTrue(verify_sealed_object(quorum))
        self.assertEqual(
            quorum["payload_sha256"],
            "08053b9e94fff39c6507b16a0926772e6e9a95c1b4eb87d08b6770249ffd32d8",
        )
        self.assertEqual(
            quorum["content_sha256"],
            "d94bf1f58fec1e5e446206b309a2f63321dea78fcadc0029c31ed9fab09761d7",
        )

    def test_v4_freezes_minimal_claim_critical_quorum_semantics(self):
        q = self.index["policy:deadline-receipt-quorum:v4"]
        self.assertEqual(q["frozen_provider_pool_size"], 3)
        self.assertEqual(q["minimum_independent_provider_groups"], 2)
        self.assertEqual(
            q["threshold_rule"],
            "at_least_two_distinct_qualifying_receipts_from_frozen_three_provider_pool",
        )
        self.assertEqual(
            q["provider_pool_rule"],
            "exactly_three_frozen_independent_roughtime_provider_groups",
        )
        self.assertEqual(q["provider_outage_rule"], "never_lower_quorum")
        self.assertEqual(q["provider_substitution_rule"], "unlisted_provider_prohibited")
        self.assertEqual(q["qualifying_receipt_family"], "ROUGHTIME")
        self.assertEqual(q["roughtime_upper_bound_rule"], "midpoint_plus_radius")
        self.assertEqual(q["nonce_profile"], "FPP_ROUGHTIME_NONCE_V2")
        self.assertEqual(q["nonce_hash_algorithm"], "SHA256")
        self.assertEqual(q["nonce_length_bytes"], 32)
        self.assertEqual(q["nonce_client_random_bytes"], 32)
        self.assertEqual(
            q["receipt_independence_rule"],
            "independent_subject_bound_nonce_per_provider_no_causal_chain",
        )
        self.assertEqual(
            q["cryptographic_replay_rule"],
            "raw_request_response_nonce_and_profile_must_replay_pass_pinned_low_level_verifier",
        )
        self.assertEqual(
            q["raw_evidence_retention_rule"],
            "exact_request_response_client_random_and_provider_binding_retained_for_each_counted_receipt",
        )
        self.assertEqual(
            q["receipt_authority_binding_rule"],
            "counted_receipt_must_cross_bind_exact_provider_profile_and_qualification_state_package",
        )
        self.assertEqual(
            q["orchestration_claim_rule"],
            "provider_attempt_order_retry_backoff_and_unused_provider_transcripts_not_prerequisites_of_external_existence_claim",
        )

    def test_v4_excludes_execution_orchestration_from_claim_critical_policy(self):
        q = self.index["policy:deadline-receipt-quorum:v4"]
        removed = {
            "provider_attempt_rule",
            "provider_order_rule",
            "request_retry_rule",
            "retry_backoff_factor",
            "retry_backoff_initial_seconds",
            "retry_backoff_max_seconds",
            "retry_state_binding_rule",
            "retry_state_output_rule",
            "retry_state_rule",
            "backoff_block_rule",
            "success_retry_rule",
            "verified_nonqualifying_response_rule",
            "execution_transcript_rule",
            "verification_transcript_rule",
            "timeout_per_attempt_seconds",
        }
        self.assertTrue(removed.isdisjoint(q))

    def test_minimal_evaluation_surface(self):
        policy = self.index["policy:genesis-evaluation:v2"]
        self.assertEqual(policy["metrics"], ["absolute_error", "squared_error"])
        self.assertEqual(policy["aggregation_rule"], "NONE_FOR_GENESIS_V1")
        self.assertEqual(
            policy["baseline_comparison_rule"],
            "DEFER_UNTIL_DISTINCT_SECOND_METHOD",
        )
        self.assertNotIn("baseline_method_ref", policy)

    def test_acceptance_v2_is_noncircular(self):
        policy = self.index["policy:genesis-acceptance:v2"]
        self.assertEqual(
            policy["final_external_evidence_subject"],
            "SIGNED_MANIFEST_ACCEPTANCE",
        )
        self.assertEqual(
            policy["final_external_evidence_role"],
            "EXTERNAL_FINAL_VALIDATION_INPUT",
        )
        self.assertEqual(policy["intermediate_anchor_rule"], "OPTIONAL_AUDIT_ONLY")
        self.assertNotIn("required_external_anchor_evidence", policy)


if __name__ == "__main__":
    unittest.main()
