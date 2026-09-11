# FTC_001 Remediation Status

Date: 2026-09-11
Status: SECOND ADVERSARIAL REVIEW REQUIRED

## Blocking findings

B01 RESOLVED IN DESIGN. Two stage payload and final content identity removes circular event IDs.

B02 RESOLVED IN DESIGN. Forecast and anchor objects are immutable. Lifecycle is derived from append only evidence events.

B03 RESOLVED IN DESIGN. Local submission latency is operational metadata and cannot determine prospective eligibility.

B04 RESOLVED IN DESIGN. Prospective eligibility now requires `verified_external_existence_bound <= external_proof_deadline`. Genesis must freeze the anchor specific bound construction.

B05 RESOLVED IN DESIGN. IssuanceCyclePlan precommits expected slots and IssuanceCycleManifest requires complete slot accounting.

B06 RESOLVED IN DESIGN. Retry budget, triggers, selection, and exhausted retry treatment are precommitted.

B07 RESOLVED IN DESIGN. SourceContract is first class normative infrastructure.

B08 RESOLVED IN DESIGN. TransformationDefinition and FittedState are first class normative infrastructure.

B09 RESOLVED IN DESIGN. ReviewDecision is first class and cannot override hard trust failures.

B10 RESOLVED IN DESIGN. Deterministic ValidationReport excludes runtime validation time.

B11 RESOLVED IN DESIGN. object_role and evidence_class are separate. Prospective eligibility is derived.

B12 RESOLVED IN DESIGN. Machine identifiers and protocol tokens are ASCII only.

B13 RESOLVED IN DESIGN. Arrays require explicit ordered semantics or deterministic sorting.

B14 RESOLVED IN DESIGN. SHA256 is frozen for version 1 and migration requires schema versioning.

B15 RESOLVED IN DESIGN. ManifestAcceptance is a separate immutable governance object.

B16 RESOLVED IN DESIGN. Retention classes and trust degradation on unavailable bytes are defined.

B17 RESOLVED IN DESIGN. Correction objects cannot author scoring consequences.

B18 RESOLVED IN DESIGN. Default withdrawal rule preserves issued forecasts in confirmatory cohorts.

B19 RESOLVED IN DESIGN. Resolution evidence admissibility is separated from forecast information cutoff.

B20 RESOLVED IN DESIGN. ForecastMethod declares evidence observability class and opaque internal knowledge is not overclaimed.

## Remaining freeze conditions

These resolutions are design changes, not implementation evidence.

FTC_001 remains open until a second adversarial design review confirms that the remediation did not introduce new blocking ambiguity.

Genesis remains prohibited.
