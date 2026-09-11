# Next Accepted Task

Task ID: GEN_001
State: ZERO COST PROVIDER REHEARSAL READINESS REQUIRED

## Objective

Complete Genesis readiness without creating Forecast Ledger history, issuing genuine forecasts, or introducing a recurring paid service dependency.

## Repository work already delivered

1. FPP_TIME_EVIDENCE_V1 separates signed wall clock deadline evidence from Bitcoin durability evidence.
2. Deadline quorum remains fail closed and requires two independent provider groups.
3. The current candidate quorum object is `policy:deadline-receipt-quorum:v2`.
4. Version 2 uses an exactly three frozen independent Roughtime provider pool with a two receipt threshold.
5. RFC 3161 is optional auxiliary evidence for the current minimum profile.
6. The historical RFC 3161 checker remains frozen at version 1.3 and report schema 1.2 absent a new concrete correctness or security defect.
7. Existing FreeTSA, DigiCert, Sectigo ordinary, and Sectigo Qualified rehearsal artifacts remain permanently non forecast historical evidence.
8. Commercial Sectigo and Signicat qualification work is paused for the Genesis minimum profile.
9. OTS_BTC_BUNDLE_V1 remains the Bitcoin durability layer.
10. Bootstrap governance uses an owner controlled Ed25519 key outside the candidate manifest graph.
11. Genesis manifest and ManifestAcceptance sequence is defined.
12. Deterministic IssuanceSchedulePolicy uses one cycle per official target release instance.
13. Initial target candidate set contains CPI monthly change, U-3 unemployment rate, and real GDP Advance Estimate.
14. Official source contract candidates and semantic target parsing are implemented.
15. The initial method set contains only `method:last-observed-value:v1`.
16. Candidate object lineage is append only: v0.2 base, v0.3 predecessor patch, and v0.4 current patch.
17. Version 0.4 retires the old deadline quorum object by exact predecessor content hash and adds the version 2 zero cost quorum object.
18. The effective candidate still contains 22 sealed objects.
19. The materializer applies predecessor patches in order and fails closed on retirement hash mismatch, replacement hash mismatch, duplicate additions, dependency mismatch, or object count mismatch.
20. Repository tests assert two of three threshold semantics, provider independence, subject bound Roughtime nonce semantics, midpoint plus radius upper bound, provider outage behavior, unlisted provider rejection, key rotation behavior, and zero recurring cash cost policy.

## Current Roughtime candidate pool

The current read only candidates are:

1. `roughtime.se`
2. `time.txryan.com`
3. `Cloudflare-Roughtime-2`

All three remain:

`NOT READY FOR NON_FORECAST_REHEARSAL`

No Roughtime request has been authorized.

## Required next closure

The next accepted work is provider rehearsal readiness review only.

For each Roughtime candidate, obtain and retain enough authoritative public evidence to freeze a rehearsal entry profile containing:

```text
provider_id
operator_identity
endpoint
protocol_version
root_public_key
usage_authorization_basis
time_source_disclosure
subject_nonce_construction
verifier_implementation_and_version
raw_request_response_retention_rule
upper_bound_rule
key_rotation_rule
independence_classification
```

Then perform an independent read only review of the three entry profiles.

If all three are suitable, mark each:

`READY FOR NON_FORECAST_REHEARSAL`

That state still does not authorize a request.

The actual UDP request or other Roughtime network query must be authorized in a separate task that names the exact synthetic subject and exact provider set.

## Required owner controlled external closure after rehearsal readiness

1. Separately authorize and run synthetic Roughtime rehearsals for the frozen three provider pool.
2. Retain all successful and failed raw evidence.
3. Independently verify each rehearsal before creating any final ProviderProfile.
4. Generate the owner Ed25519 bootstrap key locally and provide only the public key and its SHA256.
5. Run a non forecast OpenTimestamps stamp, proof upgrade, and strong Bitcoin Core verification.
6. Retrieve and retain the three selected retrospective official BLS and BEA raw source fixtures with SHA256 metadata.
7. Preserve all failed and successful rehearsal artifacts needed for operational review.

## Provider qualification rules

1. `REHEARSAL_AUTHORIZATION != GENESIS_AUTHORIZATION`.
2. A successful rehearsal never creates prospective evidence.
3. A successful rehearsal never creates Forecast Ledger history.
4. The deadline upper bound for Roughtime is `midpoint + radius`.
5. At least two receipts must independently satisfy the frozen deadline.
6. Provider outage never lowers the required threshold.
7. Unlisted providers cannot be substituted after observing failures.
8. Provider key rotation requires a new ProviderProfile and accepted manifest change before the new key can qualify.
9. Final provider groups are defined by independent operational trust authority.
10. No paid commercial provider is required by the selected minimum profile.
11. RFC 3161 is optional auxiliary evidence and cannot substitute for the required Roughtime threshold under version 2.

## Required final freeze after owner evidence is available

1. Convert all three successful Roughtime provider rehearsals into exact sealed ProviderProfiles only after qualification evidence closes.
2. Validate real official source bytes through the source adapters and retain exact semantic reports.
3. Run the full final test suite and content address the final report.
4. Build exact ValidatorContract against the final candidate commit and final test report.
5. Seal BootstrapGovernanceRoot, OTS verifier profile, final candidate TrustedManifest, and ManifestAcceptance inputs.
6. Run final Genesis readiness adversarial review with no unresolved blocking finding.

## Allowed work

1. Genesis readiness documents and synthetic tests.
2. Read only Roughtime provider qualification assessments.
3. Development of local offline Roughtime parsing and verification tests that issue no network request.
4. Separately authorized non forecast external provider rehearsals after provider specific entry criteria close.
5. Non forecast OTS and Bitcoin verification rehearsal.
6. Official archived release parser fixtures permanently marked non prospective.
7. Candidate governance, target, policy, validator, and manifest objects.
8. Independent verification tooling required for Genesis readiness.

## Prohibited work

1. Genuine prospective forecast issuance.
2. Forecast Ledger Genesis creation.
3. Production model or LLM forecast execution.
4. Generating forecast values to choose or reject Genesis targets.
5. Treating rehearsal artifacts as native prospective evidence.
6. Uploading, reading, copying, referencing, or committing the owner private signing key.
7. Weakening receipt quorum because of provider outage.
8. Sending a Roughtime request without a separate task authorizing the exact request after entry criteria review.
9. Sending an RFC 3161 request without separate explicit authorization.
10. Treating public endpoint reachability as qualification.
11. Entering a paid provider contract for the current zero cost minimum profile without a separate governance decision.
12. Hosted API, frontend, persistent service, or production database work.

## Exit criteria

GEN_001 exits only when every required readiness item for the selected final Genesis profile is closed and final adversarial review contains no blocking finding.

Completion of GEN_001 authorizes only a separate Genesis acceptance decision. It does not create Forecast Ledger Genesis or authorize a genuine prospective forecast.
