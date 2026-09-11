# RFC 3161 Provider Qualification Rehearsal Checker

Version: 1.1
Status: GEN_001 QUALIFICATION READINESS TOOLING

This checker evaluates retained RFC 3161 rehearsal evidence. It does not create
a forecast, execute Genesis, create Forecast Ledger Genesis, accept a Genesis
Manifest, or grant production qualification.

Every input profile must state:

```json
{
  "provider_id": "freetsa_rfc3161",
  "classification": "NON_FORECAST_REHEARSAL",
  "prospective_eligible": false,
  "captured_utc": "2026-09-11T00:00:00Z",
  "trust_anchor_source": "independently retrieved provider Root CA",
  "provider_policy_evidence_source": "UNAVAILABLE",
  "crl_source": "independently retrieved provider CRL",
  "evidence_files": {
    "subject": "subject.txt",
    "request": "request.tsq",
    "response": "response.tsr",
    "tool_versions": "tool_versions.txt",
    "trust_anchor": "root_ca.pem",
    "untrusted_chain": "chain.pem",
    "crl": "tsa.crl.pem",
    "independent_tsa_certificate": "tsa_independent.pem",
    "provider_policy": "provider-cps.pdf",
    "reviewed_semantic_assertion": "reviewed-semantics.json"
  }
}
```

Profile fields never establish policy or accuracy meaning. Clearing either
semantic blocker requires a separately retained, canonically sealed
`RFC3161ReviewedSemanticAssertion` with classification
`REVIEWED_RFC3161_QUALIFICATION_SEMANTICS`. The assertion binds the exact policy
file SHA256 and observed token policy OID, records independent review
dispositions, identifies a document section/page/reference for audit, and
records the review capture time. When an omitted token accuracy is admitted, the
assertion also records a non-negative conservative bound in seconds.

The assertion payload, before canonical sealing adds `object_type`, `object_id`,
`payload_sha256`, and `content_sha256`, is:

```json
{
  "schema_version": "1.0",
  "classification": "REVIEWED_RFC3161_QUALIFICATION_SEMANTICS",
  "prospective_eligible": false,
  "provider_id": "provider_rfc3161",
  "provider_policy_sha256": "64-lowercase-hex",
  "token_policy_oid": "observed-policy-oid",
  "policy_review_disposition": "DOCUMENTED_APPLICABLE",
  "accuracy_review_disposition": "DOCUMENTED_CONSERVATIVE_BOUND",
  "conservative_accuracy_bound_seconds": 1,
  "evidence_locator": "CPS section/page/reference",
  "reviewed_at": "2026-09-11T00:00:00Z"
}
```

The checker treats `openssl verify -crl_check` as `TSA_SIGNER_ONLY` revocation
verification. It does not claim `FULL_CERTIFICATION_PATH`; that stronger scope
would require every necessary chain revocation artifact and separate support.

Paths are relative to the evidence directory. Absolute paths and paths escaping
the evidence directory are rejected. The checker reads raw evidence but never
modifies it. The output path must not already exist, preventing accidental
overwrite of a historical report.

Run:

```bash
PYTHONPATH=src python3 scripts/genesis/check_rfc3161_rehearsal.py \
  --evidence-dir ~/fpp-genesis-rehearsal/freetsa \
  --provider-profile ~/fpp-genesis-rehearsal/freetsa/provider_profile.json \
  --output ~/fpp-genesis-rehearsal/freetsa/qualification_report_v1.json
```

The same profile shape applies to DigiCert and Sectigo; only retained evidence
and provider-specific policy statements change.

## Decision rule

`REHEARSAL_FAILED` means retained evidence is malformed, contradictory, or
failed a cryptographic or validity check.

`REHEARSAL_INCOMPLETE` means no failed check was observed but mandatory raw,
revocation, policy, or accuracy evidence is missing. Missing policy semantics
and unspecified accuracy are never inferred.

`REHEARSAL_VERIFIED` means the configured rehearsal evidence passed all checks
and has no unresolved qualification blocker. It remains a non-forecast
rehearsal and does not imply production qualification.

## FreeTSA observation

The previously observed FreeTSA token policy `tsa_policy1` currently lacks an
observed direct CPS definition, and its token reports `Accuracy: unspecified`.
Those observations necessarily produce `REHEARSAL_INCOMPLETE` with
`TOKEN_POLICY_SEMANTICS_UNDOCUMENTED` and
`TIMESTAMP_ACCURACY_UNSPECIFIED`, even when every cryptographic check succeeds.

DigiCert and Sectigo raw requests and responses parse and bind the known
non-forecast subject. They remain `REHEARSAL_INCOMPLETE` until their independent
signer and trust-anchor material, revocation material, applicable policy
semantics, and accuracy semantics are retained and checked.
