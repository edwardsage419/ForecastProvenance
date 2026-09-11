# Point in Time Eligibility Rules

Version: 0.2 candidate
Status: FTC_001 REMEDIATION CANDIDATE

## Forecast evidence rule

Every consequential external evidentiary input used by an IssuedForecast must have a defensible `available_at <= information_cutoff`.

Unknown required availability fails closed.

`reference_start`, `reference_end`, `published_at`, `available_at`, `retrieved_at`, revision time, and snapshot closure time are distinct.

A SourceContract defines how `available_at` is established for a source.

Retrieval time establishes project retrieval, not historical availability.

## Revisions

A revised observation is a distinct evidentiary state. Later revisions cannot replace the bound revision in an issued snapshot.

## Transformations

Stateless transformations bind TransformationDefinition.

Fitted transformations additionally bind FittedState, fit evidence snapshots, and `fit_information_cutoff`.

Every consequential fit input must satisfy its applicable availability rule at the fit cutoff.

## Retrieval enabled methods

External retrievals must be logged and validated under SourceContracts. Unlogged consequential retrieval yields `INELIGIBLE_TRUST_UNKNOWN`.

## Model internal state

ForecastMethod declares an evidence observability class.

Trust Core does not claim item level provenance for opaque internal learned knowledge. Closed models can still be prospectively evaluated after Genesis under a truthful `PARTIAL_EXTERNAL` or `OPAQUE_INTERNAL` classification.

## Resolution evidence is separate

Outcome resolution evidence is governed by ResolutionRule and its resolution source contracts. It can legitimately become available after forecast issuance or target reference periods.

Forecast `information_cutoff` is not applied mechanically to outcome resolution evidence.

## Historical replay

Faithful replay requires defensible historical availability for every consequential externally observable input. Unknown availability prevents promotion to faithful replay.

## Validation

Known availability after cutoff is INVALID.

Required availability that cannot be established is INELIGIBLE_TRUST_UNKNOWN.

All required eligible external inputs at or before cutoff pass the point in time check.
