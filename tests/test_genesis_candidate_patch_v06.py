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


class GenesisCandidatePatchV06Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = json.loads(BASE.read_text(encoding="utf-8"))
        cls.index = {obj["object_id"]: obj for obj in base["objects"]}
        cls.patches = [json.loads(path.read_text(encoding="utf-8")) for path in PATCHES]
        self_names = [path.name for path in PATCHES]
        self_predecessors = [None, "candidate_patch_v0_3.json", "candidate_patch_v0_4.json", "candidate_patch_v0_5.json"]
        for patch, expected in zip(cls.patches, self_predecessors):
            if expected is not None:
                assert patch["predecessor_patch"] == expected
            apply_patch(cls.index, patch)

    def test_v06_is_non_prospective_and_count_is_21(self):
        patch = self.patches[-1]
        self.assertEqual(patch["candidate_version"], "0.6")
        self.assertEqual(patch["status"], "GEN_001_CANDIDATE_ONLY")
        self.assertIs(patch["prospective_eligible"], False)
        self.assertEqual(patch["effective_object_count"], 21)
        self.assertEqual(len(self.index), 21)

    def test_v06_retires_historical_review_evaluation_acceptance_by_exact_hash(self):
        self.assertNotIn("policy:genesis-human-review:v1", self.index)
        self.assertNotIn("policy:genesis-evaluation:v1", self.index)
        self.assertNotIn("policy:genesis-acceptance:v1", self.index)
        self.assertIn("policy:genesis-evaluation:v2", self.index)
        self.assertIn("policy:genesis-acceptance:v2", self.index)

    def test_v06_new_objects_are_sealed(self):
        for object_id in ("policy:genesis-evaluation:v2", "policy:genesis-acceptance:v2"):
            self.assertTrue(verify_sealed_object(self.index[object_id]))

    def test_minimal_evaluation_surface(self):
        policy = self.index["policy:genesis-evaluation:v2"]
        self.assertEqual(policy["metrics"], ["absolute_error", "squared_error"])
        self.assertEqual(policy["aggregation_rule"], "NONE_FOR_GENESIS_V1")
        self.assertEqual(policy["baseline_comparison_rule"], "DEFER_UNTIL_DISTINCT_SECOND_METHOD")
        self.assertNotIn("baseline_method_ref", policy)

    def test_acceptance_v2_is_noncircular(self):
        policy = self.index["policy:genesis-acceptance:v2"]
        self.assertEqual(policy["final_external_evidence_subject"], "SIGNED_MANIFEST_ACCEPTANCE")
        self.assertEqual(policy["final_external_evidence_role"], "EXTERNAL_FINAL_VALIDATION_INPUT")
        self.assertEqual(policy["intermediate_anchor_rule"], "OPTIONAL_AUDIT_ONLY")
        self.assertNotIn("required_external_anchor_evidence", policy)


if __name__ == "__main__":
    unittest.main()
