from __future__ import annotations

from typing import Any, Mapping

from .canonical import verify_sealed_object
from .core import Validation, aggregate
from ._checks import check as _check

PROFILE_RECEIPT_FIELDS = (
    "provider_id",
    "operator_identity",
    "host",
    "port",
    "transport",
    "operator_declared_protocol",
    "wire_version_hex",
    "offered_version_hex",
    "wire_profile",
    "require_type",
    "require_srv",
    "root_public_key_base64",
    "packet_profile",
    "transport_profile",
    "nonce_profile",
    "verifier_repository",
    "verifier_tag",
    "verifier_commit",
    "verifier_build_profile_sha256",
)


def validate_production_receipt_profile_binding(
    receipt: Mapping[str, Any],
    *,
    provider_profile: Mapping[str, Any],
    qualification_decision: Mapping[str, Any],
    qualification_state_package: Mapping[str, Any],
) -> Validation:
    checks = []
    if not verify_sealed_object(provider_profile):
        checks.append(_check("production_receipt.profile_seal", False, "INVALID_PROVIDER_PROFILE_SEAL"))
        return aggregate(checks)
    if not verify_sealed_object(qualification_decision):
        checks.append(_check("production_receipt.decision_seal", False, "INVALID_QUALIFICATION_DECISION_SEAL"))
        return aggregate(checks)
    if not verify_sealed_object(qualification_state_package):
        checks.append(_check("production_receipt.state_package_seal", False, "INVALID_QUALIFICATION_STATE_PACKAGE_SEAL"))
        return aggregate(checks)

    profile_ref = {
        "object_id": provider_profile["object_id"],
        "content_sha256": provider_profile["content_sha256"],
    }
    decision_ref = {
        "object_id": qualification_decision["object_id"],
        "content_sha256": qualification_decision["content_sha256"],
    }

    signed_payload = qualification_decision.get("signed_payload", {})
    checks.append(_check(
        "production_receipt.decision_profile_binding",
        signed_payload.get("provider_profile_ref") == profile_ref,
        "QUALIFICATION_DECISION_PROFILE_MISMATCH",
    ))
    checks.append(_check(
        "production_receipt.state_profile_binding",
        qualification_state_package.get("provider_profile_ref") == profile_ref,
        "QUALIFICATION_STATE_PROFILE_MISMATCH",
    ))
    checks.append(_check(
        "production_receipt.state_decision_binding",
        qualification_state_package.get("qualification_decision_ref") == decision_ref,
        "QUALIFICATION_STATE_DECISION_MISMATCH",
    ))
    checks.append(_check(
        "production_receipt.state",
        qualification_state_package.get("qualification_state") == "PRODUCTION_QUALIFIED",
        "PROVIDER_NOT_PRODUCTION_QUALIFIED_AT_EVENT_DEADLINE",
    ))

    for field in PROFILE_RECEIPT_FIELDS:
        checks.append(_check(
            f"production_receipt.profile_field.{field}",
            receipt.get(field) == provider_profile.get(field),
            f"RECEIPT_PROVIDER_PROFILE_{field.upper()}_MISMATCH",
        ))

    checks.append(_check(
        "production_receipt.no_fallback",
        provider_profile.get("no_fallback") is True,
        "PROVIDER_PROFILE_FALLBACK_NOT_PROHIBITED",
    ))
    return aggregate(checks)
