# GEN_001 P6 Static Preflight Regression Coverage

Date: 2026-09-14
Status: PRE_GENESIS REGRESSION COVERAGE HARDENING RECORD
Classification: NON_FORECAST_REVIEW
Prospective eligible: false
Network authorization: none

## Scope

P6 static preflight was performed against the previously frozen input HEAD:

```text
e86df37bd3c7f3c5321896169a59d49d06ec4638
```

Repository and PR state were rechecked before the repair. The branch was `design/gen-001`; PR #6 remained Draft, open and unmerged; `main` remained the exact merge base with the branch ahead and not behind.

No Roughtime provider request, RFC3161 request, production qualification execution, Genesis action, Forecast Ledger action, private-key handling, merge, rebase or force push occurred.

## Execution availability

The available validation environment reported:

```text
Python 3.13.5
pytest 9.0.2
jsonschema 4.26.0
Git 2.47.3
Go 1.23.2 linux/amd64
```

A fresh validation checkout could not be created because the command environment could not resolve `github.com`. No repository test, schema meta-validation, compile check or adversarial execution was performed in that environment.

Therefore:

```text
P6_FULL_REGRESSION = NOT_EXECUTED
P6_PASS = NO
```

The connectivity limitation is an execution-environment condition. It is not a test PASS and is not an implementation failure.

## Static coverage finding

`NEXT_ACCEPTED_TASK.md` requires explicit qualification-signature-authority regressions for the manifest-bound high-level adapter. Static inspection found that the implementation already rejected the relevant substitutions, while the focused adapter test file did not directly exercise every required branch.

The missing direct focused coverage was:

```text
caller injection of expected_authority_id
caller injection of expected_authority_public_key
missing provider_authority_inputs member
qualification verifier build-profile identity mismatch
qualification verifier binary identity mismatch
```

The same inspection also confirmed that the adapter implementation already prohibits caller authority override fields, requires the exact three-provider authority-input set, checks the frozen qualification authority identity and public-key hash, validates the exact Ed25519 build-profile identity, checks the frozen verifier binary identity, and constructs `PinnedEd25519Verifier` internally.

This was classified as a P5 regression-coverage gap rather than a new Trust Core semantic change.

## Repair

Focused tests were added only to:

```text
tests/test_claim_authority_qualification_root_v1.py
```

Repair commit:

```text
2d0b5a9c289226ac9752e686fdb3b62a8e0ec732
```

The new cases directly cover:

```text
signature_verifier injection rejection
expected_authority_id injection rejection
expected_authority_public_key injection rejection
external authority ID mismatch rejection
external authority public-key mismatch rejection
qualification verifier contract substitution rejection
main ValidatorContract substitution rejection
Ed25519 build-profile identity mismatch rejection
Ed25519 binary identity mismatch rejection
extra provider authority input rejection
missing provider authority input rejection
state-package provider identity substitution rejection
exact internal pinned-authority binding
```

No Trust Core source, schema, candidate object, provider qualification record or production evidence object was modified by this coverage repair.

## P6 consequence

The previous frozen P6 input HEAD is superseded because the focused regression surface changed. P6 must start from zero on the final exact `design/gen-001` HEAD after this record is committed and after dynamic repository state is rechecked.

No test result from any earlier HEAD may be inherited.

The P6 execution plan still requires at least:

```text
Python compile/import checks
Draft 2020-12 meta-validation over every current schema
historical candidate/materializer regression
candidate v0.6 regression
P1/P2/P4 focused regression
claim-authority regression
qualification signature-authority regression
production receipt/profile admission regression
strong Bitcoin verifier authority tests
full repository pytest
complete synthetic adversarial suite
explicit failure and skip accounting
```

A POSIX execution environment is preferred because several mandatory synthetic strong-Bitcoin tests are explicitly skipped on Windows. Any mandatory security-test skip must be classified before P6 can pass.

The current `scripts/genesis/run_final_readiness_tests.sh` is insufficient by itself as the complete P6 evidence record because P6 also requires explicit schema meta-validation, focused-suite execution and richer environment/failure/skip accounting. This is an execution-plan requirement and does not itself change Trust Core semantics.

## Stage disposition

```text
P5_IMPLEMENTATION = COMPLETE_WITH_CLAIM_AUTHORITY_HARDENING_PENDING_REGRESSION
P5_REGRESSION_COVERAGE_HARDENING = COMPLETE_PENDING_EXECUTION
P6_FULL_REGRESSION = NOT_EXECUTED
P6_PASS = NO
P7 = PROHIBITED_UNTIL_P6_PASS
P8 = PENDING
P9 = PENDING
GENESIS_READY = NO
```

## Safety state

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
production forecasting = PROHIBITED
network_authorized = false
```

The Genesis Ed25519 private key was not accessed, requested, read, copied, uploaded, processed or referenced as an input.