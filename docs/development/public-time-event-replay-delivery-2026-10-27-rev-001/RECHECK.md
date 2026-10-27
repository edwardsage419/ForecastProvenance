# D245 focused output-protection and final-delivery recheck

**Result: P2 is closed; no remaining actionable findings in the bounded delivery review.** Original `REVIEW.md` and the first ZIP remain preserved as prior-revision evidence.

The generated portable driver now rejects existing files or symlink entries before subject/native work. Its final writer uses exclusive creation with `open('x', encoding='utf-8')`, so a result created after preflight is preserved. The builder requires exactly one occurrence of each original ROOT assignment and output sink before applying those documented I/O transformations; it does not silently modify another source variant. The original D241 driver, protocol audit algorithm, validator sources, binary and raw event inputs remain unchanged.

Independently ran only the two new pure tests: dangling result symlink refusal before subject/native checks, and the actual generated output AST sink refusing a result created after preflight. Both passed, exit 0 (0.297 seconds); no native or network branch ran. The earlier six tests were not repeated in this recheck.

The final archive was independently checked:

- 2,742,486 bytes; SHA256 `6f8b62c87aba43d5bb044061b6e5884fc2c1db4eab77e4ab224b2033353e89ba`.
- 82 unique safe regular-file members, 81 manifest rows, 79 fixed inputs and 4,871,129 uncompressed bytes. Every member's size/hash matches the manifest and the retained final fresh root.
- All previous 76 fixed input bytes match the preserved first ZIP. The only added members are the upstream BSD2 license, Go1.27.3 license and provenance notice. The final catalog identity matches its declared 22,170-byte size and SHA256.
- Reversing the two documented portable replacements reconstructs the original D241 replay script byte-for-byte. Apart from those portable changes, README/manifest updates and three added notice assets, the first ZIP's members are preserved.
- The Go license's 1,453 bytes produce the declared public Git blob ID `2a7cf70da6e498df9c11ab6a5eaa2ddd7af34da4`. README paths and exclusive-output description match the final members. This checks the supplied notice identities and inclusion, not a comprehensive legal determination.
- The final restored native-result file remains byte-identical to D241 with SHA256 `0e958df92b17c7b8bb19dc34de7188d085d46143dd08f49ca9f794359b3bd0c5`; the final passive-result file equals the earlier passive result. The fresh-root native replay and session exit are retained execution evidence, not rerun by this reviewer.

Only this recheck document was added in the repository. No native/Go execution, network request, private/test-key handling, Git write or protocol-state action occurred. The package retains its NON_FORECAST, consumed-authorization, local-route, incomplete-history and `NOT_READY / NONE` limits. Any proposed Git preservation action is outside this review.
