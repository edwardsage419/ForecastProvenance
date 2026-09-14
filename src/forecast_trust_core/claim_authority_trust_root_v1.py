from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .canonical import CanonicalizationError, sorted_refs, validate_ref, verify_sealed_object
from .claim_authority_v1 import (
    BitcoinRecomputation,
    WallClockRecomputation,
    derive_confirmatory_eligibility_from_evidence,
    recompute_bitcoin_durability_claim_authoritatively,
    recompute_external_existence_claim_authoritatively,
    recompute_pre_outcome_durability_authoritatively,
    validate_final_genesis_acceptance_authoritatively,
    validate_persisted_cycle_plan_report_authoritatively,
    validate_persisted_final_acceptance_report_authoritatively,
    validate_cycle_plan_authoritatively,
)
from .core import Validation


WALL_AUTHORITY_OVERRIDE_KEYS = frozenset(
    {
        "quorum_policy_ref",
        "qualification_verifier_contract_ref",
        "validator_contract_ref",
        "expected_validator_contract_ref",
    }
)
BITCOIN_AUTHORITY_OVERRIDE_KEYS = frozenset(
    {
        "validator_contract_ref",
        "expected_validator_contract_ref",
        "expected_strong_verifier_contract_ref",
    }
)


@dataclass(frozen=True)
class TrustedManifestAuthorityContext:
    trusted_manifest_ref: Mapping[str, str]
    validator_contract_ref: Mapping[str, str]
    deadline_receipt_quorum_policy_ref: Mapping[str, str]
    provider_profile_refs: tuple[Mapping[str, str], ...]
    qualification_decision_refs: tuple[Mapping[str, str], ...]
    qualification_verifier_contract_ref: Mapping[str, str]
    strong_bitcoin_verifier_contract_ref: Mapping[str, str]


def _exact_ref(obj: Mapping[str, Any], *, object_type: str | None = None) -> dict[str, str]:
    if not verify_sealed_object(obj):
        raise ValueError("trusted authority input must be a valid sealed object")
    if object_type is not None and obj.get("object_type") != object_type:
        raise ValueError(f"expected sealed object_type {object_type}")
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def _required_ref(manifest: Mapping[str, Any], field: str) -> dict[str, str]:
    value = manifest.get(field)
    try:
        validate_ref(value)
    except (CanonicalizationError, TypeError) as exc:
        raise ValueError(f"TrustedManifest {field} is missing or malformed") from exc
    return dict(value)


def _required_ref_set(manifest: Mapping[str, Any], field: str, *, exact_count: int) -> tuple[Mapping[str, str], ...]:
    value = manifest.get(field)
    if not isinstance(value, list):
        raise ValueError(f"TrustedManifest {field} must be a list")
    try:
        normalized = sorted_refs(value)
    except CanonicalizationError as exc:
        raise ValueError(f"TrustedManifest {field} contains malformed references") from exc
    pairs = [(item["object_id"], item["content_sha256"]) for item in normalized]
    if len(normalized) != exact_count or len(pairs) != len(set(pairs)):
        raise ValueError(f"TrustedManifest {field} must contain exactly {exact_count} unique references")
    if value != normalized:
        raise ValueError(f"TrustedManifest {field} must be deterministically sorted")
    return tuple(normalized)


def derive_trusted_manifest_authority_context(
    trusted_manifest: Mapping[str, Any],
) -> TrustedManifestAuthorityContext:
    """Extract the only admissible claim-authority roots from an exact sealed TrustedManifest."""
    manifest_ref = _exact_ref(trusted_manifest, object_type="TrustedManifest")
    if "status" in trusted_manifest:
        raise ValueError("TrustedManifest may not self-assert acceptance status")
    return TrustedManifestAuthorityContext(
        trusted_manifest_ref=manifest_ref,
        validator_contract_ref=_required_ref(trusted_manifest, "validator_contract_ref"),
        deadline_receipt_quorum_policy_ref=_required_ref(trusted_manifest, "deadline_receipt_quorum_policy_ref"),
        provider_profile_refs=_required_ref_set(trusted_manifest, "provider_profile_refs", exact_count=3),
        qualification_decision_refs=_required_ref_set(trusted_manifest, "qualification_decision_refs", exact_count=3),
        qualification_verifier_contract_ref=_required_ref(trusted_manifest, "qualification_verifier_contract_ref"),
        strong_bitcoin_verifier_contract_ref=_required_ref(trusted_manifest, "strong_bitcoin_verifier_contract_ref"),
    )


def _reject_authority_overrides(inputs: Mapping[str, Any], prohibited: frozenset[str], label: str) -> None:
    overlap = sorted(set(inputs) & prohibited)
    if overlap:
        raise ValueError(f"{label} caller authority override prohibited: {','.join(overlap)}")


def _profile_refs(profiles: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return sorted_refs(_exact_ref(item, object_type="RoughtimeProductionProviderProfile") for item in profiles)


def _package_decision_refs(packages: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    refs: list[Mapping[str, Any]] = []
    for package in packages:
        _exact_ref(package, object_type="RoughtimeProviderQualificationStatePackage")
        decision_ref = package.get("qualification_decision_ref")
        validate_ref(decision_ref)
        refs.append(decision_ref)
    return sorted_refs(refs)


def bind_wall_clock_inputs_to_manifest(
    trusted_manifest: Mapping[str, Any],
    wall_clock_inputs: Mapping[str, Any],
) -> dict[str, Any]:
    context = derive_trusted_manifest_authority_context(trusted_manifest)
    _reject_authority_overrides(wall_clock_inputs, WALL_AUTHORITY_OVERRIDE_KEYS, "wall-clock")
    profiles = wall_clock_inputs.get("provider_profiles")
    packages = wall_clock_inputs.get("qualification_state_packages")
    if not isinstance(profiles, Sequence) or isinstance(profiles, (str, bytes, bytearray)):
        raise ValueError("provider_profiles must be a sequence")
    if not isinstance(packages, Sequence) or isinstance(packages, (str, bytes, bytearray)):
        raise ValueError("qualification_state_packages must be a sequence")
    if _profile_refs(profiles) != list(context.provider_profile_refs):
        raise ValueError("wall-clock ProviderProfile set differs from TrustedManifest")
    if _package_decision_refs(packages) != list(context.qualification_decision_refs):
        raise ValueError("wall-clock QualificationDecision set differs from TrustedManifest")
    bound = dict(wall_clock_inputs)
    bound.update(
        quorum_policy_ref=dict(context.deadline_receipt_quorum_policy_ref),
        qualification_verifier_contract_ref=dict(context.qualification_verifier_contract_ref),
        validator_contract_ref=dict(context.validator_contract_ref),
        expected_validator_contract_ref=dict(context.validator_contract_ref),
    )
    return bound


def bind_bitcoin_inputs_to_manifest(
    trusted_manifest: Mapping[str, Any],
    bitcoin_inputs: Mapping[str, Any],
) -> dict[str, Any]:
    context = derive_trusted_manifest_authority_context(trusted_manifest)
    _reject_authority_overrides(bitcoin_inputs, BITCOIN_AUTHORITY_OVERRIDE_KEYS, "Bitcoin")
    contract = bitcoin_inputs.get("strong_verifier_contract")
    contract_ref = _exact_ref(contract, object_type="StrongBitcoinVerifierContract")
    if contract_ref != dict(context.strong_bitcoin_verifier_contract_ref):
        raise ValueError("StrongBitcoinVerifierContract differs from TrustedManifest")
    bound = dict(bitcoin_inputs)
    bound.update(
        validator_contract_ref=dict(context.validator_contract_ref),
        expected_validator_contract_ref=dict(context.validator_contract_ref),
        expected_strong_verifier_contract_ref=dict(context.strong_bitcoin_verifier_contract_ref),
    )
    return bound


def recompute_external_existence_from_trusted_manifest(
    trusted_manifest: Mapping[str, Any],
    subject: Mapping[str, Any],
    *,
    wall_clock_inputs: Mapping[str, Any],
    claim_deadline_utc: str | None = None,
) -> WallClockRecomputation:
    bound = bind_wall_clock_inputs_to_manifest(trusted_manifest, wall_clock_inputs)
    return recompute_external_existence_claim_authoritatively(
        subject,
        claim_deadline_utc=claim_deadline_utc,
        **bound,
    )


def recompute_bitcoin_durability_from_trusted_manifest(
    trusted_manifest: Mapping[str, Any],
    subject: Mapping[str, Any],
    *,
    bitcoin_inputs: Mapping[str, Any],
) -> BitcoinRecomputation:
    bound = bind_bitcoin_inputs_to_manifest(trusted_manifest, bitcoin_inputs)
    return recompute_bitcoin_durability_claim_authoritatively(subject, **bound)


def validate_cycle_plan_from_trusted_manifest(
    trusted_manifest: Mapping[str, Any],
    plan: Mapping[str, Any],
    *,
    required_slots: Sequence[Mapping[str, Any]],
    required_schedule_policy_ref: Mapping[str, Any],
    wall_clock_inputs: Mapping[str, Any],
) -> tuple[Validation, WallClockRecomputation]:
    bound = bind_wall_clock_inputs_to_manifest(trusted_manifest, wall_clock_inputs)
    return validate_cycle_plan_authoritatively(
        plan,
        required_slots=required_slots,
        required_schedule_policy_ref=required_schedule_policy_ref,
        wall_clock_inputs=bound,
    )


def validate_final_genesis_acceptance_from_trusted_manifest(
    trusted_manifest: Mapping[str, Any],
    acceptance: Mapping[str, Any],
    *,
    final_evidence_subject_ref: Mapping[str, Any],
    wall_clock_inputs: Mapping[str, Any],
    bitcoin_inputs: Mapping[str, Any],
):
    context = derive_trusted_manifest_authority_context(trusted_manifest)
    manifest_ref = dict(context.trusted_manifest_ref)
    if acceptance.get("candidate_manifest_ref") != manifest_ref:
        raise ValueError("ManifestAcceptance does not bind the exact TrustedManifest authority root")
    wall = bind_wall_clock_inputs_to_manifest(trusted_manifest, wall_clock_inputs)
    bitcoin = bind_bitcoin_inputs_to_manifest(trusted_manifest, bitcoin_inputs)
    return validate_final_genesis_acceptance_authoritatively(
        acceptance,
        final_evidence_subject_ref=final_evidence_subject_ref,
        wall_clock_inputs=wall,
        bitcoin_inputs=bitcoin,
    )


def validate_persisted_final_acceptance_report_from_trusted_manifest(
    persisted_report: Mapping[str, Any],
    trusted_manifest: Mapping[str, Any],
    acceptance: Mapping[str, Any],
    *,
    final_evidence_subject_ref: Mapping[str, Any],
    wall_clock_inputs: Mapping[str, Any],
    bitcoin_inputs: Mapping[str, Any],
):
    context = derive_trusted_manifest_authority_context(trusted_manifest)
    if acceptance.get("candidate_manifest_ref") != dict(context.trusted_manifest_ref):
        raise ValueError("ManifestAcceptance does not bind the exact TrustedManifest authority root")
    wall = bind_wall_clock_inputs_to_manifest(trusted_manifest, wall_clock_inputs)
    bitcoin = bind_bitcoin_inputs_to_manifest(trusted_manifest, bitcoin_inputs)
    return validate_persisted_final_acceptance_report_authoritatively(
        persisted_report,
        acceptance,
        final_evidence_subject_ref=final_evidence_subject_ref,
        wall_clock_inputs=wall,
        bitcoin_inputs=bitcoin,
        trusted_manifest_ref=dict(context.trusted_manifest_ref),
    )


def validate_persisted_cycle_plan_report_from_trusted_manifest(
    persisted_report: Mapping[str, Any],
    trusted_manifest: Mapping[str, Any],
    plan: Mapping[str, Any],
    *,
    required_slots: Sequence[Mapping[str, Any]],
    required_schedule_policy_ref: Mapping[str, Any],
    wall_clock_inputs: Mapping[str, Any],
):
    context = derive_trusted_manifest_authority_context(trusted_manifest)
    bound = bind_wall_clock_inputs_to_manifest(trusted_manifest, wall_clock_inputs)
    return validate_persisted_cycle_plan_report_authoritatively(
        persisted_report,
        plan,
        required_slots=required_slots,
        required_schedule_policy_ref=required_schedule_policy_ref,
        wall_clock_inputs=bound,
        trusted_manifest_ref=dict(context.trusted_manifest_ref),
    )


def recompute_pre_outcome_durability_from_trusted_manifest(
    trusted_manifest: Mapping[str, Any],
    primary_subject: Mapping[str, Any],
    *,
    bitcoin_inputs: Mapping[str, Any],
    durability_record: Mapping[str, Any],
    durability_record_wall_clock_inputs: Mapping[str, Any],
):
    bitcoin = bind_bitcoin_inputs_to_manifest(trusted_manifest, bitcoin_inputs)
    wall = bind_wall_clock_inputs_to_manifest(trusted_manifest, durability_record_wall_clock_inputs)
    return recompute_pre_outcome_durability_authoritatively(
        primary_subject,
        bitcoin_inputs=bitcoin,
        durability_record=durability_record,
        durability_record_wall_clock_inputs=wall,
    )


def derive_confirmatory_eligibility_from_trusted_manifest(
    trusted_manifest: Mapping[str, Any],
    forecast: Mapping[str, Any],
    *,
    component_specs: Sequence[Mapping[str, Any]],
    required_claim_requirements: Sequence[Mapping[str, Any]],
    hard_invalidation_reason_codes: Sequence[str] = (),
):
    derive_trusted_manifest_authority_context(trusted_manifest)
    bound_specs: list[dict[str, Any]] = []
    for spec in component_specs:
        item = dict(spec)
        kind = item.get("kind")
        if kind in {"wall_clock_deadline", "external_existence"}:
            item["authority_inputs"] = bind_wall_clock_inputs_to_manifest(
                trusted_manifest, item["authority_inputs"]
            )
        elif kind == "bitcoin_durability":
            item["authority_inputs"] = bind_bitcoin_inputs_to_manifest(
                trusted_manifest, item["authority_inputs"]
            )
        elif kind == "pre_outcome_durability":
            nested = dict(item["authority_inputs"])
            nested["bitcoin_inputs"] = bind_bitcoin_inputs_to_manifest(
                trusted_manifest, nested["bitcoin_inputs"]
            )
            nested["durability_record_wall_clock_inputs"] = bind_wall_clock_inputs_to_manifest(
                trusted_manifest, nested["durability_record_wall_clock_inputs"]
            )
            item["authority_inputs"] = nested
        else:
            raise ValueError("unknown authoritative component kind")
        bound_specs.append(item)
    return derive_confirmatory_eligibility_from_evidence(
        forecast,
        component_specs=bound_specs,
        required_claim_requirements=required_claim_requirements,
        hard_invalidation_reason_codes=hard_invalidation_reason_codes,
    )
