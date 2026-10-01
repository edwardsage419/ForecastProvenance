from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

from .canonical import (
    CanonicalizationError,
    canonical_json,
    content_hash,
    parse_json_strict,
    require_utc_timestamp,
    sorted_refs,
    validate_ref,
    verify_sealed_object,
)
from .core import Validation, aggregate
from ._checks import check as _check, required as _required

CLAIM_TYPES = frozenset({
    "EXTERNAL_EXISTENCE_BOUND_VERIFIED",
    "DEADLINE_EXISTENCE_VERIFIED",
    "BITCOIN_DURABILITY_VERIFIED",
    "PRE_OUTCOME_DURABILITY_VERIFIED",
    "CONFIRMATORY_PROSPECTIVE_ELIGIBLE",
})
CLAIM_STATES = frozenset({"VERIFIED", "FAILED", "UNRESOLVED", "NOT_APPLICABLE"})


def _claim(
    claim_type: str,
    subject_ref: Mapping[str, Any],
    state: str,
    *,
    reason_codes: Sequence[str],
    policy_refs: Sequence[Mapping[str, Any]] = (),
    evidence_refs: Sequence[Mapping[str, Any]] = (),
    verified_upper_bound: str | None = None,
    frozen_deadline: str | None = None,
) -> dict[str, Any]:
    if claim_type not in CLAIM_TYPES:
        raise ValueError("unknown claim type")
    if state not in CLAIM_STATES:
        raise ValueError("unknown claim state")
    validate_ref(subject_ref)
    out: dict[str, Any] = {
        "claim_type": claim_type,
        "subject_ref": dict(subject_ref),
        "state": state,
        "policy_refs": sorted_refs(policy_refs),
        "evidence_refs": sorted_refs(evidence_refs),
        "reason_codes": sorted(set(reason_codes)),
    }
    if verified_upper_bound is not None:
        require_utc_timestamp(verified_upper_bound)
        out["verified_upper_bound"] = verified_upper_bound
    if frozen_deadline is not None:
        require_utc_timestamp(frozen_deadline)
        out["frozen_deadline"] = frozen_deadline
    return out


def derive_external_existence_claim(
    subject_ref: Mapping[str, Any],
    *,
    verified_upper_bound: str | None,
    policy_refs: Sequence[Mapping[str, Any]] = (),
    evidence_refs: Sequence[Mapping[str, Any]] = (),
    verification_failed: bool = False,
) -> dict[str, Any]:
    if verification_failed:
        return _claim(
            "EXTERNAL_EXISTENCE_BOUND_VERIFIED",
            subject_ref,
            "FAILED",
            reason_codes=("EXTERNAL_EXISTENCE_VERIFICATION_FAILED",),
            policy_refs=policy_refs,
            evidence_refs=evidence_refs,
        )
    if verified_upper_bound is None:
        return _claim(
            "EXTERNAL_EXISTENCE_BOUND_VERIFIED",
            subject_ref,
            "UNRESOLVED",
            reason_codes=("EXTERNAL_EXISTENCE_EVIDENCE_UNRESOLVED",),
            policy_refs=policy_refs,
            evidence_refs=evidence_refs,
        )
    require_utc_timestamp(verified_upper_bound)
    return _claim(
        "EXTERNAL_EXISTENCE_BOUND_VERIFIED",
        subject_ref,
        "VERIFIED",
        reason_codes=("EXTERNAL_EXISTENCE_BOUND_VERIFIED",),
        policy_refs=policy_refs,
        evidence_refs=evidence_refs,
        verified_upper_bound=verified_upper_bound,
    )


def derive_deadline_existence_claim(
    subject_ref: Mapping[str, Any],
    *,
    external_existence_claim: Mapping[str, Any],
    frozen_deadline: str | None,
) -> dict[str, Any]:
    if frozen_deadline is None:
        return _claim(
            "DEADLINE_EXISTENCE_VERIFIED",
            subject_ref,
            "NOT_APPLICABLE",
            reason_codes=("NO_FROZEN_DEADLINE",),
        )
    require_utc_timestamp(frozen_deadline)
    base_state = external_existence_claim.get("state")
    if base_state == "FAILED":
        state, reason = "FAILED", "BASE_EXISTENCE_VERIFICATION_FAILED"
    elif base_state != "VERIFIED":
        state, reason = "UNRESOLVED", "BASE_EXISTENCE_UNRESOLVED"
    else:
        upper = external_existence_claim.get("verified_upper_bound")
        require_utc_timestamp(upper)
        if upper <= frozen_deadline:
            state, reason = "VERIFIED", "EXISTED_BY_FROZEN_DEADLINE"
        else:
            state, reason = "FAILED", "VERIFIED_EXISTENCE_AFTER_FROZEN_DEADLINE"
    return _claim(
        "DEADLINE_EXISTENCE_VERIFIED",
        subject_ref,
        state,
        reason_codes=(reason,),
        frozen_deadline=frozen_deadline,
        verified_upper_bound=(external_existence_claim.get("verified_upper_bound") if base_state == "VERIFIED" else None),
    )


def derive_bitcoin_durability_claim(
    subject_ref: Mapping[str, Any],
    *,
    bundle_subject_ref: Mapping[str, Any] | None,
    ots_bundle_binding_verified: bool | None,
    strong_bitcoin_verification_passed: bool | None,
    evidence_refs: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    validate_ref(subject_ref)
    if bundle_subject_ref is not None:
        validate_ref(bundle_subject_ref)
    exact = dict(subject_ref)
    if bundle_subject_ref is not None and dict(bundle_subject_ref) != exact:
        state, reason = "FAILED", "EXTERNAL_TIME_BUNDLE_SUBJECT_MISMATCH"
    elif ots_bundle_binding_verified is False:
        state, reason = "FAILED", "OTS_BUNDLE_BINDING_FAILED"
    elif strong_bitcoin_verification_passed is False:
        state, reason = "FAILED", "STRONG_BITCOIN_VERIFICATION_FAILED"
    elif ots_bundle_binding_verified is None or strong_bitcoin_verification_passed is None:
        state, reason = "UNRESOLVED", "BITCOIN_DURABILITY_EVIDENCE_PENDING"
    else:
        state, reason = "VERIFIED", "BITCOIN_DURABILITY_VERIFIED"
    return _claim(
        "BITCOIN_DURABILITY_VERIFIED",
        subject_ref,
        state,
        reason_codes=(reason,),
        evidence_refs=evidence_refs,
    )


def derive_pre_outcome_durability_claim(
    subject_ref: Mapping[str, Any],
    *,
    bitcoin_durability_claim: Mapping[str, Any],
    durability_record_deadline_claim: Mapping[str, Any] | None,
    applicable: bool = True,
) -> dict[str, Any]:
    if not applicable:
        return _claim(
            "PRE_OUTCOME_DURABILITY_VERIFIED",
            subject_ref,
            "NOT_APPLICABLE",
            reason_codes=("NO_OUTCOME_INFORMATION_BARRIER",),
        )
    bitcoin_state = bitcoin_durability_claim.get("state")
    deadline_state = None if durability_record_deadline_claim is None else durability_record_deadline_claim.get("state")
    if bitcoin_state == "FAILED" or deadline_state == "FAILED":
        state, reason = "FAILED", "DURABILITY_OR_PRE_OUTCOME_DEADLINE_FAILED"
    elif bitcoin_state != "VERIFIED" or deadline_state != "VERIFIED":
        state, reason = "UNRESOLVED", "PRE_OUTCOME_DURABILITY_UNRESOLVED"
    else:
        state, reason = "VERIFIED", "DURABILITY_VERIFIED_BEFORE_OUTCOME_BARRIER"
    return _claim(
        "PRE_OUTCOME_DURABILITY_VERIFIED",
        subject_ref,
        state,
        reason_codes=(reason,),
    )


def derive_confirmatory_eligibility(
    subject_ref: Mapping[str, Any],
    *,
    required_claims: Sequence[Mapping[str, Any]],
    hard_invalidation_reason_codes: Sequence[str] = (),
    applicable: bool = True,
) -> dict[str, Any]:
    if not applicable:
        return _claim(
            "CONFIRMATORY_PROSPECTIVE_ELIGIBLE",
            subject_ref,
            "NOT_APPLICABLE",
            reason_codes=("SCIENTIFIC_ELIGIBILITY_NOT_APPLICABLE",),
        )
    if hard_invalidation_reason_codes:
        return _claim(
            "CONFIRMATORY_PROSPECTIVE_ELIGIBLE",
            subject_ref,
            "FAILED",
            reason_codes=tuple(hard_invalidation_reason_codes),
        )
    required_states = [item.get("state") for item in required_claims]
    if any(state in {"FAILED", "NOT_APPLICABLE"} for state in required_states):
        state, reason = "FAILED", "REQUIRED_TRUST_CLAIM_NOT_VERIFIED"
    elif any(state != "VERIFIED" for state in required_states):
        state, reason = "UNRESOLVED", "REQUIRED_TRUST_CLAIM_UNRESOLVED"
    else:
        state, reason = "VERIFIED", "ALL_REQUIRED_CONFIRMATORY_CLAIMS_VERIFIED"
    return _claim(
        "CONFIRMATORY_PROSPECTIVE_ELIGIBLE",
        subject_ref,
        state,
        reason_codes=(reason,),
    )


def validate_derived_claim_vector(claims: Sequence[Mapping[str, Any]]) -> Validation:
    checks = []
    ordering = []
    for index, claim in enumerate(claims):
        claim_type = claim.get("claim_type")
        state = claim.get("state")
        checks.append(_check(f"derived_claims[{index}].type", claim_type in CLAIM_TYPES, "UNKNOWN_CLAIM_TYPE"))
        checks.append(_check(f"derived_claims[{index}].state", state in CLAIM_STATES, "UNKNOWN_CLAIM_STATE"))
        try:
            validate_ref(claim.get("subject_ref"))
            ordering.append((claim_type, claim["subject_ref"]["object_id"], claim["subject_ref"]["content_sha256"]))
        except (CanonicalizationError, TypeError, KeyError):
            checks.append(_check(f"derived_claims[{index}].subject", False, "MALFORMED_CLAIM_SUBJECT_REF"))
    checks.append(_check("derived_claims.order", ordering == sorted(ordering), "UNSORTED_DERIVED_CLAIMS"))
    checks.append(_check("derived_claims.unique", len(ordering) == len(set(ordering)), "DUPLICATE_DERIVED_CLAIM"))
    return aggregate(checks)


def validate_manifest_acceptance_v2(
    manifest: Mapping[str, Any],
    acceptance: Mapping[str, Any],
    *,
    bootstrap_root_ref: Mapping[str, Any],
    acceptance_rule_ref: Mapping[str, Any],
    required_validation_report_refs: Sequence[Mapping[str, Any]],
) -> Validation:
    if not verify_sealed_object(manifest) or not verify_sealed_object(acceptance):
        return aggregate([_check("acceptance_v2.seals", False, "INVALID_SEAL")])
    checks = _required(
        acceptance,
        (
            "candidate_manifest_ref",
            "bootstrap_governance_root_ref",
            "acceptance_rule_ref",
            "required_validation_report_refs",
            "authority_ref",
            "decision",
            "reason_codes",
            "blocking_finding_refs",
            "signature_ref",
        ),
        "acceptance_v2",
    )
    checks.append(_check("acceptance_v2.no_final_evidence_self_ref", "external_anchor_evidence_ref" not in acceptance and "final_external_evidence_ref" not in acceptance, "FINAL_EVIDENCE_SELF_REFERENCE_PROHIBITED"))
    exact_manifest = {"object_id": manifest["object_id"], "content_sha256": manifest["content_sha256"]}
    checks.append(_check("acceptance_v2.manifest", acceptance.get("candidate_manifest_ref") == exact_manifest, "MANIFEST_HASH_MISMATCH"))
    checks.append(_check("acceptance_v2.bootstrap", acceptance.get("bootstrap_governance_root_ref") == bootstrap_root_ref, "BOOTSTRAP_ROOT_MISMATCH"))
    checks.append(_check("acceptance_v2.rule", acceptance.get("acceptance_rule_ref") == acceptance_rule_ref, "ACCEPTANCE_RULE_MISMATCH"))
    try:
        expected_reports = sorted_refs(required_validation_report_refs)
        actual_reports = sorted_refs(acceptance.get("required_validation_report_refs", []))
        checks.append(_check("acceptance_v2.reports", actual_reports == expected_reports, "VALIDATION_REPORT_SET_MISMATCH"))
    except CanonicalizationError:
        checks.append(_check("acceptance_v2.reports", False, "MALFORMED_VALIDATION_REPORT_REF"))
    checks.append(_check("acceptance_v2.decision", acceptance.get("decision") == "ACCEPT", "MANIFEST_NOT_ACCEPTED"))
    blocking = acceptance.get("blocking_finding_refs")
    checks.append(_check("acceptance_v2.blocking", isinstance(blocking, list) and len(blocking) == 0, "BLOCKING_FINDINGS_PRESENT"))
    return aggregate(checks)


def validate_final_genesis_acceptance(
    acceptance: Mapping[str, Any],
    *,
    final_evidence_subject_ref: Mapping[str, Any],
    external_existence_state: str,
    bitcoin_durability_state: str,
) -> Validation:
    if not verify_sealed_object(acceptance):
        return aggregate([_check("final_acceptance.seal", False, "INVALID_ACCEPTANCE_SEAL")])
    exact = {"object_id": acceptance["object_id"], "content_sha256": acceptance["content_sha256"]}
    checks = [
        _check("final_acceptance.subject", final_evidence_subject_ref == exact, "FINAL_EVIDENCE_SUBJECT_MISMATCH"),
        _check("final_acceptance.existence", external_existence_state == "VERIFIED", "FINAL_ACCEPTANCE_EXISTENCE_NOT_VERIFIED"),
        _check("final_acceptance.bitcoin", bitcoin_durability_state == "VERIFIED", "FINAL_ACCEPTANCE_DURABILITY_NOT_VERIFIED"),
    ]
    return aggregate(checks)


def _object_ref(obj: Mapping[str, Any]) -> dict[str, str]:
    if not verify_sealed_object(obj):
        raise ValueError("cannot reference invalid sealed state object")
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def collect_qualification_state_objects(
    record_root: Path,
    *,
    provider_id: str,
    as_of_utc: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    require_utc_timestamp(as_of_utc)
    root = Path(record_root).resolve()
    if not root.is_dir():
        raise ValueError("qualification record root must be a directory")
    metadata: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    seen_refs: set[tuple[str, str]] = set()
    for path in sorted(root.rglob("*.json"), key=lambda p: p.relative_to(root).as_posix()):
        if path.is_symlink() or not path.is_file():
            raise ValueError("qualification state record must be regular non-symlink JSON")
        try:
            value = parse_json_strict(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, CanonicalizationError):
            continue
        if not isinstance(value, dict) or value.get("provider_id") != provider_id:
            continue
        obj_type = value.get("object_type")
        if obj_type == "RoughtimeProviderMetadataReview":
            event_time = value.get("reviewed_at")
            if isinstance(event_time, str) and event_time <= as_of_utc:
                target = metadata
            else:
                continue
        elif obj_type == "RoughtimeRequalificationEvent":
            event_time = value.get("detected_at")
            if isinstance(event_time, str) and event_time <= as_of_utc:
                target = events
            else:
                continue
        else:
            continue
        ref = _object_ref(value)
        pair = (ref["object_id"], ref["content_sha256"])
        if pair in seen_refs:
            raise ValueError("duplicate qualification state object reference")
        seen_refs.add(pair)
        target.append(value)
    metadata.sort(key=lambda item: (item["reviewed_at"], item["object_id"], item["content_sha256"]))
    events.sort(key=lambda item: (item["detected_at"], item["object_id"], item["content_sha256"]))
    return metadata, events


def validate_qualification_state_package(
    package: Mapping[str, Any],
    *,
    record_root: Path,
) -> Validation:
    if not verify_sealed_object(package):
        return aggregate([_check("qualification_state_package.seal", False, "INVALID_SEAL")])
    checks = _required(
        package,
        (
            "provider_id",
            "as_of_utc",
            "provider_profile_ref",
            "qualification_decision_ref",
            "qualification_evidence_manifest_sha256",
            "qualification_verifier_contract_ref",
            "metadata_review_refs",
            "requalification_event_refs",
            "qualification_state_report_sha256",
            "qualification_state",
        ),
        "qualification_state_package",
    )
    try:
        metadata, events = collect_qualification_state_objects(
            record_root,
            provider_id=package["provider_id"],
            as_of_utc=package["as_of_utc"],
        )
        expected_metadata = sorted_refs(_object_ref(item) for item in metadata)
        expected_events = sorted_refs(_object_ref(item) for item in events)
        actual_metadata = sorted_refs(package.get("metadata_review_refs", []))
        actual_events = sorted_refs(package.get("requalification_event_refs", []))
        checks.append(_check("qualification_state_package.metadata_complete", actual_metadata == expected_metadata, "INCOMPLETE_METADATA_REVIEW_SET"))
        checks.append(_check("qualification_state_package.events_complete", actual_events == expected_events, "INCOMPLETE_REQUALIFICATION_EVENT_SET"))
    except (ValueError, CanonicalizationError, KeyError, TypeError):
        checks.append(_check("qualification_state_package.collection", False, "STATE_PACKAGE_COLLECTION_FAILED"))
    checks.append(_check("qualification_state_package.state", package.get("qualification_state") in {"PRODUCTION_QUALIFIED", "QUALIFICATION_EXPIRED", "REQUALIFICATION_REQUIRED", "QUALIFICATION_BLOCKED", "QUALIFICATION_REVIEW_READY", "REHEARSAL_VERIFIED", "UNREVIEWED"}, "UNKNOWN_QUALIFICATION_STATE"))
    return aggregate(checks)


def validate_provider_admission_set(
    packages: Sequence[Mapping[str, Any]],
    *,
    frozen_deadline_utc: str,
    admitted_provider_profile_refs: Sequence[Mapping[str, Any]],
    admitted_qualification_decision_refs: Sequence[Mapping[str, Any]],
) -> Validation:
    require_utc_timestamp(frozen_deadline_utc)
    checks = []
    checks.append(_check("provider_admission.cardinality", len(packages) == 3, "GENESIS_PROVIDER_SET_MUST_HAVE_THREE_MEMBERS"))
    try:
        profiles = sorted_refs(admitted_provider_profile_refs)
        decisions = sorted_refs(admitted_qualification_decision_refs)
    except CanonicalizationError:
        return aggregate(checks + [_check("provider_admission.manifest_refs", False, "MALFORMED_PROVIDER_ADMISSION_REF")])
    actual_profiles = []
    actual_decisions = []
    provider_ids = []
    for index, package in enumerate(packages):
        checks.append(_check(f"provider_admission[{index}].deadline", package.get("as_of_utc") == frozen_deadline_utc, "QUALIFICATION_STATE_AS_OF_MISMATCH"))
        checks.append(_check(f"provider_admission[{index}].state", package.get("qualification_state") == "PRODUCTION_QUALIFIED", "PROVIDER_NOT_PRODUCTION_QUALIFIED_AT_DEADLINE"))
        provider_ids.append(package.get("provider_id"))
        if isinstance(package.get("provider_profile_ref"), Mapping):
            actual_profiles.append(package["provider_profile_ref"])
        if isinstance(package.get("qualification_decision_ref"), Mapping):
            actual_decisions.append(package["qualification_decision_ref"])
    checks.append(_check("provider_admission.unique_provider_ids", len(provider_ids) == len(set(provider_ids)) == 3, "DUPLICATE_OR_MISSING_PROVIDER_ID"))
    try:
        checks.append(_check("provider_admission.profile_set", sorted_refs(actual_profiles) == profiles, "PROVIDER_PROFILE_SET_MISMATCH"))
        checks.append(_check("provider_admission.decision_set", sorted_refs(actual_decisions) == decisions, "QUALIFICATION_DECISION_SET_MISMATCH"))
    except CanonicalizationError:
        checks.append(_check("provider_admission.ref_set", False, "MALFORMED_PROVIDER_ADMISSION_REF"))
    return aggregate(checks)


def qualification_state_package_digest(package: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(package)).hexdigest()
