# Point in Time Eligibility Rules

Version: 0.1 candidate
Status: FTC_001 REVIEW CANDIDATE

## 1. Core rule

Every evidentiary input used by an IssuedForecast must have a defensible `available_at` that is less than or equal to the forecast `information_cutoff`.

Unknown required availability fails closed.

## 2. Distinct times

An evidence record may carry:

1. `reference_start`.
2. `reference_end`.
3. `published_at`.
4. `available_at`.
5. `retrieved_at`.
6. `revision_published_at`.
7. `source_snapshot_closed_at`.

These fields are not interchangeable.

## 3. available_at semantics

`available_at` is the earliest time the protocol can defensibly establish that the exact evidentiary value or artifact was available to the forecasting process under the accepted source contract.

It is a protocol claim supported by source specific evidence.

A source contract must define how `available_at` is determined.

## 4. Publication and retrieval

`published_at` can support `available_at` when the source contract establishes that publication made the data accessible under the required conditions.

`retrieved_at` proves when this project retrieved something. It does not by itself prove when the information first became available.

## 5. Revisions

A revised observation is a distinct evidentiary state.

A forecast input binds the exact revision or source snapshot used.

A later revision cannot replace an earlier observation inside an issued forecast's evidence graph.

## 6. Source snapshots

EvidenceSnapshot must bind:

```text
information_cutoff
snapshot_closed_at
member identities
member content hashes
source contract identities
transformation identities
```

Every member that can influence the forecast must pass eligibility individually or through a recursively validated snapshot contract.

## 7. Fitted transformations

A fitted transform must bind:

1. fitting window.
2. fit information cutoff.
3. training or fitting evidence snapshot.
4. fitted state content hash.
5. implementation identity.
6. hyperparameter or configuration identity where consequential.

The fit information cutoff must not exceed the forecast information cutoff.

## 8. Retrieval enabled methods

A ForecastMethod that can retrieve information during execution must declare a retrieval policy.

ForecastRunAttempt must retain enough evidence to show which retrievals occurred and their temporal eligibility.

Unlogged consequential retrieval produces `INELIGIBLE_TRUST_UNKNOWN`.

## 9. LLM and agent methods

Language models and agents are treated as forecast methods, not trusted clocks or evidence sources.

A model's internal knowledge cutoff statement cannot establish the availability time of a consequential fact used in a confirmatory forecast.

Any external retrieved evidence remains subject to ordinary source contracts and availability checks.

## 10. Historical replay

For faithful replay classification, every consequential evidence item must independently satisfy the historical cutoff rule.

If historical availability cannot be established, the experiment may remain retrospective but cannot be promoted to faithful replay.

## 11. Validation rule

For every required dependency:

```text
verified available_at <= information_cutoff
```

If true for all required dependencies, point in time eligibility passes.

If any verified `available_at` is later than cutoff, validation is `INVALID`.

If a required `available_at` cannot be established, validation is `INELIGIBLE_TRUST_UNKNOWN`.
