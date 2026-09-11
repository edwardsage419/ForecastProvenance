# Next Accepted Task

Task ID: GEN_001
State: ROUGHTIME REHEARSAL ENTRY READY, NETWORK REQUEST NOT AUTHORIZED

## Objective

Complete Genesis readiness without creating Forecast Ledger history, issuing genuine forecasts, or introducing a recurring paid service dependency.

## Repository work already delivered

1. `FPP_TIME_EVIDENCE_V1` separates signed wall clock deadline evidence from Bitcoin durability evidence.
2. The current deadline quorum candidate is `policy:deadline-receipt-quorum:v2`.
3. Version 2 uses an exactly three frozen independent Roughtime provider pool with a two receipt threshold.
4. RFC 3161 is optional auxiliary evidence for the current minimum profile.
5. Candidate object lineage is append only: v0.2 base, v0.3 predecessor patch, and v0.4 current patch.
6. The effective candidate contains 22 sealed objects.
7. Roughtime provider entry review is closed in `docs/GEN_001_ROUGHTIME_REHEARSAL_ENTRY_REVIEW_2026_09_11.md`.
8. The common rehearsal verifier candidate is `github.com/tannerryan/roughtime` at commit `56b346a16cd7e8317bb0d24f1ec15549cf93a4c9`.
9. No Roughtime request has been sent.

## Frozen rehearsal entry pool

```text
roughtime.se
endpoint = roughtime.se:2002/udp
protocol = draft-ietf-ntp-roughtime-15
root key = S3AzfZJ5CjSdkJ21ZJGbxqdYP/SoE8fXKY0+aicsehI=
status = READY FOR NON_FORECAST_REHEARSAL

time.txryan.com
endpoint = time.txryan.com:2002/udp
protocol = draft-ietf-ntp-roughtime-19
root key = iBVjxg/1j7y1+kQUTBYdTabxCppesU/07D4PMDJk2WA=
status = READY FOR NON_FORECAST_REHEARSAL

Cloudflare-Roughtime-2
endpoint = roughtime.cloudflare.com:2003/udp
protocol = draft-ietf-ntp-roughtime-08
root key = 0GD7c3yP8xEc4Zl2zeuN2SlLvDVVocjsPSL8/Rl/7zg=
status = READY FOR NON_FORECAST_REHEARSAL
```

Entry readiness does not authorize a request.

## Required next closure

The next accepted work is offline rehearsal tooling and exact network authorization preparation.

Allowed without another network authorization:

1. Freeze local build instructions for the pinned verifier commit.
2. Add offline parser and verifier fixtures that issue no network request.
3. Define the exact subject bound nonce derivation and retained evidence package.
4. Define maximum attempts, timeout behavior, request order, and fail closed error codes.
5. Prepare a single exact synthetic rehearsal command or script that remains disabled by default and cannot run without explicit operator authorization.

Before any actual UDP request, a separate task must explicitly authorize:

```text
synthetic_subject_bytes
synthetic_subject_sha256
exact three provider set
draft 15 for roughtime.se
draft 19 for time.txryan.com
draft 08 for Cloudflare-Roughtime-2
verifier commit 56b346a16cd7e8317bb0d24f1ec15549cf93a4c9
attempt limits
timeouts
request order
evidence output directory
NON_FORECAST_REHEARSAL classification
prospective_eligible=false
```

## Provider qualification rules

1. `REHEARSAL_AUTHORIZATION != GENESIS_AUTHORIZATION`.
2. `READY FOR NON_FORECAST_REHEARSAL != REHEARSAL_VERIFIED`.
3. `REHEARSAL_VERIFIED != PRODUCTION_QUALIFIED`.
4. A successful rehearsal never creates prospective evidence or Forecast Ledger history.
5. The Roughtime deadline upper bound is `midpoint + radius`.
6. At least two receipts must independently satisfy the frozen deadline.
7. Provider outage never lowers the required threshold.
8. Unlisted providers cannot be substituted after observing failures.
9. Provider key rotation requires a new ProviderProfile and accepted manifest change before the new key can qualify.
10. Final provider groups are defined by independent operational trust authority.
11. No paid commercial provider is required by the selected minimum profile.
12. RFC 3161 cannot substitute for the required Roughtime threshold under version 2.

## Other owner controlled closure

After Roughtime rehearsal authorization and execution, GEN_001 still requires:

1. Independent review of all three rehearsal evidence packages.
2. Owner generated Ed25519 public key only. The private key remains outside repository and connected systems.
3. Non forecast OpenTimestamps stamp, proof upgrade, and strong Bitcoin Core verification.
4. Retrieval and retention of the three selected retrospective official BLS and BEA raw source fixtures.
5. Source adapter reports, final readiness tests, exact ValidatorContract, final ProviderProfiles, BootstrapGovernanceRoot, OTS verifier profile, TrustedManifest, ManifestAcceptance inputs, and final adversarial review.

## Prohibited work

1. Genuine prospective forecast issuance.
2. Forecast Ledger Genesis creation.
3. Production model or LLM forecast execution.
4. Generating forecast values to choose or reject Genesis targets.
5. Treating rehearsal artifacts as native prospective evidence.
6. Uploading, reading, copying, referencing, or committing the owner private signing key.
7. Weakening receipt quorum because of provider outage.
8. Sending any Roughtime request without a separate explicit authorization containing the exact fields above.
9. Sending an RFC 3161 request without separate explicit authorization.
10. Treating public endpoint reachability as qualification.
11. Entering a paid provider contract for the current zero cost minimum profile without a separate governance decision.
12. Hosted API, frontend, persistent service, or production database work.

## Safety state

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
```

Completion of this task does not create Genesis and does not authorize a genuine prospective forecast.
