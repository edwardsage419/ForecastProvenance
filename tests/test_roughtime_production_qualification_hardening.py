from __future__ import annotations

import pytest

import forecast_trust_core._roughtime_production_qualification_hardening as hardening


def _manifest(provider_id: str = "roughtime.se", *, include_evidence: bool = True):
    entries = [
        {
            "relative_path": "reports/aggregate.json",
            "size": 3,
            "sha256": "a" * 64,
            "artifact_type": "aggregate_report",
            "required": True,
            "provider_id": provider_id,
        }
    ]
    if include_evidence:
        entries.insert(
            0,
            {
                "relative_path": "evidence/criterion.bin",
                "size": 1,
                "sha256": "b" * 64,
                "artifact_type": "criterion_evidence",
                "required": True,
                "provider_id": provider_id,
            },
        )
    return {
        "schema_version": "1.0",
        "object_type": "RoughtimeQualificationEvidenceManifest",
        "criteria_id": "FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1",
        "criteria_sha256": "c" * 64,
        "provider_id": provider_id,
        "entries": entries,
    }


def _profile(provider_id: str = "roughtime.se"):
    return {"provider_id": provider_id}


def _metadata():
    return {
        "object_id": "metadata:1",
        "content_sha256": "d" * 64,
        "source_captures": [
            {
                "retrieved_at": "2026-09-13T10:00:00Z",
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
        "criteria_checks": [
            {
                "criterion_id": "CRYPTOGRAPHIC",
                "disposition": "PASS",
                "evidence_sha256s": ["b" * 64],
                "reason_codes": [],
            }
        ],
    }


def test_bound_review_requires_criterion_evidence_in_manifest(monkeypatch):
    monkeypatch.setattr(
        hardening,
        "validate_qualification_evidence_manifest",
        lambda _manifest: "e" * 64,
    )
    monkeypatch.setattr(
        hardening,
        "validate_qualification_review",
        lambda *_args, **_kwargs: "review-ok",
    )

    assert hardening.validate_bound_qualification_review(
        _review(),
        profile=_profile(),
        metadata_review=_metadata(),
        evidence_manifest=_manifest(),
    ) == "review-ok"

    with pytest.raises(ValueError, match="outside complete manifest"):
        hardening.validate_bound_qualification_review(
            _review(),
            profile=_profile(),
            metadata_review=_metadata(),
            evidence_manifest=_manifest(include_evidence=False),
        )


def test_bound_review_requires_distinct_execution_and_review_events(monkeypatch):
    monkeypatch.setattr(
        hardening,
        "validate_qualification_evidence_manifest",
        lambda _manifest: "e" * 64,
    )
    review = _review()
    review["reviewer_id"] = review["executor_id"]

    with pytest.raises(ValueError, match="distinct event identities"):
        hardening.validate_bound_qualification_review(
            review,
            profile=_profile(),
            metadata_review=_metadata(),
            evidence_manifest=_manifest(),
        )


def test_bound_review_rejects_metadata_capture_after_review(monkeypatch):
    monkeypatch.setattr(
        hardening,
        "validate_qualification_evidence_manifest",
        lambda _manifest: "e" * 64,
    )
    metadata = _metadata()
    metadata["source_captures"][0]["retrieved_at"] = "2026-09-13T10:06:00Z"

    with pytest.raises(ValueError, match="after qualification review"):
        hardening.validate_bound_qualification_review(
            _review(),
            profile=_profile(),
            metadata_review=metadata,
            evidence_manifest=_manifest(),
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
