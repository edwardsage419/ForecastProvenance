from __future__ import annotations

import base64
import hashlib
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from ._checks import check as _check
from ._roughtime_execution import QualifiedVerifierBackend
from ._roughtime_support import _parse_precise_utc_ns, derive_nonce_v2_hex
from .architecture_compression_v1 import (
    _claim,
    derive_bitcoin_durability_claim,
    validate_derived_claim_vector,
    validate_final_genesis_acceptance,
)
from .architecture_compression_v1_hardening import (
    derive_confirmatory_eligibility_strict,
    derive_deadline_existence_claim_strict,
    derive_pre_outcome_durability_claim_strict,
    validate_provider_admission_set_authoritatively,
)
from .canonical import (
    CanonicalizationError,
    canonical_json,
    parse_json_strict,
    seal_object,
    sorted_refs,
    validate_ref,
    verify_sealed_object,
)
from .core import Validation, aggregate, validate_cycle_plan
from .production_evidence_contracts_v1 import (
    validate_durability_verification_record_contract,
    validate_external_time_evidence_bundle_contract,
    validate_open_timestamps_proof_artifact_contract,
    validate_roughtime_production_receipt_contract,
    validate_strong_bitcoin_verifier_contract,
)
from ._verified_executable import PinnedExecutable


HEX64 = frozenset("0123456789abcdef")
ORIGIN_CLASSES = frozenset({"SYNTHETIC", "RETROSPECTIVE", "LIVE_OPERATIONAL"})
BITCOIN_VERIFIER_PROTOCOL = "FPP_STRONG_BITCOIN_VERIFIER_V1"

PRODUCTION_EVIDENCE_CONTRACT_VALIDATORS = {
    "ExternalTimeEvidenceBundle": validate_external_time_evidence_bundle_contract,
    "RoughtimeProductionReceiptEvidence": validate_roughtime_production_receipt_contract,
    "OpenTimestampsProofArtifact": validate_open_timestamps_proof_artifact_contract,
    "DurabilityVerificationRecord": validate_durability_verification_record_contract,
    "StrongBitcoinVerifierContract": validate_strong_bitcoin_verifier_contract,
}


@dataclass(frozen=True)
class WallClockRecomputation:
    external_existence_claim: Mapping[str, Any]
    deadline_existence_claim: Mapping[str, Any]
    evidence_bundle_ref: Mapping[str, str]


@dataclass(frozen=True)
class BitcoinRecomputation:
    bitcoin_durability_claim: Mapping[str, Any]
    evidence_bundle_ref: Mapping[str, str]
    proof_artifact_ref: Mapping[str, str]
    strong_verification_report: Mapping[str, Any]


def _exact_ref(obj: Mapping[str, Any], *, object_type: str | None = None) -> dict[str, str]:
    declared_type = obj.get("object_type") if isinstance(obj, Mapping) else None
    contract_type = object_type or declared_type
    contract_validator = PRODUCTION_EVIDENCE_CONTRACT_VALIDATORS.get(str(contract_type))
    if contract_validator is not None:
        contract_validator(obj)
    if not verify_sealed_object(obj):
        raise ValueError("authoritative input must be a valid sealed object")
    if object_type is not None and obj.get("object_type") != object_type:
        raise ValueError(f"expected sealed object_type {object_type}")
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def _require_ref_equal(actual: Any, expected: Mapping[str, Any], name: str) -> None:
    try:
        validate_ref(actual)
        validate_ref(expected)
    except (CanonicalizationError, TypeError) as exc:
        raise ValueError(f"{name} reference malformed") from exc
    if dict(actual) != dict(expected):
        raise ValueError(f"{name} reference mismatch")


def _require_hex64(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(ch not in HEX64 for ch in value):
        raise ValueError(f"{name} must be 64 lowercase hex characters")
    return value


def _decode_canonical_base64(value: Any, name: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be non-empty base64")
    try:
        raw = base64.b64decode(value, validate=True)
    except Exception as exc:
        raise ValueError(f"{name} must be canonical base64") from exc
    if base64.b64encode(raw).decode("ascii") != value:
        raise ValueError(f"{name} must be canonical base64")
    return raw


def _ceil_ns_to_utc_seconds(value: int) -> str:
    if type(value) is not int or value < 0:
        raise ValueError("UTC nanoseconds must be a nonnegative integer")
    seconds = (value + 999_999_999) // 1_000_000_000
    return datetime.fromtimestamp(seconds, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_origin_evidence(obj: Mapping[str, Any], object_type: str) -> None:
    _exact_ref(obj, object_type=object_type)
    if obj.get("origin_class") not in ORIGIN_CLASSES:
        raise ValueError(f"{object_type} origin_class invalid")
    if obj.get("prospective_eligible") is not False:
        raise ValueError(f"{object_type} prospective_eligible must be false")


def _validate_bundle(
    bundle: Mapping[str, Any],
    *,
    subject_ref: Mapping[str, Any],
    receipt_evidence: Sequence[Mapping[str, Any]],
    provider_profiles: Sequence[Mapping[str, Any]],
    qualification_state_packages: Sequence[Mapping[str, Any]],
    quorum_policy_ref: Mapping[str, Any],
    validator_contract_ref: Mapping[str, Any],
) -> dict[str, str]:
    _validate_origin_evidence(bundle, "ExternalTimeEvidenceBundle")
    bundle_ref = _exact_ref(bundle)
    _require_ref_equal(bundle.get("subject_ref"), subject_ref, "bundle subject")
    _require_ref_equal(bundle.get("quorum_policy_ref"), quorum_policy_ref, "bundle quorum policy")
    _require_ref_equal(bundle.get("validator_contract_ref"), validator_contract_ref, "bundle validator contract")
    deadline = bundle.get("receipt_quorum_deadline_utc")
    from .canonical import require_utc_timestamp
    require_utc_timestamp(deadline)
    try:
        expected_receipts = sorted_refs(_exact_ref(item, object_type="RoughtimeProductionReceiptEvidence") for item in receipt_evidence)
        expected_profiles = sorted_refs(_exact_ref(item, object_type="RoughtimeProductionProviderProfile") for item in provider_profiles)
        expected_packages = sorted_refs(_exact_ref(item, object_type="RoughtimeProviderQualificationStatePackage") for item in qualification_state_packages)
        actual_receipts = sorted_refs(bundle.get("receipt_evidence_refs", []))
        actual_profiles = sorted_refs(bundle.get("provider_profile_refs", []))
        actual_packages = sorted_refs(bundle.get("qualification_state_package_refs", []))
    except (CanonicalizationError, TypeError, ValueError) as exc:
        raise ValueError("bundle evidence reference set malformed") from exc
    if actual_receipts != expected_receipts:
        raise ValueError("bundle receipt evidence set mismatch")
    if actual_profiles != expected_profiles:
        raise ValueError("bundle provider profile set mismatch")
    if actual_packages != expected_packages:
        raise ValueError("bundle qualification state package set mismatch")
    if len(actual_profiles) != 3 or len(actual_packages) != 3:
        raise ValueError("Genesis wall-clock bundle requires exactly three admitted providers")
    if not 1 <= len(actual_receipts) <= 3:
        raise ValueError("bundle receipt evidence cardinality invalid")
    return bundle_ref


def _replay_receipt(
    receipt: Mapping[str, Any],
    *,
    subject_ref: Mapping[str, Any],
    bundle_deadline_utc: str,
    profile: Mapping[str, Any],
    state_package: Mapping[str, Any],
    build_profile: Mapping[str, Any],
    backend: QualifiedVerifierBackend,
) -> tuple[str, int]:
    _validate_origin_evidence(receipt, "RoughtimeProductionReceiptEvidence")
    profile_ref = _exact_ref(profile, object_type="RoughtimeProductionProviderProfile")
    package_ref = _exact_ref(state_package, object_type="RoughtimeProviderQualificationStatePackage")
    _require_ref_equal(receipt.get("subject_ref"), subject_ref, "receipt subject")
    _require_ref_equal(receipt.get("provider_profile_ref"), profile_ref, "receipt provider profile")
    _require_ref_equal(receipt.get("qualification_state_package_ref"), package_ref, "receipt qualification state")
    if receipt.get("provider_id") != profile.get("provider_id") or receipt.get("provider_id") != state_package.get("provider_id"):
        raise ValueError("receipt provider identity mismatch")
    if receipt.get("frozen_deadline_utc") != bundle_deadline_utc:
        raise ValueError("receipt frozen deadline mismatch")
    if profile.get("verifier_build_profile_sha256") != build_profile.get("profile_sha256"):
        raise ValueError("provider profile verifier build binding mismatch")
    if receipt.get("verifier_build_profile_sha256") != build_profile.get("profile_sha256"):
        raise ValueError("receipt verifier build binding mismatch")

    request = _decode_canonical_base64(receipt.get("request_base64"), "request_base64")
    response = _decode_canonical_base64(receipt.get("response_base64"), "response_base64")
    if hashlib.sha256(request).hexdigest() != receipt.get("request_sha256"):
        raise ValueError("receipt request hash mismatch")
    if hashlib.sha256(response).hexdigest() != receipt.get("response_sha256"):
        raise ValueError("receipt response hash mismatch")

    nonce_hex = derive_nonce_v2_hex(subject_ref["content_sha256"], receipt.get("client_random_hex"))
    provider = dict(profile)
    provider["nonce_hex"] = nonce_hex
    rebuilt, _transcript = backend.build_request(provider)
    if rebuilt != request:
        raise ValueError("retained request does not equal deterministic strict-verifier request")

    verified = backend.verify_response(provider, request, response)
    if not verified.verified or verified.failure_code is not None:
        raise ValueError("strict Roughtime response verification failed")
    if verified.midpoint_utc is None or verified.radius_nanoseconds is None:
        raise ValueError("strict Roughtime verifier omitted authenticated time output")
    if type(verified.radius_nanoseconds) is not int or verified.radius_nanoseconds <= 0:
        raise ValueError("strict Roughtime radius invalid")
    upper_ns = _parse_precise_utc_ns(verified.midpoint_utc, "midpoint_utc") + verified.radius_nanoseconds
    deadline_ns = _parse_precise_utc_ns(bundle_deadline_utc, "receipt_quorum_deadline_utc")
    if upper_ns > deadline_ns:
        raise ValueError("authenticated receipt upper bound exceeds frozen receipt deadline")
    return str(profile["provider_id"]), upper_ns


def recompute_external_existence_claim_authoritatively(
    subject: Mapping[str, Any],
    *,
    bundle: Mapping[str, Any],
    receipt_evidence: Sequence[Mapping[str, Any]],
    provider_profiles: Sequence[Mapping[str, Any]],
    qualification_state_packages: Sequence[Mapping[str, Any]],
    provider_authority_inputs: Mapping[str, Mapping[str, Any]],
    quorum_policy_ref: Mapping[str, Any],
    qualification_verifier_contract_ref: Mapping[str, Any],
    validator_contract_ref: Mapping[str, Any],
    expected_validator_contract_ref: Mapping[str, Any],
    roughtime_verifier_binary: Path,
    roughtime_verifier_build_profile: Mapping[str, Any],
    claim_deadline_utc: str | None = None,
) -> WallClockRecomputation:
    """Recompute wall-clock claims from exact retained evidence. No claim state is accepted as input."""
    subject_ref = _exact_ref(subject)
    try:
        _require_ref_equal(validator_contract_ref, expected_validator_contract_ref, "active ValidatorContract")
        bundle_ref = _validate_bundle(
            bundle,
            subject_ref=subject_ref,
            receipt_evidence=receipt_evidence,
            provider_profiles=provider_profiles,
            qualification_state_packages=qualification_state_packages,
            quorum_policy_ref=quorum_policy_ref,
            validator_contract_ref=validator_contract_ref,
        )
        bundle_deadline = str(bundle["receipt_quorum_deadline_utc"])
        bundle_origin = bundle.get("origin_class")
        if any(receipt.get("origin_class") != bundle_origin for receipt in receipt_evidence):
            raise ValueError("receipt evidence origin class differs from its bundle")
        if claim_deadline_utc is not None and claim_deadline_utc != bundle_deadline:
            raise ValueError("claim deadline differs from frozen receipt quorum deadline")

        admitted_profiles = [_exact_ref(item, object_type="RoughtimeProductionProviderProfile") for item in provider_profiles]
        admitted_decisions = []
        for package in qualification_state_packages:
            validate_ref(package["qualification_decision_ref"])
            admitted_decisions.append(dict(package["qualification_decision_ref"]))
        admission = validate_provider_admission_set_authoritatively(
            qualification_state_packages,
            frozen_deadline_utc=bundle_deadline,
            admitted_provider_profile_refs=admitted_profiles,
            admitted_qualification_decision_refs=admitted_decisions,
            provider_inputs=provider_authority_inputs,
            qualification_verifier_contract_ref=qualification_verifier_contract_ref,
        )
        if not admission.valid:
            raise ValueError("authoritative provider admission failed")

        profiles_by_id = {str(item["provider_id"]): item for item in provider_profiles}
        packages_by_id = {str(item["provider_id"]): item for item in qualification_state_packages}
        if len(profiles_by_id) != 3 or len(packages_by_id) != 3:
            raise ValueError("duplicate provider identity in admitted set")
        backend = QualifiedVerifierBackend(Path(roughtime_verifier_binary), roughtime_verifier_build_profile)

        qualifying: list[tuple[str, int]] = []
        seen_receipt_providers: set[str] = set()
        for receipt in receipt_evidence:
            provider_id = str(receipt.get("provider_id"))
            if provider_id in seen_receipt_providers:
                raise ValueError("duplicate receipt evidence for provider identity")
            if provider_id not in profiles_by_id or provider_id not in packages_by_id:
                raise ValueError("receipt provider is outside admitted set")
            seen_receipt_providers.add(provider_id)
            qualifying.append(
                _replay_receipt(
                    receipt,
                    subject_ref=subject_ref,
                    bundle_deadline_utc=bundle_deadline,
                    profile=profiles_by_id[provider_id],
                    state_package=packages_by_id[provider_id],
                    build_profile=roughtime_verifier_build_profile,
                    backend=backend,
                )
            )
        if len({provider for provider, _upper in qualifying}) < 2:
            raise ValueError("fewer than two independent admitted Roughtime providers qualify")
        conservative_upper = max(upper for _provider, upper in qualifying)
        verified_upper_bound = _ceil_ns_to_utc_seconds(conservative_upper)
        evidence_refs = [bundle_ref]
        evidence_refs.extend(_exact_ref(item) for item in receipt_evidence)
        evidence_refs.extend(_exact_ref(item) for item in qualification_state_packages)
        base = _claim(
            "EXTERNAL_EXISTENCE_BOUND_VERIFIED",
            subject_ref,
            "VERIFIED",
            reason_codes=("AUTHORITATIVE_ROUGHTIME_QUORUM_RECOMPUTED",),
            policy_refs=(quorum_policy_ref,),
            evidence_refs=evidence_refs,
            verified_upper_bound=verified_upper_bound,
        )
        deadline_claim = derive_deadline_existence_claim_strict(
            subject_ref,
            external_existence_claim=base,
            frozen_deadline=claim_deadline_utc,
        )
        return WallClockRecomputation(base, deadline_claim, bundle_ref)
    except Exception as exc:
        reason = "AUTHORITATIVE_EXTERNAL_EXISTENCE_RECOMPUTATION_FAILED"
        base = _claim(
            "EXTERNAL_EXISTENCE_BOUND_VERIFIED",
            subject_ref,
            "FAILED",
            reason_codes=(reason, type(exc).__name__.upper()),
            policy_refs=(quorum_policy_ref,),
        )
        deadline_claim = derive_deadline_existence_claim_strict(
            subject_ref,
            external_existence_claim=base,
            frozen_deadline=claim_deadline_utc,
        )
        return WallClockRecomputation(base, deadline_claim, _exact_ref(bundle) if verify_sealed_object(bundle) else subject_ref)


def _validate_bitcoin_verifier_contract(
    contract: Mapping[str, Any],
    *,
    expected_contract_ref: Mapping[str, Any],
    executable: Path,
) -> tuple[dict[str, str], PinnedExecutable]:
    contract_ref = _exact_ref(contract, object_type="StrongBitcoinVerifierContract")
    _require_ref_equal(contract_ref, expected_contract_ref, "strong Bitcoin verifier contract")
    expected = {
        "schema_version": "1.0",
        "protocol": BITCOIN_VERIFIER_PROTOCOL,
        "action": "verify-bitcoin-durability",
        "input_schema_version": "1.0",
        "output_schema_version": "1.0",
        "verification_mode": "OWNER_CONTROLLED_BITCOIN_CORE",
        "bitcoin_header_time_role": "DURABILITY_ONLY_NOT_CIVIL_TIME_BOUND",
    }
    for field, value in expected.items():
        if contract.get(field) != value:
            raise ValueError(f"strong Bitcoin verifier contract {field} mismatch")
    timeout = contract.get("timeout_seconds")
    if type(timeout) is not int or not (1 <= timeout <= 300):
        raise ValueError("strong Bitcoin verifier timeout invalid")
    pinned = PinnedExecutable.load(
        Path(executable),
        contract.get("executable_sha256"),
        label="strong Bitcoin verifier executable",
    )
    return contract_ref, pinned


def _run_bitcoin_verifier(
    contract: Mapping[str, Any],
    *,
    executable: PinnedExecutable,
    bundle_bytes: bytes,
    proof_bytes: bytes,
) -> Mapping[str, Any]:
    bundle_sha = hashlib.sha256(bundle_bytes).hexdigest()
    proof_sha = hashlib.sha256(proof_bytes).hexdigest()
    request = {
        "schema_version": "1.0",
        "action": "verify-bitcoin-durability",
        "verification_mode": "OWNER_CONTROLLED_BITCOIN_CORE",
        "bundle_sha256": bundle_sha,
        "bundle_base64": base64.b64encode(bundle_bytes).decode("ascii"),
        "proof_sha256": proof_sha,
        "proof_base64": base64.b64encode(proof_bytes).decode("ascii"),
    }
    with executable.snapshot(prefix="fpp-bitcoin-verifier-") as snapshot:
        completed = subprocess.run(
            [str(snapshot)],
            input=canonical_json(request),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=int(contract["timeout_seconds"]),
        )
    if completed.returncode != 0:
        raise ValueError("strong Bitcoin verifier execution failed")
    try:
        output = parse_json_strict(completed.stdout.decode("utf-8"))
    except (UnicodeDecodeError, CanonicalizationError) as exc:
        raise ValueError("strong Bitcoin verifier output is not strict JSON") from exc
    if not isinstance(output, dict):
        raise ValueError("strong Bitcoin verifier output must be an object")
    common = {
        "schema_version": "1.0",
        "action": "verify-bitcoin-durability",
        "verification_mode": "OWNER_CONTROLLED_BITCOIN_CORE",
        "bundle_sha256": bundle_sha,
        "proof_sha256": proof_sha,
    }
    for field, value in common.items():
        if output.get(field) != value:
            raise ValueError(f"strong Bitcoin verifier output {field} mismatch")
    if type(output.get("verified")) is not bool:
        raise ValueError("strong Bitcoin verifier output verified must be boolean")
    if output["verified"]:
        required = set(common) | {
            "verified", "bitcoin_block_height", "bitcoin_block_hash",
            "bitcoin_header_sha256", "node_version",
        }
        if set(output) != required:
            raise ValueError("strong Bitcoin verifier success output keys mismatch")
        if type(output["bitcoin_block_height"]) is not int or output["bitcoin_block_height"] < 0:
            raise ValueError("bitcoin block height invalid")
        _require_hex64(output["bitcoin_block_hash"], "bitcoin_block_hash")
        _require_hex64(output["bitcoin_header_sha256"], "bitcoin_header_sha256")
        if not isinstance(output["node_version"], str) or not output["node_version"]:
            raise ValueError("node_version invalid")
    else:
        required = set(common) | {"verified", "reason_code"}
        if set(output) != required:
            raise ValueError("strong Bitcoin verifier failure output keys mismatch")
        if not isinstance(output["reason_code"], str) or not output["reason_code"]:
            raise ValueError("strong Bitcoin verifier failure reason missing")
    return output


def recompute_bitcoin_durability_claim_authoritatively(
    subject: Mapping[str, Any],
    *,
    bundle: Mapping[str, Any],
    proof_artifact: Mapping[str, Any],
    strong_verifier_contract: Mapping[str, Any],
    strong_verifier_executable: Path,
    validator_contract_ref: Mapping[str, Any],
    expected_validator_contract_ref: Mapping[str, Any],
    expected_strong_verifier_contract_ref: Mapping[str, Any],
    persisted_strong_report: Mapping[str, Any] | None = None,
) -> BitcoinRecomputation:
    """Execute the exact hash-pinned local strong verifier over exact bundle/proof bytes."""
    subject_ref = _exact_ref(subject)
    _require_ref_equal(validator_contract_ref, expected_validator_contract_ref, "active ValidatorContract")
    _validate_origin_evidence(bundle, "ExternalTimeEvidenceBundle")
    bundle_ref = _exact_ref(bundle, object_type="ExternalTimeEvidenceBundle")
    _require_ref_equal(bundle.get("subject_ref"), subject_ref, "Bitcoin bundle subject")
    _require_ref_equal(bundle.get("validator_contract_ref"), validator_contract_ref, "Bitcoin bundle validator contract")
    _validate_origin_evidence(proof_artifact, "OpenTimestampsProofArtifact")
    if proof_artifact.get("origin_class") != bundle.get("origin_class"):
        raise ValueError("OTS proof origin class differs from its bundle")
    proof_ref = _exact_ref(proof_artifact)
    _require_ref_equal(proof_artifact.get("external_time_evidence_bundle_ref"), bundle_ref, "OTS proof bundle")
    proof_bytes = _decode_canonical_base64(proof_artifact.get("proof_base64"), "proof_base64")
    if hashlib.sha256(proof_bytes).hexdigest() != proof_artifact.get("proof_sha256"):
        raise ValueError("OTS proof artifact hash mismatch")
    strong_contract_ref, pinned_executable = _validate_bitcoin_verifier_contract(
        strong_verifier_contract,
        expected_contract_ref=expected_strong_verifier_contract_ref,
        executable=strong_verifier_executable,
    )
    bundle_bytes = canonical_json(dict(bundle))
    output = _run_bitcoin_verifier(
        strong_verifier_contract,
        executable=pinned_executable,
        bundle_bytes=bundle_bytes,
        proof_bytes=proof_bytes,
    )
    report_payload: dict[str, Any] = {
        "schema_version": "1.0",
        "origin_class": "LIVE_OPERATIONAL" if proof_artifact.get("origin_class") == "LIVE_OPERATIONAL" else "SYNTHETIC",
        "prospective_eligible": False,
        "subject_ref": dict(subject_ref),
        "external_time_evidence_bundle_ref": bundle_ref,
        "ots_proof_ref": proof_ref,
        "strong_verifier_contract_ref": strong_contract_ref,
        "validator_contract_ref": dict(validator_contract_ref),
        "bundle_sha256": hashlib.sha256(bundle_bytes).hexdigest(),
        "proof_sha256": hashlib.sha256(proof_bytes).hexdigest(),
        "verification_mode": "OWNER_CONTROLLED_BITCOIN_CORE",
        "bitcoin_header_time_role": "DURABILITY_ONLY_NOT_CIVIL_TIME_BOUND",
        "verified": bool(output["verified"]),
    }
    if output["verified"]:
        report_payload.update(
            bitcoin_block_height=output["bitcoin_block_height"],
            bitcoin_block_hash=output["bitcoin_block_hash"],
            bitcoin_header_sha256=output["bitcoin_header_sha256"],
            node_version=output["node_version"],
        )
    else:
        report_payload["reason_code"] = output["reason_code"]
    report = seal_object(
        report_payload,
        object_type="StrongBitcoinVerificationReport",
        stable_context=f"bitcoin-{bundle_ref['content_sha256'][:12]}",
    )
    if persisted_strong_report is not None and dict(persisted_strong_report) != report:
        raise ValueError("persisted strong Bitcoin verification report differs from recomputation")
    claim = derive_bitcoin_durability_claim(
        subject_ref,
        bundle_subject_ref=bundle.get("subject_ref"),
        ots_bundle_binding_verified=True,
        strong_bitcoin_verification_passed=bool(output["verified"]),
        evidence_refs=(bundle_ref, proof_ref, strong_contract_ref, _exact_ref(report)),
    )
    return BitcoinRecomputation(claim, bundle_ref, proof_ref, report)


def build_validation_report_v2(
    candidate_object: Mapping[str, Any],
    *,
    validator_contract_ref: Mapping[str, Any],
    trusted_manifest_ref: Mapping[str, Any],
    dependency_refs: Sequence[Mapping[str, Any]],
    validation: Validation,
    derived_claims: Sequence[Mapping[str, Any]],
    manifest_acceptance_ref: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    candidate_ref = _exact_ref(candidate_object)
    validate_ref(validator_contract_ref)
    validate_ref(trusted_manifest_ref)
    claims = [dict(item) for item in derived_claims]
    claims.sort(key=lambda item: (
        str(item.get("claim_type")),
        str(item.get("subject_ref", {}).get("object_id")),
        str(item.get("subject_ref", {}).get("content_sha256")),
    ))
    if not validate_derived_claim_vector(claims).valid:
        raise ValueError("derived claim vector is structurally invalid")
    payload: dict[str, Any] = {
        "schema_version": "2.0",
        "validator_contract_ref": dict(validator_contract_ref),
        "trusted_manifest_ref": dict(trusted_manifest_ref),
        "candidate_object_ref": candidate_ref,
        "dependency_refs": sorted_refs(dependency_refs),
        "result": validation.result.value,
        "checks": [
            {"check_id": check.check_id, "status": check.status, "reason_code": check.reason_code}
            for check in validation.checks
        ],
        "derived_claims": claims,
    }
    if manifest_acceptance_ref is not None:
        validate_ref(manifest_acceptance_ref)
        payload["manifest_acceptance_ref"] = dict(manifest_acceptance_ref)
    return seal_object(
        payload,
        object_type="ValidationReport",
        stable_context=f"v2-{candidate_ref['content_sha256'][:12]}-{validator_contract_ref['content_sha256'][:12]}",
    )


def compare_persisted_validation_report_to_recomputed(
    persisted_report: Mapping[str, Any],
    recomputed_report: Mapping[str, Any],
) -> Validation:
    """Equality-only audit helper. It grants no authority unless recomputed_report came from raw evidence."""
    checks = [
        _check("validation_report_recompute.persisted_seal", verify_sealed_object(persisted_report), "INVALID_PERSISTED_VALIDATION_REPORT"),
        _check("validation_report_recompute.recomputed_seal", verify_sealed_object(recomputed_report), "INVALID_RECOMPUTED_VALIDATION_REPORT"),
        _check("validation_report_recompute.exact", dict(persisted_report) == dict(recomputed_report), "PERSISTED_VALIDATION_REPORT_RECOMPUTATION_MISMATCH"),
    ]
    return aggregate(checks)


def _require_live_wall_inputs(inputs: Mapping[str, Any]) -> None:
    bundle = inputs.get("bundle")
    _validate_origin_evidence(bundle, "ExternalTimeEvidenceBundle")
    if bundle.get("origin_class") != "LIVE_OPERATIONAL":
        raise ValueError("production readiness requires LIVE_OPERATIONAL wall-clock bundle")
    receipts = inputs.get("receipt_evidence")
    if not isinstance(receipts, Sequence) or isinstance(receipts, (str, bytes, bytearray)):
        raise ValueError("wall-clock receipt evidence must be a sequence")
    for receipt in receipts:
        _validate_origin_evidence(receipt, "RoughtimeProductionReceiptEvidence")
        if receipt.get("origin_class") != "LIVE_OPERATIONAL":
            raise ValueError("production readiness requires LIVE_OPERATIONAL Roughtime evidence")


def _require_live_bitcoin_inputs(inputs: Mapping[str, Any]) -> None:
    bundle = inputs.get("bundle")
    proof = inputs.get("proof_artifact")
    _validate_origin_evidence(bundle, "ExternalTimeEvidenceBundle")
    _validate_origin_evidence(proof, "OpenTimestampsProofArtifact")
    if bundle.get("origin_class") != "LIVE_OPERATIONAL" or proof.get("origin_class") != "LIVE_OPERATIONAL":
        raise ValueError("production readiness requires LIVE_OPERATIONAL Bitcoin evidence")
    if bundle.get("origin_class") != proof.get("origin_class"):
        raise ValueError("Bitcoin proof origin class differs from its bundle")


def _genesis_non_scientific_claims(subject_ref: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    pre_outcome = _claim(
        "PRE_OUTCOME_DURABILITY_VERIFIED",
        subject_ref,
        "NOT_APPLICABLE",
        reason_codes=("NO_OUTCOME_INFORMATION_BARRIER",),
    )
    scientific = _claim(
        "CONFIRMATORY_PROSPECTIVE_ELIGIBLE",
        subject_ref,
        "NOT_APPLICABLE",
        reason_codes=("SCIENTIFIC_ELIGIBILITY_NOT_APPLICABLE",),
    )
    return pre_outcome, scientific


def _collect_authority_dependency_refs(value: Any) -> list[dict[str, str]]:
    found: dict[tuple[str, str], dict[str, str]] = {}

    def visit(item: Any) -> None:
        if isinstance(item, Mapping):
            if verify_sealed_object(item):
                exact = _exact_ref(item)
                found[(exact["object_id"], exact["content_sha256"])] = exact
                return
            if set(item) == {"object_id", "content_sha256"}:
                try:
                    validate_ref(item)
                except CanonicalizationError:
                    return
                exact = {"object_id": item["object_id"], "content_sha256": item["content_sha256"]}
                found[(exact["object_id"], exact["content_sha256"])] = exact
                return
            for child in item.values():
                visit(child)
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            for child in item:
                visit(child)

    visit(value)
    return sorted_refs(found.values())


def validate_persisted_final_acceptance_report_authoritatively(
    persisted_report: Mapping[str, Any],
    acceptance: Mapping[str, Any],
    *,
    final_evidence_subject_ref: Mapping[str, Any],
    wall_clock_inputs: Mapping[str, Any],
    bitcoin_inputs: Mapping[str, Any],
    trusted_manifest_ref: Mapping[str, Any],
) -> tuple[Validation, Mapping[str, Any]]:
    """Recompute final evidence from raw inputs before comparing a persisted ValidationReport."""
    validation, claims, strong_report = validate_final_genesis_acceptance_authoritatively(
        acceptance,
        final_evidence_subject_ref=final_evidence_subject_ref,
        wall_clock_inputs=wall_clock_inputs,
        bitcoin_inputs=bitcoin_inputs,
    )
    validator_ref = wall_clock_inputs["validator_contract_ref"]
    _require_ref_equal(bitcoin_inputs["validator_contract_ref"], validator_ref, "final report ValidatorContract")
    dependencies = _collect_authority_dependency_refs(
        {
            "wall": wall_clock_inputs,
            "bitcoin": bitcoin_inputs,
            "strong_report": strong_report,
        }
    )
    recomputed = build_validation_report_v2(
        acceptance,
        validator_contract_ref=validator_ref,
        trusted_manifest_ref=trusted_manifest_ref,
        dependency_refs=dependencies,
        validation=validation,
        derived_claims=claims,
    )
    return compare_persisted_validation_report_to_recomputed(persisted_report, recomputed), recomputed


def validate_persisted_cycle_plan_report_authoritatively(
    persisted_report: Mapping[str, Any],
    plan: Mapping[str, Any],
    *,
    required_slots: Sequence[Mapping[str, Any]],
    required_schedule_policy_ref: Mapping[str, Any],
    wall_clock_inputs: Mapping[str, Any],
    trusted_manifest_ref: Mapping[str, Any],
) -> tuple[Validation, Mapping[str, Any]]:
    """Recompute cycle-plan time claims from raw evidence before report equality."""
    validation, wall = validate_cycle_plan_authoritatively(
        plan,
        required_slots=required_slots,
        required_schedule_policy_ref=required_schedule_policy_ref,
        wall_clock_inputs=wall_clock_inputs,
    )
    dependencies = _collect_authority_dependency_refs(
        {"wall": wall_clock_inputs, "schedule_policy_ref": required_schedule_policy_ref, "required_slots": required_slots}
    )
    recomputed = build_validation_report_v2(
        plan,
        validator_contract_ref=wall_clock_inputs["validator_contract_ref"],
        trusted_manifest_ref=trusted_manifest_ref,
        dependency_refs=dependencies,
        validation=validation,
        derived_claims=(wall.external_existence_claim, wall.deadline_existence_claim),
    )
    return compare_persisted_validation_report_to_recomputed(persisted_report, recomputed), recomputed


def validate_cycle_plan_authoritatively(
    plan: Mapping[str, Any],
    *,
    required_slots: Sequence[Mapping[str, Any]],
    required_schedule_policy_ref: Mapping[str, Any],
    wall_clock_inputs: Mapping[str, Any],
) -> tuple[Validation, WallClockRecomputation]:
    """Successor path: raw existence bounds are not accepted."""
    if not verify_sealed_object(plan):
        raise ValueError("successor cycle plan must be a valid sealed object")
    _require_live_wall_inputs(wall_clock_inputs)
    wall = recompute_external_existence_claim_authoritatively(
        plan,
        claim_deadline_utc=str(plan["plan_commitment_deadline"]),
        **dict(wall_clock_inputs),
    )
    structural = validate_cycle_plan(
        plan,
        verified_plan_existence_bound=wall.external_existence_claim.get("verified_upper_bound") if wall.external_existence_claim.get("state") == "VERIFIED" else None,
        verified_plan_ref=_exact_ref(plan),
        required_slots=required_slots,
        required_schedule_policy_ref=required_schedule_policy_ref,
    )
    checks = list(structural.checks)
    checks.append(_check(
        "cycle_plan_authority.deadline_claim",
        wall.deadline_existence_claim.get("state") == "VERIFIED",
        "PLAN_DEADLINE_EXISTENCE_NOT_AUTHORITATIVELY_VERIFIED",
    ))
    return aggregate(checks), wall


def validate_final_genesis_acceptance_authoritatively(
    acceptance: Mapping[str, Any],
    *,
    final_evidence_subject_ref: Mapping[str, Any],
    wall_clock_inputs: Mapping[str, Any],
    bitcoin_inputs: Mapping[str, Any],
) -> tuple[Validation, tuple[Mapping[str, Any], ...], Mapping[str, Any]]:
    """Final Genesis validation from raw evidence only; no state strings are accepted."""
    acceptance_ref = _exact_ref(acceptance, object_type="ManifestAcceptance")
    _require_ref_equal(final_evidence_subject_ref, acceptance_ref, "final evidence subject")
    _require_live_wall_inputs(wall_clock_inputs)
    _require_live_bitcoin_inputs(bitcoin_inputs)
    wall_bundle_ref = _exact_ref(wall_clock_inputs["bundle"], object_type="ExternalTimeEvidenceBundle")
    bitcoin_bundle_ref = _exact_ref(bitcoin_inputs["bundle"], object_type="ExternalTimeEvidenceBundle")
    if wall_bundle_ref != bitcoin_bundle_ref:
        raise ValueError("final acceptance wall-clock and Bitcoin evidence must use the same exact ExternalTimeEvidenceBundle")
    wall = recompute_external_existence_claim_authoritatively(
        acceptance,
        claim_deadline_utc=None,
        **dict(wall_clock_inputs),
    )
    bitcoin = recompute_bitcoin_durability_claim_authoritatively(
        acceptance,
        **dict(bitcoin_inputs),
    )
    pre_outcome, scientific = _genesis_non_scientific_claims(acceptance_ref)
    checks = validate_final_genesis_acceptance(
        acceptance,
        final_evidence_subject_ref=final_evidence_subject_ref,
        external_existence_state=str(wall.external_existence_claim["state"]),
        bitcoin_durability_state=str(bitcoin.bitcoin_durability_claim["state"]),
    )
    claims = (
        wall.external_existence_claim,
        wall.deadline_existence_claim,
        bitcoin.bitcoin_durability_claim,
        pre_outcome,
        scientific,
    )
    return checks, claims, bitcoin.strong_verification_report


def recompute_pre_outcome_durability_authoritatively(
    primary_subject: Mapping[str, Any],
    *,
    bitcoin_inputs: Mapping[str, Any],
    durability_record: Mapping[str, Any],
    durability_record_wall_clock_inputs: Mapping[str, Any],
) -> tuple[Mapping[str, Any], BitcoinRecomputation, WallClockRecomputation]:
    primary_ref = _exact_ref(primary_subject)
    bitcoin = recompute_bitcoin_durability_claim_authoritatively(primary_subject, **dict(bitcoin_inputs))
    dvr_ref = _exact_ref(durability_record, object_type="DurabilityVerificationRecord")
    _require_ref_equal(durability_record.get("primary_subject_ref"), primary_ref, "DVR primary subject")
    _require_ref_equal(
        durability_record.get("external_time_evidence_bundle_ref"),
        bitcoin.evidence_bundle_ref,
        "DVR primary external-time bundle",
    )
    _require_ref_equal(durability_record.get("ots_proof_ref"), bitcoin.proof_artifact_ref, "DVR OTS proof")
    _require_ref_equal(
        durability_record.get("strong_verification_report_ref"),
        _exact_ref(bitcoin.strong_verification_report),
        "DVR strong verification report",
    )
    barrier = durability_record.get("outcome_information_barrier")
    from .canonical import require_utc_timestamp
    require_utc_timestamp(barrier)
    wall = recompute_external_existence_claim_authoritatively(
        durability_record,
        claim_deadline_utc=str(barrier),
        **dict(durability_record_wall_clock_inputs),
    )
    claim = derive_pre_outcome_durability_claim_strict(
        primary_ref,
        bitcoin_durability_claim=bitcoin.bitcoin_durability_claim,
        durability_record_deadline_claim=wall.deadline_existence_claim,
        durability_record_subject_ref=dvr_ref,
        durability_record_bound_subject_ref=durability_record.get("primary_subject_ref"),
        applicable=True,
    )
    return claim, bitcoin, wall


def derive_confirmatory_eligibility_from_evidence(
    forecast: Mapping[str, Any],
    *,
    component_specs: Sequence[Mapping[str, Any]],
    required_claim_requirements: Sequence[Mapping[str, Any]],
    hard_invalidation_reason_codes: Sequence[str] = (),
) -> tuple[Mapping[str, Any], tuple[Mapping[str, Any], ...]]:
    """Recompute component claims from evidence specs; caller-supplied claim mappings are never accepted."""
    forecast_ref = _exact_ref(forecast)
    claims: list[Mapping[str, Any]] = []
    for spec in component_specs:
        kind = spec.get("kind")
        required_subject_ref = spec.get("required_subject_ref")
        validate_ref(required_subject_ref)
        if kind == "wall_clock_deadline":
            subject = spec["subject"]
            if _exact_ref(subject) != dict(required_subject_ref):
                raise ValueError("wall-clock component subject substitution")
            _require_live_wall_inputs(spec["authority_inputs"])
            wall = recompute_external_existence_claim_authoritatively(
                subject,
                claim_deadline_utc=spec["claim_deadline_utc"],
                **dict(spec["authority_inputs"]),
            )
            claims.append(wall.deadline_existence_claim)
        elif kind == "bitcoin_durability":
            subject = spec["subject"]
            if _exact_ref(subject) != dict(required_subject_ref):
                raise ValueError("Bitcoin component subject substitution")
            _require_live_bitcoin_inputs(spec["authority_inputs"])
            bitcoin = recompute_bitcoin_durability_claim_authoritatively(
                subject,
                **dict(spec["authority_inputs"]),
            )
            claims.append(bitcoin.bitcoin_durability_claim)
        elif kind == "pre_outcome_durability":
            subject = spec["subject"]
            if _exact_ref(subject) != dict(required_subject_ref):
                raise ValueError("pre-outcome component subject substitution")
            pre_inputs = spec["authority_inputs"]
            _require_live_bitcoin_inputs(pre_inputs["bitcoin_inputs"])
            _require_live_wall_inputs(pre_inputs["durability_record_wall_clock_inputs"])
            if pre_inputs["durability_record"].get("origin_class") != "LIVE_OPERATIONAL":
                raise ValueError("production eligibility requires LIVE_OPERATIONAL DurabilityVerificationRecord")
            claim, _bitcoin, _wall = recompute_pre_outcome_durability_authoritatively(
                subject,
                **dict(pre_inputs),
            )
            claims.append(claim)
        elif kind == "external_existence":
            subject = spec["subject"]
            if _exact_ref(subject) != dict(required_subject_ref):
                raise ValueError("external-existence component subject substitution")
            _require_live_wall_inputs(spec["authority_inputs"])
            wall = recompute_external_existence_claim_authoritatively(
                subject,
                claim_deadline_utc=None,
                **dict(spec["authority_inputs"]),
            )
            claims.append(wall.external_existence_claim)
        else:
            raise ValueError("unknown authoritative component kind")
    eligibility = derive_confirmatory_eligibility_strict(
        forecast_ref,
        required_claims=claims,
        required_claim_requirements=required_claim_requirements,
        hard_invalidation_reason_codes=hard_invalidation_reason_codes,
        applicable=True,
    )
    return eligibility, tuple(claims)
