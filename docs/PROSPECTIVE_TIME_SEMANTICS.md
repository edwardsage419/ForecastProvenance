# Prospective Time Semantics

Version: 0.3 candidate
Status: FTC_001 FREEZE CANDIDATE

## External time principle

Local wall clock fields, Git metadata, filesystem time, signatures without an independent time source, and operator claimed submission time are operational metadata only.

Scientific prospective eligibility uses externally verified existence bounds produced by an accepted AnchorScheme verifier.

## Plan precommitment inequality

Each IssuanceCyclePlan binds `plan_commitment_deadline` and a fixed `execution_window_open`.

Eligibility requires:

```text
verified_plan_existence_bound <= plan_commitment_deadline < execution_window_open
```

Genesis must bind a minimum safety margin between the deadline and the execution window that is adequate for the selected anchor's conservative time precision.

The protocol does not rely on locally asserted attempt start times to prove that planning preceded execution.

## Forecast existence inequality

Each planned slot binds an `external_proof_deadline` derived from the accepted target and Genesis protocol.

Eligibility requires:

```text
verified_forecast_existence_bound <= external_proof_deadline
```

The exact construction of each verified external bound is AnchorScheme specific and is a Genesis blocking parameter.

## Deadline immutability

Both deadlines are fixed inside the externally committed cycle plan before the execution window opens.

Changing either deadline creates a new cycle plan and requires a new plan precommitment proof.

## Pending and late states

A proof may remain operationally pending when the accepted anchor scheme permits later proof completion.

Pending evidence does not establish final prospective verification.

A verified existence bound later than its frozen deadline yields `LATE_OR_INELIGIBLE`.

An unverifiable required bound yields `INELIGIBLE_TRUST_UNKNOWN` once the applicable pending policy is exhausted.

## Target relationship

TargetDefinition supplies or binds a deterministic rule for the slot external proof deadline. Genesis must ensure target horizons and closure semantics are compatible with the conservative precision of the selected anchor.

## Anchor latency

Operational submission latency may be monitored for reliability. It cannot decide scientific eligibility unless it is itself based on independently verifiable external evidence admitted by the active AnchorScheme.

## OpenTimestamps boundary

FTC_001 freezes the abstract requirement that an AnchorScheme return a conservative verified existence bound for exact content.

Genesis must freeze the exact OTS_BTC_BATCH_V1 proof parser, accepted attestation types, conservative Bitcoin time bound construction, confirmation policy, verifier version, malformed proof behavior, and safety margin before any genuine prospective forecast is permitted.