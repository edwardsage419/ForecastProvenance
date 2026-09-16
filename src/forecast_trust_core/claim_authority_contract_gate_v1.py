from __future__ import annotations

from typing import Any, Mapping, Sequence

from .canonical import CanonicalizationError, require_utc_timestamp, validate_ref, verify_sealed_object


BUNDLE_KEYS = frozenset({
    "schema_version", "object_type", "origin_class", "prospective_eligible",
    "subject_ref", "receipt_quorum_deadline_utc", "receipt_evidence_refs",
    "provider_profile_refs", "qualification_state_package_refs",
    "quorum_policy_ref", "validator_contract_ref", "object_id",
    "payload_sha256", "content_sha256",
})
RECEIPT_KEYS = frozenset({
    "schema_version", "object_type", "origin_class", "prospective_eligible",
    "subject_ref", "frozen_deadline_utc", "provider_id", "provider_profile_ref",
    "qualification_state_package_ref", "verifier_build_profile_sha256",
    "client_random_hex", "request_sha256", "request_base64", "response_sha256",
    "response_base64", "object_id", "payload_sha256", "content_sha256",
})
OTS_KEYS = frozenset({
    "schema_version", "object_type", "origin_class", "prospective_eligible",
    "external_time_evidence_bundle_ref", "proof_sha256", "proof_base64",
    "object_id", "payload_sha256", "content_sha256",
})
DVR_KEYS = frozenset({
    "schema_version", "object_type", "origin_class", "prospective_eligible",
    "primary_subject_ref", "external_time_evidence_bundle_ref", "ots_proof_ref",
    "strong_verification_report_ref", "outcome_information_barrier", "object_id",
    "payload_sha256", "content_sha256",
})
STRONG_CONTRACT_KEYS = frozenset({
    "schema_version", "object_type", "object_role", "protocol", "action",
    "input_schema_version", "output_schema_version", "verification_mode",
    "bitcoin_header_time_role", "executable_sha256", "timeout_seconds",
    "object_id", "payload_sha256", "content_sha256",
})
LIVE_OR_SYNTHETIC = frozenset({"SYNTHETIC", "LIVE_OPERATIONAL"})
BUNDLE_ORIGINS = frozenset({"SYNTHETIC", "RETROSPECTIVE", "LIVE_OPERATIONAL"})
HEX64 = frozenset("0123456789abcdef")


def _fail(message: str) -> None:
    raise ValueError(f"authoritative object contract violation: {message}")


def _hex64(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(ch not in HEX64 for ch in value):
        _fail(f"{field} must be 64 lowercase hex characters")
    return value


def _canonical_base64(value: Any, field: str) -> bytes:
    import base64

    if not isinstance(value, str) or not value:
        _fail(f"{field} must be non-empty base64")
    try:
        raw = base64.b64decode(value, validate=True)
    except Exception as exc:
        raise ValueError(f"authoritative object contract violation: {field} must be canonical base64") from exc
    if base64.b64encode(raw).decode("ascii") != value:
        _fail(f"{field} must be canonical base64")
    return raw


def _exact_sealed(obj: Mapping[str, Any], *, object_type: str, keys: frozenset[str]) -> None:
    if not isinstance(obj, Mapping):
        _fail(f"{object_type} must be an object")
    if frozenset(obj) != keys:
        _fail(f"{object_type} field set mismatch")
    if not verify_sealed_object(obj):
        _fail(f"{object_type} seal invalid")
    if obj.get("schema_version") != "1.0":
        _fail(f"{object_type} schema_version mismatch")
    if obj.get("object_type") != object_type:
        _fail(f"{object_type} object_type mismatch")


def _ref(value: Any, field: str) -> None:
    try:
        validate_ref(value)
    except (CanonicalizationError, TypeError) as exc:
        raise ValueError(f"authoritative object contract violation: {field} reference malformed") from exc


def _ref_array(value: Any, field: str, *, minimum: int, maximum: int) -> None:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        _fail(f"{field} cardinality invalid")
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(value):
        _ref(item, f"{field}[{index}]")
        pair = (item["object_id"], item["content_sha256"])
        if pair in seen:
            _fail(f"{field} contains duplicate references")
        seen.add(pair)


def validate_bundle_contract(bundle: Mapping[str, Any], *, require_full_quorum_shape: bool = True) -> None:
    _exact_sealed(bundle, object_type="ExternalTimeEvidenceBundle", keys=BUNDLE_KEYS)
    origin = bundle.get("origin_class")
    if origin not in BUNDLE_ORIGINS:
        _fail("ExternalTimeEvidenceBundle origin_class invalid")
    if bundle.get("prospective_eligible") is not False:
        _fail("ExternalTimeEvidenceBundle.prospective_eligible must be false")
    _ref(bundle.get("subject_ref"), "ExternalTimeEvidenceBundle.subject_ref")
    _ref(bundle.get("quorum_policy_ref"), "ExternalTimeEvidenceBundle.quorum_policy_ref")
    _ref(bundle.get("validator_contract_ref"), "ExternalTimeEvidenceBundle.validator_contract_ref")
    require_utc_timestamp(bundle.get("receipt_quorum_deadline_utc"))
    if require_full_quorum_shape or origin == "LIVE_OPERATIONAL":
        _ref_array(bundle.get("receipt_evidence_refs"), "ExternalTimeEvidenceBundle.receipt_evidence_refs", minimum=1, maximum=3)
        _ref_array(bundle.get("provider_profile_refs"), "ExternalTimeEvidenceBundle.provider_profile_refs", minimum=3, maximum=3)
        _ref_array(bundle.get("qualification_state_package_refs"), "ExternalTimeEvidenceBundle.qualification_state_package_refs", minimum=3, maximum=3)
    else:
        for field in ("receipt_evidence_refs", "provider_profile_refs", "qualification_state_package_refs"):
            value = bundle.get(field)
            if not isinstance(value, list):
                _fail(f"ExternalTimeEvidenceBundle.{field} must be an array")
            for index, item in enumerate(value):
                _ref(item, f"ExternalTimeEvidenceBundle.{field}[{index}]")


def validate_receipt_contract(receipt: Mapping[str, Any]) -> None:
    _exact_sealed(receipt, object_type="RoughtimeProductionReceiptEvidence", keys=RECEIPT_KEYS)
    if receipt.get("origin_class") not in LIVE_OR_SYNTHETIC:
        _fail("RoughtimeProductionReceiptEvidence origin_class invalid")
    if receipt.get("prospective_eligible") is not False:
        _fail("RoughtimeProductionReceiptEvidence.prospective_eligible must be false")
    _ref(receipt.get("subject_ref"), "RoughtimeProductionReceiptEvidence.subject_ref")
    _ref(receipt.get("provider_profile_ref"), "RoughtimeProductionReceiptEvidence.provider_profile_ref")
    _ref(receipt.get("qualification_state_package_ref"), "RoughtimeProductionReceiptEvidence.qualification_state_package_ref")
    require_utc_timestamp(receipt.get("frozen_deadline_utc"))
    if receipt.get("provider_id") not in {"roughtime.se", "time.txryan.com", "TimeNL-Roughtime"}:
        _fail("RoughtimeProductionReceiptEvidence provider_id invalid")
    for field in ("verifier_build_profile_sha256", "client_random_hex", "request_sha256", "response_sha256"):
        _hex64(receipt.get(field), field)
    _canonical_base64(receipt.get("request_base64"), "request_base64")
    _canonical_base64(receipt.get("response_base64"), "response_base64")


def validate_ots_contract(proof: Mapping[str, Any]) -> None:
    _exact_sealed(proof, object_type="OpenTimestampsProofArtifact", keys=OTS_KEYS)
    if proof.get("origin_class") not in LIVE_OR_SYNTHETIC:
        _fail("OpenTimestampsProofArtifact origin_class invalid")
    if proof.get("prospective_eligible") is not False:
        _fail("OpenTimestampsProofArtifact.prospective_eligible must be false")
    _ref(proof.get("external_time_evidence_bundle_ref"), "OpenTimestampsProofArtifact.external_time_evidence_bundle_ref")
    _hex64(proof.get("proof_sha256"), "proof_sha256")
    _canonical_base64(proof.get("proof_base64"), "proof_base64")


def validate_dvr_contract(dvr: Mapping[str, Any]) -> None:
    _exact_sealed(dvr, object_type="DurabilityVerificationRecord", keys=DVR_KEYS)
    if dvr.get("origin_class") not in LIVE_OR_SYNTHETIC:
        _fail("DurabilityVerificationRecord origin_class invalid")
    if dvr.get("prospective_eligible") is not False:
        _fail("DurabilityVerificationRecord.prospective_eligible must be false")
    _ref(dvr.get("primary_subject_ref"), "DurabilityVerificationRecord.primary_subject_ref")
    _ref(dvr.get("external_time_evidence_bundle_ref"), "DurabilityVerificationRecord.external_time_evidence_bundle_ref")
    _ref(dvr.get("ots_proof_ref"), "DurabilityVerificationRecord.ots_proof_ref")
    _ref(dvr.get("strong_verification_report_ref"), "DurabilityVerificationRecord.strong_verification_report_ref")
    require_utc_timestamp(dvr.get("outcome_information_barrier"))


def validate_strong_contract(contract: Mapping[str, Any]) -> None:
    _exact_sealed(contract, object_type="StrongBitcoinVerifierContract", keys=STRONG_CONTRACT_KEYS)
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
        if contract.get(field) != value:
            _fail(f"StrongBitcoinVerifierContract {field} mismatch")
    _hex64(contract.get("executable_sha256"), "executable_sha256")
    timeout = contract.get("timeout_seconds")
    if type(timeout) is not int or not 1 <= timeout <= 300:
        _fail("StrongBitcoinVerifierContract timeout_seconds invalid")


def validate_wall_inputs(inputs: Mapping[str, Any]) -> None:
    if not isinstance(inputs, Mapping):
        _fail("wall-clock inputs must be a mapping")
    validate_bundle_contract(inputs.get("bundle"), require_full_quorum_shape=True)
    receipts = inputs.get("receipt_evidence")
    if not isinstance(receipts, Sequence) or isinstance(receipts, (str, bytes, bytearray)):
        _fail("receipt_evidence must be a sequence")
    for receipt in receipts:
        validate_receipt_contract(receipt)


def validate_bitcoin_inputs(inputs: Mapping[str, Any]) -> None:
    if not isinstance(inputs, Mapping):
        _fail("Bitcoin inputs must be a mapping")
    bundle = inputs.get("bundle")
    full_shape = isinstance(bundle, Mapping) and bundle.get("origin_class") == "LIVE_OPERATIONAL"
    validate_bundle_contract(bundle, require_full_quorum_shape=full_shape)
    validate_ots_contract(inputs.get("proof_artifact"))
    validate_strong_contract(inputs.get("strong_verifier_contract"))
