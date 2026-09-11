# FTC_001 Third Adversarial Scientific Design Review

Date: 2026-09-11
Review target: version 0.3 freeze candidate
Initial disposition: FOUR RESIDUAL BLOCKERS IDENTIFIED

## F3-B01 Cycle plan selection freedom can preserve cherry picking

Severity: BLOCKING

External precommitment proves that a chosen plan existed before its execution window. It does not prevent an operator from privately evaluating multiple candidate target and method plans and externally committing only the favorable plan.

Required repair: the active trusted manifest must bind an IssuanceSchedulePolicy that deterministically derives required cycle slots from protocol state, cycle identity, calendar rules, target set, and method set. IssuanceCyclePlan must be a deterministic instantiation of that policy rather than a discretionary forecast menu.

## F3-B02 Randomness fixed inside the plan can be precomputed before commitment

Severity: BLOCKING

A stochastic seed written into a candidate plan is known before the plan is externally committed. An operator can evaluate multiple plan and seed variants and anchor only a favorable one.

Required repair: confirmatory stochastic methods must derive eligible randomness from an admitted public randomness value that becomes available only after the plan commitment boundary, or use independently auditable complete request accounting. A plan embedded operator chosen seed is insufficient.

## F3-B03 Prospective proof deadline lacks an explicit outcome information barrier

Severity: BLOCKING

A target specific external proof deadline must be constrained to occur before the protocol considers outcome information admissible. Otherwise a target definition could accidentally permit anchoring after the outcome becomes observable.

Required repair: TargetDefinition must bind an ex ante `outcome_information_barrier_rule`. Every slot must satisfy `external_proof_deadline <= outcome_information_barrier` under the target and Genesis schedule contract.

## F3-B04 SourceContract can still permit favorable artifact selection

Severity: BLOCKING

When several source artifacts satisfy broad source identity and timing conditions, a forecaster could select a favorable artifact unless the source contract defines deterministic artifact selection.

Required repair: SourceContract must bind a deterministic artifact selection rule or explicit ordered selection policy. Unknown or discretionary selection is ineligible for confirmatory use.

## F3-H01 CurrentVerifiabilityReport needs explicit as of semantics

Severity: HIGH

Current verifiability changes over time as artifacts become unavailable or recoverable. The report must state an `as_of` time and remain a derived operational assessment rather than rewriting scientific object history.

## F3-H02 Governance successor forks need an explicit policy

Severity: HIGH

A compromised or disputed authority could sign two successor manifests from one predecessor. The validator needs a frozen governance fork rule rather than choosing a branch implicitly.

Required repair: AcceptanceRule must define fork handling. Ambiguous competing accepted successors fail closed unless the predecessor governance rule explicitly resolves them.

## F3-H03 Schedule policy changes can create retroactive cycle reinterpretation

Severity: HIGH

Historical cycle validity must always use the schedule policy version bound by the applicable historical manifest. A new schedule policy cannot reinterpret old cycles.

## Initial review conclusion

The core architecture remains viable. These findings are narrow and repairable within FTC_001. No implementation is authorized until F3-B01 through F3-B04 are resolved and the high severity findings receive explicit contract treatment.