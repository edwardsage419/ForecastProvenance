import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "fixtures" / "synthetic" / "adversarial_registry.json"


class AdversarialRegistryTests(unittest.TestCase):
    def test_all_96_cases_are_accounted_for_exactly_once(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        groups = [registry["automated"], registry["design_boundary"], registry["genesis_boundary"]]
        flat = [case for group in groups for case in group]
        self.assertEqual(len(flat), 96)
        self.assertEqual(sorted(flat), list(range(1, 97)))
        self.assertEqual(len(set(flat)), 96)

    def test_synthetic_origin_is_explicit(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.assertEqual(registry["origin_class"], "SYNTHETIC")
        self.assertIs(registry["prospective_eligible"], False)
        self.assertTrue(registry["boundary_rule"])


if __name__ == "__main__":
    unittest.main()
