# Genesis Abort Conditions

Version: 0.4 candidate
Status: GEN_001 ARCHITECTURE COMPRESSION P5 CLAIM-AUTHORITY HARDENING

Genesis readiness, final acceptance, and any later operation fail closed. Abort preserves evidence and stops progression to a stronger trust claim.

## Readiness abort conditions

GEN_001 cannot exit while any selected required item in `GENESIS_READINESS_EVIDENCE_MATRIX.md` remains open.

Blocking examples include:

1. any of the three frozen Roughtime providers lacks production qualification under the exact frozen criteria;
2. provider-state evidence cannot be reconstructed from a content-closed retained record set;
3. a provider is `QUALIFICATION_EXPIRED`, `REQUALIFICATION_REQUIRED`, or otherwise non-qualified at a required historical deadline;
4. exact final validator or qualification-verifier contract cannot be content bound;
5. BootstrapGovernanceRoot public-key input is missing, malformed, or does not match the manifest-bound qualification-authority key hash where that authority is required;
6. QualificationDecision signature verification is not executed by the exact hash-pinned Ed25519 verifier bound through the qualification verifier contract;
7. strong OpenTimestamps/Bitcoin verification cannot be completed under the frozen verifier contract;
8. any selected target lacks retained official first-release/parser evidence required for final readiness;
9. candidate v0.6 dependency closure, predecessor retirement hash checks, or sealed-object validation fails;
10. final adversarial review contains a blocking finding;
11. a required minimum mechanism introduces an unapproved recurring paid dependency.

## Candidate construction abort conditions

Construction stops if:

1. any dependency is referenced without its exact full content hash;
2. any v0.6 retirement does not match the exact predecessor content hash;
3. effective candidate materialization is not deterministic or does not contain exactly the justified dependency closure;
4. historical v0.2 through v0.5 candidate bytes are edited or reinterpreted;
5. Genesis v1 reintroduces a scientific Human Review authority without an explicit successor design decision;
6. EvaluationPolicy includes baseline delta, pairwise method comparison, aggregate predictive-skill claims, or probabilistic scoring without a distinct admitted method/class;
7. dormant PublicRandomnessPolicy, FittedState, closed-model, stochastic, or externally audited attempt paths become Genesis blockers without an admitted method requiring them;
8. TrustedManifest omits the exact three ProviderProfiles, matching QualificationDecisions, quorum policy, main ValidatorContract, qualification-verifier contract, or strong Bitcoin verifier contract required by the admitted Genesis v1 evidence path.

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

## Claim-authority abort conditions

A successor P2 claim or readiness decision is rejected if:

1. a caller-supplied `VERIFIED` state, raw bound, boolean, report field, or schema-valid claim is used as authority instead of exact evidence recomputation;
2. a claim subject/type differs from the exact required subject/type;
3. an evidence bundle, OTS proof, DurabilityVerificationRecord, provider profile, QualificationDecision, validator contract, or verifier contract is spliced from a different authority chain;
4. caller-provided expected verifier refs replace the exact refs derived from the TrustedManifest;
5. a provider runtime input supplies `signature_verifier`, `expected_authority_id`, or `expected_authority_public_key` instead of the manifest-bound qualification-verifier path injecting them;
6. the independently supplied qualification authority ID/public-key bytes differ from the values/hash frozen in the exact qualification verifier contract;
7. the Ed25519 verifier build profile or executable hash differs from the manifest-bound qualification verifier contract;
8. provider authority input keys, ProviderProfile provider IDs, or state-package provider IDs do not form the same exact three-provider set;
9. synthetic or retrospective evidence is used to satisfy a production readiness path requiring admitted operational evidence;
10. a persisted ValidationReport or StrongBitcoinVerificationReport differs from deterministic recomputation.

Historical low-level helper interfaces remain historical/non-authoritative and cannot close successor claim/readiness gates.

## Final Genesis evidence abort conditions

Independent final validation fails when:

1. final external evidence subject is not the exact signed ManifestAcceptance;
2. authoritative recomputation of `EXTERNAL_EXISTENCE_BOUND_VERIFIED(ManifestAcceptance)` is not `VERIFIED`;
3. authoritative recomputation of `BITCOIN_DURABILITY_VERIFIED(ManifestAcceptance)` is not `VERIFIED`;
4. optional intermediate bootstrap or candidate-manifest anchors are substituted for missing final acceptance evidence;
5. final evidence package or validator/verifier contract cannot be independently replayed;
6. wall-clock and Bitcoin evidence do not bind the same exact ExternalTimeEvidenceBundle where the final acceptance path requires that common bundle;
7. final validation depends on persisted claim/state values without re-deriving them from exact evidence.

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
6. qualification verifier contract does not bind the frozen criteria, exact main ValidatorContract, exact signature projection, accepted authority key hash, and exact Ed25519 verifier build/binary identity;
7. any runtime signature-verifier callback or authority substitution is supplied by the provider evidence caller;
8. provider input identity closure differs from the exact manifest-admitted three-provider set;
9. a key, endpoint, wire profile, verifier identity, use permission, independence fact, or other qualification-relevant state requires requalification and no new accepted qualification state exists.

A provider outage does not lower qualification requirements and does not lower the receipt threshold.

## Deadline-existence abort conditions

`DEADLINE_EXISTENCE_VERIFIED` fails when the exact subject has a verified conservative wall-clock upper bound after its frozen deadline or the base existence verification fails.

Missing/pending wall-clock evidence remains `UNRESOLVED` until deterministically decidable. Bitcoin durability never repairs a missed wall-clock deadline.

## Bitcoin durability abort conditions

`BITCOIN_DURABILITY_VERIFIED` fails when:

1. OTS proof does not bind the exact ExternalTimeEvidenceBundle;
2. the bundle does not bind the exact primary subject and frozen wall-clock evidence;
3. strong Bitcoin verification fails or is not executed under the exact manifest-bound hash-pinned verifier contract;
4. proof or verification bytes needed for replay are unavailable;
5. a persisted strong-verification report is used instead of re-execution or differs from recomputation.

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
9. production-provider admission failure at the relevant frozen deadline;
10. any required component claim was accepted from caller-supplied claim state rather than authoritative evidence recomputation.

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
