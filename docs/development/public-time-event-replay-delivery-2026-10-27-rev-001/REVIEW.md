# D245 bounded delivery review

**Result: one P2 finding in the derived driver's result-file protection.** The finite archive, fixed input closure, passive replay and preserved historical/native-result evidence otherwise pass the checks below.

## P2 — Make result refusal include symlinks and final exclusive creation

The portable insertion in `build_delivery.py` checks only `OFFLINE_REPLAY.json.exists()`, while the preserved original audit later writes that path with `write_text()`. A dangling symlink is an existing output directory entry for which `exists()` is false; the audit can therefore follow it and create its result outside the restored root. Also, a result created by another normal invocation while the audit runs will be overwritten by the later `write_text()`. Thus the advertised existing-result refusal is not complete, even without assuming a malicious same-user process.

Reject existing symlink entries before any native work and make the final result write exclusive (`open('x')` or equivalent), so a preexisting or concurrently created output is preserved. Record this as an I/O-only derivation from the preserved original driver, with an exact source-line check before transformation. Add a pure refusal test for a dangling output symlink and an isolated exclusive-write collision check; no native replay is needed to exercise either guard. Keep the original D241 script and protocol audit algorithm unchanged.

## Independent verification

- Ran only `test_delivery.py` under `-I -S -B`: all six pure methods passed, exit 0 (0.956 seconds). These cover fresh roots including a space, passive-result equality, combined missing/substituted inputs, existing regular output refusal, subject preflight rejection, bounded export/no overwrite, the finite input allowlist and symlink input rejection. No native or network branch ran.
- Independently verified the current ZIP's 2,739,527-byte size and SHA256 `5e4b99a4ea25c4e0a81de0ed2ae9d43c74a20789e87c7dbb31bdb56cf9c4da2d`; its 79 unique members are safe relative regular-file paths. All 78 manifest rows match raw member size/hash; the inventory plus manifest exactly covers the archive. Total uncompressed size is 4,866,498 bytes, below the 8 MiB cap.
- Verified all 76 fixed input members against the pinned delivery catalog and current source originals. The declared restored root contains byte-identical members. The restored native result, `RESTORED_NATIVE.json`, and the original D241 audit output are byte-identical with SHA256 `0e958df92b17c7b8bb19dc34de7188d085d46143dd08f49ca9f794359b3bd0c5`.
- Checked that the derived driver's preserved prefix/suffix exactly match the original replay driver around its sole original ROOT assignment, and the insertion is the documented physical-root, public-subject identity and output preflight block. The original driver remains separately retained; the derived file has its own manifest identity and is not presented as unchanged original code.
- Inspected the pinned reusable helper's safe path and bootstrap reader implementation: it admits the reader bytes before executing only the selected import/read helper definitions, rather than following arbitrary callbacks or a repository scan. The builder uses a finite fixed input catalog, validates each admitted input and enforces byte/member budgets before exclusive ZIP creation.

## Scope limits

The package accurately distinguishes passive matching of retained audit evidence from optional offline native cryptographic replay. The current fresh-root native completion/negative cases are retained evidence, not a native run repeated by this reviewer. No new UDP event, Go/test-key source, private key, venv/wallet/Core payload, production qualification or protocol authority is introduced by the inspected allowlist. The README preserves consumed-authorization/backoff, local-route, incomplete-history, software-trust and `NOT_READY / NONE` limits and explicitly requires network denial for optional native replay.

Only this review file was added in the repository. No native verifier, network action, Git write or protocol-state action was performed. This review concerns the new-event delivery only and does not rewrite or supersede the preserved D241/D221 artifacts.
