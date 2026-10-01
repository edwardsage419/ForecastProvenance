import json
import unittest
from pathlib import Path

from forecast_trust_core.canonical import verify_sealed_object


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "genesis" / "candidate" / "objects" / "candidate_object_set_v0_2.json"


def iter_full_refs(value):
    if isinstance(value, dict):
        if set(value) == {"object_id", "content_sha256"}:
            yield value
            return
        for member in value.values():
            yield from iter_full_refs(member)
    elif isinstance(value, list):
        for member in value:
            yield from iter_full_refs(member)


class GenesisCandidateObjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        cls.objects = cls.bundle["objects"]
        cls.index = {obj["object_id"]: obj for obj in cls.objects}

    def test_bundle_is_explicitly_non_prospective(self):
        self.assertEqual(self.bundle["status"], "GEN_001_CANDIDATE_ONLY")
        self.assertIs(self.bundle["prospective_eligible"], False)

    def test_object_count_and_ids_are_unique(self):
        self.assertEqual(self.bundle["object_count"], 16)
        self.assertEqual(len(self.objects), 16)
        self.assertEqual(len(self.index), 16)

    def test_every_candidate_object_is_sealed(self):
        for obj in self.objects:
            with self.subTest(object_id=obj["object_id"]):
                self.assertTrue(verify_sealed_object(obj))

    def test_every_full_dependency_ref_closes_exactly(self):
        refs = []
        for obj in self.objects:
            refs.extend(iter_full_refs(obj))
        self.assertGreater(len(refs), 0)
        for ref in refs:
            with self.subTest(ref=ref):
                target = self.index.get(ref["object_id"])
                self.assertIsNotNone(target)
                self.assertEqual(target["content_sha256"], ref["content_sha256"])

    def test_evaluation_policy_binds_full_baseline_hash(self):
        evaluation = self.index["policy:genesis-evaluation:v1"]
        baseline = self.index["method:last-observed-value:v1"]
        self.assertEqual(
            evaluation["baseline_method_ref"],
            {
                "object_id": baseline["object_id"],
                "content_sha256": baseline["content_sha256"],
            },
        )

    def test_baseline_binds_all_three_target_hashes(self):
        baseline = self.index["method:last-observed-value:v1"]
        target_ids = {
            "target:us-cpi-all-items-mom-sa:v1",
            "target:us-unemployment-rate-u3-sa:v1",
            "target:us-real-gdp-qoq-saar-advance:v1",
        }
        refs = baseline["compatible_target_refs"]
        self.assertEqual({ref["object_id"] for ref in refs}, target_ids)
        for ref in refs:
            self.assertEqual(
                self.index[ref["object_id"]]["content_sha256"],
                ref["content_sha256"],
            )


if __name__ == "__main__":
    unittest.main()
