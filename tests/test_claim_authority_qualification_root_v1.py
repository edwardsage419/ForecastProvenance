from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import forecast_trust_core.claim_authority_trust_root_v1 as trust_root
from forecast_trust_core.canonical import seal_object


PROFILE_SHA256 = "a" * 64
BINARY_SHA256 = "b" * 64
AUTHORITY_ID = "authority:bootstrap:test:v1"
AUTHORITY_PUBLIC_KEY = b"k" * 32


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def sealed(kind, object_id, **payload):
    return seal_object(
        {"schema_version": "1.0", **payload},
        object_type=kind,
        stable_context="qualification-root-test",
        semantic_id=object_id,
    )


def fixture():
    validator = sealed("ValidatorContract", "validator:main:test:v1", value="main")
    quorum = sealed("PolicyDefinition", "policy:quorum:test:v1", value="quorum")
    profiles = [
        sealed("RoughtimeProductionProviderProfile", f"profile:p{index}:v1", provider_id=f"p{index}")
        for index in range(3)
    ]
    decisions = [
        sealed("RoughtimeQualificationDecision", f"decision:p{index}:v1", provider_id=f"p{index}")
        for index in range(3)
    ]
    qualification_contract = sealed(
        "RoughtimeQualificationVerifierContract",
        "validator:qualification:test:v1",
        criteria_id="FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1",
        criteria_sha256="88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e",
        validator_contract_ref=ref(validator),
        decision_signature_projection="FPP_ROUGHTIME_QUALIFICATION_DECISION_V1",
        signature_algorithm="ED25519",
        authority_id=AUTHORITY_ID,
        authority_public_key_sha256=hashlib.sha256(AUTHORITY_PUBLIC_KEY).hexdigest(),
        ed25519_verifier_build_profile_sha256=PROFILE_SHA256,
        ed25519_verifier_binary_sha256=BINARY_SHA256,
    )
    bitcoin = sealed(
        "StrongBitcoinVerifierContract",
        "validator:bitcoin:test:v1",
        value="bitcoin",
    )
    manifest = sealed(
        "TrustedManifest",
        "manifest:qualification-root:test:v1",
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
        qualification_verifier_contract_ref=ref(qualification_contract),
        strong_bitcoin_verifier_contract_ref=ref(bitcoin),
    )
    packages = [
        sealed(
            "RoughtimeProviderQualificationStatePackage",
            f"state:p{index}:v1",
            provider_id=f"p{index}",
            qualification_decision_ref=ref(decisions[index]),
        )
        for index in range(3)
    ]
    build_profile = {"binary_sha256": BINARY_SHA256}
    provider_inputs = {
        f"p{index}": {"profile": profiles[index], "decision": decisions[index]}
        for index in range(3)
    }
    wall = {
        "provider_profiles": profiles,
        "qualification_state_packages": packages,
        "provider_authority_inputs": provider_inputs,
        "qualification_verifier_contract": qualification_contract,
        "qualification_ed25519_build_profile": build_profile,
        "qualification_ed25519_binary": Path("synthetic-ed25519-verifier"),
    }
    return {
        "validator": validator,
        "manifest": manifest,
        "profiles": profiles,
        "decisions": decisions,
        "qualification_contract": qualification_contract,
        "build_profile": build_profile,
        "wall": wall,
    }


def patch_pinned_verifier(monkeypatch):
    sentinel = object()
    monkeypatch.setattr(
        trust_root,
        "validate_ed25519_build_profile",
        lambda _profile: PROFILE_SHA256,
    )
    monkeypatch.setattr(
        trust_root,
        "PinnedEd25519Verifier",
        lambda path, digest: sentinel,
    )
    return sentinel


def test_provider_runtime_cannot_inject_signature_verifier(monkeypatch):
    fx = fixture()
    patch_pinned_verifier(monkeypatch)
    fx["wall"]["provider_authority_inputs"]["p0"]["signature_verifier"] = lambda *_args: True
    with pytest.raises(ValueError, match="caller authority override prohibited"):
        trust_root.bind_wall_clock_inputs_to_manifest(
            fx["manifest"],
            fx["wall"],
            qualification_authority_id=AUTHORITY_ID,
            qualification_authority_public_key=AUTHORITY_PUBLIC_KEY,
        )


def test_external_authority_key_must_match_manifest_bound_contract(monkeypatch):
    fx = fixture()
    patch_pinned_verifier(monkeypatch)
    with pytest.raises(ValueError, match="public key differs from frozen contract"):
        trust_root.bind_wall_clock_inputs_to_manifest(
            fx["manifest"],
            fx["wall"],
            qualification_authority_id=AUTHORITY_ID,
            qualification_authority_public_key=b"x" * 32,
        )


def test_substituted_qualification_verifier_contract_fails_manifest_binding(monkeypatch):
    fx = fixture()
    patch_pinned_verifier(monkeypatch)
    substitute = sealed(
        "RoughtimeQualificationVerifierContract",
        "validator:qualification:substitute:v1",
        criteria_id="FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1",
        criteria_sha256="88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e",
        validator_contract_ref=ref(fx["validator"]),
        decision_signature_projection="FPP_ROUGHTIME_QUALIFICATION_DECISION_V1",
        signature_algorithm="ED25519",
        authority_id=AUTHORITY_ID,
        authority_public_key_sha256=hashlib.sha256(AUTHORITY_PUBLIC_KEY).hexdigest(),
        ed25519_verifier_build_profile_sha256=PROFILE_SHA256,
        ed25519_verifier_binary_sha256=BINARY_SHA256,
    )
    fx["wall"]["qualification_verifier_contract"] = substitute
    with pytest.raises(ValueError, match="differs from TrustedManifest"):
        trust_root.bind_wall_clock_inputs_to_manifest(
            fx["manifest"],
            fx["wall"],
            qualification_authority_id=AUTHORITY_ID,
            qualification_authority_public_key=AUTHORITY_PUBLIC_KEY,
        )


def test_qualification_contract_cannot_bind_different_main_validator(monkeypatch):
    fx = fixture()
    patch_pinned_verifier(monkeypatch)
    malicious_validator = sealed("ValidatorContract", "validator:malicious:test:v1", value="malicious")
    replacement = sealed(
        "RoughtimeQualificationVerifierContract",
        "validator:qualification:test:v1",
        criteria_id="FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1",
        criteria_sha256="88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e",
        validator_contract_ref=ref(malicious_validator),
        decision_signature_projection="FPP_ROUGHTIME_QUALIFICATION_DECISION_V1",
        signature_algorithm="ED25519",
        authority_id=AUTHORITY_ID,
        authority_public_key_sha256=hashlib.sha256(AUTHORITY_PUBLIC_KEY).hexdigest(),
        ed25519_verifier_build_profile_sha256=PROFILE_SHA256,
        ed25519_verifier_binary_sha256=BINARY_SHA256,
    )
    payload = {
        key: value
        for key, value in fx["manifest"].items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    payload["qualification_verifier_contract_ref"] = ref(replacement)
    manifest = seal_object(
        payload,
        object_type="TrustedManifest",
        stable_context="qualification-root-main-validator-substitution",
        semantic_id="manifest:qualification-root:substitute:v1",
    )
    fx["wall"]["qualification_verifier_contract"] = replacement
    with pytest.raises(ValueError, match="ValidatorContract mismatch"):
        trust_root.bind_wall_clock_inputs_to_manifest(
            manifest,
            fx["wall"],
            qualification_authority_id=AUTHORITY_ID,
            qualification_authority_public_key=AUTHORITY_PUBLIC_KEY,
        )


def test_extra_provider_authority_input_is_rejected(monkeypatch):
    fx = fixture()
    patch_pinned_verifier(monkeypatch)
    fx["wall"]["provider_authority_inputs"]["p-extra"] = {}
    with pytest.raises(ValueError, match="exactly match the admitted provider identity set"):
        trust_root.bind_wall_clock_inputs_to_manifest(
            fx["manifest"],
            fx["wall"],
            qualification_authority_id=AUTHORITY_ID,
            qualification_authority_public_key=AUTHORITY_PUBLIC_KEY,
        )


def test_state_package_provider_identity_set_must_match_profiles(monkeypatch):
    fx = fixture()
    patch_pinned_verifier(monkeypatch)
    fx["wall"]["qualification_state_packages"][2] = sealed(
        "RoughtimeProviderQualificationStatePackage",
        "state:wrong-provider:v1",
        provider_id="other-provider",
        qualification_decision_ref=ref(fx["decisions"][2]),
    )
    with pytest.raises(ValueError, match="provider identities differ from ProviderProfiles"):
        trust_root.bind_wall_clock_inputs_to_manifest(
            fx["manifest"],
            fx["wall"],
            qualification_authority_id=AUTHORITY_ID,
            qualification_authority_public_key=AUTHORITY_PUBLIC_KEY,
        )


def test_exact_binding_injects_only_pinned_authority(monkeypatch):
    fx = fixture()
    sentinel = patch_pinned_verifier(monkeypatch)
    bound = trust_root.bind_wall_clock_inputs_to_manifest(
        fx["manifest"],
        fx["wall"],
        qualification_authority_id=AUTHORITY_ID,
        qualification_authority_public_key=AUTHORITY_PUBLIC_KEY,
    )
    for provider_id, item in bound["provider_authority_inputs"].items():
        assert item["expected_authority_id"] == AUTHORITY_ID
        assert item["expected_authority_public_key"] == AUTHORITY_PUBLIC_KEY
        assert item["signature_verifier"] is sentinel
        assert provider_id in {"p0", "p1", "p2"}
    assert "qualification_verifier_contract" not in bound
    assert "qualification_ed25519_build_profile" not in bound
    assert "qualification_ed25519_binary" not in bound
    assert bound["qualification_verifier_contract_ref"] == fx["manifest"]["qualification_verifier_contract_ref"]
    assert bound["validator_contract_ref"] == fx["manifest"]["validator_contract_ref"]
