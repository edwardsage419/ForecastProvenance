from __future__ import annotations

from typing import Any, Mapping

from .canonical import verify_sealed_object
from .claim_authority_contract_gate_v1 import validate_receipt_contract
from .core import Validation, aggregate
from ._checks import check as _check


def _exact_ref(obj: Mapping[str, Any]) -> dict[str, str]:
    if not verify_sealed_object(obj):
        raise ValueError("object seal invalid")
    return {
        "object_id": obj["object_id"],
        "content_sha256": obj["content_sha256"],
    }


def _receipt_contract_valid(receipt: Mapping[str, Any]) -> bool:
    try:
        validate_receipt_contract(receipt)
    except (TypeError, ValueError):
        return False
    return True


def validate_production_receipt_profile_binding(
    receipt: Mapping[str, Any],
    *,
    provider_profile: Mapping[str, Any],
    qualification_decision: Mapping[str, Any],
    qualification_state_package: Mapping[str, Any],
) -> Validation:
    checks = []
    if not _receipt_contract_valid(receipt):
        checks.append(
            _check(
                "production_receipt.receipt_contract",
                False,
                "INVALID_PRODUCTION_RECEIPT_CONTRACT",
            )
        )
        return aggregate(checks)
    if not verify_sealed_object(provider_profile):
        checks.append(_check("production_receipt.profile_seal", False, "INVALID_PROVIDER_PROFILE_SEAL"))
        return aggregate(checks)
    if not verify_sealed_object(qualification_decision):
        checks.append(_check("production_receipt.decision_seal", False, "INVALID_QUALIFICATION_DECISION_SEAL"))
        return aggregate(checks)
    if not verify_sealed_object(qualification_state_package):
        checks.append(_check("production_receipt.state_package_seal", False, "INVALID_QUALIFICATION_STATE_PACKAGE_SEAL"))
        return aggregate(checks)

    try:
        profile_ref = _exact_ref(provider_profile)
        decision_ref = _exact_ref(qualification_decision)
        state_package_ref = _exact_ref(qualification_state_package)
    except (KeyError, TypeError, ValueError):
        checks.append(_check("production_receipt.authority_refs", False, "INVALID_PRODUCTION_RECEIPT_AUTHORITY_REF"))
        return aggregate(checks)

    signed_payload = qualification_decision.get("signed_payload", {})
    checks.append(_check(
        "production_receipt.decision_profile_binding",
        isinstance(signed_payload, Mapping) and signed_payload.get("provider_profile_ref") == profile_ref,
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
    checks.append(_check(
        "production_receipt.provider_profile_ref",
        receipt.get("provider_profile_ref") == profile_ref,
        "RECEIPT_PROVIDER_PROFILE_REF_MISMATCH",
    ))
    checks.append(_check(
        "production_receipt.qualification_state_package_ref",
        receipt.get("qualification_state_package_ref") == state_package_ref,
        "RECEIPT_QUALIFICATION_STATE_PACKAGE_REF_MISMATCH",
    ))
    checks.append(_check(
        "production_receipt.provider_identity",
        receipt.get("provider_id") == provider_profile.get("provider_id")
        and receipt.get("provider_id") == qualification_state_package.get("provider_id"),
        "RECEIPT_PROVIDER_IDENTITY_MISMATCH",
    ))
    checks.append(_check(
        "production_receipt.verifier_build_profile",
        receipt.get("verifier_build_profile_sha256")
        == provider_profile.get("verifier_build_profile_sha256"),
        "RECEIPT_VERIFIER_BUILD_PROFILE_MISMATCH",
    ))
    checks.append(_check(
        "production_receipt.no_fallback",
        provider_profile.get("no_fallback") is True,
        "PROVIDER_PROFILE_FALLBACK_NOT_PROHIBITED",
    ))
    return aggregate(checks)
