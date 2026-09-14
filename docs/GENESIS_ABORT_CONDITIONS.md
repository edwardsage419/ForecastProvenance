# Genesis Abort Conditions

Version: 0.4 candidate
Status: GEN_001 ARCHITECTURE COMPRESSION P5

Genesis readiness, final acceptance, and any later operation fail closed. Abort preserves evidence and stops progression to a stronger trust claim.

## Readiness abort conditions

GEN_001 cannot exit while any selected required item in `GENESIS_READINESS_EVIDENCE_MATRIX.md` remains open.

Blocking examples include:

1. any of the three frozen Roughtime providers lacks production qualification under the exact frozen criteria;
2. provider-state evidence cannot be reconstructed from a content-closed retained record set;
3. a provider is `QUALIFICATION_EXPIRED`, `REQUALIFICATION_REQUIRED`, or otherwise non-qualified at a required historical deadline;
4. exact final validator or qualification-verifier contract cannot be content bound;
5. BootstrapGovernanceRoot public-key input is missing or malformed;
6. strong OpenTimestamps/Bitcoin verification cannot be completed under the frozen verifier contract;
7. any selected target lacks retained official first-release/parser evidence required for final readiness;
8. candidate v0.6 dependency closure, predecessor retirement hash checks, or sealed-object validation fails;
9. final adversarial review contains a blocking finding;
10. a required minimum mechanism introduces an unapproved recurring paid dependency.

## Candidate construction abort conditions

Construction stops if:

1. any dependency is referenced without its exact full content hash;
2. any v0.6 retirement does not match the exact predecessor content hash;
3. effective candidate materialization is not deterministic or does not contain exactly the justified dependency closure;
4. historical v0.2 through v0.5 candidate bytes are edited or reinterpreted;
5. Genesis v1 reintroduces a scientific Human Review authority without an explicit successor design decision;
6. EvaluationPolicy includes baseline delta, pairwise method comparison, aggregate predictive-skill claims, or probabilistic scoring without a distinct admitted method/class;
7. dormant PublicRandomnessPolicy, FittedState, closed-model, stochastic, or externally audited attempt paths become Genesis blockers without an admitted method requiring them;
8. TrustedManifest omits the exact three ProviderProfiles, matching QualificationDecisions, quorum policy, or qualification-verifier contract required by the provider-admission firewall.

## ManifestAcceptance abort conditions

ManifestAcceptance v2 is rejected if:

1. owner authority proof does not verify against the exact external BootstrapGovernanceRoot;
2. the signed object does not bind the exact candidate TrustedManifest;
3. required validation-report refs do not match the frozen acceptance rule;
4. blocking findings are nonempty for an `ACCEPT` decision;
5. the signed acceptance contains or requires a self-reference to final external evidence that can exist only after signing;
6. candidate manifest changes after signing;
7. private key material appears in repository, CI, logs, fixtures, prompts, connected tools, or third-party systems.

Any suspected Genesis private-key exposure invalidates that key for Genesis use and requires a new key before another acceptance attempt.

## Final Genesis evidence abort conditions

Independent final validation fails when:

1. final external evidence subject is not the exact signed ManifestAcceptance;
2. `EXTERNAL_EXISTENCE_BOUND_VERIFIED(ManifestAcceptance)` is not `VERIFIED`;
3. `BITCOIN_DURABILITY_VERIFIED(ManifestAcceptance)` is not `VERIFIED`;
4. optional intermediate bootstrap or candidate-manifest anchors are substituted for missing final acceptance evidence;
5. final evidence package or validator contract cannot be independently replayed.

For Genesis governance acceptance, `PRE_OUTCOME_DURABILITY_VERIFIED` and `CONFIRMATORY_PROSPECTIVE_ELIGIBLE` are `NOT_APPLICABLE`.

Genesis authorization remains a separate explicit step after successful final validation.

## Provider admission abort conditions

For every consequential deadline event after a separately authorized Genesis:

```text
as_of_utc = frozen_deadline_utc
```

The event fails the production-provider admission gate when:

1. any of the three manifest-admitted providers does not derive to `PRODUCTION_QUALIFIED` at that as-of;
2. ProviderProfile or QualificationDecision refs differ from the exact TrustedManifest bindings;
3. qualification-state package omits a retained metadata review or requalification event relevant through the as-of;
4. qualification-state package is built from a caller-selected event subset instead of the authoritative content-closed record root;
5. qualification verifier contract differs from the exact manifest binding;
6. a key, endpoint, wire profile, verifier identity, use permission, independence fact, or other qualification-relevant state requires requalification and no new accepted qualification state exists.

A provider outage does not lower qualification requirements and does not lower the receipt threshold.

## Deadline-existence abort conditions

`DEADLINE_EXISTENCE_VERIFIED` fails when the exact subject has a verified conservative wall-clock upper bound after its frozen deadline or the base existence verification fails.

Missing/pending wall-clock evidence remains `UNRESOLVED` until deterministically decidable. Bitcoin durability never repairs a missed wall-clock deadline.

## Bitcoin durability abort conditions

`BITCOIN_DURABILITY_VERIFIED` fails when:

1. OTS proof does not bind the exact ExternalTimeEvidenceBundle;
2. the bundle does not bind the exact primary subject and frozen wall-clock evidence;
3. strong Bitcoin verification fails;
4. proof or verification bytes needed for replay are unavailable.

Pending Bitcoin completion remains `UNRESOLVED` and does not rewrite a weaker verified deadline-existence claim.

## Pre-outcome durability abort conditions

`PRE_OUTCOME_DURABILITY_VERIFIED` fails when Bitcoin durability is verified but the exact DurabilityVerificationRecord does not itself obtain verified deadline existence by the frozen outcome-information barrier.

A post-outcome durability completion may remain valid historical durability evidence while failing the stronger pre-outcome claim.

## Confirmatory prospective eligibility abort conditions

`CONFIRMATORY_PROSPECTIVE_ELIGIBLE` is `FAILED` when any required Trust Core claim is failed or a hard invalidation exists, including:

1. target/method/source/schedule/validator binding mismatch;
2. mandatory slot or cycle accounting mismatch;
3. future-information use;
4. selection-control violation;
5. retry/first-success violation;
6. required deadline-existence failure;
7. required Bitcoin durability failure;
8. required pre-outcome durability failure;
9. production-provider admission failure at the relevant frozen deadline.

If no required claim fails but at least one remains unresolved, eligibility remains `UNRESOLVED` rather than being silently classified as failed or verified.

## Resolution abort conditions

Official artifact conflict, changed layout ambiguity, or insufficient semantic evidence produces `REVIEW_REQUIRED` or `UNRESOLVED`.

Compressed Genesis v1 has no scientific ReviewDecision authority that can choose a favorable resolved value. Hash mismatch, future information, missing mandatory evidence, failed time claims, incomplete cycle accounting, or output-selection violations are never human-overridable.

## Evaluation abort conditions

Evaluation fails closed when:

1. expected/issued/failed/omitted/ineligible/unresolved/withdrawn denominator accounting is incomplete;
2. an unresolved resolution is assigned a numerical outcome without an admitted deterministic resolution path;
3. absolute or squared error semantics differ from `policy:genesis-evaluation:v2`;
4. P2 temporal claim states are hidden inside a generic nonscorable status;
5. correction or withdrawal attempts to erase historical cohort membership;
6. deferred comparison/aggregation semantics are presented as Genesis v1 normative results.

## Cost and infrastructure abort conditions

No Genesis readiness or operation may silently introduce a recurring paid dependency. Any new paid provider, API, hosted database, certificate, monitoring, or subscription requires separate cost/security review and explicit owner approval.

## Abort record

Every aborted candidate or later operation retains an immutable reasoned record sufficient to identify the stage, reason codes, and evidence refs. An abort record is administrative scientific history and never prospective forecast history.

## Recovery rule

The project never weakens a trust requirement solely to preserve a candidate, cycle, provider, target, schedule, or favorable evaluation result.
