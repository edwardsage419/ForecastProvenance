# Scientific Invariant Coverage

Version: 0.1 review map

| Invariant | Primary Trust Core coverage | Adversarial cases | Current disposition |
| --- | --- | --- | --- |
| S1 No future information | Point in time rules | ADV001, ADV003, ADV035 | Covered, source contract gap B07 |
| S2 Forecast immutability | IssuedForecast and correction rules | ADV014, ADV024, ADV025, ADV026 | Covered, lifecycle gap B02 |
| S3 Versioned semantics | Target, rule, method contracts | ADV008, ADV009, ADV010 | Covered |
| S4 Reproducibility | Hash bindings and retained dependencies | ADV005, ADV020, ADV040 | Retention gap B16 |
| S5 Independent resolution | ResolutionRule | ADV009, ADV037 | Covered, review contract gap B09 |
| S6 Evidence traceability | EvidenceSnapshot and dependencies | ADV004, ADV011, ADV034 | Source and transform gaps B07, B08 |
| S7 Observation remains observation | Target and source semantics | ADV034 | Needs explicit source contract semantics |
| S8 Explicit uncertainty | UNKNOWN and unresolved states | ADV002, ADV020, ADV037 | Covered |
| S9 No silent rewrite | Content hashes and corrections | ADV004, ADV005, ADV014, ADV025 | Covered |
| S10 Evaluation integrity | Attempt accounting and cohort rule | ADV012, ADV013, ADV038 | Batch completeness gaps B05, B06, B18 |
| S11 Genuine human evidence remains human | Human review path | No dedicated case yet | Gap B09, add synthetic cases |
| S12 Missing evidence cannot be inferred | UNKNOWN fail closed | ADV002, ADV011, ADV020, ADV034 | Covered |
| S13 Prospective status requires external evidence | AnchorReceipt | ADV015 through ADV021, ADV039 | Timing relation gaps B03, B04 |
| S14 Integrity and predictive skill separate | Trust Core scope | Architectural invariant | Covered |
| S15 Native evidence begins at Genesis | Classification and Genesis gate | ADV022, ADV023 | Classification gap B11 |
| S16 Trust uncertainty fails closed | Validation aggregation | ADV002, ADV007, ADV020, ADV034, ADV040 | Covered |
