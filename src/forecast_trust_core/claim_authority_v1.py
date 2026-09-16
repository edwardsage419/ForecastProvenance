from __future__ import annotations

from typing import Mapping

from . import claim_authority_contract_gate_v1 as _gate
from . import claim_authority_v1_legacy as _legacy
from .canonical import CanonicalizationError, validate_ref


# Re-export the historical implementation surface. Selected authoritative entry
# points below add exact object-contract checks before delegating.
for _name, _value in vars(_legacy).items():
    if not _name.startswith("__"):
        globals()[_name] = _value


# Expose the narrow contract validators for focused adversarial regression.
_validate_bundle_contract = _gate.validate_bundle_contract
_validate_receipt_contract = _gate.validate_receipt_contract
_validate_ots_contract = _gate.validate_ots_contract
_validate_dvr_contract = _gate.validate_dvr_contract
_validate_strong_contract = _gate.validate_strong_contract


def _sync_legacy_dependencies() -> None:
    # Preserve existing dependency-injection seams used by focused tests.
    _legacy.QualifiedVerifierBackend = globals()["QualifiedVerifierBackend"]
    _legacy.validate_provider_admission_set_authoritatively = globals()[
        "validate_provider_admission_set_authoritatively"
    ]


def recompute_external_existence_claim_authoritatively(subject, **kwargs):
    _gate.validate_wall_inputs(kwargs)
    _sync_legacy_dependencies()
    return _legacy.recompute_external_existence_claim_authoritatively(subject, **kwargs)


def recompute_bitcoin_durability_claim_authoritatively(subject, **kwargs):
    _gate.validate_bitcoin_inputs(kwargs)
    _sync_legacy_dependencies()
    return _legacy.recompute_bitcoin_durability_claim_authoritatively(subject, **kwargs)


def validate_cycle_plan_authoritatively(
    plan,
    *,
    required_slots,
    required_schedule_policy_ref,
    wall_clock_inputs,
):
    _gate.validate_wall_inputs(wall_clock_inputs)
    _sync_legacy_dependencies()
    return _legacy.validate_cycle_plan_authoritatively(
        plan,
        required_slots=required_slots,
        required_schedule_policy_ref=required_schedule_policy_ref,
        wall_clock_inputs=wall_clock_inputs,
    )


def validate_final_genesis_acceptance_authoritatively(
    acceptance,
    *,
    final_evidence_subject_ref,
    wall_clock_inputs,
    bitcoin_inputs,
):
    # Preserve the pre-existing fail-closed ordering: wrong final subject and
    # evidence splicing are rejected before deeper object-contract validation.
    acceptance_ref = _legacy._exact_ref(acceptance, object_type="ManifestAcceptance")
    _legacy._require_ref_equal(final_evidence_subject_ref, acceptance_ref, "final evidence subject")

    wall_bundle = wall_clock_inputs.get("bundle") if isinstance(wall_clock_inputs, Mapping) else None
    bitcoin_bundle = bitcoin_inputs.get("bundle") if isinstance(bitcoin_inputs, Mapping) else None
    if wall_bundle is not None and bitcoin_bundle is not None:
        try:
            wall_ref = _legacy._exact_ref(wall_bundle, object_type="ExternalTimeEvidenceBundle")
            bitcoin_ref = _legacy._exact_ref(bitcoin_bundle, object_type="ExternalTimeEvidenceBundle")
        except (TypeError, ValueError):
            wall_ref = bitcoin_ref = None
        if wall_ref is not None and bitcoin_ref is not None and wall_ref != bitcoin_ref:
            raise ValueError(
                "final acceptance wall-clock and Bitcoin evidence must use the same exact ExternalTimeEvidenceBundle"
            )

    _gate.validate_wall_inputs(wall_clock_inputs)
    _gate.validate_bitcoin_inputs(bitcoin_inputs)
    _sync_legacy_dependencies()
    return _legacy.validate_final_genesis_acceptance_authoritatively(
        acceptance,
        final_evidence_subject_ref=final_evidence_subject_ref,
        wall_clock_inputs=wall_clock_inputs,
        bitcoin_inputs=bitcoin_inputs,
    )


def recompute_pre_outcome_durability_authoritatively(
    primary_subject,
    *,
    bitcoin_inputs,
    durability_record,
    durability_record_wall_clock_inputs,
):
    # Keep the public recomputation seams injectable while enforcing the DVR
    # contract before the derived pre-outcome claim is constructed.
    primary_ref = _legacy._exact_ref(primary_subject)
    _gate.validate_dvr_contract(durability_record)
    dvr_ref = _legacy._exact_ref(durability_record, object_type="DurabilityVerificationRecord")

    bitcoin_fn = globals()["recompute_bitcoin_durability_claim_authoritatively"]
    wall_fn = globals()["recompute_external_existence_claim_authoritatively"]
    bitcoin = bitcoin_fn(primary_subject, **dict(bitcoin_inputs))

    _legacy._require_ref_equal(
        durability_record.get("primary_subject_ref"),
        primary_ref,
        "DVR primary subject",
    )
    _legacy._require_ref_equal(
        durability_record.get("external_time_evidence_bundle_ref"),
        bitcoin.evidence_bundle_ref,
        "DVR primary external-time bundle",
    )
    _legacy._require_ref_equal(
        durability_record.get("ots_proof_ref"),
        bitcoin.proof_artifact_ref,
        "DVR OTS proof",
    )
    _legacy._require_ref_equal(
        durability_record.get("strong_verification_report_ref"),
        _legacy._exact_ref(bitcoin.strong_verification_report),
        "DVR strong verification report",
    )
    barrier = durability_record.get("outcome_information_barrier")
    wall = wall_fn(
        durability_record,
        claim_deadline_utc=str(barrier),
        **dict(durability_record_wall_clock_inputs),
    )
    claim = _legacy.derive_pre_outcome_durability_claim_strict(
        primary_ref,
        bitcoin_durability_claim=bitcoin.bitcoin_durability_claim,
        durability_record_deadline_claim=wall.deadline_existence_claim,
        durability_record_subject_ref=dvr_ref,
        durability_record_bound_subject_ref=durability_record.get("primary_subject_ref"),
        applicable=True,
    )
    return claim, bitcoin, wall


def derive_confirmatory_eligibility_from_evidence(
    forecast,
    *,
    component_specs,
    required_claim_requirements,
    hard_invalidation_reason_codes=(),
):
    # Preserve subject-substitution rejection before authority-input validation.
    for spec in component_specs:
        if not isinstance(spec, Mapping):
            raise ValueError("component spec must be a mapping")
        kind = spec.get("kind")
        required_subject_ref = spec.get("required_subject_ref")
        try:
            validate_ref(required_subject_ref)
        except (CanonicalizationError, TypeError) as exc:
            raise ValueError("component required_subject_ref malformed") from exc
        subject = spec.get("subject")
        if kind in {"wall_clock_deadline", "bitcoin_durability", "pre_outcome_durability", "external_existence"}:
            if _legacy._exact_ref(subject) != dict(required_subject_ref):
                if kind == "wall_clock_deadline":
                    raise ValueError("wall-clock component subject substitution")
                if kind == "bitcoin_durability":
                    raise ValueError("Bitcoin component subject substitution")
                if kind == "pre_outcome_durability":
                    raise ValueError("pre-outcome component subject substitution")
                raise ValueError("external-existence component subject substitution")

        authority_inputs = spec.get("authority_inputs")
        if kind in {"wall_clock_deadline", "external_existence"}:
            _gate.validate_wall_inputs(authority_inputs)
        elif kind == "bitcoin_durability":
            _gate.validate_bitcoin_inputs(authority_inputs)
        elif kind == "pre_outcome_durability":
            if not isinstance(authority_inputs, Mapping):
                raise ValueError("pre-outcome authority inputs must be a mapping")
            _gate.validate_bitcoin_inputs(authority_inputs.get("bitcoin_inputs"))
            _gate.validate_dvr_contract(authority_inputs.get("durability_record"))
            _gate.validate_wall_inputs(authority_inputs.get("durability_record_wall_clock_inputs"))

    _sync_legacy_dependencies()
    return _legacy.derive_confirmatory_eligibility_from_evidence(
        forecast,
        component_specs=component_specs,
        required_claim_requirements=required_claim_requirements,
        hard_invalidation_reason_codes=hard_invalidation_reason_codes,
    )


def validate_persisted_final_acceptance_report_authoritatively(
    persisted_report,
    acceptance,
    *,
    final_evidence_subject_ref,
    wall_clock_inputs,
    bitcoin_inputs,
    trusted_manifest_ref,
):
    _gate.validate_wall_inputs(wall_clock_inputs)
    _gate.validate_bitcoin_inputs(bitcoin_inputs)
    _sync_legacy_dependencies()
    return _legacy.validate_persisted_final_acceptance_report_authoritatively(
        persisted_report,
        acceptance,
        final_evidence_subject_ref=final_evidence_subject_ref,
        wall_clock_inputs=wall_clock_inputs,
        bitcoin_inputs=bitcoin_inputs,
        trusted_manifest_ref=trusted_manifest_ref,
    )


def validate_persisted_cycle_plan_report_authoritatively(
    persisted_report,
    plan,
    *,
    required_slots,
    required_schedule_policy_ref,
    wall_clock_inputs,
    trusted_manifest_ref,
):
    _gate.validate_wall_inputs(wall_clock_inputs)
    _sync_legacy_dependencies()
    return _legacy.validate_persisted_cycle_plan_report_authoritatively(
        persisted_report,
        plan,
        required_slots=required_slots,
        required_schedule_policy_ref=required_schedule_policy_ref,
        wall_clock_inputs=wall_clock_inputs,
        trusted_manifest_ref=trusted_manifest_ref,
    )
