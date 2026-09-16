from __future__ import annotations

from typing import Any, Mapping, Sequence

from . import claim_authority_v1_legacy as _legacy
from .canonical import CanonicalizationError, require_utc_timestamp, validate_ref, verify_sealed_object


# Preserve the historical implementation byte-for-byte behind this contract gate.
# All public names remain available from the historical module unless explicitly
# overridden below.
for _name, _value in vars(_legacy).items():
    if not _name.startswith("__"):
        globals()[_name] = _value


BUNDLE_KEYS = frozenset({
    "schema_version", "object_type", "origin_class", "prospective_eligible",
    "subject_ref", "receipt_quorum_deadline_utc", "receipt_evidence_refs",
    "provider_profile_refs", "qualification_state_package_refs",
    "quorum_policy_ref", "validator_contract_ref", "object_id",
    "payload_sha256", "content_sha256",
})
RECEIPT_KEYS = frozenset({
    "schema_version", "object_type", "origin_class", "prospective_eligible",
    "subject_ref", "frozen_deadline_utc", "provider_id",
    "provider_profile_ref", "qualification_state_package_ref",
    "verifier_build_profile_sha256", "client_random_hex", "request_sha256",
    "request_base64", "response_sha256", "response_base64", "object_id",
    "payload_sha256", "content_sha256",
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
STRONG_REPORT_BASE_KEYS = frozenset({
    "schema_version", "object_type", "origin_class", "prospective_eligible",
    "subject_ref", "external_time_evidence_bundle_ref", "ots_proof_ref",
    "strong_verifier_contract_ref", "validator_contract_ref", "bundle_sha256",
    "proof_sha256", "verification_mode", "bitcoin_header_time_role", "verified",
    "object_id", "payload_sha256", "content_sha256",
})
LIVE_OR_SYNTHETIC = frozenset({"SYNTHETIC", "LIVE_OPERATIONAL"})
BUNDLE_ORIGINS = frozenset({"SYNTHETIC", "RETROSPECTIVE", "LIVE_OPERATIONAL"})


def _contract_error(message: str) -> None:
    raise ValueError(f"authoritative object contract violation: {message}")


def _require_exact_sealed(
    obj: Mapping[str, Any],
    *,
    object_type: str,
    keys: frozenset[str],
) -> None:
    if not isinstance(obj, Mapping):
        _contract_error(f"{object_type} must be an object")
    if frozenset(obj) != keys:
        _contract_error(f"{object_type} field set mismatch")
    if not verify_sealed_object(obj):
        _contract_error(f"{object_type} seal invalid")
    if obj.get("schema_version") != "1.0":
        _contract_error(f"{object_type} schema_version mismatch")
    if obj.get("object_type") != object_type:
        _contract_error(f"{object_type} object_type mismatch")


def _require_ref(value: Any, field: str) -> None:
    try:
        validate_ref(value)
    except (CanonicalizationError, TypeError) as exc:
        raise ValueError(f"authoritative object contract violation: {field} reference malformed") from exc


def _require_ref_array(value: Any, field: str, *, minimum: int, maximum: int) -> None:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        _contract_error(f"{field} cardinality invalid")
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(value):
        _require_ref(item, f"{field}[{index}]")
        pair = (item["object_id"], item["content_sha256"])
        if pair in seen:
            _contract_error(f"{field} contains duplicate references")
        seen.add(pair)


def _require_false(value: Any, field: str) -> None:
    if value is not False:
        _contract_error(f"{field} must be false")


def _validate_bundle_contract(bundle: Mapping[str, Any]) -> None:
    _require_exact_sealed(bundle, object_type="ExternalTimeEvidenceBundle", keys=BUNDLE_KEYS)
    if bundle.get("origin_class") not in BUNDLE_ORIGINS:
        _contract_error("ExternalTimeEvidenceBundle origin_class invalid")
    _require_false(bundle.get("prospective_eligible"), "ExternalTimeEvidenceBundle.prospective_eligible")
    _require_ref(bundle.get("subject_ref"), "ExternalTimeEvidenceBundle.subject_ref")
    _require_ref_array(bundle.get("receipt_evidence_refs"), "ExternalTimeEvidenceBundle.receipt_evidence_refs", minimum=1, maximum=3)
    _require_ref_array(bundle.get("provider_profile_refs"), "ExternalTimeEvidenceBundle.provider_profile_refs", minimum=3, maximum=3)
    _require_ref_array(bundle.get("qualification_state_package_refs"), "ExternalTimeEvidenceBundle.qualification_state_package_refs", minimum=3, maximum=3)
    _require_ref(bundle.get("quorum_policy_ref"), "ExternalTimeEvidenceBundle.quorum_policy_ref")
    _require_ref(bundle.get("validator_contract_ref"), "ExternalTimeEvidenceBundle.validator_contract_ref")
    require_utc_timestamp(bundle.get("receipt_quorum_deadline_utc"))


def _validate_receipt_contract(receipt: Mapping[str, Any]) -> None:
    _require_exact_sealed(receipt, object_type="RoughtimeProductionReceiptEvidence", keys=RECEIPT_KEYS)
    if receipt.get("origin_class") not in LIVE_OR_SYNTHETIC:
        _contract_error("RoughtimeProductionReceiptEvidence origin_class invalid")
    _require_false(receipt.get("prospective_eligible"), "RoughtimeProductionReceiptEvidence.prospective_eligible")
    _require_ref(receipt.get("subject_ref"), "RoughtimeProductionReceiptEvidence.subject_ref")
    _require_ref(receipt.get("provider_profile_ref"), "RoughtimeProductionReceiptEvidence.provider_profile_ref")
    _require_ref(receipt.get("qualification_state_package_ref"), "RoughtimeProductionReceiptEvidence.qualification_state_package_ref")
    require_utc_timestamp(receipt.get("frozen_deadline_utc"))
    if receipt.get("provider_id") not in {"roughtime.se", "time.txryan.com", "TimeNL-Roughtime"}:
        _contract_error("RoughtimeProductionReceiptEvidence provider_id invalid")
    for field in ("verifier_build_profile_sha256", "client_random_hex", "request_sha256", "response_sha256"):
        _legacy._require_hex64(receipt.get(field), field)
    _legacy._decode_canonical_base64(receipt.get("request_base64"), "request_base64")
    _legacy._decode_canonical_base64(receipt.get("response_base64"), "response_base64")


def _validate_ots_contract(proof: Mapping[str, Any]) -> None:
    _require_exact_sealed(proof, object_type="OpenTimestampsProofArtifact", keys=OTS_KEYS)
    if proof.get("origin_class") not in LIVE_OR_SYNTHETIC:
        _contract_error("OpenTimestampsProofArtifact origin_class invalid")
    _require_false(proof.get("prospective_eligible"), "OpenTimestampsProofArtifact.prospective_eligible")
    _require_ref(proof.get("external_time_evidence_bundle_ref"), "OpenTimestampsProofArtifact.external_time_evidence_bundle_ref")
    _legacy._require_hex64(proof.get("proof_sha256"), "proof_sha256")
    _legacy._decode_canonical_base64(proof.get("proof_base64"), "proof_base64")


def _validate_dvr_contract(dvr: Mapping[str, Any]) -> None:
    _require_exact_sealed(dvr, object_type="DurabilityVerificationRecord", keys=DVR_KEYS)
    if dvr.get("origin_class") not in LIVE_OR_SYNTHETIC:
        _contract_error("DurabilityVerificationRecord origin_class invalid")
    _require_false(dvr.get("prospective_eligible"), "DurabilityVerificationRecord.prospective_eligible")
    _require_ref(dvr.get("primary_subject_ref"), "DurabilityVerificationRecord.primary_subject_ref")
    _require_ref(dvr.get("external_time_evidence_bundle_ref"), "DurabilityVerificationRecord.external_time_evidence_bundle_ref")
    _require_ref(dvr.get("ots_proof_ref"), "DurabilityVerificationRecord.ots_proof_ref")
    _require_ref(dvr.get("strong_verification_report_ref"), "DurabilityVerificationRecord.strong_verification_report_ref")
    require_utc_timestamp(dvr.get("outcome_information_barrier"))


def _validate_strong_contract(contract: Mapping[str, Any]) -> None:
    _require_exact_sealed(contract, object_type="StrongBitcoinVerifierContract", keys=STRONG_CONTRACT_KEYS)
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
            _contract_error(f"StrongBitcoinVerifierContract {field} mismatch")
    _legacy._require_hex64(contract.get("executable_sha256"), "executable_sha256")
    timeout = contract.get("timeout_seconds")
    if type(timeout) is not int or not 1 <= timeout <= 300:
        _contract_error("StrongBitcoinVerifierContract timeout_seconds invalid")


def _validate_strong_report(report: Mapping[str, Any]) -> None:
    if not isinstance(report, Mapping):
        _contract_error("StrongBitcoinVerificationReport must be an object")
    verified = report.get("verified")
    if type(verified) is not bool:
        _contract_error("StrongBitcoinVerificationReport verified must be boolean")
    keys = set(STRONG_REPORT_BASE_KEYS)
    if verified:
        keys.update({"bitcoin_block_height", "bitcoin_block_hash", "bitcoin_header_sha256", "node_version"})
    else:
        keys.add("reason_code")
    _require_exact_sealed(report, object_type="StrongBitcoinVerificationReport", keys=frozenset(keys))
    if report.get("origin_class") not in LIVE_OR_SYNTHETIC:
        _contract_error("StrongBitcoinVerificationReport origin_class invalid")
    _require_false(report.get("prospective_eligible"), "StrongBitcoinVerificationReport.prospective_eligible")
    for field in ("subject_ref", "external_time_evidence_bundle_ref", "ots_proof_ref", "strong_verifier_contract_ref", "validator_contract_ref"):
        _require_ref(report.get(field), f"StrongBitcoinVerificationReport.{field}")
    for field in ("bundle_sha256", "proof_sha256"):
        _legacy._require_hex64(report.get(field), field)
    if report.get("verification_mode") != "OWNER_CONTROLLED_BITCOIN_CORE":
        _contract_error("StrongBitcoinVerificationReport verification_mode mismatch")
    if report.get("bitcoin_header_time_role") != "DURABILITY_ONLY_NOT_CIVIL_TIME_BOUND":
        _contract_error("StrongBitcoinVerificationReport bitcoin_header_time_role mismatch")
    if verified:
        if type(report.get("bitcoin_block_height")) is not int or report["bitcoin_block_height"] < 0:
            _contract_error("StrongBitcoinVerificationReport bitcoin_block_height invalid")
        _legacy._require_hex64(report.get("bitcoin_block_hash"), "bitcoin_block_hash")
        _legacy._require_hex64(report.get("bitcoin_header_sha256"), "bitcoin_header_sha256")
        if not isinstance(report.get("node_version"), str) or not report["node_version"]:
            _contract_error("StrongBitcoinVerificationReport node_version invalid")
    elif not isinstance(report.get("reason_code"), str) or not report["reason_code"]:
        _contract_error("StrongBitcoinVerificationReport reason_code invalid")


def _validate_wall_inputs(inputs: Mapping[str, Any]) -> None:
    if not isinstance(inputs, Mapping):
        _contract_error("wall-clock inputs must be a mapping")
    _validate_bundle_contract(inputs.get("bundle"))
    receipts = inputs.get("receipt_evidence")
    if not isinstance(receipts, Sequence) or isinstance(receipts, (str, bytes, bytearray)):
        _contract_error("receipt_evidence must be a sequence")
    for receipt in receipts:
        _validate_receipt_contract(receipt)


def _validate_bitcoin_inputs(inputs: Mapping[str, Any]) -> None:
    if not isinstance(inputs, Mapping):
        _contract_error("Bitcoin inputs must be a mapping")
    _validate_bundle_contract(inputs.get("bundle"))
    _validate_ots_contract(inputs.get("proof_artifact"))
    _validate_strong_contract(inputs.get("strong_verifier_contract"))
    persisted = inputs.get("persisted_strong_report")
    if persisted is not None:
        _validate_strong_report(persisted)


def _sync_legacy_dependencies() -> None:
    # Existing focused tests monkeypatch these public dependency seams on this
    # module. Keep that behavior while the implementation lives behind the gate.
    _legacy.QualifiedVerifierBackend = globals()["QualifiedVerifierBackend"]
    _legacy.validate_provider_admission_set_authoritatively = globals()[
        "validate_provider_admission_set_authoritatively"
    ]


def recompute_external_existence_claim_authoritatively(subject, **kwargs):
    _validate_wall_inputs(kwargs)
    _sync_legacy_dependencies()
    return _legacy.recompute_external_existence_claim_authoritatively(subject, **kwargs)


def recompute_bitcoin_durability_claim_authoritatively(subject, **kwargs):
    _validate_bitcoin_inputs(kwargs)
    _sync_legacy_dependencies()
    return _legacy.recompute_bitcoin_durability_claim_authoritatively(subject, **kwargs)


def validate_cycle_plan_authoritatively(plan, *, required_slots, required_schedule_policy_ref, wall_clock_inputs):
    _validate_wall_inputs(wall_clock_inputs)
    _sync_legacy_dependencies()
    return _legacy.validate_cycle_plan_authoritatively(
        plan,
        required_slots=required_slots,
        required_schedule_policy_ref=required_schedule_policy_ref,
        wall_clock_inputs=wall_clock_inputs,
    )


def validate_final_genesis_acceptance_authoritatively(
    acceptance,
    *,
    final_evidence_subject_ref,
    wall_clock_inputs,
    bitcoin_inputs,
):
    _validate_wall_inputs(wall_clock_inputs)
    _validate_bitcoin_inputs(bitcoin_inputs)
    _sync_legacy_dependencies()
    return _legacy.validate_final_genesis_acceptance_authoritatively(
        acceptance,
        final_evidence_subject_ref=final_evidence_subject_ref,
        wall_clock_inputs=wall_clock_inputs,
        bitcoin_inputs=bitcoin_inputs,
    )


def recompute_pre_outcome_durability_authoritatively(
    primary_subject,
    *,
    bitcoin_inputs,
    durability_record,
    durability_record_wall_clock_inputs,
):
    _validate_bitcoin_inputs(bitcoin_inputs)
    _validate_dvr_contract(durability_record)
    _validate_wall_inputs(durability_record_wall_clock_inputs)
    _sync_legacy_dependencies()
    return _legacy.recompute_pre_outcome_durability_authoritatively(
        primary_subject,
        bitcoin_inputs=bitcoin_inputs,
        durability_record=durability_record,
        durability_record_wall_clock_inputs=durability_record_wall_clock_inputs,
    )


def derive_confirmatory_eligibility_from_evidence(
    forecast,
    *,
    component_specs,
    required_claim_requirements,
    hard_invalidation_reason_codes=(),
):
    for spec in component_specs:
        if not isinstance(spec, Mapping):
            _contract_error("component spec must be a mapping")
        kind = spec.get("kind")
        authority_inputs = spec.get("authority_inputs")
        if kind in {"wall_clock_deadline", "external_existence"}:
            _validate_wall_inputs(authority_inputs)
        elif kind == "bitcoin_durability":
            _validate_bitcoin_inputs(authority_inputs)
        elif kind == "pre_outcome_durability":
            if not isinstance(authority_inputs, Mapping):
                _contract_error("pre-outcome authority inputs must be a mapping")
            _validate_bitcoin_inputs(authority_inputs.get("bitcoin_inputs"))
            _validate_dvr_contract(authority_inputs.get("durability_record"))
            _validate_wall_inputs(authority_inputs.get("durability_record_wall_clock_inputs"))
    _sync_legacy_dependencies()
    return _legacy.derive_confirmatory_eligibility_from_evidence(
        forecast,
        component_specs=component_specs,
        required_claim_requirements=required_claim_requirements,
        hard_invalidation_reason_codes=hard_invalidation_reason_codes,
    )


def validate_persisted_final_acceptance_report_authoritatively(
    persisted_report,
    acceptance,
    *,
    final_evidence_subject_ref,
    wall_clock_inputs,
    bitcoin_inputs,
    trusted_manifest_ref,
):
    _validate_wall_inputs(wall_clock_inputs)
    _validate_bitcoin_inputs(bitcoin_inputs)
    _sync_legacy_dependencies()
    return _legacy.validate_persisted_final_acceptance_report_authoritatively(
        persisted_report,
        acceptance,
        final_evidence_subject_ref=final_evidence_subject_ref,
        wall_clock_inputs=wall_clock_inputs,
        bitcoin_inputs=bitcoin_inputs,
        trusted_manifest_ref=trusted_manifest_ref,
    )


def validate_persisted_cycle_plan_report_authoritatively(
    persisted_report,
    plan,
    *,
    required_slots,
    required_schedule_policy_ref,
    wall_clock_inputs,
    trusted_manifest_ref,
):
    _validate_wall_inputs(wall_clock_inputs)
    _sync_legacy_dependencies()
    return _legacy.validate_persisted_cycle_plan_report_authoritatively(
        persisted_report,
        plan,
        required_slots=required_slots,
        required_schedule_policy_ref=required_schedule_policy_ref,
        wall_clock_inputs=wall_clock_inputs,
        trusted_manifest_ref=trusted_manifest_ref,
    )
