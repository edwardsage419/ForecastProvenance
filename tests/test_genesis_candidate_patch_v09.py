import hashlib
import json
from pathlib import Path

from forecast_trust_core.canonical import verify_sealed_object


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "genesis" / "candidate" / "objects" / "candidate_object_set_v0_2.json"
PATCHES = [
    ROOT / "genesis" / "candidate" / "objects" / f"candidate_patch_v0_{version}.json"
    for version in range(3, 10)
]
SCHEMA_FILES = {
    "target_instance": "target_instance_v1.schema.json",
    "forecast_slot": "forecast_slot_v1.schema.json",
    "schedule_derivation_evidence": "schedule_derivation_evidence_v1.schema.json",
    "issuance_cycle_plan": "issuance_cycle_plan_v1.schema.json",
    "issuance_cycle_manifest": "issuance_cycle_manifest_v1.schema.json",
}


def apply_patch(index, patch):
    for retirement in patch.get("retire_objects", []):
        object_id = retirement["object_id"]
        assert index[object_id]["content_sha256"] == retirement["retires_content_sha256"]
        del index[object_id]
    for replacement in patch.get("replace_objects", []):
        object_id = replacement["object_id"]
        assert index[object_id]["content_sha256"] == replacement["replaces_content_sha256"]
        index[object_id] = replacement["replacement"]
    for obj in patch.get("add_objects", []):
        assert obj["object_id"] not in index
        index[obj["object_id"]] = obj
    assert len(index) == patch["effective_object_count"]


def load_v09():
    base = json.loads(BASE.read_text(encoding="utf-8"))
    index = {obj["object_id"]: obj for obj in base["objects"]}
    patches = [json.loads(path.read_text(encoding="utf-8")) for path in PATCHES]
    for patch in patches:
        apply_patch(index, patch)
    return index, patches


def test_v09_is_exact_successor_and_remains_candidate_only():
    index, patches = load_v09()
    patch = patches[-1]
    assert patch["candidate_version"] == "0.9"
    assert patch["predecessor_patch"] == "candidate_patch_v0_8.json"
    assert patch["status"] == "GEN_001_CANDIDATE_ONLY"
    assert patch["prospective_eligible"] is False
    assert "accepted" not in patch
    assert "effective" not in patch
    assert len(index) == 21


def test_v09_retires_exact_v2_and_adds_valid_sealed_v3():
    index, patches = load_v09()
    retirement = patches[-1]["retire_objects"][0]
    assert retirement == {
        "object_id": "policy:genesis-issuance-schedule:v2",
        "reason": "superseded_by_v3_genesis_runtime_contract_freeze",
        "retires_content_sha256": "ffeeadf78744612a06184ab65cbbf779b0a66b04f5fbcd67ba36ef218b6712dd",
    }
    assert "policy:genesis-issuance-schedule:v2" not in index
    schedule = index["policy:genesis-issuance-schedule:v3"]
    assert verify_sealed_object(schedule)
    assert schedule["policy_type"] == "ISSUANCE_SCHEDULE"
    assert schedule["canonical_runtime_contract_version"] == "GENESIS_RUNTIME_CONTRACT_V1"
    assert schedule["schedule_parser_id"] == "GENESIS_SCHEDULE_PARSER_V1"
    assert schedule["runtime_semantic_id_rule"] == "PROHIBITED_RECONSTRUCT_WITHOUT_OVERRIDE"
    assert schedule["runtime_identity_match_rule"] == "RECONSTRUCT_AND_REQUIRE_EXACT_COMPLETE_REFERENCE"


def test_v3_binds_exact_schema_bytes_and_identity_contexts():
    index, _ = load_v09()
    schedule = index["policy:genesis-issuance-schedule:v3"]
    assert set(schedule["runtime_contract_schema_sha256"]) == set(SCHEMA_FILES)
    for contract, filename in SCHEMA_FILES.items():
        digest = hashlib.sha256((ROOT / "schemas" / filename).read_bytes()).hexdigest()
        assert schedule["runtime_contract_schema_sha256"][contract] == digest
    assert schedule["runtime_object_types"] == {
        "forecast_slot": "ForecastSlot",
        "issuance_cycle_manifest": "IssuanceCycleManifest",
        "issuance_cycle_plan": "IssuanceCyclePlan",
        "schedule_derivation_evidence": "ScheduleDerivationEvidence",
        "target_instance": "TargetInstance",
    }
    assert schedule["runtime_schema_versions"] == {key: "1.0" for key in SCHEMA_FILES}
    assert schedule["runtime_stable_context_templates"] == {
        "forecast_slot": "genesis-forecast-slot:{target_instance_object_id}:{method_object_id}",
        "issuance_cycle_manifest": "genesis-issuance-cycle-manifest:{cycle_plan_object_id}",
        "issuance_cycle_plan": "genesis-issuance-cycle-plan:{target_instance_object_id}",
        "schedule_derivation_evidence": "genesis-schedule-derivation:{target_object_id}:{reference_period}:{schedule_artifact_sha256}",
        "target_instance": "genesis-target-instance:{target_object_id}:{reference_period}",
    }


def test_v3_preserves_v2_schedule_semantics_and_freezes_non_self_authority():
    index, _ = load_v09()
    schedule = index["policy:genesis-issuance-schedule:v3"]
    assert schedule["normative_timezone"] == "America/New_York"
    assert schedule["relative_timing_basis"] == "LOCAL_CALENDAR_ARITHMETIC_THEN_UTC"
    assert schedule["ambiguous_or_nonexistent_local_time_rule"] == "FAIL_CLOSED"
    assert schedule["external_proof_offset_elapsed_hours"] == 24
    assert schedule["timezone_database_binding_rule"] == "exact_iana_tzdb_artifact_ref_and_version_required"
    assert schedule["schedule_evidence_authority_rule"] == (
        "supporting_evidence_must_replay_under_manifest_bound_policy_target_source_and_validator"
    )


def test_historical_v08_bytes_and_semantics_remain_unchanged():
    raw = (ROOT / "genesis" / "candidate" / "objects" / "candidate_patch_v0_8.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "a3fea944010b0d33419daa8b05586b4ff988fc94cdff8c5ea6a20119b6efe1b9"
    historical = json.loads(raw)
    assert historical["candidate_version"] == "0.8"
    assert historical["add_objects"][0]["object_id"] == "policy:genesis-issuance-schedule:v2"


def test_historical_v04_plan_schema_bytes_remain_unchanged():
    raw = (ROOT / "schemas" / "issuance_cycle_plan.schema.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "698ab353090f220d647d8d21af05a4f0d923b9203acf8fdc3908203449a992b5"
