# GEN_001 Genesis v1 Dependency and Review Surface Reduction V1

Date: 2026-09-14
Status: ARCHITECTURE_COMPRESSION_P3_DESIGN_CONTROL
Classification: PRE_GENESIS_DESIGN
Prospective eligible: false
Genesis effect: none
Network authorization: none
Basis commit: `05a6ae57c1fb6d6dfe080e9924ab22a6c6188de0`

## Purpose

This record closes Architecture Compression P3 at the design level.

P3 reduces the instantiated Genesis v1 dependency graph to capabilities actually used by the initial deterministic method and target profile. It also reduces the human review and evaluation surface while preserving provenance, mandatory cycle accounting, point-in-time evidence, P2 temporal claims, immutable history, and complete cohort denominators.

Historical candidate objects, existing validators, historical reports, rehearsal evidence, and prior candidate semantics remain unchanged. P5 must implement this design through an explicit successor candidate patch and aligned schemas, validators, readiness controls, abort conditions, and tests.

## Current effective candidate inventory

The current effective v0.5 candidate contains 22 sealed normative objects:

```text
3 TargetDefinition
3 ResolutionRule
6 SourceContract
1 IssuanceSchedule PolicyDefinition
1 Evaluation PolicyDefinition
1 Deadline Receipt Quorum PolicyDefinition v3
1 ForecastMethod: method:last-observed-value:v1
1 Retry PolicyDefinition
1 Omission PolicyDefinition
1 Correction PolicyDefinition
1 Retention PolicyDefinition
1 Human Review PolicyDefinition
1 Acceptance PolicyDefinition
```

The current candidate already does not instantiate a `PublicRandomnessPolicy`, `FittedState`, stochastic method, closed model, external request-audit method, or model retrieval policy.

The current initial method is:

```text
method:last-observed-value:v1
selection_control_class = DETERMINISTIC_REPLAY
randomness_policy = NONE
```

It emits one deterministic point forecast from the immediately preceding admissible first-release official value.

## P3 governing principle

A generic Trust Core interface does not become a Genesis v1 dependency merely because the interface exists.

Genesis v1 instantiates only capabilities required by at least one admitted target, method, schedule, evidence path, resolution path, correction path, evaluation path, or governance path.

Dormant interfaces remain available for successor manifests. Their dormant existence does not create a readiness blocker and does not require a placeholder policy object.

## Dependency classification

### Required in Genesis v1

The compressed Genesis v1 profile still requires:

1. the three selected `TargetDefinition` objects;
2. the three selected `ResolutionRule` objects;
3. the six schedule and first-release `SourceContract` objects;
4. one deterministic `IssuanceSchedulePolicy`;
5. `method:last-observed-value:v1` as the only initial `ForecastMethod`;
6. one `RetryPolicy`;
7. one `OmissionPolicy`;
8. one `CorrectionPolicy`;
9. one `RetentionPolicy`;
10. one minimal `EvaluationPolicy`;
11. the active deadline receipt quorum policy;
12. the P1 successor `AcceptancePolicy`;
13. exact `ValidatorContract` binding;
14. P1 and P2 external-time and durability semantics;
15. `BootstrapGovernanceRoot`, `TrustedManifest`, and signed `ManifestAcceptance`;
16. complete attempt, failure, omission, correction, resolution, and cohort accounting.

### Dormant Trust Core interfaces

These interfaces remain available to future successor manifests but are not instantiated Genesis v1 dependencies:

```text
PublicRandomnessPolicy
FittedState
fitted TransformationDefinition state
POSTCOMMIT_PUBLIC_RANDOMNESS execution
EXTERNALLY_AUDITED_ATTEMPTS execution
closed-model observability classes
model TrustReport
consequential retrieval accounting for opaque models
probabilistic output contracts
multi-method comparison policy
```

No readiness item may require production evidence, fixtures, provider relationships, policy objects, or validators for one of these dormant capabilities before Genesis v1.

## Public randomness decision

`PublicRandomnessPolicy` is absent from the compressed Genesis v1 manifest because every admitted Genesis method declares `randomness_policy = NONE` and uses `DETERMINISTIC_REPLAY`.

The generic trusted-manifest interface may retain a `public_randomness_policies` collection. For Genesis v1 the collection is empty.

An empty collection is materially different from a placeholder randomness policy. A placeholder would create an unused normative dependency and an unnecessary future attack surface.

The generic `IssuanceCyclePlan` interface currently includes `public_randomness_policy_ref_or_none`. P5 must align the Genesis v1 plan profile so a deterministic-only cycle does not require a content reference to a nonexistent randomness policy. The successor representation may conditionally omit the field or use another canonical explicit not-applicable representation accepted by the frozen schema. JSON null must not be introduced if canonicalization continues to prohibit null.

The existing `RetryPolicy.randomness_progression_rule = NONE_FOR_INITIAL_METHOD` may remain as an explicit constant because it does not instantiate public randomness or an external dependency.

## Fitted state and transformation decision

The initial method performs no fitting. Genesis v1 therefore has:

```text
FittedState objects = 0
fitted transformation dependencies = 0
```

The generic `FittedState` and `TransformationDefinition` contracts remain available for later statistical methods.

A parser used to extract an official first-release scalar is an evidence-processing implementation and does not by itself require a fitted model-state object. Parser identity and exact source artifact binding remain required where they affect the forecast input or resolved outcome.

The compressed Genesis manifest may retain a generic `transformation_definitions` collection as an empty collection when no admitted method consumes a separate transformation object.

## Closed-model observability and retrieval decision

Genesis v1 admits no closed model and no method whose consequential external retrieval set is hidden or model-controlled.

Therefore the following generic paths are dormant for Genesis v1:

```text
PARTIAL_EXTERNAL observability
OPAQUE_INTERNAL observability
closed-model TrustReport validation
model retrieval completeness accounting
EXTERNALLY_AUDITED_ATTEMPTS
UNCONTROLLED_NONDETERMINISM exploratory handling
```

They remain Trust Core interfaces for later successor manifests. They do not create Genesis readiness items and need no Genesis fixtures beyond preserving generic unit coverage already present in the repository.

The initial deterministic method must still bind every consequential forecast input through point-in-time source evidence. Dormancy of closed-model observability does not weaken the SourceContract or information-cutoff requirements.

## Human review decision

The compressed Genesis v1 profile does not instantiate a Human Review Policy for scientific resolution.

The current effective candidate object:

```text
object_id = policy:genesis-human-review:v1
content_sha256 = 3205098b37d4eef44dfd1f327bae4d9fcdbf64fa87a939ac84c4200b8a3b8e19
```

is historical candidate material and remains immutable. P5 should retire it by exact predecessor hash in the successor candidate lineage.

Genesis v1 handles official-source ambiguity deterministically:

```text
unique admissible semantic match -> RESOLVED
material official conflict -> REVIEW_REQUIRED diagnostic state, not a resolved value
layout or semantic ambiguity -> REVIEW_REQUIRED or UNRESOLVED
insufficient admissible evidence by deadline -> UNRESOLVED
```

`REVIEW_REQUIRED` in Genesis v1 means owner attention is needed. It does not grant an authority to select an outcome value. A `ReviewDecision` cannot convert a Genesis v1 ambiguous or conflicting case into `RESOLVED` unless a future successor manifest explicitly introduces an admitted review rule for future records.

This removes an unnecessary subjective resolution path while preserving evidence of the ambiguity itself.

The generic Trust Core `ReviewRule` and `ReviewDecision` interfaces remain available for future protocols. They are not Genesis v1 blockers.

## Human review security effect

Removing the instantiated Genesis review policy narrows attack surface in four ways:

1. there is no authority path that can select among conflicting official values;
2. there is no semantic-equivalence override for a changed official layout during Genesis v1;
3. there is no need to maintain reviewer identity or reviewer-authority governance for scientific resolution;
4. a parser or source-contract ambiguity remains visibly unresolved instead of being converted into a favorable value.

The cost is reduced operational flexibility. An official layout change may create more unresolved records until a successor manifest is accepted. For Genesis v1 this is acceptable because provenance integrity has priority over continuity of scoring.

## Evaluation compression decision

The current EvaluationPolicy treats `method:last-observed-value:v1` as a comparison baseline while that exact method is also the only admitted Genesis forecasting method.

That creates a tautological comparison:

```text
method forecast == baseline forecast
absolute_error_delta == 0
squared_error_delta == 0
```

The comparison conveys no information during a one-method Genesis.

P3 therefore removes baseline comparison from the compressed Genesis v1 normative evaluation surface.

The current historical candidate object remains unchanged:

```text
object_id = policy:genesis-evaluation:v1
content_sha256 = 37743b52bd8a38ea7ae1fe5a4ef230c07797deb05030c5bf0fcfe7a998dc3d3e
```

P5 should retire it by exact predecessor hash and add a successor evaluation policy with a new semantic ID and sealed content hash.

## Minimal Genesis v1 scoring surface

For an issued forecast that is confirmatory-prospectively eligible and whose target resolves under the frozen rule, the minimal normative numerical evaluation contains only:

```text
resolved_outcome
forecast_value
absolute_error
squared_error
```

The arithmetic contract remains exact decimal and versioned.

Genesis v1 does not require normative:

```text
absolute_error_delta_vs_baseline
squared_error_delta_vs_baseline
mean_absolute_error
root_mean_squared_error
mean_absolute_error_delta_vs_baseline
mean_squared_error_delta_vs_baseline
pairwise method comparison
cross-target aggregate score
statistical significance claim
leaderboard
calibration metric
```

Those capabilities may be added when a genuinely distinct second method or forecast class exists.

## Cohort integrity remains mandatory

Evaluation compression does not reduce denominator accounting.

Every expected slot remains represented in the cohort accounting, including at least:

```text
expected
issued
failed
omitted
ineligible
unresolved
withdrawn
```

The implementation may additionally expose `prospective_eligible`, `resolved`, and `scorable` counts when they are deterministic derived subsets.

P2 temporal claim states must remain inspectable for each applicable cycle or issued record. Evaluation reporting must not collapse an existence, durability, or pre-outcome-durability failure into an unexplained generic omission.

A record contributes numerical error metrics only when the active evaluation policy says it is scorable. Missing or failed stronger trust claims remain visible in the denominator even when no numerical score is produced.

## Aggregation decision

No aggregate predictive-skill statistic is required in the Genesis v1 Trust Core.

Raw immutable per-forecast results and complete denominators are sufficient to build elapsed prospective history. Non-authoritative Product Layer reports may later summarize these records, but a summary does not become a Genesis Trust Core claim unless a successor EvaluationPolicy explicitly freezes that aggregation rule.

This removes arithmetic and cohort-window complexity from the Genesis blocker set without losing any underlying record.

## Method identity decision

`method:last-observed-value:v1` remains the sole initial ForecastMethod.

It may still be described informally as a persistence-style baseline because it is suitable for future comparisons. Within Genesis v1 it is simply the admitted forecasting method. Genesis v1 makes no method-superiority claim.

When a distinct second method is introduced, a successor manifest may add a baseline relationship and pairwise comparison rules prospectively.

## Failure Corpus boundary

Attempt failures, omissions, temporal failures, resolution ambiguity, withdrawals, and abort records remain mandatory retained history where applicable.

A separately governed Failure Corpus index is not a Genesis v1 dependency. It may be derived from immutable retained failure-bearing records for reporting and analysis.

This preserves failure accountability without adding a second normative classification system to the Genesis Trust Core.

## TrustedManifest representation

The generic TrustedManifest contract may retain future-capability collections. Under the compressed Genesis v1 instance:

```text
methods = [method:last-observed-value:v1]
public_randomness_policies = []
transformation_definitions = [] unless an actually used stateless transformation is separately instantiated
review_rules = []
```

An empty future-capability collection does not authorize that capability.

The exact selected source contracts, targets, resolution rules, schedule policy, operational policies, time policies, validator contract, and acceptance rule remain content-bound dependencies.

## Successor effective object target

If P1, P2, and P3 are implemented without adding another Genesis-specific policy object, the expected compressed candidate object count after P5 is 21 rather than the current 22.

The reduction is the retirement of the instantiated Human Review Policy. The EvaluationPolicy and AcceptancePolicy are replaced by successor versions, so those replacements do not change cardinality.

This count is a P3 design target, not a frozen P5 output. P5 must recompute exact dependency closure and object count after constructing all successor sealed objects.

## P5 implementation map

P5 must implement P3 together with P1 and P2 rather than partially applying this record.

At minimum P5 must address:

### Candidate lineage

1. create a successor candidate patch after v0.5;
2. retire `policy:genesis-human-review:v1` by exact content hash;
3. retire `policy:genesis-evaluation:v1` by exact content hash;
4. add the minimal successor EvaluationPolicy;
5. replace or retire `policy:genesis-acceptance:v1` according to P1 with exact predecessor binding;
6. preserve `method:last-observed-value:v1` unless another direct defect requires versioning;
7. preserve all historical patch files unchanged.

### Manifest and object profiles

1. Genesis manifest `public_randomness_policies` is empty;
2. Genesis manifest `review_rules` is empty;
3. unused transformation and fitted-state dependencies are absent;
4. cycle-plan randomness policy reference becomes conditionally absent or canonically not applicable for deterministic-only methods;
5. no closed-model TrustReport or retrieval-accounting object is required.

### Validator and schema behavior

1. deterministic methods validate through deterministic replay without a PublicRandomnessPolicy;
2. fitted-state checks run only when an admitted method actually binds fitted state;
3. retrieval-accounting and model-observability checks run only for method profiles that require them;
4. Genesis v1 resolution does not accept human review as a value-selection path;
5. evaluation validates only the minimal scoring fields plus complete denominator accounting;
6. P2 claim vector remains independent of evaluation scoring status.

### Readiness controls

1. current GR028 Human review policy must cease to be a selected compressed-Genesis blocker;
2. GR023 Evaluation policy must close on the minimal scoring and denominator contract;
3. no readiness item may require dormant randomness, fitted-state, closed-model, or multi-method capabilities;
4. the readiness matrix must distinguish `OUT_OF_PROFILE` or an equivalent explicit state from an unresolved blocker.

### Abort conditions

1. official source ambiguity deterministically yields `REVIEW_REQUIRED` or `UNRESOLVED` without an override path;
2. missing dormant-capability objects must not abort a Genesis candidate;
3. attempts to use a dormant capability without a successor manifest fail closed;
4. missing required cohort members or temporal claims remain blocking where applicable.

### Tests

At minimum update or supersede tests that currently assert:

```text
effective v0.5 object count == 22
policy:genesis-human-review:v1 is a required operational policy
policy:genesis-evaluation:v1 binds method:last-observed-value:v1 as baseline_method_ref
```

Add negative tests proving:

1. deterministic Genesis cycles do not require a randomness policy;
2. a stochastic method cannot enter the compressed Genesis manifest without a successor policy;
3. a review decision cannot select a Genesis v1 outcome value;
4. baseline deltas and aggregate metrics are not required Genesis outputs;
5. denominator completeness remains fail closed.

## Security properties preserved

P3 preserves:

1. deterministic mandatory-cycle construction;
2. deterministic method replay and first-success retry rules;
3. exact point-in-time SourceContract evidence;
4. exact target, method, source, schedule, resolution, and policy bindings;
5. complete attempt, retry, failure, omission, correction, and withdrawal history;
6. P1 final-acceptance anchoring topology;
7. P2 separated temporal and durability claims;
8. immutable historical candidate and forecast records;
9. fail-closed behavior on ambiguous official outcomes;
10. cohort construction from expected slots rather than successful outputs.

## Current implementation status

```text
P3_DEPENDENCY_COMPRESSION = COMPLETE
P3_HUMAN_REVIEW_REDUCTION = COMPLETE
P3_EVALUATION_REDUCTION = COMPLETE
CURRENT_V0_5_CANDIDATE_ALIGNED = NO
CURRENT_VALIDATOR_ALIGNED = NO
CURRENT_READINESS_MATRIX_ALIGNED = NO
CURRENT_EVALUATION_REPORTING_ALIGNED = NO
P5_VERSIONED_IMPLEMENTATION_REQUIRED = YES
GENESIS_READY = NO
```

## Relationship to P4

P4 establishes a complexity firewall around provider qualification.

The Forecast Trust Core should consume a small frozen interface such as exact `ProviderProfile`, exact `QualificationDecision`, qualification criteria identity and version, and retained evidence-package hash. Provider qualification internals remain a supporting subsystem rather than becoming an expanding Trust Core governance surface.

P3 does not change the frozen production qualification criteria or qualify any provider.

## Network and qualification boundary

```text
network_authorized = false
Roughtime provider requests authorized = 0
RFC3161 requests authorized = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
```

## Safety boundary

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production forecasting = PROHIBITED
```

This record does not authorize Genesis, Forecast Ledger creation, forecast issuance, provider qualification execution, or any network time request.

The Genesis Ed25519 private key remains outside repository, GitHub, CI, ChatGPT, Codex, logs, prompts, fixtures, and third-party systems. Only the public key may enter project objects at a later separately authorized governance step.
