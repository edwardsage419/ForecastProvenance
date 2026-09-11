# Forecast Trust Core

Version: 0.1 design

## Purpose

Forecast Trust Core defines the minimum model neutral contracts required to determine whether a forecast record is internally coherent, temporally admissible, externally anchored, reproducibly bound to its dependencies, and valid under the accepted protocol state.

It does not establish predictive skill.

## Core objects

### TargetDefinition

Binds target identity and version, forecast class, formal semantics, outcome space, entity and geography rules, reference period and horizon, measurement source rule, vintage policy, ambiguity policy, unresolved policy, resolution deadline, and substantive hash.

### ResolutionRule

Binds rule identity and version, compatible target identity, source hierarchy, conflict policy, evidence sufficiency rule, allowed resolution states, vintage selection rule, deadline, ambiguity policy, and substantive hash.

### EvidenceSnapshot

Binds snapshot identity, information cutoff, close time, deterministic members, source identity, relevant temporal metadata, transformations, source references, trusted upstream root, and deterministic snapshot hash.

### ForecastMethod

Binds method identity and version, family, compatible forecast classes, required inputs, implementation identity, fitted state identity, model identity, prompt or configuration identity, retrieval policy, randomness policy, probability semantics, limitations, and substantive hash.

### ForecastRunAttempt

Binds attempt identity, method identity, start and end times, information cutoff, input snapshots, terminal status, failure reason, output reference, configuration, randomness, and tool or evidence log reference.

Every retry receives a distinct attempt identity.

### IssuedForecast

Binds forecast identity, claimed issuance metadata, information cutoff, target identity, horizon, scope, probability or predictive distribution, method identity, evidence roots, resolution rule identity, consequential code identity, run attempt identity, substantive hash, and lifecycle status.

### AnchorReceipt

Binds anchor receipt identity, anchor scheme version, forecast or batch manifest hash, external proof material, anchor time semantics, verification method version, verification status, delay and finality semantics, and content identity.

### ForecastCorrection

Binds correction identity, original forecast identity, correction time, type, reason, affected fields, authority reference, corrected metadata or replacement forecast reference, scoring consequence, and content identity.

## Minimum validation outcomes

1. VALID.
2. INVALID.
3. INELIGIBLE_TRUST_UNKNOWN.
4. PENDING_EXTERNAL_ANCHOR.
5. VALID_NON_PROSPECTIVE.

The implementation may refine these names later through a versioned contract decision.
