import json
import tempfile
import unittest
from pathlib import Path

from forecast_trust_core.architecture_compression_v1 import (
    derive_bitcoin_durability_claim,
    derive_confirmatory_eligibility,
    derive_deadline_existence_claim,
    derive_external_existence_claim,
    derive_pre_outcome_durability_claim,
    validate_final_genesis_acceptance,
    validate_manifest_acceptance_v2,
    validate_provider_admission_set,
    validate_qualification_state_package,
)
from forecast_trust_core.canonical import canonical_json, seal_object


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def sealed(kind, object_id, **payload):
    base = {"schema_version": "1.0", **payload}
    return seal_object(base, object_type=kind, stable_context="test", semantic_id=object_id)


class ArchitectureCompressionP5Tests(unittest.TestCase):
    def test_timely_existence_survives_late_durability_failure(self):
        subject = sealed("TestSubject", "subject:test:v1", value="1")
        sref = ref(subject)
        existence = derive_external_existence_claim(
            sref,
            verified_upper_bound="2026-09-01T00:00:00Z",
        )
        deadline = derive_deadline_existence_claim(
            sref,
            external_existence_claim=existence,
            frozen_deadline="2026-09-02T00:00:00Z",
        )
        bitcoin = derive_bitcoin_durability_claim(
            sref,
            bundle_subject_ref=sref,
            ots_bundle_binding_verified=True,
            strong_bitcoin_verification_passed=True,
        )
        late_dvr_deadline = {
            "claim_type": "DEADLINE_EXISTENCE_VERIFIED",
            "subject_ref": sref,
            "state": "FAILED",
        }
        pre_outcome = derive_pre_outcome_durability_claim(
            sref,
            bitcoin_durability_claim=bitcoin,
            durability_record_deadline_claim=late_dvr_deadline,
        )
        eligible = derive_confirmatory_eligibility(
            sref,
            required_claims=(deadline, bitcoin, pre_outcome),
        )
        self.assertEqual(deadline["state"], "VERIFIED")
        self.assertEqual(bitcoin["state"], "VERIFIED")
        self.assertEqual(pre_outcome["state"], "FAILED")
        self.assertEqual(eligible["state"], "FAILED")

    def test_genesis_acceptance_final_evidence_is_separate_and_exact(self):
        manifest = sealed("TrustedManifest", "manifest:test:v1", manifest_sequence=1)
        bootstrap = sealed("BootstrapGovernanceRoot", "bootstrap:test:v1", project_id="test")
        rule = sealed("PolicyDefinition", "policy:acceptance:test:v2", policy_type="ACCEPTANCE")
        report = sealed("ValidationReport", "validation:test:v1", result="VALID")
        authority = sealed("Authority", "authority:test:v1", role="OWNER")
        signature = sealed("Signature", "signature:test:v1", algorithm="ED25519")
        acceptance = sealed(
            "ManifestAcceptance",
            "acceptance:test:v2",
            candidate_manifest_ref=ref(manifest),
            bootstrap_governance_root_ref=ref(bootstrap),
            acceptance_rule_ref=ref(rule),
            required_validation_report_refs=[ref(report)],
            authority_ref=ref(authority),
            decision="ACCEPT",
            reason_codes=[],
            blocking_finding_refs=[],
            signature_ref=ref(signature),
        )
        result = validate_manifest_acceptance_v2(
            manifest,
            acceptance,
            bootstrap_root_ref=ref(bootstrap),
            acceptance_rule_ref=ref(rule),
            required_validation_report_refs=[ref(report)],
        )
        self.assertTrue(result.valid)
        final = validate_final_genesis_acceptance(
            acceptance,
            final_evidence_subject_ref=ref(acceptance),
            external_existence_state="VERIFIED",
            bitcoin_durability_state="VERIFIED",
        )
        self.assertTrue(final.valid)
        wrong = validate_final_genesis_acceptance(
            acceptance,
            final_evidence_subject_ref=ref(manifest),
            external_existence_state="VERIFIED",
            bitcoin_durability_state="VERIFIED",
        )
        self.assertFalse(wrong.valid)

    def test_state_package_rejects_omitted_requalification_event(self):
        profile = sealed("RoughtimeProductionProviderProfile", "profile:test:v1", provider_id="roughtime.se")
        decision = sealed("RoughtimeQualificationDecision", "decision:test:v1", provider_id="roughtime.se")
        verifier = sealed("ValidatorContract", "validator:qualification:test:v1", contract="test")
        metadata = sealed(
            "RoughtimeProviderMetadataReview",
            "metadata:test:v1",
            provider_id="roughtime.se",
            reviewed_at="2026-09-01T00:00:00Z",
        )
        event = sealed(
            "RoughtimeRequalificationEvent",
            "requal:test:v1",
            provider_id="roughtime.se",
            detected_at="2026-09-05T00:00:00Z",
        )
        package = sealed(
            "RoughtimeProviderQualificationStatePackage",
            "state-package:test:v1",
            provider_id="roughtime.se",
            as_of_utc="2026-09-10T00:00:00Z",
            provider_profile_ref=ref(profile),
            qualification_decision_ref=ref(decision),
            qualification_evidence_manifest_sha256="0" * 64,
            qualification_verifier_contract_ref=ref(verifier),
            metadata_review_refs=[ref(metadata)],
            requalification_event_refs=[],
            qualification_state_report_sha256="1" * 64,
            qualification_state="PRODUCTION_QUALIFIED",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "metadata.json").write_bytes(canonical_json(metadata))
            (root / "event.json").write_bytes(canonical_json(event))
            result = validate_qualification_state_package(package, record_root=root)
        self.assertFalse(result.valid)
        self.assertIn("INCOMPLETE_REQUALIFICATION_EVENT_SET", {c.reason_code for c in result.checks})

    def test_provider_admission_requires_three_qualified_at_exact_deadline(self):
        deadline = "2026-09-10T00:00:00Z"
        profiles = []
        decisions = []
        packages = []
        provider_ids = ["roughtime.se", "time.txryan.com", "TimeNL-Roughtime"]
        for index, provider_id in enumerate(provider_ids):
            profile = sealed("RoughtimeProductionProviderProfile", f"profile:test:{index}", provider_id=provider_id)
            decision = sealed("RoughtimeQualificationDecision", f"decision:test:{index}", provider_id=provider_id)
            profiles.append(ref(profile))
            decisions.append(ref(decision))
            packages.append({
                "provider_id": provider_id,
                "as_of_utc": deadline,
                "provider_profile_ref": ref(profile),
                "qualification_decision_ref": ref(decision),
                "qualification_state": "PRODUCTION_QUALIFIED",
            })
        result = validate_provider_admission_set(
            packages,
            frozen_deadline_utc=deadline,
            admitted_provider_profile_refs=profiles,
            admitted_qualification_decision_refs=decisions,
        )
        self.assertTrue(result.valid)
        packages[2]["qualification_state"] = "QUALIFICATION_EXPIRED"
        failed = validate_provider_admission_set(
            packages,
            frozen_deadline_utc=deadline,
            admitted_provider_profile_refs=profiles,
            admitted_qualification_decision_refs=decisions,
        )
        self.assertFalse(failed.valid)


if __name__ == "__main__":
    unittest.main()
