import unittest

from forecast_trust_core.canonical import seal_object
from forecast_trust_core.production_receipt_admission_v1 import validate_production_receipt_profile_binding


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def sealed(kind, object_id, **payload):
    return seal_object({"schema_version": "1.0", **payload}, object_type=kind, stable_context="test", semantic_id=object_id)


class ProductionReceiptAdmissionTests(unittest.TestCase):
    def test_exact_manifest_profile_binding_required(self):
        profile_fields = {
            "provider_id": "roughtime.se",
            "operator_identity": "operator",
            "host": "example.test",
            "port": 2002,
            "transport": "udp",
            "operator_declared_protocol": "roughtime",
            "wire_version_hex": "0x8000000c",
            "offered_version_hex": "0x8000000c",
            "wire_profile": "draft12",
            "require_type": True,
            "require_srv": True,
            "root_public_key_base64": "AA==",
            "packet_profile": "STANDARD_1024_BODY",
            "transport_profile": "UDP_ONLY",
            "nonce_profile": "FPP_ROUGHTIME_NONCE_V2",
            "verifier_repository": "repo",
            "verifier_tag": "tag",
            "verifier_commit": "commit",
            "verifier_build_profile_sha256": "0" * 64,
            "no_fallback": True,
        }
        profile = sealed("RoughtimeProductionProviderProfile", "profile:test:v1", **profile_fields)
        decision = sealed(
            "RoughtimeQualificationDecision",
            "decision:test:v1",
            signed_payload={"provider_profile_ref": ref(profile)},
        )
        state = sealed(
            "RoughtimeProviderQualificationStatePackage",
            "state:test:v1",
            provider_profile_ref=ref(profile),
            qualification_decision_ref=ref(decision),
            qualification_state="PRODUCTION_QUALIFIED",
        )
        receipt = dict(profile_fields)
        receipt.pop("no_fallback")
        result = validate_production_receipt_profile_binding(
            receipt,
            provider_profile=profile,
            qualification_decision=decision,
            qualification_state_package=state,
        )
        self.assertTrue(result.valid)
        receipt["root_public_key_base64"] = "AQ=="
        bad = validate_production_receipt_profile_binding(
            receipt,
            provider_profile=profile,
            qualification_decision=decision,
            qualification_state_package=state,
        )
        self.assertFalse(bad.valid)


if __name__ == "__main__":
    unittest.main()
