from __future__ import annotations

import pytest

import forecast_trust_core.claim_authority_trust_root_v1 as trust_root
from forecast_trust_core.canonical import seal_object


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def sealed(kind, object_id, **payload):
    return seal_object(
        {"schema_version": "1.0", **payload},
        object_type=kind,
        stable_context="claim-authority-trust-root-test",
        semantic_id=object_id,
    )


def manifest_fixture():
    validator = sealed("ValidatorContract", "validator:trust-root:v1", value="validator")
    quorum = sealed("PolicyDefinition", "policy:quorum:trust-root:v1", value="quorum")
    qualification_verifier = sealed("ValidatorContract", "validator:qualification:trust-root:v1", value="qualification")
    strong_bitcoin = sealed("StrongBitcoinVerifierContract", "validator:bitcoin:trust-root:v1", value="bitcoin")
    targets = [
        sealed("TargetDefinition", f"target:t{index}:v1", value=f"target-{index}")
        for index in range(3)
    ]
    resolutions = [
        sealed("ResolutionRule", f"resolution:r{index}:v1", value=f"resolution-{index}")
        for index in range(3)
    ]
    methods = [sealed("ForecastMethod", "method:m0:v1", value="method")]
    sources = [
        sealed("SourceContract", f"source:s{index}:v1", value=f"source-{index}")
        for index in range(6)
    ]
    schedule = sealed(
        "PolicyDefinition",
        "policy:schedule:trust-root:v2",
        value="schedule",
        canonical_runtime_contract_version="GENESIS_RUNTIME_CONTRACT_V1",
    )
    retry = sealed("PolicyDefinition", "policy:retry:trust-root:v1", value="retry")
    omission = sealed("PolicyDefinition", "policy:omission:trust-root:v1", value="omission")
    correction = sealed("PolicyDefinition", "policy:correction:trust-root:v1", value="correction")
    evaluation = sealed("PolicyDefinition", "policy:evaluation:trust-root:v2", value="evaluation")
    profiles = [
        sealed("RoughtimeProductionProviderProfile", f"profile:p{index}:v1", provider_id=f"p{index}")
        for index in range(3)
    ]
    decisions = [
        sealed("RoughtimeQualificationDecision", f"decision:p{index}:v1", provider_id=f"p{index}")
        for index in range(3)
    ]
    manifest = sealed(
        "TrustedManifest",
        "manifest:trust-root:v1",
        manifest_sequence=1,
        target_refs=sorted((ref(item) for item in targets), key=lambda item: (item["object_id"], item["content_sha256"])),
        resolution_rule_refs=sorted((ref(item) for item in resolutions), key=lambda item: (item["object_id"], item["content_sha256"])),
        method_refs=sorted((ref(item) for item in methods), key=lambda item: (item["object_id"], item["content_sha256"])),
        source_contract_refs=sorted((ref(item) for item in sources), key=lambda item: (item["object_id"], item["content_sha256"])),
        issuance_schedule_policy_ref=ref(schedule),
        retry_policy_ref=ref(retry),
        omission_policy_ref=ref(omission),
        correction_policy_ref=ref(correction),
        evaluation_policy_ref=ref(evaluation),
        validator_contract_ref=ref(validator),
        deadline_receipt_quorum_policy_ref=ref(quorum),
        provider_profile_refs=sorted((ref(item) for item in profiles), key=lambda item: (item["object_id"], item["content_sha256"])),
        qualification_decision_refs=sorted((ref(item) for item in decisions), key=lambda item: (item["object_id"], item["content_sha256"])),
        qualification_verifier_contract_ref=ref(qualification_verifier),
        strong_bitcoin_verifier_contract_ref=ref(strong_bitcoin),
    )
    return {
        "manifest": manifest,
        "validator": validator,
        "quorum": quorum,
        "qualification_verifier": qualification_verifier,
        "strong_bitcoin": strong_bitcoin,
        "targets": targets,
        "resolutions": resolutions,
        "methods": methods,
        "sources": sources,
        "schedule": schedule,
        "retry": retry,
        "omission": omission,
        "correction": correction,
        "evaluation": evaluation,
        "profiles": profiles,
        "decisions": decisions,
    }


def state_packages(fx):
    return [
        sealed(
            "RoughtimeProviderQualificationStatePackage",
            f"state:p{index}:v1",
            provider_id=f"p{index}",
            qualification_decision_ref=ref(fx["decisions"][index]),
        )
        for index in range(3)
    ]


def test_manifest_authority_context_extracts_exact_roots():
    fx = manifest_fixture()
    context = trust_root.derive_genesis_runtime_v1_authority_context(
        fx["manifest"], fx["schedule"]
    )
    assert list(context.target_refs) == fx["manifest"]["target_refs"]
    assert list(context.resolution_rule_refs) == fx["manifest"]["resolution_rule_refs"]
    assert list(context.method_refs) == fx["manifest"]["method_refs"]
    assert list(context.source_contract_refs) == fx["manifest"]["source_contract_refs"]
    assert context.issuance_schedule_policy_ref == ref(fx["schedule"])
    assert context.retry_policy_ref == ref(fx["retry"])
    assert context.omission_policy_ref == ref(fx["omission"])
    assert context.correction_policy_ref == ref(fx["correction"])
    assert context.evaluation_policy_ref == ref(fx["evaluation"])
    assert context.validator_contract_ref == ref(fx["validator"])
    assert context.deadline_receipt_quorum_policy_ref == ref(fx["quorum"])
    assert context.strong_bitcoin_verifier_contract_ref == ref(fx["strong_bitcoin"])
    assert list(context.provider_profile_refs) == fx["manifest"]["provider_profile_refs"]
    assert list(context.qualification_decision_refs) == fx["manifest"]["qualification_decision_refs"]


def test_manifest_missing_scientific_root_fails_closed():
    fx = manifest_fixture()
    payload = {
        key: value for key, value in fx["manifest"].items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256", "method_refs"}
    }
    broken = seal_object(
        payload,
        object_type="TrustedManifest",
        stable_context="missing-method-root",
        semantic_id="manifest:missing-method-root:v1",
    )
    with pytest.raises(ValueError, match="method_refs"):
        trust_root.derive_genesis_runtime_v1_authority_context(
            broken, fx["schedule"]
        )


def test_manifest_missing_evaluation_policy_ref_fails_closed():
    fx = manifest_fixture()
    payload = {
        key: value for key, value in fx["manifest"].items()
        if key
        not in {
            "object_type",
            "object_id",
            "payload_sha256",
            "content_sha256",
            "evaluation_policy_ref",
        }
    }
    broken = seal_object(
        payload,
        object_type="TrustedManifest",
        stable_context="missing-evaluation-root",
        semantic_id="manifest:missing-evaluation-root:v1",
    )
    with pytest.raises(ValueError, match="evaluation_policy_ref"):
        trust_root.derive_genesis_runtime_v1_authority_context(
            broken, fx["schedule"]
        )


def test_manifest_malformed_evaluation_policy_ref_fails_closed():
    fx = manifest_fixture()
    payload = {
        key: value for key, value in fx["manifest"].items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    payload["evaluation_policy_ref"] = {"object_id": fx["evaluation"]["object_id"]}
    broken = seal_object(
        payload,
        object_type="TrustedManifest",
        stable_context="malformed-evaluation-root",
        semantic_id="manifest:malformed-evaluation-root:v1",
    )
    with pytest.raises(ValueError, match="evaluation_policy_ref"):
        trust_root.derive_genesis_runtime_v1_authority_context(
            broken, fx["schedule"]
        )


def test_manifest_evaluation_policy_ref_is_extracted_as_exact_value():
    fx = manifest_fixture()
    context = trust_root.derive_genesis_runtime_v1_authority_context(
        fx["manifest"], fx["schedule"]
    )
    assert context.evaluation_policy_ref == fx["manifest"]["evaluation_policy_ref"]


def test_genesis_runtime_confirmatory_requires_complete_authoritative_components():
    fx = manifest_fixture()
    forecast = sealed("IssuedForecast", "forecast:genesis-runtime:v1", value="forecast")
    with pytest.raises(ValueError, match="Genesis v1 authoritative component set incomplete"):
        trust_root.derive_confirmatory_eligibility_from_genesis_runtime_v1(
            fx["manifest"],
            fx["schedule"],
            forecast,
            component_specs=[],
            required_claim_requirements=[],
        )


@pytest.mark.parametrize(
    "runtime_contract_version", [None, "CALLER_SELECTED_RUNTIME_V1"]
)
def test_cycle_plan_wrapper_executes_frozen_historical_validation(
    monkeypatch, runtime_contract_version
):
    fx = manifest_fixture()
    schedule_fields = {"value": "historical-schedule"}
    if runtime_contract_version is not None:
        schedule_fields["canonical_runtime_contract_version"] = runtime_contract_version
    schedule = sealed(
        "PolicyDefinition", "policy:schedule:historical:v1", **schedule_fields
    )
    manifest_payload = {
        key: value
        for key, value in fx["manifest"].items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    manifest_payload["issuance_schedule_policy_ref"] = ref(schedule)
    manifest = seal_object(
        manifest_payload,
        object_type="TrustedManifest",
        stable_context="claim-authority-trust-root-test",
        semantic_id=fx["manifest"]["object_id"],
    )
    plan = sealed(
        "IssuanceCyclePlan",
        "plan:historical-wrapper:v1",
        plan_commitment_deadline="2026-09-10T00:00:00Z",
        execution_window_open="2026-09-11T00:00:00Z",
        execution_window_close="2026-09-12T00:00:00Z",
        schedule_policy_ref=ref(schedule),
    )
    required_slots = [ref(fx["targets"][0])]
    wall_clock_inputs = {"historical": "inputs"}
    bound_wall_clock_inputs = {"manifest": "bound"}
    expected = (object(), object())
    calls = []

    def fake_bind(manifest, inputs, **kwargs):
        calls.append(("bind", manifest, inputs, kwargs))
        return bound_wall_clock_inputs

    def fake_validate(candidate, **kwargs):
        calls.append(("validate", candidate, kwargs))
        return expected

    monkeypatch.setattr(trust_root, "bind_wall_clock_inputs_to_manifest", fake_bind)
    monkeypatch.setattr(trust_root, "validate_cycle_plan_authoritatively", fake_validate)

    result = trust_root.validate_cycle_plan_from_trusted_manifest(
        manifest,
        plan,
        required_slots=required_slots,
        required_schedule_policy_ref=ref(schedule),
        wall_clock_inputs=wall_clock_inputs,
    )

    assert result is expected
    assert calls == [
        (
            "bind",
            manifest,
            wall_clock_inputs,
            {
                "qualification_authority_id": None,
                "qualification_authority_public_key": None,
            },
        ),
        (
            "validate",
            plan,
            {
                "required_slots": required_slots,
                "required_schedule_policy_ref": ref(schedule),
                "wall_clock_inputs": bound_wall_clock_inputs,
            },
        ),
    ]


def test_manifest_missing_strong_bitcoin_verifier_ref_fails_closed():
    fx = manifest_fixture()
    payload = {
        key: value for key, value in fx["manifest"].items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256", "strong_bitcoin_verifier_contract_ref"}
    }
    broken = seal_object(
        payload,
        object_type="TrustedManifest",
        stable_context="missing-bitcoin",
        semantic_id="manifest:missing-bitcoin:v1",
    )
    with pytest.raises(ValueError, match="strong_bitcoin_verifier_contract_ref"):
        trust_root.derive_trusted_manifest_authority_context(broken)


def test_self_asserted_manifest_status_is_rejected():
    fx = manifest_fixture()
    payload = {
        key: value for key, value in fx["manifest"].items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    payload["status"] = "ACCEPTED"
    broken = seal_object(
        payload,
        object_type="TrustedManifest",
        stable_context="self-status",
        semantic_id="manifest:self-status:v1",
    )
    with pytest.raises(ValueError, match="self-assert"):
        trust_root.derive_trusted_manifest_authority_context(broken)


def test_caller_cannot_substitute_main_validator_with_matching_expected_ref():
    fx = manifest_fixture()
    malicious = sealed("ValidatorContract", "validator:malicious:v1", value="malicious")
    inputs = {
        "provider_profiles": fx["profiles"],
        "qualification_state_packages": state_packages(fx),
        "validator_contract_ref": ref(malicious),
        "expected_validator_contract_ref": ref(malicious),
    }
    with pytest.raises(ValueError, match="caller authority override prohibited"):
        trust_root.bind_wall_clock_inputs_to_manifest(fx["manifest"], inputs)


def test_caller_cannot_substitute_quorum_or_qualification_verifier():
    fx = manifest_fixture()
    inputs = {
        "provider_profiles": fx["profiles"],
        "qualification_state_packages": state_packages(fx),
        "quorum_policy_ref": {"object_id": "policy:malicious", "content_sha256": "1" * 64},
        "qualification_verifier_contract_ref": {"object_id": "validator:malicious", "content_sha256": "2" * 64},
    }
    with pytest.raises(ValueError, match="caller authority override prohibited"):
        trust_root.bind_wall_clock_inputs_to_manifest(fx["manifest"], inputs)


def test_provider_profile_substitution_fails_against_manifest():
    fx = manifest_fixture()
    substitute = sealed("RoughtimeProductionProviderProfile", "profile:substitute:v1", provider_id="p0")
    profiles = [substitute, fx["profiles"][1], fx["profiles"][2]]
    inputs = {
        "provider_profiles": profiles,
        "qualification_state_packages": state_packages(fx),
    }
    with pytest.raises(ValueError, match="ProviderProfile set differs"):
        trust_root.bind_wall_clock_inputs_to_manifest(fx["manifest"], inputs)


def test_qualification_decision_substitution_fails_against_manifest():
    fx = manifest_fixture()
    packages = state_packages(fx)
    substitute = sealed("RoughtimeQualificationDecision", "decision:substitute:v1", provider_id="p0")
    packages[0] = sealed(
        "RoughtimeProviderQualificationStatePackage",
        "state:substitute:v1",
        provider_id="p0",
        qualification_decision_ref=ref(substitute),
    )
    with pytest.raises(ValueError, match="QualificationDecision set differs"):
        trust_root.bind_wall_clock_inputs_to_manifest(
            fx["manifest"],
            {"provider_profiles": fx["profiles"], "qualification_state_packages": packages},
        )


def test_caller_cannot_substitute_strong_bitcoin_verifier_with_matching_expected_ref():
    fx = manifest_fixture()
    malicious = sealed("StrongBitcoinVerifierContract", "validator:bitcoin:malicious:v1", value="malicious")
    inputs = {
        "strong_verifier_contract": malicious,
        "expected_strong_verifier_contract_ref": ref(malicious),
    }
    with pytest.raises(ValueError, match="caller authority override prohibited"):
        trust_root.bind_bitcoin_inputs_to_manifest(fx["manifest"], inputs)


def test_strong_bitcoin_verifier_contract_must_equal_manifest_ref():
    fx = manifest_fixture()
    substitute = sealed("StrongBitcoinVerifierContract", "validator:bitcoin:substitute:v1", value="substitute")
    with pytest.raises(ValueError, match="differs from TrustedManifest"):
        trust_root.bind_bitcoin_inputs_to_manifest(
            fx["manifest"], {"strong_verifier_contract": substitute}
        )


def test_manifest_acceptance_must_bind_same_trusted_manifest_before_final_evidence(monkeypatch):
    fx = manifest_fixture()
    other_manifest = sealed(
        "TrustedManifest",
        "manifest:other:v1",
        **{
            key: value
            for key, value in fx["manifest"].items()
            if key
            not in {
                "schema_version",
                "object_type",
                "object_id",
                "payload_sha256",
                "content_sha256",
            }
        },
    )
    acceptance = sealed(
        "ManifestAcceptance",
        "acceptance:wrong-manifest:v2",
        candidate_manifest_ref=ref(other_manifest),
    )
    with pytest.raises(ValueError, match="exact TrustedManifest authority root"):
        trust_root.validate_final_genesis_acceptance_from_trusted_manifest(
            fx["manifest"],
            acceptance,
            final_evidence_subject_ref=ref(acceptance),
            wall_clock_inputs={},
            bitcoin_inputs={},
        )
