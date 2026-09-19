import json
import unittest
from pathlib import Path

from forecast_trust_core.canonical import verify_sealed_object

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "genesis" / "candidate" / "objects" / "candidate_object_set_v0_2.json"
PATCH_V3 = ROOT / "genesis" / "candidate" / "objects" / "candidate_patch_v0_3.json"
PATCH_V4 = ROOT / "genesis" / "candidate" / "objects" / "candidate_patch_v0_4.json"
PATCH_V5 = ROOT / "genesis" / "candidate" / "objects" / "candidate_patch_v0_5.json"


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
            raise AssertionError("candidate replacement predecessor hash mismatch")
        replacement_obj = replacement["replacement"]
        if replacement_obj["object_id"] != object_id:
            raise AssertionError("candidate replacement object id mismatch")
        index[object_id] = replacement_obj
    for obj in patch.get("add_objects", []):
        if obj["object_id"] in index:
            raise AssertionError("candidate add collides")
        index[obj["object_id"]] = obj
    if len(index) != patch["effective_object_count"]:
        raise AssertionError("effective count mismatch")


def effective_objects():
    base = json.loads(BASE.read_text(encoding="utf-8"))
    p3 = json.loads(PATCH_V3.read_text(encoding="utf-8"))
    p4 = json.loads(PATCH_V4.read_text(encoding="utf-8"))
    p5 = json.loads(PATCH_V5.read_text(encoding="utf-8"))
    if p4["predecessor_patch"] != PATCH_V3.name or p5["predecessor_patch"] != PATCH_V4.name:
        raise AssertionError("patch predecessor chain mismatch")
    index = {obj["object_id"]: obj for obj in base["objects"]}
    for patch in (p3, p4, p5):
        apply_patch(index, patch)
    return p3, p4, p5, index


class GenesisCandidatePatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p3, cls.p4, cls.p5, cls.index = effective_objects()

    def test_v05_is_non_prospective_and_count_stable(self):
        self.assertEqual(self.p5["candidate_version"], "0.5")
        self.assertEqual(self.p5["status"], "GEN_001_CANDIDATE_ONLY")
        self.assertIs(self.p5["prospective_eligible"], False)
        self.assertEqual(self.p5["effective_object_count"], 22)
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

    def test_v3_retires_v2_by_exact_hash_without_rewriting_history(self):
        self.assertNotIn("policy:deadline-receipt-quorum:v1", self.index)
        self.assertNotIn("policy:deadline-receipt-quorum:v2", self.index)
        self.assertIn("policy:deadline-receipt-quorum:v3", self.index)
        self.assertEqual(self.p4["add_objects"][0]["object_id"], "policy:deadline-receipt-quorum:v2")
        retirement = self.p5["retire_objects"][0]
        self.assertEqual(retirement["object_id"], "policy:deadline-receipt-quorum:v2")
        self.assertEqual(
            retirement["retires_content_sha256"],
            "e47ef74b1a956646a53cdc6674016f25185c8a5783f17a30bde705d1882d3f2b",
        )

    def test_v3_hash_is_frozen(self):
        quorum = self.index["policy:deadline-receipt-quorum:v3"]
        self.assertEqual(quorum["payload_sha256"], "9225a8ca00a722a5d4252b2f111416f1d3b6aa649408e87d2ad894e8830b32e3")
        self.assertEqual(quorum["content_sha256"], "4e06b92306f618240d3d9114d2e2eceeb1265e1cf6fb0555dac651697863fe0b")

    def test_v3_closes_pre_rehearsal_ambiguity_and_fails_closed(self):
        q = self.index["policy:deadline-receipt-quorum:v3"]
        self.assertEqual(q["minimum_independent_provider_groups"], 2)
        self.assertEqual(q["frozen_provider_pool_size"], 3)
        self.assertEqual(q["threshold_rule"], "two_of_three_frozen_independent_provider_groups")
        self.assertEqual(q["provider_pool_rule"], "exactly_three_frozen_independent_roughtime_provider_groups")
        self.assertEqual(q["qualifying_receipt_family"], "ROUGHTIME")
        self.assertEqual(q["minimum_rfc3161_provider_groups"], 0)
        self.assertEqual(q["rfc3161_role"], "OPTIONAL_AUXILIARY")
        self.assertEqual(q["provider_outage_rule"], "never_lower_quorum")
        self.assertEqual(q["provider_substitution_rule"], "unlisted_provider_prohibited")
        self.assertEqual(q["roughtime_upper_bound_rule"], "midpoint_plus_radius")
        self.assertEqual(q["nonce_profile"], "FPP_ROUGHTIME_NONCE_V2")
        self.assertEqual(q["nonce_hash_algorithm"], "SHA256")
        self.assertEqual(q["nonce_length_bytes"], 32)
        self.assertEqual(q["nonce_client_random_bytes"], 32)
        self.assertEqual(q["provider_attempt_rule"], "evaluate_all_three_frozen_providers_in_frozen_order_attempt_each_when_retry_eligible")
        self.assertEqual(q["receipt_independence_rule"], "independent_subject_bound_nonce_per_provider_no_causal_chain")
        self.assertEqual(q["packet_profile_rule"], "STANDARD_1024_BODY_ONLY")
        self.assertEqual(q["transport_rule"], "UDP_ONLY")
        self.assertEqual(q["protocol_fallback_rule"], "PROHIBITED_WITHIN_DEADLINE_EVENT")
        self.assertEqual(q["packet_fallback_rule"], "PROHIBITED_WITHIN_DEADLINE_EVENT")
        self.assertEqual(q["transport_fallback_rule"], "PROHIBITED_WITHIN_DEADLINE_EVENT")
        self.assertEqual(q["request_retry_rule"], "maximum_two_attempts_same_exact_request_bytes_per_provider")
        self.assertEqual(q["retry_state_rule"], "persist_per_root_until_properly_signed_response")
        self.assertEqual(q["backoff_block_rule"], "backoff_active_counts_nonqualifying_no_network_attempt")
        self.assertEqual(q["radius_rule"], "strictly_positive_authenticated_radius_required")
        self.assertEqual(q["report_validation_rule"], "schema_and_executable_cross_field_semantic_validation_required")
        self.assertEqual(q["verifier_build_binding_rule"], "exact_content_addressed_verifier_build_profile_required")
        self.assertEqual(q["cryptographic_replay_rule"], "raw_request_response_nonce_and_profile_must_replay_pass_pinned_low_level_verifier")
        self.assertEqual(q["verification_transcript_rule"], "per_qualifying_receipt_verification_transcript_sha256_required")
        self.assertEqual(q["retry_state_binding_rule"], "exact_pre_attempt_retry_state_snapshot_sha256_bound_into_plan_and_authorization")
        self.assertEqual(q["retry_state_output_rule"], "post_attempt_retry_state_snapshot_sha256_required_in_report")
        self.assertEqual(q["version_offer_rule"], "singleton_frozen_wire_version_only")
        self.assertEqual(q["execution_transcript_rule"], "report_execution_transcript_sha256_required")
        self.assertEqual(q["verified_nonqualifying_response_rule"], "properly_signed_but_project_nonqualifying_response_stops_retry_and_resets_protocol_backoff")
        self.assertEqual(q["standards_transition_rule"], "wire_or_protocol_change_requires_reviewed_profile_and_manifest_change")
        self.assertEqual(q["cost_rule"], "ZERO_RECURRING_CASH_COST")


if __name__ == "__main__":
    unittest.main()
