from __future__ import annotations

from typing import Any, Mapping

from ._checks import check as _check
from .canonical import verify_sealed_object
from .core import Validation, aggregate
from .production_evidence_contracts_v1 import (
    validate_roughtime_production_receipt_contract,
)


def _ref(obj: Mapping[str, Any]) -> dict[str, str]:
    return {
        "object_id": obj["object_id"],
        "content_sha256": obj["content_sha256"],
    }


def _sealed_type_valid(obj: Mapping[str, Any], object_type: str) -> bool:
    return (
        verify_sealed_object(obj)
        and obj.get("schema_version") == "1.0"
        and obj.get("object_type") == object_type
    )


def validate_production_receipt_profile_binding(
    receipt: Mapping[str, Any],
    *,
    provider_profile: Mapping[str, Any],
    qualification_decision: Mapping[str, Any],
    qualification_state_package: Mapping[str, Any],
) -> Validation:
    try:
        validate_roughtime_production_receipt_contract(receipt)
    except (KeyError, TypeError, ValueError):
        return aggregate(
            [
                _check(
                    "production_receipt.contract",
                    False,
                    "INVALID_PRODUCTION_RECEIPT_CONTRACT",
                )
            ]
        )

    if not _sealed_type_valid(provider_profile, "RoughtimeProductionProviderProfile"):
        return aggregate(
            [_check("production_receipt.profile_seal", False, "INVALID_PROVIDER_PROFILE")]
        )
    if not _sealed_type_valid(qualification_decision, "RoughtimeQualificationDecision"):
        return aggregate(
            [_check("production_receipt.decision_seal", False, "INVALID_QUALIFICATION_DECISION")]
        )
    if not _sealed_type_valid(
        qualification_state_package,
        "RoughtimeProviderQualificationStatePackage",
    ):
        return aggregate(
            [
                _check(
                    "production_receipt.state_package_seal",
                    False,
                    "INVALID_QUALIFICATION_STATE_PACKAGE",
                )
            ]
        )

    signed_payload = qualification_decision.get("signed_payload")
    if not isinstance(signed_payload, Mapping):
        return aggregate(
            [
                _check(
                    "production_receipt.decision_payload",
                    False,
                    "INVALID_QUALIFICATION_DECISION_SIGNED_PAYLOAD",
                )
            ]
        )

    profile_ref = _ref(provider_profile)
    decision_ref = _ref(qualification_decision)
    state_package_ref = _ref(qualification_state_package)
    provider_id = receipt.get("provider_id")

    checks = [
        _check(
            "production_receipt.decision_profile_binding",
            signed_payload.get("provider_profile_ref") == profile_ref,
            "QUALIFICATION_DECISION_PROFILE_MISMATCH",
        ),
        _check(
            "production_receipt.decision_provider_binding",
            signed_payload.get("provider_id") == provider_id,
            "QUALIFICATION_DECISION_PROVIDER_MISMATCH",
        ),
        _check(
            "production_receipt.state_profile_binding",
            qualification_state_package.get("provider_profile_ref") == profile_ref,
            "QUALIFICATION_STATE_PROFILE_MISMATCH",
        ),
        _check(
            "production_receipt.state_decision_binding",
            qualification_state_package.get("qualification_decision_ref") == decision_ref,
            "QUALIFICATION_STATE_DECISION_MISMATCH",
        ),
        _check(
            "production_receipt.state",
            qualification_state_package.get("qualification_state") == "PRODUCTION_QUALIFIED",
            "PROVIDER_NOT_PRODUCTION_QUALIFIED_AT_EVENT_DEADLINE",
        ),
        _check(
            "production_receipt.profile_ref",
            receipt.get("provider_profile_ref") == profile_ref,
            "RECEIPT_PROVIDER_PROFILE_REF_MISMATCH",
        ),
        _check(
            "production_receipt.state_package_ref",
            receipt.get("qualification_state_package_ref") == state_package_ref,
            "RECEIPT_QUALIFICATION_STATE_PACKAGE_REF_MISMATCH",
        ),
        _check(
            "production_receipt.profile_provider_identity",
            provider_profile.get("provider_id") == provider_id,
            "RECEIPT_PROVIDER_PROFILE_IDENTITY_MISMATCH",
        ),
        _check(
            "production_receipt.state_provider_identity",
            qualification_state_package.get("provider_id") == provider_id,
            "RECEIPT_QUALIFICATION_STATE_PROVIDER_IDENTITY_MISMATCH",
        ),
        _check(
            "production_receipt.verifier_build_profile",
            receipt.get("verifier_build_profile_sha256")
            == provider_profile.get("verifier_build_profile_sha256"),
            "RECEIPT_VERIFIER_BUILD_PROFILE_MISMATCH",
        ),
        _check(
            "production_receipt.no_fallback",
            provider_profile.get("no_fallback") is True,
            "PROVIDER_PROFILE_FALLBACK_NOT_PROHIBITED",
        ),
    ]
    return aggregate(checks)
