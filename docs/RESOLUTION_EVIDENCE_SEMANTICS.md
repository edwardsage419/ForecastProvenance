# Resolution Evidence Semantics

Version: 0.3 candidate
Status: FTC_001 FREEZE CANDIDATE

Outcome resolution has its own temporal and evidentiary contract. Forecast information cutoff rules do not apply to resolution evidence.

## Resolution evidence record

A consequential resolution evidence item binds:

```text
source_contract_ref
artifact_ref
published_at_or_unknown
retrieved_at
vintage_id_or_state
reference_period
content_sha256
```

## Admissibility

ResolutionEvidencePolicy determines ordered source priority, acceptable vintages, evidence sufficiency, conflict treatment, resolution deadline, and any authorized human review path.

Evidence can be published after forecast issuance and after the target reference period when the frozen resolution rule expects that publication schedule.

## Vintage selection

The active rule must specify whether resolution uses first release, a named revision window, final available vintage by a fixed deadline, or another deterministic policy.

A later revision cannot silently replace the vintage selected by the frozen rule.

## Retrieval

`retrieved_at` records project acquisition time. It does not redefine source publication time or the target period.

## Conflicts

Conflicting eligible sources follow the precommitted source priority and conflict rule. Human review is permitted only through an authorized ReviewRule and immutable ReviewDecision.

## Deadline

The resolution deadline determines when a target is resolved, unresolved, or awaiting an allowed source under the frozen policy.

Failure to obtain sufficient evidence by the deadline yields the policy defined unresolved state. It cannot be converted to a favorable resolved outcome by operator discretion.