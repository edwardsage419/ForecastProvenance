from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from ._ed25519_qualification import validate_build_profile as validate_ed25519_build_profile
from ._ed25519_verifier import PinnedEd25519Verifier
from ._roughtime_production_qualification import (
    CRITERIA_ID,
    CRITERIA_SHA256,
    DECISION_SIGNATURE_PROJECTION,
)
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
PROVIDER_AUTHORITY_OVERRIDE_KEYS = frozenset(
    {
        "expected_authority_id",
        "expected_authority_public_key",
        "signature_verifier",
    }
)
QUALIFICATION_VERIFIER_CONTRACT_KEYS = frozenset(
    {
        "schema_version",
        "object_type",
        "criteria_id",
        "criteria_sha256",
        "validator_contract_ref",
        "decision_signature_projection",
        "signature_algorithm",
        "authority_id",
        "authority_public_key_sha256",
        "ed25519_verifier_build_profile_sha256",
        "ed25519_verifier_binary_sha256",
        "object_id",
        "payload_sha256",
        "content_sha256",
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


def _required_ref_set(
    manifest: Mapping[str, Any],
    field: str,
    *,
    exact_count: int,
) -> tuple[Mapping[str, str], ...]:
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
        deadline_receipt_quorum_policy_ref=_required_ref(
            trusted_manifest, "deadline_receipt_quorum_policy_ref"
        ),
        provider_profile_refs=_required_ref_set(
            trusted_manifest, "provider_profile_refs", exact_count=3
        ),
        qualification_decision_refs=_required_ref_set(
            trusted_manifest, "qualification_decision_refs", exact_count=3
        ),
        qualification_verifier_contract_ref=_required_ref(
            trusted_manifest, "qualification_verifier_contract_ref"
        ),
        strong_bitcoin_verifier_contract_ref=_required_ref(
            trusted_manifest, "strong_bitcoin_verifier_contract_ref"
        ),
    )


def _reject_authority_overrides(
    inputs: Mapping[str, Any], prohibited: frozenset[str], label: str
) -> None:
    overlap = sorted(set(inputs) & prohibited)
    if overlap:
        raise ValueError(
            f"{label} caller authority override prohibited: {','.join(overlap)}"
        )


def _profile_refs(profiles: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return sorted_refs(
        _exact_ref(item, object_type="RoughtimeProductionProviderProfile")
        for item in profiles
    )


def _package_decision_refs(packages: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    refs: list[Mapping[str, Any]] = []
    for package in packages:
        _exact_ref(package, object_type="RoughtimeProviderQualificationStatePackage")
        decision_ref = package.get("qualification_decision_ref")
        validate_ref(decision_ref)
        refs.append(decision_ref)
    return sorted_refs(refs)


def _provider_id_set(
    profiles: Sequence[Mapping[str, Any]],
    packages: Sequence[Mapping[str, Any]],
) -> frozenset[str]:
    profile_ids = [item.get("provider_id") for item in profiles]
    package_ids = [item.get("provider_id") for item in packages]
    if any(not isinstance(item, str) or not item for item in profile_ids + package_ids):
        raise ValueError("provider identity set contains a missing or invalid provider_id")
    profile_set = frozenset(profile_ids)
    package_set = frozenset(package_ids)
    if len(profile_ids) != 3 or len(profile_set) != 3:
        raise ValueError("ProviderProfile set must contain exactly three unique provider identities")
    if len(package_ids) != 3 or len(package_set) != 3:
        raise ValueError("qualification state package set must contain exactly three unique provider identities")
    if profile_set != package_set:
        raise ValueError("qualification state package provider identities differ from ProviderProfiles")
    return profile_set


def _hex64(value: Any, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        raise ValueError(f"{field} must be 64 lowercase hex characters")
    return value


def _validate_qualification_verifier_contract(
    context: TrustedManifestAuthorityContext,
    contract: Mapping[str, Any],
    *,
    authority_id: str | None,
    authority_public_key: bytes | None,
    ed25519_build_profile: Mapping[str, Any],
    ed25519_binary: Path,
) -> PinnedEd25519Verifier:
    contract_ref = _exact_ref(contract, object_type="RoughtimeQualificationVerifierContract")
    if contract_ref != dict(context.qualification_verifier_contract_ref):
        raise ValueError("qualification verifier contract differs from TrustedManifest")
    if set(contract) != QUALIFICATION_VERIFIER_CONTRACT_KEYS:
        raise ValueError("qualification verifier contract fields invalid")
    if contract["schema_version"] != "1.0":
        raise ValueError("qualification verifier contract schema_version mismatch")
    if contract["criteria_id"] != CRITERIA_ID or contract["criteria_sha256"] != CRITERIA_SHA256:
        raise ValueError("qualification verifier contract criteria binding mismatch")
    if contract["validator_contract_ref"] != dict(context.validator_contract_ref):
        raise ValueError("qualification verifier contract ValidatorContract mismatch")
    if contract["decision_signature_projection"] != DECISION_SIGNATURE_PROJECTION:
        raise ValueError("qualification verifier contract decision signature projection mismatch")
    if contract["signature_algorithm"] != "ED25519":
        raise ValueError("qualification verifier contract signature algorithm mismatch")
    if not isinstance(authority_id, str) or not authority_id:
        raise ValueError("external qualification authority_id must be nonempty")
    if contract["authority_id"] != authority_id:
        raise ValueError("external qualification authority_id differs from frozen contract")
    if not isinstance(authority_public_key, bytes) or len(authority_public_key) != 32:
        raise ValueError("external qualification authority public key must be 32 bytes")
    public_key_sha256 = hashlib.sha256(authority_public_key).hexdigest()
    if contract["authority_public_key_sha256"] != public_key_sha256:
        raise ValueError("external qualification authority public key differs from frozen contract")

    profile_sha256 = validate_ed25519_build_profile(ed25519_build_profile)
    if contract["ed25519_verifier_build_profile_sha256"] != profile_sha256:
        raise ValueError("qualification Ed25519 verifier build profile mismatch")
    binary_sha256 = _hex64(ed25519_build_profile["binary_sha256"], "binary_sha256")
    if contract["ed25519_verifier_binary_sha256"] != binary_sha256:
        raise ValueError("qualification Ed25519 verifier binary binding mismatch")
    return PinnedEd25519Verifier(Path(ed25519_binary), binary_sha256)


def _bind_provider_authority_inputs(
    provider_authority_inputs: Mapping[str, Mapping[str, Any]],
    *,
    expected_provider_ids: frozenset[str],
    authority_id: str,
    authority_public_key: bytes,
    signature_verifier: PinnedEd25519Verifier,
) -> dict[str, dict[str, Any]]:
    if not isinstance(provider_authority_inputs, Mapping):
        raise ValueError("provider_authority_inputs must be a mapping")
    if frozenset(provider_authority_inputs) != expected_provider_ids:
        raise ValueError("provider_authority_inputs must exactly match the admitted provider identity set")
    bound: dict[str, dict[str, Any]] = {}
    for provider_id, raw in provider_authority_inputs.items():
        if not isinstance(provider_id, str) or not provider_id:
            raise ValueError("provider authority input key must be a nonempty provider_id")
        if not isinstance(raw, Mapping):
            raise ValueError("provider authority input must be a mapping")
        _reject_authority_overrides(
            raw, PROVIDER_AUTHORITY_OVERRIDE_KEYS, f"provider {provider_id}"
        )
        item = dict(raw)
        item.update(
            expected_authority_id=authority_id,
            expected_authority_public_key=authority_public_key,
            signature_verifier=signature_verifier,
        )
        bound[provider_id] = item
    return bound


def bind_wall_clock_inputs_to_manifest(
    trusted_manifest: Mapping[str, Any],
    wall_clock_inputs: Mapping[str, Any],
    *,
    qualification_authority_id: str | None = None,
    qualification_authority_public_key: bytes | None = None,
) -> dict[str, Any]:
    context = derive_trusted_manifest_authority_context(trusted_manifest)
    _reject_authority_overrides(
        wall_clock_inputs, WALL_AUTHORITY_OVERRIDE_KEYS, "wall-clock"
    )
    profiles = wall_clock_inputs.get("provider_profiles")
    packages = wall_clock_inputs.get("qualification_state_packages")
    if not isinstance(profiles, Sequence) or isinstance(
        profiles, (str, bytes, bytearray)
    ):
        raise ValueError("provider_profiles must be a sequence")
    if not isinstance(packages, Sequence) or isinstance(
        packages, (str, bytes, bytearray)
    ):
        raise ValueError("qualification_state_packages must be a sequence")
    if _profile_refs(profiles) != list(context.provider_profile_refs):
        raise ValueError("wall-clock ProviderProfile set differs from TrustedManifest")
    if _package_decision_refs(packages) != list(context.qualification_decision_refs):
        raise ValueError("wall-clock QualificationDecision set differs from TrustedManifest")
    expected_provider_ids = _provider_id_set(profiles, packages)

    qualification_contract = wall_clock_inputs.get("qualification_verifier_contract")
    ed25519_build_profile = wall_clock_inputs.get("qualification_ed25519_build_profile")
    ed25519_binary = wall_clock_inputs.get("qualification_ed25519_binary")
    if not isinstance(qualification_contract, Mapping):
        raise ValueError("qualification_verifier_contract object is required")
    if not isinstance(ed25519_build_profile, Mapping):
        raise ValueError("qualification_ed25519_build_profile is required")
    if not isinstance(ed25519_binary, (str, Path)):
        raise ValueError("qualification_ed25519_binary path is required")
    signature_verifier = _validate_qualification_verifier_contract(
        context,
        qualification_contract,
        authority_id=qualification_authority_id,
        authority_public_key=qualification_authority_public_key,
        ed25519_build_profile=ed25519_build_profile,
        ed25519_binary=Path(ed25519_binary),
    )

    raw_provider_inputs = wall_clock_inputs.get("provider_authority_inputs")
    provider_inputs = _bind_provider_authority_inputs(
        raw_provider_inputs,
        expected_provider_ids=expected_provider_ids,
        authority_id=qualification_authority_id,
        authority_public_key=qualification_authority_public_key,
        signature_verifier=signature_verifier,
    )

    bound = dict(wall_clock_inputs)
    bound["provider_authority_inputs"] = provider_inputs
    bound.update(
        quorum_policy_ref=dict(context.deadline_receipt_quorum_policy_ref),
        qualification_verifier_contract_ref=dict(
            context.qualification_verifier_contract_ref
        ),
        validator_contract_ref=dict(context.validator_contract_ref),
        expected_validator_contract_ref=dict(context.validator_contract_ref),
    )
    bound.pop("qualification_verifier_contract", None)
    bound.pop("qualification_ed25519_build_profile", None)
    bound.pop("qualification_ed25519_binary", None)
    return bound


def bind_bitcoin_inputs_to_manifest(
    trusted_manifest: Mapping[str, Any],
    bitcoin_inputs: Mapping[str, Any],
) -> dict[str, Any]:
    context = derive_trusted_manifest_authority_context(trusted_manifest)
    _reject_authority_overrides(
        bitcoin_inputs, BITCOIN_AUTHORITY_OVERRIDE_KEYS, "Bitcoin"
    )
    contract = bitcoin_inputs.get("strong_verifier_contract")
    contract_ref = _exact_ref(contract, object_type="StrongBitcoinVerifierContract")
    if contract_ref != dict(context.strong_bitcoin_verifier_contract_ref):
        raise ValueError("StrongBitcoinVerifierContract differs from TrustedManifest")
    bound = dict(bitcoin_inputs)
    bound.update(
        validator_contract_ref=dict(context.validator_contract_ref),
        expected_validator_contract_ref=dict(context.validator_contract_ref),
        expected_strong_verifier_contract_ref=dict(
            context.strong_bitcoin_verifier_contract_ref
        ),
    )
    return bound


def recompute_external_existence_from_trusted_manifest(
    trusted_manifest: Mapping[str, Any],
    subject: Mapping[str, Any],
    *,
    wall_clock_inputs: Mapping[str, Any],
    qualification_authority_id: str | None = None,
    qualification_authority_public_key: bytes | None = None,
    claim_deadline_utc: str | None = None,
) -> WallClockRecomputation:
    bound = bind_wall_clock_inputs_to_manifest(
        trusted_manifest,
        wall_clock_inputs,
        qualification_authority_id=qualification_authority_id,
        qualification_authority_public_key=qualification_authority_public_key,
    )
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
    qualification_authority_id: str | None = None,
    qualification_authority_public_key: bytes | None = None,
) -> tuple[Validation, WallClockRecomputation]:
    bound = bind_wall_clock_inputs_to_manifest(
        trusted_manifest,
        wall_clock_inputs,
        qualification_authority_id=qualification_authority_id,
        qualification_authority_public_key=qualification_authority_public_key,
    )
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
    qualification_authority_id: str | None = None,
    qualification_authority_public_key: bytes | None = None,
):
    context = derive_trusted_manifest_authority_context(trusted_manifest)
    manifest_ref = dict(context.trusted_manifest_ref)
    if acceptance.get("candidate_manifest_ref") != manifest_ref:
        raise ValueError(
            "ManifestAcceptance does not bind the exact TrustedManifest authority root"
        )
    wall = bind_wall_clock_inputs_to_manifest(
        trusted_manifest,
        wall_clock_inputs,
        qualification_authority_id=qualification_authority_id,
        qualification_authority_public_key=qualification_authority_public_key,
    )
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
    qualification_authority_id: str | None = None,
    qualification_authority_public_key: bytes | None = None,
):
    context = derive_trusted_manifest_authority_context(trusted_manifest)
    if acceptance.get("candidate_manifest_ref") != dict(context.trusted_manifest_ref):
        raise ValueError(
            "ManifestAcceptance does not bind the exact TrustedManifest authority root"
        )
    wall = bind_wall_clock_inputs_to_manifest(
        trusted_manifest,
        wall_clock_inputs,
        qualification_authority_id=qualification_authority_id,
        qualification_authority_public_key=qualification_authority_public_key,
    )
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
    qualification_authority_id: str | None = None,
    qualification_authority_public_key: bytes | None = None,
):
    context = derive_trusted_manifest_authority_context(trusted_manifest)
    bound = bind_wall_clock_inputs_to_manifest(
        trusted_manifest,
        wall_clock_inputs,
        qualification_authority_id=qualification_authority_id,
        qualification_authority_public_key=qualification_authority_public_key,
    )
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
    qualification_authority_id: str | None = None,
    qualification_authority_public_key: bytes | None = None,
):
    bitcoin = bind_bitcoin_inputs_to_manifest(trusted_manifest, bitcoin_inputs)
    wall = bind_wall_clock_inputs_to_manifest(
        trusted_manifest,
        durability_record_wall_clock_inputs,
        qualification_authority_id=qualification_authority_id,
        qualification_authority_public_key=qualification_authority_public_key,
    )
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
    qualification_authority_id: str | None = None,
    qualification_authority_public_key: bytes | None = None,
    hard_invalidation_reason_codes: Sequence[str] = (),
):
    derive_trusted_manifest_authority_context(trusted_manifest)
    bound_specs: list[dict[str, Any]] = []
    for spec in component_specs:
        item = dict(spec)
        kind = item.get("kind")
        if kind in {"wall_clock_deadline", "external_existence"}:
            item["authority_inputs"] = bind_wall_clock_inputs_to_manifest(
                trusted_manifest,
                item["authority_inputs"],
                qualification_authority_id=qualification_authority_id,
                qualification_authority_public_key=qualification_authority_public_key,
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
            nested["durability_record_wall_clock_inputs"] = (
                bind_wall_clock_inputs_to_manifest(
                    trusted_manifest,
                    nested["durability_record_wall_clock_inputs"],
                    qualification_authority_id=qualification_authority_id,
                    qualification_authority_public_key=qualification_authority_public_key,
                )
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
