from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import forecast_trust_core._roughtime_production_qualification_hardening as hardening
from forecast_trust_core.canonical import canonical_json


CRITERIA_ID = "FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1"
CRITERIA_SHA256 = "88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e"
BUILD_PROFILE_SHA256 = "1" * 64
BINARY_BYTES = b"verifier-binary"
BINARY_SHA256 = hashlib.sha256(BINARY_BYTES).hexdigest()
EXECUTION_BYTES = b"aggregate qualification report"
EXECUTION_SHA256 = hashlib.sha256(EXECUTION_BYTES).hexdigest()
REVIEW_BASIS_BYTES = b"independent review basis"
REVIEW_BASIS_SHA256 = hashlib.sha256(REVIEW_BASIS_BYTES).hexdigest()
CRITERION_BYTES = b"criterion evidence"
CRITERION_SHA256 = hashlib.sha256(CRITERION_BYTES).hexdigest()


def _build_profile():
    return {
        "profile_sha256": BUILD_PROFILE_SHA256,
        "binary_sha256": BINARY_SHA256,
    }


def _build_profile_bytes():
    return json.dumps(_build_profile(), sort_keys=True).encode("utf-8")


def _artifact_bytes(*, include_criterion: bool = True, include_binary: bool = True, exact_build_profile: bool = True):
    artifacts = {
        "reports/aggregate.json": EXECUTION_BYTES,
        "review/basis.bin": REVIEW_BASIS_BYTES,
        "verifier/build-profile.json": (
            _build_profile_bytes() if exact_build_profile else b'{"profile_sha256":"wrong"}'
        ),
    }
    if include_criterion:
        artifacts["evidence/criterion.bin"] = CRITERION_BYTES
    if include_binary:
        artifacts["verifier/fpp-roughtime-strict"] = BINARY_BYTES
    return artifacts


def _manifest(provider_id: str = "roughtime.se", *, include_evidence: bool = True, include_binary: bool = True, exact_build_profile: bool = True):
    artifacts = _artifact_bytes(
        include_criterion=include_evidence,
        include_binary=include_binary,
        exact_build_profile=exact_build_profile,
    )
    entries = []
    for path, data in sorted(artifacts.items()):
        entries.append(
            {
                "relative_path": path,
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "artifact_type": "test_artifact",
                "required": True,
                "provider_id": provider_id,
            }
        )
    return {
        "schema_version": "1.0",
        "object_type": "RoughtimeQualificationEvidenceManifest",
        "criteria_id": CRITERIA_ID,
        "criteria_sha256": CRITERIA_SHA256,
        "provider_id": provider_id,
        "entries": entries,
    }


def _write_package(
    root: Path,
    manifest: dict,
    *,
    include_evidence: bool = True,
    include_binary: bool = True,
    exact_build_profile: bool = True,
    canonical_manifest: bool = True,
    extra_file: bool = False,
) -> Path:
    artifacts = _artifact_bytes(
        include_criterion=include_evidence,
        include_binary=include_binary,
        exact_build_profile=exact_build_profile,
    )
    for relative, data in artifacts.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    manifest_bytes = canonical_json(manifest)
    if not canonical_manifest:
        manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    (root / "manifest.json").write_bytes(manifest_bytes)
    if extra_file:
        (root / "unexpected.txt").write_bytes(b"unexpected")
    return root


def _profile(provider_id: str = "roughtime.se"):
    return {
        "provider_id": provider_id,
        "verifier_build_profile_sha256": BUILD_PROFILE_SHA256,
    }


def _metadata():
    return {
        "object_id": "metadata:1",
        "content_sha256": "d" * 64,
        "reviewed_at": "2026-09-13T10:00:00Z",
        "source_captures": [
            {
                "retrieved_at": "2026-09-13T09:59:00Z",
            }
        ],
    }


def _review():
    return {
        "executor_id": "event:execution:1",
        "reviewer_id": "event:review:1",
        "reviewed_at": "2026-09-13T10:05:00Z",
        "metadata_review_ref": {
            "object_id": "metadata:1",
            "content_sha256": "d" * 64,
        },
        "execution_report_sha256": EXECUTION_SHA256,
        "verifier_build_profile_sha256": BUILD_PROFILE_SHA256,
        "verifier_binary_sha256": BINARY_SHA256,
        "review_basis_sha256": REVIEW_BASIS_SHA256,
        "criteria_checks": [
            {
                "criterion_id": "CRYPTOGRAPHIC",
                "disposition": "PASS",
                "evidence_sha256s": [CRITERION_SHA256],
                "reason_codes": [],
            }
        ],
    }


def _patch_review_validators(monkeypatch):
    monkeypatch.setattr(
        hardening,
        "validate_qualification_review",
        lambda *_args, **_kwargs: "review-ok",
    )
    monkeypatch.setattr(
        hardening,
        "validate_verifier_build_profile",
        lambda profile: profile["profile_sha256"],
    )


def test_bound_review_requires_package_root(tmp_path: Path, monkeypatch):
    _patch_review_validators(monkeypatch)
    with pytest.raises(ValueError, match="package root"):
        hardening.validate_bound_qualification_review(
            _review(),
            profile=_profile(),
            metadata_review=_metadata(),
            evidence_manifest=_manifest(),
            verifier_build_profile=_build_profile(),
        )


def test_bound_review_requires_canonical_manifest_file(tmp_path: Path, monkeypatch):
    _patch_review_validators(monkeypatch)
    manifest = _manifest()
    root = _write_package(tmp_path, manifest, canonical_manifest=False)
    with pytest.raises(ValueError, match="exact FPP_JCS_1 canonical manifest"):
        hardening.validate_bound_qualification_review(
            _review(),
            profile=_profile(),
            metadata_review=_metadata(),
            evidence_manifest=manifest,
            evidence_package_root=root,
            verifier_build_profile=_build_profile(),
        )


def test_bound_review_rejects_unexpected_package_file(tmp_path: Path, monkeypatch):
    _patch_review_validators(monkeypatch)
    manifest = _manifest()
    root = _write_package(tmp_path, manifest, extra_file=True)
    with pytest.raises(ValueError, match="unexpected"):
        hardening.validate_bound_qualification_review(
            _review(),
            profile=_profile(),
            metadata_review=_metadata(),
            evidence_manifest=manifest,
            evidence_package_root=root,
            verifier_build_profile=_build_profile(),
        )


def test_bound_review_requires_criterion_evidence_in_manifest(tmp_path: Path, monkeypatch):
    _patch_review_validators(monkeypatch)
    manifest = _manifest(include_evidence=False)
    root = _write_package(tmp_path, manifest, include_evidence=False)
    with pytest.raises(ValueError, match="outside complete manifest"):
        hardening.validate_bound_qualification_review(
            _review(),
            profile=_profile(),
            metadata_review=_metadata(),
            evidence_manifest=manifest,
            evidence_package_root=root,
            verifier_build_profile=_build_profile(),
        )


def test_bound_review_requires_distinct_execution_and_review_events(tmp_path: Path, monkeypatch):
    _patch_review_validators(monkeypatch)
    manifest = _manifest()
    root = _write_package(tmp_path, manifest)
    review = _review()
    review["reviewer_id"] = review["executor_id"]
    with pytest.raises(ValueError, match="distinct event identities"):
        hardening.validate_bound_qualification_review(
            review,
            profile=_profile(),
            metadata_review=_metadata(),
            evidence_manifest=manifest,
            evidence_package_root=root,
            verifier_build_profile=_build_profile(),
        )


def test_bound_review_rejects_capture_after_metadata_review(tmp_path: Path, monkeypatch):
    _patch_review_validators(monkeypatch)
    manifest = _manifest()
    root = _write_package(tmp_path, manifest)
    metadata = _metadata()
    metadata["source_captures"][0]["retrieved_at"] = "2026-09-13T10:01:00Z"
    with pytest.raises(ValueError, match="after metadata review"):
        hardening.validate_bound_qualification_review(
            _review(),
            profile=_profile(),
            metadata_review=metadata,
            evidence_manifest=manifest,
            evidence_package_root=root,
            verifier_build_profile=_build_profile(),
        )


def test_bound_review_requires_critical_raw_hashes_in_manifest(tmp_path: Path, monkeypatch):
    _patch_review_validators(monkeypatch)
    manifest = _manifest(include_binary=False)
    root = _write_package(tmp_path, manifest, include_binary=False)
    with pytest.raises(ValueError, match="verifier_binary_sha256 is not retained"):
        hardening.validate_bound_qualification_review(
            _review(),
            profile=_profile(),
            metadata_review=_metadata(),
            evidence_manifest=manifest,
            evidence_package_root=root,
            verifier_build_profile=_build_profile(),
        )


def test_bound_review_requires_exact_retained_build_profile(tmp_path: Path, monkeypatch):
    _patch_review_validators(monkeypatch)
    manifest = _manifest(exact_build_profile=False)
    root = _write_package(tmp_path, manifest, exact_build_profile=False)
    with pytest.raises(ValueError, match="exact JSON object is not retained"):
        hardening.validate_bound_qualification_review(
            _review(),
            profile=_profile(),
            metadata_review=_metadata(),
            evidence_manifest=manifest,
            evidence_package_root=root,
            verifier_build_profile=_build_profile(),
        )


def test_bound_review_cross_binds_build_profile_and_binary(tmp_path: Path, monkeypatch):
    _patch_review_validators(monkeypatch)
    manifest = _manifest()
    root = _write_package(tmp_path, manifest)
    build_profile = _build_profile()
    build_profile["binary_sha256"] = "9" * 64
    with pytest.raises(ValueError, match="verifier binary identity mismatch"):
        hardening.validate_bound_qualification_review(
            _review(),
            profile=_profile(),
            metadata_review=_metadata(),
            evidence_manifest=manifest,
            evidence_package_root=root,
            verifier_build_profile=build_profile,
        )


def test_authoritative_state_rejects_as_of_before_review(tmp_path: Path, monkeypatch):
    _patch_review_validators(monkeypatch)
    manifest = _manifest()
    root = _write_package(tmp_path, manifest)
    with pytest.raises(ValueError, match="predates qualification review"):
        hardening.derive_authoritative_qualification_state(
            provider_id="roughtime.se",
            as_of_utc="2026-09-13T10:04:59Z",
            rehearsal_verified=True,
            profile=_profile(),
            evidence_manifest=manifest,
            evidence_package_root=root,
            verifier_build_profile=_build_profile(),
            review=_review(),
            metadata_reviews=[_metadata()],
        )


def test_authoritative_state_rejects_backdated_metadata_capture(tmp_path: Path, monkeypatch):
    _patch_review_validators(monkeypatch)
    manifest = _manifest()
    root = _write_package(tmp_path, manifest)
    metadata = _metadata()
    metadata["source_captures"][0]["retrieved_at"] = "2026-09-13T10:01:00Z"
    with pytest.raises(ValueError, match="after metadata review"):
        hardening.derive_authoritative_qualification_state(
            provider_id="roughtime.se",
            as_of_utc="2026-09-13T10:06:00Z",
            rehearsal_verified=True,
            profile=_profile(),
            evidence_manifest=manifest,
            evidence_package_root=root,
            verifier_build_profile=_build_profile(),
            review=_review(),
            metadata_reviews=[metadata],
        )


def test_state_report_requires_exact_recomputation(monkeypatch):
    expected = {
        "schema_version": "1.0",
        "object_type": "RoughtimeQualificationStateReport",
        "provider_id": "roughtime.se",
        "as_of_utc": "2026-09-14T00:00:00Z",
        "state": "PRODUCTION_QUALIFIED",
        "reason_codes": ["SIGNED_DECISION_VALID_AND_METADATA_CURRENT"],
        "active_requalification_event_refs": [],
        "report_sha256": "f" * 64,
    }
    monkeypatch.setattr(
        hardening,
        "derive_authoritative_qualification_state",
        lambda **_kwargs: dict(expected),
    )
    assert hardening.validate_qualification_state_by_recomputation(
        expected,
        rehearsal_verified=True,
    ) == "f" * 64
    forged = dict(expected)
    forged["state"] = "QUALIFICATION_EXPIRED"
    with pytest.raises(ValueError, match="not the exact deterministic result"):
        hardening.validate_qualification_state_by_recomputation(
            forged,
            rehearsal_verified=True,
        )
