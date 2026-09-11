import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from forecast_trust_core.canonical import seal_object, verify_sealed_object
from forecast_trust_core.rfc3161_rehearsal import (
    CertificateObservation,
    CrlObservation,
    OpenSSLBackend,
    RehearsalEvidenceError,
    RequestObservation,
    TokenObservation,
    check_rehearsal,
)

OPENSSL_EXECUTABLE = os.environ.get("OPENSSL_EXECUTABLE") or shutil.which("openssl")


class FakeBackend:
    def __init__(self, subject_sha256: str):
        tsa = CertificateObservation(
            subject="CN=FreeTSA TSA",
            issuer="CN=FreeTSA Root CA",
            serial="C2E986160DA8E9CD",
            not_before="2025-01-01T00:00:00Z",
            not_after="2027-01-01T00:00:00Z",
            eku=("Time Stamping",),
            eku_critical=True,
            sha256_der="32e841a95cc1164101ffde41298ef2fc75c1c4372ef095e88a6bbd47dfb191fc",
            pem=b"tsa certificate",
        )
        root = CertificateObservation(
            subject="CN=FreeTSA Root CA",
            issuer="CN=FreeTSA Root CA",
            serial="01",
            not_before="2020-01-01T00:00:00Z",
            not_after="2030-01-01T00:00:00Z",
            eku=(),
            eku_critical=False,
            sha256_der="a6379e7cecc05faa3cbf076013d745e327bbbaa38c0b9af22469d4701d18aabc",
            pem=b"root certificate",
        )
        self.request = RequestObservation("sha256", subject_sha256, "0x001234", True)
        self.token = TokenObservation(
            "GRANTED", "sha256", subject_sha256, "1234",
            "2026-09-11T08:00:00Z", "tsa_policy1", "1 second", "yes", (tsa, root), tsa.sha256_der,
        )
        self.anchor = root
        self.chain_certificates = ()
        self.chain_result = (True, "tsa.pem: OK")
        self.revocation_result = (True, "tsa.pem: OK")
        self.signature_result = (True, "Verification: OK")
        self.crl_signature_result = (True, "verify OK")
        self.crl_signature_issuer = None
        self.crl = CrlObservation(
            "CN=FreeTSA Root CA", "2025-09-18T14:45:18Z", "2026-09-18T14:45:18Z"
        )
        self.parse_error = None

    def version(self):
        return "OpenSSL test-double"

    def parse_request(self, request):
        return self.request

    def parse_response(self, response):
        if self.parse_error:
            raise RehearsalEvidenceError(self.parse_error)
        return self.token

    def inspect_trust_anchor(self, trust_anchor):
        if "tsa" in trust_anchor.name:
            return self.token.certificates[0]
        return self.anchor

    def inspect_certificate_chain(self, chain):
        return self.chain_certificates

    def verify_chain(self, tsa_certificate, trust_anchor, untrusted_chain, crl, at_time):
        return self.revocation_result if crl is not None else self.chain_result

    def verify_response(self, request, response, trust_anchor, untrusted_chain):
        return self.signature_result

    def inspect_crl(self, crl):
        return self.crl

    def verify_crl_signature(self, crl, issuer_certificate):
        self.crl_signature_issuer = issuer_certificate
        return self.crl_signature_result


class RFC3161RehearsalTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "evidence with spaces" / "路径"
        self.root.mkdir(parents=True)
        self.subject = b"NON_FORECAST_REHEARSAL subject\n"
        files = {
            "subject.txt": self.subject,
            "request.tsq": b"request",
            "response.tsr": b"response",
            "tool_versions.txt": b"OpenSSL 3.0 test\nPython 3.11 test\n",
            "root_ca.pem": b"root",
            "chain.pem": b"chain",
            "tsa.crl.pem": b"crl",
            "provider-cps.pdf": b"provider policy evidence",
            "independent-tsa.pem": b"independent tsa certificate",
        }
        for name, content in files.items():
            (self.root / name).write_bytes(content)
        self.subject_sha256 = hashlib.sha256(self.subject).hexdigest()
        self.backend = FakeBackend(self.subject_sha256)
        self.profile = {
            "provider_id": "freetsa_rfc3161",
            "classification": "NON_FORECAST_REHEARSAL",
            "prospective_eligible": False,
            "captured_utc": "2026-09-11T08:00:01Z",
            "trust_anchor_source": "independently retrieved FreeTSA Root CA",
            "provider_policy_evidence_source": "https://example.test/cps.pdf sha256:abc",
            "policy_semantics": {"documented": True, "applicable_policy_oids": ["tsa_policy1"]},
            "accuracy_semantics": {"documented": True},
            "crl_source": "https://example.test/root.crl",
            "evidence_files": {
                "subject": "subject.txt",
                "request": "request.tsq",
                "response": "response.tsr",
                "tool_versions": "tool_versions.txt",
                "trust_anchor": "root_ca.pem",
                "untrusted_chain": "chain.pem",
                "crl": "tsa.crl.pem",
                "provider_policy": "provider-cps.pdf",
                "independent_tsa_certificate": "independent-tsa.pem",
                "reviewed_semantic_assertion": "reviewed-semantics.json",
            },
        }
        self.write_assertion()

    def tearDown(self):
        self.tempdir.cleanup()

    def check(self):
        return check_rehearsal(self.root, self.profile, backend=self.backend)

    def write_assertion(self, **overrides):
        payload = {
            "schema_version": "1.1",
            "classification": "REVIEWED_RFC3161_QUALIFICATION_SEMANTICS",
            "prospective_eligible": False,
            "provider_id": "freetsa_rfc3161",
            "provider_policy_sha256": hashlib.sha256(b"provider policy evidence").hexdigest(),
            "token_policy_oid": "tsa_policy1",
            "policy_review_disposition": "DOCUMENTED_APPLICABLE",
            "accuracy_review_disposition": "TOKEN_ACCURACY_ACCEPTED",
            "observed_token_accuracy": "1 second",
            "reviewer_id": "reviewer:test",
            "review_authority": "GEN_001_REHEARSAL_REVIEWER",
            "review_basis": "retained provider policy SHA256 and CPS section 1.2",
            "evidence_locator": "CPS section 1.2, test fixture",
            "reviewed_at": "2026-09-11T08:00:00Z",
        }
        payload.update(overrides)
        for key in tuple(payload):
            if payload[key] is None:
                del payload[key]
        assertion = seal_object(
            payload,
            object_type="RFC3161ReviewedSemanticAssertion",
            stable_context="freetsa_rfc3161",
        )
        (self.root / "reviewed-semantics.json").write_text(
            json.dumps(assertion, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def blocker_codes(report):
        return {item["code"] for item in report["unresolved_qualification_blockers"]}

    def configure_intermediate_issued_signer(self):
        tsa, root = self.backend.token.certificates
        intermediate = replace(
            root,
            subject="CN=Intermediate TSA CA",
            issuer=root.subject,
            serial="02",
            sha256_der="2" * 64,
            pem=b"intermediate certificate",
        )
        tsa = replace(tsa, issuer=intermediate.subject)
        self.backend.token = replace(
            self.backend.token,
            certificates=(tsa, intermediate, root),
            signer_sha256_der=tsa.sha256_der,
        )
        self.backend.chain_certificates = (intermediate,)
        self.backend.crl = replace(self.backend.crl, issuer=intermediate.subject)
        return tsa, intermediate, root

    def test_successful_rehearsal_is_verified_but_never_production_qualified(self):
        report = self.check()
        self.assertEqual(report["final_rehearsal_status"], "REHEARSAL_VERIFIED")
        self.assertEqual(report["classification"], "NON_FORECAST_REHEARSAL")
        self.assertIs(report["prospective_eligible"], False)
        self.assertNotIn("PRODUCTION_QUALIFIED", repr(report))
        self.assertTrue(verify_sealed_object(report))

    def test_message_imprint_mismatch_fails(self):
        self.backend.token = replace(self.backend.token, message_imprint="0" * 64)
        report = self.check()
        self.assertEqual(report["final_rehearsal_status"], "REHEARSAL_FAILED")
        self.assertIn("MESSAGE_IMPRINT_MISMATCH", self.blocker_codes(report))

    def test_nonce_mismatch_fails(self):
        self.backend.token = replace(self.backend.token, response_nonce="deadbeef")
        self.assertIn("NONCE_MISMATCH", self.blocker_codes(self.check()))

    def test_wrong_trust_anchor_fails(self):
        self.backend.chain_result = (False, "unable to get local issuer certificate")
        self.assertIn("CERTIFICATE_CHAIN_VERIFICATION_FAILED", self.blocker_codes(self.check()))

    def test_certificate_invalid_at_token_time_fails(self):
        tsa, root = self.backend.token.certificates
        tsa = replace(tsa, not_after="2026-01-01T00:00:00Z")
        self.backend.token = replace(self.backend.token, certificates=(tsa, root))
        self.assertIn("TSA_CERTIFICATE_INVALID_AT_GENTIME", self.blocker_codes(self.check()))

    def test_revoked_certificate_or_crl_failure_fails(self):
        self.backend.chain_result = (False, "certificate revoked")
        self.assertIn("CERTIFICATE_REVOCATION_CHECK_FAILED", self.blocker_codes(self.check()))

    def test_missing_policy_evidence_is_incomplete(self):
        (self.root / "reviewed-semantics.json").unlink()
        self.profile["provider_policy_evidence_source"] = "UNAVAILABLE"
        self.profile["policy_semantics"] = {"documented": False, "applicable_policy_oids": []}
        report = self.check()
        self.assertEqual(report["final_rehearsal_status"], "REHEARSAL_INCOMPLETE")
        self.assertIn("TOKEN_POLICY_SEMANTICS_UNDOCUMENTED", self.blocker_codes(report))

    def test_unspecified_accuracy_is_incomplete(self):
        self.backend.token = replace(self.backend.token, accuracy="unspecified")
        (self.root / "reviewed-semantics.json").unlink()
        self.profile["accuracy_semantics"] = {"documented": False}
        self.assertIn("TIMESTAMP_ACCURACY_UNSPECIFIED", self.blocker_codes(self.check()))

    def test_profile_semantic_booleans_without_reviewed_assertion_do_not_clear(self):
        (self.root / "reviewed-semantics.json").unlink()
        self.profile["policy_semantics"] = {
            "documented": True,
            "applicable_policy_oids": ["tsa_policy1"],
        }
        self.profile["accuracy_semantics"] = {"documented": True}
        report = self.check()
        self.assertEqual(report["final_rehearsal_status"], "REHEARSAL_INCOMPLETE")
        self.assertIn("REVIEWED_SEMANTIC_ASSERTION_MISSING", self.blocker_codes(report))
        self.assertFalse(report["policy_semantics_documented"])
        self.assertFalse(report["accuracy_semantics_documented"])

    def test_arbitrary_policy_bytes_and_profile_booleans_cannot_verify(self):
        (self.root / "reviewed-semantics.json").unlink()
        self.profile["policy_semantics"] = {"documented": True, "applicable_policy_oids": ["tsa_policy1"]}
        self.profile["accuracy_semantics"] = {"documented": True}
        self.assertNotEqual(self.check()["final_rehearsal_status"], "REHEARSAL_VERIFIED")

    def test_semantic_assertion_policy_hash_mismatch_does_not_clear(self):
        self.write_assertion(provider_policy_sha256="0" * 64)
        report = self.check()
        self.assertEqual(report["final_rehearsal_status"], "REHEARSAL_INCOMPLETE")
        self.assertIn("REVIEWED_SEMANTIC_ASSERTION_POLICY_HASH_MISMATCH", self.blocker_codes(report))

    def test_semantic_assertion_wrong_policy_oid_does_not_clear(self):
        self.write_assertion(token_policy_oid="1.2.3.4")
        report = self.check()
        self.assertEqual(report["final_rehearsal_status"], "REHEARSAL_INCOMPLETE")
        self.assertIn("REVIEWED_SEMANTIC_ASSERTION_POLICY_OID_MISMATCH", self.blocker_codes(report))

    def test_negative_conservative_accuracy_bound_does_not_clear(self):
        self.backend.token = replace(self.backend.token, accuracy="unspecified")
        self.write_assertion(
            accuracy_review_disposition="DOCUMENTED_CONSERVATIVE_BOUND",
            observed_token_accuracy="unspecified",
            conservative_accuracy_bound_seconds=-1,
        )
        report = self.check()
        self.assertEqual(report["final_rehearsal_status"], "REHEARSAL_INCOMPLETE")
        self.assertIn("REVIEWED_SEMANTIC_ASSERTION_INVALID", self.blocker_codes(report))

    def test_present_assertion_without_accuracy_review_does_not_clear(self):
        self.backend.token = replace(self.backend.token, accuracy="unspecified")
        self.write_assertion(
            accuracy_review_disposition="NOT_DOCUMENTED",
            observed_token_accuracy="unspecified",
        )
        report = self.check()
        self.assertEqual(report["final_rehearsal_status"], "REHEARSAL_INCOMPLETE")
        self.assertFalse(report["accuracy_semantics_documented"])

    def test_missing_reviewer_id_does_not_clear_semantic_blockers(self):
        self.write_assertion(reviewer_id=None)
        report = self.check()
        self.assertEqual(report["final_rehearsal_status"], "REHEARSAL_INCOMPLETE")
        self.assertIn("REVIEWED_SEMANTIC_ASSERTION_INVALID", self.blocker_codes(report))

    def test_missing_reviewer_authority_does_not_clear_semantic_blockers(self):
        self.write_assertion(review_authority=None)
        report = self.check()
        self.assertEqual(report["final_rehearsal_status"], "REHEARSAL_INCOMPLETE")
        self.assertIn("REVIEWED_SEMANTIC_ASSERTION_INVALID", self.blocker_codes(report))

    def test_missing_reviewer_basis_does_not_clear_semantic_blockers(self):
        self.write_assertion(review_basis=None)
        report = self.check()
        self.assertEqual(report["final_rehearsal_status"], "REHEARSAL_INCOMPLETE")
        self.assertIn("REVIEWED_SEMANTIC_ASSERTION_INVALID", self.blocker_codes(report))

    def test_empty_reviewer_provenance_is_rejected(self):
        for field in ("reviewer_id", "review_authority", "review_basis"):
            with self.subTest(field=field):
                self.write_assertion(**{field: "   "})
                self.assertIn("REVIEWED_SEMANTIC_ASSERTION_INVALID", self.blocker_codes(self.check()))

    def test_accuracy_observation_mismatch_does_not_clear(self):
        self.write_assertion(observed_token_accuracy="10 seconds")
        report = self.check()
        self.assertEqual(report["final_rehearsal_status"], "REHEARSAL_INCOMPLETE")
        self.assertIn("REVIEWED_SEMANTIC_ASSERTION_ACCURACY_MISMATCH", self.blocker_codes(report))

    def test_one_second_assertion_cannot_validate_ten_second_token(self):
        self.backend.token = replace(self.backend.token, accuracy="10 seconds")
        report = self.check()
        self.assertIn("REVIEWED_SEMANTIC_ASSERTION_ACCURACY_MISMATCH", self.blocker_codes(report))

    def test_conservative_bound_rejects_specified_observed_accuracy(self):
        self.write_assertion(
            accuracy_review_disposition="DOCUMENTED_CONSERVATIVE_BOUND",
            observed_token_accuracy="1 second",
            conservative_accuracy_bound_seconds=1,
        )
        self.assertIn("REVIEWED_SEMANTIC_ASSERTION_INVALID", self.blocker_codes(self.check()))

    def test_accepted_accuracy_rejects_unspecified_observation(self):
        self.backend.token = replace(self.backend.token, accuracy="unspecified")
        self.write_assertion(observed_token_accuracy="unspecified")
        self.assertIn("REVIEWED_SEMANTIC_ASSERTION_INVALID", self.blocker_codes(self.check()))

    def test_accepted_accuracy_rejects_conservative_bound(self):
        self.write_assertion(conservative_accuracy_bound_seconds=1)
        self.assertIn("REVIEWED_SEMANTIC_ASSERTION_INVALID", self.blocker_codes(self.check()))

    def test_matching_unspecified_accuracy_and_bound_can_verify(self):
        self.backend.token = replace(self.backend.token, accuracy="unspecified")
        self.write_assertion(
            accuracy_review_disposition="DOCUMENTED_CONSERVATIVE_BOUND",
            observed_token_accuracy="unspecified",
            conservative_accuracy_bound_seconds=1,
        )
        self.assertEqual(self.check()["final_rehearsal_status"], "REHEARSAL_VERIFIED")

    def test_malformed_rfc3161_response_fails(self):
        self.backend.parse_error = "bad ASN.1"
        report = self.check()
        self.assertEqual(report["final_rehearsal_status"], "REHEARSAL_FAILED")
        self.assertIn("MALFORMED_RFC3161_RESPONSE", self.blocker_codes(report))

    def test_missing_raw_evidence_fails_closed_as_incomplete(self):
        (self.root / "response.tsr").unlink()
        report = self.check()
        self.assertEqual(report["final_rehearsal_status"], "REHEARSAL_INCOMPLETE")
        self.assertIn("MISSING_RAW_EVIDENCE", self.blocker_codes(report))

    def test_windows_path_hashing_regression_and_determinism(self):
        first = self.check()
        second = self.check()
        self.assertEqual(first, second)
        self.assertEqual(first["subject_sha256"], self.subject_sha256)

    def test_revocation_scope_is_explicitly_signer_only(self):
        report = self.check()
        self.assertEqual(report["revocation_verification_scope"], "TSA_SIGNER_ONLY")
        self.assertEqual(report["crl_evidence"]["verification_scope"], "TSA_SIGNER_ONLY")

    def test_direct_root_signer_selects_root_as_crl_issuer(self):
        report = self.check()
        crl = report["crl_evidence"]
        self.assertEqual(crl["signer_issuer_subject"], self.backend.anchor.subject)
        self.assertEqual(crl["selected_crl_issuer_certificate_subject"], self.backend.anchor.subject)
        self.assertEqual(
            crl["selected_crl_issuer_certificate_sha256_der"], self.backend.anchor.sha256_der
        )
        self.assertTrue(crl["crl_issuer_matches_signer_issuer"])
        self.assertEqual(self.backend.crl_signature_issuer, self.backend.anchor.pem)

    def test_intermediate_issued_signer_crl_passes_signer_only_revocation(self):
        _, intermediate, _ = self.configure_intermediate_issued_signer()
        report = self.check()
        self.assertEqual(report["final_rehearsal_status"], "REHEARSAL_VERIFIED")
        self.assertEqual(
            report["crl_evidence"]["selected_crl_issuer_certificate_sha256_der"],
            intermediate.sha256_der,
        )
        self.assertEqual(self.backend.crl_signature_issuer, intermediate.pem)

    def test_wrong_intermediate_fails_chain_validation(self):
        self.configure_intermediate_issued_signer()
        self.backend.chain_result = (False, "certificate signature failure")
        report = self.check()
        self.assertEqual(report["final_rehearsal_status"], "REHEARSAL_FAILED")
        self.assertIn("CERTIFICATE_CHAIN_VERIFICATION_FAILED", self.blocker_codes(report))
        self.assertIn("CERTIFICATE_REVOCATION_CHECK_FAILED", self.blocker_codes(report))

    def test_root_issued_crl_for_intermediate_issued_signer_fails(self):
        _, _, root = self.configure_intermediate_issued_signer()
        self.backend.crl = replace(self.backend.crl, issuer=root.subject)
        report = self.check()
        self.assertIn("CRL_ISSUER_MISMATCH", self.blocker_codes(report))
        self.assertFalse(report["crl_evidence"]["crl_issuer_matches_signer_issuer"])

    def test_crl_issuer_subject_mismatch_fails(self):
        self.backend.crl = replace(self.backend.crl, issuer="CN=Unrelated CRL Issuer")
        self.assertIn("CRL_ISSUER_MISMATCH", self.blocker_codes(self.check()))

    def test_missing_direct_issuer_fails_closed(self):
        tsa, root = self.backend.token.certificates
        tsa = replace(tsa, issuer="CN=Missing Intermediate")
        self.backend.token = replace(
            self.backend.token, certificates=(tsa, root), signer_sha256_der=tsa.sha256_der
        )
        report = self.check()
        self.assertIn("SIGNER_ISSUER_CERTIFICATE_SELECTION_FAILED", self.blocker_codes(report))
        self.assertEqual(
            report["crl_evidence"]["selected_crl_issuer_certificate_subject"], "UNAVAILABLE"
        )

    def test_ambiguous_direct_issuer_fails_closed(self):
        _, intermediate, _ = self.configure_intermediate_issued_signer()
        duplicate_subject = replace(
            intermediate,
            serial="03",
            sha256_der="3" * 64,
            pem=b"different intermediate certificate",
        )
        self.backend.chain_certificates = (intermediate, duplicate_subject)
        report = self.check()
        self.assertIn("SIGNER_ISSUER_CERTIFICATE_SELECTION_FAILED", self.blocker_codes(report))
        self.assertIsNone(self.backend.crl_signature_issuer)

    def test_unrelated_untrusted_intermediate_cannot_satisfy_signer_issuer(self):
        tsa, root = self.backend.token.certificates
        tsa = replace(tsa, issuer="CN=Expected Intermediate")
        unrelated = replace(
            root,
            subject="CN=Unrelated Intermediate",
            serial="04",
            sha256_der="4" * 64,
            pem=b"unrelated intermediate certificate",
        )
        self.backend.token = replace(
            self.backend.token, certificates=(tsa, root), signer_sha256_der=tsa.sha256_der
        )
        self.backend.chain_certificates = (unrelated,)
        report = self.check()
        self.assertIn("SIGNER_ISSUER_CERTIFICATE_SELECTION_FAILED", self.blocker_codes(report))

    def test_multi_level_inventory_does_not_claim_full_path_revocation(self):
        tsa, root = self.backend.token.certificates
        intermediate = replace(
            tsa,
            subject="CN=Intermediate TSA CA",
            serial="02",
            sha256_der="2" * 64,
        )
        self.backend.token = replace(self.backend.token, certificates=(tsa, intermediate, root))
        report = self.check()
        self.assertNotEqual(report["revocation_verification_scope"], "FULL_CERTIFICATION_PATH")

    def test_escaping_evidence_path_is_rejected(self):
        self.profile["evidence_files"]["subject"] = "../subject.txt"
        report = self.check()
        self.assertEqual(report["final_rehearsal_status"], "REHEARSAL_INCOMPLETE")
        self.assertIn("MISSING_RAW_EVIDENCE", self.blocker_codes(report))


@unittest.skipUnless(OPENSSL_EXECUTABLE, "OpenSSL is required for PKI integration coverage")
class OpenSSLSignerCrlIntegrationTests(unittest.TestCase):
    def test_intermediate_issued_signer_and_crl_validate_to_independent_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            def run(*args):
                subprocess.run(
                    [OPENSSL_EXECUTABLE, *args], cwd=root, check=True, capture_output=True
                )

            run(
                "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                "-keyout", "root.key", "-out", "root.pem", "-days", "3650",
                "-subj", "/CN=Synthetic Root",
                "-addext", "basicConstraints=critical,CA:TRUE",
                "-addext", "keyUsage=critical,keyCertSign,cRLSign",
            )
            run(
                "req", "-new", "-newkey", "rsa:2048", "-nodes",
                "-keyout", "intermediate.key", "-out", "intermediate.csr",
                "-subj", "/CN=Synthetic Intermediate",
                "-addext", "basicConstraints=critical,CA:TRUE",
                "-addext", "keyUsage=critical,keyCertSign,cRLSign",
            )
            run(
                "x509", "-req", "-in", "intermediate.csr", "-CA", "root.pem",
                "-CAkey", "root.key", "-set_serial", "2", "-days", "3650",
                "-copy_extensions", "copy", "-out", "intermediate.pem",
            )
            run(
                "req", "-new", "-newkey", "rsa:2048", "-nodes",
                "-keyout", "signer.key", "-out", "signer.csr",
                "-subj", "/CN=Synthetic TSA Signer",
                "-addext", "basicConstraints=critical,CA:FALSE",
                "-addext", "keyUsage=critical,digitalSignature",
                "-addext", "extendedKeyUsage=critical,timeStamping",
            )
            run(
                "x509", "-req", "-in", "signer.csr", "-CA", "intermediate.pem",
                "-CAkey", "intermediate.key", "-set_serial", "3", "-days", "3650",
                "-copy_extensions", "copy", "-out", "signer.pem",
            )
            (root / "index.txt").write_text("", encoding="ascii")
            (root / "serial").write_text("1000\n", encoding="ascii")
            (root / "crlnumber").write_text("1000\n", encoding="ascii")
            (root / "ca.cnf").write_text(
                """[ca]
default_ca=issuer_ca
[issuer_ca]
database=index.txt
new_certs_dir=.
certificate=intermediate.pem
private_key=intermediate.key
serial=serial
crlnumber=crlnumber
default_md=sha256
default_days=365
default_crl_days=30
policy=policy_any
[policy_any]
commonName=supplied
""",
                encoding="ascii",
            )
            run("ca", "-gencrl", "-config", "ca.cnf", "-out", "intermediate.crl", "-batch")

            backend = OpenSSLBackend(OPENSSL_EXECUTABLE)
            at_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            chain_ok, _ = backend.verify_chain(
                (root / "signer.pem").read_bytes(),
                root / "root.pem",
                root / "intermediate.pem",
                root / "intermediate.crl",
                at_time,
            )
            signature_ok, _ = backend.verify_crl_signature(
                root / "intermediate.crl", (root / "intermediate.pem").read_bytes()
            )
            wrong_issuer_ok, _ = backend.verify_crl_signature(
                root / "intermediate.crl", (root / "root.pem").read_bytes()
            )
            self.assertTrue(chain_ok)
            self.assertTrue(signature_ok)
            self.assertFalse(wrong_issuer_ok)


class RetainedRFC3161ReportTests(unittest.TestCase):
    def test_retained_reports_are_sealed_and_non_forecast(self):
        reports_dir = Path(__file__).resolve().parents[1] / "genesis" / "rehearsal" / "reports"
        reports = {
            path.stem: json.loads(path.read_text(encoding="utf-8"))
            for path in reports_dir.glob("*_report.json")
        }
        self.assertEqual(
            set(reports),
            {
                "freetsa_v2_report",
                "digicert_v2_report",
                "sectigo_v2_report",
                "sectigo_qualified_v1_report",
            },
        )
        for report in reports.values():
            self.assertTrue(verify_sealed_object(report))
            self.assertEqual(report["classification"], "NON_FORECAST_REHEARSAL")
            self.assertIs(report["prospective_eligible"], False)
            self.assertEqual(
                report["subject_sha256"],
                "3837b8ce2e012a913cbdab6f7e52bdc045013bdc4acfbc88abc99cee149275c6",
            )
        for name in ("freetsa_v2_report", "digicert_v2_report", "sectigo_v2_report"):
            self.assertEqual(reports[name]["final_rehearsal_status"], "REHEARSAL_INCOMPLETE")
        self.assertEqual(
            reports["sectigo_qualified_v1_report"]["final_rehearsal_status"],
            "REHEARSAL_VERIFIED",
        )

    def test_freetsa_report_reproduces_known_observations(self):
        path = Path(__file__).resolve().parents[1] / "genesis" / "rehearsal" / "reports" / "freetsa_v2_report.json"
        report = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(report["rfc3161_response_status"], "GRANTED")
        self.assertTrue(report["message_imprint_matches_subject"])
        self.assertTrue(report["nonce_equal"])
        self.assertTrue(report["certificate_requested"])
        self.assertEqual(report["token_policy_oid"], "tsa_policy1")
        self.assertEqual(report["token_accuracy"], "unspecified")
        self.assertEqual(report["token_ordering"], "yes")
        self.assertEqual(report["tsa_certificate_serial"], "C2E986160DA8E9CD")
        self.assertEqual(
            report["tsa_certificate_sha256_der"],
            "32e841a95cc1164101ffde41298ef2fc75c1c4372ef095e88a6bbd47dfb191fc",
        )
        self.assertTrue(report["independent_tsa_certificate_matches_embedded"])
        self.assertEqual(
            report["trust_anchor_sha256_der"],
            "a6379e7cecc05faa3cbf076013d745e327bbbaa38c0b9af22469d4701d18aabc",
        )
        self.assertTrue(report["trust_anchor_matches_embedded_certificate"])
        self.assertTrue(report["certificate_chain_verification"]["verified"])
        self.assertTrue(report["rfc3161_signature_verification"]["verified"])
        self.assertTrue(report["crl_evidence"]["signature_verification"]["verified"])
        self.assertTrue(report["crl_evidence"]["certificate_revocation_check"]["verified"])
        self.assertTrue(
            {"TIMESTAMP_ACCURACY_UNSPECIFIED", "TOKEN_POLICY_SEMANTICS_UNDOCUMENTED"}.issubset(
                {item["code"] for item in report["unresolved_qualification_blockers"]}
            )
        )

    def test_sectigo_qualified_report_reproduces_reviewed_observations(self):
        path = (
            Path(__file__).resolve().parents[1]
            / "genesis"
            / "rehearsal"
            / "reports"
            / "sectigo_qualified_v1_report.json"
        )
        report = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(report["final_rehearsal_status"], "REHEARSAL_VERIFIED")
        self.assertEqual(report["token_policy_oid"], "0.4.0.2023.1.1")
        self.assertEqual(
            report["token_accuracy"],
            "0x01 seconds, unspecified millis, unspecified micros",
        )
        self.assertEqual(report["request_nonce"], "20812634066f3b14")
        self.assertEqual(report["response_nonce"], "20812634066f3b14")
        self.assertEqual(
            report["crl_evidence"]["selected_crl_issuer_certificate_sha256_der"],
            "cd0a3e00a1bdae3a159fa9e3d70f8e664f560fdce16357cbe440ed0b0d88244f",
        )
        self.assertTrue(report["semantic_assertion_evidence"]["verified"])


if __name__ == "__main__":
    unittest.main()
