import json
import unittest
from pathlib import Path

from forecast_trust_core.canonical import verify_sealed_object

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "genesis" / "candidate" / "objects" / "candidate_object_set_v0_2.json"
PATCHES = [
    ROOT / "genesis" / "candidate" / "objects" / f"candidate_patch_v0_{version}.json"
    for version in range(3, 9)
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


class GenesisCandidatePatchV08Tests(unittest.TestCase):
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
            "candidate_patch_v0_7.json",
        ]
        for patch, expected in zip(cls.patches, predecessors):
            if expected is not None:
                assert patch["predecessor_patch"] == expected
            apply_patch(cls.index, patch)

    def test_v08_is_non_prospective_and_count_is_21(self):
        patch = self.patches[-1]
        self.assertEqual(patch["candidate_version"], "0.8")
        self.assertEqual(patch["status"], "GEN_001_CANDIDATE_ONLY")
        self.assertIs(patch["prospective_eligible"], False)
        self.assertEqual(patch["effective_object_count"], 21)
        self.assertEqual(len(self.index), 21)

    def test_v08_retires_schedule_v1_by_exact_hash_and_adds_sealed_v2(self):
        patch = self.patches[-1]
        retirement = patch["retire_objects"][0]
        self.assertEqual(retirement["object_id"], "policy:genesis-issuance-schedule:v1")
        self.assertEqual(
            retirement["retires_content_sha256"],
            "efb42e0838b2d17a8c99d408bf56718298f12823f1a70da0bbd4bd8d7fbc2a27",
        )
        self.assertNotIn("policy:genesis-issuance-schedule:v1", self.index)
        self.assertIn("policy:genesis-issuance-schedule:v2", self.index)
        schedule = self.index["policy:genesis-issuance-schedule:v2"]
        self.assertTrue(verify_sealed_object(schedule))
        self.assertEqual(
            schedule["payload_sha256"],
            "af044d07ddd379a48a028a5d603420f00c88a3cc1c6a89bb879973037c6b886b",
        )
        self.assertEqual(
            schedule["content_sha256"],
            "ffeeadf78744612a06184ab65cbbf779b0a66b04f5fbcd67ba36ef218b6712dd",
        )

    def test_v2_freezes_dst_safe_calendar_arithmetic(self):
        schedule = self.index["policy:genesis-issuance-schedule:v2"]
        self.assertEqual(schedule["normative_timezone"], "America/New_York")
        self.assertEqual(schedule["relative_timing_basis"], "LOCAL_CALENDAR_ARITHMETIC_THEN_UTC")
        self.assertEqual(schedule["plan_commitment_offset_calendar_days"], 8)
        self.assertEqual(schedule["information_cutoff_offset_calendar_days"], 7)
        self.assertEqual(schedule["execution_window_open_offset_calendar_days"], 7)
        self.assertEqual(schedule["execution_window_close_offset_calendar_days"], 6)
        self.assertEqual(schedule["external_proof_offset_elapsed_hours"], 24)
        self.assertEqual(schedule["durability_completion_offset_elapsed_hours"], 0)
        self.assertEqual(schedule["ambiguous_or_nonexistent_local_time_rule"], "FAIL_CLOSED")
        self.assertEqual(
            schedule["timezone_database_binding_rule"],
            "schedule_derivation_evidence_must_bind_exact_iana_tzdb_version",
        )

    def test_v2_freezes_runtime_identity_derivation(self):
        schedule = self.index["policy:genesis-issuance-schedule:v2"]
        self.assertEqual(
            schedule["target_instance_identity_rule"],
            "recompute_with_seal_object_without_semantic_id",
        )
        self.assertEqual(
            schedule["target_instance_stable_context_template"],
            "genesis-target-instance:{target_object_id}:{reference_period}",
        )
        self.assertEqual(
            schedule["forecast_slot_identity_rule"],
            "recompute_with_seal_object_without_semantic_id",
        )
        self.assertEqual(
            schedule["forecast_slot_stable_context_template"],
            "genesis-forecast-slot:{target_instance_object_id}:{method_object_id}",
        )

    def test_v08_preserves_prior_compression_successors(self):
        self.assertIn("policy:deadline-receipt-quorum:v4", self.index)
        self.assertIn("policy:genesis-evaluation:v2", self.index)
        self.assertIn("policy:genesis-acceptance:v2", self.index)
        self.assertNotIn("policy:genesis-human-review:v1", self.index)


if __name__ == "__main__":
    unittest.main()
