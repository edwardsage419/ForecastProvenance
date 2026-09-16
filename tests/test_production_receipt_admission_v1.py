import unittest

from forecast_trust_core.canonical import seal_object
from forecast_trust_core.production_receipt_admission_v1 import (
    validate_production_receipt_profile_binding,
)


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def sealed(kind, object_id, **payload):
    return seal_object(
        {"schema_version": "1.0", **payload},
        object_type=kind,
        stable_context="test",
        semantic_id=object_id,
    )


def fixture():
    provider_id = "roughtime.se"
    verifier_hash = "0" * 64
    profile = sealed(
        "RoughtimeProductionProviderProfile",
        "profile:test:v1",
        provider_id=provider_id,
        verifier_build_profile_sha256=verifier_hash,
        no_fallback=True,
    )
    decision = sealed(
        "RoughtimeQualificationDecision",
        "decision:test:v1",
        signed_payload={
            "provider_id": provider_id,
            "provider_profile_ref": ref(profile),
        },
    )
    state = sealed(
        "RoughtimeProviderQualificationStatePackage",
        "state:test:v1",
        provider_id=provider_id,
        provider_profile_ref=ref(profile),
        qualification_decision_ref=ref(decision),
        qualification_state="PRODUCTION_QUALIFIED",
    )
    receipt = sealed(
        "RoughtimeProductionReceiptEvidence",
        "receipt:test:v1",
        origin_class="SYNTHETIC",
        prospective_eligible=False,
        subject_ref={"object_id": "subject:test:v1", "content_sha256": "a" * 64},
        frozen_deadline_utc="2026-09-20T00:00:00Z",
        provider_id=provider_id,
        provider_profile_ref=ref(profile),
        qualification_state_package_ref=ref(state),
        verifier_build_profile_sha256=verifier_hash,
        client_random_hex="1" * 64,
        request_sha256="2" * 64,
        request_base64="cmVxdWVzdA==",
        response_sha256="3" * 64,
        response_base64="cmVzcG9uc2U=",
    )
    return profile, decision, state, receipt


class ProductionReceiptAdmissionTests(unittest.TestCase):
    def test_schema_conforming_receipt_binds_exact_profile_and_state(self):
        profile, decision, state, receipt = fixture()
        result = validate_production_receipt_profile_binding(
            receipt,
            provider_profile=profile,
            qualification_decision=decision,
            qualification_state_package=state,
        )
        self.assertTrue(result.valid)

    def test_wrong_exact_profile_ref_fails(self):
        profile, decision, state, receipt = fixture()
        wrong_profile = sealed(
            "RoughtimeProductionProviderProfile",
            "profile:wrong:v1",
            provider_id="roughtime.se",
            verifier_build_profile_sha256="0" * 64,
            no_fallback=True,
        )
        bad = sealed(
            "RoughtimeProductionReceiptEvidence",
            "receipt:wrong-profile:v1",
            **{
                key: value
                for key, value in receipt.items()
                if key not in {
                    "schema_version",
                    "object_type",
                    "object_id",
                    "payload_sha256",
                    "content_sha256",
                    "provider_profile_ref",
                }
            },
            provider_profile_ref=ref(wrong_profile),
        )
        result = validate_production_receipt_profile_binding(
            bad,
            provider_profile=profile,
            qualification_decision=decision,
            qualification_state_package=state,
        )
        self.assertFalse(result.valid)

    def test_schema_incompatible_extra_field_fails_closed(self):
        profile, decision, state, receipt = fixture()
        bad = sealed(
            "RoughtimeProductionReceiptEvidence",
            "receipt:extra-field:v1",
            **{
                key: value
                for key, value in receipt.items()
                if key not in {
                    "schema_version",
                    "object_type",
                    "object_id",
                    "payload_sha256",
                    "content_sha256",
                }
            },
            unexpected_profile_copy="must-not-be-present",
        )
        result = validate_production_receipt_profile_binding(
            bad,
            provider_profile=profile,
            qualification_decision=decision,
            qualification_state_package=state,
        )
        self.assertFalse(result.valid)
        self.assertIn(
            "INVALID_PRODUCTION_RECEIPT_CONTRACT",
            {check.reason_code for check in result.checks},
        )

    def test_verifier_build_profile_mismatch_fails(self):
        profile, decision, state, receipt = fixture()
        bad = sealed(
            "RoughtimeProductionReceiptEvidence",
            "receipt:wrong-verifier:v1",
            **{
                key: value
                for key, value in receipt.items()
                if key not in {
                    "schema_version",
                    "object_type",
                    "object_id",
                    "payload_sha256",
                    "content_sha256",
                    "verifier_build_profile_sha256",
                }
            },
            verifier_build_profile_sha256="f" * 64,
        )
        result = validate_production_receipt_profile_binding(
            bad,
            provider_profile=profile,
            qualification_decision=decision,
            qualification_state_package=state,
        )
        self.assertFalse(result.valid)


if __name__ == "__main__":
    unittest.main()
