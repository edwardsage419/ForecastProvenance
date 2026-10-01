from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

import pytest

import forecast_trust_core.architecture_compression_v1_hardening as hardening
from forecast_trust_core.canonical import canonical_json, seal_object


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def sealed(kind, object_id, **payload):
    return seal_object(
        {"schema_version": "1.0", **payload},
        object_type=kind,
        stable_context="test",
        semantic_id=object_id,
    )


def claim(claim_type, subject_ref, state="VERIFIED"):
    return {
        "claim_type": claim_type,
        "subject_ref": dict(subject_ref),
        "state": state,
        "policy_refs": [],
        "evidence_refs": [],
        "reason_codes": [],
    }


def test_deadline_claim_rejects_verified_existence_from_another_subject():
    subject_a = sealed("Subject", "subject:a:v1", value="a")
    subject_b = sealed("Subject", "subject:b:v1", value="b")
    foreign = claim("EXTERNAL_EXISTENCE_BOUND_VERIFIED", ref(subject_b))
    foreign["verified_upper_bound"] = "2026-09-01T00:00:00Z"
    result = hardening.derive_deadline_existence_claim_strict(
        ref(subject_a),
        external_existence_claim=foreign,
        frozen_deadline="2026-09-02T00:00:00Z",
    )
    assert result["state"] == "FAILED"
    assert "EXTERNAL_EXISTENCE_SUBJECT_TYPE_OR_STATE_MISMATCH" in result["reason_codes"]


def test_pre_outcome_claim_rejects_cross_subject_bitcoin_claim():
    subject_a = sealed("Subject", "subject:a:v1", value="a")
    subject_b = sealed("Subject", "subject:b:v1", value="b")
    dvr = sealed("DurabilityVerificationRecord", "dvr:a:v1", value="dvr")
    bitcoin = claim("BITCOIN_DURABILITY_VERIFIED", ref(subject_b))
    dvr_deadline = claim("DEADLINE_EXISTENCE_VERIFIED", ref(dvr))
    result = hardening.derive_pre_outcome_durability_claim_strict(
        ref(subject_a),
        bitcoin_durability_claim=bitcoin,
        durability_record_deadline_claim=dvr_deadline,
        durability_record_subject_ref=ref(dvr),
        durability_record_bound_subject_ref=ref(subject_a),
    )
    assert result["state"] == "FAILED"
    assert "BITCOIN_DURABILITY_SUBJECT_TYPE_OR_STATE_MISMATCH" in result["reason_codes"]


def test_confirmatory_eligibility_rejects_required_claim_subject_substitution():
    forecast = sealed("IssuedForecast", "forecast:a:v1", value="1")
    plan = sealed("IssuanceCyclePlan", "plan:a:v1", cycle="a")
    other_plan = sealed("IssuanceCyclePlan", "plan:b:v1", cycle="b")
    supplied = [claim("DEADLINE_EXISTENCE_VERIFIED", ref(other_plan))]
    requirements = [
        {
            "claim_type": "DEADLINE_EXISTENCE_VERIFIED",
            "subject_ref": ref(plan),
        }
    ]
    result = hardening.derive_confirmatory_eligibility_strict(
        ref(forecast),
        required_claims=supplied,
        required_claim_requirements=requirements,
    )
    assert result["state"] == "FAILED"
    assert "REQUIRED_CLAIM_SET_SUBSTITUTION" in result["reason_codes"]


def test_confirmatory_eligibility_rejects_unknown_or_recursive_claim_type():
    forecast = sealed("IssuedForecast", "forecast:a:v1", value="1")
    supplied = [claim("CONFIRMATORY_PROSPECTIVE_ELIGIBLE", ref(forecast))]
    requirements = [
        {
            "claim_type": "CONFIRMATORY_PROSPECTIVE_ELIGIBLE",
            "subject_ref": ref(forecast),
        }
    ]
    result = hardening.derive_confirmatory_eligibility_strict(
        ref(forecast),
        required_claims=supplied,
        required_claim_requirements=requirements,
    )
    assert result["state"] == "FAILED"
    assert "MALFORMED_OR_UNKNOWN_REQUIRED_CLAIM_BINDING" in result["reason_codes"]


def _state_package_fixture(*, state="PRODUCTION_QUALIFIED", report_sha="1" * 64):
    profile = sealed("RoughtimeProductionProviderProfile", "profile:test:v1", provider_id="roughtime.se")
    decision = sealed("RoughtimeQualificationDecision", "decision:test:v1", provider_id="roughtime.se")
    verifier = sealed("ValidatorContract", "validator:qualification:test:v1", contract="test")
    evidence_manifest = {
        "schema_version": "1.0",
        "object_type": "RoughtimeQualificationEvidenceManifest",
        "provider_id": "roughtime.se",
        "entries": [],
    }
    manifest_sha = hashlib.sha256(canonical_json(evidence_manifest)).hexdigest()
    package = sealed(
        "RoughtimeProviderQualificationStatePackage",
        "state-package:test:v1",
        provider_id="roughtime.se",
        as_of_utc="2026-09-10T00:00:00Z",
        provider_profile_ref=ref(profile),
        qualification_decision_ref=ref(decision),
        qualification_evidence_manifest_sha256=manifest_sha,
        qualification_verifier_contract_ref=ref(verifier),
        metadata_review_refs=[],
        requalification_event_refs=[],
        qualification_state_report_sha256=report_sha,
        qualification_state=state,
    )
    return profile, decision, verifier, evidence_manifest, package


def _validate_package(package, profile, decision, verifier, evidence_manifest, root):
    return hardening.validate_qualification_state_package_authoritatively(
        package,
        record_root=root,
        profile=profile,
        evidence_manifest=evidence_manifest,
        evidence_package_root=root,
        verifier_build_profile={},
        review={},
        decision=decision,
        qualification_verifier_contract_ref=ref(verifier),
        expected_authority_id="authority:test:v1",
        expected_authority_public_key=b"x" * 32,
        signature_verifier=lambda *_args: True,
    )


def test_state_package_cannot_self_assert_production_qualified(monkeypatch):
    profile, decision, verifier, evidence_manifest, package = _state_package_fixture()
    monkeypatch.setattr(
        hardening,
        "derive_authoritative_qualification_state",
        lambda **_kwargs: {
            "provider_id": "roughtime.se",
            "as_of_utc": "2026-09-10T00:00:00Z",
            "state": "REQUALIFICATION_REQUIRED",
            "report_sha256": "2" * 64,
        },
    )
    with tempfile.TemporaryDirectory() as tmp:
        result = _validate_package(
            package,
            profile,
            decision,
            verifier,
            evidence_manifest,
            Path(tmp),
        )
    reasons = {check.reason_code for check in result.checks if check.status == "FAIL"}
    assert "SELF_ASSERTED_QUALIFICATION_STATE_MISMATCH" in reasons
    assert "QUALIFICATION_STATE_REPORT_HASH_MISMATCH" in reasons


def test_state_package_accepts_only_exact_authoritative_state(monkeypatch):
    profile, decision, verifier, evidence_manifest, package = _state_package_fixture()
    monkeypatch.setattr(
        hardening,
        "derive_authoritative_qualification_state",
        lambda **_kwargs: {
            "provider_id": "roughtime.se",
            "as_of_utc": "2026-09-10T00:00:00Z",
            "state": "PRODUCTION_QUALIFIED",
            "report_sha256": "1" * 64,
        },
    )
    with tempfile.TemporaryDirectory() as tmp:
        result = _validate_package(
            package,
            profile,
            decision,
            verifier,
            evidence_manifest,
            Path(tmp),
        )
    assert result.valid


def test_state_package_rejects_authoritative_provider_or_as_of_substitution(monkeypatch):
    profile, decision, verifier, evidence_manifest, package = _state_package_fixture()
    monkeypatch.setattr(
        hardening,
        "derive_authoritative_qualification_state",
        lambda **_kwargs: {
            "provider_id": "time.txryan.com",
            "as_of_utc": "2026-09-11T00:00:00Z",
            "state": "PRODUCTION_QUALIFIED",
            "report_sha256": "1" * 64,
        },
    )
    with tempfile.TemporaryDirectory() as tmp:
        result = _validate_package(
            package,
            profile,
            decision,
            verifier,
            evidence_manifest,
            Path(tmp),
        )
    reasons = {check.reason_code for check in result.checks if check.status == "FAIL"}
    assert "AUTHORITATIVE_STATE_PROVIDER_MISMATCH" in reasons
    assert "AUTHORITATIVE_STATE_AS_OF_MISMATCH" in reasons


def test_state_store_malformed_json_fails_closed(monkeypatch):
    profile, decision, verifier, evidence_manifest, package = _state_package_fixture()
    monkeypatch.setattr(
        hardening,
        "derive_authoritative_qualification_state",
        lambda **_kwargs: {
            "provider_id": "roughtime.se",
            "as_of_utc": "2026-09-10T00:00:00Z",
            "state": "PRODUCTION_QUALIFIED",
            "report_sha256": "1" * 64,
        },
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "broken.json").write_text("{not-json", encoding="utf-8")
        result = _validate_package(
            package,
            profile,
            decision,
            verifier,
            evidence_manifest,
            root,
        )
    reasons = {check.reason_code for check in result.checks if check.status == "FAIL"}
    assert "AUTHORITATIVE_STATE_COLLECTION_FAILED" in reasons


def test_state_store_noncanonical_timestamp_fails_closed():
    metadata = sealed(
        "RoughtimeProviderMetadataReview",
        "metadata:test:v1",
        provider_id="roughtime.se",
        reviewed_at="2026-09-10T00:00:00+00:00",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "metadata.json").write_bytes(canonical_json(metadata))
        with pytest.raises(Exception):
            hardening.collect_qualification_state_objects_strict(
                root,
                provider_id="roughtime.se",
                as_of_utc="2026-09-10T01:00:00Z",
            )


def test_state_store_symlink_fails_closed(tmp_path: Path):
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    link = tmp_path / "linked.json"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    with pytest.raises(ValueError, match="symlink"):
        hardening.collect_qualification_state_objects_strict(
            tmp_path,
            provider_id="roughtime.se",
            as_of_utc="2026-09-10T01:00:00Z",
        )
