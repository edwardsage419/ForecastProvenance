import pytest

import forecast_trust_core.claim_authority_v1 as authority
from forecast_trust_core.canonical import seal_object


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def sealed_v1(kind, object_id, **payload):
    return seal_object(
        {"schema_version": "1.0", **payload},
        object_type=kind,
        stable_context="manifest-acceptance-contract-test",
        semantic_id=object_id,
    )


def acceptance_payload():
    manifest = sealed_v1("TrustedManifest", "manifest:acceptance-contract:v1", value="m")
    bootstrap = sealed_v1("BootstrapGovernanceRoot", "bootstrap:acceptance-contract:v1", value="b")
    rule = sealed_v1("PolicyDefinition", "policy:acceptance-contract:v2", value="r")
    report = sealed_v1("ValidationReport", "validation:acceptance-contract:v1", value="v")
    authority_obj = sealed_v1("Authority", "authority:acceptance-contract:v1", value="a")
    signature = sealed_v1("Signature", "signature:acceptance-contract:v1", value="s")
    return {
        "candidate_manifest_ref": ref(manifest),
        "bootstrap_governance_root_ref": ref(bootstrap),
        "acceptance_rule_ref": ref(rule),
        "required_validation_report_refs": [ref(report)],
        "authority_ref": ref(authority_obj),
        "decision": "ACCEPT",
        "reason_codes": [],
        "blocking_finding_refs": [],
        "signature_ref": ref(signature),
    }


def sealed_acceptance(schema_version="2.0", object_id="acceptance:contract:v2", **extra):
    payload = {"schema_version": schema_version, **acceptance_payload(), **extra}
    return seal_object(
        payload,
        object_type="ManifestAcceptance",
        stable_context="manifest-acceptance-contract-test",
        semantic_id=object_id,
    )


def test_manifest_acceptance_v2_exact_contract_is_accepted():
    authority._validate_manifest_acceptance_v2_contract(sealed_acceptance())


def test_manifest_acceptance_schema_v1_is_rejected_even_with_valid_seal():
    bad = sealed_acceptance(
        schema_version="1.0",
        object_id="acceptance:schema-v1:contract:v2",
    )
    with pytest.raises(ValueError, match="schema_version mismatch"):
        authority._validate_manifest_acceptance_v2_contract(bad)


def test_manifest_acceptance_additional_property_is_rejected():
    bad = sealed_acceptance(
        object_id="acceptance:extra:contract:v2",
        unexpected="forbidden",
    )
    with pytest.raises(ValueError, match="field set mismatch"):
        authority._validate_manifest_acceptance_v2_contract(bad)


def test_manifest_acceptance_requires_nonempty_validation_report_set():
    payload = acceptance_payload()
    payload["required_validation_report_refs"] = []
    bad = seal_object(
        {"schema_version": "2.0", **payload},
        object_type="ManifestAcceptance",
        stable_context="manifest-acceptance-contract-test",
        semantic_id="acceptance:no-reports:contract:v2",
    )
    with pytest.raises(ValueError, match="must be non-empty"):
        authority._validate_manifest_acceptance_v2_contract(bad)
