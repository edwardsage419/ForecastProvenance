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
        stable_context="qualification-state-contract-test",
        semantic_id=object_id,
    )


def valid_state_package():
    profile = sealed("RefObject", "profile:state-contract:v1", value="p")
    decision = sealed("RefObject", "decision:state-contract:v1", value="d")
    verifier = sealed("RefObject", "verifier:state-contract:v1", value="v")
    package = sealed(
        "RoughtimeProviderQualificationStatePackage",
        "state-package:contract:v1",
        provider_id="roughtime.se",
        as_of_utc=DEADLINE,
        provider_profile_ref=ref(profile),
        qualification_decision_ref=ref(decision),
        qualification_evidence_manifest_sha256="1" * 64,
        qualification_verifier_contract_ref=ref(verifier),
        metadata_review_refs=[],
        requalification_event_refs=[],
        qualification_state_report_sha256="2" * 64,
        qualification_state="PRODUCTION_QUALIFIED",
    )
    return package, profile, decision, verifier


def reseal_with_extra(obj, object_id):
    payload = {
        key: value
        for key, value in obj.items()
        if key not in {"schema_version", "object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    payload["unexpected"] = "forbidden"
    return sealed(obj["object_type"], object_id, **payload)


def test_exact_qualification_state_package_contract_is_accepted():
    package, _profile, _decision, _verifier = valid_state_package()
    authority._validate_qualification_state_package_contract(package)


def test_extra_field_in_sealed_qualification_state_package_is_rejected():
    package, _profile, _decision, _verifier = valid_state_package()
    bad = reseal_with_extra(package, "state-package:extra:v1")
    with pytest.raises(ValueError, match="field set mismatch"):
        authority._validate_qualification_state_package_contract(bad)


def test_public_provider_admission_rejects_contract_invalid_package_before_recomputation():
    package, profile, decision, verifier = valid_state_package()
    bad = reseal_with_extra(package, "state-package:public-extra:v1")
    with pytest.raises(ValueError, match="field set mismatch"):
        authority.validate_provider_admission_set_authoritatively(
            [bad],
            frozen_deadline_utc=DEADLINE,
            admitted_provider_profile_refs=[ref(profile)],
            admitted_qualification_decision_refs=[ref(decision)],
            provider_inputs={},
            qualification_verifier_contract_ref=ref(verifier),
        )


def test_invalid_provider_id_in_sealed_state_package_is_rejected():
    package, _profile, _decision, _verifier = valid_state_package()
    payload = {
        key: value
        for key, value in package.items()
        if key not in {"schema_version", "object_type", "object_id", "payload_sha256", "content_sha256", "provider_id"}
    }
    bad = sealed(
        "RoughtimeProviderQualificationStatePackage",
        "state-package:provider-substitution:v1",
        provider_id="unlisted.example",
        **payload,
    )
    with pytest.raises(ValueError, match="provider_id invalid"):
        authority._validate_qualification_state_package_contract(bad)
