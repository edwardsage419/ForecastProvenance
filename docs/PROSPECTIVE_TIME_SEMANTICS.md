# Prospective Time Semantics

Version: 0.2 candidate
Status: FTC_001 REMEDIATION CANDIDATE

## External proof rule

Local `claimed_issued_at`, Git metadata, filesystem time, signatures without an independent time source, and locally claimed anchor submission time are operational metadata only.

For a forecast to qualify as externally verified prospective evidence, the validator must establish an accepted external existence bound for the exact anchored issuance cycle manifest.

## Deadline inequality

Each planned forecast slot binds an `external_proof_deadline` derived from the accepted target and Genesis protocol.

Version 1 eligibility uses:

```text
verified_external_existence_bound <= external_proof_deadline
```

The exact construction of `verified_external_existence_bound` is anchor scheme specific and must be frozen before Genesis.

If the bound is later than the deadline, the slot is `LATE_OR_INELIGIBLE`.

If the bound cannot be established, the slot is `INELIGIBLE_TRUST_UNKNOWN` or remains pending when the accepted anchor scheme explicitly supports a pending state.

## Anchor latency

Operational submission latency may be measured for reliability, but a locally claimed submission timestamp cannot determine scientific prospective eligibility.

Genesis can impose operational service targets separately.

## Target relationship

The target contract or Genesis bound target profile must define how `external_proof_deadline` relates to target closure, outcome observability, and information cutoff.

The deadline must be fixed before forecast output inspection.

A target is Genesis eligible only when the selected anchor's conservative external time precision is adequate for this deadline.

## OpenTimestamps candidate

For OTS_BTC_BATCH_V1, Genesis acceptance testing must define and independently test the conservative Bitcoin attestation time bound used by the verifier. The project must not claim second level precision.

Pending proof does not establish final prospective verification.
