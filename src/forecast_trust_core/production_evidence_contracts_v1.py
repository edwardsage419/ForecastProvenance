from __future__ import annotations

import re
from typing import Any, Mapping

from .canonical import (
    require_ascii_token,
    require_utc_timestamp,
    validate_ref,
    verify_sealed_object,
)


HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
PROVIDER_IDS = frozenset({"roughtime.se", "time.txryan.com", "TimeNL-Roughtime"})
LIVE_OR_SYNTHETIC = frozenset({"SYNTHETIC", "LIVE_OPERATIONAL"})
BUNDLE_ORIGIN_CLASSES = frozenset({"SYNTHETIC", "RETROSPECTIVE", "LIVE_OPERATIONAL"})

EXTERNAL_TIME_EVIDENCE_BUNDLE_KEYS = frozenset(
    {
        "schema_version",
        "object_type",
        "origin_class",
        "prospective_eligible",
        "subject_ref",
        "receipt_quorum_deadline_utc",
        "receipt_evidence_refs",
        "provider_profile_refs",
        "qualification_state_package_refs",
        "quorum_policy_ref",
        "validator_contract_ref",
        "object_id",
        "payload_sha256",
        "content_sha256",
    }
)

ROUGHTIME_PRODUCTION_RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "object_type",
        "origin_class",
        "prospective_eligible",
        "subject_ref",
        "frozen_deadline_utc",
        "provider_id",
        "provider_profile_ref",
        "qualification_state_package_ref",
        "verifier_build_profile_sha256",
        "client_random_hex",
        "request_sha256",
        "request_base64",
        "response_sha256",
        "response_base64",
        "object_id",
        "payload_sha256",
        "content_sha256",
    }
)

OPEN_TIMESTAMPS_PROOF_KEYS = frozenset(
    {
        "schema_version",
        "object_type",
        "origin_class",
        "prospective_eligible",
        "external_time_evidence_bundle_ref",
        "proof_sha256",
        "proof_base64",
        "object_id",
        "payload_sha256",
        "content_sha256",
    }
)

DURABILITY_VERIFICATION_RECORD_KEYS = frozenset(
    {
        "schema_version",
        "object_type",
        "origin_class",
        "prospective_eligible",
        "primary_subject_ref",
        "external_time_evidence_bundle_ref",
        "ots_proof_ref",
        "strong_verification_report_ref",
        "outcome_information_barrier",
        "object_id",
        "payload_sha256",
        "content_sha256",
    }
)

STRONG_BITCOIN_VERIFIER_CONTRACT_KEYS = frozenset(
    {
        "schema_version",
        "object_type",
        "object_role",
        "protocol",
        "action",
        "input_schema_version",
        "output_schema_version",
        "verification_mode",
        "bitcoin_header_time_role",
        "executable_sha256",
        "timeout_seconds",
        "object_id",
        "payload_sha256",
        "content_sha256",
    }
)


def _require_exact_keys(value: Mapping[str, Any], expected: frozenset[str], label: str) -> None:
    actual = frozenset(value)
    if actual != expected:
        raise ValueError(
            f"{label} fields invalid; missing={sorted(expected - actual)} extra={sorted(actual - expected)}"
        )


def _require_hex64(value: Any, label: str) -> str:
    if not isinstance(value, str) or HEX64_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be 64 lowercase hex characters")
    return value


def _require_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a nonempty string")
    return value


def _require_ref(value: Any, label: str) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object reference")
    try:
        validate_ref(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} reference invalid") from exc


def _require_ref_list(value: Any, label: str, *, minimum: int, maximum: int) -> None:
    if not isinstance(value, list) or not (minimum <= len(value) <= maximum):
        raise ValueError(f"{label} must contain between {minimum} and {maximum} references")
    for index, item in enumerate(value):
        _require_ref(item, f"{label}[{index}]")


def _require_sealed_exact(
    value: Mapping[str, Any],
    *,
    object_type: str,
    expected_keys: frozenset[str],
    label: str,
) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    _require_exact_keys(value, expected_keys, label)
    if not verify_sealed_object(value):
        raise ValueError(f"{label} seal invalid")
    if value.get("schema_version") != "1.0":
        raise ValueError(f"{label} schema_version mismatch")
    if value.get("object_type") != object_type:
        raise ValueError(f"{label} object_type mismatch")
    require_ascii_token(str(value["object_id"]), f"{label}.object_id")
    _require_hex64(value["payload_sha256"], f"{label}.payload_sha256")
    _require_hex64(value["content_sha256"], f"{label}.content_sha256")


def validate_external_time_evidence_bundle_contract(bundle: Mapping[str, Any]) -> None:
    _require_sealed_exact(
        bundle,
        object_type="ExternalTimeEvidenceBundle",
        expected_keys=EXTERNAL_TIME_EVIDENCE_BUNDLE_KEYS,
        label="ExternalTimeEvidenceBundle",
    )
    if bundle["origin_class"] not in BUNDLE_ORIGIN_CLASSES:
        raise ValueError("ExternalTimeEvidenceBundle origin_class invalid")
    if bundle["prospective_eligible"] is not False:
        raise ValueError("ExternalTimeEvidenceBundle prospective_eligible must be false")
    _require_ref(bundle["subject_ref"], "ExternalTimeEvidenceBundle.subject_ref")
    require_utc_timestamp(bundle["receipt_quorum_deadline_utc"])
    _require_ref_list(
        bundle["receipt_evidence_refs"],
        "ExternalTimeEvidenceBundle.receipt_evidence_refs",
        minimum=1,
        maximum=3,
    )
    _require_ref_list(
        bundle["provider_profile_refs"],
        "ExternalTimeEvidenceBundle.provider_profile_refs",
        minimum=3,
        maximum=3,
    )
    _require_ref_list(
        bundle["qualification_state_package_refs"],
        "ExternalTimeEvidenceBundle.qualification_state_package_refs",
        minimum=3,
        maximum=3,
    )
    _require_ref(bundle["quorum_policy_ref"], "ExternalTimeEvidenceBundle.quorum_policy_ref")
    _require_ref(bundle["validator_contract_ref"], "ExternalTimeEvidenceBundle.validator_contract_ref")


def validate_roughtime_production_receipt_contract(receipt: Mapping[str, Any]) -> None:
    _require_sealed_exact(
        receipt,
        object_type="RoughtimeProductionReceiptEvidence",
        expected_keys=ROUGHTIME_PRODUCTION_RECEIPT_KEYS,
        label="RoughtimeProductionReceiptEvidence",
    )
    if receipt["origin_class"] not in LIVE_OR_SYNTHETIC:
        raise ValueError("RoughtimeProductionReceiptEvidence origin_class invalid")
    if receipt["prospective_eligible"] is not False:
        raise ValueError("RoughtimeProductionReceiptEvidence prospective_eligible must be false")
    _require_ref(receipt["subject_ref"], "RoughtimeProductionReceiptEvidence.subject_ref")
    require_utc_timestamp(receipt["frozen_deadline_utc"])
    if receipt["provider_id"] not in PROVIDER_IDS:
        raise ValueError("RoughtimeProductionReceiptEvidence provider_id invalid")
    _require_ref(receipt["provider_profile_ref"], "RoughtimeProductionReceiptEvidence.provider_profile_ref")
    _require_ref(
        receipt["qualification_state_package_ref"],
        "RoughtimeProductionReceiptEvidence.qualification_state_package_ref",
    )
    _require_hex64(
        receipt["verifier_build_profile_sha256"],
        "RoughtimeProductionReceiptEvidence.verifier_build_profile_sha256",
    )
    _require_hex64(receipt["client_random_hex"], "RoughtimeProductionReceiptEvidence.client_random_hex")
    _require_hex64(receipt["request_sha256"], "RoughtimeProductionReceiptEvidence.request_sha256")
    _require_nonempty_string(receipt["request_base64"], "RoughtimeProductionReceiptEvidence.request_base64")
    _require_hex64(receipt["response_sha256"], "RoughtimeProductionReceiptEvidence.response_sha256")
    _require_nonempty_string(receipt["response_base64"], "RoughtimeProductionReceiptEvidence.response_base64")


def validate_open_timestamps_proof_artifact_contract(proof: Mapping[str, Any]) -> None:
    _require_sealed_exact(
        proof,
        object_type="OpenTimestampsProofArtifact",
        expected_keys=OPEN_TIMESTAMPS_PROOF_KEYS,
        label="OpenTimestampsProofArtifact",
    )
    if proof["origin_class"] not in LIVE_OR_SYNTHETIC:
        raise ValueError("OpenTimestampsProofArtifact origin_class invalid")
    if proof["prospective_eligible"] is not False:
        raise ValueError("OpenTimestampsProofArtifact prospective_eligible must be false")
    _require_ref(
        proof["external_time_evidence_bundle_ref"],
        "OpenTimestampsProofArtifact.external_time_evidence_bundle_ref",
    )
    _require_hex64(proof["proof_sha256"], "OpenTimestampsProofArtifact.proof_sha256")
    _require_nonempty_string(proof["proof_base64"], "OpenTimestampsProofArtifact.proof_base64")


def validate_durability_verification_record_contract(record: Mapping[str, Any]) -> None:
    _require_sealed_exact(
        record,
        object_type="DurabilityVerificationRecord",
        expected_keys=DURABILITY_VERIFICATION_RECORD_KEYS,
        label="DurabilityVerificationRecord",
    )
    if record["origin_class"] not in LIVE_OR_SYNTHETIC:
        raise ValueError("DurabilityVerificationRecord origin_class invalid")
    if record["prospective_eligible"] is not False:
        raise ValueError("DurabilityVerificationRecord prospective_eligible must be false")
    _require_ref(record["primary_subject_ref"], "DurabilityVerificationRecord.primary_subject_ref")
    _require_ref(
        record["external_time_evidence_bundle_ref"],
        "DurabilityVerificationRecord.external_time_evidence_bundle_ref",
    )
    _require_ref(record["ots_proof_ref"], "DurabilityVerificationRecord.ots_proof_ref")
    _require_ref(
        record["strong_verification_report_ref"],
        "DurabilityVerificationRecord.strong_verification_report_ref",
    )
    require_utc_timestamp(record["outcome_information_barrier"])


def validate_strong_bitcoin_verifier_contract(contract: Mapping[str, Any]) -> None:
    _require_sealed_exact(
        contract,
        object_type="StrongBitcoinVerifierContract",
        expected_keys=STRONG_BITCOIN_VERIFIER_CONTRACT_KEYS,
        label="StrongBitcoinVerifierContract",
    )
    expected = {
        "object_role": "NORMATIVE",
        "protocol": "FPP_STRONG_BITCOIN_VERIFIER_V1",
        "action": "verify-bitcoin-durability",
        "input_schema_version": "1.0",
        "output_schema_version": "1.0",
        "verification_mode": "OWNER_CONTROLLED_BITCOIN_CORE",
        "bitcoin_header_time_role": "DURABILITY_ONLY_NOT_CIVIL_TIME_BOUND",
    }
    for field, value in expected.items():
        if contract[field] != value:
            raise ValueError(f"StrongBitcoinVerifierContract {field} mismatch")
    _require_hex64(contract["executable_sha256"], "StrongBitcoinVerifierContract.executable_sha256")
    timeout = contract["timeout_seconds"]
    if type(timeout) is not int or not (1 <= timeout <= 300):
        raise ValueError("StrongBitcoinVerifierContract timeout_seconds invalid")
