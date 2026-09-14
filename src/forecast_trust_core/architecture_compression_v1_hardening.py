from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

from ._checks import check as _check
from ._roughtime_production_qualification_hardening import (
    derive_authoritative_qualification_state,
)
from .architecture_compression_v1 import (
    CLAIM_STATES,
    CLAIM_TYPES,
    _claim,
    derive_confirmatory_eligibility,
    derive_deadline_existence_claim,
    derive_pre_outcome_durability_claim,
    validate_provider_admission_set,
)
from .canonical import (
    CanonicalizationError,
    canonical_json,
    parse_json_strict,
    require_utc_timestamp,
    sorted_refs,
    validate_ref,
    verify_sealed_object,
)
from .core import Validation, aggregate

COMPONENT_CLAIM_TYPES = CLAIM_TYPES - {"CONFIRMATORY_PROSPECTIVE_ELIGIBLE"}


def _exact_ref(obj: Mapping[str, Any]) -> dict[str, str]:
    if not verify_sealed_object(obj):
        raise ValueError("authoritative input must be a valid sealed object")
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def _claim_matches(
    claim: Mapping[str, Any],
    *,
    claim_type: str,
    subject_ref: Mapping[str, Any],
) -> bool:
    try:
        validate_ref(subject_ref)
        validate_ref(claim.get("subject_ref"))
    except (CanonicalizationError, TypeError):
        return False
    return (
        claim_type in CLAIM_TYPES
        and claim.get("claim_type") == claim_type
        and claim.get("state") in CLAIM_STATES
        and dict(claim["subject_ref"]) == dict(subject_ref)
    )


def derive_deadline_existence_claim_strict(
    subject_ref: Mapping[str, Any],
    *,
    external_existence_claim: Mapping[str, Any],
    frozen_deadline: str | None,
) -> dict[str, Any]:
    """Derive deadline existence only from the matching base claim for the exact subject."""
    if frozen_deadline is None:
        return derive_deadline_existence_claim(
            subject_ref,
            external_existence_claim=external_existence_claim,
            frozen_deadline=None,
        )
    require_utc_timestamp(frozen_deadline)
    if not _claim_matches(
        external_existence_claim,
        claim_type="EXTERNAL_EXISTENCE_BOUND_VERIFIED",
        subject_ref=subject_ref,
    ):
        return _claim(
            "DEADLINE_EXISTENCE_VERIFIED",
            subject_ref,
            "FAILED",
            reason_codes=("EXTERNAL_EXISTENCE_SUBJECT_TYPE_OR_STATE_MISMATCH",),
            frozen_deadline=frozen_deadline,
        )
    return derive_deadline_existence_claim(
        subject_ref,
        external_existence_claim=external_existence_claim,
        frozen_deadline=frozen_deadline,
    )


def derive_pre_outcome_durability_claim_strict(
    primary_subject_ref: Mapping[str, Any],
    *,
    bitcoin_durability_claim: Mapping[str, Any],
    durability_record_deadline_claim: Mapping[str, Any] | None,
    durability_record_subject_ref: Mapping[str, Any] | None,
    durability_record_bound_subject_ref: Mapping[str, Any] | None,
    applicable: bool = True,
) -> dict[str, Any]:
    """Require exact BTC subject plus exact DVR deadline and DVR-to-primary binding."""
    if not applicable:
        return derive_pre_outcome_durability_claim(
            primary_subject_ref,
            bitcoin_durability_claim=bitcoin_durability_claim,
            durability_record_deadline_claim=durability_record_deadline_claim,
            applicable=False,
        )
    try:
        validate_ref(primary_subject_ref)
        if durability_record_subject_ref is None or durability_record_bound_subject_ref is None:
            raise CanonicalizationError("missing DVR binding")
        validate_ref(durability_record_subject_ref)
        validate_ref(durability_record_bound_subject_ref)
    except (CanonicalizationError, TypeError):
        return _claim(
            "PRE_OUTCOME_DURABILITY_VERIFIED",
            primary_subject_ref,
            "FAILED",
            reason_codes=("DURABILITY_RECORD_BINDING_MALFORMED",),
        )
    bitcoin_exact = _claim_matches(
        bitcoin_durability_claim,
        claim_type="BITCOIN_DURABILITY_VERIFIED",
        subject_ref=primary_subject_ref,
    )
    deadline_exact = (
        durability_record_deadline_claim is not None
        and _claim_matches(
            durability_record_deadline_claim,
            claim_type="DEADLINE_EXISTENCE_VERIFIED",
            subject_ref=durability_record_subject_ref,
        )
    )
    record_binding_exact = dict(durability_record_bound_subject_ref) == dict(primary_subject_ref)
    if not bitcoin_exact:
        reason = "BITCOIN_DURABILITY_SUBJECT_TYPE_OR_STATE_MISMATCH"
    elif not deadline_exact:
        reason = "DURABILITY_RECORD_DEADLINE_SUBJECT_TYPE_OR_STATE_MISMATCH"
    elif not record_binding_exact:
        reason = "DURABILITY_RECORD_PRIMARY_SUBJECT_MISMATCH"
    else:
        return derive_pre_outcome_durability_claim(
            primary_subject_ref,
            bitcoin_durability_claim=bitcoin_durability_claim,
            durability_record_deadline_claim=durability_record_deadline_claim,
            applicable=True,
        )
    return _claim(
        "PRE_OUTCOME_DURABILITY_VERIFIED",
        primary_subject_ref,
        "FAILED",
        reason_codes=(reason,),
    )


def derive_confirmatory_eligibility_strict(
    subject_ref: Mapping[str, Any],
    *,
    required_claims: Sequence[Mapping[str, Any]],
    required_claim_requirements: Sequence[Mapping[str, Any]],
    hard_invalidation_reason_codes: Sequence[str] = (),
    applicable: bool = True,
) -> dict[str, Any]:
    """Aggregate only the exact predeclared known claim-type/subject requirement set."""
    if not applicable:
        return derive_confirmatory_eligibility(
            subject_ref,
            required_claims=required_claims,
            hard_invalidation_reason_codes=hard_invalidation_reason_codes,
            applicable=False,
        )
    expected: list[tuple[str, str, str]] = []
    actual: list[tuple[str, str, str]] = []
    try:
        for requirement in required_claim_requirements:
            if set(requirement) != {"claim_type", "subject_ref"}:
                raise CanonicalizationError("malformed claim requirement")
            claim_type = requirement["claim_type"]
            if claim_type not in COMPONENT_CLAIM_TYPES:
                raise CanonicalizationError("unknown or recursive claim requirement")
            validate_ref(requirement["subject_ref"])
            expected.append(
                (
                    str(claim_type),
                    requirement["subject_ref"]["object_id"],
                    requirement["subject_ref"]["content_sha256"],
                )
            )
        for claim in required_claims:
            claim_type = claim.get("claim_type")
            if claim_type not in COMPONENT_CLAIM_TYPES or claim.get("state") not in CLAIM_STATES:
                raise CanonicalizationError("unknown component claim")
            validate_ref(claim.get("subject_ref"))
            actual.append(
                (
                    str(claim_type),
                    claim["subject_ref"]["object_id"],
                    claim["subject_ref"]["content_sha256"],
                )
            )
    except (CanonicalizationError, TypeError, KeyError):
        return _claim(
            "CONFIRMATORY_PROSPECTIVE_ELIGIBLE",
            subject_ref,
            "FAILED",
            reason_codes=("MALFORMED_OR_UNKNOWN_REQUIRED_CLAIM_BINDING",),
        )
    if len(expected) != len(set(expected)):
        return _claim(
            "CONFIRMATORY_PROSPECTIVE_ELIGIBLE",
            subject_ref,
            "FAILED",
            reason_codes=("DUPLICATE_REQUIRED_CLAIM_REQUIREMENT",),
        )
    if len(actual) != len(set(actual)) or sorted(actual) != sorted(expected):
        return _claim(
            "CONFIRMATORY_PROSPECTIVE_ELIGIBLE",
            subject_ref,
            "FAILED",
            reason_codes=("REQUIRED_CLAIM_SET_SUBSTITUTION",),
        )
    return derive_confirmatory_eligibility(
        subject_ref,
        required_claims=required_claims,
        hard_invalidation_reason_codes=hard_invalidation_reason_codes,
        applicable=True,
    )


def collect_qualification_state_objects_strict(
    record_root: Path,
    *,
    provider_id: str,
    as_of_utc: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Scan a dedicated provider-state store fail-closed; no malformed record may disappear."""
    require_utc_timestamp(as_of_utc)
    root = Path(record_root).resolve()
    if not root.is_dir():
        raise ValueError("qualification state record root must be a directory")
    metadata: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    seen_refs: set[tuple[str, str]] = set()
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        if path.is_symlink():
            raise ValueError("qualification state store contains a symlink")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError("qualification state store contains a non-regular file")
        if path.suffix != ".json":
            raise ValueError("qualification state store contains an unexpected non-JSON file")
        try:
            value = parse_json_strict(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, CanonicalizationError) as exc:
            raise ValueError("qualification state store contains malformed JSON") from exc
        if not isinstance(value, dict):
            raise ValueError("qualification state record must be a JSON object")
        if value.get("provider_id") != provider_id:
            raise ValueError("qualification state store contains a different provider")
        if not verify_sealed_object(value):
            raise ValueError("qualification state store contains an invalid sealed object")
        obj_type = value.get("object_type")
        if obj_type == "RoughtimeProviderMetadataReview":
            event_time = value.get("reviewed_at")
            if not isinstance(event_time, str):
                raise ValueError("metadata review missing reviewed_at")
            require_utc_timestamp(event_time)
            target = metadata
        elif obj_type == "RoughtimeRequalificationEvent":
            event_time = value.get("detected_at")
            if not isinstance(event_time, str):
                raise ValueError("requalification event missing detected_at")
            require_utc_timestamp(event_time)
            target = events
        else:
            raise ValueError("qualification state store contains an unexpected object type")
        ref = _exact_ref(value)
        pair = (ref["object_id"], ref["content_sha256"])
        if pair in seen_refs:
            raise ValueError("duplicate qualification state object reference")
        seen_refs.add(pair)
        if event_time <= as_of_utc:
            target.append(value)
    metadata.sort(key=lambda item: (item["reviewed_at"], item["object_id"], item["content_sha256"]))
    events.sort(key=lambda item: (item["detected_at"], item["object_id"], item["content_sha256"]))
    return metadata, events


def validate_qualification_state_package_authoritatively(
    package: Mapping[str, Any],
    *,
    record_root: Path,
    profile: Mapping[str, Any],
    evidence_manifest: Mapping[str, Any],
    evidence_package_root: Path,
    verifier_build_profile: Mapping[str, Any],
    review: Mapping[str, Any],
    decision: Mapping[str, Any],
    qualification_verifier_contract_ref: Mapping[str, Any],
    expected_authority_id: str,
    expected_authority_public_key: bytes,
    signature_verifier,
    rehearsal_verified: bool = True,
    evidence_manifest_relative_path: str = "manifest.json",
) -> Validation:
    """Validate package closure and recompute provider state from authoritative qualification inputs."""
    checks = []
    if not verify_sealed_object(package):
        return aggregate([_check("qualification_state_authority.package_seal", False, "INVALID_STATE_PACKAGE_SEAL")])
    try:
        require_utc_timestamp(package["as_of_utc"])
        validate_ref(qualification_verifier_contract_ref)
        profile_ref = _exact_ref(profile)
        decision_ref = _exact_ref(decision)
        metadata, events = collect_qualification_state_objects_strict(
            record_root,
            provider_id=str(package["provider_id"]),
            as_of_utc=str(package["as_of_utc"]),
        )
        expected_metadata_refs = sorted_refs(_exact_ref(item) for item in metadata)
        expected_event_refs = sorted_refs(_exact_ref(item) for item in events)
        actual_metadata_refs = sorted_refs(package.get("metadata_review_refs", []))
        actual_event_refs = sorted_refs(package.get("requalification_event_refs", []))
    except (ValueError, CanonicalizationError, KeyError, TypeError):
        return aggregate([_check("qualification_state_authority.collection", False, "AUTHORITATIVE_STATE_COLLECTION_FAILED")])

    checks.extend(
        [
            _check("qualification_state_authority.profile", package.get("provider_profile_ref") == profile_ref, "STATE_PACKAGE_PROFILE_MISMATCH"),
            _check("qualification_state_authority.decision", package.get("qualification_decision_ref") == decision_ref, "STATE_PACKAGE_DECISION_MISMATCH"),
            _check("qualification_state_authority.verifier", package.get("qualification_verifier_contract_ref") == qualification_verifier_contract_ref, "STATE_PACKAGE_VERIFIER_CONTRACT_MISMATCH"),
            _check("qualification_state_authority.metadata_complete", actual_metadata_refs == expected_metadata_refs, "INCOMPLETE_METADATA_REVIEW_SET"),
            _check("qualification_state_authority.events_complete", actual_event_refs == expected_event_refs, "INCOMPLETE_REQUALIFICATION_EVENT_SET"),
        ]
    )
    expected_manifest_sha256 = hashlib.sha256(canonical_json(evidence_manifest)).hexdigest()
    checks.append(
        _check(
            "qualification_state_authority.evidence_manifest",
            package.get("qualification_evidence_manifest_sha256") == expected_manifest_sha256,
            "STATE_PACKAGE_EVIDENCE_MANIFEST_MISMATCH",
        )
    )
    if any(check.status == "FAIL" for check in checks):
        return aggregate(checks)

    try:
        authoritative = derive_authoritative_qualification_state(
            provider_id=str(package["provider_id"]),
            as_of_utc=str(package["as_of_utc"]),
            rehearsal_verified=rehearsal_verified,
            profile=profile,
            evidence_manifest=evidence_manifest,
            evidence_package_root=evidence_package_root,
            evidence_manifest_relative_path=evidence_manifest_relative_path,
            verifier_build_profile=verifier_build_profile,
            review=review,
            decision=decision,
            metadata_reviews=metadata,
            requalification_events=events,
            expected_authority_id=expected_authority_id,
            expected_authority_public_key=expected_authority_public_key,
            signature_verifier=signature_verifier,
        )
    except (ValueError, CanonicalizationError, KeyError, TypeError):
        checks.append(_check("qualification_state_authority.recompute", False, "AUTHORITATIVE_QUALIFICATION_STATE_RECOMPUTATION_FAILED"))
        return aggregate(checks)

    checks.extend(
        [
            _check("qualification_state_authority.report_provider", authoritative.get("provider_id") in {None, package.get("provider_id")}, "AUTHORITATIVE_STATE_PROVIDER_MISMATCH"),
            _check("qualification_state_authority.report_as_of", authoritative.get("as_of_utc") in {None, package.get("as_of_utc")}, "AUTHORITATIVE_STATE_AS_OF_MISMATCH"),
            _check("qualification_state_authority.state", package.get("qualification_state") == authoritative.get("state"), "SELF_ASSERTED_QUALIFICATION_STATE_MISMATCH"),
            _check("qualification_state_authority.report", package.get("qualification_state_report_sha256") == authoritative.get("report_sha256"), "QUALIFICATION_STATE_REPORT_HASH_MISMATCH"),
        ]
    )
    return aggregate(checks)


def validate_provider_admission_set_authoritatively(
    packages: Sequence[Mapping[str, Any]],
    *,
    frozen_deadline_utc: str,
    admitted_provider_profile_refs: Sequence[Mapping[str, Any]],
    admitted_qualification_decision_refs: Sequence[Mapping[str, Any]],
    provider_inputs: Mapping[str, Mapping[str, Any]],
    qualification_verifier_contract_ref: Mapping[str, Any],
) -> Validation:
    """Only admit the three-provider set after every package passes authoritative recomputation."""
    checks = []
    for index, package in enumerate(packages):
        provider_id = package.get("provider_id")
        inputs = provider_inputs.get(str(provider_id))
        if inputs is None:
            checks.append(_check(f"provider_admission_authority[{index}]", False, "MISSING_AUTHORITATIVE_PROVIDER_INPUTS"))
            continue
        try:
            result = validate_qualification_state_package_authoritatively(
                package,
                record_root=inputs["record_root"],
                profile=inputs["profile"],
                evidence_manifest=inputs["evidence_manifest"],
                evidence_package_root=inputs["evidence_package_root"],
                verifier_build_profile=inputs["verifier_build_profile"],
                review=inputs["review"],
                decision=inputs["decision"],
                qualification_verifier_contract_ref=qualification_verifier_contract_ref,
                expected_authority_id=inputs["expected_authority_id"],
                expected_authority_public_key=inputs["expected_authority_public_key"],
                signature_verifier=inputs["signature_verifier"],
                rehearsal_verified=bool(inputs.get("rehearsal_verified", True)),
                evidence_manifest_relative_path=str(inputs.get("evidence_manifest_relative_path", "manifest.json")),
            )
        except (KeyError, TypeError, ValueError):
            checks.append(_check(f"provider_admission_authority[{index}]", False, "AUTHORITATIVE_PROVIDER_INPUTS_INVALID"))
            continue
        checks.extend(result.checks)
    if any(check.status != "PASS" for check in checks):
        return aggregate(checks)
    base = validate_provider_admission_set(
        packages,
        frozen_deadline_utc=frozen_deadline_utc,
        admitted_provider_profile_refs=admitted_provider_profile_refs,
        admitted_qualification_decision_refs=admitted_qualification_decision_refs,
    )
    return aggregate(tuple(checks) + base.checks)
