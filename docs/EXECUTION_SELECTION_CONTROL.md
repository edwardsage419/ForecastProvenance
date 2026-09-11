# Execution Selection Control

Version: 0.3 candidate
Status: FTC_001 FREEZE CANDIDATE

## Threat

A complete ledger of recorded retries does not detect hidden runs performed before or outside the recorded attempt chain. This matters when a method can produce multiple outputs from the same declared inputs.

## Method selection control class

Every ForecastMethod declares one `selection_control_class`.

`DETERMINISTIC_REPLAY`: the same bound method, configuration, fitted state, and evidence produce one deterministic prediction under the supported execution contract.

`PRECOMMITTED_RANDOMNESS`: stochasticity is fully determined by a seed or randomness object fixed by the accepted cycle plan or by an accepted post commitment challenge rule. The randomness binding is part of the eligible run attempt.

`EXTERNALLY_AUDITED_ATTEMPTS`: a third party execution service supplies independently verifiable request identities or receipts sufficient to establish complete eligible attempt accounting under the active policy.

`UNCONTROLLED_NONDETERMINISM`: hidden alternative outputs cannot be ruled out under the current evidence contract.

## Confirmatory eligibility

Version 1 confirmatory prospective issuance admits only the first three classes when their class specific validation rules pass.

`UNCONTROLLED_NONDETERMINISM` may be retained for exploratory or operational research and is ineligible for confirmatory trust claims.

## Precomputed output rule

For deterministic methods, precomputation does not create output selection freedom when exact inputs and configuration are bound and replay verification succeeds.

For stochastic methods, the eligible randomness must be fixed by the precommitted protocol. Operator chosen randomness after inspecting candidate outputs is invalid.

For externally audited methods, the policy must establish the complete eligible request set. An unverifiable claim that a recorded request was the only request is insufficient.

## Closed model limitation

A closed model that provides nondeterministic outputs without enforceable seed semantics or independently auditable request completeness is classified `UNCONTROLLED_NONDETERMINISM` for confirmatory issuance, even if the model can otherwise be identified.

This does not prevent prospective exploratory use. It prevents a stronger claim about freedom from output selection bias.