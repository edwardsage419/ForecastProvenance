from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

import forecast_trust_core.genesis_governance_authority_v1 as gov
from forecast_trust_core.canonical import content_hash, seal_object


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def sealed(kind, object_id, *, schema_version="1.0", **payload):
    return seal_object(
        {"schema_version": schema_version, **payload},
        object_type=kind,
        stable_context="genesis-governance-authority-test",
        semantic_id=object_id,
    )


def reseal(obj, **changes):
    payload = {
        key: value
        for key, value in obj.items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    payload.update(changes)
    return seal_object(
        payload,
        object_type=obj["object_type"],
        stable_context="genesis-governance-authority-test-mutation",
        semantic_id=obj["object_id"],
    )


class FakePinnedVerifier:
    result = True
    calls = []

    def __init__(self, binary_path, binary_sha256):
        self.binary_path = Path(binary_path)
        self.binary_sha256 = binary_sha256

    def __call__(self, public_key, message, signature):
        type(self).calls.append(
            (self.binary_path, self.binary_sha256, public_key, message, signature)
        )
        return type(self).result


def fixture_set():
    public_key = bytes(range(32))
    rule = sealed("PolicyDefinition", "policy:genesis-acceptance:v2", value="acceptance-rule")
    validator = sealed("ValidatorContract", "validator:genesis-governance:v1", value="validator")
    manifest = sealed("TrustedManifest", "manifest:genesis-governance:v1", value="manifest")
    report = sealed("ValidationReport", "validation:genesis-governance:v1", value="report")
    root = sealed(
        "BootstrapGovernanceRoot",
        "bootstrap:genesis:v1",
        project_id="ForecastProvenance",
        authority_id="owner:genesis:v1",
        authority_key_type="ED25519",
        authority_public_key_base64=base64.b64encode(public_key).decode("ascii"),
        acceptance_rule_ref=ref(rule),
        canonicalization_scheme="FPP_JCS_1",
        hash_algorithm="SHA-256",
        bootstrap_version=1,
    )
    build_profile = {
        "profile_sha256": "a" * 64,
        "binary_sha256": "b" * 64,
    }
    contract = sealed(
        "GenesisGovernanceSignatureVerifierContract",
        "validator:genesis-governance-signature:v1",
        validator_contract_ref=ref(validator),
        signature_algorithm="ED25519",
        authority_id=root["authority_id"],
        authority_public_key_sha256=hashlib.sha256(public_key).hexdigest(),
        ed25519_verifier_build_profile_sha256=build_profile["profile_sha256"],
        ed25519_verifier_binary_sha256=build_profile["binary_sha256"],
        allowed_signature_projections=[gov.MANIFEST_ACCEPTANCE_PROJECTION],
    )
    dummy_signature = sealed(
        "GenesisGovernanceSignature",
        "signature:dummy:v1",
        signature_projection=gov.MANIFEST_ACCEPTANCE_PROJECTION,
        signed_payload={"placeholder": "not-authoritative"},
        signed_payload_sha256=content_hash({"placeholder": "not-authoritative"}),
        signature_algorithm="ED25519",
        authority_signature_base64=base64.b64encode(b"\x00" * 64).decode("ascii"),
    )
    acceptance = sealed(
        "ManifestAcceptance",
        "acceptance:genesis:v2",
        schema_version="2.0",
        candidate_manifest_ref=ref(manifest),
        bootstrap_governance_root_ref=ref(root),
        acceptance_rule_ref=ref(rule),
        required_validation_report_refs=[ref(report)],
        authority_ref=ref(root),
        decision="ACCEPT",
        reason_codes=[],
        blocking_finding_refs=[],
        signature_ref=ref(dummy_signature),
    )
    signed_payload = gov.manifest_acceptance_signed_payload(acceptance)
    signature = sealed(
        "GenesisGovernanceSignature",
        "signature:acceptance:v1",
        signature_projection=gov.MANIFEST_ACCEPTANCE_PROJECTION,
        signed_payload=signed_payload,
        signed_payload_sha256=content_hash(signed_payload),
        signature_algorithm="ED25519",
        authority_signature_base64=base64.b64encode(b"\x01" * 64).decode("ascii"),
    )
    acceptance = reseal(acceptance, signature_ref=ref(signature))
    assert gov.manifest_acceptance_signed_payload(acceptance) == signed_payload
    return {
        "public_key": public_key,
        "rule": rule,
        "validator": validator,
        "manifest": manifest,
        "report": report,
        "root": root,
        "build_profile": build_profile,
        "contract": contract,
        "signature": signature,
        "acceptance": acceptance,
    }


def patch_crypto(monkeypatch, *, valid=True):
    FakePinnedVerifier.result = valid
    FakePinnedVerifier.calls = []
    monkeypatch.setattr(gov, "PinnedEd25519Verifier", FakePinnedVerifier)
    monkeypatch.setattr(
        gov,
        "validate_build_profile",
        lambda profile: profile["profile_sha256"],
    )


def verify(fx):
    return gov.verify_manifest_acceptance_signature_authoritatively(
        fx["acceptance"],
        signature_evidence=fx["signature"],
        bootstrap_root=fx["root"],
        governance_verifier_contract=fx["contract"],
        ed25519_verifier_build_profile=fx["build_profile"],
        ed25519_verifier_binary=Path("/synthetic/fpp-ed25519-verify"),
        expected_validator_contract_ref=ref(fx["validator"]),
    )


def test_new_governance_schemas_are_draft_2020_12_valid():
    root = Path(__file__).resolve().parents[1] / "schemas"
    for name in (
        "bootstrap_governance_root_v1.schema.json",
        "genesis_governance_signature_verifier_contract_v1.schema.json",
        "genesis_governance_signature_v1.schema.json",
    ):
        schema = json.loads((root / name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)


def test_bootstrap_root_accepts_only_canonical_32_byte_public_key():
    fx = fixture_set()
    assert gov.validate_bootstrap_governance_root(fx["root"]) == fx["public_key"]
    bad = reseal(fx["root"], authority_public_key_base64=base64.b64encode(b"short").decode("ascii"))
    with pytest.raises(ValueError, match="32 bytes"):
        gov.validate_bootstrap_governance_root(bad)


def test_manifest_acceptance_projection_excludes_signature_ref_but_binds_identity_and_decision():
    fx = fixture_set()
    payload = gov.manifest_acceptance_signed_payload(fx["acceptance"])
    assert "signature_ref" not in payload
    assert "payload_sha256" not in payload
    assert "content_sha256" not in payload
    assert payload["acceptance_object_id"] == fx["acceptance"]["object_id"]
    assert payload["candidate_manifest_ref"] == ref(fx["manifest"])
    assert payload["bootstrap_governance_root_ref"] == ref(fx["root"])
    assert payload["decision"] == "ACCEPT"


def test_authoritative_manifest_acceptance_signature_uses_pinned_verifier(monkeypatch):
    fx = fixture_set()
    patch_crypto(monkeypatch, valid=True)
    result = verify(fx)
    assert result == ref(fx["signature"])
    assert len(FakePinnedVerifier.calls) == 1
    binary_path, binary_hash, public_key, message, signature = FakePinnedVerifier.calls[0]
    assert binary_path == Path("/synthetic/fpp-ed25519-verify")
    assert binary_hash == fx["contract"]["ed25519_verifier_binary_sha256"]
    assert public_key == fx["public_key"]
    assert message == gov.manifest_acceptance_signing_bytes(fx["acceptance"])
    assert signature == b"\x01" * 64


def test_invalid_ed25519_signature_fails_closed(monkeypatch):
    fx = fixture_set()
    patch_crypto(monkeypatch, valid=False)
    with pytest.raises(ValueError, match="Ed25519 signature invalid"):
        verify(fx)


def test_signature_payload_substitution_fails_before_crypto(monkeypatch):
    fx = fixture_set()
    patch_crypto(monkeypatch, valid=True)
    bad_payload = dict(fx["signature"]["signed_payload"])
    bad_payload["decision"] = "REJECT"
    bad_signature = reseal(
        fx["signature"],
        signed_payload=bad_payload,
        signed_payload_sha256=content_hash(bad_payload),
    )
    bad_acceptance = reseal(fx["acceptance"], signature_ref=ref(bad_signature))
    fx.update(signature=bad_signature, acceptance=bad_acceptance)
    with pytest.raises(ValueError, match="payload mismatch"):
        verify(fx)
    assert FakePinnedVerifier.calls == []


def test_signature_ref_substitution_fails_closed(monkeypatch):
    fx = fixture_set()
    patch_crypto(monkeypatch, valid=True)
    other = reseal(fx["signature"], authority_signature_base64=base64.b64encode(b"\x02" * 64).decode("ascii"))
    fx["signature"] = other
    with pytest.raises(ValueError, match="signature_ref"):
        verify(fx)
    assert FakePinnedVerifier.calls == []


def test_bootstrap_root_substitution_fails_closed(monkeypatch):
    fx = fixture_set()
    patch_crypto(monkeypatch, valid=True)
    other_root = reseal(
        fx["root"],
        authority_public_key_base64=base64.b64encode(bytes(reversed(range(32)))).decode("ascii"),
    )
    fx["root"] = other_root
    with pytest.raises(ValueError):
        verify(fx)
    assert FakePinnedVerifier.calls == []


def test_acceptance_authority_ref_must_be_bootstrap_root(monkeypatch):
    fx = fixture_set()
    patch_crypto(monkeypatch, valid=True)
    other = sealed("Authority", "authority:substitute:v1", value="substitute")
    fx["acceptance"] = reseal(fx["acceptance"], authority_ref=ref(other))
    with pytest.raises(ValueError, match="authority_ref"):
        verify(fx)
    assert FakePinnedVerifier.calls == []


def test_acceptance_rule_must_match_bootstrap_root(monkeypatch):
    fx = fixture_set()
    patch_crypto(monkeypatch, valid=True)
    other_rule = sealed("PolicyDefinition", "policy:other-acceptance:v2", value="other")
    fx["acceptance"] = reseal(fx["acceptance"], acceptance_rule_ref=ref(other_rule))
    with pytest.raises(ValueError, match="acceptance rule"):
        verify(fx)
    assert FakePinnedVerifier.calls == []


def test_governance_verifier_public_key_hash_mismatch_fails(monkeypatch):
    fx = fixture_set()
    patch_crypto(monkeypatch, valid=True)
    fx["contract"] = reseal(fx["contract"], authority_public_key_sha256="f" * 64)
    with pytest.raises(ValueError, match="public-key hash"):
        verify(fx)
    assert FakePinnedVerifier.calls == []


def test_governance_verifier_build_profile_and_binary_are_both_bound(monkeypatch):
    fx = fixture_set()
    patch_crypto(monkeypatch, valid=True)
    wrong_build = reseal(fx["contract"], ed25519_verifier_build_profile_sha256="c" * 64)
    fx["contract"] = wrong_build
    with pytest.raises(ValueError, match="build-profile hash"):
        verify(fx)
    fx = fixture_set()
    patch_crypto(monkeypatch, valid=True)
    fx["contract"] = reseal(fx["contract"], ed25519_verifier_binary_sha256="d" * 64)
    with pytest.raises(ValueError, match="binary hash"):
        verify(fx)


def test_contract_must_authorize_manifest_acceptance_projection(monkeypatch):
    fx = fixture_set()
    patch_crypto(monkeypatch, valid=True)
    fx["contract"] = reseal(
        fx["contract"],
        allowed_signature_projections=[gov.GENESIS_AUTHORIZATION_PROJECTION],
    )
    with pytest.raises(ValueError, match="does not authorize ManifestAcceptance"):
        verify(fx)
    assert FakePinnedVerifier.calls == []


def test_signed_payload_sha256_mismatch_fails_closed(monkeypatch):
    fx = fixture_set()
    patch_crypto(monkeypatch, valid=True)
    bad_signature = reseal(fx["signature"], signed_payload_sha256="e" * 64)
    fx["acceptance"] = reseal(fx["acceptance"], signature_ref=ref(bad_signature))
    fx["signature"] = bad_signature
    with pytest.raises(ValueError, match="signed_payload_sha256"):
        verify(fx)
    assert FakePinnedVerifier.calls == []


def test_genesis_authorization_projection_remains_unimplemented_in_d1():
    payload = {"placeholder": "authorization"}
    signature = sealed(
        "GenesisGovernanceSignature",
        "signature:authorization:not-yet:v1",
        signature_projection=gov.GENESIS_AUTHORIZATION_PROJECTION,
        signed_payload=payload,
        signed_payload_sha256=content_hash(payload),
        signature_algorithm="ED25519",
        authority_signature_base64=base64.b64encode(b"\x03" * 64).decode("ascii"),
    )
    with pytest.raises(ValueError, match="not implemented in R6-D1"):
        gov.validate_genesis_governance_signature(
            signature,
            expected_projection=gov.GENESIS_AUTHORIZATION_PROJECTION,
        )


def test_bootstrap_root_unknown_field_is_rejected():
    fx = fixture_set()
    bad = reseal(fx["root"], private_key="PROHIBITED")
    with pytest.raises(ValueError, match="field set mismatch"):
        gov.validate_bootstrap_governance_root(bad)


def test_public_authority_api_has_no_signature_verifier_callback(monkeypatch):
    fx = fixture_set()
    patch_crypto(monkeypatch, valid=True)
    with pytest.raises(TypeError):
        gov.verify_manifest_acceptance_signature_authoritatively(
            fx["acceptance"],
            signature_evidence=fx["signature"],
            bootstrap_root=fx["root"],
            governance_verifier_contract=fx["contract"],
            ed25519_verifier_build_profile=fx["build_profile"],
            ed25519_verifier_binary=Path("/synthetic/fpp-ed25519-verify"),
            expected_validator_contract_ref=ref(fx["validator"]),
            signature_verifier=lambda *_: True,
        )
