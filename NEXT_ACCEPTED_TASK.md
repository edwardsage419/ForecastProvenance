# Next Accepted Task

Task ID: GEN_001-AC-P1
State: PRE_GENESIS ARCHITECTURE COMPRESSION; P1 GENESIS ANCHORING SPECIFICATION RECONCILIATION; NETWORK REQUEST NOT AUTHORIZED

## Objective

Reconcile the Genesis anchoring requirements and produce a versioned candidate for a minimal final-acceptance anchoring chain.

P1 must identify every current normative and readiness-control statement that requires separate bootstrap, manifest, acceptance, or related anchoring; determine which requirements conflict or overlap; and propose one internally consistent candidate without silently reinterpreting historical documents.

## P0 boundary already established

The active project mainline is Pre-Genesis Architecture Compression.

Roughtime production qualification is paused as the active mainline. Existing qualification criteria and retained evidence remain unchanged supporting evidence.

P0 changed project control state only. It did not change candidate objects, schemas, validators, historical classifications, Genesis semantics, or prospective eligibility.

## P1 design target

Review this minimal commitment-chain candidate:

```text
BootstrapGovernanceRoot
→ TrustedManifest
→ Validation Reports
→ owner-signed ManifestAcceptance
→ one final external time/durability evidence package
→ independent final validation
→ separate explicit Genesis authorization
```

The review must determine whether separate bootstrap and manifest anchoring can be reduced from mandatory Genesis requirements to optional audit evidence while preserving the intended security properties.

The design must retain a clear distinction between signed wall-clock evidence and durable public anchoring. Bitcoin block timestamps must not be treated as precise civil-time upper bounds.

## Accepted P1 execution

1. Locate the exact normative Genesis anchoring procedure, acceptance-policy, readiness-matrix, validator-contract, and candidate-object requirements that currently govern bootstrap, manifest, validation reports, acceptance, and final external evidence.
2. Build a contradiction and redundancy table that identifies every requirement that must be reconciled.
3. State the security property provided by each retained anchoring step and the attack surface created by removing or weakening a step.
4. Draft the smallest internally consistent anchoring candidate that preserves independently verifiable precommitment and final acceptance.
5. Preserve existing historical candidate semantics. Any normative change must use a new versioned policy, patch, or successor object as appropriate.
6. Update documentation and tests only after the proposed semantics are explicit enough to validate deterministically.
7. Keep all work offline. Do not execute any provider request, production qualification event, Genesis acceptance, forecast issuance, or ledger creation.

## Required review constraints

The proposed P1 candidate must preserve at least these properties:

1. the trusted bootstrap authority is supplied outside the candidate manifest graph;
2. the owner signature binds the exact accepted manifest and required validation reports;
3. the final external evidence package binds the accepted object set without depending on mutable repository state;
4. independent final validation can reconstruct the exact acceptance basis;
5. no candidate object can select its own trust root;
6. no historical object is modified or reclassified;
7. Genesis remains subject to a separate explicit authorization after readiness closure.

## Out of scope for P1

P1 does not reopen production qualification criteria, provider selection, Roughtime transport semantics, RFC3161 engineering, stochastic execution, public randomness, `FittedState`, closed-model support, evaluation metrics, or product-layer functionality except where a direct anchoring dependency must be identified.

P2 and later phases will address temporal-claim separation, dependency reduction, qualification firewalling, candidate/schema/validator updates, and full offline regression.

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
