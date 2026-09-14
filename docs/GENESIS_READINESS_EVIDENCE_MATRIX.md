# GEN_001 Readiness Evidence Matrix

Date: 2026-09-14
Status: ACTIVE REVIEW CONTROL
Profile: ARCHITECTURE_COMPRESSION_P5

## Purpose

This matrix is the authoritative GEN_001 readiness checklist. Closure requires retained content-addressed evidence where applicable and the exact versioned validator semantics. Narrative confidence does not close an item.

## Status values

`CLOSED_DESIGN`, `CLOSED_REPOSITORY`, `OWNER_ACTION_REQUIRED`, `EXTERNAL_EVIDENCE_REQUIRED`, `FINAL_FREEZE_REQUIRED`, `PRODUCTION_QUALIFICATION_REQUIRED`, `RETIRED_FROM_GENESIS_V1`.

## Architecture Compression alignment

```text
P1 Genesis anchoring reconciliation = IMPLEMENTED_IN_SUCCESSOR_CANDIDATE_AND_VALIDATOR
P2 temporal claim separation = IMPLEMENTED_IN_VERSIONED_CLAIM_VALIDATOR
P3 dependency/review/evaluation compression = IMPLEMENTED_IN_CANDIDATE_V0_6
P4 provider-qualification firewall = IMPLEMENTED_AS_VERSIONED_SUPPORTING_BOUNDARY
current effective candidate = v0.6
current effective object count = 21
Genesis ready = NO
```

Historical v0.2 through v0.5 candidate semantics remain unchanged.

## Evidence matrix

| ID | Readiness item | Current status | Required closing evidence |
| --- | --- | --- | --- |
| GR001 | Trust Core normative contract | CLOSED_REPOSITORY | Historical FTC_001 plus Architecture Compression successor contracts |
| GR002 | Trust Core synthetic adversarial execution | CLOSED_REPOSITORY | Historical ADV suite retained; P6 reruns consolidated suite |
| GR003 | Separated time/durability claims | CLOSED_REPOSITORY | P2 claim vector implemented with VERIFIED/FAILED/UNRESOLVED/NOT_APPLICABLE |
| GR004 | Deadline receipt quorum rule | CLOSED_REPOSITORY | `policy:deadline-receipt-quorum:v3`; two-of-three, outage never lowers threshold |
| GR005 | Roughtime provider: roughtime.se | PRODUCTION_QUALIFICATION_REQUIRED | Frozen criteria, complete evidence package, review, decision, sealed ProviderProfile |
| GR006 | Roughtime provider: time.txryan.com | PRODUCTION_QUALIFICATION_REQUIRED | Same standard as GR005 |
| GR007 | Roughtime provider: TimeNL-Roughtime | PRODUCTION_QUALIFICATION_REQUIRED | Same standard plus frozen pilot requirements |
| GR008 | OpenTimestamps non-forecast rehearsal | OWNER_ACTION_REQUIRED | Stamp/proof bytes and retained command/verifier identity |
| GR009 | Strong Bitcoin verification | OWNER_ACTION_REQUIRED | Owner-controlled Bitcoin Core verification record |
| GR010 | Bootstrap governance contract | CLOSED_DESIGN | Out-of-graph BootstrapGovernanceRoot and successor acceptance semantics |
| GR011 | Owner Ed25519 bootstrap public key | OWNER_ACTION_REQUIRED | Public key only; private key remains outside project systems |
| GR012 | Initial target selection policy | CLOSED_DESIGN | Three selected low-frequency reconstructable targets |
| GR013 | Initial TargetDefinition objects | CLOSED_REPOSITORY | Three sealed target candidates |
| GR014 | Initial ResolutionRule objects | CLOSED_REPOSITORY | Three sealed rules |
| GR015 | BLS/BEA SourceContracts | CLOSED_REPOSITORY | Six sealed source candidates |
| GR016 | Semantic target parser | CLOSED_REPOSITORY | Fail-closed parser tests |
| GR017 | Real official archive fixture: CPI | EXTERNAL_EVIDENCE_REQUIRED | Retained official first-release bytes and parser report |
| GR018 | Real official archive fixture: U-3 | EXTERNAL_EVIDENCE_REQUIRED | Retained official first-release bytes and parser report |
| GR019 | Real official archive fixture: GDP Advance | EXTERNAL_EVIDENCE_REQUIRED | Retained official first-release bytes and parser report |
| GR020 | Issuance schedule policy | CLOSED_REPOSITORY | One cycle per release; deterministic mandatory slot universe |
| GR021 | Initial method set | CLOSED_REPOSITORY | Only `method:last-observed-value:v1`; deterministic replay; randomness NONE |
| GR022 | Point-in-time method evidence | CLOSED_REPOSITORY | First-release-only input and revised-database fallback prohibition |
| GR023 | Evaluation policy | CLOSED_REPOSITORY | `policy:genesis-evaluation:v2`; outcome, forecast, absolute error, squared error, full denominators |
| GR024 | Retry policy | CLOSED_REPOSITORY | Max attempts, eligible technical failures, first-success rule |
| GR025 | Omission policy | CLOSED_REPOSITORY | Explicit reasons and mandatory-instance visibility |
| GR026 | Correction policy | CLOSED_REPOSITORY | Immutable original plus versioned replacement semantics |
| GR027 | Retention policy | CLOSED_REPOSITORY | Indefinite content-addressed critical retention and owner-controlled backup |
| GR028 | Scientific Human Review policy | RETIRED_FROM_GENESIS_V1 | v0.6 exact-hash retirement; ambiguity becomes REVIEW_REQUIRED/UNRESOLVED without value selection |
| GR029 | Genesis acceptance policy | CLOSED_REPOSITORY | `policy:genesis-acceptance:v2`; final evidence subject is signed ManifestAcceptance and supplied separately to final validation |
| GR030 | Candidate object dependency closure | CLOSED_REPOSITORY | v0.6 lineage, 21 objects, exact predecessor retirement hashes, new objects sealed |
| GR031 | Exact final Genesis validator binding | FINAL_FREEZE_REQUIRED | Exact source/artifact hash including Architecture Compression v1 validator and tests |
| GR032 | Final BootstrapGovernanceRoot | FINAL_FREEZE_REQUIRED | GR011 public key plus exact acceptance rule and canonical object |
| GR033 | Final Roughtime ProviderProfiles and decisions | FINAL_FREEZE_REQUIRED | GR005 through GR007 closed, three exact profiles, three matching signed decisions |
| GR034 | Qualification verifier contract | FINAL_FREEZE_REQUIRED | Exact verifier contract for static decision validation and dynamic historical state recomputation |
| GR035 | Provider qualification-state package boundary | FINAL_FREEZE_REQUIRED | Content-closed record root/package collector, no caller-selected event subset, exact as-of reconstruction |
| GR036 | Final OTS Bitcoin verifier profile | FINAL_FREEZE_REQUIRED | GR008/GR009 evidence and exact verifier contract |
| GR037 | Candidate Genesis TrustedManifest | FINAL_FREEZE_REQUIRED | Exact refs to 21 candidate objects where applicable plus provider profiles, decisions, quorum and validator contracts |
| GR038 | ManifestAcceptance signature | FINAL_FREEZE_REQUIRED | Owner signature over exact candidate manifest; no post-signature final-evidence self-reference |
| GR039 | Final ManifestAcceptance external existence evidence | FINAL_FREEZE_REQUIRED | Exact signed ManifestAcceptance subject gets `EXTERNAL_EXISTENCE_BOUND_VERIFIED = VERIFIED` |
| GR040 | Final ManifestAcceptance Bitcoin durability | FINAL_FREEZE_REQUIRED | Exact signed ManifestAcceptance gets `BITCOIN_DURABILITY_VERIFIED = VERIFIED` |
| GR041 | Independent final Genesis validation | FINAL_FREEZE_REQUIRED | Separate final evidence input binds exact acceptance; no blocking finding |
| GR042 | Final readiness adversarial review | FINAL_FREEZE_REQUIRED | P1-P4 attack surfaces and P5 implementation reviewed with no blocker |
| GR043 | Genesis authorization | OUTSIDE GEN_001 | Separate explicit owner authorization only after all required readiness closure |

## Provider admission rule

For every consequential Genesis v1 deadline event, the qualification supporting subsystem reconstructs each admitted provider at:

```text
as_of_utc = frozen_deadline_utc
```

All three manifest-admitted providers must derive to `PRODUCTION_QUALIFIED` before the event may use the frozen three-provider production pool. Receipt quorum then remains at least two independently qualifying receipts from those three.

A provider outage never lowers the receipt threshold. An expired, blocked, or requalification-required provider blocks the stronger admitted-pool claim for a new event.

The historical state basis must be content-closed. Caller-selected metadata-review or requalification-event subsets are insufficient.

## P2 temporal claim rule

A timely wall-clock existence proof remains a verified historical fact even if Bitcoin durability is pending or later completes too late for pre-outcome eligibility.

The matrix tracks separately:

```text
EXTERNAL_EXISTENCE_BOUND_VERIFIED
DEADLINE_EXISTENCE_VERIFIED
BITCOIN_DURABILITY_VERIFIED
PRE_OUTCOME_DURABILITY_VERIFIED
CONFIRMATORY_PROSPECTIVE_ELIGIBLE
```

For final Genesis governance acceptance, pre-outcome durability and scientific prospective eligibility are `NOT_APPLICABLE`; final validation requires verified external existence and verified Bitcoin durability over the exact signed ManifestAcceptance.

## Fail-closed rule

Every selected required readiness item must close before GEN_001 can exit. Architecture Compression does not promote any rehearsal result, lower provider qualification criteria, authorize network traffic, or create Genesis.

## Safety state

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
production forecasting = PROHIBITED
network_authorized = false
```
