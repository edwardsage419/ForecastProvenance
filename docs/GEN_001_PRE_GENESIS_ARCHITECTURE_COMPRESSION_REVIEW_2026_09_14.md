# GEN_001 Pre-Genesis Architecture Compression Review

Date: 2026-09-14
Classification: NON_NORMATIVE_PROJECT_CONTROL
Prospective eligible: false
Genesis effect: none
Network authorization: none
Transition basis commit: `b8356f70844034fa7c448be30f39312ef95907cc`

## Purpose

This record documents the project-control decision to move the active GEN_001 workstream from Roughtime production qualification governance to Pre-Genesis Architecture Compression.

It is intentionally non-normative. It does not amend candidate objects, schemas, validators, policies, qualification criteria, historical evidence, readiness results, prospective eligibility, or Genesis requirements. Where this record describes a future design direction, existing normative project artifacts continue to control until a later versioned change is accepted.

## Reason for the transition

The project has accumulated sufficient provider-qualification machinery to expose a larger architectural question: Genesis v1 should instantiate only the minimum mechanisms required to create a credible, independently verifiable prospective history.

The project value to preserve is the ability for a third party to verify:

1. which cycles and slots were mandatory;
2. which attempts, retries, failures, and omissions occurred;
3. which information was available before the applicable cutoff;
4. how an admitted method was executed;
5. how an outcome was resolved;
6. how the complete evaluation cohort was constructed;
7. which trust assumptions and external evidence support each temporal or durability claim.

Additional infrastructure has value only when it protects one of these properties or enables a real later capability at acceptable maintenance cost.

## Control decision

Effective from this record, the active repository workstream is:

```text
PRE_GENESIS_ARCHITECTURE_COMPRESSION
```

The former active workstream:

```text
ROUGHTIME_PRODUCTION_QUALIFICATION_GOVERNANCE
```

is paused as a mainline task.

Its frozen criteria, schemas, validators, retained evidence, qualification reviews, and historical rehearsal classifications remain preserved. They may be consumed later as a supporting subsystem. No provider becomes production qualified through this transition.

## Genesis v1 compression principles

The Genesis v1 design should be reduced to capabilities actually needed at first prospective operation:

1. a small set of low-frequency targets with reconstructable official schedules;
2. a deterministic issuance schedule and complete mandatory-cycle universe;
3. a deterministic or fully auditable initial method;
4. point-in-time source contracts;
5. complete attempt, retry, failure, and omission accounting;
6. immutable forecast, correction, resolution, and evaluation-cohort records;
7. external deadline-existence evidence;
8. durable public anchoring;
9. an exact validator contract;
10. an external bootstrap governance root, trusted manifest, and owner-signed manifest acceptance.

The first prospective history is intended to prove provenance and cohort integrity under real operation before broader forecasting capability is added.

## Deferred capabilities

The following capabilities are deferred from the Genesis v1 minimum profile unless a concrete dependency review shows that one is currently necessary:

1. custom transparency logging;
2. universal forecasting support;
3. closed nondeterministic model strong-confirmatory support;
4. unused stochastic execution and randomness workflows;
5. unused `FittedState` machinery;
6. complex DID, user PKI, or multi-party governance;
7. additional time protocols;
8. new RFC3161 engineering absent a correctness or security defect;
9. new recurring paid infrastructure.

Deferral does not delete future interfaces. A later successor manifest or versioned policy may add a capability without reinterpreting historical forecasts.

## Genesis anchoring design direction for P1

The current architecture contains an inconsistency between documents that require several independent anchoring stages and acceptance or readiness controls that do not express the same requirement uniformly.

P1 must resolve that inconsistency explicitly.

The candidate to review is:

```text
BootstrapGovernanceRoot
→ TrustedManifest
→ Validation Reports
→ owner-signed ManifestAcceptance
→ one final external time/durability evidence package
→ independent final validation
→ separate explicit Genesis authorization
```

Separate bootstrap and manifest anchors may be considered optional audit evidence if the final accepted construction preserves their required security properties. P0 does not make that change.

## Temporal and durability claim direction for P2

Temporal claims should be represented independently rather than collapsed into one binary prospective status.

At minimum, P2 should review explicit derivation of:

```text
DEADLINE_EXISTENCE_VERIFIED
BITCOIN_DURABILITY_VERIFIED
PRE_OUTCOME_DURABILITY_VERIFIED
CONFIRMATORY_PROSPECTIVE_ELIGIBLE
```

A record that obtained timely existence evidence and later obtained durability evidence after the required information barrier must retain the existence fact while failing the stronger pre-outcome durability or confirmatory eligibility claim as applicable.

Bitcoin durability strengthens resistance to historical rewriting. Bitcoin block time is not a substitute for a precise civil-time upper bound.

Wall-clock providers retain their own key, operator, and governance trust assumptions. Those assumptions must remain disclosed.

## Provider-qualification complexity firewall for P4

Provider qualification is to be maintained as a supporting subsystem.

The Forecast Trust Core should consume frozen outputs such as:

```text
ProviderProfile
QualificationDecision
qualification criteria version
qualification evidence package hash
```

The Trust Core should not absorb additional provider-governance machinery unless a concrete correctness or security dependency requires it.

Existing qualification criteria remain frozen historical project artifacts. This control decision neither weakens them nor declares any provider qualified.

## Evaluation direction for P3 and P5

Genesis v1 should prioritize cohort integrity over metric breadth.

The minimum scoring surface may be limited to:

```text
resolved outcome
forecast value
absolute error
squared error
```

The cohort must still retain complete denominators for expected, issued, failed, omitted, ineligible, unresolved, withdrawn, and any other required lifecycle status.

Multiple-method comparison, baseline deltas, complex aggregation, probabilistic scoring, calibration, and leaderboard semantics may be added when a real second method or forecast class creates a concrete need.

Any change to current normative evaluation semantics requires a versioned later phase. This record alone changes nothing.

## Ordered workstream

```text
P0  record this transition and synchronize project control documents
P1  reconcile Genesis anchoring semantics and design the final-acceptance candidate
P2  separate temporal and durability claims from derived prospective eligibility
P3  remove unused Genesis v1 dependencies and reduce human-review/evaluation surface
P4  establish the provider-qualification complexity firewall
P5  update candidate objects, schemas, validators, tests, readiness matrix, abort conditions, and adversarial review
P6  rerun complete offline regression and synthetic adversarial suite
P7  reconsider whether Roughtime production qualification is still required
P8  perform a separate final pre-Genesis high-level review
P9  require separate explicit Genesis authorization
```

P0 is complete when this record and the repository control documents consistently name Architecture Compression as the active workstream.

## Historical preservation

All existing historical records retain the classifications and meanings they had when created.

In particular:

```text
NON_FORECAST_REHEARSAL remains NON_FORECAST_REHEARSAL
prospective_eligible remains false for retained rehearsal evidence
production-qualified provider count remains 0
PRODUCTION_QUALIFIED remains NO
```

No prior candidate object, qualification result, rehearsal, resolution, evaluation, or governance record is silently edited or reinterpreted by this transition.

## Cost and operating constraints

The design must remain operable by a single owner.

The default dependency order remains local tools, open-source tools, Git/GitHub, existing ChatGPT/Codex access, and free public infrastructure. New recurring paid APIs, SaaS products, cloud databases, TSA services, certificates, or monitoring subscriptions require a separate cost and security review plus explicit approval before adoption.

## Safety boundary

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

No Roughtime or RFC3161 provider request is authorized by this record.

The Genesis Ed25519 private key is outside the permitted project-tooling boundary. It must not be accessed, read, copied, displayed, uploaded, transmitted, logged, referenced, or processed. Only the public key may enter project objects at a later authorized governance step.
