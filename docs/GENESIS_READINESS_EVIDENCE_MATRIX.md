# GEN_001 Readiness Evidence Matrix

Date: 2026-09-16
Status: ACTIVE REVIEW CONTROL
Profile: POST_P6_CORRECTNESS_REPAIR_PENDING_FRESH_REGRESSION

## Purpose

This matrix is the authoritative GEN_001 readiness checklist. Closure requires retained content-addressed evidence where applicable and the exact versioned validator semantics. Narrative confidence does not close an item.

The historical P6 exact-head PASS remains retained execution provenance. Post-P6 correctness findings required source/test repair, so that historical execution does not close regression requirements for the repaired tree.

## Status values

`CLOSED_DESIGN`, `CLOSED_REPOSITORY`, `OWNER_ACTION_REQUIRED`, `EXTERNAL_EVIDENCE_REQUIRED`, `FINAL_FREEZE_REQUIRED`, `PRODUCTION_QUALIFICATION_REQUIRED`, `REGRESSION_REQUIRED`, `DESIGN_REVIEW_REQUIRED`, `RETIRED_FROM_GENESIS_V1`.

## Architecture Compression alignment

```text
P1 Genesis anchoring reconciliation = IMPLEMENTED_IN_SUCCESSOR_CANDIDATE_AND_VALIDATOR
P2 temporal claim separation = IMPLEMENTED_REPAIR_PENDING_FRESH_REGRESSION
P3 dependency/review/evaluation compression = IMPLEMENTED_IN_CANDIDATE_V0_6
P4 provider-qualification firewall = IMPLEMENTED_AS_VERSIONED_SUPPORTING_BOUNDARY
P5 claim-authority hardening = POST_P6_REPAIR_PENDING_FRESH_REGRESSION
P6 historical exact-head execution = PASS_RETAINED_AS_HISTORY
P6 repaired-tree execution = REQUIRED_FROM_ZERO
P7 dependency reevaluation = PAUSED_PENDING_FRESH_P6
current effective candidate = v0.6
current effective object count = 21
Genesis ready = NO
```

Historical v0.2 through v0.5 candidate semantics remain unchanged. The post-P6 repair does not change candidate bytes or candidate lineage.

## Evidence matrix

| ID | Readiness item | Current status | Required closing evidence |
| --- | --- | --- | --- |
| GR001 | Trust Core normative contract | CLOSED_REPOSITORY | Historical FTC_001 plus Architecture Compression successor contracts |
| GR002 | Trust Core synthetic adversarial execution | REGRESSION_REQUIRED | Fresh complete adversarial and repository regression on one exact final repair HEAD; historical P6 PASS retained but cannot close the modified tree |
| GR003 | Separated time/durability claims and evidence authority | REGRESSION_REQUIRED | P2 claim vector plus exact evidence-object contract enforcement, authoritative evidence-to-claim recomputation, persisted-report equality and fresh exact-head P6 PASS |
| GR004 | Deadline receipt quorum rule | CLOSED_REPOSITORY | Current `policy:deadline-receipt-quorum:v3`; two-of-three threshold and outage never lowers threshold; P7_F1 execution-accounting disposition tracked separately in GR044 |
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
| GR031 | Exact final Genesis validator binding | FINAL_FREEZE_REQUIRED | Exact source/schema/artifact hashes including repaired claim-authority modules, production evidence contract module and final fresh P6 report |
| GR032 | Final BootstrapGovernanceRoot | FINAL_FREEZE_REQUIRED | GR011 public key plus exact acceptance rule and canonical object |
| GR033 | Final Roughtime ProviderProfiles and decisions | FINAL_FREEZE_REQUIRED | GR005 through GR007 closed, three exact profiles, three matching signed decisions, subject to P7 dependency decision |
| GR034 | Qualification verifier contract | FINAL_FREEZE_REQUIRED | Exact manifest-bound contract binding frozen criteria, main ValidatorContract, decision-signature projection, accepted bootstrap authority key hash, Ed25519 verifier build-profile hash and binary hash |
| GR035 | Provider qualification-state package boundary | FINAL_FREEZE_REQUIRED | Content-closed record root/package collector, exact three-provider input closure, no caller-selected event subset, exact as-of reconstruction |
| GR036 | Final strong Bitcoin verifier contract | FINAL_FREEZE_REQUIRED | GR008/GR009 evidence plus exact hash-pinned local verifier contract; persisted report is not authority |
| GR037 | Candidate Genesis TrustedManifest | FINAL_FREEZE_REQUIRED | Exact refs to 21 candidate objects where applicable plus all dependencies retained by the final post-P7 Genesis profile |
| GR038 | ManifestAcceptance signature | FINAL_FREEZE_REQUIRED | Owner signature over exact candidate manifest; no post-signature final-evidence self-reference |
| GR039 | Final ManifestAcceptance external existence evidence | FINAL_FREEZE_REQUIRED | Exact signed ManifestAcceptance subject gets authoritative recomputation under the final post-P7 temporal profile |
| GR040 | Final ManifestAcceptance Bitcoin durability | FINAL_FREEZE_REQUIRED | Exact signed ManifestAcceptance gets authoritative recomputation `BITCOIN_DURABILITY_VERIFIED = VERIFIED` from exact bundle/proof and strong verifier execution under the final post-P7 profile |
| GR041 | Independent final Genesis validation | FINAL_FREEZE_REQUIRED | Independently supplied BootstrapGovernanceRoot/public authority bytes, exact TrustedManifest authority refs, raw final evidence recomputation, persisted-report equality where applicable, no blocking finding |
| GR042 | Final readiness adversarial review | REGRESSION_REQUIRED | Post-P6 findings repaired, fresh full P6 passes on one exact final repair HEAD, P7_F1 resolved by versioned semantics, then final P1-P7 adversarial review closes with no blocker |
| GR043 | Genesis authorization | OUTSIDE GEN_001 | Separate explicit owner authorization only after all required readiness closure |
| GR044 | Production wall-clock complete provider execution accounting | DESIGN_REVIEW_REQUIRED | P7 must either preserve current v3 attempt-all-three semantics and bind a minimal authoritative production event accounting record, or adopt a successor versioned policy that explicitly changes the execution requirement; `NON_FORECAST_REHEARSAL` reports cannot substitute |

## Provider admission rule

For every consequential Genesis v1 deadline event under the current v0.6 profile, the qualification supporting subsystem reconstructs each admitted provider at:

```text
as_of_utc = frozen_deadline_utc
```

All three manifest-admitted providers must derive to `PRODUCTION_QUALIFIED` before the event may use the frozen three-provider production pool. Receipt quorum then remains at least two independently qualifying receipts from those three.

A provider outage never lowers the receipt threshold. An expired, blocked, or requalification-required provider blocks the stronger admitted-pool claim for a new event.

The historical state basis must be content-closed. Caller-selected metadata-review or requalification-event subsets are insufficient. Runtime provider-authority input keys must exactly equal the three admitted provider identities.

QualificationDecision signatures must be verified by the exact hash-pinned Ed25519 verifier described by the manifest-bound qualification verifier contract. Caller-supplied signature callbacks or authority substitutions are prohibited. The accepted authority public-key bytes are supplied independently from the BootstrapGovernanceRoot/governance context and must match the contract-bound hash.

Provider independence and common-dependency evidence belongs to the qualification evidence/review/decision authority chain. ProviderProfile remains the frozen operational and cryptographic identity object.

## Production execution-accounting rule

The current v3 policy also requires all three frozen providers to be evaluated in frozen order and attempted when retry-eligible. The repository rehearsal execution layer records complete ordered provider results, but rehearsal evidence is permanently non-production.

The current production wall-clock authority consumes exact qualifying receipt evidence and exact provider admission state. It does not yet bind a dedicated authoritative production event record proving complete attempt-all-three execution accounting. This is `P7_F1` and remains a readiness blocker until P7 supplies a versioned disposition.

A two-of-three receipt quorum alone must not be described as proving complete execution of all v3 required attempts.

## P2 temporal claim authority rule

A timely wall-clock existence proof remains a verified historical fact even if Bitcoin durability is pending or later completes too late for pre-outcome eligibility.

The matrix tracks separately:

```text
EXTERNAL_EXISTENCE_BOUND_VERIFIED
DEADLINE_EXISTENCE_VERIFIED
BITCOIN_DURABILITY_VERIFIED
PRE_OUTCOME_DURABILITY_VERIFIED
CONFIRMATORY_PROSPECTIVE_ELIGIBLE
```

A claim state is readiness-relevant only when reconstructed through the successor authoritative path from exact retained evidence under the exact TrustedManifest-bound validator/verifier contracts.

For production evidence objects consumed directly by the repaired authority path, an internally valid seal is insufficient. The exact normative object contract must pass first, including exact field set, schema/object identity, admissible origin class, `prospective_eligible` rule, required reference shapes, required cardinality and fixed verifier-contract values where applicable. Caller-supplied `VERIFIED` strings, schema-invalid sealed objects, persisted claims and report seals cannot substitute for recomputation.

Production readiness paths require operational evidence of the admitted origin class. Synthetic evidence may exercise tests but cannot close a production readiness item.

The current v0.6 final Genesis governance mapping continues to require verified external existence and Bitcoin durability for the exact signed ManifestAcceptance until P7 completes its dependency reevaluation. Pre-outcome durability and scientific prospective eligibility remain `NOT_APPLICABLE` for governance acceptance.

## Historical P6 and fresh regression rule

Historical P6 provenance remains:

```text
historical exact HEAD = 70dc89f187842d8dcc6ba428241aae614d520bd4
historical evidence manifest SHA256 = a330a3952b55ce0f4415f25c5580ad2cdf53c05801e78f728239ab73caa8bb5d
historical result = PASS
```

The post-P6 correctness repair changes source and tests after that execution. The repaired tree must therefore complete the full mandatory regression from zero on one exact final HEAD. Passing subsets from earlier repair commits cannot close GR002, GR003 or GR042.

## Fail-closed rule

Every selected required readiness item must close before GEN_001 can exit. Architecture Compression does not promote any rehearsal result, lower provider qualification criteria, authorize network traffic or create Genesis.

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
