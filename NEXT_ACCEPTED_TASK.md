# Next Accepted Task

Task ID: GEN_001
State: OWNER EVIDENCE AND FINAL FREEZE REQUIRED

## Objective

Complete Genesis readiness without creating Forecast Ledger history or issuing genuine forecasts.

## Repository work already delivered

1. FPP_TIME_EVIDENCE_V1 separates signed wall-clock deadline evidence from Bitcoin durability evidence.
2. DEADLINE_RECEIPT_QUORUM_V1 requires two independent provider groups and at least one RFC 3161 receipt.
3. The historical provider design snapshot started from FreeTSA and DigiCert with Sectigo as backup; current qualification state is maintained separately in `docs/GENESIS_PROVIDER_QUALIFICATION_STATUS_2026_09_11.md`.
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
22. Reusable RFC 3161 qualification rehearsal automation emits sealed, permanently non-prospective reports for FreeTSA, DigiCert, Sectigo ordinary, and Sectigo Qualified.
23. RFC 3161 checker engineering is closed at checker version 1.3 and report schema 1.2 unless new external evidence exposes a concrete correctness or security defect.
24. Sectigo Qualified has a retained `REHEARSAL_VERIFIED` report but remains `NON_FORECAST_REHEARSAL`, `prospective_eligible=false`, and `PRODUCTION_QUALIFIED=NO`.
25. Signicat AS is the current leading second-provider candidate and remains `SIGNICAT NOT READY FOR NON_FORECAST_REHEARSAL` pending explicit authorization and critical signer-identity evidence.

## Required owner-controlled external closure

1. Close two independent provider groups under the frozen quorum rule. FreeTSA remains `REHEARSAL_INCOMPLETE` because directly applicable `tsa_policy1` semantics and a conservative accuracy bound remain undocumented. DigiCert remains `REHEARSAL_INCOMPLETE` with insufficient retained accuracy evidence. Sectigo ordinary remains `REHEARSAL_INCOMPLETE`. Sectigo Qualified is `REHEARSAL_VERIFIED` but still lacks closed production entitlement and controlling commercial terms.
2. Obtain direct written Sectigo confirmation sufficient to resolve production authorization, controlling contract, entitlement, pricing, quota, SLA, support, maintenance, termination, and related production-operational requirements before any production ProviderProfile is considered.
3. Obtain direct written Signicat confirmation sufficient to evaluate `REHEARSAL_AUTHORIZATION`, including the exact authorized endpoint, operative signer set and trusted-list mapping, policy, nonce/request semantics, revocation behavior, and applicable rate or automation constraints. Do not send a Signicat RFC 3161 request until a separate independent review marks it ready and a separate task authorizes the exact request.
4. Generate the owner Ed25519 bootstrap key locally and provide only the public key and its SHA256.
5. Run a non-forecast OpenTimestamps stamp, proof upgrade, and strong Bitcoin Core verification.
6. Retrieve and retain the three selected retrospective official BLS and BEA raw source fixtures with SHA256 metadata.
7. Preserve all failed and successful rehearsal artifacts needed for provider and operational review.

## Provider qualification rules

1. `REHEARSAL_AUTHORIZATION != PRODUCTION_AUTHORIZATION`.
2. `REHEARSAL_VERIFIED != PRODUCTION_QUALIFIED`.
3. A successful rehearsal never grants production entitlement or Genesis quorum eligibility by itself.
4. The RFC 3161 deadline upper bound remains `genTime + declared_accuracy`.
5. Provider-group independence is defined by independent operational trust authority. Ordinary supplier overlap is due diligence unless it is demonstrated to create shared timestamp-issuance control, shared signing-key control, a common PKI authority, or another dependency that defeats the independent-provider-group assumption.
6. No production ProviderProfile may be created or frozen until the separately required qualification and final-freeze evidence is closed.

## Required final-freeze closure after owner evidence is available

8. Convert qualifying time-provider evidence into sealed production ProviderProfile objects only after production qualification prerequisites are closed.
9. Validate real official source bytes through the source adapters and retain exact semantic reports.
10. Run the full final test suite and content-address the final report.
11. Build exact ValidatorContract against the final candidate commit and final test report.
12. Seal BootstrapGovernanceRoot, OTS verifier profile, final candidate TrustedManifest, and ManifestAcceptance inputs.
13. Run final Genesis readiness adversarial review with no unresolved blocking finding.

## Allowed work

1. Genesis readiness documents and synthetic tests.
2. Read-only provider qualification assessments and direct provider inquiries that issue no timestamp request.
3. Separately authorized non-forecast external time-provider rehearsals after provider-specific rehearsal entry criteria close.
4. Non-forecast OTS and Bitcoin verification rehearsal.
5. Official archived release parser fixtures permanently marked non-prospective.
6. Construction of candidate governance, target, policy, validator, and manifest objects.
7. Production ProviderProfile construction only in a separately authorized final-freeze task after qualification prerequisites close.
8. Independent verification tooling required for Genesis readiness.
9. Fail-closed tests for every new readiness object or external-evidence parser.

## Prohibited work

1. Genuine prospective forecast issuance.
2. Forecast Ledger Genesis creation.
3. Production model or LLM forecast execution.
4. Generating forecast values to choose or reject Genesis targets.
5. Treating rehearsal artifacts as native prospective evidence.
6. Importing Psychohistory artifacts as native evidence.
7. Uploading or committing the owner private signing key.
8. Weakening receipt quorum because of provider outage.
9. Sending a provider RFC 3161 request without a separate task authorizing the exact request after entry criteria are reviewed.
10. Treating public endpoint reachability, anonymous access, or successful rehearsal as production authorization.
11. Paid infrastructure without a separate governance exception.
12. Hosted API, frontend, persistent service, or production database work.

## Exit criteria

GEN_001 exits only when every required item through GR038 in `GENESIS_READINESS_EVIDENCE_MATRIX.md` is closed for the selected final Genesis profile and final adversarial review contains no blocking finding.

Completion of GEN_001 authorizes only a separate Genesis acceptance decision. It does not create Forecast Ledger Genesis or authorize a genuine prospective forecast.
