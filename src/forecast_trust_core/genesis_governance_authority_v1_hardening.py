from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from . import genesis_governance_authority_v1 as _base

PROJECT_ID = "forecast-provenance-project"
REQUIRED_SIGNATURE_PROJECTIONS = (
    _base.GENESIS_AUTHORIZATION_PROJECTION,
    _base.MANIFEST_ACCEPTANCE_PROJECTION,
)


def validate_bootstrap_governance_root(root: Mapping[str, Any]) -> bytes:
    if not isinstance(root, Mapping):
        raise ValueError("BootstrapGovernanceRoot must be an object")
    if root.get("project_id") != PROJECT_ID:
        raise ValueError("BootstrapGovernanceRoot project_id mismatch")
    return _base.validate_bootstrap_governance_root(root)


def validate_governance_signature_verifier_contract(
    contract: Mapping[str, Any],
    *,
    bootstrap_root: Mapping[str, Any],
    ed25519_verifier_build_profile: Mapping[str, Any],
    expected_validator_contract_ref: Mapping[str, Any],
) -> bytes:
    validate_bootstrap_governance_root(bootstrap_root)
    projections = contract.get("allowed_signature_projections") if isinstance(contract, Mapping) else None
    if projections != list(REQUIRED_SIGNATURE_PROJECTIONS):
        raise ValueError(
            "Genesis governance signature verifier contract must authorize the exact frozen projection set"
        )
    return _base.validate_governance_signature_verifier_contract(
        contract,
        bootstrap_root=bootstrap_root,
        ed25519_verifier_build_profile=ed25519_verifier_build_profile,
        expected_validator_contract_ref=expected_validator_contract_ref,
    )


def verify_manifest_acceptance_signature_authoritatively(
    acceptance: Mapping[str, Any],
    *,
    signature_evidence: Mapping[str, Any],
    bootstrap_root: Mapping[str, Any],
    governance_verifier_contract: Mapping[str, Any],
    ed25519_verifier_build_profile: Mapping[str, Any],
    ed25519_verifier_binary: Path,
    expected_validator_contract_ref: Mapping[str, Any],
) -> dict[str, str]:
    validate_governance_signature_verifier_contract(
        governance_verifier_contract,
        bootstrap_root=bootstrap_root,
        ed25519_verifier_build_profile=ed25519_verifier_build_profile,
        expected_validator_contract_ref=expected_validator_contract_ref,
    )
    return _base.verify_manifest_acceptance_signature_authoritatively(
        acceptance,
        signature_evidence=signature_evidence,
        bootstrap_root=bootstrap_root,
        governance_verifier_contract=governance_verifier_contract,
        ed25519_verifier_build_profile=ed25519_verifier_build_profile,
        ed25519_verifier_binary=Path(ed25519_verifier_binary),
        expected_validator_contract_ref=expected_validator_contract_ref,
    )
