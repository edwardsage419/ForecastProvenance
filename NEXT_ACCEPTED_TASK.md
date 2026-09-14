# Next Accepted Task

Task ID: GEN_001-AC-P4
State: PRE_GENESIS ARCHITECTURE COMPRESSION; P4 PROVIDER-QUALIFICATION COMPLEXITY FIREWALL; NETWORK REQUEST NOT AUTHORIZED

## Objective

Establish a strict boundary between Forecast Trust Core and the provider-qualification supporting subsystem so Genesis v1 consumes only the minimum frozen qualification outputs required to validate deadline evidence.

P4 is a design and dependency-reconciliation task. It does not execute production qualification, change the frozen production qualification criteria, request live provider evidence, or qualify any provider.

Candidate objects, schemas, validator implementation, readiness matrix, abort conditions, and full tests are updated together later in P5.

## P1 through P3 boundary already established

P1 design control:

`docs/GEN_001_GENESIS_ANCHORING_RECONCILIATION_V1.md`

P2 design control:

`docs/GEN_001_TEMPORAL_CLAIM_SEPARATION_V1.md`

P3 design control:

`docs/GEN_001_GENESIS_V1_DEPENDENCY_COMPRESSION_V1.md`

P4 must preserve all accepted P1 through P3 properties.

## Retained qualification state

```text
PRODUCTION_QUALIFICATION_CRITERIA = FROZEN_V1
criteria_id = FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1
criteria_sha256 = 88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
PRODUCTION_QUALIFICATION_EXECUTION = NOT_READY
ACTIVE_MAINLINE = PAUSED
```

The completed provider exercise remains permanently:

```text
classification = NON_FORECAST_REHEARSAL
prospective_eligible = false
```

P4 cannot promote it or use it as an authorization for another request.

## Firewall design target

Forecast Trust Core should consume a small content-addressed qualification boundary rather than the full qualification workflow.

The expected minimum consumed interface is approximately:

```text
ProviderProfile exact full reference
QualificationDecision exact full reference
qualification criteria ID and version/hash
qualification evidence package or manifest full hash
qualification state required by the active deadline-receipt policy
```

The exact P4 record must determine which of these are mandatory and whether any can be transitively bound by another object without loss of independent verification.

## Supporting-subsystem internals

The following are presumptively outside the Forecast Trust Core dependency graph unless P4 finds a specific security property that requires direct consumption:

```text
provider discovery workflow
metadata collection workflow
network transport diagnostics
rehearsal orchestration
qualification execution orchestration
review workflow mechanics
individual raw evidence-file enumeration in the TrustedManifest
requalification scheduling machinery
operator research notes
provider continuity monitoring implementation
build and packaging workflow internals beyond frozen verifier identity
```

These materials remain retained where required for independent qualification verification. Exclusion from the Trust Core graph does not authorize deletion or weaken the frozen qualification criteria.

## Accepted P4 execution

1. Inventory every current provider-qualification object, schema, validator, readiness item, candidate dependency, and report that could leak qualification subsystem complexity into Genesis Trust Core.
2. Identify the exact security properties Forecast Trust Core needs from a provider qualification result.
3. Define the smallest frozen qualification output interface that preserves those properties.
4. Determine whether `ProviderProfile`, `QualificationDecision`, criteria identity, and evidence-package hash provide sufficient transitive binding.
5. Identify which qualification internals remain supporting evidence and which must be directly referenced by a final provider profile or qualification decision.
6. Ensure the active deadline receipt validator can determine whether a receipt provider was admitted at the historical cycle without re-running governance research or provider discovery.
7. Preserve exact provider key, protocol/wire profile, endpoint or identity rules, operational authority, and independence assumptions required by the active quorum policy.
8. Preserve fail-closed handling of stale, revoked, superseded, requalified, or mismatched provider state.
9. Prevent future qualification feature growth from automatically expanding the Forecast Trust Core manifest schema.
10. Identify every P5 object, schema, validator, readiness, abort-condition, and test change required to implement the firewall.
11. Keep all work offline.

## Required security properties

The firewall must preserve at least:

1. exact provider identity and cryptographic root binding;
2. exact protocol and wire-profile identity where required by receipt verification;
3. exact qualification criteria identity and version;
4. explicit qualification decision under the accepted authority model;
5. content identity of the retained evidence package sufficient to independently verify that decision;
6. provider-group independence classification required by the two-of-three quorum;
7. key rotation and standards-transition fail-closed behavior;
8. historical provider state selection by exact content identity rather than current provider metadata;
9. no automatic promotion of rehearsal evidence into production qualification;
10. no lowering of the frozen qualification standard to simplify Genesis.

## Complexity firewall rule

A new provider-qualification feature should change Forecast Trust Core only when the core needs a new security fact that cannot be represented by the existing frozen qualification output interface.

Changes to evidence collection, diagnostics, research workflow, operator review notes, or qualification automation should remain inside the qualification subsystem when the final frozen outputs are unchanged.

This rule is intended to prevent the provider qualification subsystem from becoming a second governance platform inside the Forecast Trust Core.

## P4 out of scope

P4 does not:

1. select a new provider;
2. remove or weaken the frozen two-of-three quorum;
3. change `FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1`;
4. execute live repeatability;
5. make a QualificationDecision;
6. seal a production ProviderProfile;
7. reopen Roughtime wire or verifier engineering absent a concrete correctness/security defect;
8. reopen RFC3161 engineering;
9. modify P1 anchoring, P2 temporal claims, or P3 dependency/evaluation decisions;
10. authorize Genesis or prospective forecasting.

## P5 handoff requirement

P4 must end with an explicit implementation map for P5 covering at least:

```text
TrustedManifest provider references
ProviderProfile schema/profile boundary
QualificationDecision references
qualification evidence package binding
historical provider-state selection
receipt validator admission checks
readiness matrix entries
abort conditions
tests for stale/mismatched/unqualified providers
```

P5 then implements P1 through P4 together as one versioned compressed Genesis candidate rather than incrementally mutating historical candidate semantics.

## Network boundary

```text
network_authorized = false
Roughtime provider requests authorized by this task = 0
RFC3161 requests authorized by this task = 0
production qualification requests authorized by this task = 0
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

The Genesis Ed25519 private key must not be accessed, read, copied, displayed, uploaded, transmitted, logged, referenced, or processed. Only the public key may enter project objects at a later separately authorized governance step.
