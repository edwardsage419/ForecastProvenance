from __future__ import annotations

import base64
import copy
import hashlib
import os
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError
import forecast_trust_core.qualification_state_package_v2 as package_v2


from forecast_trust_core._roughtime_production_qualification import (
    CRITERIA_ID,
    CRITERIA_SHA256,
    DECISION_SIGNATURE_PROJECTION,
    REVIEW_CRITERIA,
    object_ref,
)
from forecast_trust_core._roughtime_profile import PROVIDER_BY_ID
from forecast_trust_core.canonical import canonical_json, content_hash, seal_object, verify_sealed_object
from forecast_trust_core.claim_authority_contract_gate_v1 import (
    validate_qualification_state_package_contract,
)
from forecast_trust_core.qualification_state_package_v2 import (
    QualificationStatePackageError,
    build_dynamic_qualification_state_package,
    verify_dynamic_qualification_state_package,
)
from forecast_trust_core.qualification_validation_contracts_v1 import (
    qualification_state_history_snapshot_signed_projection,
    build_qualification_state_history_snapshot,
)


AS_OF = "2026-09-20T00:00:00Z"
PROVIDER_REF = {"object_id": "provider:roughtime.se:v1", "content_sha256": "1" * 64}
DECISION_REF = {"object_id": "decision:roughtime.se:v1", "content_sha256": "2" * 64}
VERIFIER_REF = {"object_id": "verifier:qualification:v2", "content_sha256": "3" * 64}
MEMBER_PATHS = {
    "provider_source": "provider.json",
    "decision_transport": "decision.json",
    "review_transport": "review.json",
    "metadata_transport": "metadata.json",
    "history_transport": "history.json",
    "state_report": "events/state-report.json",
}


def _profile(provider_id: str = "roughtime.se") -> dict:
    provider = PROVIDER_BY_ID[provider_id]
    return seal_object(
        {
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
        },
        object_type="RoughtimeProductionProviderProfile",
        stable_context=provider_id,
    )


def _metadata(profile: dict, *, reviewed_at: str = "2026-09-18T00:00:00Z") -> dict:
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
            "lifecycle_status": "STANDARD",
            "rotation_notice_status": "NONE_PUBLISHED",
            "change_disposition": "UNCHANGED",
            "reason_codes": [],
        },
        object_type="RoughtimeProviderMetadataReview",
        stable_context=str(profile["provider_id"]),
    )


def _review(profile: dict, metadata: dict) -> dict:
    checks = [
        {
            "criterion_id": criterion_id,
            "disposition": (
                "NOT_APPLICABLE" if criterion_id == "PILOT_EXPERIMENTAL" else "PASS"
            ),
            "evidence_sha256s": (
                [] if criterion_id == "PILOT_EXPERIMENTAL" else ["3" * 64]
            ),
            "reason_codes": [],
        }
        for criterion_id in sorted(REVIEW_CRITERIA)
    ]
    return seal_object(
        {
            "schema_version": "1.0",
            "criteria_id": CRITERIA_ID,
            "criteria_sha256": CRITERIA_SHA256,
            "provider_id": profile["provider_id"],
            "provider_profile_ref": object_ref(profile),
            "evidence_manifest_sha256": "4" * 64,
            "execution_report_sha256": "5" * 64,
            "verifier_build_profile_sha256": profile["verifier_build_profile_sha256"],
            "verifier_binary_sha256": "6" * 64,
            "metadata_review_ref": object_ref(metadata),
            "executor_id": "owner:execution-event:1",
            "reviewer_id": "owner:independent-review-event:1",
            "review_basis_sha256": "7" * 64,
            "criteria_checks": checks,
            "evidence_complete": True,
            "deterministic_validation_passed": True,
            "strict_replay_passed": True,
            "blocking_findings": [],
            "review_result": "PASS",
            "reviewed_at": "2026-09-18T00:05:00Z",
        },
        object_type="RoughtimeQualificationReview",
        stable_context=str(profile["provider_id"]),
    )


def _decision(profile: dict, metadata: dict, review: dict) -> dict:
    signed_payload = {
        "criteria_id": CRITERIA_ID,
        "criteria_sha256": CRITERIA_SHA256,
        "provider_id": profile["provider_id"],
        "provider_profile_ref": object_ref(profile),
        "evidence_manifest_sha256": review["evidence_manifest_sha256"],
        "verifier_build_profile_sha256": review["verifier_build_profile_sha256"],
        "verifier_binary_sha256": review["verifier_binary_sha256"],
        "independent_review_ref": object_ref(review),
        "metadata_review_ref": object_ref(metadata),
        "decision_result": "PRODUCTION_QUALIFIED",
        "decision_timestamp": "2026-09-18T00:10:00Z",
        "authority_id": "authority:test-only:v1",
        "authority_public_key_sha256": "8" * 64,
    }
    return seal_object(
        {
            "schema_version": "1.0",
            "signature_projection": DECISION_SIGNATURE_PROJECTION,
            "signed_payload": signed_payload,
            "signed_payload_sha256": content_hash(signed_payload),
            "signature_algorithm": "ED25519",
            "authority_signature_base64": base64.b64encode(b"T" * 64).decode("ascii"),
        },
        object_type="RoughtimeQualificationDecision",
        stable_context=str(profile["provider_id"]),
    )


def _history(
    profile: dict,
    metadata_refs: list[dict],
    *,
    sequence: int = 0,
    through_as_of_utc: str = AS_OF,
    predecessor_snapshot_ref: dict | None = None,
    event_refs: list[dict] | None = None,
) -> dict:
    payload = {
        "schema_version": "1.0",
        "provider_profile_ref": object_ref(profile),
        "snapshot_sequence": sequence,
        "through_as_of_utc": through_as_of_utc,
        "metadata_review_refs": sorted(
            metadata_refs,
            key=lambda ref: (ref["object_id"], ref["content_sha256"]),
        ),
        "requalification_event_refs": sorted(
            event_refs or [],
            key=lambda ref: (ref["object_id"], ref["content_sha256"]),
        ),
        "authority_signature_base64": base64.b64encode(b"H" * 64).decode("ascii"),
    }
    if predecessor_snapshot_ref is not None:
        payload["predecessor_snapshot_ref"] = predecessor_snapshot_ref
    projection = {
        "schema_version": "1.0",
        "object_type": "QualificationStateHistorySnapshot",
        "provider_profile_ref": payload["provider_profile_ref"],
        "snapshot_sequence": sequence,
    }
    if predecessor_snapshot_ref is not None:
        projection["predecessor_snapshot_ref"] = predecessor_snapshot_ref
    projection.update(
        {
            "through_as_of_utc": through_as_of_utc,
            "metadata_review_refs": payload["metadata_review_refs"],
            "requalification_event_refs": payload["requalification_event_refs"],
        }
    )
    payload["signed_payload_sha256"] = content_hash(projection)
    return build_qualification_state_history_snapshot(payload)


def _unchecked_history(snapshot: dict, *, remove: tuple[str, ...] = (), **changes) -> dict:
    payload = {
        key: copy.deepcopy(value)
        for key, value in snapshot.items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    payload.update(changes)
    for field in remove:
        payload.pop(field, None)
    payload["signed_payload_sha256"] = content_hash(
        qualification_state_history_snapshot_signed_projection(payload)
    )
    return seal_object(
        payload,
        object_type="QualificationStateHistorySnapshot",
        stable_context="v1",
    )


def _state_report() -> dict:
    core = {
        "schema_version": "1.0",
        "object_type": "RoughtimeQualificationStateReport",
        "provider_id": "roughtime.se",
        "as_of_utc": AS_OF,
        "state": "PRODUCTION_QUALIFIED",
        "reason_codes": [],
        "active_requalification_event_refs": [],
    }
    return {**core, "report_sha256": content_hash(core)}


def _fixture_objects() -> dict[str, dict]:
    profile = _profile()
    metadata = _metadata(profile)
    review = _review(profile, metadata)
    decision = _decision(profile, metadata, review)
    history = _history(profile, [object_ref(metadata)])
    return {
        "provider.json": profile,
        "metadata.json": metadata,
        "review.json": review,
        "decision.json": decision,
        "history.json": history,
        "events/state-report.json": _state_report(),
    }


def _write_members(root: Path, objects: dict[str, dict] | None = None) -> dict[str, dict]:
    objects = objects or _fixture_objects()
    root.mkdir()
    for relative_path, obj in objects.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_json(obj))
    return objects


def _read_member(root: Path, relative_path: str) -> dict:
    return json.loads((root / relative_path).read_text(encoding="utf-8"))


def _state_report_member_sha256(root: Path) -> str:
    return hashlib.sha256((root / MEMBER_PATHS["state_report"]).read_bytes()).hexdigest()


def _build(
    root: Path,
    *,
    member_paths: dict[str, str] | None = None,
    provider_profile_ref: dict | None = None,
    qualification_decision_ref: dict | None = None,
    qualification_state_history_snapshot_ref: dict | None = None,
    as_of_utc: str = AS_OF,
    state_report_member_sha256: str | None = None,
) -> dict:
    if not root.exists():
        _write_members(root)
    defaults = _fixture_objects()
    return build_dynamic_qualification_state_package(
        root,
        provider_profile_ref=provider_profile_ref or object_ref(defaults["provider.json"]),
        qualification_decision_ref=(
            qualification_decision_ref or object_ref(defaults["decision.json"])
        ),
        qualification_state_history_snapshot_ref=(
            qualification_state_history_snapshot_ref
            or object_ref(defaults["history.json"])
        ),
        state_report_member_sha256=(
            state_report_member_sha256 or _state_report_member_sha256(root)
        ),
        as_of_utc=as_of_utc,
        member_paths=member_paths or MEMBER_PATHS,
    )


def _ref(package: dict) -> dict[str, str]:
    return {
        "object_id": package["object_id"],
        "content_sha256": package["content_sha256"],
    }


def _resolver_for(package: dict):
    expected_ref = _ref(package)
    serialized = canonical_json(package)

    def resolve(package_ref):
        if dict(package_ref) != expected_ref:
            raise KeyError("exact package reference not found")
        return serialized

    return resolve


def _expected_metadata(root: Path) -> dict:
    return {
        "schema_version": "2.0",
        "provider_profile_ref": object_ref(_read_member(root, "provider.json")),
        "qualification_decision_ref": object_ref(_read_member(root, "decision.json")),
        "qualification_state_history_snapshot_ref": object_ref(
            _read_member(root, "history.json")
        ),
        "state_report_member_sha256": _state_report_member_sha256(root),
        "as_of_utc": AS_OF,
    }


def _payload(package: dict) -> dict:
    return {
        key: copy.deepcopy(value)
        for key, value in package.items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }


def _reseal(package: dict, *, object_type: str = "DynamicQualificationStatePackage", **changes) -> dict:
    payload = _payload(package)
    payload.update(changes)
    return seal_object(payload, object_type=object_type, stable_context="v2")


def _verify(package: dict, root: Path, *, expected_metadata: dict | None = None) -> dict[str, str]:
    return verify_dynamic_qualification_state_package(
        _ref(package),
        root,
        resolve_package=_resolver_for(package),
        expected_metadata=expected_metadata,
    )


def _event(
    profile: dict,
    *,
    detected_at: str = "2026-09-19T12:00:00Z",
) -> dict:
    return seal_object(
        {
            "schema_version": "1.0",
            "provider_id": profile["provider_id"],
            "provider_profile_ref": object_ref(profile),
            "trigger_code": "STANDARDS_MIGRATION",
            "detected_at": detected_at,
            "evidence_sha256s": ["9" * 64],
            "reason_codes": ["RFC_PROFILE_CHANGED"],
        },
        object_type="RoughtimeRequalificationEvent",
        stable_context=str(profile["provider_id"]),
    )


def _replace_member(
    package: dict,
    root: Path,
    relative_path: str,
    obj: dict,
    *,
    package_changes: dict | None = None,
) -> dict:
    data = canonical_json(obj)
    (root / relative_path).write_bytes(data)
    members = copy.deepcopy(package["members"])
    member = next(item for item in members if item["relative_path"] == relative_path)
    member["byte_length"] = len(data)
    member["sha256"] = hashlib.sha256(data).hexdigest()
    return _reseal(package, members=members, **(package_changes or {}))


def _add_member(
    package: dict,
    root: Path,
    relative_path: str,
    obj: dict,
    *,
    role: str = "opaque-extra",
) -> dict:
    data = canonical_json(obj)
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    members = copy.deepcopy(package["members"])
    members.append(
        {
            "role": role,
            "relative_path": relative_path,
            "byte_length": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    )
    members.sort(key=lambda item: (item["role"], item["relative_path"]))
    return _reseal(package, members=members)


def _remove_member(package: dict, root: Path, relative_path: str) -> dict:
    (root / relative_path).unlink()
    members = [
        copy.deepcopy(item)
        for item in package["members"]
        if item["relative_path"] != relative_path
    ]
    return _reseal(package, members=members)


def _successor_package(root: Path) -> tuple[dict, dict[str, dict]]:
    objects = _fixture_objects()
    profile = objects["provider.json"]
    metadata_0 = objects["metadata.json"]
    metadata_1 = _metadata(profile, reviewed_at="2026-09-19T12:00:00Z")
    event_1 = _event(profile)
    history_0 = _history(
        profile,
        [object_ref(metadata_0)],
        through_as_of_utc="2026-09-19T00:00:00Z",
    )
    history_1 = _history(
        profile,
        [object_ref(metadata_0), object_ref(metadata_1)],
        sequence=1,
        predecessor_snapshot_ref=object_ref(history_0),
        event_refs=[object_ref(event_1)],
    )
    objects["metadata-1.json"] = metadata_1
    objects["event-1.json"] = event_1
    objects["history-0.json"] = history_0
    objects["history.json"] = history_1
    _write_members(root, objects)
    member_paths = {
        **MEMBER_PATHS,
        "metadata-successor": "metadata-1.json",
        "event-successor": "event-1.json",
        "history-predecessor": "history-0.json",
    }
    return (
        _build(
            root,
            member_paths=member_paths,
            qualification_state_history_snapshot_ref=object_ref(history_1),
        ),
        objects,
    )


def test_valid_package_is_standard_sealed_and_verified_by_exact_reference(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)

    verified_ref = _verify(package, root, expected_metadata=_expected_metadata(root))

    assert verified_ref == _ref(package)
    assert verify_sealed_object(package)
    assert package["object_id"] == f"dynamicqualificationstatepackage:v2:{package['payload_sha256'][:12]}"
    assert set(package) == {
        "schema_version",
        "object_type",
        "provider_profile_ref",
        "qualification_decision_ref",
        "qualification_state_history_snapshot_ref",
        "state_report_member_sha256",
        "as_of_utc",
        "members",
        "object_id",
        "payload_sha256",
        "content_sha256",
    }


def test_schema_accepts_the_standard_sealed_package(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    schema = json.loads(
        (Path(__file__).parents[1] / "schemas" / "dynamic_qualification_state_package_v2.schema.json").read_text(
            encoding="utf-8"
        )
    )

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(package)


def test_identical_builds_are_deterministic(tmp_path: Path):
    root = tmp_path / "root"
    first = _build(root)

    second = _build(root)

    assert second == first


@pytest.mark.parametrize("change", ["root_ref", "member_bytes"])
def test_semantic_rebinding_or_member_rewrite_is_rejected(tmp_path: Path, change: str):
    root = tmp_path / "root"
    _build(root)
    with pytest.raises((QualificationStatePackageError, ValueError)):
        if change == "root_ref":
            _build(
                root,
                provider_profile_ref={
                    "object_id": "provider:changed:v1",
                    "content_sha256": "a" * 64,
                },
            )
        else:
            (root / "provider.json").write_bytes(b'{"provider":"changed.example"}\n')
            _build(root)


def test_forged_payload_sha256_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    forged = copy.deepcopy(package)
    forged["payload_sha256"] = "0" * 64
    forged["content_sha256"] = content_hash(
        {key: value for key, value in forged.items() if key != "content_sha256"}
    )

    with pytest.raises(QualificationStatePackageError, match="payload_sha256"):
        _verify(forged, root)


def test_forged_content_sha256_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    forged = {**package, "content_sha256": "0" * 64}

    with pytest.raises(QualificationStatePackageError, match="content_sha256"):
        _verify(forged, root)


def test_forged_object_id_with_valid_internal_hashes_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    forged = copy.deepcopy(package)
    forged["object_id"] = "dynamicqualificationstatepackage:v2:forged"
    forged["content_sha256"] = content_hash(
        {key: value for key, value in forged.items() if key != "content_sha256"}
    )

    with pytest.raises(QualificationStatePackageError, match="object_id"):
        _verify(forged, root)


@pytest.mark.parametrize(
    ("package_factory", "message"),
    [
        (lambda package: _reseal(package, object_type="WrongPackageType"), "object_type"),
        (lambda package: _reseal(package, schema_version="3.0"), "schema_version"),
    ],
)
def test_wrong_contract_identity_is_rejected(tmp_path: Path, package_factory, message: str):
    root = tmp_path / "root"
    package = package_factory(_build(root))

    with pytest.raises(QualificationStatePackageError, match=message):
        _verify(package, root)


def test_id_only_resolution_is_rejected_before_resolver_use(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)

    with pytest.raises(QualificationStatePackageError, match="exact package reference"):
        verify_dynamic_qualification_state_package(
            {"object_id": package["object_id"]},
            root,
            resolve_package=lambda _ref: pytest.fail("resolver must not receive an ID-only reference"),
        )


def test_duplicate_json_keys_are_rejected_by_strict_package_parse(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    serialized = canonical_json(package).decode("utf-8")
    duplicate = serialized[:-1] + ',"schema_version":"2.0"}'

    with pytest.raises(QualificationStatePackageError, match="strict package JSON"):
        verify_dynamic_qualification_state_package(
            _ref(package),
            root,
            resolve_package=lambda _ref: duplicate,
        )


def test_missing_member_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    (root / "provider.json").unlink()

    with pytest.raises(QualificationStatePackageError, match="missing member"):
        _verify(package, root)


def test_member_hash_and_byte_length_are_independently_verified(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    path = root / "provider.json"
    path.write_bytes(b"X" + path.read_bytes()[1:])

    with pytest.raises(QualificationStatePackageError, match="hash mismatch"):
        _verify(package, root)

    path.write_bytes(path.read_bytes() + b"x")
    with pytest.raises(QualificationStatePackageError, match="byte-length mismatch"):
        _verify(package, root)


def test_unexpected_member_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    (root / "extra.json").write_bytes(b"{}")

    with pytest.raises(QualificationStatePackageError, match="unexpected extra file"):
        _verify(package, root)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda members: members.append(dict(members[0])), "duplicate path"),
        (lambda members: members.append({**members[0], "role": "another_role"}), "duplicate path"),
        (lambda members: members[0].update(relative_path="../outside"), "path traversal"),
        (lambda members: members[0].update(relative_path="/absolute"), "path traversal"),
        (lambda members: members[0].update(relative_path=r"events\state-report.json"), "POSIX path"),
    ],
)
def test_verifier_rejects_ambiguous_or_noncanonical_manifest_paths(
    tmp_path: Path, mutation, message: str
):
    root = tmp_path / "root"
    package = _build(root)
    members = copy.deepcopy(package["members"])
    mutation(members)
    forged = _reseal(package, members=members)

    with pytest.raises(QualificationStatePackageError, match=message):
        _verify(forged, root)


def test_verifier_rejects_symlink_member(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    target = root / "provider-target.json"
    (root / "provider.json").rename(target)
    (root / "provider.json").symlink_to(target.name)

    with pytest.raises(QualificationStatePackageError, match="symlink"):
        _verify(package, root)


def test_verifier_rejects_non_regular_member(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    (root / "provider.json").unlink()
    (root / "provider.json").mkdir()

    with pytest.raises(QualificationStatePackageError, match="non-regular"):
        _verify(package, root)


def test_state_report_transport_role_is_not_required(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    members = copy.deepcopy(package["members"])
    next(member for member in members if member["role"] == "state_report")["role"] = "other_report"
    forged = _reseal(
        package,
        members=sorted(members, key=lambda item: (item["role"], item["relative_path"])),
    )

    assert _verify(forged, root) == _ref(forged)


def test_duplicate_state_report_path_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    members = copy.deepcopy(package["members"])
    state_report = next(member for member in members if member["role"] == "state_report")
    members.append({**state_report, "relative_path": "provider.json"})
    forged = _reseal(package, members=members)

    with pytest.raises(QualificationStatePackageError, match="duplicate path"):
        _verify(forged, root)


def test_state_report_digest_mismatch_is_rejected_by_builder(tmp_path: Path):
    root = tmp_path / "root"
    _write_members(root)

    with pytest.raises(QualificationStatePackageError, match="state report"):
        _build(root, state_report_member_sha256="4" * 64)


@pytest.mark.parametrize(
    "member_document",
    [
        {"object_type": "DynamicQualificationStatePackage", "schema_version": "2.0"},
        {
            "object_type": "QualificationValidationResult",
            "qualification_state_package_ref": {
                "object_id": "dynamicqualificationstatepackage:v2:future",
                "content_sha256": "5" * 64,
            },
        },
        {
            "object_type": "DetachedAuthenticationEvidence",
            "qualification_state_package_ref": {
                "object_id": "dynamicqualificationstatepackage:v2:future",
                "content_sha256": "6" * 64,
            },
        },
    ],
)
def test_self_or_downstream_member_is_outside_local_families(
    tmp_path: Path,
    member_document: dict,
):
    root = tmp_path / "root"
    package = _build(root)
    forged = _add_member(package, root, "cycle.json", member_document)

    with pytest.raises(QualificationStatePackageError, match="allowed local family"):
        _verify(forged, root)


def test_reserved_package_document_path_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    package_path = root / "dynamic_qualification_state_package_v2.json"
    package_path.write_bytes(b"{}")

    with pytest.raises(QualificationStatePackageError, match="package definition"):
        build_dynamic_qualification_state_package(
            root,
            provider_profile_ref=PROVIDER_REF,
            qualification_decision_ref=DECISION_REF,
            qualification_state_history_snapshot_ref={
                "object_id": "qualificationstatehistorysnapshot:v1:fixture",
                "content_sha256": "4" * 64,
            },
            state_report_member_sha256=hashlib.sha256(package_path.read_bytes()).hexdigest(),
            as_of_utc=AS_OF,
            member_paths={"state_report": package_path.name},
        )


def test_historical_v1_package_contract_remains_accepted():
    v1_package = seal_object(
        {
            "schema_version": "1.0",
            "provider_id": "roughtime.se",
            "as_of_utc": AS_OF,
            "provider_profile_ref": PROVIDER_REF,
            "qualification_decision_ref": DECISION_REF,
            "qualification_evidence_manifest_sha256": "7" * 64,
            "qualification_verifier_contract_ref": VERIFIER_REF,
            "metadata_review_refs": [],
            "requalification_event_refs": [],
            "qualification_state_report_sha256": "8" * 64,
            "qualification_state": "PRODUCTION_QUALIFIED",
        },
        object_type="RoughtimeProviderQualificationStatePackage",
        stable_context="historical-v1-regression",
    )

    validate_qualification_state_package_contract(v1_package)


def test_expected_metadata_schema_version_must_match(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    expected = _expected_metadata(root)
    expected["schema_version"] = "3.0"

    with pytest.raises(QualificationStatePackageError, match="metadata mismatch"):
        _verify(package, root, expected_metadata=expected)


def test_resolver_cannot_substitute_a_different_exact_package(tmp_path: Path):
    root = tmp_path / "root"
    requested = _build(root)
    members = copy.deepcopy(requested["members"])
    members[0]["role"] = "substituted-role"
    members.sort(key=lambda item: (item["role"], item["relative_path"]))
    substituted = _reseal(requested, members=members)

    with pytest.raises(QualificationStatePackageError, match="exact package reference"):
        verify_dynamic_qualification_state_package(
            _ref(requested),
            root,
            resolve_package=lambda _ref: canonical_json(substituted),
        )


def test_verifier_rejects_resealed_state_report_rebinding(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    forged = _reseal(package, state_report_member_sha256="0" * 64)

    with pytest.raises(QualificationStatePackageError, match="state report"):
        _verify(forged, root)


def test_builder_rejects_member_swap_after_path_check(tmp_path: Path, monkeypatch):
    root = tmp_path / "root"
    _write_members(root)
    outside = tmp_path / "outside"
    _write_members(outside)
    outside_state = b'{"state":"OUTSIDE"}\n'
    (outside / MEMBER_PATHS["state_report"]).write_bytes(outside_state)
    target = root / MEMBER_PATHS["state_report"]
    hidden = tmp_path / "root-hidden"
    original_read_bytes = Path.read_bytes
    raced = False

    def racing_read_bytes(path: Path) -> bytes:
        nonlocal raced
        if path == target and not raced:
            raced = True
            root.rename(hidden)
            root.symlink_to(outside, target_is_directory=True)
            try:
                return original_read_bytes(path)
            finally:
                root.unlink()
                hidden.rename(root)
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", racing_read_bytes)

    with pytest.raises(QualificationStatePackageError, match="state report|changed"):
        _build(
            root,
            state_report_member_sha256=hashlib.sha256(outside_state).hexdigest(),
        )


def test_verifier_rejects_member_swap_after_path_check(tmp_path: Path, monkeypatch):
    root = tmp_path / "root"
    package = _build(root)
    original_provider = (root / "provider.json").read_bytes()
    (root / "provider.json").write_bytes(b'{"provider":"substitute.xx"}\n')
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "provider.json").write_bytes(original_provider)
    target = root / "provider.json"
    hidden = tmp_path / "root-hidden"
    original_read_bytes = Path.read_bytes
    raced = False

    def racing_read_bytes(path: Path) -> bytes:
        nonlocal raced
        if path == target and not raced:
            raced = True
            root.rename(hidden)
            root.symlink_to(outside, target_is_directory=True)
            try:
                return original_read_bytes(path)
            finally:
                root.unlink()
                hidden.rename(root)
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", racing_read_bytes)

    with pytest.raises(QualificationStatePackageError, match="byte-length mismatch|hash mismatch|changed|symlink"):
        _verify(package, root)


def test_root_enumeration_error_is_fail_closed(tmp_path: Path):
    root = tmp_path / "root"
    _write_members(root)
    concealed = root / "concealed"
    concealed.mkdir()
    (concealed / "unexpected.json").write_bytes(b"{}")
    concealed.chmod(0)
    try:
        with pytest.raises(QualificationStatePackageError, match="enumerate package root"):
            _build(root)
    finally:
        concealed.chmod(0o700)


def test_builder_rejects_symlink_member(tmp_path: Path):
    root = tmp_path / "root"
    _write_members(root)
    target = root / "provider-target.json"
    (root / "provider.json").rename(target)
    (root / "provider.json").symlink_to(target.name)

    with pytest.raises(QualificationStatePackageError, match="symlink"):
        _build(root)


def test_builder_rejects_non_regular_member(tmp_path: Path):
    root = tmp_path / "root"
    _write_members(root)
    (root / "provider.json").unlink()
    (root / "provider.json").mkdir()

    with pytest.raises(QualificationStatePackageError, match="non-regular"):
        _build(root)


@pytest.mark.parametrize(
    "relative_path",
    [
        ".",
        "./provider.json",
        "nested//provider.json",
        "provider.json/",
    ],
)
def test_schema_rejects_runtime_noncanonical_member_paths(
    tmp_path: Path, relative_path: str
):
    root = tmp_path / "root"
    package = _build(root)
    members = copy.deepcopy(package["members"])
    members[0]["relative_path"] = relative_path
    forged = _reseal(package, members=members)
    schema = json.loads(
        (
            Path(__file__).parents[1]
            / "schemas"
            / "dynamic_qualification_state_package_v2.schema.json"
        ).read_text(encoding="utf-8")
    )

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(forged)


def test_runtime_rejects_single_dot_member_path(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    members = copy.deepcopy(package["members"])
    members[0]["relative_path"] = "."
    forged = _reseal(package, members=members)

    with pytest.raises(QualificationStatePackageError, match="POSIX path|path traversal"):
        _verify(forged, root)


def _package_schema_validator() -> Draft202012Validator:
    schema = json.loads(
        (
            Path(__file__).parents[1]
            / "schemas"
            / "dynamic_qualification_state_package_v2.schema.json"
        ).read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _frozen_projection_package() -> dict:
    return seal_object(
        {
            "schema_version": "2.0",
            "provider_profile_ref": PROVIDER_REF,
            "qualification_decision_ref": DECISION_REF,
            "qualification_state_history_snapshot_ref": {
                "object_id": "qualificationstatehistorysnapshot:v1:fixture",
                "content_sha256": "4" * 64,
            },
            "state_report_member_sha256": "5" * 64,
            "as_of_utc": AS_OF,
            "members": [
                {
                    "role": "opaque-transport-label",
                    "relative_path": "member.json",
                    "byte_length": 2,
                    "sha256": "6" * 64,
                }
            ],
        },
        object_type="DynamicQualificationStatePackage",
        stable_context="v2",
    )


def test_schema_accepts_exact_frozen_package_projection():
    _package_schema_validator().validate(_frozen_projection_package())


@pytest.mark.parametrize(
    "candidate_field",
    ["verifier_contract_ref", "state_report_sha256"],
)
def test_schema_rejects_removed_candidate_projection_fields(candidate_field: str):
    package = _frozen_projection_package()
    payload = _payload(package)
    payload[candidate_field] = VERIFIER_REF if candidate_field.endswith("_ref") else "7" * 64
    candidate = seal_object(
        payload,
        object_type="DynamicQualificationStatePackage",
        stable_context="v2",
    )
    with pytest.raises(ValidationError):
        _package_schema_validator().validate(candidate)


def test_schema_requires_state_report_member_sha256():
    package = _frozen_projection_package()
    payload = _payload(package)
    del payload["state_report_member_sha256"]
    missing = seal_object(payload, object_type="DynamicQualificationStatePackage", stable_context="v2")

    with pytest.raises(ValidationError):
        _package_schema_validator().validate(missing)


def _replace_selected_history(package: dict, root: Path, snapshot: dict) -> dict:
    return _replace_member(
        package,
        root,
        "history.json",
        snapshot,
        package_changes={"qualification_state_history_snapshot_ref": object_ref(snapshot)},
    )


def test_transport_roles_cannot_establish_semantic_identity(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    members = copy.deepcopy(package["members"])
    for index, member in enumerate(members):
        member["role"] = f"opaque-{index:02d}"
    members.sort(key=lambda item: (item["role"], item["relative_path"]))

    rebound = _reseal(package, members=members)

    assert _verify(rebound, root) == _ref(rebound)


def test_state_report_is_selected_by_raw_member_digest(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    selected_path = next(
        member["relative_path"]
        for member in package["members"]
        if member["sha256"] == package["state_report_member_sha256"]
    )
    members = copy.deepcopy(package["members"])
    for member in members:
        member["role"] = (
            "provider-looking-label"
            if member["relative_path"] == selected_path
            else f"transport-{member['relative_path'].replace('/', '-')}"
        )
    members.sort(key=lambda item: (item["role"], item["relative_path"]))
    rebound = _reseal(package, members=members)

    assert _verify(rebound, root) == _ref(rebound)


def test_zero_state_report_digest_matches_are_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    forged = _reseal(package, state_report_member_sha256="0" * 64)

    with pytest.raises(QualificationStatePackageError, match="state report"):
        _verify(forged, root)


def test_multiple_state_report_digest_matches_are_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    duplicated = _add_member(
        package, root, "events/state-report-copy.json", _state_report(), role="copy"
    )

    with pytest.raises(QualificationStatePackageError, match="state report"):
        _verify(duplicated, root)


def test_arbitrary_json_member_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    forged = _add_member(
        package,
        root,
        "operator-note.json",
        {"note": "not a package-local semantic object"},
    )

    with pytest.raises(QualificationStatePackageError, match="allowed local family"):
        _verify(forged, root)


@pytest.mark.parametrize(
    "relative_path",
    ["provider.json", "decision.json", "history.json", "review.json", "metadata.json"],
)
def test_missing_referenced_local_object_is_rejected(tmp_path: Path, relative_path: str):
    root = tmp_path / "root"
    package = _build(root)
    missing = _remove_member(package, root, relative_path)

    with pytest.raises(QualificationStatePackageError, match="missing referenced local"):
        _verify(missing, root)


def test_extra_unreachable_allowed_object_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    profile = _read_member(root, "provider.json")
    extra = _add_member(
        package,
        root,
        "unreachable-event.json",
        _event(profile, detected_at="2026-09-19T13:00:00Z"),
    )

    with pytest.raises(QualificationStatePackageError) as caught:
        _verify(extra, root)
    assert (
        caught.value.stage
        is package_v2.QualificationStatePackageStage.HISTORY_COMPLETENESS_INVALID
    )


def test_duplicate_physical_copy_of_exact_ref_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    duplicate = _add_member(
        package, root, "provider-copy.json", _read_member(root, "provider.json")
    )

    with pytest.raises(QualificationStatePackageError, match="duplicate ExactRef"):
        _verify(duplicate, root)


def test_same_object_id_with_conflicting_content_hash_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    profile = _read_member(root, "provider.json")
    payload = {
        key: value
        for key, value in profile.items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    payload["verifier_build_profile_sha256"] = "a" * 64
    conflict = seal_object(
        payload,
        object_type="RoughtimeProductionProviderProfile",
        stable_context="conflict",
        semantic_id=profile["object_id"],
    )
    forged = _add_member(package, root, "profile-conflict.json", conflict)

    with pytest.raises(QualificationStatePackageError, match="object_id.*different content"):
        _verify(forged, root)


def test_state_report_semantic_hash_tampering_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    report = _read_member(root, "events/state-report.json")
    report["reason_codes"] = ["TAMPERED"]
    data = canonical_json(report)
    forged = _replace_member(
        package,
        root,
        "events/state-report.json",
        report,
        package_changes={"state_report_member_sha256": hashlib.sha256(data).hexdigest()},
    )

    with pytest.raises(QualificationStatePackageError, match="state report"):
        _verify(forged, root)


def test_external_and_static_authorities_are_not_local_members(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)

    assert {member["relative_path"] for member in package["members"]} == set(
        MEMBER_PATHS.values()
    )
    assert _verify(package, root) == _ref(package)


def test_sequence_zero_history_snapshot_is_accepted(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)

    assert _verify(package, root) == _ref(package)


def test_sequence_zero_predecessor_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    history = _read_member(root, "history.json")
    invalid = _unchecked_history(
        history,
        predecessor_snapshot_ref={
            "object_id": "qualificationstatehistorysnapshot:v1:forbidden",
            "content_sha256": "a" * 64,
        },
    )
    forged = _replace_selected_history(package, root, invalid)

    with pytest.raises(QualificationStatePackageError, match="sequence zero"):
        _verify(forged, root)


def test_successor_history_chain_and_record_edges_are_accepted(tmp_path: Path):
    root = tmp_path / "root"
    package, _objects = _successor_package(root)

    assert _verify(package, root) == _ref(package)


def test_successor_missing_predecessor_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package, objects = _successor_package(root)
    invalid = _unchecked_history(
        objects["history.json"], remove=("predecessor_snapshot_ref",)
    )
    forged = _replace_selected_history(package, root, invalid)

    with pytest.raises(QualificationStatePackageError, match="predecessor"):
        _verify(forged, root)


def test_successor_sequence_gap_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package, objects = _successor_package(root)
    invalid = _unchecked_history(objects["history.json"], snapshot_sequence=2)
    forged = _replace_selected_history(package, root, invalid)

    with pytest.raises(QualificationStatePackageError, match="sequence"):
        _verify(forged, root)


def test_successor_provider_mismatch_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package, objects = _successor_package(root)
    other_profile = _profile("time.txryan.com")
    package = _add_member(package, root, "other-provider.json", other_profile)
    invalid = _unchecked_history(
        objects["history.json"], provider_profile_ref=object_ref(other_profile)
    )
    forged = _replace_selected_history(package, root, invalid)

    with pytest.raises(QualificationStatePackageError, match="provider"):
        _verify(forged, root)


def test_successor_nonincreasing_cutoff_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package, objects = _successor_package(root)
    invalid = _unchecked_history(
        objects["history.json"],
        through_as_of_utc=objects["history-0.json"]["through_as_of_utc"],
    )
    forged = _replace_selected_history(package, root, invalid)

    with pytest.raises(QualificationStatePackageError, match="cutoff|through_as_of"):
        _verify(forged, root)


def test_successor_record_removal_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package, objects = _successor_package(root)
    invalid = _unchecked_history(
        objects["history.json"],
        metadata_review_refs=[object_ref(objects["metadata-1.json"])],
    )
    forged = _replace_selected_history(package, root, invalid)

    with pytest.raises(QualificationStatePackageError, match="record removal|subset"):
        _verify(forged, root)


@pytest.mark.parametrize(
    "reviewed_at",
    ["2026-09-19T00:00:00Z", "2026-09-21T00:00:00Z"],
)
def test_new_history_record_must_be_strictly_within_successor_window(
    tmp_path: Path,
    reviewed_at: str,
):
    root = tmp_path / "root"
    package, objects = _successor_package(root)
    replacement_metadata = _metadata(objects["provider.json"], reviewed_at=reviewed_at)
    package = _replace_member(package, root, "metadata-1.json", replacement_metadata)
    replacement_history = _history(
        objects["provider.json"],
        [object_ref(objects["metadata.json"]), object_ref(replacement_metadata)],
        sequence=1,
        predecessor_snapshot_ref=object_ref(objects["history-0.json"]),
        event_refs=[object_ref(objects["event-1.json"])],
    )
    forged = _replace_selected_history(package, root, replacement_history)

    with pytest.raises(QualificationStatePackageError, match="record timestamp"):
        _verify(forged, root)


@pytest.mark.parametrize("relative_path", ["metadata-1.json", "event-1.json"])
def test_snapshot_record_edges_require_local_members(tmp_path: Path, relative_path: str):
    root = tmp_path / "root"
    package, _objects = _successor_package(root)
    missing = _remove_member(package, root, relative_path)

    with pytest.raises(QualificationStatePackageError, match="missing referenced local"):
        _verify(missing, root)


def test_selected_snapshot_cutoff_must_equal_package_cutoff(tmp_path: Path):
    root = tmp_path / "root"
    package, _objects = _successor_package(root)
    forged = _reseal(package, as_of_utc="2026-09-21T00:00:00Z")

    with pytest.raises(QualificationStatePackageError, match="package cutoff"):
        _verify(forged, root)


def test_successor_record_substitution_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package, objects = _successor_package(root)
    substitute = _metadata(
        objects["provider.json"],
        reviewed_at="2026-09-19T10:00:00Z",
    )
    package = _add_member(package, root, "metadata-substitute.json", substitute)
    invalid = _unchecked_history(
        objects["history.json"],
        metadata_review_refs=sorted(
            [
                object_ref(substitute),
                object_ref(objects["metadata-1.json"]),
            ],
            key=lambda ref: (ref["object_id"], ref["content_sha256"]),
        ),
    )
    forged = _replace_selected_history(package, root, invalid)

    with pytest.raises(QualificationStatePackageError, match="record removal|subset"):
        _verify(forged, root)


def test_second_physical_copy_of_shared_semantic_object_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    duplicate = _add_member(
        package,
        root,
        "review-copy.json",
        _read_member(root, "review.json"),
        role="diagnostic-copy",
    )

    with pytest.raises(QualificationStatePackageError, match="duplicate ExactRef"):
        _verify(duplicate, root)


def test_fifo_special_file_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    package = _build(root)
    (root / "provider.json").unlink()
    os.mkfifo(root / "provider.json")

    with pytest.raises(QualificationStatePackageError, match="non-regular"):
        _verify(package, root)


def test_predecessor_exactref_cycle_is_rejected(
    tmp_path: Path,
    monkeypatch,
):
    import forecast_trust_core.canonical as canonical_module

    monkeypatch.setattr(canonical_module, "sha256_hex", lambda _data: "a" * 64)
    objects = _fixture_objects()
    profile = objects["provider.json"]
    metadata = objects["metadata.json"]
    cyclic_ref = {
        "object_id": "qualificationstatehistorysnapshot:v1:aaaaaaaaaaaa",
        "content_sha256": "a" * 64,
    }
    cyclic_history = _history(
        profile,
        [object_ref(metadata)],
        sequence=1,
        predecessor_snapshot_ref=cyclic_ref,
    )
    assert object_ref(cyclic_history) == cyclic_ref
    objects["history.json"] = cyclic_history
    root = tmp_path / "root"
    _write_members(root, objects)

    with pytest.raises(QualificationStatePackageError, match="cycle"):
        build_dynamic_qualification_state_package(
            root,
            provider_profile_ref=object_ref(profile),
            qualification_decision_ref=object_ref(objects["decision.json"]),
            qualification_state_history_snapshot_ref=cyclic_ref,
            state_report_member_sha256=_state_report_member_sha256(root),
            as_of_utc=AS_OF,
            member_paths=MEMBER_PATHS,
        )


def test_staged_closure_returns_typed_package_inputs_before_history_validation(
    tmp_path: Path,
):
    root = tmp_path / "root"
    package = _build(root)

    closure = package_v2.build_package_closure(
        _ref(package),
        root,
        parsed_package=package,
    )

    assert isinstance(closure, package_v2.PackageClosureResult)
    assert closure.package_ref == _ref(package)
    assert closure.parsed_package == package
    assert closure.provider_profile_ref == package["provider_profile_ref"]
    assert closure.qualification_decision_ref == package["qualification_decision_ref"]
    assert (
        closure.selected_history_snapshot_ref
        == package["qualification_state_history_snapshot_ref"]
    )
    assert closure.qualification_review_ref == object_ref(closure.qualification_review)
    assert closure.ordered_history_snapshot_chain == (closure.selected_history_snapshot,)
    assert closure.metadata_reviews == (_read_member(root, "metadata.json"),)
    assert closure.requalification_events == ()
    assert closure.state_report == _read_member(root, "events/state-report.json")
    assert closure.state_report_member_sha256 == package["state_report_member_sha256"]
    assert closure.as_of_utc == AS_OF

def test_staged_closure_exposes_package_schema_stage_without_message_parsing(
    tmp_path: Path,
):
    root = tmp_path / "root"
    package = _build(root)
    malformed = _reseal(package, schema_version="9.9")

    with pytest.raises(QualificationStatePackageError) as caught:
        package_v2.build_package_closure(
            _ref(malformed),
            root,
            parsed_package=malformed,
        )

    assert (
        caught.value.stage
        is package_v2.QualificationStatePackageStage.PACKAGE_SCHEMA_INVALID
    )


def test_staged_closure_maps_each_prehistory_failure_from_its_code_path(
    tmp_path: Path,
):
    identity_root = tmp_path / "identity"
    identity_package = _build(identity_root)
    wrong_ref = {
        "object_id": identity_package["object_id"],
        "content_sha256": "0" * 64,
    }

    manifest_root = tmp_path / "manifest"
    manifest_package = _build(manifest_root)
    malformed_manifest = _reseal(
        manifest_package,
        members=list(reversed(manifest_package["members"])),
    )

    closure_root = tmp_path / "closure"
    closure_package = _build(closure_root)
    (closure_root / "provider.json").write_bytes(b"tampered")

    input_root = tmp_path / "input"
    input_package = _build(input_root)
    profile = _read_member(input_root, "provider.json")
    profile_payload = {
        key: value
        for key, value in profile.items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    profile_payload["criteria_id"] = "INVALID"
    invalid_profile = seal_object(
        profile_payload,
        object_type="RoughtimeProductionProviderProfile",
        stable_context=str(profile["provider_id"]),
    )
    invalid_input = _replace_member(
        input_package,
        input_root,
        "provider.json",
        invalid_profile,
        package_changes={"provider_profile_ref": object_ref(invalid_profile)},
    )

    report_root = tmp_path / "report"
    report_package = _build(report_root)
    report = _read_member(report_root, "events/state-report.json")
    report["report_sha256"] = "0" * 64
    report_bytes = canonical_json(report)
    invalid_report = _replace_member(
        report_package,
        report_root,
        "events/state-report.json",
        report,
        package_changes={
            "state_report_member_sha256": hashlib.sha256(report_bytes).hexdigest()
        },
    )

    cases = (
        (
            identity_package,
            identity_root,
            wrong_ref,
            package_v2.QualificationStatePackageStage.PACKAGE_SEALED_IDENTITY_OR_REFERENCE_INVALID,
        ),
        (
            malformed_manifest,
            manifest_root,
            _ref(malformed_manifest),
            package_v2.QualificationStatePackageStage.PACKAGE_MEMBER_MANIFEST_INVALID,
        ),
        (
            closure_package,
            closure_root,
            _ref(closure_package),
            package_v2.QualificationStatePackageStage.PACKAGE_MEMBER_CLOSURE_INVALID,
        ),
        (
            invalid_input,
            input_root,
            _ref(invalid_input),
            package_v2.QualificationStatePackageStage.QUALIFICATION_INPUT_SCHEMA_INVALID,
        ),
        (
            invalid_report,
            report_root,
            _ref(invalid_report),
            package_v2.QualificationStatePackageStage.STATE_REPORT_MEMBER_INVALID,
        ),
    )
    for candidate, root, candidate_ref, expected_stage in cases:
        with pytest.raises(QualificationStatePackageError) as caught:
            package_v2.build_package_closure(
                candidate_ref,
                root,
                parsed_package=candidate,
            )
        assert caught.value.stage is expected_stage
def test_history_structural_failures_are_deferred_to_distinct_typed_helpers(
    tmp_path: Path,
):
    cutoff_root = tmp_path / "cutoff"
    cutoff_package, _ = _successor_package(cutoff_root)
    cutoff_package = _reseal(
        cutoff_package,
        as_of_utc="2026-09-21T00:00:00Z",
    )
    cutoff_closure = package_v2.build_package_closure(
        _ref(cutoff_package),
        cutoff_root,
        parsed_package=cutoff_package,
    )
    with pytest.raises(QualificationStatePackageError) as cutoff_error:
        package_v2.validate_history_cutoff(cutoff_closure)
    assert (
        cutoff_error.value.stage
        is package_v2.QualificationStatePackageStage.HISTORY_CUTOFF_INVALID
    )

    succession_root = tmp_path / "succession"
    succession_package, succession_objects = _successor_package(succession_root)
    sequence_gap = _unchecked_history(
        succession_objects["history.json"],
        snapshot_sequence=2,
    )
    succession_package = _replace_selected_history(
        succession_package,
        succession_root,
        sequence_gap,
    )
    succession_closure = package_v2.build_package_closure(
        _ref(succession_package),
        succession_root,
        parsed_package=succession_package,
    )
    with pytest.raises(QualificationStatePackageError) as succession_error:
        package_v2.validate_history_succession(succession_closure)
    assert (
        succession_error.value.stage
        is package_v2.QualificationStatePackageStage.HISTORY_SUCCESSION_INVALID
    )

    completeness_root = tmp_path / "completeness"
    completeness_package, completeness_objects = _successor_package(completeness_root)
    record_removal = _unchecked_history(
        completeness_objects["history.json"],
        metadata_review_refs=[
            object_ref(completeness_objects["metadata-1.json"])
        ],
    )
    completeness_package = _replace_selected_history(
        completeness_package,
        completeness_root,
        record_removal,
    )
    completeness_closure = package_v2.build_package_closure(
        _ref(completeness_package),
        completeness_root,
        parsed_package=completeness_package,
    )
    with pytest.raises(QualificationStatePackageError) as completeness_error:
        package_v2.validate_history_completeness(completeness_closure)
    assert (
        completeness_error.value.stage
        is package_v2.QualificationStatePackageStage.HISTORY_COMPLETENESS_INVALID
    )


def test_valid_history_passes_each_separate_structural_helper(tmp_path: Path):
    root = tmp_path / "root"
    package, _ = _successor_package(root)
    closure = package_v2.build_package_closure(
        _ref(package),
        root,
        parsed_package=package,
    )

    package_v2.validate_history_cutoff(closure)
    package_v2.validate_history_succession(closure)
    package_v2.validate_history_completeness(closure)


@pytest.mark.parametrize(
    "case",
    ["missing_successor_predecessor", "sequence_zero_predecessor"],
)
def test_predecessor_shape_is_deferred_to_history_succession(
    tmp_path: Path,
    case: str,
):
    root = tmp_path / "root"
    package, objects = _successor_package(root)
    if case == "missing_successor_predecessor":
        invalid = _unchecked_history(
            objects["history.json"],
            remove=("predecessor_snapshot_ref",),
        )
    else:
        invalid = _unchecked_history(
            objects["history.json"],
            snapshot_sequence=0,
        )
    package = _replace_selected_history(package, root, invalid)

    closure = package_v2.build_package_closure(
        _ref(package),
        root,
        parsed_package=package,
    )
    with pytest.raises(QualificationStatePackageError) as caught:
        package_v2.validate_history_succession(closure)

    assert (
        caught.value.stage
        is package_v2.QualificationStatePackageStage.HISTORY_SUCCESSION_INVALID
    )
def test_predecessor_cycle_is_deferred_to_history_succession(tmp_path: Path):
    from dataclasses import replace

    root = tmp_path / "root"
    package, _ = _successor_package(root)
    closure = package_v2.build_package_closure(
        _ref(package),
        root,
        parsed_package=package,
    )
    cyclic_closure = replace(closure, history_predecessor_cycle=True)

    with pytest.raises(QualificationStatePackageError) as caught:
        package_v2.validate_history_succession(cyclic_closure)

    assert (
        caught.value.stage
        is package_v2.QualificationStatePackageStage.HISTORY_SUCCESSION_INVALID
    )

def test_staged_closure_defers_external_evidence_binding_but_wrapper_preserves_it(
    tmp_path: Path,
):
    root = tmp_path / "package"
    objects = _write_members(root)
    package = _build(root)

    review_payload = {
        key: copy.deepcopy(value)
        for key, value in objects["review.json"].items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    review_payload["evidence_manifest_sha256"] = "9" * 64
    changed_review = seal_object(
        review_payload,
        object_type="RoughtimeQualificationReview",
        stable_context="roughtime.se",
    )

    decision_payload = {
        key: copy.deepcopy(value)
        for key, value in objects["decision.json"].items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    decision_payload["signed_payload"]["independent_review_ref"] = object_ref(
        changed_review
    )
    decision_payload["signed_payload_sha256"] = content_hash(
        decision_payload["signed_payload"]
    )
    changed_decision = seal_object(
        decision_payload,
        object_type="RoughtimeQualificationDecision",
        stable_context="roughtime.se",
    )

    package = _replace_member(package, root, "review.json", changed_review)
    package = _replace_member(
        package,
        root,
        "decision.json",
        changed_decision,
        package_changes={"qualification_decision_ref": object_ref(changed_decision)},
    )

    closure = package_v2.build_package_closure(
        _ref(package),
        root,
        parsed_package=package,
    )
    assert closure.qualification_decision_ref == object_ref(changed_decision)

    with pytest.raises(QualificationStatePackageError) as captured:
        verify_dynamic_qualification_state_package(
            _ref(package),
            root,
            resolve_package=_resolver_for(package),
        )
    assert captured.value.stage is package_v2.QualificationStatePackageStage.QUALIFICATION_INPUT_SCHEMA_INVALID
