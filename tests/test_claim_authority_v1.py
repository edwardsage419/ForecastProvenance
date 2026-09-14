from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

import forecast_trust_core.claim_authority_v1 as authority
from forecast_trust_core.canonical import seal_object
from forecast_trust_core.core import Result, Validation, validate_cycle_plan


PROVIDERS = ("roughtime.se", "time.txryan.com", "TimeNL-Roughtime")
DEADLINE = "2026-09-20T00:00:00Z"


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def sealed(kind, object_id, **payload):
    return seal_object(
        {"schema_version": "1.0", **payload},
        object_type=kind,
        stable_context="claim-authority-test",
        semantic_id=object_id,
    )


def make_validator_contract():
    return sealed("ValidatorContract", "validator:test:v1", contract="synthetic")


def make_wall_fixture(receipt_provider_ids=("roughtime.se", "time.txryan.com")):
    subject = sealed("Subject", "subject:test:v1", value="x")
    validator = make_validator_contract()
    quorum = sealed("PolicyDefinition", "policy:quorum:test:v1", policy_type="DEADLINE_RECEIPT_QUORUM")
    qualification_verifier = sealed("ValidatorContract", "validator:qualification:test:v1", contract="synthetic")
    build_profile = {"profile_sha256": "a" * 64}
    profiles = []
    packages = []
    for provider_id in PROVIDERS:
        decision = sealed("RoughtimeQualificationDecision", f"decision:{provider_id}:v1", provider_id=provider_id)
        profile = sealed(
            "RoughtimeProductionProviderProfile",
            f"profile:{provider_id}:v1",
            provider_id=provider_id,
            verifier_build_profile_sha256="a" * 64,
        )
        package = sealed(
            "RoughtimeProviderQualificationStatePackage",
            f"state:{provider_id}:v1",
            provider_id=provider_id,
            as_of_utc=DEADLINE,
            provider_profile_ref=ref(profile),
            qualification_decision_ref=ref(decision),
            qualification_state="PRODUCTION_QUALIFIED",
        )
        profiles.append(profile)
        packages.append(package)

    profile_by_id = {item["provider_id"]: item for item in profiles}
    package_by_id = {item["provider_id"]: item for item in packages}
    receipts = []
    for index, provider_id in enumerate(receipt_provider_ids):
        request = f"request:{provider_id}".encode()
        response = f"response:{provider_id}".encode()
        receipt = sealed(
            "RoughtimeProductionReceiptEvidence",
            f"receipt:{provider_id}:v1",
            origin_class="SYNTHETIC",
            prospective_eligible=False,
            subject_ref=ref(subject),
            frozen_deadline_utc=DEADLINE,
            provider_id=provider_id,
            provider_profile_ref=ref(profile_by_id[provider_id]),
            qualification_state_package_ref=ref(package_by_id[provider_id]),
            verifier_build_profile_sha256="a" * 64,
            client_random_hex=f"{index + 1:064x}",
            request_sha256=hashlib.sha256(request).hexdigest(),
            request_base64=base64.b64encode(request).decode("ascii"),
            response_sha256=hashlib.sha256(response).hexdigest(),
            response_base64=base64.b64encode(response).decode("ascii"),
        )
        receipts.append(receipt)

    bundle = sealed(
        "ExternalTimeEvidenceBundle",
        "time-bundle:test:v1",
        origin_class="SYNTHETIC",
        prospective_eligible=False,
        subject_ref=ref(subject),
        receipt_quorum_deadline_utc=DEADLINE,
        receipt_evidence_refs=sorted((ref(item) for item in receipts), key=lambda item: (item["object_id"], item["content_sha256"])),
        provider_profile_refs=sorted((ref(item) for item in profiles), key=lambda item: (item["object_id"], item["content_sha256"])),
        qualification_state_package_refs=sorted((ref(item) for item in packages), key=lambda item: (item["object_id"], item["content_sha256"])),
        quorum_policy_ref=ref(quorum),
        validator_contract_ref=ref(validator),
    )
    return {
        "subject": subject,
        "validator": validator,
        "quorum": quorum,
        "qualification_verifier": qualification_verifier,
        "profiles": profiles,
        "packages": packages,
        "receipts": receipts,
        "bundle": bundle,
        "build_profile": build_profile,
        "provider_inputs": {provider: {} for provider in PROVIDERS},
    }


class FakeRoughtimeBackend:
    def __init__(self, _binary, _profile):
        pass

    def build_request(self, provider):
        request = f"request:{provider['provider_id']}".encode()
        return request, {"synthetic": True}

    def verify_response(self, provider, request, response):
        assert request == f"request:{provider['provider_id']}".encode()
        assert response == f"response:{provider['provider_id']}".encode()
        second = {"roughtime.se": "10", "time.txryan.com": "20", "TimeNL-Roughtime": "30"}[provider["provider_id"]]
        return SimpleNamespace(
            verified=True,
            failure_code=None,
            midpoint_utc=f"2026-09-19T23:59:{second}Z",
            radius_nanoseconds=500_000_000,
        )


def wall_kwargs(fx):
    return dict(
        bundle=fx["bundle"],
        receipt_evidence=fx["receipts"],
        provider_profiles=fx["profiles"],
        qualification_state_packages=fx["packages"],
        provider_authority_inputs=fx["provider_inputs"],
        quorum_policy_ref=ref(fx["quorum"]),
        qualification_verifier_contract_ref=ref(fx["qualification_verifier"]),
        validator_contract_ref=ref(fx["validator"]),
        expected_validator_contract_ref=ref(fx["validator"]),
        roughtime_verifier_binary=Path("/synthetic/fpp-roughtime"),
        roughtime_verifier_build_profile=fx["build_profile"],
    )


@pytest.fixture
def accepted_wall(monkeypatch):
    monkeypatch.setattr(authority, "QualifiedVerifierBackend", FakeRoughtimeBackend)
    monkeypatch.setattr(
        authority,
        "validate_provider_admission_set_authoritatively",
        lambda *args, **kwargs: Validation(Result.VALID, ()),
    )


def test_two_independent_retained_receipts_recompute_verified_existence(accepted_wall):
    fx = make_wall_fixture()
    result = authority.recompute_external_existence_claim_authoritatively(
        fx["subject"], claim_deadline_utc=DEADLINE, **wall_kwargs(fx)
    )
    assert result.external_existence_claim["state"] == "VERIFIED"
    assert result.deadline_existence_claim["state"] == "VERIFIED"
    assert result.external_existence_claim["verified_upper_bound"] == "2026-09-19T23:59:21Z"


def test_one_receipt_cannot_satisfy_two_of_three_quorum(accepted_wall):
    fx = make_wall_fixture(("roughtime.se",))
    result = authority.recompute_external_existence_claim_authoritatively(
        fx["subject"], claim_deadline_utc=DEADLINE, **wall_kwargs(fx)
    )
    assert result.external_existence_claim["state"] == "FAILED"


def test_duplicate_provider_receipt_identity_fails_closed(accepted_wall):
    fx = make_wall_fixture()
    original = fx["receipts"][0]
    duplicate = sealed(
        "RoughtimeProductionReceiptEvidence",
        "receipt:duplicate:v1",
        **{key: value for key, value in original.items() if key not in {"schema_version", "object_type", "object_id", "payload_sha256", "content_sha256"}},
    )
    fx["receipts"] = [original, duplicate]
    fx["bundle"] = sealed(
        "ExternalTimeEvidenceBundle",
        "time-bundle:duplicate:v1",
        origin_class="SYNTHETIC",
        prospective_eligible=False,
        subject_ref=ref(fx["subject"]),
        receipt_quorum_deadline_utc=DEADLINE,
        receipt_evidence_refs=sorted((ref(item) for item in fx["receipts"]), key=lambda item:(item["object_id"],item["content_sha256"])),
        provider_profile_refs=sorted((ref(item) for item in fx["profiles"]), key=lambda item:(item["object_id"],item["content_sha256"])),
        qualification_state_package_refs=sorted((ref(item) for item in fx["packages"]), key=lambda item:(item["object_id"],item["content_sha256"])),
        quorum_policy_ref=ref(fx["quorum"]),
        validator_contract_ref=ref(fx["validator"]),
    )
    result = authority.recompute_external_existence_claim_authoritatively(
        fx["subject"], claim_deadline_utc=DEADLINE, **wall_kwargs(fx)
    )
    assert result.external_existence_claim["state"] == "FAILED"


def test_unbound_extra_receipt_fails_bundle_closure(accepted_wall):
    fx = make_wall_fixture()
    fx["receipts"] = [*fx["receipts"], fx["receipts"][0]]
    result = authority.recompute_external_existence_claim_authoritatively(
        fx["subject"], claim_deadline_utc=DEADLINE, **wall_kwargs(fx)
    )
    assert result.external_existence_claim["state"] == "FAILED"


def test_missing_retained_receipt_fails_bundle_closure(accepted_wall):
    fx = make_wall_fixture()
    fx["receipts"] = fx["receipts"][:1]
    result = authority.recompute_external_existence_claim_authoritatively(
        fx["subject"], claim_deadline_utc=DEADLINE, **wall_kwargs(fx)
    )
    assert result.external_existence_claim["state"] == "FAILED"


def test_wrong_validator_contract_ref_cannot_authorize_wall_clock_claim(accepted_wall):
    fx = make_wall_fixture()
    wrong = sealed("ValidatorContract", "validator:wrong:v1", contract="wrong")
    kwargs = wall_kwargs(fx)
    kwargs["expected_validator_contract_ref"] = ref(wrong)
    result = authority.recompute_external_existence_claim_authoritatively(
        fx["subject"], claim_deadline_utc=DEADLINE, **kwargs
    )
    assert result.external_existence_claim["state"] == "FAILED"


def test_provider_state_admission_failure_blocks_existence(monkeypatch):
    fx = make_wall_fixture()
    monkeypatch.setattr(authority, "QualifiedVerifierBackend", FakeRoughtimeBackend)
    monkeypatch.setattr(
        authority,
        "validate_provider_admission_set_authoritatively",
        lambda *args, **kwargs: Validation(Result.INVALID, ()),
    )
    result = authority.recompute_external_existence_claim_authoritatively(
        fx["subject"], claim_deadline_utc=DEADLINE, **wall_kwargs(fx)
    )
    assert result.external_existence_claim["state"] == "FAILED"


def make_bitcoin_fixture(tmp_path: Path, *, verified=True):
    subject = sealed("Subject", "subject:bitcoin:v1", value="x")
    validator = make_validator_contract()
    bundle = sealed(
        "ExternalTimeEvidenceBundle",
        "bundle:bitcoin:v1",
        origin_class="SYNTHETIC",
        prospective_eligible=False,
        subject_ref=ref(subject),
        receipt_quorum_deadline_utc=DEADLINE,
        receipt_evidence_refs=[],
        provider_profile_refs=[],
        qualification_state_package_refs=[],
        quorum_policy_ref=ref(sealed("PolicyDefinition", "policy:q:bitcoin:v1", value="q")),
        validator_contract_ref=ref(validator),
    )
    proof_bytes = b"synthetic-ots-proof"
    proof = sealed(
        "OpenTimestampsProofArtifact",
        "proof:bitcoin:v1",
        origin_class="SYNTHETIC",
        prospective_eligible=False,
        external_time_evidence_bundle_ref=ref(bundle),
        proof_sha256=hashlib.sha256(proof_bytes).hexdigest(),
        proof_base64=base64.b64encode(proof_bytes).decode("ascii"),
    )
    exe = tmp_path / "synthetic-bitcoin-verifier"
    success = "True" if verified else "False"
    extra = (
        '"bitcoin_block_height":123,"bitcoin_block_hash":"' + "b"*64 +
        '","bitcoin_header_sha256":"' + "c"*64 + '","node_version":"synthetic-node"'
        if verified else '"reason_code":"SYNTHETIC_VERIFICATION_FAILED"'
    )
    exe.write_text(
        "#!/usr/bin/env python3\n"
        "import json,sys\n"
        "r=json.load(sys.stdin)\n"
        "o={"
        '"schema_version":"1.0","action":"verify-bitcoin-durability",'
        '"verification_mode":"OWNER_CONTROLLED_BITCOIN_CORE",'
        '"bundle_sha256":r["bundle_sha256"],"proof_sha256":r["proof_sha256"],'
        f'"verified":{success},{extra}'
        "}\njson.dump(o,sys.stdout,separators=(',',':'),sort_keys=True)\n",
        encoding="utf-8",
    )
    exe.chmod(0o755)
    contract = sealed(
        "StrongBitcoinVerifierContract",
        "validator:bitcoin:test:v1",
        object_role="NORMATIVE",
        protocol="FPP_STRONG_BITCOIN_VERIFIER_V1",
        action="verify-bitcoin-durability",
        input_schema_version="1.0",
        output_schema_version="1.0",
        verification_mode="OWNER_CONTROLLED_BITCOIN_CORE",
        bitcoin_header_time_role="DURABILITY_ONLY_NOT_CIVIL_TIME_BOUND",
        executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
        timeout_seconds=10,
    )
    return subject, validator, bundle, proof, exe, contract


@pytest.mark.skipif(os.name == "nt", reason="synthetic executable fixture is POSIX")
def test_hash_pinned_local_strong_verifier_recomputes_bitcoin_claim(tmp_path):
    subject, validator, bundle, proof, exe, contract = make_bitcoin_fixture(tmp_path, verified=True)
    result = authority.recompute_bitcoin_durability_claim_authoritatively(
        subject, bundle=bundle, proof_artifact=proof, strong_verifier_contract=contract,
        strong_verifier_executable=exe, validator_contract_ref=ref(validator),
        expected_validator_contract_ref=ref(validator), expected_strong_verifier_contract_ref=ref(contract),
    )
    assert result.bitcoin_durability_claim["state"] == "VERIFIED"
    assert result.strong_verification_report["verified"] is True


@pytest.mark.skipif(os.name == "nt", reason="synthetic executable fixture is POSIX")
def test_failed_strong_bitcoin_verifier_produces_failed_durability(tmp_path):
    subject, validator, bundle, proof, exe, contract = make_bitcoin_fixture(tmp_path, verified=False)
    result = authority.recompute_bitcoin_durability_claim_authoritatively(
        subject, bundle=bundle, proof_artifact=proof, strong_verifier_contract=contract,
        strong_verifier_executable=exe, validator_contract_ref=ref(validator),
        expected_validator_contract_ref=ref(validator), expected_strong_verifier_contract_ref=ref(contract),
    )
    assert result.bitcoin_durability_claim["state"] == "FAILED"


@pytest.mark.skipif(os.name == "nt", reason="synthetic executable fixture is POSIX")
def test_wrong_ots_bundle_binding_rejected(tmp_path):
    subject, validator, bundle, proof, exe, contract = make_bitcoin_fixture(tmp_path, verified=True)
    other = sealed("ExternalTimeEvidenceBundle", "bundle:other:v1", value="other")
    bad = sealed(
        "OpenTimestampsProofArtifact", "proof:bad:v1", origin_class="SYNTHETIC",
        prospective_eligible=False, external_time_evidence_bundle_ref=ref(other),
        proof_sha256=proof["proof_sha256"], proof_base64=proof["proof_base64"],
    )
    with pytest.raises(ValueError, match="OTS proof bundle"):
        authority.recompute_bitcoin_durability_claim_authoritatively(
            subject, bundle=bundle, proof_artifact=bad, strong_verifier_contract=contract,
            strong_verifier_executable=exe, validator_contract_ref=ref(validator),
            expected_validator_contract_ref=ref(validator), expected_strong_verifier_contract_ref=ref(contract),
        )


@pytest.mark.skipif(os.name == "nt", reason="synthetic executable fixture is POSIX")
def test_persisted_strong_report_must_equal_recomputation(tmp_path):
    subject, validator, bundle, proof, exe, contract = make_bitcoin_fixture(tmp_path, verified=True)
    bogus = sealed("StrongBitcoinVerificationReport", "report:bogus:v1", value="bogus")
    with pytest.raises(ValueError, match="persisted strong Bitcoin"):
        authority.recompute_bitcoin_durability_claim_authoritatively(
            subject, bundle=bundle, proof_artifact=proof, strong_verifier_contract=contract,
            strong_verifier_executable=exe, validator_contract_ref=ref(validator),
            expected_validator_contract_ref=ref(validator), expected_strong_verifier_contract_ref=ref(contract),
            persisted_strong_report=bogus,
        )


def test_validation_report_exact_recomputation_equality():
    candidate = sealed("Subject", "subject:report:v1", value="x")
    validator = make_validator_contract()
    manifest = sealed("TrustedManifest", "manifest:test:v1", value="m")
    validation = Validation(Result.VALID, ())
    claim = authority._claim(
        "EXTERNAL_EXISTENCE_BOUND_VERIFIED", ref(candidate), "VERIFIED",
        reason_codes=("TEST",), verified_upper_bound="2026-09-01T00:00:00Z",
    )
    recomputed = authority.build_validation_report_v2(
        candidate, validator_contract_ref=ref(validator), trusted_manifest_ref=ref(manifest),
        dependency_refs=[], validation=validation, derived_claims=[claim],
    )
    assert authority.compare_persisted_validation_report_to_recomputed(recomputed, recomputed).valid


def test_structurally_valid_but_fabricated_report_claim_rejected_by_equality():
    candidate = sealed("Subject", "subject:report-fake:v1", value="x")
    validator = make_validator_contract()
    manifest = sealed("TrustedManifest", "manifest:test-fake:v1", value="m")
    validation = Validation(Result.VALID, ())
    verified = authority._claim(
        "EXTERNAL_EXISTENCE_BOUND_VERIFIED", ref(candidate), "VERIFIED",
        reason_codes=("TEST",), verified_upper_bound="2026-09-01T00:00:00Z",
    )
    failed = authority._claim(
        "EXTERNAL_EXISTENCE_BOUND_VERIFIED", ref(candidate), "FAILED",
        reason_codes=("RECOMPUTED_FAILURE",),
    )
    persisted = authority.build_validation_report_v2(
        candidate, validator_contract_ref=ref(validator), trusted_manifest_ref=ref(manifest),
        dependency_refs=[], validation=validation, derived_claims=[verified],
    )
    recomputed = authority.build_validation_report_v2(
        candidate, validator_contract_ref=ref(validator), trusted_manifest_ref=ref(manifest),
        dependency_refs=[], validation=validation, derived_claims=[failed],
    )
    assert not authority.compare_persisted_validation_report_to_recomputed(persisted, recomputed).valid


def test_successor_cycle_plan_rejects_raw_existence_bound_injection_by_api():
    plan = sealed("IssuanceCyclePlan", "plan:api:v1", value="x")
    with pytest.raises(TypeError):
        authority.validate_cycle_plan_authoritatively(
            plan, required_slots=[], required_schedule_policy_ref={"object_id":"policy:x","content_sha256":"0"*64},
            wall_clock_inputs={}, verified_plan_existence_bound="2026-09-01T00:00:00Z",
        )


def test_final_acceptance_rejects_state_string_injection_by_api():
    acceptance = sealed("ManifestAcceptance", "acceptance:api:v2", value="x")
    with pytest.raises(TypeError):
        authority.validate_final_genesis_acceptance_authoritatively(
            acceptance, final_evidence_subject_ref=ref(acceptance), wall_clock_inputs={}, bitcoin_inputs={},
            external_existence_state="VERIFIED", bitcoin_durability_state="VERIFIED",
        )


def test_final_acceptance_rejects_wrong_subject_before_claim_consumption():
    acceptance = sealed("ManifestAcceptance", "acceptance:subject:v2", value="x")
    other = sealed("ManifestAcceptance", "acceptance:other:v2", value="y")
    with pytest.raises(ValueError, match="final evidence subject"):
        authority.validate_final_genesis_acceptance_authoritatively(
            acceptance, final_evidence_subject_ref=ref(other), wall_clock_inputs={}, bitcoin_inputs={},
        )


def test_final_acceptance_rejects_evidence_splicing_between_bundles():
    acceptance = sealed("ManifestAcceptance", "acceptance:splice:v2", value="x")
    validator = make_validator_contract()
    b1 = sealed("ExternalTimeEvidenceBundle", "bundle:splice1:v1", validator_contract_ref=ref(validator))
    b2 = sealed("ExternalTimeEvidenceBundle", "bundle:splice2:v1", validator_contract_ref=ref(validator))
    with pytest.raises(ValueError, match="same exact ExternalTimeEvidenceBundle"):
        authority.validate_final_genesis_acceptance_authoritatively(
            acceptance, final_evidence_subject_ref=ref(acceptance),
            wall_clock_inputs={"bundle": b1}, bitcoin_inputs={"bundle": b2},
        )


def test_final_acceptance_maps_non_scientific_claims_not_applicable(monkeypatch):
    acceptance = sealed("ManifestAcceptance", "acceptance:na:v2", value="x")
    bundle = sealed("ExternalTimeEvidenceBundle", "bundle:na:v1", value="b")
    external = authority._claim(
        "EXTERNAL_EXISTENCE_BOUND_VERIFIED", ref(acceptance), "VERIFIED",
        reason_codes=("RECOMPUTED",), verified_upper_bound="2026-09-01T00:00:00Z",
    )
    deadline = authority._claim(
        "DEADLINE_EXISTENCE_VERIFIED", ref(acceptance), "NOT_APPLICABLE",
        reason_codes=("NO_FROZEN_DEADLINE",),
    )
    bitcoin_claim = authority._claim(
        "BITCOIN_DURABILITY_VERIFIED", ref(acceptance), "VERIFIED", reason_codes=("RECOMPUTED",),
    )
    report = sealed("StrongBitcoinVerificationReport", "bitcoin-report:na:v1", verified=True)
    monkeypatch.setattr(
        authority, "recompute_external_existence_claim_authoritatively",
        lambda *args, **kwargs: authority.WallClockRecomputation(external, deadline, ref(bundle)),
    )
    monkeypatch.setattr(
        authority, "recompute_bitcoin_durability_claim_authoritatively",
        lambda *args, **kwargs: authority.BitcoinRecomputation(
            bitcoin_claim, ref(bundle), {"object_id":"proof:na:v1","content_sha256":"1"*64}, report
        ),
    )
    validation, claims, _report = authority.validate_final_genesis_acceptance_authoritatively(
        acceptance, final_evidence_subject_ref=ref(acceptance),
        wall_clock_inputs={"bundle": bundle}, bitcoin_inputs={"bundle": bundle},
    )
    states = {item["claim_type"]: item["state"] for item in claims}
    assert validation.valid
    assert states["PRE_OUTCOME_DURABILITY_VERIFIED"] == "NOT_APPLICABLE"
    assert states["CONFIRMATORY_PROSPECTIVE_ELIGIBLE"] == "NOT_APPLICABLE"


def test_late_durability_record_preserves_bitcoin_but_fails_pre_outcome(monkeypatch):
    subject = sealed("IssuedForecast", "forecast:late-dvr:v1", value="1")
    bundle = sealed("ExternalTimeEvidenceBundle", "bundle:late-dvr:v1", value="b")
    proof_ref = {"object_id":"proof:late-dvr:v1","content_sha256":"2"*64}
    report = sealed("StrongBitcoinVerificationReport", "report:late-dvr:v1", verified=True)
    bitcoin_claim = authority._claim(
        "BITCOIN_DURABILITY_VERIFIED", ref(subject), "VERIFIED", reason_codes=("RECOMPUTED",)
    )
    dvr = sealed(
        "DurabilityVerificationRecord", "dvr:late:v1", origin_class="SYNTHETIC", prospective_eligible=False,
        primary_subject_ref=ref(subject), external_time_evidence_bundle_ref=ref(bundle), ots_proof_ref=proof_ref,
        strong_verification_report_ref=ref(report), outcome_information_barrier="2026-09-20T00:00:00Z",
    )
    dvr_external = authority._claim(
        "EXTERNAL_EXISTENCE_BOUND_VERIFIED", ref(dvr), "VERIFIED",
        reason_codes=("RECOMPUTED",), verified_upper_bound="2026-09-20T00:00:01Z",
    )
    dvr_deadline = authority._claim(
        "DEADLINE_EXISTENCE_VERIFIED", ref(dvr), "FAILED",
        reason_codes=("VERIFIED_EXISTENCE_AFTER_FROZEN_DEADLINE",),
        verified_upper_bound="2026-09-20T00:00:01Z", frozen_deadline="2026-09-20T00:00:00Z",
    )
    monkeypatch.setattr(
        authority, "recompute_bitcoin_durability_claim_authoritatively",
        lambda *args, **kwargs: authority.BitcoinRecomputation(bitcoin_claim, ref(bundle), proof_ref, report),
    )
    monkeypatch.setattr(
        authority, "recompute_external_existence_claim_authoritatively",
        lambda *args, **kwargs: authority.WallClockRecomputation(dvr_external, dvr_deadline, ref(bundle)),
    )
    pre, bitcoin, _wall = authority.recompute_pre_outcome_durability_authoritatively(
        subject, bitcoin_inputs={}, durability_record=dvr, durability_record_wall_clock_inputs={},
    )
    assert bitcoin.bitcoin_durability_claim["state"] == "VERIFIED"
    assert pre["state"] == "FAILED"


def test_confirmatory_path_does_not_accept_caller_constructed_claims():
    forecast = sealed("IssuedForecast", "forecast:no-claims:v1", value="1")
    with pytest.raises(TypeError):
        authority.derive_confirmatory_eligibility_from_evidence(
            forecast, component_specs=[], required_claim_requirements=[], required_claims=[],
        )


def test_confirmatory_component_subject_substitution_rejected():
    forecast = sealed("IssuedForecast", "forecast:substitution:v1", value="1")
    plan = sealed("IssuanceCyclePlan", "plan:a:v1", value="a")
    other = sealed("IssuanceCyclePlan", "plan:b:v1", value="b")
    with pytest.raises(ValueError, match="subject substitution"):
        authority.derive_confirmatory_eligibility_from_evidence(
            forecast,
            component_specs=[{
                "kind":"wall_clock_deadline", "subject":other, "required_subject_ref":ref(plan),
                "claim_deadline_utc":DEADLINE, "authority_inputs":{},
            }],
            required_claim_requirements=[{"claim_type":"DEADLINE_EXISTENCE_VERIFIED","subject_ref":ref(plan)}],
        )


def test_historical_cycle_plan_raw_bound_contract_remains_available():
    schedule = sealed("PolicyDefinition", "policy:schedule:historical:v1", value="s")
    plan = sealed(
        "IssuanceCyclePlan", "plan:historical:v1",
        plan_commitment_deadline="2026-09-10T00:00:00Z",
        execution_window_open="2026-09-11T00:00:00Z",
        execution_window_close="2026-09-12T00:00:00Z",
        expected_slots=[], schedule_policy_ref=ref(schedule),
    )
    result = validate_cycle_plan(
        plan, verified_plan_existence_bound="2026-09-09T00:00:00Z", verified_plan_ref=ref(plan),
        required_slots=[], required_schedule_policy_ref=ref(schedule),
    )
    assert result.valid
