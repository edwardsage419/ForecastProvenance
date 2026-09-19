from __future__ import annotations

import base64
import hashlib
from pathlib import Path

import pytest

from forecast_trust_core._roughtime_profile import PROVIDER_BY_ID
from forecast_trust_core._roughtime_production_qualification import (
    CRITERIA_ID,
    CRITERIA_SHA256,
    DECISION_SIGNATURE_PROJECTION,
    REVIEW_CRITERIA,
    collect_manifest_artifacts,
    derive_qualification_state,
    object_ref,
    qualification_decision_signing_bytes,
    validate_production_provider_profile,
    validate_provider_metadata_review,
    validate_qualification_decision,
    validate_qualification_evidence_manifest,
    validate_qualification_review,
    validate_requalification_event,
)
from forecast_trust_core.canonical import content_hash, seal_object

ROOT = Path(__file__).resolve().parents[1]


def _profile(provider_id: str = "roughtime.se") -> dict[str, object]:
    provider = PROVIDER_BY_ID[provider_id]
    payload = {
        "schema_version": "1.0",
        "criteria_id": CRITERIA_ID,
        "criteria_sha256": CRITERIA_SHA256,
        "provider_id": provider.provider_id,
        "operator_identity": provider.operator_identity,
        "host": provider.host,
        "port": provider.port,
        "transport": provider.transport,
        "operator_declared_protocol": provider.operator_declared_protocol,
        "wire_version_hex": provider.wire_version_hex,
        "offered_version_hex": provider.offered_version_hex,
        "wire_profile": provider.wire_profile,
        "require_type": provider.require_type,
        "require_srv": provider.require_srv,
        "root_public_key_base64": provider.root_public_key_base64,
        "packet_profile": "STANDARD_1024_BODY",
        "transport_profile": "UDP_ONLY",
        "nonce_profile": "FPP_ROUGHTIME_NONCE_V2",
        "verifier_repository": "github.com/tannerryan/roughtime",
        "verifier_tag": "v1.27.0",
        "verifier_commit": "56b346a16cd7e8317bb0d24f1ec15549cf93a4c9",
        "verifier_build_profile_sha256": "1" * 64,
        "service_classification": (
            "PILOT_EXPERIMENTAL"
            if provider_id == "TimeNL-Roughtime"
            else "STANDARD_PUBLIC_SERVICE"
        ),
        "no_fallback": True,
    }
    return seal_object(
        payload,
        object_type="RoughtimeProductionProviderProfile",
        stable_context=provider_id,
    )


def _metadata(
    profile: dict[str, object],
    reviewed_at: str = "2026-09-13T10:00:00Z",
) -> dict[str, object]:
    lifecycle = (
        "PILOT_EXPERIMENTAL"
        if profile["service_classification"] == "PILOT_EXPERIMENTAL"
        else "STANDARD"
    )
    return seal_object(
        {
            "schema_version": "1.0",
            "provider_id": profile["provider_id"],
            "provider_profile_ref": object_ref(profile),
            "reviewed_at": reviewed_at,
            "source_captures": [
                {
                    "source_id": "operator:primary",
                    "evidence_locator": "https://operator.example/evidence",
                    "retrieved_at": reviewed_at,
                    "capture_sha256": "2" * 64,
                }
            ],
            "operator_identity_status": "UNCHANGED",
            "service_status": "ACTIVE",
            "endpoint_status": "UNCHANGED",
            "root_key_status": "UNCHANGED",
            "protocol_status": "UNCHANGED",
            "use_permission_status": "AFFIRMATIVE",
            "lifecycle_status": lifecycle,
            "rotation_notice_status": "NONE_PUBLISHED",
            "change_disposition": "UNCHANGED",
            "reason_codes": [],
        },
        object_type="RoughtimeProviderMetadataReview",
        stable_context=str(profile["provider_id"]),
    )


def _manifest_hash(profile: dict[str, object]) -> str:
    data = b"aggregate qualification report"
    relative_path = "reports/aggregate.json"
    manifest = {
        "schema_version": "1.0",
        "object_type": "RoughtimeQualificationEvidenceManifest",
        "criteria_id": CRITERIA_ID,
        "criteria_sha256": CRITERIA_SHA256,
        "provider_id": profile["provider_id"],
        "entries": [
            {
                "relative_path": relative_path,
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "artifact_type": "aggregate_report",
                "required": True,
                "provider_id": profile["provider_id"],
            }
        ],
    }
    return validate_qualification_evidence_manifest(
        manifest,
        artifact_bytes={relative_path: data},
    )


def _review(
    profile: dict[str, object],
    metadata: dict[str, object],
    manifest_hash: str,
) -> dict[str, object]:
    checks = []
    for criterion_id in sorted(REVIEW_CRITERIA):
        disposition = "PASS"
        evidence = ["3" * 64]
        if (
            criterion_id == "PILOT_EXPERIMENTAL"
            and profile["service_classification"] != "PILOT_EXPERIMENTAL"
        ):
            disposition = "NOT_APPLICABLE"
            evidence = []
        checks.append(
            {
                "criterion_id": criterion_id,
                "disposition": disposition,
                "evidence_sha256s": evidence,
                "reason_codes": [],
            }
        )
    return seal_object(
        {
            "schema_version": "1.0",
            "criteria_id": CRITERIA_ID,
            "criteria_sha256": CRITERIA_SHA256,
            "provider_id": profile["provider_id"],
            "provider_profile_ref": object_ref(profile),
            "evidence_manifest_sha256": manifest_hash,
            "execution_report_sha256": "4" * 64,
            "verifier_build_profile_sha256": profile["verifier_build_profile_sha256"],
            "verifier_binary_sha256": "5" * 64,
            "metadata_review_ref": object_ref(metadata),
            "executor_id": "owner:execution-event:1",
            "reviewer_id": "owner:independent-review-event:1",
            "review_basis_sha256": "6" * 64,
            "criteria_checks": checks,
            "evidence_complete": True,
            "deterministic_validation_passed": True,
            "strict_replay_passed": True,
            "blocking_findings": [],
            "review_result": "PASS",
            "reviewed_at": "2026-09-13T10:05:00Z",
        },
        object_type="RoughtimeQualificationReview",
        stable_context=str(profile["provider_id"]),
    )


def _fake_signature(public_key: bytes, message: bytes) -> bytes:
    return hashlib.sha512(public_key + message).digest()


def _fake_verifier(public_key: bytes, message: bytes, signature: bytes) -> bool:
    return signature == _fake_signature(public_key, message)


def _decision(
    profile: dict[str, object],
    metadata: dict[str, object],
    review: dict[str, object],
    manifest_hash: str,
    *,
    public_key: bytes,
    authority_id: str,
) -> dict[str, object]:
    signed_payload = {
        "criteria_id": CRITERIA_ID,
        "criteria_sha256": CRITERIA_SHA256,
        "provider_id": profile["provider_id"],
        "provider_profile_ref": object_ref(profile),
        "evidence_manifest_sha256": manifest_hash,
        "verifier_build_profile_sha256": review["verifier_build_profile_sha256"],
        "verifier_binary_sha256": review["verifier_binary_sha256"],
        "independent_review_ref": object_ref(review),
        "metadata_review_ref": object_ref(metadata),
        "decision_result": "PRODUCTION_QUALIFIED",
        "decision_timestamp": "2026-09-13T10:10:00Z",
        "authority_id": authority_id,
        "authority_public_key_sha256": hashlib.sha256(public_key).hexdigest(),
    }
    signature = _fake_signature(
        public_key,
        qualification_decision_signing_bytes(signed_payload),
    )
    return seal_object(
        {
            "schema_version": "1.0",
            "signature_projection": DECISION_SIGNATURE_PROJECTION,
            "signed_payload": signed_payload,
            "signed_payload_sha256": content_hash(signed_payload),
            "signature_algorithm": "ED25519",
            "authority_signature_base64": base64.b64encode(signature).decode("ascii"),
        },
        object_type="RoughtimeQualificationDecision",
        stable_context=str(profile["provider_id"]),
    )


def _qualified_inputs() -> tuple:
    profile = _profile()
    metadata = _metadata(profile)
    manifest_hash = _manifest_hash(profile)
    review = _review(profile, metadata, manifest_hash)
    authority_key = b"K" * 32
    authority_id = "authority:genesis-owner:v1"
    decision = _decision(
        profile,
        metadata,
        review,
        manifest_hash,
        public_key=authority_key,
        authority_id=authority_id,
    )
    return profile, metadata, manifest_hash, review, authority_key, authority_id, decision


def test_frozen_criteria_hash_matches_repository_bytes() -> None:
    data = (
        ROOT
        / "docs"
        / "GEN_001_ROUGHTIME_PRODUCTION_QUALIFICATION_CRITERIA_V1.md"
    ).read_bytes()
    assert hashlib.sha256(data).hexdigest() == CRITERIA_SHA256


@pytest.mark.parametrize(
    "provider_id",
    ["roughtime.se", "time.txryan.com", "TimeNL-Roughtime"],
)
def test_provider_profile_requires_exact_frozen_identity(provider_id: str) -> None:
    profile = _profile(provider_id)
    assert validate_production_provider_profile(profile) == profile["content_sha256"]


def test_profile_rejects_endpoint_substitution() -> None:
    profile = _profile()
    payload = {
        key: value
        for key, value in profile.items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    payload["host"] = "unexpected.example"
    tampered = seal_object(
        payload,
        object_type="RoughtimeProductionProviderProfile",
        stable_context="roughtime.se",
    )
    with pytest.raises(ValueError, match="host mismatch"):
        validate_production_provider_profile(tampered)


def test_manifest_closes_exact_artifact_set_and_excludes_itself(tmp_path: Path) -> None:
    profile = _profile()
    package = tmp_path / "package"
    (package / "reports").mkdir(parents=True)
    (package / "reports" / "aggregate.json").write_bytes(b"abc")
    (package / "manifest.json").write_text("excluded self", encoding="utf-8")
    artifacts = collect_manifest_artifacts(package, manifest_relative_path="manifest.json")

    manifest = {
        "schema_version": "1.0",
        "object_type": "RoughtimeQualificationEvidenceManifest",
        "criteria_id": CRITERIA_ID,
        "criteria_sha256": CRITERIA_SHA256,
        "provider_id": profile["provider_id"],
        "entries": [
            {
                "relative_path": "reports/aggregate.json",
                "size": 3,
                "sha256": hashlib.sha256(b"abc").hexdigest(),
                "artifact_type": "aggregate_report",
                "required": True,
                "provider_id": profile["provider_id"],
            }
        ],
    }
    assert validate_qualification_evidence_manifest(manifest, artifact_bytes=artifacts)

    (package / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected"):
        validate_qualification_evidence_manifest(
            manifest,
            artifact_bytes=collect_manifest_artifacts(
                package,
                manifest_relative_path="manifest.json",
            ),
        )

    bad = dict(manifest)
    bad["entries"] = [dict(manifest["entries"][0], relative_path="../escape")]
    with pytest.raises(ValueError, match="relative_path"):
        validate_qualification_evidence_manifest(bad)


def test_decision_requires_external_authority_and_exact_signature() -> None:
    profile, metadata, manifest_hash, review, authority_key, authority_id, decision = _qualified_inputs()

    assert validate_qualification_decision(
        decision,
        profile=profile,
        review=review,
        metadata_review=metadata,
        evidence_manifest_sha256=manifest_hash,
        expected_authority_id=authority_id,
        expected_authority_public_key=authority_key,
        signature_verifier=_fake_verifier,
    )

    with pytest.raises(ValueError, match="authority public key mismatch"):
        validate_qualification_decision(
            decision,
            profile=profile,
            review=review,
            metadata_review=metadata,
            evidence_manifest_sha256=manifest_hash,
            expected_authority_id=authority_id,
            expected_authority_public_key=b"Q" * 32,
            signature_verifier=_fake_verifier,
        )

    with pytest.raises(ValueError, match="signature invalid"):
        validate_qualification_decision(
            decision,
            profile=profile,
            review=review,
            metadata_review=metadata,
            evidence_manifest_sha256=manifest_hash,
            expected_authority_id=authority_id,
            expected_authority_public_key=authority_key,
            signature_verifier=lambda _pk, _message, _signature: False,
        )


def test_rehearsal_and_review_cannot_auto_qualify() -> None:
    pre = derive_qualification_state(
        provider_id="roughtime.se",
        as_of_utc="2026-09-13T10:00:00Z",
        rehearsal_verified=True,
    )
    assert pre["state"] == "REHEARSAL_VERIFIED"

    profile = _profile()
    metadata = _metadata(profile)
    manifest_hash = _manifest_hash(profile)
    review = _review(profile, metadata, manifest_hash)
    ready = derive_qualification_state(
        provider_id="roughtime.se",
        as_of_utc="2026-09-13T10:06:00Z",
        rehearsal_verified=True,
        profile=profile,
        evidence_manifest_sha256=manifest_hash,
        review=review,
        metadata_reviews=[metadata],
    )
    assert ready["state"] == "QUALIFICATION_REVIEW_READY"


def test_signed_state_expires_and_requalification_trigger_dominates() -> None:
    profile, metadata, manifest_hash, review, authority_key, authority_id, decision = _qualified_inputs()
    kwargs = dict(
        provider_id="roughtime.se",
        rehearsal_verified=True,
        profile=profile,
        evidence_manifest_sha256=manifest_hash,
        review=review,
        decision=decision,
        metadata_reviews=[metadata],
        expected_authority_id=authority_id,
        expected_authority_public_key=authority_key,
        signature_verifier=_fake_verifier,
    )

    assert derive_qualification_state(
        as_of_utc="2026-09-14T00:00:00Z",
        **kwargs,
    )["state"] == "PRODUCTION_QUALIFIED"

    assert derive_qualification_state(
        as_of_utc="2026-12-13T10:00:01Z",
        **kwargs,
    )["state"] == "QUALIFICATION_EXPIRED"

    trigger = seal_object(
        {
            "schema_version": "1.0",
            "provider_id": profile["provider_id"],
            "provider_profile_ref": object_ref(profile),
            "trigger_code": "STANDARDS_MIGRATION",
            "detected_at": "2026-09-20T00:00:00Z",
            "evidence_sha256s": ["7" * 64],
            "reason_codes": ["RFC_PROFILE_CHANGED"],
        },
        object_type="RoughtimeRequalificationEvent",
        stable_context="roughtime.se",
    )
    assert validate_requalification_event(trigger, profile=profile)
    kwargs["requalification_events"] = [trigger]
    assert derive_qualification_state(
        as_of_utc="2026-09-21T00:00:00Z",
        **kwargs,
    )["state"] == "REQUALIFICATION_REQUIRED"


def test_pilot_provider_requires_pilot_gate_pass() -> None:
    profile = _profile("TimeNL-Roughtime")
    metadata = _metadata(profile)
    manifest_hash = _manifest_hash(profile)
    review = _review(profile, metadata, manifest_hash)
    payload = {
        key: value
        for key, value in review.items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    checks = [dict(item) for item in payload["criteria_checks"]]
    for item in checks:
        if item["criterion_id"] == "PILOT_EXPERIMENTAL":
            item["disposition"] = "NOT_APPLICABLE"
            item["evidence_sha256s"] = []
    payload["criteria_checks"] = checks
    bad_review = seal_object(
        payload,
        object_type="RoughtimeQualificationReview",
        stable_context="TimeNL-Roughtime",
    )
    with pytest.raises(ValueError, match="pilot provider requires PASS"):
        validate_qualification_review(
            bad_review,
            profile=profile,
            metadata_review=metadata,
            evidence_manifest_sha256=manifest_hash,
        )


def test_metadata_review_cannot_label_root_change_unchanged() -> None:
    profile = _profile()
    review = _metadata(profile)
    payload = {
        key: value
        for key, value in review.items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    payload["root_key_status"] = "CHANGED"
    bad = seal_object(
        payload,
        object_type="RoughtimeProviderMetadataReview",
        stable_context="roughtime.se",
    )
    with pytest.raises(ValueError, match="UNCHANGED metadata disposition conflicts"):
        validate_provider_metadata_review(bad, profile=profile)
