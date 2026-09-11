# Architecture

Version: 0.1 design
Status: PRE_GENESIS_DESIGN

## Architectural principle

The system is an append only evidence architecture whose first responsibility is to preserve independently checkable scientific claims about forecasting processes.

## Layer 0 Normative contracts

Defines canonicalization, identifiers, content hashes, trusted manifests, target semantics, point in time rules, method semantics, resolution semantics, correction rules, and anchor semantics.

No validator may derive its trusted root solely from the object being validated.

## Layer 1 Forecast Trust Core

Forecast Trust Core is the first implementation phase and contains eight versioned object families:

1. TargetDefinition.
2. ResolutionRule.
3. EvidenceSnapshot.
4. ForecastMethod.
5. ForecastRunAttempt.
6. IssuedForecast.
7. AnchorReceipt.
8. ForecastCorrection.

Trust Core validates object identity, dependency bindings, admissible information cutoffs, lifecycle transitions, correction boundaries, run attempt accounting, anchor evidence, and trusted roots.

## Layer 2 Prospective Forecast Ledger

This layer does not exist before Forecast Ledger Genesis.

After Genesis it stores genuine issued forecasts and their immutable lifecycle records. It must never contain synthetic fixtures or predecessor research artifacts as prospective records.

## Layer 3 Outcome Resolution Ledger

Stores resolution objects separately from forecasts. Each resolution binds the target version, resolution rule version, source hierarchy, evidence, source vintage, resolver provenance, ambiguity state, and unresolved state where applicable.

## Layer 4 Evaluation Ledger

Stores evaluation cohort manifests and results. Confirmatory cohorts and scoring rules are frozen before result inspection. Evaluation explicitly accounts for all issued records within scope.

## Layer 5 Forecast Failure Corpus

Derived only from resolved prospective history after enough evidence exists. Failure attribution remains unknown when the evidence cannot support a stronger causal classification.

## Layer 6 Trust profiles and public outputs

Produces decomposable profiles by target family, horizon, regime, information set, calibration, method family, and failure mode. The architecture avoids a single opaque universal trust score.

## Trust root design

The project uses explicit trusted manifests.

A trusted manifest contains the accepted identities and versions of consequential targets, methods, resolution rules, anchor schemes, canonicalization rules, and validator versions for a declared protocol state.

Validators receive a trusted manifest as explicit input. Scientific objects cannot authenticate their own upstream semantics by embedding recomputed hashes.

Before Genesis, the accepted Genesis manifest itself must be content addressed, publicly retained, and externally time anchored.

## Canonical representation

Scientific JSON objects use one deterministic canonicalization contract with UTF 8, deterministic key ordering, deterministic separators, a fixed newline policy, no runtime random identifiers, no injected wall clock values, explicit hash coverage, and self hash exclusion.

SHA256 is the default content digest for version 1 unless a later decision records a deliberate change.

## Point in time semantics

Where applicable, observations distinguish reference period, publication time, defensible availability time, retrieval time, revision identity, revision publication time, provider version, source snapshot or trusted source reference, and transformation version.

Every forecast input must satisfy available_at less than or equal to information_cutoff under its accepted source contract.

Unknown required availability is ineligible.

## Fitted transformation rule

Every transform declares stateless or fitted status. Fitted transforms bind the fitting window, fit information cutoff, input snapshot root, fitted state identity, and code version identity.

## Historical experiment classes

1. Genuine contemporaneous forecast.
2. Faithful historical replay.
3. Retrospective model experiment.

A current model operating on historical evidence does not become a faithful replay merely through prompting.

## Storage doctrine

Initial authoritative state is file based and content addressed in Git. SQLite, DuckDB, Parquet, services, and hosted databases are deferred until a measured need exists.
