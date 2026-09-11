# Next Accepted Task

Task ID: GEN_001
State: PRE-REHEARSAL TOOLING FREEZE REQUIRED, NETWORK REQUEST NOT AUTHORIZED

## Objective

Close the remaining offline Roughtime implementation gate without creating Forecast Ledger history, sending provider requests, or introducing a paid dependency.

## Repository work now targeted

The current candidate design is:

```text
FPP_TIME_EVIDENCE_V1
policy:deadline-receipt-quorum:v3
FPP_ROUGHTIME_NONCE_V2
candidate lineage v0.2 + v0.3 + v0.4 + v0.5
```

Current provider pool:

```text
roughtime.se
time.txryan.com
TimeNL-Roughtime
```

Cloudflare-Roughtime-2 is historical only.

## Next accepted work

Allowed now:

1. obtain the pinned `github.com/tannerryan/roughtime` source at tag `v1.27.0`, commit `56b346a16cd7e8317bb0d24f1ec15549cf93a4c9`;
2. freeze an exact Go 1.27.x toolchain and retain version/build metadata;
3. build a project-controlled strict low-level wrapper that:
   - uses the exact frozen provider wire profiles;
   - creates one exact request per provider;
   - uses `STANDARD_1024_BODY`;
   - uses UDP only for the current profile;
   - applies FPP_ROUGHTIME_NONCE_V2;
   - does not negotiate beyond the frozen wire profile;
   - does not use causal chaining;
   - makes at most two attempts with identical request bytes;
   - persists retry/backoff state across process invocations;
   - stops after the first properly signed verified response, including a cryptographically verified response that is project-nonqualifying;
   - retains all raw attempts;
4. create offline fixtures covering all three wire profiles and every fail-closed error class;
5. create a content-addressed verifier build profile binding source tree, exact Go toolchain, dependency graph, build command, strict-wrapper source and produced executable hashes;
6. define and retain a content-addressed persistent retry-state snapshot before plan construction, and a post-run retry-state snapshot after execution;
7. make the offline plan bind both `verifier_build_profile_sha256` and `retry_state_snapshot_sha256`;
8. require every qualifying receipt to bind a verification transcript hash and require raw request/response/nonce/profile replay through the pinned low-level verifier;
9. run the Python executable semantic validator against synthetic valid and adversarial evidence packages;
10. recheck provider endpoints, roots, operator evidence and standards-transition status immediately before any future rehearsal plan is authorized.

No provider packet is authorized by this task.

## Required exact rehearsal boundary

A later network task must separately supply and authorize:

```text
exact synthetic subject bytes and SHA256
exact frozen deadline
exact current three-provider pool
exact plan SHA256
exact authorization-record SHA256
pinned verifier commit
verifier_build_profile_sha256
retry_state_snapshot_sha256
frozen singleton offered version and wire/TYPE/SRV profiles
attempt limits
timeout/backoff behavior
persistent retry-state location
verification/execution transcript output locations
evidence output directory
classification = NON_FORECAST_REHEARSAL
prospective_eligible = false
```

The offline plan itself remains `network_authorized=false`.

Only a separate explicit authorization record may set `network_authorized=true` for one exact plan.

## Provider qualification rules

1. `PUBLIC_ENTRY_EVIDENCE_READY != NETWORK_AUTHORIZED`.
2. `REHEARSAL_AUTHORIZATION != GENESIS_AUTHORIZATION`.
3. `REHEARSAL_VERIFIED != GENESIS_PROVIDER_QUALIFIED`.
4. Every deadline event evaluates all three frozen providers; a provider under active protocol backoff is recorded as non-qualifying without a network attempt.
5. At least two independently valid receipts are required.
6. Provider outage never lowers quorum.
7. No provider may be substituted after observing failures.
8. Protocol, packet or transport fallback inside a deadline event is prohibited. A properly signed but project-nonqualifying response terminates retries and resets protocol backoff while remaining non-qualifying for quorum.
9. Provider root/endpoint/wire-profile changes require versioned review.
10. Final RFC or standards transition requires compatibility review before further qualification.
11. JSON Schema alone never establishes receipt or quorum validity; executable semantic validation is required.
12. Semantic validation alone never establishes cryptographic validity; raw evidence must replay under the pinned low-level verifier and exact content-addressed verifier build profile.
13. The exact pre-attempt retry-state snapshot is bound into the plan and authorization; the post-attempt state snapshot and execution transcript are retained in the report.
14. RFC3161 remains optional auxiliary evidence.

## Other remaining GEN_001 closure

After Roughtime tooling and separately authorized rehearsals:

1. freeze three final ProviderProfiles and final verifier profile;
2. obtain owner bootstrap Ed25519 public key only;
3. complete OTS stamp/upgrade/strong Bitcoin verification;
4. retrieve and validate the three retrospective official source fixtures;
5. run a clean final repository test suite;
6. build exact ValidatorContract;
7. freeze BootstrapGovernanceRoot and candidate TrustedManifest;
8. sign and externally evidence ManifestAcceptance;
9. complete final adversarial review;
10. require a separate explicit Genesis acceptance decision.

## Prohibited work

No prospective forecast, Forecast Ledger, Genesis, provider network request, RFC3161 POST, private signing key access, paid provider contract, hosted production service or quorum weakening is authorized.

## Safety state

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
```
