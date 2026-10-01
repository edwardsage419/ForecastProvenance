import pytest

import forecast_trust_core.claim_authority_trust_root_v1 as trust_root
import forecast_trust_core.claim_authority_v1 as authority
from forecast_trust_core.canonical import seal_object


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def sealed(kind, object_id, **payload):
    return seal_object(
        {"schema_version": "1.0", **payload},
        object_type=kind,
        stable_context="confirmatory-authority-completeness-test",
        semantic_id=object_id,
    )


def test_empty_temporal_requirement_set_cannot_authorize_confirmatory_verified():
    forecast = sealed("IssuedForecast", "forecast:confirmatory-empty:v1", value="x")
    eligibility, claims = authority.derive_confirmatory_eligibility_from_evidence(
        forecast,
        component_specs=[],
        required_claim_requirements=[],
    )
    assert claims == ()
    assert eligibility["state"] == "UNRESOLVED"
    assert "FULL_TRUST_CORE_CHECK_AUTHORITY_NOT_IMPLEMENTED" in eligibility["reason_codes"]


def test_caller_supplied_hard_invalidation_cannot_be_authority():
    forecast = sealed("IssuedForecast", "forecast:confirmatory-caller:v1", value="x")
    with pytest.raises(ValueError, match="hard invalidation authority prohibited"):
        authority.derive_confirmatory_eligibility_from_evidence(
            forecast,
            component_specs=[],
            required_claim_requirements=[],
            hard_invalidation_reason_codes=["CALLER_SELECTED_EXCLUSION"],
        )


def test_trusted_manifest_wrapper_cannot_bypass_missing_full_trust_core_authority():
    validator = sealed("ValidatorContract", "validator:confirmatory:v1", value="v")
    quorum = sealed("PolicyDefinition", "policy:quorum:confirmatory:v1", value="q")
    qualification_verifier = sealed(
        "ValidatorContract",
        "validator:qualification:confirmatory:v1",
        value="qv",
    )
    strong_bitcoin = sealed(
        "StrongBitcoinVerifierContract",
        "validator:bitcoin:confirmatory:v1",
        value="b",
    )
    profiles = [
        sealed(
            "RoughtimeProductionProviderProfile",
            f"profile:confirmatory:{index}:v1",
            provider_id=f"p{index}",
        )
        for index in range(3)
    ]
    decisions = [
        sealed(
            "RoughtimeQualificationDecision",
            f"decision:confirmatory:{index}:v1",
            provider_id=f"p{index}",
        )
        for index in range(3)
    ]
    manifest = sealed(
        "TrustedManifest",
        "manifest:confirmatory:v1",
        validator_contract_ref=ref(validator),
        deadline_receipt_quorum_policy_ref=ref(quorum),
        provider_profile_refs=sorted(
            (ref(item) for item in profiles),
            key=lambda item: (item["object_id"], item["content_sha256"]),
        ),
        qualification_decision_refs=sorted(
            (ref(item) for item in decisions),
            key=lambda item: (item["object_id"], item["content_sha256"]),
        ),
        qualification_verifier_contract_ref=ref(qualification_verifier),
        strong_bitcoin_verifier_contract_ref=ref(strong_bitcoin),
    )
    forecast = sealed("IssuedForecast", "forecast:confirmatory-manifest:v1", value="x")
    eligibility, claims = trust_root.derive_confirmatory_eligibility_from_trusted_manifest(
        manifest,
        forecast,
        component_specs=[],
        required_claim_requirements=[],
    )
    assert claims == ()
    assert eligibility["state"] == "UNRESOLVED"
    assert "FULL_TRUST_CORE_CHECK_AUTHORITY_NOT_IMPLEMENTED" in eligibility["reason_codes"]
