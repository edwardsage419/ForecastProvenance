# Next Accepted Task

Task ID: GEN_001
State: READY FOR DESIGN

## Objective

Prepare Genesis readiness without creating Forecast Ledger history or issuing genuine forecasts.

## Required design work

1. Freeze the concrete `OTS_BTC_BATCH_V1` AnchorScheme contract, including accepted proof forms, proof parsing, conservative Bitcoin existence-bound semantics, confirmation policy, malformed proof handling, and verifier versioning.
2. Define the concrete `BootstrapGovernanceRoot` instance and retention method without deriving Genesis authority from the manifest it will accept.
3. Define Genesis manifest construction and ManifestAcceptance procedure.
4. Define deterministic IssuanceSchedulePolicy and cycle plan precommitment procedure.
5. Define criteria for the minimal initial target set, including outcome information barriers and anchor precision compatibility.
6. Freeze ResolutionEvidencePolicy templates, retry, omission, correction, retention, and evaluation policies required by Genesis.
7. Execute synthetic and non-forecast anchor rehearsals only.
8. Record explicit Genesis acceptance criteria and abort conditions.

## Prohibited work

1. Genuine prospective forecast issuance.
2. Forecast Ledger Genesis creation.
3. Production model or LLM forecast execution.
4. Treating a synthetic or rehearsal anchor as native prospective evidence.
5. Importing Psychohistory artifacts as native evidence.
6. Paid infrastructure, hosted API, frontend, persistent service, or production database work.

## Exit criteria

GEN_001 exits only when the concrete external time anchor semantics, bootstrap governance root, Genesis manifest procedure, initial target admissibility rules, required policies, rehearsal evidence, and abort rules are frozen with no unresolved blocking finding.

Completion of GEN_001 authorizes a separate Genesis acceptance decision. It does not itself create the Forecast Ledger or authorize a genuine prospective forecast.
