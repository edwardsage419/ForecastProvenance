# M1 synthetic independent replay

This is a keyless, offline development demo. It performs no protocol state
action. Model PASS means the finite installed M1 model was independently
reconstructed and replayed, with explicit external assumptions. It never
establishes real Genesis readiness, acceptance, qualification or applicability.

From the repository root, with the retained environment:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python scripts/development/replay_independent_genesis.py \
  --corpus tests/fixtures/independent_replay_v1 --mode synthetic-model \
  --output /private/tmp/fp-independent-replay-demo-<unique-run>
```

Replace `<unique-run>` with a new name. The output directory must not exist.
Repeat with `--mode public-evidence`: these same bytes cannot produce real PASS.
No provider request, signature backend, Bitcoin executable, candidate code or
private key is read or executed. The resolver reads only installed catalogue
paths; a directory/manifest cannot select the mandatory universe. Unknown files
are ignored and symlinks in known input paths are rejected.

Exit codes: model PASS 0; known contradiction FAIL 1; missing/unestablished
evidence UNKNOWN 2; command/startup/output error 3. Always inspect `result.json`
and `raw-trace.json`, including reason codes and coverage. `audit.json` contains
a nonstable generation timestamp. The stable replay identity, exact M identity,
results and traces exclude that timestamp. Raw payload and input-reference pools
are lossless: every raw O row retains its own key, basis and provenance; equal
or conflicting duplicate rows are not deduplicated. Missing raw rows cannot be
repaired by diagnostic padding.

The fixed environment is CPython 3.12.3, pytest 9.0.2 and jsonschema 4.26.0.
Exact interpreter, installed code/CLI, parser/native helper and standard-library
fingerprints are in `integration/build.json`; the independent installed pinbook
is `src/forecast_trust_core/integration_model_pins_v1.py`. The pinbook is the
model installation bootstrap, **not** self-certified corpus evidence. Obtain
the reviewed source and pinbook together. Replaying on a different build does
not automatically upgrade the model profile; a known fingerprint mismatch is
FAIL and unavailable evidence remains UNKNOWN. No hidden host calendar/tzdb is
used: retained `tzdb/*.tzif` bytes are pinned and parsed directly. The interpreter
and installed dependencies are environment prerequisites, not secret inputs.

The model includes 27 sources, all raw source locations/dispositions, 122 atomic
clauses, their field obligations and 2817 mandatory keys. It retains three
targets/resolution rules, one last-observed-value method, six source contracts,
three providers, three cycles/slots and three retrospective measurement fixtures.
The qualification engine checks all 33 provider×boundary admissions; scientific
replay actually executes the method and attempt/cohort/resolution checks. Ten
external events replay nonce/hash/transcript/retry/time arithmetic and a finite
Merkle/chain model. Three independent source/requirement/expansion proofs bind
the current exact M; the original T01 reducer computes raw O coverage itself.

Explicit seams are crypto wire/delegation authentication, challenge origin,
retained timeout observations, independently fixed complete history, Bitcoin
head/PoW trust, source authentication/availability, initial signing semantics,
and model storage control/offline/timestamps/workflow authorization facts.
Finite chain hashes are not real Bitcoin verification. Logical public model
packets are not real signed Roughtime packets. Public signing remains blocked
by G02: no message/projection/formula/backend is selected. C01's real authority
guard remains in place. SA15-01/SC-A01/AUTHORITY_SOURCE are not extended.

`integration/copies/` contains concrete second copies, checked against actual
original bytes and the verifier-fixed inventory. Pre-signing copies exclude
future cycle, outcome, final acceptance and final bundle observations; later
replay inputs have a separate complete post-signing copy. Model timestamps are
hypothetical 2030 facts, not real actions or backdated observations. Retrospective
scientific outcomes remain distinct from pre-outcome DVR commitments. Workflow
PackageAcceptance/independent review/CandidateFreeze are isolated model facts;
the implementation invokes no real stateful workflow action.

Every result preserves:

```text
REAL_GENESIS_READINESS=NOT_ESTABLISHED
prospective_eligible=false
PROTOCOL_STATE_CHANGE=NONE
```

Development test/review records and exact delivery identities are under
`docs/development/m1-autonomous-replay-run-2026-10-07-rev-001/`. Their historical
verdicts are preserved. Final M1 completion requires the final independent
review and all eight acceptance gates; the existence of this README is not a
completion verdict. Real signing contracts, public authentication, actual
operational qualification/source/chain evidence, and real workflow authorization
remain unresolved. M2/M3 do not start automatically.
