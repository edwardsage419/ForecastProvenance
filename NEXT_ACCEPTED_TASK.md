# Next Accepted Task

Task ID: GEN_001
State: READINESS REVIEW OPEN

## Objective

Complete Genesis readiness without creating Forecast Ledger history or issuing genuine forecasts.

## Delivered design candidate

1. FPP_TIME_EVIDENCE_V1 separates precise signed wall-clock deadline evidence from Bitcoin durability evidence.
2. DEADLINE_RECEIPT_QUORUM_V1 requires two independent provider groups and at least one RFC 3161 receipt.
3. OTS_BTC_BUNDLE_V1 anchors the accepted external-time evidence bundle and requires strong Bitcoin Core verification.
4. Bootstrap governance uses an owner-controlled Ed25519 key outside the candidate manifest graph.
5. Genesis manifest and ManifestAcceptance sequence is defined.
6. Deterministic IssuanceSchedulePolicy and schedule-change semantics are defined.
7. Initial target candidate set contains CPI monthly change, U-3 unemployment rate, and real GDP Advance Estimate.
8. Official source-contract candidates are defined for BLS and BEA schedule and first-release artifacts.
9. Transparent last-observed first-release baseline is defined.
10. Continuous scalar evaluation uses absolute error and squared error with target-specific reporting.
11. Genesis abort conditions and first-pass readiness adversarial review are recorded.

## Required external and implementation closure

1. Run live non-forecast RFC 3161 provider rehearsals from a networked owner-controlled environment.
2. Freeze exact qualifying provider profiles including signer chain, policy OID, accuracy, nonce behavior, and revocation capture.
3. Generate the owner Ed25519 bootstrap key locally and supply only its public key to the project.
4. Run a non-forecast OpenTimestamps stamp, proof upgrade, and strong Bitcoin Core verification.
5. Implement and adversarially test target-specific archive and parser fixtures for the three candidate targets.
6. Seal exact TargetDefinition, ResolutionRule, SourceContract, schedule, baseline, policy, and evaluation objects for the candidate Genesis manifest.
7. Run final Genesis readiness adversarial review.

## Allowed work

1. Genesis readiness documents and synthetic tests.
2. Non-forecast external time-provider rehearsals.
3. Non-forecast OTS and Bitcoin verification rehearsal.
4. Official archived release parser fixtures that are permanently marked non-prospective.
5. Construction of candidate governance, target, policy, and manifest objects.
6. Independent verification tooling required for Genesis readiness.

## Prohibited work

1. Genuine prospective forecast issuance.
2. Forecast Ledger Genesis creation.
3. Production model or LLM forecast execution.
4. Generating forecast values to choose or reject Genesis targets.
5. Treating rehearsal artifacts as native prospective evidence.
6. Importing Psychohistory artifacts as native evidence.
7. Paid infrastructure without a separate governance exception.
8. Hosted API, frontend, persistent service, or production database work.

## Exit criteria

GEN_001 exits only when external provider profiles and rehearsals, bootstrap public key, strong OTS verification, target parser/source fixtures, exact candidate manifest object closure, and final adversarial review have no unresolved blocking finding.

Completion of GEN_001 authorizes only a separate Genesis acceptance decision. It does not create Forecast Ledger Genesis or authorize a genuine prospective forecast.