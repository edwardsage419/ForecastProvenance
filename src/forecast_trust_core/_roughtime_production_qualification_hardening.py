from __future__ import annotations

from typing import Any, Mapping, Sequence

from ._roughtime_production_qualification import (
    derive_qualification_state,
    validate_qualification_decision,
    validate_qualification_evidence_manifest,
    validate_qualification_review,
)


def _manifest_binding(
    manifest: Mapping[str, Any],
    *,
    provider_id: str,
    artifact_bytes: Mapping[str, bytes] | None,
) -> tuple[str, frozenset[str]]:
    if artifact_bytes is None:
        raise ValueError("actual evidence artifact bytes are required for manifest closure")
    manifest_sha256 = validate_qualification_evidence_manifest(
        manifest,
        artifact_bytes=artifact_bytes,
    )
    if manifest["provider_id"] != provider_id:
        raise ValueError("evidence manifest provider mismatch")
    artifact_sha256s = frozenset(entry["sha256"] for entry in manifest["entries"])
    return manifest_sha256, artifact_sha256s


def validate_bound_qualification_review(
    review: Mapping[str, Any],
    *,
    profile: Mapping[str, Any],
    metadata_review: Mapping[str, Any],
    evidence_manifest: Mapping[str, Any],
    evidence_artifact_bytes: Mapping[str, bytes] | None = None,
) -> str:
    manifest_sha256, artifact_sha256s = _manifest_binding(
        evidence_manifest,
        provider_id=str(profile["provider_id"]),
        artifact_bytes=evidence_artifact_bytes,
    )

    if review["executor_id"] == review["reviewer_id"]:
        raise ValueError("qualification execution and independent review must use distinct event identities")

    reviewed_at = review["reviewed_at"]
    for index, capture in enumerate(metadata_review["source_captures"]):
        if capture["retrieved_at"] > reviewed_at:
            raise ValueError(
                f"metadata source_captures[{index}] retrieval occurs after qualification review"
            )

    for index, check in enumerate(review["criteria_checks"]):
        missing = sorted(set(check["evidence_sha256s"]) - artifact_sha256s)
        if missing:
            raise ValueError(
                f"criteria_checks[{index}] references evidence outside complete manifest: {missing}"
            )

    return validate_qualification_review(
        review,
        profile=profile,
        metadata_review=metadata_review,
        evidence_manifest_sha256=manifest_sha256,
    )


def validate_bound_qualification_decision(
    decision: Mapping[str, Any],
    *,
    profile: Mapping[str, Any],
    review: Mapping[str, Any],
    metadata_review: Mapping[str, Any],
    evidence_manifest: Mapping[str, Any],
    evidence_artifact_bytes: Mapping[str, bytes] | None = None,
    expected_authority_id: str,
    expected_authority_public_key: bytes,
    signature_verifier,
) -> str:
    manifest_sha256, _ = _manifest_binding(
        evidence_manifest,
        provider_id=str(profile["provider_id"]),
        artifact_bytes=evidence_artifact_bytes,
    )
    validate_bound_qualification_review(
        review,
        profile=profile,
        metadata_review=metadata_review,
        evidence_manifest=evidence_manifest,
        evidence_artifact_bytes=evidence_artifact_bytes,
    )
    return validate_qualification_decision(
        decision,
        profile=profile,
        review=review,
        metadata_review=metadata_review,
        evidence_manifest_sha256=manifest_sha256,
        expected_authority_id=expected_authority_id,
        expected_authority_public_key=expected_authority_public_key,
        signature_verifier=signature_verifier,
    )


def derive_authoritative_qualification_state(
    *,
    provider_id: str,
    as_of_utc: str,
    rehearsal_verified: bool,
    profile: Mapping[str, Any] | None = None,
    evidence_manifest: Mapping[str, Any] | None = None,
    evidence_artifact_bytes: Mapping[str, bytes] | None = None,
    review: Mapping[str, Any] | None = None,
    decision: Mapping[str, Any] | None = None,
    metadata_reviews: Sequence[Mapping[str, Any]] = (),
    requalification_events: Sequence[Mapping[str, Any]] = (),
    expected_authority_id: str | None = None,
    expected_authority_public_key: bytes | None = None,
    signature_verifier=None,
) -> dict[str, Any]:
    if review is None and decision is None:
        return derive_qualification_state(
            provider_id=provider_id,
            as_of_utc=as_of_utc,
            rehearsal_verified=rehearsal_verified,
        )

    if profile is None or evidence_manifest is None:
        raise ValueError(
            "profile and evidence_manifest are required once qualification review exists"
        )
    if evidence_artifact_bytes is None:
        raise ValueError(
            "actual evidence artifact bytes are required once qualification review exists"
        )

    manifest_sha256, _ = _manifest_binding(
        evidence_manifest,
        provider_id=provider_id,
        artifact_bytes=evidence_artifact_bytes,
    )

    if review is not None:
        metadata_by_ref = {
            (item["object_id"], item["content_sha256"]): item
            for item in metadata_reviews
        }
        review_ref = review["metadata_review_ref"]
        bound_metadata = metadata_by_ref.get(
            (review_ref["object_id"], review_ref["content_sha256"])
        )
        if bound_metadata is None:
            raise ValueError(
                "metadata_reviews do not contain the metadata review bound by independent review"
            )
        validate_bound_qualification_review(
            review,
            profile=profile,
            metadata_review=bound_metadata,
            evidence_manifest=evidence_manifest,
            evidence_artifact_bytes=evidence_artifact_bytes,
        )

    if decision is not None:
        if review is None:
            raise ValueError("qualification decision requires independent review")
        if (
            expected_authority_id is None
            or expected_authority_public_key is None
            or signature_verifier is None
        ):
            raise ValueError(
                "external authority and signature verifier are required for qualification decision"
            )
        decision_ref = decision["signed_payload"]["metadata_review_ref"]
        metadata_by_ref = {
            (item["object_id"], item["content_sha256"]): item
            for item in metadata_reviews
        }
        decision_metadata = metadata_by_ref.get(
            (decision_ref["object_id"], decision_ref["content_sha256"])
        )
        if decision_metadata is None:
            raise ValueError(
                "metadata_reviews do not contain the metadata review bound by qualification decision"
            )
        validate_bound_qualification_decision(
            decision,
            profile=profile,
            review=review,
            metadata_review=decision_metadata,
            evidence_manifest=evidence_manifest,
            evidence_artifact_bytes=evidence_artifact_bytes,
            expected_authority_id=expected_authority_id,
            expected_authority_public_key=expected_authority_public_key,
            signature_verifier=signature_verifier,
        )

    return derive_qualification_state(
        provider_id=provider_id,
        as_of_utc=as_of_utc,
        rehearsal_verified=rehearsal_verified,
        profile=profile,
        evidence_manifest_sha256=manifest_sha256,
        review=review,
        decision=decision,
        metadata_reviews=metadata_reviews,
        requalification_events=requalification_events,
        expected_authority_id=expected_authority_id,
        expected_authority_public_key=expected_authority_public_key,
        signature_verifier=signature_verifier,
    )


def validate_qualification_state_by_recomputation(
    report: Mapping[str, Any],
    *,
    rehearsal_verified: bool,
    profile: Mapping[str, Any] | None = None,
    evidence_manifest: Mapping[str, Any] | None = None,
    evidence_artifact_bytes: Mapping[str, bytes] | None = None,
    review: Mapping[str, Any] | None = None,
    decision: Mapping[str, Any] | None = None,
    metadata_reviews: Sequence[Mapping[str, Any]] = (),
    requalification_events: Sequence[Mapping[str, Any]] = (),
    expected_authority_id: str | None = None,
    expected_authority_public_key: bytes | None = None,
    signature_verifier=None,
) -> str:
    expected = derive_authoritative_qualification_state(
        provider_id=str(report["provider_id"]),
        as_of_utc=str(report["as_of_utc"]),
        rehearsal_verified=rehearsal_verified,
        profile=profile,
        evidence_manifest=evidence_manifest,
        evidence_artifact_bytes=evidence_artifact_bytes,
        review=review,
        decision=decision,
        metadata_reviews=metadata_reviews,
        requalification_events=requalification_events,
        expected_authority_id=expected_authority_id,
        expected_authority_public_key=expected_authority_public_key,
        signature_verifier=signature_verifier,
    )
    if dict(report) != expected:
        raise ValueError(
            "qualification state report is not the exact deterministic result of authoritative inputs"
        )
    return expected["report_sha256"]
