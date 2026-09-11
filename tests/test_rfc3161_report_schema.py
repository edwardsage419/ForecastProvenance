import copy
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads(
    (ROOT / "schemas" / "rfc3161_qualification_rehearsal_report.schema.json").read_text(
        encoding="utf-8"
    )
)
SEMANTIC_SCHEMA = json.loads(
    (ROOT / "schemas" / "rfc3161_reviewed_semantic_assertion.schema.json").read_text(
        encoding="utf-8"
    )
)


class SchemaRejection(ValueError):
    pass


def _resolve_ref(root, reference):
    if not reference.startswith("#/"):
        raise SchemaRejection("test validator supports local references only")
    value = root
    for part in reference[2:].split("/"):
        value = value[part.replace("~1", "/").replace("~0", "~")]
    return value


def validate_schema(instance, schema, root=SCHEMA):
    if "anyOf" in schema:
        for alternative in schema["anyOf"]:
            try:
                validate_schema(instance, alternative, root)
            except SchemaRejection:
                continue
            break
        else:
            raise SchemaRejection("no anyOf schema matched")
    if "not" in schema:
        try:
            validate_schema(instance, schema["not"], root)
        except SchemaRejection:
            pass
        else:
            raise SchemaRejection("not schema matched")
    if "$ref" in schema:
        validate_schema(instance, _resolve_ref(root, schema["$ref"]), root)
    expected_type = schema.get("type")
    type_checks = {
        "object": lambda value: isinstance(value, dict),
        "array": lambda value: isinstance(value, list),
        "string": lambda value: isinstance(value, str),
        "boolean": lambda value: isinstance(value, bool),
        "integer": lambda value: type(value) is int,
    }
    if expected_type in type_checks and not type_checks[expected_type](instance):
        raise SchemaRejection(f"expected {expected_type}")
    if "const" in schema and instance != schema["const"]:
        raise SchemaRejection("const mismatch")
    if "enum" in schema and instance not in schema["enum"]:
        raise SchemaRejection("enum mismatch")
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            raise SchemaRejection("string too short")
        if "pattern" in schema and re.fullmatch(schema["pattern"], instance) is None:
            raise SchemaRejection("pattern mismatch")
    if type(instance) is int and "minimum" in schema and instance < schema["minimum"]:
        raise SchemaRejection("integer below minimum")
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0) or len(instance) > schema.get("maxItems", len(instance)):
            raise SchemaRejection("array size mismatch")
        if "items" in schema:
            for item in instance:
                validate_schema(item, schema["items"], root)
    if isinstance(instance, dict):
        missing = set(schema.get("required", [])) - set(instance)
        if missing:
            raise SchemaRejection(f"missing properties: {sorted(missing)}")
        properties = schema.get("properties", {})
        for key, subschema in properties.items():
            if key in instance:
                validate_schema(instance[key], subschema, root)
        additional = schema.get("additionalProperties", True)
        extras = set(instance) - set(properties)
        if additional is False and extras:
            raise SchemaRejection(f"additional properties: {sorted(extras)}")
        if isinstance(additional, dict):
            for key in extras:
                validate_schema(instance[key], additional, root)
    for subschema in schema.get("allOf", []):
        validate_schema(instance, subschema, root)
    if "if" in schema:
        try:
            validate_schema(instance, schema["if"], root)
        except SchemaRejection:
            if "else" in schema:
                validate_schema(instance, schema["else"], root)
        else:
            if "then" in schema:
                validate_schema(instance, schema["then"], root)


class RFC3161ReportSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "genesis" / "rehearsal" / "reports" / "freetsa_v2_report.json"
        cls.incomplete = json.loads(path.read_text(encoding="utf-8"))

    def verified_report(self):
        report = copy.deepcopy(self.incomplete)
        report["final_rehearsal_status"] = "REHEARSAL_VERIFIED"
        report["policy_semantics_documented"] = True
        report["accuracy_semantics_documented"] = True
        report["revocation_verification_scope"] = "TSA_SIGNER_ONLY"
        report["crl_evidence"]["verification_scope"] = "TSA_SIGNER_ONLY"
        report["unresolved_qualification_blockers"] = []
        report["raw_evidence_sha256"]["reviewed_semantic_assertion"] = "f" * 64
        report["semantic_assertion_evidence"] = {
            "available": True,
            "verified": True,
            "raw_sha256": "f" * 64,
            "classification": "REVIEWED_RFC3161_QUALIFICATION_SEMANTICS",
            "content_sha256": "e" * 64,
            "provider_id": "freetsa_rfc3161",
            "provider_policy_sha256": report["raw_evidence_sha256"]["provider_policy"],
            "token_policy_oid": report["token_policy_oid"],
            "policy_review_disposition": "DOCUMENTED_APPLICABLE",
            "accuracy_review_disposition": "DOCUMENTED_CONSERVATIVE_BOUND",
            "observed_token_accuracy": "unspecified",
            "conservative_accuracy_bound_seconds": 1,
            "reviewer_id": "reviewer:test",
            "review_authority": "GEN_001_REHEARSAL_REVIEWER",
            "review_basis": "retained policy hash and CPS section 1.2",
            "evidence_locator": "CPS section 1.2",
            "reviewed_at": "2026-09-11T08:00:00Z",
        }
        validate_schema(report, SCHEMA)
        return report

    def assert_rejected(self, report):
        with self.assertRaises(SchemaRejection):
            validate_schema(report, SCHEMA)

    def test_schema_accepts_incomplete_report(self):
        validate_schema(self.incomplete, SCHEMA)

    def test_schema_rejects_minimal_verified_claim(self):
        report = copy.deepcopy(self.incomplete)
        report["final_rehearsal_status"] = "REHEARSAL_VERIFIED"
        for key in ("subject_sha256", "request_sha256", "response_sha256"):
            report.pop(key, None)
        self.assert_rejected(report)

    def test_schema_rejects_verified_nonce_mismatch(self):
        report = self.verified_report()
        report["nonce_equal"] = False
        self.assert_rejected(report)

    def test_schema_rejects_verified_with_blockers(self):
        report = self.verified_report()
        report["unresolved_qualification_blockers"] = [{"code": "X", "detail": "blocked"}]
        self.assert_rejected(report)

    def test_schema_rejects_verified_failed_signature(self):
        report = self.verified_report()
        report["rfc3161_signature_verification"]["verified"] = False
        self.assert_rejected(report)

    def test_schema_rejects_verified_failed_chain(self):
        report = self.verified_report()
        report["certificate_chain_verification"]["verified"] = False
        self.assert_rejected(report)

    def test_schema_rejects_overstated_revocation_scope(self):
        report = self.verified_report()
        report["revocation_verification_scope"] = "FULL_CERTIFICATION_PATH"
        report["crl_evidence"]["verification_scope"] = "FULL_CERTIFICATION_PATH"
        self.assert_rejected(report)

    def test_schema_rejects_verified_missing_conservative_bound(self):
        report = self.verified_report()
        report["semantic_assertion_evidence"].pop("conservative_accuracy_bound_seconds")
        self.assert_rejected(report)

    def test_schema_rejects_bound_with_token_accuracy_disposition(self):
        report = self.verified_report()
        assertion = report["semantic_assertion_evidence"]
        assertion["accuracy_review_disposition"] = "TOKEN_ACCURACY_ACCEPTED"
        self.assert_rejected(report)

    def test_schema_rejects_verified_missing_reviewer_provenance(self):
        for field in ("reviewer_id", "review_authority", "review_basis"):
            with self.subTest(field=field):
                report = self.verified_report()
                report["semantic_assertion_evidence"].pop(field)
                self.assert_rejected(report)

    def test_schema_rejects_invalid_observed_accuracy_structure(self):
        report = self.verified_report()
        report["semantic_assertion_evidence"]["observed_token_accuracy"] = "1 second"
        self.assert_rejected(report)

    def test_schema_rejects_conservative_review_for_specified_token_accuracy(self):
        report = self.verified_report()
        report["token_accuracy"] = "1 second"
        self.assert_rejected(report)


class ReviewedSemanticAssertionSchemaTests(unittest.TestCase):
    def assertion(self):
        return {
            "schema_version": "1.1",
            "classification": "REVIEWED_RFC3161_QUALIFICATION_SEMANTICS",
            "prospective_eligible": False,
            "provider_id": "provider_rfc3161",
            "provider_policy_sha256": "a" * 64,
            "token_policy_oid": "1.2.3.4",
            "policy_review_disposition": "DOCUMENTED_APPLICABLE",
            "accuracy_review_disposition": "TOKEN_ACCURACY_ACCEPTED",
            "observed_token_accuracy": "1 second",
            "reviewer_id": "reviewer:test",
            "review_authority": "GEN_001_REHEARSAL_REVIEWER",
            "review_basis": "retained policy hash and section 1.2",
            "evidence_locator": "section 1.2",
            "reviewed_at": "2026-09-11T08:00:00Z",
            "object_type": "RFC3161ReviewedSemanticAssertion",
            "object_id": "rfc3161reviewedsemanticassertion:test",
            "payload_sha256": "b" * 64,
            "content_sha256": "c" * 64,
        }

    def assert_rejected(self, assertion):
        with self.assertRaises(SchemaRejection):
            validate_schema(assertion, SEMANTIC_SCHEMA, SEMANTIC_SCHEMA)

    def test_semantic_schema_accepts_matching_specified_accuracy(self):
        validate_schema(self.assertion(), SEMANTIC_SCHEMA, SEMANTIC_SCHEMA)

    def test_semantic_schema_rejects_missing_reviewer_provenance(self):
        assertion = self.assertion()
        assertion.pop("review_authority")
        self.assert_rejected(assertion)

    def test_semantic_schema_rejects_accepted_unspecified_accuracy(self):
        assertion = self.assertion()
        assertion["observed_token_accuracy"] = "unspecified"
        self.assert_rejected(assertion)

    def test_semantic_schema_accepts_unspecified_with_conservative_bound(self):
        assertion = self.assertion()
        assertion["accuracy_review_disposition"] = "DOCUMENTED_CONSERVATIVE_BOUND"
        assertion["observed_token_accuracy"] = "unspecified"
        assertion["conservative_accuracy_bound_seconds"] = 1
        validate_schema(assertion, SEMANTIC_SCHEMA, SEMANTIC_SCHEMA)


if __name__ == "__main__":
    unittest.main()
