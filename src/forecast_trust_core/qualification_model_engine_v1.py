"""Keyless synthetic qualification engine; never real qualification authority.

Shares byte/member/history kernels and exact admission with the native pipeline.
Model authentication facts replace external signatures only. There is no key,
signature projection, message construction or cryptographic backend in this lane.
"""
from copy import deepcopy
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import os

from . import qualification_state_package_v2 as native_closure
from .canonical import canonical_json, parse_json_strict, verify_sealed_object, content_hash
from .authority_primitives_v1 import ExactRef
from .calendar_parser_v1 import utc
from .core import Check
from .replay_records_v1 import reduce_checks
from .qualification_validation_contracts_v1 import build_qualification_validation_result, validate_qualification_validation_result
from ._roughtime_production_qualification import REVIEW_CRITERIA
from .canonical import sha256_hex, require_utc_timestamp

DERIVED = {"object_id", "payload_sha256", "content_sha256", "object_type"}
MODEL_CRITERIA = "M1_QUALIFICATION_CRITERIA_V1"
SCHEMAS = {
    "Formation": {"model_only", "provider", "profile_ref", "metadata_ref", "review_ref", "formed_at", "permission", "authority_role", "criteria", "observation_refs"},
    "Review": {"model_only", "provider", "metadata_ref", "reviewed_at", "executor", "reviewer", "observation_refs", "criteria", "result", "criteria_evidence", "blocking_findings", "runtime", "merkle_root", "failure_probe", "schema_probe", "model_authentication"},
    "Metadata": {"model_only", "provider", "provider_profile_ref", "retrieved_at", "reviewed_at", "permission", "service_state", "change_disposition", "operator_identity", "endpoint", "protocol", "source_capture", "common_dependencies", "standards", "pilot", "operational_samples"},
    "Observation": {"model_only", "provider", "observed_at", "nonce", "wire_version", "sent_us", "midpoint_us", "radius_us", "received_us", "decoded"},
    "Event": {"model_only", "provider", "provider_profile_ref", "detected_at", "effective_at", "kind"},
    "History": {"model_only", "provider_profile_ref", "snapshot_sequence", "through_as_of_utc", "metadata_review_refs", "requalification_event_refs"},
    "Authentication": {"model_only", "subject_ref", "provider", "authority_role", "action"},
    "StateReport": {"model_only", "provider", "as_of_utc", "state", "decision_ref", "history_ref"},
}

def valid_schema(obj, family):
    fields = SCHEMAS[family] | ({"predecessor_snapshot_ref"} if family == "History" and "predecessor_snapshot_ref" in obj else set())
    if obj.get("object_type") != "SyntheticQualification" + family or obj.get("model_only") is not True or set(obj) - DERIVED != fields:
        return False
    try:
        for name in ("formed_at", "reviewed_at", "retrieved_at", "observed_at", "detected_at", "effective_at", "through_as_of_utc", "as_of_utc"):
            if name in obj: require_utc_timestamp(obj[name])
        if family == "History":
            if type(obj["snapshot_sequence"]) is not int or obj["snapshot_sequence"] < 0: return False
            for name in ("metadata_review_refs", "requalification_event_refs"):
                values = [ExactRef.from_mapping(x) for x in obj[name]]
                if len(values) != len(set(values)): return False
        return True
    except (ValueError, TypeError, KeyError):
        return False

def check(name, ok, reason):
    return Check(name, "UNKNOWN" if ok is None else "PASS" if ok else "FAIL", reason)

def ref(obj):
    return ExactRef(obj["object_id"], obj["content_sha256"])

def _validate_observation(obs, provider, number, retrieved, reviewed):
    try:
        numeric = all(type(obs[x]) is int for x in ("sent_us", "midpoint_us", "radius_us", "received_us"))
        ok = valid_schema(obs, "Observation") and numeric and 0 <= obs["radius_us"] <= 1000 and obs["sent_us"] <= obs["midpoint_us"] - obs["radius_us"] <= obs["midpoint_us"] + obs["radius_us"] <= obs["received_us"]
        ok = ok and obs["provider"] == provider and obs["nonce"] == f"model-{provider}-repeat-{number}" and obs["wire_version"] == "MODEL_RT_V1"
        ok = ok and obs["decoded"] == {"midpoint_us": obs["midpoint_us"], "radius_us": obs["radius_us"], "nonce": obs["nonce"]}
        return ok and retrieved <= utc(obs["observed_at"]) <= reviewed
    except (ValueError, KeyError, TypeError):
        return False

def model_merkle_root(observations):
    # Retained model tree commits every canonical raw exchange, in fixed order.
    # This is SHA-256 coverage capability, not Roughtime signature verification.
    level = [bytes.fromhex(sha256_hex(canonical_json(o))) for o in observations]
    if not level: return ""
    while len(level) > 1:
        if len(level) % 2: level.append(level[-1])
        level = [bytes.fromhex(sha256_hex(level[i] + level[i+1])) for i in range(0, len(level), 2)]
    return level[0].hex()

def validate_model_formation(formation, profile, review, metadata, observations, *, as_of):
    """Causal model criteria checks, including retained raw exchanges and review."""
    checks = []
    try:
        provider = profile["name"]
        formed, reviewed, retrieved = map(utc, (formation["formed_at"], review["reviewed_at"], metadata["retrieved_at"]))
        checks += [
            check("formation-input-fields", all(valid_schema(obj, family) for obj, family in
                ((formation, "Formation"), (review, "Review"), (metadata, "Metadata"))) and all(valid_schema(o, "Observation") for o in observations), "MODEL_FORMATION_INPUT_INVALID"),
            check("formation-role", formation["authority_role"] == "MODEL_QUALIFICATION_OWNER" and
                profile["authority_role"] == formation["authority_role"] and formation["provider"] == review["provider"] == metadata["provider"] == provider and metadata["provider_profile_ref"] == ref(profile).to_dict(),
                "MODEL_FORMATION_AUTHORITY_INVALID"),
            check("formation-binding", formation["profile_ref"] == ref(profile).to_dict() and
                formation["review_ref"] == ref(review).to_dict() and review["metadata_ref"] == ref(metadata).to_dict() and
                formation["metadata_ref"] == ref(metadata).to_dict(), "MODEL_FORMATION_EXACT_BINDING_INVALID"),
            check("criteria", formation["criteria"] == review["criteria"] == MODEL_CRITERIA and review["result"] == "PASS",
                "MODEL_FORMATION_CRITERIA_INVALID"),
            check("permission", formation["permission"] == metadata["permission"] == "AFFIRMATIVE" and
                profile["permission"] == "MODEL_EXPLICIT" and metadata["service_state"] == "ACTIVE" and
                metadata["change_disposition"] == "UNCHANGED", "MODEL_PERMISSION_OR_SERVICE_INVALID"),
            check("freshness", retrieved <= reviewed <= formed <= utc(as_of) and formed <= retrieved + timedelta(days=90) and
                utc(as_of) <= retrieved + timedelta(days=90), "MODEL_FORMATION_FRESHNESS_INVALID"),
            check("independent-review", review["reviewer"] != review["executor"] and
                review["reviewer"] == "model-independent-reviewer-" + provider and
                review["executor"] == profile["independence"], "MODEL_FORMATION_REVIEW_NOT_INDEPENDENT"),
        ]
        obsrefs = [ref(x).to_dict() for x in observations]
        checks.append(check("repeatability-set", formation["observation_refs"] == review["observation_refs"] == obsrefs and len(obsrefs) == 3 and
            len({x["nonce"] for x in observations}) == 3, "MODEL_REPEATABILITY_COVERAGE_INVALID"))
        values = []
        for number, obs in enumerate(observations):
            ok = _validate_observation(obs, provider, number, retrieved, reviewed)
            values.append(ok)
        checks.append(check("interop-repeatability", len(values) == 3 and all(values), "MODEL_RAW_INTEROPERABILITY_INVALID"))
        expected_evidence = [ref(metadata).to_dict(), *obsrefs]
        matrix = review["criteria_evidence"]
        evidence_valid = set(matrix) == set(REVIEW_CRITERIA) and all(matrix[k] == expected_evidence for k in matrix)
        checks.append(check("full-review-matrix", evidence_valid, "MODEL_COMPLETE_REVIEW_MATRIX_INVALID"))
        # Runtime is observed, never copied from a report's success label.
        import platform, sys
        runtime = {"python": platform.python_version(), "executable_sha256": sha256_hex(Path(sys.executable).read_bytes())}
        bad_nonce = deepcopy(observations[0]) if observations else {}
        bad_nonce["nonce"] = "model-negative-wrong-nonce"
        malformed_metadata = {k: v for k, v in metadata.items() if k != "permission"}
        derived = {
            "CRYPTOGRAPHIC": review["model_authentication"] == "FIXED_EXTERNAL_AUTH_FACT_ONLY",
            "PROTOCOL_STABILITY": metadata["protocol"] == {"wire": "MODEL_RT_V1", "transitions": []} and all(o["wire_version"] == "MODEL_RT_V1" for o in observations),
            "PRODUCTION_USE_PERMISSION": metadata["permission"] == "AFFIRMATIVE" and metadata["source_capture"]["permission_text"] == "MODEL_EXPLICIT_PERMISSION",
            "LIVE_REPEATABILITY": len(values) == 3 and all(values),
            "PILOT_EXPERIMENTAL": metadata["pilot"] == {"classification": "MODEL_PILOT" if provider == "p3" else "MODEL_STANDARD", "boundaries": "MODEL_ONLY"},
            "OPERATIONAL": metadata["service_state"] == "ACTIVE" and metadata["endpoint"] == "model://" + provider and metadata["operational_samples"] == ["AVAILABLE", "AVAILABLE", "AVAILABLE"],
            "INDEPENDENCE": metadata["operator_identity"] == profile["independence"] and review["reviewer"] != review["executor"],
            "COMMON_DEPENDENCY": metadata["common_dependencies"] == {"control_group": profile["independence"], "blocking": []},
            "PROVENANCE": metadata["source_capture"]["owner"] == profile["independence"] and metadata["source_capture"]["retrieved_at"] == metadata["retrieved_at"],
            "EVIDENCE_MANIFEST": evidence_valid and len(obsrefs) == len({ref(o) for o in observations}),
            "FRESHNESS": retrieved <= reviewed <= formed <= utc(as_of) <= retrieved + timedelta(days=90),
            "FAILURE_PATH": review["failure_probe"] == {"mutation": "wrong_nonce", "expected": "FAIL"} and not _validate_observation(bad_nonce, provider, 0, retrieved, reviewed),
            "MERKLE_COVERAGE": review["merkle_root"] == model_merkle_root(observations),
            "STANDARDS_TRANSITION": metadata["standards"] == {"profile": "MODEL_RT_V1", "migration_required": False} and metadata["protocol"]["transitions"] == [],
            "SCHEMA_VALIDATOR_REGRESSION": runtime == review["runtime"] and review["schema_probe"] == {"omit": "permission", "expected": "FAIL"} and not valid_schema(malformed_metadata, "Metadata"),
        }
        for criterion in REVIEW_CRITERIA:
            checks.append(check("criterion-" + criterion, evidence_valid and derived[criterion] and not review["blocking_findings"],
                "MODEL_EXTERNAL_CRYPTO_AUTHENTICATION_SEAM" if criterion == "CRYPTOGRAPHIC" else "MODEL_CRITERION_" + criterion))
    except (KeyError, TypeError, ValueError):
        checks.append(check("formation-schema", False, "MODEL_FORMATION_INPUT_INVALID"))
    except Exception as exc:
        checks.append(check("formation-environment", None, "MODEL_FORMATION_ENVIRONMENT_UNAVAILABLE_" + type(exc).__name__))
    return tuple(checks)

def derive_model_state(profile, formations, reviews, metadata, observations, events, as_of):
    """Replay complete chronology; adverse inputs are never filtered by verdict."""
    checks = []
    try:
        eligible = [f for f in formations if utc(f["formed_at"]) <= utc(as_of)]
        if not eligible:
            return "QUALIFICATION_BLOCKED", None, (check("decision-selection", False, "NO_EFFECTIVE_MODEL_DECISION"),)
        unique_times = {f["formed_at"] for f in eligible}
        checks.append(check("decision-conflict", len(unique_times) == len(eligible), "MODEL_CONFLICTING_DECISION_TIME"))
        latest = max(eligible, key=lambda f: (f["formed_at"], f["content_sha256"]))
        for formation in eligible:
            review = next(r for r in reviews if ref(r).to_dict() == formation["review_ref"])
            meta = next(m for m in metadata if ref(m).to_dict() == formation["metadata_ref"])
            obs = [next(o for o in observations if ref(o).to_dict() == item) for item in formation["observation_refs"]]
            checks.extend(validate_model_formation(formation, profile, review, meta, obs, as_of=formation["formed_at"]))
        selected_review = next(r for r in reviews if ref(r).to_dict() == latest["review_ref"])
        selected_metadata = next(m for m in metadata if ref(m).to_dict() == latest["metadata_ref"])
        selected_obs = [next(o for o in observations if ref(o).to_dict() == item) for item in latest["observation_refs"]]
        checks.extend(validate_model_formation(latest, profile, selected_review, selected_metadata, selected_obs, as_of=as_of))
        active = []
        for event in events:
            schema = set(event) - DERIVED == {"model_only", "provider", "provider_profile_ref", "detected_at", "effective_at", "kind"}
            valid = schema and event["provider"] == profile["name"] and event["provider_profile_ref"] == ref(profile).to_dict() and event["kind"] == "SERVICE_CHANGED"
            valid = valid and utc(event["effective_at"]) <= utc(event["detected_at"])
            checks.append(check("event-chronology", valid, "MODEL_HISTORY_EVENT_INVALID"))
            if utc(latest["formed_at"]) <= utc(event["effective_at"]) <= utc(as_of):
                active.append(event)
        relevant_metadata = []
        changed_metadata = []
        for meta in metadata:
            valid = valid_schema(meta, "Metadata") and meta["provider"] == profile["name"] and meta["provider_profile_ref"] == ref(profile).to_dict()
            valid = valid and utc(meta["retrieved_at"]) <= utc(meta["reviewed_at"])
            checks.append(check("metadata-chronology", valid, "MODEL_HISTORY_METADATA_INVALID"))
            if utc(meta["reviewed_at"]) <= utc(as_of):
                relevant_metadata.append(meta)
                if utc(latest["formed_at"]) <= utc(meta["reviewed_at"]) and (meta["change_disposition"] != "UNCHANGED" or meta["permission"] != "AFFIRMATIVE" or meta["service_state"] != "ACTIVE"):
                    changed_metadata.append(meta)
        latest_meta = max(relevant_metadata, key=lambda m: m["reviewed_at"]) if relevant_metadata else None
        checks.append(check("state-metadata-freshness", latest_meta is not None and utc(as_of) <= utc(latest_meta["retrieved_at"]) + timedelta(days=90), "MODEL_STATE_METADATA_EXPIRED"))
        checks.append(check("adverse-history", not active and not changed_metadata, "MODEL_ACTIVE_REQUALIFICATION_EVENT"))
        status = reduce_checks(checks)
        state = None if status == "UNKNOWN" else "PRODUCTION_QUALIFIED" if status == "PASS" else "REQUALIFICATION_REQUIRED" if active or changed_metadata else "QUALIFICATION_BLOCKED"
        return state, latest, tuple(checks)
    except (KeyError, TypeError, ValueError, StopIteration):
        return "QUALIFICATION_BLOCKED", None, tuple(checks) + (check("state-schema", False, "MODEL_STATE_DERIVATION_INVALID"),)
    except Exception as exc:
        return None, None, tuple(checks) + (check("state-environment", None, "MODEL_STATE_ENVIRONMENT_UNAVAILABLE_" + type(exc).__name__),)

def build_model_package_closure(package, member_bytes):
    """Isomorphic synthetic family adapter over native strict byte/history kernels.

    Inputs remain Synthetic* objects; the semantic map aliases only history roles
    required by the generic native succession/completeness kernels. No native
    signature-bearing schema is fabricated.
    """
    if package.get("object_type") != "SyntheticQualificationPackage" or package.get("model_only") is not True or not verify_sealed_object(package):
        raise ValueError("model package schema/identity")
    expected = {"model_only", "provider_profile_ref", "decision_ref", "history_ref", "as_of_utc", "members", "state_report_member_sha256"}
    if set(package) - DERIVED != expected:
        raise ValueError("model package fields")
    members = native_closure._validate_manifest(package["members"])
    if {m["relative_path"] for m in members} != set(member_bytes):
        raise ValueError("member coverage")
    # Fixed safe leaf names only. Raw native code validates actual disk closure,
    # no symlinks, exact bytes, ordering, lengths and every filesystem member.
    with TemporaryDirectory(prefix="fp-m1-model-qualification-") as temporary:
        root = Path(temporary)
        for name, raw in member_bytes.items():
            if "/" in name or name in {".", ".."}:
                raise ValueError("model member name")
            (root / name).write_bytes(raw)
        fd = native_closure._open_root(root)
        try:
            raw_members, report_path = native_closure._read_raw_members(fd, members,
                state_report_member_sha256=package["state_report_member_sha256"])
        finally:
            os.close(fd)
    objects = [parse_json_strict(v) for v in raw_members.values()]
    if any(not isinstance(o, dict) or not verify_sealed_object(o) or o.get("model_only") is not True for o in objects):
        raise ValueError("model member identity")
    for obj in objects:
        if obj["object_type"] == "SyntheticReplaySource":
            continue  # exact provider source validated by requirements + pin
        family = obj["object_type"].removeprefix("SyntheticQualification")
        if family not in SCHEMAS or not valid_schema(obj, family):
            raise ValueError("model family fields")
    byref = {ref(o): o for o in objects}
    if len(byref) != len(objects):
        raise ValueError("duplicate model member")
    profile = byref[ExactRef.from_mapping(package["provider_profile_ref"])]
    selected = byref[ExactRef.from_mapping(package["history_ref"])]
    chain = [selected]
    seen = {ref(selected)}
    while "predecessor_snapshot_ref" in chain[-1]:
        predecessor = byref[ExactRef.from_mapping(chain[-1]["predecessor_snapshot_ref"])]
        if ref(predecessor) in seen:
            raise ValueError("history cycle")
        seen.add(ref(predecessor)); chain.append(predecessor)
    roles = {"SyntheticQualificationHistory": "QualificationStateHistorySnapshot", "SyntheticQualificationMetadata": "RoughtimeProviderMetadataReview", "SyntheticQualificationEvent": "RoughtimeRequalificationEvent"}
    semantic = {(r.object_id, r.content_sha256): (roles.get(o["object_type"], o["object_type"]), o, "model") for r, o in byref.items()}
    closure = SimpleNamespace(selected_history_snapshot=selected, as_of_utc=package["as_of_utc"], history_predecessor_cycle=False,
        ordered_history_snapshot_chain=tuple(chain), typed_exact_ref_member_map=semantic,
        metadata_reviews=tuple(o for o in objects if o["object_type"] == "SyntheticQualificationMetadata"),
        requalification_events=tuple(o for o in objects if o["object_type"] == "SyntheticQualificationEvent"))
    native_closure.validate_history_cutoff(closure)
    native_closure.validate_history_succession(closure)
    native_closure.validate_history_completeness(closure)
    return profile, objects, parse_json_strict(raw_members[report_path]), selected

@dataclass(frozen=True)
class ModelValidation:
    native_result: dict | None
    checks: tuple
    selected_decision: dict | None
    model_only: bool = True

def _native_result(base, checks, decision):
    """Unavailable formatter output never grants authority or loses known FAIL."""
    try:
        result = build_qualification_validation_result(base)
        validate_qualification_validation_result(result)
        return ModelValidation(result, tuple(checks), decision)
    except Exception as exc:
        return ModelValidation(None, tuple(checks) + (check("model-result-adapter", None,
            "MODEL_RESULT_ADAPTER_UNAVAILABLE_" + type(exc).__name__),), decision)

def execute_model_qualification_validation(package, member_bytes, contract_ref, invocation_ref):
    """Executable model counterpart, with no real backend or authority shortcut."""
    checks = []
    try:
        profile, objects, retained_report, history = build_model_package_closure(package, member_bytes)
        checks.append(check("native-closure-history", True, "MODEL_NATIVE_CLOSURE_HISTORY_EXECUTED"))
        def typed(kind): return [o for o in objects if o["object_type"] == "SyntheticQualification" + kind]
        auth = typed("Authentication")
        expected_auth = {(ref(o).object_id, ref(o).content_sha256) for o in typed("History") + typed("Formation")}
        actual_auth = {(a["subject_ref"]["object_id"], a["subject_ref"]["content_sha256"]) for a in auth}
        by_subject = {ref(o): o for o in typed("History") + typed("Formation")}
        checks.append(check("model-auth-set", expected_auth == actual_auth and len(auth) == len(expected_auth) and all(
            set(a) - DERIVED == {"model_only", "subject_ref", "provider", "authority_role", "action"} and
            a["provider"] == profile["name"] and a["authority_role"] == "MODEL_QUALIFICATION_OWNER" and a["action"] == ("MODEL_HISTORY" if by_subject[ExactRef.from_mapping(a["subject_ref"])]["object_type"] == "SyntheticQualificationHistory" else "MODEL_FORMATION")
            for a in auth), "MODEL_AUTHENTICATION_FACT_INVALID"))
        state, decision, state_checks = derive_model_state(profile, typed("Formation"), typed("Review"), typed("Metadata"), typed("Observation"), typed("Event"), package["as_of_utc"])
        checks.extend(state_checks)
        recomputed_report = {"model_only": True, "provider": profile["name"], "as_of_utc": package["as_of_utc"], "state": state,
            "decision_ref": ref(decision).to_dict() if decision else {}, "history_ref": ref(history).to_dict()}
        checks.append(check("raw-report", None if state is None else {k: v for k, v in retained_report.items() if k not in DERIVED} == recomputed_report,
            "STATE_REPORT_SEMANTIC_MISMATCH"))
        checks.append(check("selected-decision", None if state is None and decision is None else decision is not None and package["decision_ref"] == ref(decision).to_dict(), "MODEL_EFFECTIVE_DECISION_MISMATCH"))
        status = reduce_checks(checks)
        if status == "UNKNOWN":
            return ModelValidation(None, tuple(checks), decision)
        base = {"schema_version": "1.0", "qualification_validation_contract_ref": contract_ref.to_dict(),
            "qualification_validation_invocation_ref": invocation_ref.to_dict(), "qualification_state_package_ref": ref(package).to_dict(),
            "validation_status": "VALID" if status == "PASS" else "INVALID"}
        if status == "PASS":
            base.update(provider_profile_ref=ref(profile).to_dict(), qualification_decision_ref=ref(decision).to_dict(),
                qualification_state_history_snapshot_ref=ref(history).to_dict(), as_of_utc=package["as_of_utc"],
                qualification_state=state, derived_state_report_semantic_sha256=content_hash(recomputed_report))
        else:
            base["primary_invalid_reason_code"] = "QUALIFICATION_STATE_DERIVATION_INVALID"
        return _native_result(base, checks, decision)
    except (ValueError, KeyError, TypeError, native_closure.QualificationStatePackageError):
        checks.append(check("native-model-validation", False, "MODEL_PACKAGE_OR_HISTORY_INVALID"))
        try:
            base = {"schema_version": "1.0", "qualification_validation_contract_ref": contract_ref.to_dict(),
                "qualification_validation_invocation_ref": invocation_ref.to_dict(), "qualification_state_package_ref": ref(package).to_dict(),
                "validation_status": "INVALID", "primary_invalid_reason_code": "PACKAGE_MEMBER_CLOSURE_INVALID"}
        except Exception as exc:
            return ModelValidation(None, tuple(checks) + (check("invalid-result-binding", None,
                "MODEL_INVALID_RESULT_BINDING_UNAVAILABLE_" + type(exc).__name__),), None)
        return _native_result(base, checks, None)
    except Exception as exc:
        return ModelValidation(None, tuple(checks) + (check("model-environment", None, "MODEL_VALIDATION_ENVIRONMENT_UNAVAILABLE_" + type(exc).__name__),), None)

