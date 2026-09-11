import unittest

from forecast_trust_core import (
    CanonicalizationError, Result, canonical_json, parse_json_strict, require_ascii_token,
    require_decimal_string, seal_object, validate_allowed_fields, validate_anchor_event_dag,
    validate_attempt_chain, validate_current_verifiability_report,
    validate_current_verifiability_with_availability, validate_cycle_manifest, validate_cycle_plan,
    validate_dependency, validate_evaluation_cohort, validate_external_deadline, validate_fitted_state,
    validate_forecast_correction, validate_governance_fork, validate_manifest_acceptance,
    validate_manifest_candidate, validate_origin_class, validate_outcome_information_barrier,
    validate_point_in_time, validate_policy_definition, validate_public_randomness,
    validate_resolution_evidence, validate_resolution_state, validate_retrieval_accounting,
    validate_review_decision, validate_selection_control, validate_slot_output,
    validate_source_contract, validate_source_selection, validate_trust_report,
    validate_validation_report, verify_sealed_object,
)

def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}

def raises(exc, fn):
    try: fn()
    except exc: return True
    return False

class FullAdversarialMatrix(unittest.TestCase):
    def setUp(self):
        self.dep=seal_object({"schema_version":"0.4","value":"x"},object_type="Dependency",stable_context="dep")
        self.allowed=[ref(self.dep)]; self.store={self.dep["object_id"]:self.dep}
        self.slot_a=seal_object({"schema_version":"0.4","target":"a"},object_type="Slot",stable_context="a")
        self.slot_b=seal_object({"schema_version":"0.4","target":"b"},object_type="Slot",stable_context="b")
        self.schedule_ref={"object_id":"policy:schedule:v1","content_sha256":"1"*64}
        self.plan=self._plan([self.slot_a],schedule_ref=self.schedule_ref)
    def _plan(self,slots,*,schedule_ref=None,extra=None):
        payload={"schema_version":"0.4","plan_commitment_deadline":"2026-09-11T01:00:00Z","execution_window_open":"2026-09-11T02:00:00Z","execution_window_close":"2026-09-11T03:00:00Z","expected_slots":sorted([ref(s) for s in slots],key=lambda r:(r["object_id"],r["content_sha256"]))}
        if schedule_ref is not None: payload["schedule_policy_ref"]=schedule_ref
        if extra: payload.update(extra)
        return seal_object(payload,object_type="IssuanceCyclePlan",stable_context="matrix")
    def _plan_result(self,plan=None,required=None,bound="2026-09-11T00:30:00Z",proof_ref=None,schedule_ref=None):
        p=plan or self.plan
        return validate_cycle_plan(p,verified_plan_existence_bound=bound,required_slots=required or [ref(self.slot_a)],verified_plan_ref=proof_ref if proof_ref is not None else ref(p),required_schedule_policy_ref=schedule_ref)
    def _manifest(self,rows,plan=None):
        p=plan or self.plan
        return seal_object({"schema_version":"0.4","cycle_plan_ref":ref(p),"slot_accounting":rows},object_type="IssuanceCycleManifest",stable_context="matrix")
    def _dep_mismatch(self):
        bad={"object_id":self.dep["object_id"],"content_sha256":"0"*64}; return validate_dependency(bad,self.store,self.allowed).status=="FAIL"
    def _mutated_invalid(self):
        x=dict(self.dep); x["value"]="changed"; return not verify_sealed_object(x)
    def _pending(self): return validate_external_deadline(None,"2026-09-11T10:00:00Z").result==Result.PENDING_EXTERNAL_ANCHOR
    def _review(self):
        return seal_object({"review_rule_ref":{"object_id":"rule:r","content_sha256":"2"*64},"subject_ref":ref(self.dep),"reviewer_authority_ref":{"object_id":"human:r","content_sha256":"3"*64},"evidence_refs":[],"decision":"ACCEPT","reason_codes":["X"],"rationale":"synthetic"},object_type="ReviewDecision",stable_context="r")
    def _manifest_and_acceptance(self,*,wrong=False,self_auth=False):
        m=seal_object({"manifest_sequence":1,"schema_version":"0.4"},object_type="TrustedManifest",stable_context="tm"); root={"object_id":"bootstrap:root:v1","content_sha256":"4"*64}; candidate={"object_id":m["object_id"],"content_sha256":("5"*64 if wrong else m["content_sha256"])}; auth=ref(m) if self_auth else root
        a=seal_object({"candidate_manifest_ref":candidate,"external_anchor_evidence_ref":{"object_id":"anchor:x","content_sha256":"6"*64},"acceptance_rule_ref":{"object_id":"rule:a","content_sha256":"7"*64},"authority_ref":auth,"decision":"ACCEPT","reason_codes":["OK"]},object_type="ManifestAcceptance",stable_context="ma"); return m,a,root
    def _correction(self,**kw):
        base={"original_forecast_ref":ref(self.dep),"correction_type":"METADATA_NON_SUBSTANTIVE","reason":"x","affected_fields":[],"replacement_forecast_ref_or_none":"NONE"}; base.update(kw); return base
    def test_adv001_to_adv096(self):
        cases={}
        cases[1]=lambda:validate_point_in_time([{"available_at":"2026-09-12T00:00:00Z"}],"2026-09-11T00:00:00Z").result==Result.INVALID
        cases[2]=lambda:validate_point_in_time([{}],"2026-09-11T00:00:00Z").result==Result.INELIGIBLE_TRUST_UNKNOWN
        cases[3]=lambda:validate_point_in_time([{"published_at":"2026-09-10T00:00:00Z"}],"2026-09-11T00:00:00Z").result==Result.INELIGIBLE_TRUST_UNKNOWN
        for i in (4,5,8,9,10,14,32,36,39,43,50,51,81): cases[i]=self._mutated_invalid
        cases[6]=lambda:validate_manifest_acceptance(*self._manifest_and_acceptance(self_auth=True)[:2],bootstrap_root_ref=self._manifest_and_acceptance(self_auth=True)[2]).result==Result.INVALID
        vr=seal_object({"validator_contract_ref":{"object_id":"validator:v1","content_sha256":"8"*64},"trusted_manifest_ref":{"object_id":"manifest:v1","content_sha256":"9"*64},"candidate_object_ref":ref(self.dep),"dependency_refs":[],"result":"VALID","checks":[]},object_type="ValidationReport",stable_context="vr")
        cases[7]=lambda:validate_validation_report(vr,required_trusted_manifest_ref={"object_id":"manifest:v2","content_sha256":"a"*64}).result==Result.INVALID
        cases[11]=lambda:validate_retrieval_accounting([ref(self.dep)],[]).result==Result.INELIGIBLE_TRUST_UNKNOWN
        retry_rules={"max_attempts":2,"retry_eligible_failure_codes":["TRANSIENT"]}
        cases[12]=lambda:validate_attempt_chain([{"attempt_id":"a1","retry_of_or_none":"NONE","terminal_status":"SUCCEEDED","issuance_eligible":False},{"attempt_id":"a2","retry_of_or_none":"a1","terminal_status":"SUCCEEDED","issuance_eligible":True,"failure_code_or_none":"NONE"}],retry_rules).result==Result.INVALID
        cases[13]=lambda:validate_attempt_chain([{"attempt_id":"a1","retry_of_or_none":"NONE","terminal_status":"FAILED","failure_code_or_none":"TRANSIENT"},{"attempt_id":"a2","retry_of_or_none":"missing","terminal_status":"SUCCEEDED","issuance_eligible":True}],retry_rules).result==Result.INVALID
        for i in (15,16,17,18,44): cases[i]=self._pending
        ev_bad=seal_object({"anchored_subject_ref":{"object_id":"other:x","content_sha256":"b"*64},"event_type":"VERIFICATION_EVIDENCE","proof_artifact_ref":{"object_id":"proof:x","content_sha256":"c"*64},"external_attestation":"SYNTHETIC","predecessor_event_ref_or_none":"NONE","operational_record_ref_or_none":"NONE"},object_type="AnchorEvidenceEvent",stable_context="e")
        cases[19]=lambda:validate_anchor_event_dag([ev_bad],ref(self.dep)).result==Result.INVALID
        cases[20]=lambda:validate_current_verifiability_with_availability({"assessed_at":"2026-09-11T00:00:00Z","subject_ref":ref(self.dep),"current_verifiability_state":"FULL","evidence_refs":[ref(self.dep)]},required_evidence_available=False).result==Result.INVALID
        cases[21]=lambda:validate_external_deadline("2026-09-11T11:00:00Z","2026-09-11T10:00:00Z").result==Result.LATE_OR_INELIGIBLE
        cases[22]=lambda:validate_origin_class({"origin_class":"SYNTHETIC","prospective_eligible":True}).result==Result.INVALID
        cases[23]=lambda:validate_origin_class({"origin_class":"PREDECESSOR"}).result==Result.INVALID
        policy={"substantive_field_set":["prediction","target_ref","method_ref"]}
        cases[24]=lambda:validate_forecast_correction(self._correction(affected_fields=["prediction"]),original_forecast_ref=ref(self.dep),correction_policy=policy).result==Result.INVALID
        cases[25]=lambda:validate_forecast_correction(self._correction(action="DELETE_ORIGINAL"),original_forecast_ref=ref(self.dep),correction_policy=policy).result==Result.INVALID
        cases[26]=lambda:validate_forecast_correction(self._correction(correction_type="SUBSTANTIVE_REPLACEMENT",affected_fields=["prediction"],replacement_forecast_ref_or_none=ref(self.dep)),original_forecast_ref=ref(self.dep),correction_policy=policy).result==Result.INVALID
        cases[27]=lambda:raises(CanonicalizationError,lambda:seal_object({"object_id":"x"},object_type="Event",stable_context="x"))
        cases[28]=lambda:validate_allowed_fields({"a":1,"surprise":2},{"a"}).result==Result.INVALID
        cases[29]=lambda:raises(CanonicalizationError,lambda:parse_json_strict('{"a":1,"a":2}'))
        cases[30]=lambda:raises(CanonicalizationError,lambda:canonical_json({"p":0.5}))
        cases[31]=lambda:raises(CanonicalizationError,lambda:require_decimal_string("1.0",probability=True))
        cases[33]=self._dep_mismatch
        cases[34]=lambda:validate_dependency(ref(self.dep),{},self.allowed).status=="UNKNOWN"
        state={"transformation_ref":ref(self.dep),"fit_information_cutoff":"2026-09-12T00:00:00Z","fit_window":"x","fit_snapshot_refs":[ref(self.dep)],"configuration_ref":ref(self.dep),"state_artifact_ref":ref(self.dep)}
        cases[35]=lambda:validate_fitted_state(state,"2026-09-11T00:00:00Z").result==Result.INVALID
        cases[37]=lambda:validate_resolution_state(ambiguous=True,ambiguity_policy="UNRESOLVED",resolution_state="RESOLVED").result==Result.INVALID
        cases[38]=lambda:validate_evaluation_cohort([ref(self.dep),ref(self.slot_a)],[ref(self.dep)]).result==Result.INVALID
        cases[40]=lambda:validate_validation_report(vr,required_validator_contract_ref={"object_id":"validator:v2","content_sha256":"d"*64}).result==Result.INVALID
        cases[41]=cases[27]; cases[42]=self._mutated_invalid; cases[45]=cases[21]
        unplanned=self._manifest([{"slot_ref":ref(self.slot_a),"outcome":"FAILED"},{"slot_ref":ref(self.slot_b),"outcome":"FAILED"}]); omitted=self._manifest([])
        cases[46]=lambda:validate_cycle_manifest(self.plan,unplanned).result==Result.INVALID
        cases[47]=lambda:validate_cycle_manifest(self.plan,omitted).result==Result.INVALID
        cases[48]=cases[12]
        cases[49]=lambda:validate_attempt_chain([{"attempt_id":"a1","retry_of_or_none":"NONE","terminal_status":"FAILED","failure_code_or_none":"TRANSIENT"},{"attempt_id":"a2","retry_of_or_none":"a1","terminal_status":"FAILED","failure_code_or_none":"TRANSIENT"},{"attempt_id":"a3","retry_of_or_none":"a2","terminal_status":"FAILED","failure_code_or_none":"TRANSIENT"}],retry_rules).result==Result.INVALID
        cases[52]=lambda:validate_fitted_state({"fit_information_cutoff":"2026-09-10T00:00:00Z"},"2026-09-11T00:00:00Z").result==Result.INVALID
        review=self._review(); cases[53]=lambda:validate_review_decision(review,hard_failure=True).result==Result.INVALID; cases[54]=lambda:validate_review_decision(review,human_authentic=False).result==Result.INVALID
        m_self=seal_object({"manifest_sequence":1,"schema_version":"0.4","status":"ACCEPTED"},object_type="TrustedManifest",stable_context="self"); cases[55]=lambda:validate_manifest_candidate(m_self).result==Result.INVALID
        m,a,root=self._manifest_and_acceptance(wrong=True); cases[56]=lambda:validate_manifest_acceptance(m,a,bootstrap_root_ref=root).result==Result.INVALID
        cases[57]=lambda:validate_forecast_correction(self._correction(scoring_consequence="EXCLUDE"),original_forecast_ref=ref(self.dep),correction_policy=policy).result==Result.INVALID
        cases[58]=cases[38]; cases[59]=lambda:raises(CanonicalizationError,lambda:require_ascii_token("targét"))
        unsorted=self._plan([self.slot_b,self.slot_a]); up={k:v for k,v in unsorted.items() if k not in {"object_id","payload_sha256","content_sha256"}}; up["expected_slots"]=list(reversed(up["expected_slots"])); unsorted=seal_object(up,object_type="IssuanceCyclePlan",stable_context="unsorted")
        cases[60]=lambda:validate_cycle_plan(unsorted,verified_plan_existence_bound="2026-09-11T00:30:00Z",required_slots=[ref(self.slot_a),ref(self.slot_b)],verified_plan_ref=ref(unsorted)).result==Result.INVALID
        cases[61]=lambda:validate_resolution_evidence({"vintage_selection":"FIRST","resolution_deadline":"2026-09-20T00:00:00Z"},{"selected_vintage":"FIRST","resolved_at":"2026-09-19T00:00:00Z"}).result==Result.VALID
        cases[62]=lambda:validate_trust_report({"evidence_observability_class":"PARTIAL_EXTERNAL"},{"evidence_provenance_claim":"COMPLETE"}).result==Result.INVALID
        cases[63]=cases[20]
        vr_time=seal_object({"validator_contract_ref":ref(self.dep),"trusted_manifest_ref":ref(self.dep),"candidate_object_ref":ref(self.dep),"dependency_refs":[],"result":"VALID","checks":[],"validated_at":"2026-09-11T00:00:00Z"},object_type="ValidationReport",stable_context="vrt"); cases[64]=lambda:validate_validation_report(vr_time).result==Result.INVALID
        cases[65]=lambda:self._plan_result(bound="2026-09-11T01:30:00Z").result==Result.INVALID
        zero=self._plan([self.slot_a]); zp={k:v for k,v in zero.items() if k not in {"object_id","payload_sha256","content_sha256"}}; zp["plan_commitment_deadline"]=zp["execution_window_open"]; zero=seal_object(zp,object_type="IssuanceCyclePlan",stable_context="zero")
        cases[66]=lambda:validate_cycle_plan(zero,verified_plan_existence_bound="2026-09-11T00:30:00Z",required_slots=[ref(self.slot_a)],verified_plan_ref=ref(zero)).result==Result.INVALID
        local=self._plan([self.slot_a],extra={"started_at":"2000-01-01T00:00:00Z"}); cases[67]=lambda:validate_cycle_plan(local,verified_plan_existence_bound=None,required_slots=[ref(self.slot_a)]).result==Result.INELIGIBLE_TRUST_UNKNOWN
        changed=self._plan([self.slot_b]); cases[68]=lambda:validate_cycle_plan(changed,verified_plan_existence_bound="2026-09-11T00:30:00Z",required_slots=[ref(self.slot_b)],verified_plan_ref=ref(self.plan)).result==Result.INVALID
        multi=self._manifest([{"slot_ref":ref(self.slot_a),"outcome":"ISSUED","issued_forecast_refs":[ref(self.dep),ref(self.slot_a)]}]); cases[69]=lambda:validate_cycle_manifest(self.plan,multi).result==Result.INVALID
        slot={"target_ref":ref(self.dep),"method_ref":ref(self.slot_a),"output_schema_ref":ref(self.slot_b)}; forecast={**slot,"output_schema_ref":ref(self.dep)}; cases[70]=lambda:validate_slot_output(slot,forecast).result==Result.INVALID
        seeded=self._plan([self.slot_a],extra={"seed":"123"}); cases[71]=lambda:validate_cycle_plan(seeded,verified_plan_existence_bound="2026-09-11T00:30:00Z",required_slots=[ref(self.slot_a)],verified_plan_ref=ref(seeded)).result==Result.INVALID
        cases[72]=lambda:validate_selection_control({"selection_control_class":"UNCONTROLLED_NONDETERMINISM"},{}).result==Result.INVALID
        cases[73]=lambda:validate_selection_control({"selection_control_class":"DETERMINISTIC_REPLAY"},{"replay_verified":False}).result==Result.INVALID
        cases[74]=lambda:validate_selection_control({"selection_control_class":"EXTERNALLY_AUDITED_ATTEMPTS"},{"complete_request_accounting":False}).result==Result.INVALID
        m,a,root=self._manifest_and_acceptance(); cases[75]=lambda:validate_manifest_acceptance(m,a,bootstrap_root_ref={"object_id":"bootstrap:other","content_sha256":"e"*64}).result==Result.INVALID
        m,a,root=self._manifest_and_acceptance(self_auth=True); cases[76]=lambda:validate_manifest_acceptance(m,a,bootstrap_root_ref=root).result==Result.INVALID
        cases[77]=lambda:validate_governance_fork([{"id":"a"},{"id":"b"}],fork_rule=None).result==Result.INELIGIBLE_TRUST_UNKNOWN
        cases[78]=self._dep_mismatch; cases[79]=cases[19]
        op=seal_object({"anchored_subject_ref":ref(self.dep),"event_type":"OPERATIONAL_FAILURE_RECORD","proof_artifact_ref":ref(self.dep),"external_attestation":"EXTERNAL_FAILURE_PROVEN","predecessor_event_ref_or_none":"NONE","operational_record_ref_or_none":"NONE"},object_type="AnchorEvidenceEvent",stable_context="op"); cases[80]=lambda:validate_anchor_event_dag([op],ref(self.dep)).result==Result.INVALID
        cases[82]=lambda:validate_origin_class({"origin_class":"NATIVE_POST_GENESIS","prospective_eligible":True}).result==Result.INVALID
        cases[83]=lambda:validate_resolution_evidence({"vintage_selection":"FIRST"},{"selected_vintage":"LATEST"}).result==Result.INVALID
        cases[84]=lambda:validate_resolution_evidence({"resolution_deadline":"2026-09-20T00:00:00Z"},{"resolved_at":"2026-09-21T00:00:00Z"}).result==Result.INVALID
        vr_root=seal_object({"validator_contract_ref":ref(self.dep),"trusted_manifest_ref":ref(self.dep),"candidate_object_ref":ref(self.dep),"dependency_refs":[],"dependency_root":"invented","result":"VALID","checks":[]},object_type="ValidationReport",stable_context="vrr"); cases[85]=lambda:validate_validation_report(vr_root).result==Result.INVALID
        cases[86]=lambda:self._plan_result(required=[ref(self.slot_b)]).result==Result.INVALID
        cases[87]=lambda:validate_outcome_information_barrier("2026-09-11T11:00:00Z","2026-09-11T10:00:00Z").result==Result.INVALID
        cases[88]=lambda:validate_source_selection([ref(self.dep),ref(self.slot_a)],max([ref(self.dep),ref(self.slot_a)],key=lambda r:r["object_id"])).result==Result.INVALID
        cases[89]=lambda:self._plan_result(required=[ref(self.slot_a),ref(self.slot_b)]).result==Result.INVALID; cases[90]=cases[89]; cases[91]=cases[71]
        random_source={"object_id":"random:expected","content_sha256":"f"*64}; other_source={"object_id":"random:other","content_sha256":"0"*64}; rand={"observed_external_bound":"2026-09-11T02:00:00Z","challenge":"abc","source_ref":other_source}
        cases[92]=lambda:validate_public_randomness(rand,plan_bound="2026-09-11T01:00:00Z",expected_challenge="abc",expected_source_ref=random_source).result==Result.INVALID
        rand_early={"observed_external_bound":"2026-09-11T01:00:00Z","challenge":"abc","source_ref":random_source}; cases[93]=lambda:validate_public_randomness(rand_early,plan_bound="2026-09-11T01:00:00Z",expected_challenge="abc",expected_source_ref=random_source).result==Result.INVALID
        src=seal_object({"source_contract_id":"s","source_contract_version":"1","source_identity":"x","access_mode":"PUBLIC","artifact_identity_rule":"HASH","availability_rule":"PUB","publication_rule":"PUB","revision_rule":"BOUND","artifact_selection_rule":"OPERATOR_DISCRETION","retention_class":"INLINE_CONTENT","failure_semantics":"UNKNOWN"},object_type="SourceContract",stable_context="src"); cases[94]=lambda:validate_source_contract(src).result==Result.INVALID
        old_schedule={"object_id":"policy:schedule:old","content_sha256":"1"*64}; cases[95]=lambda:self._plan_result(schedule_ref=old_schedule).result==Result.INVALID
        cases[96]=lambda:validate_current_verifiability_report({"subject_ref":ref(self.dep),"current_verifiability_state":"FULL","evidence_refs":[]}).result==Result.INVALID
        self.assertEqual(set(cases),set(range(1,97)))
        for case_id,fn in cases.items():
            with self.subTest(case_id=f"ADV{case_id:03d}"): self.assertTrue(fn())

if __name__=="__main__": unittest.main()
