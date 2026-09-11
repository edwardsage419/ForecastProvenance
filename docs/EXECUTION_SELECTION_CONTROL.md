# Execution Selection Control

Version: 0.4 candidate
Status: FTC_001 FINAL FREEZE CANDIDATE

## Threat

Recorded retry completeness does not detect hidden runs performed before or outside the recorded attempt chain. This matters whenever the same declared forecast slot can produce multiple candidate outputs.

## Method selection control class

Every ForecastMethod declares one `selection_control_class`.

`DETERMINISTIC_REPLAY`: the same bound method, configuration, fitted state, and evidence produce one deterministic prediction under the supported execution contract.

`POSTCOMMIT_PUBLIC_RANDOMNESS`: stochasticity is derived deterministically from an admitted public randomness value that is unavailable before the cycle plan commitment boundary and is selected by a frozen PublicRandomnessPolicy. Operator chosen seeds are ineligible.

`EXTERNALLY_AUDITED_ATTEMPTS`: a third party execution service supplies independently verifiable request identities or receipts sufficient to establish the complete eligible request set under the active policy.

`UNCONTROLLED_NONDETERMINISM`: hidden alternative outputs cannot be ruled out under the current evidence contract.

## Confirmatory eligibility

Version 1 confirmatory prospective issuance admits only the first three classes when their class specific validation rules pass.

`UNCONTROLLED_NONDETERMINISM` may be retained for exploratory or operational research and is ineligible for confirmatory prospective trust claims.

## Deterministic methods

Precomputation does not create output selection freedom only when the applicable IssuanceSchedulePolicy already fixes the required slot and exact bound inputs and replay verification reproduces the prediction.

An operator cannot choose whether a deterministic slot exists after inspecting its output because slot existence is derived from the accepted schedule policy.

## Public randomness methods

The cycle plan binds the PublicRandomnessPolicy rather than a selectable seed.

The policy must define a public randomness source, the deterministic rule selecting the eligible randomness event, the temporal relation requiring that event to become available after the plan commitment deadline, the derivation algorithm from public randomness to method seed or randomness object, and failure handling.

The eligible random value must satisfy:

```text
public_randomness_available_at > plan_commitment_deadline
```

The operator cannot substitute a different random event after inspecting outputs.

## Externally audited methods

The active policy must establish the complete eligible request set. An unverifiable claim that one recorded request was the only request is insufficient.

## Closed model limitation

A closed model providing nondeterministic outputs without enforceable postcommit randomness or independently auditable request completeness is classified `UNCONTROLLED_NONDETERMINISM` for confirmatory issuance.

This does not prevent prospective exploratory use. It limits the stronger claim that output selection bias has been controlled.