# Initial Target Admissibility for Genesis

Version: 0.1 candidate
Status: GEN_001 REVIEW CANDIDATE

## Objective

The first prospective cohort exists to establish trustworthy elapsed history with minimal operational risk.

Genesis therefore prefers a small number of slow moving, externally resolvable targets over broad coverage or high frequency forecasting.

## Required target properties

An initial target is admissible only when all conditions below hold.

### Public outcome authority

The target has a named public primary source or a deterministic source hierarchy.

The resolution source must be accessible without a paid subscription and have a durable archival path or reproducible content capture procedure.

### Deterministic semantics

The target outcome, unit, reference period, geography, entity scope, vintage rule, ambiguity rule, unresolved rule, and resolution deadline can be frozen before forecasting.

### Observable outcome barrier

The protocol can define an `outcome_information_barrier`, representing the earliest frozen time after which material outcome information may become public under the target rule.

The barrier must be based on an official release schedule or another independently observable rule.

If an unscheduled early release becomes possible and cannot be handled deterministically, the target is ineligible for the initial cohort.

### Issuance safety margin

For Genesis version 1:

```text
external_proof_deadline <= outcome_information_barrier - 24 hours
```

The 24 hour margin is a conservative initial operating rule. It creates room for external receipt retries and sharply separates issuance from outcome disclosure risk.

A later protocol may reduce this margin only through a versioned decision supported by prospective operating evidence.

### Forecast horizon

Initial targets must have a forecast horizon of at least 7 calendar days from information cutoff to outcome information barrier.

High frequency, intraday, same day, and next hour targets are excluded from Genesis version 1.

### Resolution latency

The expected primary outcome should normally resolve within 45 calendar days after the outcome information barrier.

Longer resolution is allowed only when explicitly justified and must not dominate the initial cohort.

### Source vintage stability

The protocol must state whether the target resolves on first release, a named later vintage, or another frozen version rule.

A target whose scoring outcome can be selected retrospectively among multiple favorable vintages is ineligible.

### Small operational surface

Initial Genesis should contain no more than five target definitions and no more than one scheduled forecast artifact per target and method per cycle.

The purpose is to preserve auditability while operational evidence accumulates.

## Preferred initial target families

Preferred families have official release calendars and machine readable or easily archived official outcomes, for example:

1. Scheduled macroeconomic releases with a frozen first release vintage.
2. Scheduled public agency counts or rates with explicit reference periods.
3. Other low frequency official statistics with stable release procedures.

This list is illustrative and does not admit any target by itself.

## Excluded initial target families

Genesis version 1 excludes:

1. Market prices requiring intraday deadline precision.
2. Breaking geopolitical events.
3. Targets whose resolution depends primarily on subjective news interpretation.
4. Targets requiring paid or proprietary outcome data.
5. Targets with unknown historical or future release timing.
6. Targets with outcome rules likely to change after issuance.
7. Targets where a source edit can silently overwrite the first release and no archive procedure exists.

## Method neutrality

Target admissibility does not depend on the forecast method.

A transparent baseline and a model based method can share the same target only when both satisfy the same target, evidence, schedule, issuance, and evaluation contracts.

## Initial target set freeze

GEN_001 may develop candidate targets, but no target becomes part of Genesis until its exact TargetDefinition, ResolutionRule, SourceContracts, outcome barrier rule, schedule binding, and scoring rule are included in the candidate Genesis manifest.

No forecast values may be generated to help decide which candidate targets are selected.