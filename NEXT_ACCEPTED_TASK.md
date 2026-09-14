# Next Accepted Task

Task ID: GEN_001-AC-P2
State: PRE_GENESIS ARCHITECTURE COMPRESSION; P2 TEMPORAL CLAIM SEPARATION; NETWORK REQUEST NOT AUTHORIZED

## Objective

Separate wall-clock existence, public durability, pre-outcome durability, and derived confirmatory prospective eligibility into explicit claims whose truth values can be independently validated and preserved.

P2 is a design and dependency-reconciliation task. Candidate objects, schemas, validator implementation, readiness matrix, abort conditions, and full tests are updated together later in P5.

## P1 boundary already established

P1 design control is recorded in:

`docs/GEN_001_GENESIS_ANCHORING_RECONCILIATION_V1.md`

The successor Genesis governance commitment chain is:

```text
BootstrapGovernanceRoot
→ TrustedManifest
→ Validation Reports
→ owner-signed ManifestAcceptance
→ one final external time/durability evidence package
→ independent final validation
→ separate explicit Genesis authorization
```

Standalone bootstrap and manifest anchoring are optional audit evidence in the successor design. The current v0.5 candidate and validator remain unaligned until P5 performs explicit versioned implementation.

## P2 design target

Review and define at least these independent outputs:

```text
DEADLINE_EXISTENCE_VERIFIED
BITCOIN_DURABILITY_VERIFIED
PRE_OUTCOME_DURABILITY_VERIFIED
CONFIRMATORY_PROSPECTIVE_ELIGIBLE
```

The design must prevent a late durability completion from erasing a valid earlier existence fact.

A record may therefore have:

```text
DEADLINE_EXISTENCE_VERIFIED = YES
BITCOIN_DURABILITY_VERIFIED = YES
PRE_OUTCOME_DURABILITY_VERIFIED = NO
CONFIRMATORY_PROSPECTIVE_ELIGIBLE = NO
```

when the exact subject received valid deadline-existence evidence in time and durable anchoring completed only after the applicable outcome information barrier.

## Accepted P2 execution

1. Locate every current field, policy, validator result, readiness statement, abort condition, and evaluation rule that collapses wall-clock evidence, Bitcoin durability, pre-outcome completion, or prospective eligibility into one status.
2. Identify each exact subject to which the claim applies, including Genesis acceptance evidence and forecast-cycle evidence where their semantics differ.
3. Define deterministic derivation rules for each retained claim.
4. State which evidence proves each claim and which trust assumptions remain external.
5. Preserve the distinction between Roughtime wall-clock trust and Bitcoin durability.
6. Keep Bitcoin block header time outside the precise civil-time upper-bound role.
7. Preserve historical facts when a stronger derived claim fails.
8. Identify the exact P5 object, schema, validator, readiness, abort-condition, and test changes required to implement the design.
9. Keep all work offline.

## Required P2 properties

The P2 candidate must preserve these properties:

1. wall-clock deadline existence is determined from the applicable signed-receipt policy and exact subject binding;
2. Bitcoin durability is determined independently from the durable commitment and strong verification rule;
3. pre-outcome durability compares the validated durability-completion evidence against the frozen outcome information barrier using an admissible wall-clock claim rather than Bitcoin block time as a precise timestamp;
4. confirmatory prospective eligibility is derived from all required claims and other applicable Trust Core conditions;
5. a failure of a stronger claim never rewrites a previously established weaker fact;
6. missing evidence produces an explicit fail-closed or unresolved state rather than an inferred success;
7. provider and verifier trust assumptions remain disclosed;
8. historical candidate and rehearsal semantics remain unchanged.

## Out of scope for P2

P2 does not reopen provider selection, production qualification criteria, Roughtime transport or wire semantics, RFC3161 engineering, stochastic execution, randomness, `FittedState`, closed-model support, evaluation metric reduction, or product-layer functionality.

P3 will reduce unused Genesis dependencies and human-review/evaluation surface. P4 will establish the provider-qualification complexity firewall. P5 will perform the consolidated versioned implementation.

## Network boundary

```text
network_authorized = false
Roughtime provider requests authorized by this task = 0
RFC3161 requests authorized by this task = 0
```

No prior rehearsal or qualification authorization may be reused.

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

The Genesis Ed25519 private key must not be accessed, read, copied, displayed, uploaded, transmitted, logged, referenced, or processed. Only the public key may enter project objects at a later authorized governance step.
