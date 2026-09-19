# GEN_001 P7 Dependency Reevaluation Decision

Date: 2026-09-16
Status: PRE_GENESIS_ARCHITECTURE_DECISION
Classification: PRE_GENESIS_DESIGN
Prospective eligible: false
Genesis effect: none
Network authorization: none
Basis commit: `c4cfb7bdaf22e68e14bd350468f1e95f8beb419f`

## Purpose

This record closes the P7 architecture decision and defines the minimum implementation work required before the Genesis v1 profile can be frozen again.

It does not create Genesis, a Forecast Ledger, a prospective forecast, a production-qualified provider, a production provider request, or a new accepted candidate. It does not authorize provider qualification execution. It does not modify historical candidate bytes or reinterpret historical policy versions.

## Decision summary

P7 reaches four linked decisions:

1. Genesis v1 retains Roughtime as the external civil-time evidence mechanism.
2. Genesis v1 retains production qualification for the frozen Roughtime provider pool as a supporting subsystem; the qualification governance surface is not expanded.
3. `policy:deadline-receipt-quorum:v3` is too broad for the minimum Trust Core wall-clock claim because it makes provider execution-orchestration behavior claim-critical even though the authoritative claim is established by replayable qualifying receipt evidence. A versioned successor quorum policy is required.
4. `CONFIRMATORY_PROSPECTIVE_ELIGIBLE` must have a complete positive Genesis v1 authority path before Genesis. The current fail-closed `FULL_TRUST_CORE_CHECK_AUTHORITY_NOT_IMPLEMENTED` state is safe but is not sufficient for Genesis operation.

Therefore:

```text
P7_ARCHITECTURE_DECISION = REACHED
ROUGHTIME_WALL_CLOCK = RETAIN
ROUGHTIME_PRODUCTION_QUALIFICATION = RETAIN_AS_SUPPORTING_SUBSYSTEM
P7_F1_DISPOSITION = RESOLVE_BY_SUCCESSOR_QUORUM_POLICY
R6_DISPOSITION = IMPLEMENT_MINIMAL_GENESIS_V1_POSITIVE_AUTHORITY
CANDIDATE_V0_7_REQUIRED = YES
GENESIS_READY = NO
PRODUCTION_QUALIFICATION_EXECUTION = NOT_READY
```

## Why Roughtime remains necessary

Genesis v1 requires independently replayable evidence that exact content existed no later than a frozen civil-time deadline.

Bitcoin durability does not replace this role. Bitcoin and OpenTimestamps provide durable public commitment under their trust model, but Bitcoin block header time is not accepted as a precise civil-time deadline upper bound. The P2 separation between existence and durability remains unchanged.

Removing all external wall-clock evidence would therefore remove a required Genesis v1 trust property rather than compress an unused dependency.

A single Roughtime provider is not selected as the replacement because it would collapse the wall-clock trust boundary to one provider root and one issuance-control domain. The existing two-of-three design gives one-provider fault tolerance under the frozen independence assumptions while preserving a zero-recurring-cash-cost path.

A fixed two-provider/two-of-two design is coherent but loses the availability benefit of the already frozen three-provider pool without removing the need to qualify independent provider identities. P7 therefore retains the three-provider pool and two-of-three receipt threshold.

## Production qualification decision

Production qualification remains necessary because a receipt is meaningful only relative to an admitted provider identity and frozen trust profile.

The supporting qualification subsystem supplies evidence for at least:

```text
provider/operator identity
root public key and issuance-control identity
wire/protocol profile
no-fallback profile
qualified verifier identity
production-use permission
independence/common-control review
frozen criteria identity
qualification evidence package identity
signed QualificationDecision
```

Removing production qualification entirely would replace a content-bound provider trust basis with an implicit mutable provider registry or an unreviewed key list. P7 rejects that simplification.

The P4 complexity firewall remains controlling in spirit: provider discovery, evidence acquisition, diagnostics, research workflow, criterion-by-criterion review mechanics and qualification execution remain supporting-subsystem concerns rather than expanding the Forecast Trust Core.

No new qualification governance layer is introduced by P7. The frozen V1 criteria are not weakened merely to obtain a passing provider result.

## R5 / P7_F1 root cause

`policy:deadline-receipt-quorum:v3` combines two different concerns:

1. receipt validity and quorum semantics that determine the wall-clock claim;
2. network execution/orchestration rules such as attempting all three providers, frozen attempt order, retry/backoff state, and execution transcript accounting.

The authoritative wall-clock recomputation does not depend on a provider execution transcript. It reconstructs the exact admitted provider set, replays each retained qualifying receipt under its exact ProviderProfile and verifier build, requires at least two distinct admitted providers, and derives the conservative quorum upper bound from the qualifying receipt set.

The current implementation therefore proves a set-based two-of-three wall-clock claim, while v3 additionally asserts a stronger execution-process property that the production authority package does not prove.

Adding a new normative production execution object solely to prove that stronger process property would increase Genesis Trust Core surface without improving the cryptographic time bound established by two independently qualifying receipts.

## Successor deadline receipt quorum policy

P7 selects a versioned successor policy, working semantic version `policy:deadline-receipt-quorum:v4`.

The exact sealed object must be constructed and reviewed during the implementation phase. This decision does not freeze its final hash.

The successor policy remains claim-critical for:

```text
exact frozen provider pool size = 3
exact admitted provider identities and profiles
minimum independent provider groups = 2
threshold = at least two distinct qualifying receipts from the frozen pool
unlisted provider substitution prohibited
provider outage never lowers the two-receipt threshold
subject-bound independent nonce per counted provider
exact frozen wire/protocol/profile semantics
no protocol/transport/packet fallback
positive authenticated radius
conservative upper bound = midpoint + radius
qualifying receipt upper bound at or before the frozen receipt deadline
exact verifier-build binding
raw request/response retention and deterministic strict-verifier replay
receipt/provider/qualification-state cross-binding
```

The successor policy does not make the following provider-network orchestration facts prerequisites of `EXTERNAL_EXISTENCE_BOUND_VERIFIED`:

```text
attempt all three providers after sufficient qualifying receipts already exist
provider attempt order independent of observed results
complete failed-provider attempt transcript
provider retry/backoff transcript
pre/post provider retry-state snapshot bindings
execution transcript SHA256 for nonqualifying or unused provider attempts
```

These facts may remain operational diagnostics where useful. They do not become hidden prerequisites of the civil-time claim.

A qualifying evidence bundle may contain two or three distinct qualifying receipt evidence objects. Fewer than two remains insufficient. Duplicate provider identities remain prohibited.

The successor policy does not reinterpret v3. Historical v3 evidence continues to be evaluated under v3.

## Security analysis of the R5 disposition

The two-of-three trust model already assumes that the accepted quorum contains sufficient independent provider control such that one-provider compromise cannot create an accepted false time bound.

For an accepted two-receipt subset, the conservative bound is derived from the qualifying receipts themselves. Attempting an unused third provider after the claim already has two qualifying independent receipts does not strengthen the cryptographic binding of those retained receipts.

If two provider control domains can collude to create accepted false receipts, attempting the third provider does not repair the underlying two-of-three trust assumption unless the policy also requires all successful provider results to become claim inputs and proves complete attempt visibility. P7 does not add that larger execution-audit system to Genesis v1.

The retained security boundaries are therefore explicit:

1. exact three-provider pool;
2. at least two distinct qualifying receipts;
3. provider independence/common-control qualification assumptions;
4. exact receipt replay;
5. no threshold lowering or provider substitution;
6. durable retention of the exact evidence used for the claim.

## Candidate lineage impact

The current effective candidate remains v0.6 until a successor patch is constructed and passes review.

Implementation is expected to require:

```text
candidate_patch_v0_7.json
```

with at least:

```text
retire policy:deadline-receipt-quorum:v3 by exact content hash
add policy:deadline-receipt-quorum:v4 with a new exact sealed hash
```

No new provider execution-accounting normative object is planned.

If no other normative object is required by the R6 implementation, expected effective object count remains 21 because the quorum policy replacement is one-for-one.

Historical candidate files v0.2 through v0.6 remain byte-immutable.

## R6 positive confirmatory authority is a Genesis blocker

The current repaired authority path correctly prevents false positive confirmatory eligibility. If the implemented temporal/durability component set would otherwise aggregate to `VERIFIED`, it returns:

```text
CONFIRMATORY_PROSPECTIVE_ELIGIBLE = UNRESOLVED
reason = FULL_TRUST_CORE_CHECK_AUTHORITY_NOT_IMPLEMENTED
```

That state is correct for pre-Genesis repair but cannot be the final Genesis v1 operating state. A Genesis system that can never authoritatively produce a positive confirmatory claim cannot create the intended confirmatory prospective cohort.

Therefore positive Genesis v1 confirmatory authority is mandatory before P8.

## Minimum R6 authority scope

P7 does not select a generic universal execution-authority framework.

The implementation should support only the actually instantiated Genesis v1 profile:

```text
one deterministic method: method:last-observed-value:v1
selection_control_class = DETERMINISTIC_REPLAY
one deterministic schedule family
no fitted state
no public randomness
no stochastic execution
no closed model
no externally audited model requests
```

The positive authority must deterministically reconstruct the complete applicable Genesis v1 check set from exact retained objects and evidence rather than accept caller-supplied booleans, status strings, opaque validation results, or caller-authored hard-invalidation codes.

At minimum it must establish:

1. exact historical trusted-manifest admission of target, method, source, schedule, retry, omission, correction, evaluation, time-evidence and validator dependencies;
2. deterministic mandatory cycle and slot construction;
3. exact cycle-plan binding and plan deadline claim;
4. exact point-in-time evidence and information cutoff compliance;
5. deterministic replay of `method:last-observed-value:v1` over the exact admitted evidence;
6. selection control = deterministic replay verified;
7. attempt-chain completeness for the forecast method under `policy:genesis-retry:v1`;
8. no second confirmatory method attempt after first success;
9. second attempt permitted only after an admitted retry-eligible first-attempt technical failure;
10. first-success-only issuance selection;
11. exact IssuedForecast binding to the eligible successful attempt, slot, plan, target, method, evidence and policies;
12. complete cycle-manifest accounting for every mandatory slot;
13. exact issued forecast membership/cardinality for an issued slot;
14. cycle-manifest forecast deadline claim;
15. all required Bitcoin durability and pre-outcome durability claims;
16. absence of any deterministically reconstructed hard protocol invalidation.

A failed mandatory check produces `FAILED`. Missing but nonfailed evidence produces `UNRESOLVED`. Only the complete passing set may produce `VERIFIED`.

## Reuse before expansion

The implementation should reuse current deterministic validators where they already encode the required rule, including plan validation, cycle-manifest completeness, point-in-time validation, deterministic selection control and the repaired temporal/durability authority functions.

New code should be limited to exact-object contract gates and deterministic orchestration needed to reconstruct the full Genesis v1 authority set.

A new generic governance subsystem, transparency log, user PKI, stochastic execution framework or closed-model authority layer is out of scope.

## P7 implementation sequence

The next implementation phase should proceed in this order:

1. construct the successor v4 quorum policy and candidate v0.7 retirement/addition pair;
2. align wall-clock authority and exact contract tests to the v4 semantics;
3. implement the minimum deterministic Genesis v1 R6 positive authority path;
4. add adversarial tests for hidden/missing attempts, second attempt after success, retry-ineligible retry, issued-forecast substitution, slot substitution, incomplete manifest accounting, future information, dependency substitution and synthetic/live evidence confusion;
5. update candidate materialization and control-document expectations;
6. run focused regression;
7. run the complete P6-equivalent offline regression and synthetic adversarial suite on one exact final HEAD;
8. only after the new minimal Genesis profile is frozen again, reconsider whether production qualification execution should begin.

Any correctness/security defect found during implementation returns the work to repair before a new P6 result can be accepted.

## Production qualification execution remains paused

P7 retains the need for production qualification, but this decision does not authorize it now.

The reason is sequencing rather than provider failure:

```text
successor v4 policy not yet frozen
candidate v0.7 not yet constructed
R6 positive authority not yet implemented
fresh exact-head regression not yet complete
```

Starting qualification before the final minimum profile is frozen risks qualifying against a dependency shape that is still changing.

Therefore:

```text
PRODUCTION_QUALIFICATION_EXECUTION = NOT_READY
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
network_authorized = false
```

## P7 closure state

P7 architecture decision is complete, but implementation is not complete.

```text
P7_ARCHITECTURE_DECISION = COMPLETE
P7_IMPLEMENTATION = REQUIRED
P7_F1 = OPEN_PENDING_V4_IMPLEMENTATION_AND_REGRESSION
R6 = OPEN_PENDING_POSITIVE_AUTHORITY_IMPLEMENTATION_AND_REGRESSION
CURRENT_EFFECTIVE_CANDIDATE = V0_6
CANDIDATE_V0_7 = CREATED_AND_VALIDATED
CANDIDATE_V0_7_ACCEPTANCE = NOT_YET_PERFORMED
GENESIS_READY = NO
P8 = PROHIBITED_UNTIL_P7_IMPLEMENTATION_AND_FRESH_REGRESSION_CLOSE
```

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
Roughtime provider requests authorized = 0
RFC3161 requests authorized = 0
production qualification requests authorized = 0
```

The Genesis Ed25519 private key remains prohibited from repository, GitHub, ChatGPT, Codex, logs, prompts, fixtures and remote execution environments.

PR #6 remains Draft, open and unmerged unless separately authorized.