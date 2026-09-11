# Next Accepted Task

Task ID: GEN_001
State: OWNER EVIDENCE AND FINAL FREEZE REQUIRED

## Objective

Complete Genesis readiness without creating Forecast Ledger history or issuing genuine forecasts.

## Repository work already delivered

1. FPP_TIME_EVIDENCE_V1 separates signed wall-clock deadline evidence from Bitcoin durability evidence.
2. DEADLINE_RECEIPT_QUORUM_V1 requires two independent provider groups and at least one RFC 3161 receipt.
3. Minimal provider plan is FreeTSA RFC 3161 plus DigiCert RFC 3161; Roughtime is optional.
4. OTS_BTC_BUNDLE_V1 requires strong Bitcoin verification.
5. Bootstrap governance uses an owner-controlled Ed25519 key outside the candidate manifest graph.
6. Genesis manifest and ManifestAcceptance sequence is defined.
7. Deterministic IssuanceSchedulePolicy uses one cycle per official target release instance.
8. Initial target candidate set contains CPI monthly change, U-3 unemployment rate, and real GDP Advance Estimate.
9. Official source-contract candidates are defined for BLS and BEA schedule and first-release artifacts.
10. Semantic target parsing is implemented with synthetic fail-closed regression tests.
11. Retrospective official fixture manifest fixes three historical releases and expected target semantics.
12. Official fixture downloader restricts retrieval to admitted BLS and BEA HTTPS hosts and records raw SHA256 metadata.
13. Transparent last-observed first-release baseline is defined.
14. Continuous scalar evaluation uses absolute error and squared error with target-specific reporting.
15. Retry, omission, correction, retention, human-review, and acceptance policies are materialized as sealed candidate objects.
16. Candidate object lineage is explicit: version 0.2 base plus version 0.3 patch, for 22 effective sealed objects.
17. Candidate seal, predecessor-hash, effective-count, schedule, policy-presence, and full dependency-closure tests are present.
18. Deterministic candidate materializer emits a sorted effective inventory and inventory SHA256.
19. Final validator-binding builder binds final commit, source files, schemas, pyproject, and final test-report SHA256.
20. Owner external-readiness runbook and non-forecast Ed25519, RFC 3161, OpenTimestamps, and source-fixture retrieval tooling are prepared.
21. GENESIS_READINESS_EVIDENCE_MATRIX.md is the authoritative closure checklist.
22. Reusable RFC 3161 qualification rehearsal automation emits sealed, permanently non-prospective reports for FreeTSA, DigiCert, and Sectigo.

## Required owner-controlled external closure

1. Resolve the retained RFC 3161 rehearsal blockers. FreeTSA still needs directly applicable `tsa_policy1` semantics and a conservative accuracy bound; DigiCert and Sectigo still need independent trust, revocation, policy, and accuracy packages.
2. Generate the owner Ed25519 bootstrap key locally and provide only the public key and its SHA256.
3. Run a non-forecast OpenTimestamps stamp, proof upgrade, and strong Bitcoin Core verification.
4. Retrieve and retain the three selected retrospective official BLS and BEA raw source fixtures with SHA256 metadata.
5. Preserve all failed and successful rehearsal artifacts needed for provider and operational review.

## Required final-freeze closure after owner evidence is available

6. Convert qualifying time-provider rehearsals into sealed ProviderProfile objects.
7. Validate real official source bytes through the source adapters and retain exact semantic reports.
8. Run the full final test suite and content-address the final report.
9. Build exact ValidatorContract against the final candidate commit and final test report.
10. Seal BootstrapGovernanceRoot, OTS verifier profile, final candidate TrustedManifest, and ManifestAcceptance inputs.
11. Run final Genesis readiness adversarial review with no unresolved blocking finding.

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

GEN_001 exits only when every required item through GR038 in `GENESIS_READINESS_EVIDENCE_MATRIX.md` is closed for the selected final Genesis profile and final adversarial review contains no blocking finding.

Completion of GEN_001 authorizes only a separate Genesis acceptance decision. It does not create Forecast Ledger Genesis or authorize a genuine prospective forecast.
