from __future__ import annotations

from pathlib import Path

import pytest

import forecast_trust_core.claim_authority_v1 as authority
import forecast_trust_core.genesis_final_acceptance_authority_v1 as final_authority
from forecast_trust_core.canonical import seal_object


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def sealed(kind, object_id, *, schema_version="1.0", **payload):
    return seal_object(
        {"schema_version": schema_version, **payload},
        object_type=kind,
        stable_context="genesis-final-acceptance-authority-test",
        semantic_id=object_id,
    )


def acceptance_fixture(*, decision="ACCEPT", blocking=()):
    manifest = sealed("TrustedManifest", "manifest:final-acceptance:v1", value="manifest")
    root = sealed("BootstrapGovernanceRoot", "bootstrap:final-acceptance:v1", value="root")
    rule = sealed("PolicyDefinition", "policy:genesis-acceptance:v2", value="rule")
    report = sealed("ValidationReport", "validation:final-acceptance:v1", value="report")
    signature = sealed("GenesisGovernanceSignature", "signature:final-acceptance:v1", value="sig")
    acceptance = sealed(
        "ManifestAcceptance",
        "acceptance:final-acceptance:v2",
        schema_version="2.0",
        candidate_manifest_ref=ref(manifest),
        bootstrap_governance_root_ref=ref(root),
        acceptance_rule_ref=ref(rule),
        required_validation_report_refs=[ref(report)],
        authority_ref=ref(root),
        decision=decision,
        reason_codes=[],
        blocking_finding_refs=list(blocking),
        signature_ref=ref(signature),
    )
    return acceptance


def live_final_inputs():
    validator = sealed("ValidatorContract", "validator:final-acceptance:v1", value="validator")
    bundle = sealed(
        "ExternalTimeEvidenceBundle",
        "bundle:final-acceptance:v1",
        origin_class="LIVE_OPERATIONAL",
        prospective_eligible=False,
    )
    proof = sealed(
        "OpenTimestampsProofArtifact",
        "proof:final-acceptance:v1",
        origin_class="LIVE_OPERATIONAL",
        prospective_eligible=False,
    )
    return (
        {"bundle": bundle, "receipt_evidence": [], "validator_contract_ref": ref(validator)},
        {"bundle": bundle, "proof_artifact": proof, "validator_contract_ref": ref(validator)},
    )


def patch_final_input_contracts(monkeypatch):
    monkeypatch.setattr(authority._gate, "validate_wall_inputs", lambda _inputs: None)
    monkeypatch.setattr(authority, "_validate_bitcoin_inputs_for_recomputation", lambda _inputs: None)


def test_final_acceptance_requires_governance_signature_inputs(monkeypatch):
    acceptance = acceptance_fixture()
    wall, bitcoin = live_final_inputs()
    patch_final_input_contracts(monkeypatch)
    monkeypatch.setattr(
        authority._legacy,
        "validate_final_genesis_acceptance_authoritatively",
        lambda *args, **kwargs: pytest.fail("legacy final validation must not run without owner signature authority"),
    )
    with pytest.raises(ValueError, match="governance signature inputs are required"):
        authority.validate_final_genesis_acceptance_authoritatively(
            acceptance,
            final_evidence_subject_ref=ref(acceptance),
            wall_clock_inputs=wall,
            bitcoin_inputs=bitcoin,
        )


def test_reject_decision_fails_before_governance_crypto(monkeypatch):
    acceptance = acceptance_fixture(decision="REJECT")
    wall, bitcoin = live_final_inputs()
    called = []
    monkeypatch.setattr(
        authority,
        "_validate_genesis_governance_signature_inputs",
        lambda *args, **kwargs: called.append(True),
    )
    with pytest.raises(ValueError, match="decision must be ACCEPT"):
        authority.validate_final_genesis_acceptance_authoritatively(
            acceptance,
            final_evidence_subject_ref=ref(acceptance),
            wall_clock_inputs=wall,
            bitcoin_inputs=bitcoin,
        )
    assert called == []


def test_blocking_finding_fails_before_governance_crypto(monkeypatch):
    finding = sealed("BlockingFinding", "finding:blocking:v1", value="open")
    acceptance = acceptance_fixture(blocking=(ref(finding),))
    wall, bitcoin = live_final_inputs()
    called = []
    monkeypatch.setattr(
        authority,
        "_validate_genesis_governance_signature_inputs",
        lambda *args, **kwargs: called.append(True),
    )
    with pytest.raises(ValueError, match="blocking findings must be empty"):
        authority.validate_final_genesis_acceptance_authoritatively(
            acceptance,
            final_evidence_subject_ref=ref(acceptance),
            wall_clock_inputs=wall,
            bitcoin_inputs=bitcoin,
        )
    assert called == []


def trusted_manifest_fixture():
    validator = sealed("ValidatorContract", "validator:manifest-governance:v1", value="validator")
    quorum = sealed("PolicyDefinition", "policy:quorum:manifest-governance:v1", value="quorum")
    rule = sealed("PolicyDefinition", "policy:genesis-acceptance:binding:v2", value="rule")
    qualification_verifier = sealed(
        "RoughtimeQualificationVerifierContract",
        "validator:qualification:manifest-governance:v1",
        value="qualification",
    )
    strong_bitcoin = sealed(
        "StrongBitcoinVerifierContract",
        "validator:bitcoin:manifest-governance:v1",
        value="bitcoin",
    )
    governance_verifier = sealed(
        "GenesisGovernanceSignatureVerifierContract",
        "validator:genesis-governance-signature:v1",
        value="governance",
    )
    profiles = [
        sealed("RoughtimeProductionProviderProfile", f"profile:g{index}:v1", provider_id=f"g{index}")
        for index in range(3)
    ]
    decisions = [
        sealed("RoughtimeQualificationDecision", f"decision:g{index}:v1", provider_id=f"g{index}")
        for index in range(3)
    ]
    manifest = sealed(
        "TrustedManifest",
        "manifest:governance-binding:v1",
        manifest_sequence=1,
        validator_contract_ref=ref(validator),
        acceptance_rule_ref=ref(rule),
        deadline_receipt_quorum_policy_ref=ref(quorum),
        provider_profile_refs=sorted((ref(item) for item in profiles), key=lambda item: (item["object_id"], item["content_sha256"])),
        qualification_decision_refs=sorted((ref(item) for item in decisions), key=lambda item: (item["object_id"], item["content_sha256"])),
        qualification_verifier_contract_ref=ref(qualification_verifier),
        strong_bitcoin_verifier_contract_ref=ref(strong_bitcoin),
        genesis_governance_signature_verifier_contract_ref=ref(governance_verifier),
    )
    root = sealed("BootstrapGovernanceRoot", "bootstrap:governance-binding:v1", value="root")
    report = sealed("ValidationReport", "validation:governance-binding:v1", value="report")
    signature = sealed("GenesisGovernanceSignature", "signature:governance-binding:v1", value="sig")
    acceptance = sealed(
        "ManifestAcceptance",
        "acceptance:governance-binding:v2",
        schema_version="2.0",
        candidate_manifest_ref=ref(manifest),
        bootstrap_governance_root_ref=ref(root),
        acceptance_rule_ref=ref(rule),
        required_validation_report_refs=[ref(report)],
        authority_ref=ref(root),
        decision="ACCEPT",
        reason_codes=[],
        blocking_finding_refs=[],
        signature_ref=ref(signature),
    )
    return manifest, acceptance, governance_verifier, root, signature, validator


def test_manifest_bound_governance_verifier_contract_cannot_be_substituted(monkeypatch):
    manifest, acceptance, governance_verifier, root, signature, validator = trusted_manifest_fixture()
    substitute = sealed(
        "GenesisGovernanceSignatureVerifierContract",
        "validator:genesis-governance-signature:substitute:v1",
        value="substitute",
    )
    monkeypatch.setattr(
        final_authority._governance,
        "validate_governance_signature_verifier_contract",
        lambda *args, **kwargs: pytest.fail("substitute must be rejected before contract validation"),
    )
    with pytest.raises(ValueError, match="differs from TrustedManifest"):
        final_authority.bind_genesis_governance_signature_inputs_to_manifest(
            manifest,
            acceptance,
            signature_evidence=signature,
            bootstrap_root=root,
            governance_verifier_contract=substitute,
            ed25519_verifier_build_profile={"profile_sha256": "a" * 64, "binary_sha256": "b" * 64},
            ed25519_verifier_binary=Path("/synthetic/fpp-ed25519-verify"),
        )


def test_manifest_acceptance_rule_must_match_trusted_manifest(monkeypatch):
    manifest, acceptance, governance_verifier, root, signature, _validator = trusted_manifest_fixture()
    other_rule = sealed("PolicyDefinition", "policy:other-acceptance-rule:v2", value="other")
    acceptance_payload = {
        key: value
        for key, value in acceptance.items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256", "acceptance_rule_ref"}
    }
    broken_acceptance = seal_object(
        acceptance_payload | {"acceptance_rule_ref": ref(other_rule)},
        object_type="ManifestAcceptance",
        stable_context="wrong-manifest-acceptance-rule",
        semantic_id="acceptance:wrong-manifest-rule:v2",
    )
    monkeypatch.setattr(
        final_authority._governance,
        "validate_governance_signature_verifier_contract",
        lambda *args, **kwargs: pytest.fail("rule mismatch must fail before governance verifier validation"),
    )
    with pytest.raises(ValueError, match="acceptance rule differs from TrustedManifest"):
        final_authority.bind_genesis_governance_signature_inputs_to_manifest(
            manifest,
            broken_acceptance,
            signature_evidence=signature,
            bootstrap_root=root,
            governance_verifier_contract=governance_verifier,
            ed25519_verifier_build_profile={"profile_sha256": "a" * 64, "binary_sha256": "b" * 64},
            ed25519_verifier_binary=Path("/synthetic/fpp-ed25519-verify"),
        )


def test_manifest_bound_governance_inputs_use_manifest_validator(monkeypatch):
    manifest, acceptance, governance_verifier, root, signature, validator = trusted_manifest_fixture()
    captured = {}

    def fake_validate(contract, **kwargs):
        captured.update(kwargs)
        return b"\x00" * 32

    monkeypatch.setattr(
        final_authority._governance,
        "validate_governance_signature_verifier_contract",
        fake_validate,
    )
    context, bound = final_authority.bind_genesis_governance_signature_inputs_to_manifest(
        manifest,
        acceptance,
        signature_evidence=signature,
        bootstrap_root=root,
        governance_verifier_contract=governance_verifier,
        ed25519_verifier_build_profile={"profile_sha256": "a" * 64, "binary_sha256": "b" * 64},
        ed25519_verifier_binary=Path("/synthetic/fpp-ed25519-verify"),
    )
    assert captured["expected_validator_contract_ref"] == ref(validator)
    assert bound["expected_governance_verifier_contract_ref"] == ref(governance_verifier)
    assert context.trusted_manifest_ref == ref(manifest)


def test_manifest_missing_governance_verifier_ref_fails_closed(monkeypatch):
    manifest, acceptance, governance_verifier, root, signature, _validator = trusted_manifest_fixture()
    payload = {
        key: value
        for key, value in manifest.items()
        if key not in {
            "object_type",
            "object_id",
            "payload_sha256",
            "content_sha256",
            "genesis_governance_signature_verifier_contract_ref",
        }
    }
    broken_manifest = seal_object(
        payload,
        object_type="TrustedManifest",
        stable_context="missing-governance-verifier-ref",
        semantic_id="manifest:missing-governance-verifier:v1",
    )
    acceptance = seal_object(
        {
            key: value
            for key, value in acceptance.items()
            if key not in {"object_type", "object_id", "payload_sha256", "content_sha256", "candidate_manifest_ref"}
        }
        | {"candidate_manifest_ref": ref(broken_manifest)},
        object_type="ManifestAcceptance",
        stable_context="missing-governance-verifier-ref",
        semantic_id="acceptance:missing-governance-verifier:v2",
    )
    with pytest.raises(ValueError, match="genesis_governance_signature_verifier_contract_ref"):
        final_authority.bind_genesis_governance_signature_inputs_to_manifest(
            broken_manifest,
            acceptance,
            signature_evidence=signature,
            bootstrap_root=root,
            governance_verifier_contract=governance_verifier,
            ed25519_verifier_build_profile={"profile_sha256": "a" * 64, "binary_sha256": "b" * 64},
            ed25519_verifier_binary=Path("/synthetic/fpp-ed25519-verify"),
        )
