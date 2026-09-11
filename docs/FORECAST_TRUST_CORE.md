# Forecast Trust Core

Version: 0.1 design
Status: FTC_001 REVIEW CANDIDATE

## Purpose

Forecast Trust Core defines the minimum model neutral contracts required to determine whether a forecast record is internally coherent, temporally admissible, externally anchored, reproducibly bound to its dependencies, and valid under the accepted protocol state.

It does not establish predictive skill.

## Normative documents

FTC_001 is split into the following normative design documents:

1. `TRUST_CORE_CONTRACTS.md` for the eight object families and lifecycle rules.
2. `CANONICALIZATION_AND_IDENTIFIERS.md` for deterministic bytes, hashes, identifiers, and dependency references.
3. `TRUSTED_MANIFEST.md` for validator trust roots and manifest acceptance.
4. `POINT_IN_TIME_RULES.md` for evidence eligibility.
5. `ADVERSARIAL_REVIEW_MATRIX.md` for the synthetic threat and failure matrix.

This file is the architectural summary. Where details conflict, the dedicated normative document controls during FTC_001 review.

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

## Trust model

Object identity and content identity are separate.

Every consequential dependency reference binds both semantic object ID and full SHA256.

The trusted manifest is supplied externally to candidate objects. A candidate object graph cannot choose its own trust root.

A consistent chain of recomputed hashes is insufficient when the chain does not match the accepted trusted manifest.

## Minimum validation outcomes

1. VALID.
2. INVALID.
3. INELIGIBLE_TRUST_UNKNOWN.
4. PENDING_EXTERNAL_ANCHOR.
5. VALID_NON_PROSPECTIVE.

Required trust checks can return PASS, FAIL, or UNKNOWN. UNKNOWN cannot aggregate upward into VALID.

## Pre Genesis restriction

No object can enter `PROSPECTIVE_VERIFIED` before Genesis Protocol acceptance.

All FTC_001 fixtures are synthetic or retrospective and remain permanently ineligible for native prospective classification.
