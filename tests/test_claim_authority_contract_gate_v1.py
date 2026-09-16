from pathlib import Path

import pytest

import forecast_trust_core.claim_authority_v1 as authority
from forecast_trust_core.canonical import seal_object


DEADLINE = "2026-09-20T00:00:00Z"


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def sealed(kind, object_id, **payload):
    return seal_object(
        {"schema_version": "1.0", **payload},
        object_type=kind,
        stable_context="contract-gate-test",
        semantic_id=object_id,
    )


def reference_objects():
    subject = sealed("Subject", "subject:gate:v1", value="x")
    receipts = [sealed("RefObject", "receipt-ref:gate:v1", value="r")]
    profiles = [sealed("RefObject", f"profile-ref:gate:{index}", value=index) for index in range(3)]
    states = [sealed("RefObject", f"state-ref:gate:{index}", value=index) for index in range(3)]
    quorum = sealed("PolicyDefinition", "policy:quorum:gate:v1", value="q")
    validator = sealed("ValidatorContract", "validator:gate:v1", value="v")
    return subject, receipts, profiles, states, quorum, validator


def valid_bundle(origin_class="SYNTHETIC"):
    subject, receipts, profiles, states, quorum, validator = reference_objects()
    bundle = sealed(
        "ExternalTimeEvidenceBundle",
        "bundle:gate:v1",
        origin_class=origin_class,
        prospective_eligible=False,
        subject_ref=ref(subject),
        receipt_quorum_deadline_utc=DEADLINE,
        receipt_evidence_refs=[ref(item) for item in receipts],
        provider_profile_refs=[ref(item) for item in profiles],
        qualification_state_package_refs=[ref(item) for item in states],
        quorum_policy_ref=ref(quorum),
        validator_contract_ref=ref(validator),
    )
    return subject, bundle, validator


def valid_proof(bundle):
    return sealed(
        "OpenTimestampsProofArtifact",
        "proof:gate:v1",
        origin_class="SYNTHETIC",
        prospective_eligible=False,
        external_time_evidence_bundle_ref=ref(bundle),
        proof_sha256="1" * 64,
        proof_base64="cHJvb2Y=",
    )


def valid_strong_contract():
    return sealed(
        "StrongBitcoinVerifierContract",
        "strong-contract:gate:v1",
        object_role="NORMATIVE",
        protocol="FPP_STRONG_BITCOIN_VERIFIER_V1",
        action="verify-bitcoin-durability",
        input_schema_version="1.0",
        output_schema_version="1.0",
        verification_mode="OWNER_CONTROLLED_BITCOIN_CORE",
        bitcoin_header_time_role="DURABILITY_ONLY_NOT_CIVIL_TIME_BOUND",
        executable_sha256="2" * 64,
        timeout_seconds=10,
    )


def reseal_with_extra(obj, object_id, **extra):
    payload = {
        key: value
        for key, value in obj.items()
        if key not in {"schema_version", "object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    payload.update(extra)
    return sealed(obj["object_type"], object_id, **payload)


def test_sealed_bundle_with_extra_field_is_rejected_before_bitcoin_execution():
    subject, bundle, validator = valid_bundle()
    bad_bundle = reseal_with_extra(bundle, "bundle:extra:gate:v1", unexpected="forbidden")
    proof = valid_proof(bad_bundle)
    contract = valid_strong_contract()
    with pytest.raises(ValueError, match="object contract violation"):
        authority.recompute_bitcoin_durability_claim_authoritatively(
            subject,
            bundle=bad_bundle,
            proof_artifact=proof,
            strong_verifier_contract=contract,
            strong_verifier_executable=Path("/must/not/execute"),
            validator_contract_ref=ref(validator),
            expected_validator_contract_ref=ref(validator),
            expected_strong_verifier_contract_ref=ref(contract),
        )


def test_production_receipt_rejects_retrospective_origin_even_with_valid_seal():
    subject, _bundle, _validator = valid_bundle()
    profile = sealed("RoughtimeProductionProviderProfile", "profile:gate:v1", value="p")
    state = sealed("RoughtimeProviderQualificationStatePackage", "state:gate:v1", value="s")
    receipt = sealed(
        "RoughtimeProductionReceiptEvidence",
        "receipt:retrospective:gate:v1",
        origin_class="RETROSPECTIVE",
        prospective_eligible=False,
        subject_ref=ref(subject),
        frozen_deadline_utc=DEADLINE,
        provider_id="roughtime.se",
        provider_profile_ref=ref(profile),
        qualification_state_package_ref=ref(state),
        verifier_build_profile_sha256="3" * 64,
        client_random_hex="4" * 64,
        request_sha256="5" * 64,
        request_base64="cmVxdWVzdA==",
        response_sha256="6" * 64,
        response_base64="cmVzcG9uc2U=",
    )
    with pytest.raises(ValueError, match="origin_class invalid"):
        authority._validate_receipt_contract(receipt)


def test_ots_proof_rejects_additional_properties_even_with_valid_seal():
    _subject, bundle, _validator = valid_bundle()
    proof = valid_proof(bundle)
    bad = reseal_with_extra(proof, "proof:extra:gate:v1", unexpected="forbidden")
    with pytest.raises(ValueError, match="field set mismatch"):
        authority._validate_ots_contract(bad)


def test_dvr_rejects_additional_properties_even_with_valid_seal():
    subject, bundle, _validator = valid_bundle()
    proof = valid_proof(bundle)
    report = sealed("StrongBitcoinVerificationReport", "strong-report-ref:gate:v1", value="r")
    dvr = sealed(
        "DurabilityVerificationRecord",
        "dvr:gate:v1",
        origin_class="SYNTHETIC",
        prospective_eligible=False,
        primary_subject_ref=ref(subject),
        external_time_evidence_bundle_ref=ref(bundle),
        ots_proof_ref=ref(proof),
        strong_verification_report_ref=ref(report),
        outcome_information_barrier=DEADLINE,
    )
    bad = reseal_with_extra(dvr, "dvr:extra:gate:v1", unexpected="forbidden")
    with pytest.raises(ValueError, match="field set mismatch"):
        authority._validate_dvr_contract(bad)


def test_dvr_rejects_prospective_eligible_true_even_with_valid_seal():
    subject, bundle, _validator = valid_bundle()
    proof = valid_proof(bundle)
    report = sealed("StrongBitcoinVerificationReport", "strong-report-ref:gate:v2", value="r")
    dvr = sealed(
        "DurabilityVerificationRecord",
        "dvr:prospective:gate:v1",
        origin_class="SYNTHETIC",
        prospective_eligible=True,
        primary_subject_ref=ref(subject),
        external_time_evidence_bundle_ref=ref(bundle),
        ots_proof_ref=ref(proof),
        strong_verification_report_ref=ref(report),
        outcome_information_barrier=DEADLINE,
    )
    with pytest.raises(ValueError, match="prospective_eligible must be false"):
        authority._validate_dvr_contract(dvr)


def test_strong_verifier_contract_rejects_unexpected_fields():
    contract = valid_strong_contract()
    bad = reseal_with_extra(contract, "strong-contract:extra:gate:v1", unexpected="forbidden")
    with pytest.raises(ValueError, match="field set mismatch"):
        authority._validate_strong_contract(bad)
