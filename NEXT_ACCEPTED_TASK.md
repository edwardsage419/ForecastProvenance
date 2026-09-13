# Next Accepted Task

Task ID: GEN_001
State: ROUGHTIME PRODUCTION QUALIFICATION GOVERNANCE PREPARATION; NETWORK REQUEST NOT AUTHORIZED

## Objective

Resolve and freeze the remaining Roughtime production qualification policy choices, implement production qualification schemas, evaluate retained rehearsal evidence under the frozen criteria, and complete an offline regression and adversarial review. This task is preparation for a later independent qualification review; it is not production qualification execution.

## Frozen design retained

```text
FPP_TIME_EVIDENCE_V1
policy:deadline-receipt-quorum:v3
FPP_ROUGHTIME_NONCE_V2
candidate lineage v0.2 + v0.3 + v0.4 + v0.5
provider pool = roughtime.se, time.txryan.com, TimeNL-Roughtime
packet profile = STANDARD_1024_BODY
transport profile = UDP_ONLY
quorum = 2-of-3
```

Cloudflare-Roughtime-2 remains historical only.

## Current state

The vendored Go 1.27 verifier qualification, execution orchestrator, separately authorized non-forecast rehearsal, and independent evidence review are complete. The retained rehearsal produced three qualifying provider results and remains permanently `NON_FORECAST_REHEARSAL` with `prospective_eligible=false`.

```text
REHEARSAL_VERIFIED = YES
REHEARSAL_EVIDENCE_REVIEW = PASS
PRODUCTION_QUALIFICATION_CRITERIA = BLOCKED
PRODUCTION_QUALIFICATION_EXECUTION = NOT_READY
```

D026 reconciles the current v3 quorum with the historical D015 and D024 text while preserving D025's readiness-matrix authority. The dated production qualification criteria document remains `DRAFT / NOT YET FROZEN / NOT A QUALIFICATION DECISION`.

The multi-leaf Merkle fixture task is complete. Effective deterministic offline coverage exists for typed hash-first, typed node-first, untyped draft-12 node-first, and negative wrong-order rejection. Each positive ordering fixture demonstrates a PATH of exactly 1 hash / 32 bytes. The Merkle fixture engineering gap is closed without changing the frozen provider semantics.

## Next accepted execution

1. Review the reconciled governance documents and the dated qualification criteria draft.
2. Resolve the explicitly marked policy decisions, including TimeNL pilot admissibility and freshness/repeatability parameters.
3. Freeze the accepted criteria through a separate versioned governance decision; do not infer acceptance from this draft.
4. Add separately reviewed schemas for production ProviderProfile, qualification decision/state, and the complete evidence manifest.
5. Evaluate existing retained rehearsal evidence against the frozen criteria without changing its historical classification.
6. Run the vendored verifier qualification, focused Roughtime tests, schema tests, complete repository suite, compile check, and offline adversarial review.
7. Report readiness for a later independent production qualification review. Do not execute that qualification in this task.

No provider packet is authorized by this task.

## Later network boundary

No additional live event is authorized or currently necessary. The remaining governance and schema gaps are offline gaps. If frozen criteria later require a repeatability event, it must receive a new separate exact authorization and remain non-prospective unless a future accepted governance state explicitly provides otherwise.

The offline plan remains `network_authorized=false`.

## Safety state

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
Roughtime provider requests sent by this work = 0
RFC3161 requests sent by this work = 0
network_authorized = false
```
