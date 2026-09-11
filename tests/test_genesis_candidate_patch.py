import json
import unittest
from pathlib import Path

from forecast_trust_core.canonical import verify_sealed_object


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "genesis" / "candidate" / "objects" / "candidate_object_set_v0_2.json"
PATCH = ROOT / "genesis" / "candidate" / "objects" / "candidate_patch_v0_3.json"


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


def effective_objects():
    base = json.loads(BASE.read_text(encoding="utf-8"))
    patch = json.loads(PATCH.read_text(encoding="utf-8"))
    index = {obj["object_id"]: obj for obj in base["objects"]}
    for replacement in patch["replace_objects"]:
        object_id = replacement["object_id"]
        if index[object_id]["content_sha256"] != replacement["replaces_content_sha256"]:
            raise AssertionError("candidate patch predecessor hash mismatch")
        index[object_id] = replacement["replacement"]
    for obj in patch["add_objects"]:
        if obj["object_id"] in index:
            raise AssertionError("candidate patch add collides with existing object")
        index[obj["object_id"]] = obj
    return patch, index


class GenesisCandidatePatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch, cls.index = effective_objects()

    def test_patch_is_non_prospective(self):
        self.assertEqual(self.patch["status"], "GEN_001_CANDIDATE_ONLY")
        self.assertIs(self.patch["prospective_eligible"], False)

    def test_effective_object_count(self):
        self.assertEqual(self.patch["candidate_version"], "0.3")
        self.assertEqual(self.patch["effective_object_count"], 22)
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


if __name__ == "__main__":
    unittest.main()
