# Genesis Abort Conditions

Version: 0.1 candidate
Status: GEN_001 REVIEW CANDIDATE

Genesis fails closed.

A Genesis attempt must be aborted or returned to candidate state when any condition below occurs.

## Governance blockers

1. Bootstrap private key is lost, exposed, copied into repository history, or cannot be shown to remain owner controlled before acceptance.
2. Bootstrap public key or acceptance policy changes after its governance envelope was externally evidenced.
3. ManifestAcceptance signature fails verification or does not bind the exact candidate manifest hash.
4. Competing Genesis acceptances exist without a preexisting deterministic conflict rule.

## Time evidence blockers

1. Fewer than two independent deadline receipt provider groups qualify for a required subject.
2. Any qualifying receipt does not bind the exact subject hash.
3. A provider trust root, signing certificate, policy, or Roughtime key cannot be reproduced from the frozen provider profile.
4. A receipt has no defensible conservative upper time bound.
5. A receipt upper bound exceeds the frozen deadline.
6. The OpenTimestamps proof binds a different bundle hash.
7. Required OpenTimestamps proof bytes are lost.
8. Bitcoin attestation cannot be independently verified under the frozen verifier contract.
9. A real provider is silently replaced by an unreviewed endpoint or key.

## Target and schedule blockers

1. Any initial target lacks a deterministic outcome information barrier.
2. The 24 hour initial issuance safety margin cannot be satisfied.
3. Target semantics, source vintage, resolution rule, or scoring rule remain ambiguous.
4. The schedule permits output inspection before cycle-plan precommitment is externally evidenced.
5. An expected slot is added or removed outside the accepted IssuanceSchedulePolicy.

## Evidence and method blockers

1. Required source availability cannot be established under the frozen SourceContract.
2. A fitted transformation has an unverifiable fit cutoff or state.
3. A confirmatory method has uncontrolled nondeterminism or unverifiable output selection freedom.
4. A production method or evidence source differs from the exact manifest binding.

## Evaluation blockers

1. Confirmatory cohort inclusion can be changed after forecast outcome information becomes available.
2. Withdrawals, omissions, retries, or unresolved cases can disappear from accounting.
3. Scoring semantics are not frozen before first issuance.

## Rehearsal blockers

1. Any configured deadline receipt provider cannot be successfully exercised with a non forecast subject.
2. Receipt parsing or upper bound calculation differs across supported verifier implementations without a documented deterministic resolution.
3. OTS submission, upgrade, or strong Bitcoin verification cannot be reproduced.
4. Mutation tests fail to detect changed subject bytes, receipt bytes, manifest references, or proof references.
5. A rehearsal failure is omitted from the readiness record.

## Cost blockers

1. Genesis requires a recurring paid dependency that has not received an explicit governance exception.
2. A free external provider becomes paid or access restricted before Genesis and no accepted zero cost replacement profile exists.

## Abort record

Every aborted Genesis candidate receives an immutable abort record containing:

```text
candidate_manifest_ref_or_none
abort_stage
reason_codes
evidence_refs
recorded_by
replacement_candidate_ref_or_none
```

An abort record is administrative scientific history, not prospective forecast history.

Failed candidates, rehearsal anchors, and abort records never count toward the native Forecast Ledger.