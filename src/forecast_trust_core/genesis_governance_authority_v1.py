from __future__ import annotations

import base64
import binascii
import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

from ._ed25519_qualification import validate_build_profile
from ._ed25519_verifier import PinnedEd25519Verifier
from .canonical import (
    canonical_json,
    content_hash,
    require_ascii_token,
    sorted_refs,
    validate_ref,
    verify_sealed_object,
)
from .claim_authority_contract_gate_v1 import validate_manifest_acceptance_v2_contract


BOOTSTRAP_SCHEMA_VERSION = "1.0"
BOOTSTRAP_OBJECT_TYPE = "BootstrapGovernanceRoot"
GOVERNANCE_VERIFIER_SCHEMA_VERSION = "1.0"
GOVERNANCE_VERIFIER_OBJECT_TYPE = "GenesisGovernanceSignatureVerifierContract"
GOVERNANCE_SIGNATURE_SCHEMA_VERSION = "1.0"
GOVERNANCE_SIGNATURE_OBJECT_TYPE = "GenesisGovernanceSignature"

MANIFEST_ACCEPTANCE_PROJECTION = "FPP_MANIFEST_ACCEPTANCE_V2"
GENESIS_AUTHORIZATION_PROJECTION = "FPP_GENESIS_AUTHORIZATION_V1"
KNOWN_PROJECTIONS = frozenset({MANIFEST_ACCEPTANCE_PROJECTION, GENESIS_AUTHORIZATION_PROJECTION})
MANIFEST_ACCEPTANCE_SIGNATURE_DOMAIN = b"FPP_MANIFEST_ACCEPTANCE_V2\x00"

BOOTSTRAP_KEYS = frozenset({
    "schema_version",
    "object_type",
    "project_id",
    "authority_id",
    "authority_key_type",
    "authority_public_key_base64",
    "acceptance_rule_ref",
    "canonicalization_scheme",
    "hash_algorithm",
    "bootstrap_version",
    "object_id",
    "payload_sha256",
    "content_sha256",
})

GOVERNANCE_VERIFIER_KEYS = frozenset({
    "schema_version",
    "object_type",
    "validator_contract_ref",
    "signature_algorithm",
    "authority_id",
    "authority_public_key_sha256",
    "ed25519_verifier_build_profile_sha256",
    "ed25519_verifier_binary_sha256",
    "allowed_signature_projections",
    "object_id",
    "payload_sha256",
    "content_sha256",
})

GOVERNANCE_SIGNATURE_KEYS = frozenset({
    "schema_version",
    "object_type",
    "signature_projection",
    "signed_payload",
    "signed_payload_sha256",
    "signature_algorithm",
    "authority_signature_base64",
    "object_id",
    "payload_sha256",
    "content_sha256",
})

MANIFEST_ACCEPTANCE_SIGNED_PAYLOAD_KEYS = frozenset({
    "acceptance_schema_version",
    "acceptance_object_id",
    "candidate_manifest_ref",
    "bootstrap_governance_root_ref",
    "acceptance_rule_ref",
    "required_validation_report_refs",
    "authority_ref",
    "decision",
    "reason_codes",
    "blocking_finding_refs",
})


def _exact_keys(value: Mapping[str, Any], expected: frozenset[str], name: str) -> None:
    actual = frozenset(value)
    if actual != expected:
        raise ValueError(
            f"{name} field set mismatch; missing={sorted(expected - actual)} "
            f"extra={sorted(actual - expected)}"
        )


def _hex64(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"{name} must be 64 lowercase hex characters")
    return value


def _strict_b64(value: Any, name: str, expected_len: int) -> bytes:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be nonempty canonical base64")
    try:
        decoded = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"{name} must be strict base64") from exc
    if len(decoded) != expected_len:
        raise ValueError(f"{name} must decode to exactly {expected_len} bytes")
    if base64.b64encode(decoded).decode("ascii") != value:
        raise ValueError(f"{name} must use canonical base64")
    return decoded


def _ref(value: Any, name: str) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object reference")
    if set(value) != {"object_id", "content_sha256"}:
        raise ValueError(f"{name} must contain object_id and content_sha256 only")
    object_id = require_ascii_token(value["object_id"], f"{name}.object_id")
    return {
        "object_id": object_id,
        "content_sha256": _hex64(value["content_sha256"], f"{name}.content_sha256"),
    }


def _exact_ref(obj: Mapping[str, Any], *, object_type: str | None = None) -> dict[str, str]:
    if not isinstance(obj, Mapping) or not verify_sealed_object(obj):
        raise ValueError("governance authority input must be a valid sealed object")
    if object_type is not None and obj.get("object_type") != object_type:
        raise ValueError(f"expected object_type {object_type}")
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def _sorted_unique_refs(values: Any, name: str) -> list[dict[str, str]]:
    if not isinstance(values, list):
        raise ValueError(f"{name} must be an array")
    normalized = [_ref(value, f"{name}[]") for value in values]
    expected = sorted_refs(normalized)
    if normalized != expected or len({(item["object_id"], item["content_sha256"]) for item in normalized}) != len(normalized):
        raise ValueError(f"{name} must contain unique sorted exact references")
    return normalized


def _sorted_unique_tokens(values: Any, name: str) -> list[str]:
    if not isinstance(values, list):
        raise ValueError(f"{name} must be an array")
    normalized: list[str] = []
    for index, value in enumerate(values):
        normalized.append(require_ascii_token(value, f"{name}[{index}]"))
    if normalized != sorted(normalized) or len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must contain unique sorted tokens")
    return normalized


def validate_bootstrap_governance_root(root: Mapping[str, Any]) -> bytes:
    if not isinstance(root, Mapping):
        raise ValueError("BootstrapGovernanceRoot must be an object")
    _exact_keys(root, BOOTSTRAP_KEYS, "BootstrapGovernanceRoot")
    if not verify_sealed_object(root):
        raise ValueError("BootstrapGovernanceRoot seal invalid")
    if root["schema_version"] != BOOTSTRAP_SCHEMA_VERSION or root["object_type"] != BOOTSTRAP_OBJECT_TYPE:
        raise ValueError("BootstrapGovernanceRoot schema identity mismatch")
    require_ascii_token(root["project_id"], "BootstrapGovernanceRoot.project_id")
    require_ascii_token(root["authority_id"], "BootstrapGovernanceRoot.authority_id")
    if root["authority_key_type"] != "ED25519":
        raise ValueError("BootstrapGovernanceRoot authority_key_type mismatch")
    public_key = _strict_b64(root["authority_public_key_base64"], "authority_public_key_base64", 32)
    _ref(root["acceptance_rule_ref"], "BootstrapGovernanceRoot.acceptance_rule_ref")
    if root["canonicalization_scheme"] != "FPP_JCS_1":
        raise ValueError("BootstrapGovernanceRoot canonicalization_scheme mismatch")
    if root["hash_algorithm"] != "SHA-256":
        raise ValueError("BootstrapGovernanceRoot hash_algorithm mismatch")
    if type(root["bootstrap_version"]) is not int or root["bootstrap_version"] != 1:
        raise ValueError("BootstrapGovernanceRoot bootstrap_version mismatch")
    return public_key


def validate_governance_signature_verifier_contract(
    contract: Mapping[str, Any],
    *,
    bootstrap_root: Mapping[str, Any],
    ed25519_verifier_build_profile: Mapping[str, Any],
    expected_validator_contract_ref: Mapping[str, Any],
) -> bytes:
    if not isinstance(contract, Mapping):
        raise ValueError("Genesis governance signature verifier contract must be an object")
    _exact_keys(contract, GOVERNANCE_VERIFIER_KEYS, "GenesisGovernanceSignatureVerifierContract")
    if not verify_sealed_object(contract):
        raise ValueError("Genesis governance signature verifier contract seal invalid")
    if (
        contract["schema_version"] != GOVERNANCE_VERIFIER_SCHEMA_VERSION
        or contract["object_type"] != GOVERNANCE_VERIFIER_OBJECT_TYPE
    ):
        raise ValueError("Genesis governance signature verifier contract schema identity mismatch")
    if contract["signature_algorithm"] != "ED25519":
        raise ValueError("Genesis governance signature verifier contract algorithm mismatch")

    public_key = validate_bootstrap_governance_root(bootstrap_root)
    if contract["authority_id"] != bootstrap_root["authority_id"]:
        raise ValueError("governance verifier authority_id differs from BootstrapGovernanceRoot")
    expected_key_hash = hashlib.sha256(public_key).hexdigest()
    if contract["authority_public_key_sha256"] != expected_key_hash:
        raise ValueError("governance verifier public-key hash differs from BootstrapGovernanceRoot")

    validate_ref(expected_validator_contract_ref)
    if _ref(contract["validator_contract_ref"], "validator_contract_ref") != dict(expected_validator_contract_ref):
        raise ValueError("governance verifier main ValidatorContract mismatch")

    build_profile_sha256 = validate_build_profile(ed25519_verifier_build_profile)
    if contract["ed25519_verifier_build_profile_sha256"] != build_profile_sha256:
        raise ValueError("governance verifier build-profile hash mismatch")
    if contract["ed25519_verifier_binary_sha256"] != ed25519_verifier_build_profile["binary_sha256"]:
        raise ValueError("governance verifier binary hash differs from build profile")

    projections = contract["allowed_signature_projections"]
    if not isinstance(projections, list) or not projections:
        raise ValueError("allowed_signature_projections must be a nonempty array")
    if any(item not in KNOWN_PROJECTIONS for item in projections):
        raise ValueError("governance verifier contract contains unknown signature projection")
    if projections != sorted(projections) or len(set(projections)) != len(projections):
        raise ValueError("allowed_signature_projections must be unique and sorted")
    return public_key


def manifest_acceptance_signed_payload(acceptance: Mapping[str, Any]) -> dict[str, Any]:
    validate_manifest_acceptance_v2_contract(acceptance)
    reports = _sorted_unique_refs(
        acceptance["required_validation_report_refs"],
        "ManifestAcceptance.required_validation_report_refs",
    )
    blocking = _sorted_unique_refs(
        acceptance["blocking_finding_refs"],
        "ManifestAcceptance.blocking_finding_refs",
    )
    reasons = _sorted_unique_tokens(acceptance["reason_codes"], "ManifestAcceptance.reason_codes")
    return {
        "acceptance_schema_version": acceptance["schema_version"],
        "acceptance_object_id": acceptance["object_id"],
        "candidate_manifest_ref": _ref(acceptance["candidate_manifest_ref"], "candidate_manifest_ref"),
        "bootstrap_governance_root_ref": _ref(
            acceptance["bootstrap_governance_root_ref"], "bootstrap_governance_root_ref"
        ),
        "acceptance_rule_ref": _ref(acceptance["acceptance_rule_ref"], "acceptance_rule_ref"),
        "required_validation_report_refs": reports,
        "authority_ref": _ref(acceptance["authority_ref"], "authority_ref"),
        "decision": acceptance["decision"],
        "reason_codes": reasons,
        "blocking_finding_refs": blocking,
    }


def _validate_manifest_acceptance_signed_payload(payload: Mapping[str, Any]) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("ManifestAcceptance signed payload must be an object")
    _exact_keys(payload, MANIFEST_ACCEPTANCE_SIGNED_PAYLOAD_KEYS, "ManifestAcceptance signed payload")
    if payload["acceptance_schema_version"] != "2.0":
        raise ValueError("ManifestAcceptance signed payload schema version mismatch")
    require_ascii_token(payload["acceptance_object_id"], "acceptance_object_id")
    for field in (
        "candidate_manifest_ref",
        "bootstrap_governance_root_ref",
        "acceptance_rule_ref",
        "authority_ref",
    ):
        _ref(payload[field], field)
    _sorted_unique_refs(payload["required_validation_report_refs"], "required_validation_report_refs")
    _sorted_unique_refs(payload["blocking_finding_refs"], "blocking_finding_refs")
    _sorted_unique_tokens(payload["reason_codes"], "reason_codes")
    if payload["decision"] not in {"ACCEPT", "REJECT"}:
        raise ValueError("ManifestAcceptance signed payload decision invalid")


def validate_genesis_governance_signature(
    signature_evidence: Mapping[str, Any],
    *,
    expected_projection: str,
) -> bytes:
    if not isinstance(signature_evidence, Mapping):
        raise ValueError("GenesisGovernanceSignature must be an object")
    _exact_keys(signature_evidence, GOVERNANCE_SIGNATURE_KEYS, "GenesisGovernanceSignature")
    if not verify_sealed_object(signature_evidence):
        raise ValueError("GenesisGovernanceSignature seal invalid")
    if (
        signature_evidence["schema_version"] != GOVERNANCE_SIGNATURE_SCHEMA_VERSION
        or signature_evidence["object_type"] != GOVERNANCE_SIGNATURE_OBJECT_TYPE
    ):
        raise ValueError("GenesisGovernanceSignature schema identity mismatch")
    if expected_projection not in KNOWN_PROJECTIONS:
        raise ValueError("unknown expected governance signature projection")
    if signature_evidence["signature_projection"] != expected_projection:
        raise ValueError("GenesisGovernanceSignature projection mismatch")
    if signature_evidence["signature_algorithm"] != "ED25519":
        raise ValueError("GenesisGovernanceSignature algorithm mismatch")
    payload = signature_evidence["signed_payload"]
    if expected_projection == MANIFEST_ACCEPTANCE_PROJECTION:
        _validate_manifest_acceptance_signed_payload(payload)
    else:
        raise ValueError("Genesis authorization signature projection is not implemented in R6-D1")
    if signature_evidence["signed_payload_sha256"] != content_hash(payload):
        raise ValueError("GenesisGovernanceSignature signed_payload_sha256 mismatch")
    return _strict_b64(signature_evidence["authority_signature_base64"], "authority_signature_base64", 64)


def manifest_acceptance_signing_bytes(acceptance: Mapping[str, Any]) -> bytes:
    payload = manifest_acceptance_signed_payload(acceptance)
    return MANIFEST_ACCEPTANCE_SIGNATURE_DOMAIN + canonical_json(payload)


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
    """Verify ManifestAcceptance owner authenticity from the independent bootstrap root.

    The private key is never an input. The production verifier is constructed from the
    hash-pinned Ed25519 executable; callers cannot supply a replacement verification callback.
    """
    validate_manifest_acceptance_v2_contract(acceptance)
    root_ref = _exact_ref(bootstrap_root, object_type=BOOTSTRAP_OBJECT_TYPE)
    public_key = validate_governance_signature_verifier_contract(
        governance_verifier_contract,
        bootstrap_root=bootstrap_root,
        ed25519_verifier_build_profile=ed25519_verifier_build_profile,
        expected_validator_contract_ref=expected_validator_contract_ref,
    )
    if MANIFEST_ACCEPTANCE_PROJECTION not in governance_verifier_contract["allowed_signature_projections"]:
        raise ValueError("governance verifier contract does not authorize ManifestAcceptance projection")

    if _ref(acceptance["bootstrap_governance_root_ref"], "bootstrap_governance_root_ref") != root_ref:
        raise ValueError("ManifestAcceptance bootstrap root differs from independent root")
    if _ref(acceptance["authority_ref"], "authority_ref") != root_ref:
        raise ValueError("ManifestAcceptance authority_ref must be the independent BootstrapGovernanceRoot")
    if _ref(acceptance["acceptance_rule_ref"], "acceptance_rule_ref") != _ref(
        bootstrap_root["acceptance_rule_ref"], "BootstrapGovernanceRoot.acceptance_rule_ref"
    ):
        raise ValueError("ManifestAcceptance acceptance rule differs from BootstrapGovernanceRoot")

    signature_ref = _exact_ref(signature_evidence, object_type=GOVERNANCE_SIGNATURE_OBJECT_TYPE)
    if _ref(acceptance["signature_ref"], "signature_ref") != signature_ref:
        raise ValueError("ManifestAcceptance signature_ref does not bind supplied governance signature")
    signature = validate_genesis_governance_signature(
        signature_evidence,
        expected_projection=MANIFEST_ACCEPTANCE_PROJECTION,
    )
    expected_payload = manifest_acceptance_signed_payload(acceptance)
    if dict(signature_evidence["signed_payload"]) != expected_payload:
        raise ValueError("ManifestAcceptance governance signature payload mismatch")

    verifier = PinnedEd25519Verifier(
        Path(ed25519_verifier_binary),
        governance_verifier_contract["ed25519_verifier_binary_sha256"],
    )
    signing_bytes = MANIFEST_ACCEPTANCE_SIGNATURE_DOMAIN + canonical_json(expected_payload)
    if verifier(public_key, signing_bytes, signature) is not True:
        raise ValueError("ManifestAcceptance bootstrap Ed25519 signature invalid")
    return signature_ref
