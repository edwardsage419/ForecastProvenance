from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from .canonical import canonical_json, parse_json_strict, require_utc_timestamp
from ._roughtime_control import validate_verifier_build_profile
from ._roughtime_production_qualification import (
    collect_manifest_artifacts,
    derive_qualification_state,
    validate_qualification_decision,
    validate_qualification_evidence_manifest,
    validate_qualification_review,
)


def _collect_evidence_package(
    manifest: Mapping[str, Any],
    *,
    package_root: Path | None,
    manifest_relative_path: str,
) -> Mapping[str, bytes]:
    if package_root is None:
        raise ValueError("qualification evidence package root is required")
    root = Path(package_root)
    artifact_bytes = collect_manifest_artifacts(
        root,
        manifest_relative_path=manifest_relative_path,
    )
    manifest_path = root.resolve() / manifest_relative_path
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("qualification evidence manifest file must exist as a regular non-symlink file")
    if manifest_path.read_bytes() != canonical_json(manifest):
        raise ValueError("qualification evidence manifest file is not the exact FPP_JCS_1 canonical manifest")
    return artifact_bytes


def _manifest_binding(
    manifest: Mapping[str, Any],
    *,
    provider_id: str,
    package_root: Path | None,
    manifest_relative_path: str,
) -> tuple[str, frozenset[str], Mapping[str, bytes]]:
    artifact_bytes = _collect_evidence_package(
        manifest,
        package_root=package_root,
        manifest_relative_path=manifest_relative_path,
    )
    manifest_sha256 = validate_qualification_evidence_manifest(
        manifest,
        artifact_bytes=artifact_bytes,
    )
    if manifest["provider_id"] != provider_id:
        raise ValueError("evidence manifest provider mismatch")
    artifact_sha256s = frozenset(entry["sha256"] for entry in manifest["entries"])
    return manifest_sha256, artifact_sha256s, artifact_bytes


def _require_artifact_hash(
    artifact_sha256s: frozenset[str],
    digest: Any,
    field: str,
) -> str:
    if not isinstance(digest, str) or digest not in artifact_sha256s:
        raise ValueError(f"{field} is not retained by the complete evidence manifest")
    return digest


def _require_exact_json_artifact(
    artifact_bytes: Mapping[str, bytes],
    expected: Mapping[str, Any],
    name: str,
) -> None:
    target = dict(expected)
    for data in artifact_bytes.values():
        try:
            candidate = parse_json_strict(data)
        except (TypeError, ValueError):
            continue
        if isinstance(candidate, dict) and candidate == target:
            return
    raise ValueError(f"{name} exact JSON object is not retained by the complete evidence manifest")


def _validate_metadata_causality(metadata_review: Mapping[str, Any]) -> None:
    reviewed_at = metadata_review["reviewed_at"]
    require_utc_timestamp(reviewed_at)
    for index, capture in enumerate(metadata_review["source_captures"]):
        retrieved_at = capture["retrieved_at"]
        require_utc_timestamp(retrieved_at)
        if retrieved_at > reviewed_at:
            raise ValueError(
                f"metadata source_captures[{index}] retrieval occurs after metadata review"
            )


def _validate_review_artifact_bindings(
    review: Mapping[str, Any],
    *,
    profile: Mapping[str, Any],
    verifier_build_profile: Mapping[str, Any] | None,
    artifact_bytes: Mapping[str, bytes],
    artifact_sha256s: frozenset[str],
) -> None:
    if verifier_build_profile is None:
        raise ValueError("verified Roughtime build profile is required for qualification review")
    build_profile_hash = validate_verifier_build_profile(verifier_build_profile)
    if review["verifier_build_profile_sha256"] != build_profile_hash:
        raise ValueError("qualification review verifier build profile identity mismatch")
    if profile["verifier_build_profile_sha256"] != build_profile_hash:
        raise ValueError("provider profile verifier build profile identity mismatch")
    binary_sha256 = verifier_build_profile["binary_sha256"]
    if review["verifier_binary_sha256"] != binary_sha256:
        raise ValueError("qualification review verifier binary identity mismatch")

    _require_artifact_hash(
        artifact_sha256s,
        review["execution_report_sha256"],
        "execution_report_sha256",
    )
    _require_artifact_hash(
        artifact_sha256s,
        review["verifier_binary_sha256"],
        "verifier_binary_sha256",
    )
    _require_artifact_hash(
        artifact_sha256s,
        review["review_basis_sha256"],
        "review_basis_sha256",
    )
    _require_exact_json_artifact(
        artifact_bytes,
        verifier_build_profile,
        "verifier build profile",
    )


def validate_bound_qualification_review(
    review: Mapping[str, Any],
    *,
    profile: Mapping[str, Any],
    metadata_review: Mapping[str, Any],
    evidence_manifest: Mapping[str, Any],
    evidence_package_root: Path | None = None,
    evidence_manifest_relative_path: str = "manifest.json",
    verifier_build_profile: Mapping[str, Any] | None = None,
) -> str:
    manifest_sha256, artifact_sha256s, artifact_bytes = _manifest_binding(
        evidence_manifest,
        provider_id=str(profile["provider_id"]),
        package_root=evidence_package_root,
        manifest_relative_path=evidence_manifest_relative_path,
    )
    _validate_review_artifact_bindings(
        review,
        profile=profile,
        verifier_build_profile=verifier_build_profile,
        artifact_bytes=artifact_bytes,
        artifact_sha256s=artifact_sha256s,
    )

    if review["executor_id"] == review["reviewer_id"]:
        raise ValueError("qualification execution and independent review must use distinct event identities")

    _validate_metadata_causality(metadata_review)
    require_utc_timestamp(review["reviewed_at"])
    if metadata_review["reviewed_at"] > review["reviewed_at"]:
        raise ValueError("metadata review occurs after qualification review")

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
    evidence_package_root: Path | None = None,
    evidence_manifest_relative_path: str = "manifest.json",
    verifier_build_profile: Mapping[str, Any] | None = None,
    expected_authority_id: str,
    expected_authority_public_key: bytes,
    signature_verifier,
) -> str:
    manifest_sha256, _, _ = _manifest_binding(
        evidence_manifest,
        provider_id=str(profile["provider_id"]),
        package_root=evidence_package_root,
        manifest_relative_path=evidence_manifest_relative_path,
    )
    validate_bound_qualification_review(
        review,
        profile=profile,
        metadata_review=metadata_review,
        evidence_manifest=evidence_manifest,
        evidence_package_root=evidence_package_root,
        evidence_manifest_relative_path=evidence_manifest_relative_path,
        verifier_build_profile=verifier_build_profile,
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
    evidence_package_root: Path | None = None,
    evidence_manifest_relative_path: str = "manifest.json",
    verifier_build_profile: Mapping[str, Any] | None = None,
    review: Mapping[str, Any] | None = None,
    decision: Mapping[str, Any] | None = None,
    metadata_reviews: Sequence[Mapping[str, Any]] = (),
    requalification_events: Sequence[Mapping[str, Any]] = (),
    expected_authority_id: str | None = None,
    expected_authority_public_key: bytes | None = None,
    signature_verifier=None,
) -> dict[str, Any]:
    require_utc_timestamp(as_of_utc)
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
    if evidence_package_root is None:
        raise ValueError(
            "qualification evidence package root is required once qualification review exists"
        )
    if verifier_build_profile is None:
        raise ValueError(
            "verified Roughtime build profile is required once qualification review exists"
        )

    for metadata in metadata_reviews:
        _validate_metadata_causality(metadata)

    manifest_sha256, _, _ = _manifest_binding(
        evidence_manifest,
        provider_id=provider_id,
        package_root=evidence_package_root,
        manifest_relative_path=evidence_manifest_relative_path,
    )

    if review is not None:
        require_utc_timestamp(review["reviewed_at"])
        if as_of_utc < review["reviewed_at"]:
            raise ValueError("as_of_utc predates qualification review")
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
            evidence_package_root=evidence_package_root,
            evidence_manifest_relative_path=evidence_manifest_relative_path,
            verifier_build_profile=verifier_build_profile,
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
            evidence_package_root=evidence_package_root,
            evidence_manifest_relative_path=evidence_manifest_relative_path,
            verifier_build_profile=verifier_build_profile,
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
    evidence_package_root: Path | None = None,
    evidence_manifest_relative_path: str = "manifest.json",
    verifier_build_profile: Mapping[str, Any] | None = None,
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
        evidence_package_root=evidence_package_root,
        evidence_manifest_relative_path=evidence_manifest_relative_path,
        verifier_build_profile=verifier_build_profile,
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
