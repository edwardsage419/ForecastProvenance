# GEN_001 P7 v0.7 Focused Regression Record — 2026-09-16

Status: NON-NORMATIVE IMPLEMENTATION EVIDENCE RECORD

This record documents local regression evidence supplied by the owner for the isolated P7 implementation branch. It does not freeze candidate v0.7, start Genesis, qualify any provider, or authorize production forecasting.

## Exact tested source

- repository: `edwardsage419/ForecastProvenance`
- branch under implementation: `design/p7-v4-r6`
- exact tested commit: `4cb1096e60ed6f935c9fd5700f4bc6722a1a796b`
- remote branch head was checked equal to the expected commit before the detached test worktree was created
- detached test worktree reported a clean working tree before and after execution

## Execution evidence

The owner reported the following exact-head local results from WSL:

- `python -m compileall -q src scripts tests`: PASS
- focused candidate regression: `28 passed, 70 subtests passed`
- complete repository regression: `415 passed, 188 subtests passed`
- `git diff --check`: PASS
- final `git status --short`: empty

The focused candidate regression included:

- `tests/test_genesis_candidate_objects.py`
- `tests/test_genesis_candidate_patch.py`
- `tests/test_genesis_candidate_patch_v06.py`
- `tests/test_genesis_candidate_patch_v07.py`
- `tests/test_genesis_materializer.py`

## Effective candidate materialization

The exact-head materializer output reported:

```text
candidate_version = 0.7
object_count = 21
prospective_eligible = False
patch_file = candidate_patch_v0_7.json
patch_chain = [
  candidate_patch_v0_3.json,
  candidate_patch_v0_4.json,
  candidate_patch_v0_5.json,
  candidate_patch_v0_6.json,
  candidate_patch_v0_7.json
]
v4_present = True
v3_absent = True
```

The v0.7 patch therefore preserves the intended one-in/one-out effective object count while replacing the v3 deadline-receipt quorum policy with v4.

## Historical-byte preservation

The owner executed an exact diff against the implementation-branch base for:

- `candidate_object_set_v0_2.json`
- `candidate_patch_v0_3.json`
- `candidate_patch_v0_4.json`
- `candidate_patch_v0_5.json`
- `candidate_patch_v0_6.json`

Result:

```text
historical_candidate_diff_exit=0
```

Thus the tested implementation did not modify historical v0.2-v0.6 candidate bytes.

## Interpretation

This closes the first focused regression gate for P7 Track A at commit `4cb1096e60ed6f935c9fd5700f4bc6722a1a796b`.

It does **not** establish any of the following:

- candidate v0.7 frozen or accepted
- P7 complete
- R6 complete
- authoritative positive `CONFIRMATORY_PROSPECTIVE_ELIGIBLE`
- fresh P6 closure for a later source commit
- Genesis readiness
- production provider qualification

R6 remains blocked on a Genesis-v1 exact lifecycle authority profile because the current generic lifecycle schemas/validators do not machine-bind the full plan/slot/attempt/forecast/manifest contract required for positive confirmatory authority.

## Safety state

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production qualified provider count = 0
PRODUCTION_QUALIFIED = NO
AUTHORITATIVE_CONFIRMATORY_VERIFIED = PROHIBITED
```
