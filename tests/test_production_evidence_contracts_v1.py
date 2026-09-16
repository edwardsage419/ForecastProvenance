from pathlib import Path

import pytest

import forecast_trust_core.claim_authority_v1 as authority
from forecast_trust_core.canonical import seal_object
from forecast_trust_core.production_evidence_contracts_v1 import (
    validate_durability_verification_record_contract,
    validate_external_time_evidence_bundle_contract,
    validate_open_timestamps_proof_artifact_contract,
    validate_roughtime_production_receipt_contract,
    validate_strong_bitcoin_verifier_contract,
)


DEADLINE = "2026-09-20T00:00:00Z"
PROVIDERS = ("roughtime.se", "time.txryan.com", "TimeNL-Roughtime")
DERIVED_FIELDS = {"object_type", "object_id", "payload_sha256", "content_sha256"}


def sealed(kind, object_id, **payload):
    return seal_object(
        {"schema_version": "1.0", **payload},
        object_type=kind,
        stable_context="production-evidence-contract-test",
        semantic_id=object_id,
    )


def reseal(obj, *, object_id, object_type=None, omit=(), **overrides):
    payload = {
        key: value
        for key, value in obj.items()
        if key not in DERIVED_FIELDS and key not in set(omit)
    }
    payload.update(overrides)
    return seal_object(
        payload,
        object_type=object_type or obj["object_type"],
        stable_context="production-evidence-contract-test",
        semantic_id=object_id,
    )


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def dummy_ref(object_id, digit):
    return {"object_id": object_id, "content_sha256": digit * 64}


def full_receipt(*, subject_ref, profile_ref, state_ref, extra=None, origin_class="SYNTHETIC"):
    payload = {
        "origin_class": origin_class,
        "prospective_eligible": False,
        "subject_ref": subject_ref,
        "frozen_deadline_utc": DEADLINE,
        "provider_id": "roughtime.se",
        "provider_profile_ref": profile_ref,
        "qualification_state_package_ref": state_ref,
        "verifier_build_profile_sha256": "a" * 64,
        "client_random_hex": "b" * 64,
        "request_sha256": "c" * 64,
        "request_base64": "cmVxdWVzdA==",
        "response_sha256": "d" * 64,
        "response_base64": "cmVzcG9uc2U=",
    }
    if extra:
        payload.update(extra)
    return sealed("RoughtimeProductionReceiptEvidence", "receipt:contract-test:v1", **payload)


def full_bundle(*, subject_ref, validator_ref, receipt_refs, profile_refs, state_refs, extra=None):
    payload = {
        "origin_class": "SYNTHETIC",
        "prospective_eligible": False,
        "subject_ref": subject_ref,
        "receipt_quorum_deadline_utc": DEADLINE,
        "receipt_evidence_refs": list(receipt_refs),
        "provider_profile_refs": list(profile_refs),
        "qualification_state_package_refs": list(state_refs),
        "quorum_policy_ref": dummy_ref("policy:contract-test:v1", "e"),
        "validator_contract_ref": validator_ref,
    }
    if extra:
        payload.update(extra)
    return sealed("ExternalTimeEvidenceBundle", "bundle:contract-test:v1", **payload)


def bundle_fixture():
    subject = sealed("Subject", "subject:bundle-contract:v1", value="x")
    validator = sealed("ValidatorContract", "validator:bundle-contract:v1", value="v")
    bundle = full_bundle(
        subject_ref=ref(subject),
        validator_ref=ref(validator),
        receipt_refs=[dummy_ref("receipt:bundle-contract:v1", "1")],
        profile_refs=[
            dummy_ref(f"profile:bundle-contract:{index}", digit)
            for index, digit in enumerate(("2", "3", "4"), 1)
        ],
        state_refs=[
            dummy_ref(f"state:bundle-contract:{index}", digit)
            for index, digit in enumerate(("5", "6", "7"), 1)
        ],
    )
    return subject, validator, bundle


def test_exact_bundle_contract_accepts_schema_conforming_object():
    _subject, _validator, bundle = bundle_fixture()
    validate_external_time_evidence_bundle_contract(bundle)


def test_bundle_wrong_schema_version_rejected_even_when_resealed():
    _subject, _validator, bundle = bundle_fixture()
    bad = reseal(bundle, object_id="bundle:wrong-schema:v1", schema_version="2.0")
    with pytest.raises(ValueError, match="schema_version"):
        validate_external_time_evidence_bundle_contract(bad)


def test_bundle_wrong_object_type_rejected_even_when_resealed():
    _subject, _validator, bundle = bundle_fixture()
    bad = reseal(
        bundle,
        object_id="bundle:wrong-type:v1",
        object_type="WrongExternalTimeEvidenceBundle",
    )
    with pytest.raises(ValueError, match="object_type"):
        validate_external_time_evidence_bundle_contract(bad)


def test_bundle_missing_required_field_rejected_even_when_resealed():
    _subject, _validator, bundle = bundle_fixture()
    bad = reseal(
        bundle,
        object_id="bundle:missing-validator:v1",
        omit=("validator_contract_ref",),
    )
    with pytest.raises(ValueError, match="fields invalid"):
        validate_external_time_evidence_bundle_contract(bad)


def test_bundle_malformed_reference_rejected_even_when_resealed():
    _subject, _validator, bundle = bundle_fixture()
    bad = reseal(
        bundle,
        object_id="bundle:malformed-ref:v1",
        subject_ref={"object_id": "subject:bad:v1", "content_sha256": "bad"},
    )
    with pytest.raises(ValueError, match="reference invalid"):
        validate_external_time_evidence_bundle_contract(bad)


def test_bundle_wrong_provider_cardinality_rejected_even_when_resealed():
    _subject, _validator, bundle = bundle_fixture()
    bad = reseal(
        bundle,
        object_id="bundle:wrong-cardinality:v1",
        provider_profile_refs=bundle["provider_profile_refs"][:2],
    )
    with pytest.raises(ValueError, match="between 3 and 3"):
        validate_external_time_evidence_bundle_contract(bad)


def test_wall_authority_returns_failed_for_contract_invalid_bundle():
    subject, validator, bundle = bundle_fixture()
    bad = reseal(
        bundle,
        object_id="bundle:wall-invalid:v1",
        unexpected_field="sealed-but-outside-schema",
    )
    result = authority.recompute_external_existence_claim_authoritatively(
        subject,
        bundle=bad,
        receipt_evidence=[],
        provider_profiles=[],
        qualification_state_packages=[],
        provider_authority_inputs={},
        quorum_policy_ref=bundle["quorum_policy_ref"],
        qualification_verifier_contract_ref=dummy_ref("validator:qualification:v1", "f"),
        validator_contract_ref=ref(validator),
        expected_validator_contract_ref=ref(validator),
        roughtime_verifier_binary=Path("/not/reached"),
        roughtime_verifier_build_profile={"profile_sha256": "a" * 64},
        claim_deadline_utc=DEADLINE,
    )
    assert result.external_existence_claim["state"] == "FAILED"
    assert result.deadline_existence_claim["state"] == "FAILED"


def test_sealed_receipt_with_schema_extra_field_cannot_verify_wall_claim():
    subject = sealed("Subject", "subject:contract-test:v1", value="x")
    validator = sealed("ValidatorContract", "validator:contract-test:v1", value="v")
    profiles = [
        sealed(
            "RoughtimeProductionProviderProfile",
            f"profile:{provider}:v1",
            provider_id=provider,
            verifier_build_profile_sha256="a" * 64,
        )
        for provider in PROVIDERS
    ]
    packages = [
        sealed(
            "RoughtimeProviderQualificationStatePackage",
            f"state:{provider}:v1",
            provider_id=provider,
            qualification_decision_ref=dummy_ref(f"decision:{provider}:v1", str(index + 1)),
        )
        for index, provider in enumerate(PROVIDERS)
    ]
    receipt = full_receipt(
        subject_ref=ref(subject),
        profile_ref=ref(profiles[0]),
        state_ref=ref(packages[0]),
        extra={"unexpected_field": "sealed-but-outside-schema"},
    )
    bundle = full_bundle(
        subject_ref=ref(subject),
        validator_ref=ref(validator),
        receipt_refs=[ref(receipt)],
        profile_refs=[ref(item) for item in profiles],
        state_refs=[ref(item) for item in packages],
    )
    result = authority.recompute_external_existence_claim_authoritatively(
        subject,
        bundle=bundle,
        receipt_evidence=[receipt],
        provider_profiles=profiles,
        qualification_state_packages=packages,
        provider_authority_inputs={},
        quorum_policy_ref=bundle["quorum_policy_ref"],
        qualification_verifier_contract_ref=dummy_ref("validator:qualification:v1", "f"),
        validator_contract_ref=ref(validator),
        expected_validator_contract_ref=ref(validator),
        roughtime_verifier_binary=Path("/not/reached"),
        roughtime_verifier_build_profile={"profile_sha256": "a" * 64},
        claim_deadline_utc=DEADLINE,
    )
    assert result.external_existence_claim["state"] == "FAILED"


def test_receipt_wrong_schema_version_rejected_even_when_resealed():
    receipt = full_receipt(
        subject_ref=dummy_ref("subject:receipt-schema:v1", "1"),
        profile_ref=dummy_ref("profile:receipt-schema:v1", "2"),
        state_ref=dummy_ref("state:receipt-schema:v1", "3"),
    )
    bad = reseal(receipt, object_id="receipt:wrong-schema:v1", schema_version="2.0")
    with pytest.raises(ValueError, match="schema_version"):
        validate_roughtime_production_receipt_contract(bad)


def test_sealed_schema_invalid_bundle_cannot_enter_bitcoin_authority():
    subject = sealed("Subject", "subject:bitcoin-contract:v1", value="x")
    validator = sealed("ValidatorContract", "validator:bitcoin-contract:v1", value="v")
    receipt_ref = dummy_ref("receipt:bitcoin-contract:v1", "1")
    profile_refs = [dummy_ref(f"profile:bitcoin-contract:{i}", digit) for i, digit in enumerate(("2", "3", "4"), 1)]
    state_refs = [dummy_ref(f"state:bitcoin-contract:{i}", digit) for i, digit in enumerate(("5", "6", "7"), 1)]
    bad_bundle = full_bundle(
        subject_ref=ref(subject),
        validator_ref=ref(validator),
        receipt_refs=[receipt_ref],
        profile_refs=profile_refs,
        state_refs=state_refs,
        extra={"unexpected_field": "sealed-but-outside-schema"},
    )
    with pytest.raises(ValueError, match="fields invalid"):
        authority.recompute_bitcoin_durability_claim_authoritatively(
            subject,
            bundle=bad_bundle,
            proof_artifact={},
            strong_verifier_contract={},
            strong_verifier_executable=Path("/not/reached"),
            validator_contract_ref=ref(validator),
            expected_validator_contract_ref=ref(validator),
            expected_strong_verifier_contract_ref=dummy_ref("validator:bitcoin:v1", "8"),
        )


def test_ots_proof_retrospective_origin_is_rejected_by_exact_contract():
    proof = sealed(
        "OpenTimestampsProofArtifact",
        "proof:retrospective:v1",
        origin_class="RETROSPECTIVE",
        prospective_eligible=False,
        external_time_evidence_bundle_ref=dummy_ref("bundle:retrospective:v1", "1"),
        proof_sha256="2" * 64,
        proof_base64="cHJvb2Y=",
    )
    with pytest.raises(ValueError, match="origin_class"):
        validate_open_timestamps_proof_artifact_contract(proof)


def test_dvr_extra_field_is_rejected_before_pre_outcome_claim(monkeypatch):
    subject = sealed("IssuedForecast", "forecast:dvr-contract:v1", value="1")
    bundle = sealed("ExternalTimeEvidenceBundle", "bundle:dvr-contract:v1", value="placeholder")
    proof_ref = dummy_ref("proof:dvr-contract:v1", "2")
    report = sealed("StrongBitcoinVerificationReport", "report:dvr-contract:v1", verified=True)
    bitcoin_claim = authority._claim(
        "BITCOIN_DURABILITY_VERIFIED",
        ref(subject),
        "VERIFIED",
        reason_codes=("TEST",),
    )
    monkeypatch.setattr(
        authority,
        "recompute_bitcoin_durability_claim_authoritatively",
        lambda *args, **kwargs: authority.BitcoinRecomputation(
            bitcoin_claim,
            ref(bundle),
            proof_ref,
            report,
        ),
    )
    bad_dvr = sealed(
        "DurabilityVerificationRecord",
        "dvr:contract-invalid:v1",
        origin_class="SYNTHETIC",
        prospective_eligible=False,
        primary_subject_ref=ref(subject),
        external_time_evidence_bundle_ref=ref(bundle),
        ots_proof_ref=proof_ref,
        strong_verification_report_ref=ref(report),
        outcome_information_barrier=DEADLINE,
        unexpected_field="sealed-but-outside-schema",
    )
    with pytest.raises(ValueError, match="fields invalid"):
        authority.recompute_pre_outcome_durability_authoritatively(
            subject,
            bitcoin_inputs={},
            durability_record=bad_dvr,
            durability_record_wall_clock_inputs={},
        )


def test_dvr_prospective_eligible_true_is_rejected():
    record = sealed(
        "DurabilityVerificationRecord",
        "dvr:prospective-invalid:v1",
        origin_class="SYNTHETIC",
        prospective_eligible=True,
        primary_subject_ref=dummy_ref("subject:dvr:v1", "1"),
        external_time_evidence_bundle_ref=dummy_ref("bundle:dvr:v1", "2"),
        ots_proof_ref=dummy_ref("proof:dvr:v1", "3"),
        strong_verification_report_ref=dummy_ref("report:dvr:v1", "4"),
        outcome_information_barrier=DEADLINE,
    )
    with pytest.raises(ValueError, match="prospective_eligible"):
        validate_durability_verification_record_contract(record)


def test_dvr_malformed_primary_subject_ref_is_rejected():
    record = sealed(
        "DurabilityVerificationRecord",
        "dvr:bad-ref:v1",
        origin_class="SYNTHETIC",
        prospective_eligible=False,
        primary_subject_ref={"object_id": "subject:dvr:v1", "content_sha256": "bad"},
        external_time_evidence_bundle_ref=dummy_ref("bundle:dvr:v1", "2"),
        ots_proof_ref=dummy_ref("proof:dvr:v1", "3"),
        strong_verification_report_ref=dummy_ref("report:dvr:v1", "4"),
        outcome_information_barrier=DEADLINE,
    )
    with pytest.raises(ValueError, match="reference invalid"):
        validate_durability_verification_record_contract(record)


def test_strong_bitcoin_contract_extra_field_is_rejected():
    contract = sealed(
        "StrongBitcoinVerifierContract",
        "validator:bitcoin-extra:v1",
        object_role="NORMATIVE",
        protocol="FPP_STRONG_BITCOIN_VERIFIER_V1",
        action="verify-bitcoin-durability",
        input_schema_version="1.0",
        output_schema_version="1.0",
        verification_mode="OWNER_CONTROLLED_BITCOIN_CORE",
        bitcoin_header_time_role="DURABILITY_ONLY_NOT_CIVIL_TIME_BOUND",
        executable_sha256="5" * 64,
        timeout_seconds=10,
        unexpected_field="sealed-but-outside-schema",
    )
    with pytest.raises(ValueError, match="fields invalid"):
        validate_strong_bitcoin_verifier_contract(contract)
