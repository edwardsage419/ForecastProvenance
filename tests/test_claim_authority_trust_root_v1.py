from __future__ import annotations

import pytest

import forecast_trust_core.claim_authority_trust_root_v1 as trust_root
from forecast_trust_core.canonical import seal_object


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def sealed(kind, object_id, **payload):
    return seal_object(
        {"schema_version": "1.0", **payload},
        object_type=kind,
        stable_context="claim-authority-trust-root-test",
        semantic_id=object_id,
    )


def manifest_fixture():
    validator = sealed("ValidatorContract", "validator:trust-root:v1", value="validator")
    quorum = sealed("PolicyDefinition", "policy:quorum:trust-root:v1", value="quorum")
    qualification_verifier = sealed("ValidatorContract", "validator:qualification:trust-root:v1", value="qualification")
    strong_bitcoin = sealed("StrongBitcoinVerifierContract", "validator:bitcoin:trust-root:v1", value="bitcoin")
    profiles = [
        sealed("RoughtimeProductionProviderProfile", f"profile:p{index}:v1", provider_id=f"p{index}")
        for index in range(3)
    ]
    decisions = [
        sealed("RoughtimeQualificationDecision", f"decision:p{index}:v1", provider_id=f"p{index}")
        for index in range(3)
    ]
    manifest = sealed(
        "TrustedManifest",
        "manifest:trust-root:v1",
        manifest_sequence=1,
        validator_contract_ref=ref(validator),
        deadline_receipt_quorum_policy_ref=ref(quorum),
        provider_profile_refs=sorted((ref(item) for item in profiles), key=lambda item: (item["object_id"], item["content_sha256"])),
        qualification_decision_refs=sorted((ref(item) for item in decisions), key=lambda item: (item["object_id"], item["content_sha256"])),
        qualification_verifier_contract_ref=ref(qualification_verifier),
        strong_bitcoin_verifier_contract_ref=ref(strong_bitcoin),
    )
    return {
        "manifest": manifest,
        "validator": validator,
        "quorum": quorum,
        "qualification_verifier": qualification_verifier,
        "strong_bitcoin": strong_bitcoin,
        "profiles": profiles,
        "decisions": decisions,
    }


def state_packages(fx):
    return [
        sealed(
            "RoughtimeProviderQualificationStatePackage",
            f"state:p{index}:v1",
            provider_id=f"p{index}",
            qualification_decision_ref=ref(fx["decisions"][index]),
        )
        for index in range(3)
    ]


def test_manifest_authority_context_extracts_exact_roots():
    fx = manifest_fixture()
    context = trust_root.derive_trusted_manifest_authority_context(fx["manifest"])
    assert context.validator_contract_ref == ref(fx["validator"])
    assert context.deadline_receipt_quorum_policy_ref == ref(fx["quorum"])
    assert context.strong_bitcoin_verifier_contract_ref == ref(fx["strong_bitcoin"])
    assert list(context.provider_profile_refs) == fx["manifest"]["provider_profile_refs"]
    assert list(context.qualification_decision_refs) == fx["manifest"]["qualification_decision_refs"]


def test_manifest_missing_strong_bitcoin_verifier_ref_fails_closed():
    fx = manifest_fixture()
    payload = {
        key: value for key, value in fx["manifest"].items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256", "strong_bitcoin_verifier_contract_ref"}
    }
    broken = seal_object(
        payload,
        object_type="TrustedManifest",
        stable_context="missing-bitcoin",
        semantic_id="manifest:missing-bitcoin:v1",
    )
    with pytest.raises(ValueError, match="strong_bitcoin_verifier_contract_ref"):
        trust_root.derive_trusted_manifest_authority_context(broken)


def test_self_asserted_manifest_status_is_rejected():
    fx = manifest_fixture()
    payload = {
        key: value for key, value in fx["manifest"].items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    payload["status"] = "ACCEPTED"
    broken = seal_object(
        payload,
        object_type="TrustedManifest",
        stable_context="self-status",
        semantic_id="manifest:self-status:v1",
    )
    with pytest.raises(ValueError, match="self-assert"):
        trust_root.derive_trusted_manifest_authority_context(broken)


def test_caller_cannot_substitute_main_validator_with_matching_expected_ref():
    fx = manifest_fixture()
    malicious = sealed("ValidatorContract", "validator:malicious:v1", value="malicious")
    inputs = {
        "provider_profiles": fx["profiles"],
        "qualification_state_packages": state_packages(fx),
        "validator_contract_ref": ref(malicious),
        "expected_validator_contract_ref": ref(malicious),
    }
    with pytest.raises(ValueError, match="caller authority override prohibited"):
        trust_root.bind_wall_clock_inputs_to_manifest(fx["manifest"], inputs)


def test_caller_cannot_substitute_quorum_or_qualification_verifier():
    fx = manifest_fixture()
    inputs = {
        "provider_profiles": fx["profiles"],
        "qualification_state_packages": state_packages(fx),
        "quorum_policy_ref": {"object_id": "policy:malicious", "content_sha256": "1" * 64},
        "qualification_verifier_contract_ref": {"object_id": "validator:malicious", "content_sha256": "2" * 64},
    }
    with pytest.raises(ValueError, match="caller authority override prohibited"):
        trust_root.bind_wall_clock_inputs_to_manifest(fx["manifest"], inputs)


def test_provider_profile_substitution_fails_against_manifest():
    fx = manifest_fixture()
    substitute = sealed("RoughtimeProductionProviderProfile", "profile:substitute:v1", provider_id="p0")
    profiles = [substitute, fx["profiles"][1], fx["profiles"][2]]
    inputs = {
        "provider_profiles": profiles,
        "qualification_state_packages": state_packages(fx),
    }
    with pytest.raises(ValueError, match="ProviderProfile set differs"):
        trust_root.bind_wall_clock_inputs_to_manifest(fx["manifest"], inputs)


def test_qualification_decision_substitution_fails_against_manifest():
    fx = manifest_fixture()
    packages = state_packages(fx)
    substitute = sealed("RoughtimeQualificationDecision", "decision:substitute:v1", provider_id="p0")
    packages[0] = sealed(
        "RoughtimeProviderQualificationStatePackage",
        "state:substitute:v1",
        provider_id="p0",
        qualification_decision_ref=ref(substitute),
    )
    with pytest.raises(ValueError, match="QualificationDecision set differs"):
        trust_root.bind_wall_clock_inputs_to_manifest(
            fx["manifest"],
            {"provider_profiles": fx["profiles"], "qualification_state_packages": packages},
        )


def test_caller_cannot_substitute_strong_bitcoin_verifier_with_matching_expected_ref():
    fx = manifest_fixture()
    malicious = sealed("StrongBitcoinVerifierContract", "validator:bitcoin:malicious:v1", value="malicious")
    inputs = {
        "strong_verifier_contract": malicious,
        "expected_strong_verifier_contract_ref": ref(malicious),
    }
    with pytest.raises(ValueError, match="caller authority override prohibited"):
        trust_root.bind_bitcoin_inputs_to_manifest(fx["manifest"], inputs)


def test_strong_bitcoin_verifier_contract_must_equal_manifest_ref():
    fx = manifest_fixture()
    substitute = sealed("StrongBitcoinVerifierContract", "validator:bitcoin:substitute:v1", value="substitute")
    with pytest.raises(ValueError, match="differs from TrustedManifest"):
        trust_root.bind_bitcoin_inputs_to_manifest(
            fx["manifest"], {"strong_verifier_contract": substitute}
        )


def test_manifest_acceptance_must_bind_same_trusted_manifest_before_final_evidence(monkeypatch):
    fx = manifest_fixture()
    other_manifest = sealed(
        "TrustedManifest",
        "manifest:other:v1",
        manifest_sequence=1,
        validator_contract_ref=ref(fx["validator"]),
        deadline_receipt_quorum_policy_ref=ref(fx["quorum"]),
        provider_profile_refs=fx["manifest"]["provider_profile_refs"],
        qualification_decision_refs=fx["manifest"]["qualification_decision_refs"],
        qualification_verifier_contract_ref=ref(fx["qualification_verifier"]),
        strong_bitcoin_verifier_contract_ref=ref(fx["strong_bitcoin"]),
    )
    acceptance = sealed(
        "ManifestAcceptance",
        "acceptance:wrong-manifest:v2",
        candidate_manifest_ref=ref(other_manifest),
    )
    with pytest.raises(ValueError, match="exact TrustedManifest authority root"):
        trust_root.validate_final_genesis_acceptance_from_trusted_manifest(
            fx["manifest"],
            acceptance,
            final_evidence_subject_ref=ref(acceptance),
            wall_clock_inputs={},
            bitcoin_inputs={},
        )
