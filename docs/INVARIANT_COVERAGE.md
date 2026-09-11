# Scientific Invariant Coverage

Version: 0.4 freeze map
Status: FTC_001 ACCEPTED DESIGN

| Invariant | Primary coverage | Adversarial cases | Freeze disposition |
| --- | --- | --- | --- |
| S1 No future information | Point in time rules, SourceContract | ADV001, ADV003, ADV034, ADV035 | Covered |
| S2 Forecast immutability | IssuedForecast, correction policy, immutable events | ADV014, ADV024, ADV025, ADV026, ADV042, ADV043 | Covered |
| S3 Versioned semantics | Target, rule, method, policy contracts | ADV008, ADV009, ADV010, ADV050, ADV051, ADV078 | Covered |
| S4 Reproducibility | Canonicalization, full hash dependencies, retention | ADV005, ADV020, ADV040, ADV063, ADV073 | Covered |
| S5 Independent resolution | ResolutionRule, ResolutionEvidencePolicy, ReviewDecision | ADV009, ADV037, ADV053, ADV083, ADV084 | Covered |
| S6 Evidence traceability | EvidenceSnapshot, SourceContract, transformation contracts | ADV004, ADV011, ADV034, ADV052, ADV088, ADV094 | Covered |
| S7 Observation remains observation | Source and target semantics | ADV034, ADV050, ADV088 | Covered |
| S8 Explicit uncertainty | UNKNOWN aggregation, unresolved states | ADV002, ADV020, ADV037, ADV074 | Covered |
| S9 No silent rewrite | Content hashes, immutable events, corrections | ADV004, ADV005, ADV014, ADV025, ADV081 | Covered |
| S10 Evaluation integrity | Schedule policy, cycle accounting, retry, withdrawal rules | ADV012, ADV013, ADV038, ADV046 through ADV049, ADV058, ADV089, ADV090 | Covered |
| S11 Genuine human evidence remains human | ReviewRule and ReviewDecision | ADV053, ADV054 | Covered |
| S12 Missing evidence cannot be inferred | Fail closed trust aggregation | ADV002, ADV011, ADV020, ADV034, ADV074 | Covered |
| S13 Prospective status requires external evidence | Prospective time semantics and AnchorScheme | ADV015 through ADV021, ADV039, ADV065 through ADV068, ADV087 | Covered at abstract Trust Core interface; concrete OTS semantics remain Genesis blocker |
| S14 Integrity and predictive skill separate | Trust Core scope and ValidationReport | Architecture level | Covered |
| S15 Native evidence begins at Genesis | Origin classes and Genesis gate | ADV022, ADV023, ADV082 | Covered |
| S16 Trust uncertainty fails closed | Validation aggregation and governance resolution | ADV002, ADV007, ADV020, ADV040, ADV074, ADV077 | Covered |

## Additional threat coverage

Output selection bias is covered by ADV071 through ADV074 and ADV091 through ADV093.

Governance bootstrap and fork handling are covered by ADV075 through ADV077.

Current verifiability is covered by ADV020, ADV063, ADV081, and ADV096.

Source selection is covered by ADV088 and ADV094.

Historical schedule integrity is covered by ADV086, ADV089, ADV090, and ADV095.

No invariant has an unresolved blocking design gap inside FTC_001 scope.