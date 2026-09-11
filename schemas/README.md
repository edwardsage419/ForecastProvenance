# Schema scope

These JSON Schema files are interoperability descriptions for the first synthetic implementation. The Python validator remains the executable source for frozen v0.4 semantic rules.

No schema in this directory authorizes prospective issuance. The concrete Genesis AnchorScheme and BootstrapGovernanceRoot remain uninstantiated.

`rfc3161_qualification_rehearsal_report.schema.json` describes the sealed output of
the non-forecast RFC 3161 qualification rehearsal checker. Its closed status
vocabulary is `REHEARSAL_VERIFIED`, `REHEARSAL_INCOMPLETE`, and
`REHEARSAL_FAILED`; production qualification is intentionally not representable.

`rfc3161_reviewed_semantic_assertion.schema.json` describes the separately
reviewed, sealed assertion that binds policy and accuracy conclusions to the
exact retained provider-policy SHA256 and observed token policy OID. Provider
profile booleans cannot substitute for this assertion. Version 1.1 also requires
reviewer provenance and binds the exact normalized observed token accuracy; the
provenance fields do not claim cryptographic reviewer authentication.
