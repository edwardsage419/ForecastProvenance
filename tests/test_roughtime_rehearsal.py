import base64, copy, hashlib, unittest
from datetime import datetime, timezone
from forecast_trust_core.canonical import canonical_json, seal_object
from forecast_trust_core.roughtime_rehearsal import (
    FAILURE_CODES, PACKET_PROFILE, PROVIDERS, PROVIDER_ORDER, TRANSPORT_PROFILE,
    VERIFIER_COMMIT, VERIFIER_REPOSITORY, VERIFIER_TAG, derive_nonce_v2_hex,
    upper_bound_utc, validate_authorization_record, validate_plan,
    validate_quorum_results, validate_rehearsal_report,
)

SUBJECT = "3837b8ce2e012a913cbdab6f7e52bdc045013bdc4acfbc88abc99cee149275c6"
DEADLINE = "2026-09-12T00:00:00Z"
SEAL_FIELDS = {"object_type", "object_id", "payload_sha256", "content_sha256"}


def plan_fixture():
    providers = []
    for i, p in enumerate(PROVIDERS, 1):
        rnd = (bytes([i]) * 32).hex()
        providers.append({**p.__dict__, "packet_profile": PACKET_PROFILE,
            "transport_profile": TRANSPORT_PROFILE, "client_random_hex": rnd,
            "nonce_profile": "FPP_ROUGHTIME_NONCE_V2",
            "nonce_hex": derive_nonce_v2_hex(SUBJECT, rnd), "maximum_attempts": 2,
            "timeout_per_attempt_seconds": 2, "retry_backoff_initial_seconds": 1,
            "retry_backoff_factor": "1.5", "retry_backoff_max_seconds": 86400,
            "retry_request_rule": "same_exact_request_bytes", "network_authorized": False})
    core = {"schema_version":"1.1", "classification":"NON_FORECAST_REHEARSAL",
        "prospective_eligible":False, "network_authorized":False,
        "subject_label":"SYNTHETIC_TEST_ONLY", "subject_sha256":SUBJECT,
        "frozen_deadline_utc":DEADLINE, "nonce_profile":"FPP_ROUGHTIME_NONCE_V2",
        "packet_profile":PACKET_PROFILE, "transport_profile":TRANSPORT_PROFILE,
        "provider_attempt_rule":"evaluate_all_three_frozen_providers_in_frozen_order_attempt_each_when_retry_eligible",
        "quorum_threshold":2, "retry_state_rule":"persist_per_root_until_properly_signed_response",
        "backoff_block_rule":"backoff_active_counts_nonqualifying_no_network_attempt",
        "verifier_repository":VERIFIER_REPOSITORY, "verifier_tag":VERIFIER_TAG,
        "verifier_commit":VERIFIER_COMMIT, "verifier_build_profile_sha256":"c"*64,
        "retry_state_snapshot_sha256":"d"*64, "providers":providers}
    return {**core, "plan_sha256": hashlib.sha256(canonical_json(core)).hexdigest()}


def auth_fixture(plan):
    core = {"schema_version":"1.0", "classification":"NON_FORECAST_REHEARSAL",
        "prospective_eligible":False, "network_authorized":True,
        "rehearsal_plan_sha256":plan["plan_sha256"], "subject_sha256":SUBJECT,
        "frozen_deadline_utc":DEADLINE, "provider_order":list(PROVIDER_ORDER),
        "verifier_commit":VERIFIER_COMMIT,
        "verifier_build_profile_sha256":plan["verifier_build_profile_sha256"],
        "retry_state_snapshot_sha256":plan["retry_state_snapshot_sha256"],
        "authorized_by":"test:operator", "authorized_at_utc":"2026-09-11T23:00:00Z",
        "authorization_scope":"exact_plan_only_no_prospective_use"}
    return {**core, "authorization_sha256":hashlib.sha256(canonical_json(core)).hexdigest()}


def receipt_fixture(plan, auth, pid):
    p = next(x for x in PROVIDERS if x.provider_id == pid)
    item = next(x for x in plan["providers"] if x["provider_id"] == pid)
    req, resp = f"request:{pid}".encode(), f"response:{pid}".encode()
    payload = {"schema_version":"1.1", "classification":"NON_FORECAST_REHEARSAL",
        "prospective_eligible":False, "rehearsal_plan_sha256":plan["plan_sha256"],
        "authorization_record_sha256":auth["authorization_sha256"], **p.__dict__,
        "packet_profile":PACKET_PROFILE, "transport_profile":TRANSPORT_PROFILE,
        "subject_sha256":SUBJECT, "client_random_hex":item["client_random_hex"],
        "nonce_profile":"FPP_ROUGHTIME_NONCE_V2", "nonce_hex":item["nonce_hex"],
        "request_sha256":hashlib.sha256(req).hexdigest(), "request_base64":base64.b64encode(req).decode(),
        "response_sha256":hashlib.sha256(resp).hexdigest(), "response_base64":base64.b64encode(resp).decode(),
        "verifier_repository":VERIFIER_REPOSITORY, "verifier_tag":VERIFIER_TAG,
        "verifier_commit":VERIFIER_COMMIT, "verifier_source_sha256":"a"*64,
        "verifier_binary_sha256":"b"*64, "verifier_build_profile_sha256":plan["verifier_build_profile_sha256"],
        "verification_transcript_sha256":"e"*64, "midpoint_utc":"2026-09-11T23:59:50Z",
        "radius_seconds":3, "verified_receipt_upper_bound_utc":"2026-09-11T23:59:53Z",
        "frozen_deadline_utc":DEADLINE, "root_key_match":True, "wire_profile_match":True,
        "delegation_verified":True, "signature_verified":True, "nonce_verified":True,
        "merkle_proof_verified":True, "midpoint_inside_delegation":True,
        "upper_bound_at_or_before_deadline":True, "qualifies":True}
    return seal_object(payload, object_type="RoughtimeReceipt", stable_context=pid,
        semantic_id=f"roughtimereceipt:{pid}")


def report_fixture():
    plan, auth = plan_fixture(), None
    auth = auth_fixture(plan)
    results=[]
    for i,pid in enumerate(PROVIDER_ORDER):
        req, resp = f"request:{pid}".encode(), f"response:{pid}".encode()
        attempt={"attempt_number":1,"request_sha256":hashlib.sha256(req).hexdigest(),
            "request_base64":base64.b64encode(req).decode()}
        if i<2:
            attempt.update(response_sha256=hashlib.sha256(resp).hexdigest(),
                response_base64=base64.b64encode(resp).decode(), outcome="QUALIFYING_VERIFIED_RESPONSE")
            results.append({"provider_id":pid,"attempts":[attempt],"qualifies":True,
                "receipt":receipt_fixture(plan,auth,pid)})
        else:
            attempt.update(outcome="FAILED", failure_code="TRANSPORT_TIMEOUT")
            results.append({"provider_id":pid,"attempts":[attempt],"qualifies":False,
                "final_failure_code":"TRANSPORT_TIMEOUT"})
    payload={"schema_version":"1.1","classification":"NON_FORECAST_REHEARSAL",
        "prospective_eligible":False,"network_authorized_by_report":False,
        "rehearsal_plan_sha256":plan["plan_sha256"],"authorization_record_sha256":auth["authorization_sha256"],
        "subject_sha256":SUBJECT,"provider_attempt_order":list(PROVIDER_ORDER),"quorum_threshold":2,
        "verifier_repository":VERIFIER_REPOSITORY,"verifier_tag":VERIFIER_TAG,"verifier_commit":VERIFIER_COMMIT,
        "verifier_build_profile_sha256":plan["verifier_build_profile_sha256"],
        "retry_state_before_sha256":plan["retry_state_snapshot_sha256"],"retry_state_after_sha256":"f"*64,
        "execution_transcript_sha256":"1"*64,"provider_results":results,"qualifying_provider_count":2,
        "final_rehearsal_status":"REHEARSAL_VERIFIED"}
    report=seal_object(payload,object_type="RoughtimeRehearsalReport",stable_context="test",
        semantic_id="roughtimerehearsalreport:test")
    return plan,auth,report


def reseal(report, suffix="bad"):
    payload={k:v for k,v in report.items() if k not in SEAL_FIELDS}
    return seal_object(payload,object_type="RoughtimeRehearsalReport",stable_context=suffix,
        semantic_id=f"roughtimerehearsalreport:{suffix}")


class RoughtimeRehearsalTests(unittest.TestCase):
    def test_nonce_vector_and_pool_profiles(self):
        rnd="000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
        self.assertEqual(derive_nonce_v2_hex(SUBJECT,rnd),"f1aac0ea4fe95337ffe47119d0988c674509188eeff0e76d8e9df2040fff0223")
        self.assertEqual(PROVIDER_ORDER,("roughtime.se","time.txryan.com","TimeNL-Roughtime"))
        self.assertEqual([p.require_type for p in PROVIDERS],[True,True,False])
        self.assertTrue(all(p.offered_version_hex=="0x8000000c" for p in PROVIDERS))

    def test_plan_authorization_and_quorum_types(self):
        plan=plan_fixture(); validate_plan(plan); auth=auth_fixture(plan); validate_authorization_record(auth,plan)
        self.assertTrue(validate_quorum_results(dict(zip(PROVIDER_ORDER,[True,True,False]))))
        with self.assertRaises(ValueError): validate_quorum_results(dict(zip(PROVIDER_ORDER,[1,True,False])))
        with self.assertRaises(ValueError): upper_bound_utc(datetime(2026,9,11,tzinfo=timezone.utc),0)

    def test_valid_report(self):
        plan,auth,report=report_fixture(); validate_rehearsal_report(report,plan=plan,authorization=auth)

    def test_cross_field_report_tampering_fails(self):
        plan,auth,report=report_fixture()
        mutations=[]
        a=copy.deepcopy(report); a["qualifying_provider_count"]=1; mutations.append(a)
        b=copy.deepcopy(report); b["provider_results"][0].pop("receipt"); mutations.append(reseal(b,"no-receipt"))
        c=copy.deepcopy(report); c["provider_results"][0]["attempts"][0]["request_base64"]=base64.b64encode(b"tampered").decode(); mutations.append(reseal(c,"raw"))
        for bad in mutations:
            with self.subTest():
                with self.assertRaises(ValueError): validate_rehearsal_report(bad,plan=plan,authorization=auth)

    def test_retry_bytes_and_backoff_rules(self):
        plan,auth,report=report_fixture()
        r=copy.deepcopy(report); x=r["provider_results"][2]; req=b"different"
        x["attempts"].append({"attempt_number":2,"request_sha256":hashlib.sha256(req).hexdigest(),
            "request_base64":base64.b64encode(req).decode(),"outcome":"FAILED","failure_code":"TRANSPORT_TIMEOUT"})
        with self.assertRaises(ValueError): validate_rehearsal_report(reseal(r,"retry"),plan=plan,authorization=auth)
        r=copy.deepcopy(report); r["provider_results"][2]={"provider_id":"TimeNL-Roughtime","attempts":[],
            "qualifies":False,"final_failure_code":"BACKOFF_ACTIVE"}
        validate_rehearsal_report(reseal(r,"backoff"),plan=plan,authorization=auth)

    def test_verified_nonqualifying_stops_retry(self):
        plan,auth,report=report_fixture(); pid=PROVIDER_ORDER[2]
        req,resp=f"request:{pid}".encode(),f"response:{pid}".encode()
        terminal={"attempt_number":1,"request_sha256":hashlib.sha256(req).hexdigest(),
            "request_base64":base64.b64encode(req).decode(),"response_sha256":hashlib.sha256(resp).hexdigest(),
            "response_base64":base64.b64encode(resp).decode(),"outcome":"VERIFIED_NONQUALIFYING_RESPONSE",
            "failure_code":"UPPER_BOUND_AFTER_DEADLINE"}
        r=copy.deepcopy(report); r["provider_results"][2]={"provider_id":pid,"attempts":[terminal],
            "qualifies":False,"final_failure_code":"UPPER_BOUND_AFTER_DEADLINE"}
        validate_rehearsal_report(reseal(r,"nonqual"),plan=plan,authorization=auth)
        terminal2=copy.deepcopy(terminal); terminal2["failure_code"]="RADIUS_INVALID"
        retry={"attempt_number":2,"request_sha256":hashlib.sha256(req).hexdigest(),
            "request_base64":base64.b64encode(req).decode(),"outcome":"FAILED","failure_code":"TRANSPORT_TIMEOUT"}
        r["provider_results"][2]={"provider_id":pid,"attempts":[terminal2,retry],"qualifies":False,
            "final_failure_code":"TRANSPORT_TIMEOUT"}
        with self.assertRaises(ValueError): validate_rehearsal_report(reseal(r,"retry-after-verified"),plan=plan,authorization=auth)

    def test_authorization_deadline_and_binding_fail_closed(self):
        plan=plan_fixture(); auth=auth_fixture(plan)
        for when in (DEADLINE,"2026-09-12T00:00:01Z"):
            bad=dict(auth); bad["authorized_at_utc"]=when
            bad["authorization_sha256"]=hashlib.sha256(canonical_json({k:v for k,v in bad.items() if k!="authorization_sha256"})).hexdigest()
            with self.assertRaises(ValueError): validate_authorization_record(bad,plan)
        changed=copy.deepcopy(plan); changed["verifier_build_profile_sha256"]="0"*64
        changed["plan_sha256"]=hashlib.sha256(canonical_json({k:v for k,v in changed.items() if k!="plan_sha256"})).hexdigest()
        validate_plan(changed)
        with self.assertRaises(ValueError): validate_authorization_record(auth,changed)

    def test_plan_retry_policy_drift_fails(self):
        for field,value in (("retry_backoff_initial_seconds",2),("retry_backoff_factor","2"),
                            ("retry_backoff_max_seconds",2),("retry_request_rule","new_request_each_retry")):
            plan=plan_fixture(); plan["providers"][0][field]=value
            plan["plan_sha256"]=hashlib.sha256(canonical_json({k:v for k,v in plan.items() if k!="plan_sha256"})).hexdigest()
            with self.subTest(field=field):
                with self.assertRaises(ValueError): validate_plan(plan)

    def test_report_binding_and_failure_vocabulary(self):
        plan,auth,report=report_fixture()
        for field in ("verifier_build_profile_sha256","retry_state_before_sha256"):
            bad=copy.deepcopy(report); bad[field]="0"*64
            with self.subTest(field=field):
                with self.assertRaises(ValueError): validate_rehearsal_report(reseal(bad,field),plan=plan,authorization=auth)
        self.assertIn("RADIUS_INVALID",FAILURE_CODES); self.assertIn("RETRY_STATE_INVALID",FAILURE_CODES)
        self.assertNotIn("WHATEVER",FAILURE_CODES)


if __name__ == "__main__": unittest.main()
