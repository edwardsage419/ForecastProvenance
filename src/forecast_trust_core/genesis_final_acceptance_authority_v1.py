from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from . import claim_authority_trust_root_v1 as _trust_root
from . import claim_authority_v1 as _authority
from . import genesis_governance_authority_v1_hardening as _governance
from .canonical import CanonicalizationError, validate_ref, verify_sealed_object

GOVERNANCE_VERIFIER_REF_FIELD = "genesis_governance_signature_verifier_contract_ref"


def _exact_ref(obj: Mapping[str, Any], *, object_type: str | None = None) -> dict[str, str]:
    if not isinstance(obj, Mapping) or not verify_sealed_object(obj):
        raise ValueError("Genesis final-acceptance authority input must be a valid sealed object")
    if object_type is not None and obj.get("object_type") != object_type:
        raise ValueError(f"expected sealed object_type {object_type}")
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def _required_manifest_ref(trusted_manifest: Mapping[str, Any], field: str) -> dict[str, str]:
    value = trusted_manifest.get(field)
    try:
        validate_ref(value)
    except (CanonicalizationError, TypeError) as exc:
        raise ValueError(f"TrustedManifest {field} is missing or malformed") from exc
    return dict(value)


def _required_manifest_governance_verifier_ref(
    trusted_manifest: Mapping[str, Any],
) -> dict[str, str]:
    return _required_manifest_ref(trusted_manifest, GOVERNANCE_VERIFIER_REF_FIELD)


def bind_genesis_governance_signature_inputs_to_manifest(
    trusted_manifest: Mapping[str, Any],
    acceptance: Mapping[str, Any],
    *,
    signature_evidence: Mapping[str, Any],
    bootstrap_root: Mapping[str, Any],
    governance_verifier_contract: Mapping[str, Any],
    ed25519_verifier_build_profile: Mapping[str, Any],
    ed25519_verifier_binary: str | Path,
) -> tuple[_trust_root.TrustedManifestAuthorityContext, dict[str, Any]]:
    context = _trust_root.derive_trusted_manifest_authority_context(trusted_manifest)
    manifest_ref = dict(context.trusted_manifest_ref)
    if acceptance.get("candidate_manifest_ref") != manifest_ref:
        raise ValueError(
            "ManifestAcceptance does not bind the exact TrustedManifest authority root"
        )

    manifest_acceptance_rule_ref = _required_manifest_ref(
        trusted_manifest,
        "acceptance_rule_ref",
    )
    if acceptance.get("acceptance_rule_ref") != manifest_acceptance_rule_ref:
        raise ValueError(
            "ManifestAcceptance acceptance rule differs from TrustedManifest"
        )

    expected_contract_ref = _required_manifest_governance_verifier_ref(trusted_manifest)
    contract_ref = _exact_ref(
        governance_verifier_contract,
        object_type="GenesisGovernanceSignatureVerifierContract",
    )
    if contract_ref != expected_contract_ref:
        raise ValueError(
            "GenesisGovernanceSignatureVerifierContract differs from TrustedManifest"
        )

    _governance.validate_governance_signature_verifier_contract(
        governance_verifier_contract,
        bootstrap_root=bootstrap_root,
        ed25519_verifier_build_profile=ed25519_verifier_build_profile,
        expected_validator_contract_ref=dict(context.validator_contract_ref),
    )

    bound = {
        "signature_evidence": signature_evidence,
        "bootstrap_root": bootstrap_root,
        "governance_verifier_contract": governance_verifier_contract,
        "ed25519_verifier_build_profile": ed25519_verifier_build_profile,
        "ed25519_verifier_binary": Path(ed25519_verifier_binary),
        "expected_governance_verifier_contract_ref": expected_contract_ref,
    }
    return context, bound


def validate_final_genesis_acceptance_from_trusted_manifest(
    trusted_manifest: Mapping[str, Any],
    acceptance: Mapping[str, Any],
    *,
    signature_evidence: Mapping[str, Any],
    bootstrap_root: Mapping[str, Any],
    governance_verifier_contract: Mapping[str, Any],
    ed25519_verifier_build_profile: Mapping[str, Any],
    ed25519_verifier_binary: str | Path,
    final_evidence_subject_ref: Mapping[str, Any],
    wall_clock_inputs: Mapping[str, Any],
    bitcoin_inputs: Mapping[str, Any],
    qualification_authority_id: str | None = None,
    qualification_authority_public_key: bytes | None = None,
):
    context, governance_inputs = bind_genesis_governance_signature_inputs_to_manifest(
        trusted_manifest,
        acceptance,
        signature_evidence=signature_evidence,
        bootstrap_root=bootstrap_root,
        governance_verifier_contract=governance_verifier_contract,
        ed25519_verifier_build_profile=ed25519_verifier_build_profile,
        ed25519_verifier_binary=ed25519_verifier_binary,
    )
    wall = _trust_root.bind_wall_clock_inputs_to_manifest(
        trusted_manifest,
        wall_clock_inputs,
        qualification_authority_id=qualification_authority_id,
        qualification_authority_public_key=qualification_authority_public_key,
    )
    bitcoin = _trust_root.bind_bitcoin_inputs_to_manifest(trusted_manifest, bitcoin_inputs)
    return _authority.validate_final_genesis_acceptance_authoritatively(
        acceptance,
        final_evidence_subject_ref=final_evidence_subject_ref,
        wall_clock_inputs=wall,
        bitcoin_inputs=bitcoin,
        governance_signature_inputs=governance_inputs,
    )


def validate_persisted_final_acceptance_report_from_trusted_manifest(
    persisted_report: Mapping[str, Any],
    trusted_manifest: Mapping[str, Any],
    acceptance: Mapping[str, Any],
    *,
    signature_evidence: Mapping[str, Any],
    bootstrap_root: Mapping[str, Any],
    governance_verifier_contract: Mapping[str, Any],
    ed25519_verifier_build_profile: Mapping[str, Any],
    ed25519_verifier_binary: str | Path,
    final_evidence_subject_ref: Mapping[str, Any],
    wall_clock_inputs: Mapping[str, Any],
    bitcoin_inputs: Mapping[str, Any],
    qualification_authority_id: str | None = None,
    qualification_authority_public_key: bytes | None = None,
):
    context, governance_inputs = bind_genesis_governance_signature_inputs_to_manifest(
        trusted_manifest,
        acceptance,
        signature_evidence=signature_evidence,
        bootstrap_root=bootstrap_root,
        governance_verifier_contract=governance_verifier_contract,
        ed25519_verifier_build_profile=ed25519_verifier_build_profile,
        ed25519_verifier_binary=ed25519_verifier_binary,
    )
    wall = _trust_root.bind_wall_clock_inputs_to_manifest(
        trusted_manifest,
        wall_clock_inputs,
        qualification_authority_id=qualification_authority_id,
        qualification_authority_public_key=qualification_authority_public_key,
    )
    bitcoin = _trust_root.bind_bitcoin_inputs_to_manifest(trusted_manifest, bitcoin_inputs)
    return _authority.validate_persisted_final_acceptance_report_authoritatively(
        persisted_report,
        acceptance,
        final_evidence_subject_ref=final_evidence_subject_ref,
        wall_clock_inputs=wall,
        bitcoin_inputs=bitcoin,
        trusted_manifest_ref=dict(context.trusted_manifest_ref),
        governance_signature_inputs=governance_inputs,
    )
