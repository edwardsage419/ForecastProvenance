import unittest

from forecast_trust_core import CanonicalizationError, Result, canonical_json, require_ascii_token, require_decimal_string, seal_object, validate_cycle_manifest, validate_cycle_plan, validate_dependency, validate_external_deadline, validate_point_in_time, validate_selection_control, verify_sealed_object


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def slot(name):
    return seal_object({"schema_version": "0.4", "target": name}, object_type="Slot", stable_context=name)


def plan(slots, deadline="2026-09-11T01:00:00Z", window="2026-09-11T02:00:00Z"):
    refs = sorted([ref(s) for s in slots], key=lambda r: (r["object_id"], r["content_sha256"]))
    return seal_object({"schema_version":"0.4","plan_commitment_deadline":deadline,"execution_window_open":window,"execution_window_close":"2026-09-11T03:00:00Z","expected_slots":refs}, object_type="IssuanceCyclePlan", stable_context="adv")


class AdversarialExecutionTests(unittest.TestCase):
    def test_21_automated_cases_fail_closed(self):
        s = slot("a")
        p = plan([s])
        dep = seal_object({"schema_version": "0.4", "x": "y"}, object_type="Dependency", stable_context="d")
        store = {dep["object_id"]: dep}
        allowed = [ref(dep)]
        cases = {
            "ADV001": lambda: validate_point_in_time([{"available_at":"2026-09-12T00:00:00Z"}], "2026-09-11T00:00:00Z").result == Result.INVALID,
            "ADV002": lambda: validate_point_in_time([{}], "2026-09-11T00:00:00Z").result == Result.INELIGIBLE_TRUST_UNKNOWN,
            "ADV021": lambda: validate_external_deadline("2026-09-11T11:00:00Z", "2026-09-11T10:00:00Z").result == Result.LATE_OR_INELIGIBLE,
            "ADV027": lambda: not verify_sealed_object({**dep, "content_sha256":"0"*64}),
            "ADV030": self._float_rejected,
            "ADV031": self._decimal_rejected,
            "ADV033": lambda: validate_dependency({"object_id":dep["object_id"],"content_sha256":"0"*64}, store, allowed).status == "FAIL",
            "ADV041": self._circular_input_rejected,
            "ADV042": lambda: not verify_sealed_object({**dep, "x":"mutated"}),
            "ADV045": lambda: validate_external_deadline("2026-09-11T11:00:00Z", "2026-09-11T10:00:00Z").result == Result.LATE_OR_INELIGIBLE,
            "ADV047": lambda: self._missing_slot_invalid(p),
            "ADV059": self._non_ascii_token_rejected,
            "ADV060": self._unsorted_plan_invalid,
            "ADV063": lambda: validate_dependency(ref(dep), {}, allowed).status == "UNKNOWN",
            "ADV065": lambda: validate_cycle_plan(p, verified_plan_existence_bound="2026-09-11T01:30:00Z", required_slots=[ref(s)]).result == Result.INVALID,
            "ADV066": lambda: self._zero_margin_invalid(s),
            "ADV069": lambda: self._multi_forecast_slot_invalid(p, s),
            "ADV072": lambda: validate_selection_control({"selection_control_class":"UNCONTROLLED_NONDETERMINISM"}, {}).result == Result.INVALID,
            "ADV073": lambda: validate_selection_control({"selection_control_class":"DETERMINISTIC_REPLAY"}, {"replay_verified":False}).result == Result.INVALID,
            "ADV074": lambda: validate_selection_control({"selection_control_class":"EXTERNALLY_AUDITED_ATTEMPTS"}, {"complete_request_accounting":False}).result == Result.INVALID,
            "ADV078": lambda: validate_dependency({"object_id":dep["object_id"],"content_sha256":"f"*64}, store, allowed).status == "FAIL"
        }
        self.assertEqual(len(cases), 21)
        for case_id, func in cases.items():
            with self.subTest(case_id=case_id):
                self.assertTrue(func())

    def _float_rejected(self):
        try: canonical_json({"p":0.5})
        except CanonicalizationError: return True
        return False

    def _decimal_rejected(self):
        try: require_decimal_string("1.0", probability=True)
        except CanonicalizationError: return True
        return False

    def _circular_input_rejected(self):
        try: seal_object({"object_id":"x","schema_version":"0.4"}, object_type="Event", stable_context="x")
        except CanonicalizationError: return True
        return False

    def _non_ascii_token_rejected(self):
        try: require_ascii_token("targét")
        except CanonicalizationError: return True
        return False

    def _missing_slot_invalid(self, p):
        m = seal_object({"schema_version":"0.4","cycle_plan_ref":ref(p),"slot_accounting":[]}, object_type="IssuanceCycleManifest", stable_context="missing")
        return validate_cycle_manifest(p, m).result == Result.INVALID

    def _unsorted_plan_invalid(self):
        a,b=slot("a"),slot("b")
        refs=sorted([ref(a),ref(b)], key=lambda r:(r["object_id"],r["content_sha256"]), reverse=True)
        p=seal_object({"schema_version":"0.4","plan_commitment_deadline":"2026-09-11T01:00:00Z","execution_window_open":"2026-09-11T02:00:00Z","execution_window_close":"2026-09-11T03:00:00Z","expected_slots":refs}, object_type="IssuanceCyclePlan", stable_context="unsorted")
        return validate_cycle_plan(p, verified_plan_existence_bound="2026-09-11T00:30:00Z", required_slots=[ref(a),ref(b)]).result == Result.INVALID

    def _zero_margin_invalid(self, s):
        p=plan([s], deadline="2026-09-11T02:00:00Z", window="2026-09-11T02:00:00Z")
        return validate_cycle_plan(p, verified_plan_existence_bound="2026-09-11T01:00:00Z", required_slots=[ref(s)]).result == Result.INVALID

    def _multi_forecast_slot_invalid(self, p, s):
        m=seal_object({"schema_version":"0.4","cycle_plan_ref":ref(p),"slot_accounting":[{"slot_ref":ref(s),"outcome":"ISSUED","issued_forecast_refs":[ref(s),ref(s)]}]}, object_type="IssuanceCycleManifest", stable_context="multi")
        return validate_cycle_manifest(p, m).result == Result.INVALID


if __name__ == "__main__":
    unittest.main()
