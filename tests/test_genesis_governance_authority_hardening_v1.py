from __future__ import annotations

import base64

import pytest

import forecast_trust_core.genesis_governance_authority_v1_hardening as hardening
from forecast_trust_core.canonical import seal_object


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def sealed(kind, object_id, **payload):
    return seal_object(
        {"schema_version": "1.0", **payload},
        object_type=kind,
        stable_context="genesis-governance-hardening-test",
        semantic_id=object_id,
    )


def bootstrap_root(*, project_id=hardening.PROJECT_ID):
    rule = sealed("PolicyDefinition", "policy:acceptance:hardening:v2", value="rule")
    return sealed(
        "BootstrapGovernanceRoot",
        "bootstrap:hardening:v1",
        project_id=project_id,
        authority_id="authority:genesis-owner:v1",
        authority_key_type="ED25519",
        authority_public_key_base64=base64.b64encode(b"\x01" * 32).decode("ascii"),
        acceptance_rule_ref=ref(rule),
        canonicalization_scheme="FPP_JCS_1",
        hash_algorithm="SHA-256",
        bootstrap_version=1,
    )


def test_bootstrap_project_id_is_exact():
    bad = bootstrap_root(project_id="other-project")
    with pytest.raises(ValueError, match="project_id mismatch"):
        hardening.validate_bootstrap_governance_root(bad)


def test_governance_verifier_requires_both_frozen_projections(monkeypatch):
    root = bootstrap_root()
    contract = sealed(
        "GenesisGovernanceSignatureVerifierContract",
        "validator:governance:hardening:v1",
        validator_contract_ref={"object_id": "validator:main:v1", "content_sha256": "1" * 64},
        signature_algorithm="ED25519",
        authority_id="authority:genesis-owner:v1",
        authority_public_key_sha256="2" * 64,
        ed25519_verifier_build_profile_sha256="3" * 64,
        ed25519_verifier_binary_sha256="4" * 64,
        allowed_signature_projections=[hardening._base.MANIFEST_ACCEPTANCE_PROJECTION],
    )
    monkeypatch.setattr(
        hardening._base,
        "validate_governance_signature_verifier_contract",
        lambda *args, **kwargs: pytest.fail("base validator must not run for incomplete projection set"),
    )
    with pytest.raises(ValueError, match="exact frozen projection set"):
        hardening.validate_governance_signature_verifier_contract(
            contract,
            bootstrap_root=root,
            ed25519_verifier_build_profile={},
            expected_validator_contract_ref={"object_id": "validator:main:v1", "content_sha256": "1" * 64},
        )


def test_governance_verifier_exact_projection_order_is_frozen(monkeypatch):
    root = bootstrap_root()
    contract = sealed(
        "GenesisGovernanceSignatureVerifierContract",
        "validator:governance:reordered:v1",
        validator_contract_ref={"object_id": "validator:main:v1", "content_sha256": "1" * 64},
        signature_algorithm="ED25519",
        authority_id="authority:genesis-owner:v1",
        authority_public_key_sha256="2" * 64,
        ed25519_verifier_build_profile_sha256="3" * 64,
        ed25519_verifier_binary_sha256="4" * 64,
        allowed_signature_projections=list(reversed(hardening.REQUIRED_SIGNATURE_PROJECTIONS)),
    )
    monkeypatch.setattr(
        hardening._base,
        "validate_governance_signature_verifier_contract",
        lambda *args, **kwargs: pytest.fail("base validator must not run for reordered projection set"),
    )
    with pytest.raises(ValueError, match="exact frozen projection set"):
        hardening.validate_governance_signature_verifier_contract(
            contract,
            bootstrap_root=root,
            ed25519_verifier_build_profile={},
            expected_validator_contract_ref={"object_id": "validator:main:v1", "content_sha256": "1" * 64},
        )
