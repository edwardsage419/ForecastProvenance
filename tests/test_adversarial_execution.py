import unittest
from forecast_trust_core import Result, validate_external_deadline
class CompatibilitySmokeTests(unittest.TestCase):
    def test_pending_external_evidence_is_not_prospective(self): self.assertEqual(validate_external_deadline(None,"2026-09-11T10:00:00Z").result,Result.PENDING_EXTERNAL_ANCHOR)
if __name__=="__main__": unittest.main()
