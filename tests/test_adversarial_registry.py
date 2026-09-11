import json
import pathlib
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]; REGISTRY=ROOT/"fixtures"/"synthetic"/"adversarial_registry.json"
class AdversarialRegistryTests(unittest.TestCase):
    def test_all_96_cases_are_accounted_for(self): self.assertEqual(json.loads(REGISTRY.read_text())["synthetic_attack_paths_executed"],list(range(1,97)))
    def test_synthetic_origin_is_explicit(self):
        r=json.loads(REGISTRY.read_text()); self.assertEqual(r["origin_class"],"SYNTHETIC"); self.assertIs(r["prospective_eligible"],False); self.assertTrue(r["external_positive_evidence_note"])
if __name__=="__main__": unittest.main()
