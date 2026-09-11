# Next Accepted Task

Task ID: GEN_001
State: READINESS REVIEW OPEN

## Objective

Complete Genesis readiness without creating Forecast Ledger history or issuing genuine forecasts.

## Delivered design and repository closure

1. FPP_TIME_EVIDENCE_V1 separates signed wall-clock deadline evidence from Bitcoin durability evidence.
2. DEADLINE_RECEIPT_QUORUM_V1 requires two independent provider groups and at least one RFC 3161 receipt.
3. OTS_BTC_BUNDLE_V1 anchors the accepted external-time evidence bundle and requires strong Bitcoin Core verification.
4. Bootstrap governance uses an owner-controlled Ed25519 key outside the candidate manifest graph.
5. Genesis manifest and ManifestAcceptance sequence is defined.
6. Deterministic IssuanceSchedulePolicy uses one cycle per official target release instance.
7. Initial target candidate set contains CPI monthly change, U-3 unemployment rate, and real GDP Advance Estimate.
8. Official source-contract candidates are defined for BLS and BEA schedule and first-release artifacts.
9. Semantic target parsing is implemented with synthetic fail-closed regression tests.
10. Transparent last-observed first-release baseline is defined.
11. Continuous scalar evaluation uses absolute error and squared error with target-specific reporting.
12. Retry, omission, correction, retention, human-review, and acceptance policies are materialized as sealed candidate objects.
13. Genesis abort conditions and first-pass readiness adversarial review are recorded.
14. Candidate object lineage is explicit: version 0.2 base plus version 0.3 patch, for 22 effective sealed objects.
15. Candidate seal, predecessor-hash, effective-count, schedule, policy-presence, and full dependency-closure tests are present.
16. Owner external-readiness runbook and non-forecast Ed25519, RFC 3161, and OpenTimestamps rehearsal scripts are prepared.

## Required owner-controlled external closure

1. Run live non-forecast wall-clock provider rehearsals from a networked owner-controlled environment.
2. Freeze exact qualifying provider profiles including signer chain, policy OID, accuracy, nonce behavior, and revocation capture.
3. Generate the owner Ed25519 bootstrap key locally and supply only its public key to the project.
4. Run a non-forecast OpenTimestamps stamp, proof upgrade, and strong Bitcoin Core verification.

## Required repository and source closure

5. Retain real official BLS and BEA first-release archive bytes and prove the source adapters and semantic parser against those fixtures.
6. Bind the exact Genesis validator implementation at the final candidate commit.
7. Construct the final candidate Genesis TrustedManifest only after all required profiles, public key, source fixtures, and validator binding are fixed.
8. Run final Genesis readiness adversarial review with no unresolved blocking finding.

## Allowed work

1. Genesis readiness documents and synthetic tests.
2. Non-forecast external time-provider rehearsals.
3. Non-forecast OTS and Bitcoin verification rehearsal.
4. Official archived release parser fixtures permanently marked non-prospective.
5. Construction of candidate governance, target, policy, provider-profile, validator, and manifest objects.
6. Independent verification tooling required for Genesis readiness.
7. Fail-closed tests for every new readiness object or external-evidence parser.

## Prohibited work

1. Genuine prospective forecast issuance.
2. Forecast Ledger Genesis creation.
3. Production model or LLM forecast execution.
4. Generating forecast values to choose or reject Genesis targets.
5. Treating rehearsal artifacts as native prospective evidence.
6. Importing Psychohistory artifacts as native evidence.
7. Uploading or committing the owner private signing key.
8. Weakening receipt quorum because of provider outage.
9. Paid infrastructure without a separate governance exception.
10. Hosted API, frontend, persistent service, or production database work.

## Exit criteria

GEN_001 exits only when external provider profiles and rehearsals, bootstrap public key, strong OTS verification, real official source fixtures, exact validator binding, final candidate TrustedManifest closure, and final adversarial review have no unresolved blocking finding.

Completion of GEN_001 authorizes only a separate Genesis acceptance decision. It does not create Forecast Ledger Genesis or authorize a genuine prospective forecast.