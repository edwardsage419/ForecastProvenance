# Forecast Trust Core Adversarial Review Matrix

Version: 0.4 candidate
Status: FTC_001 FINAL FREEZE CANDIDATE

All FTC_001 test material is synthetic. No fixture may be represented as genuine prospective history.

| ID | Attack or failure | Required construction | Expected result |
| --- | --- | --- | --- |
| ADV001 | Future information leakage | Evidence member available after information cutoff | INVALID |
| ADV002 | Unknown availability | Required member lacks defensible available_at | INELIGIBLE_TRUST_UNKNOWN |
| ADV003 | Publication time substitution | Publication or retrieval metadata promoted to availability without source contract support | INELIGIBLE_TRUST_UNKNOWN |
| ADV004 | Revised data substitution | Replace issued snapshot member with later revision | INVALID |
| ADV005 | Snapshot reseal | Mutate one member and recompute snapshot hash | INVALID against trusted dependency |
| ADV006 | Circular trust root | Mutate upstream objects, recompute descendants, provide self selected manifest | INVALID |
| ADV007 | Manifest substitution | Validate historical object with newest manifest instead of required manifest | INELIGIBLE_TRUST_UNKNOWN |
| ADV008 | Target semantic mutation | Change target semantics under same target ID and version | INVALID |
| ADV009 | Resolution hindsight | Modify source priority after outcome becomes known | INVALID |
| ADV010 | Method mutation | Change consequential prompt, model, fitted state, code, or configuration without method version change | INVALID |
| ADV011 | Hidden retrieval | Consequential external retrieval absent from retrieval log | INELIGIBLE_TRUST_UNKNOWN |
| ADV012 | Retry cherry picking | Multiple eligible attempts exist but only favorable success retained | INVALID |
| ADV013 | Retry lineage deletion | Delete failed precursor attempt required by retry policy | INVALID |
| ADV014 | Probability mutation | Change prediction after sealing and recompute forecast hash | INVALID against accepted cycle manifest |
| ADV015 | Local backdating | Edit claimed issuance time earlier | No prospective upgrade |
| ADV016 | Git time backdating | Use commit metadata as sole time proof | No prospective upgrade |
| ADV017 | Signature as clock | Valid signature without independent time source | No prospective upgrade |
| ADV018 | Pending anchor promotion | Pending proof called final prospective verification | INVALID |
| ADV019 | Anchor target mismatch | Valid proof refers to different subject hash | INVALID |
| ADV020 | Anchor proof loss | Required proof bytes unavailable | Current verifiability degrades |
| ADV021 | Late anchor | Verified forecast existence bound exceeds frozen deadline | LATE_OR_INELIGIBLE |
| ADV022 | Synthetic contamination | Synthetic fixture is reported as prospective eligible | INVALID |
| ADV023 | Predecessor contamination | External or predecessor artifact is represented as native prospective evidence | INVALID |
| ADV024 | Non substantive correction abuse | Change prediction through metadata correction | INVALID |
| ADV025 | Correction erasure | Correction deletes original forecast | INVALID |
| ADV026 | Replacement overwrite | Substantive replacement reuses original forecast identity | INVALID |
| ADV027 | Hash recursion | Self hash included in its own hash projection | INVALID SCHEMA |
| ADV028 | Unknown extension field | Undeclared consequential field accepted silently | INVALID SCHEMA |
| ADV029 | Duplicate JSON key | Parser accepts duplicate property names | INVALID CANONICALIZATION |
| ADV030 | Floating probability | Scientific probability encoded as JSON float | INVALID CANONICALIZATION |
| ADV031 | Noncanonical decimal | Decimal uses exponent form, plus sign, trailing zero, or negative zero | INVALID CANONICALIZATION |
| ADV032 | Unicode byte mutation | Byte different string substituted after hashing | HASH MISMATCH |
| ADV033 | Dependency ID only | ID matches while full hash differs | INVALID |
| ADV034 | Missing source contract | Availability claim lacks admitted source contract | INELIGIBLE_TRUST_UNKNOWN |
| ADV035 | Fitted transform leakage | Fit cutoff exceeds forecast information cutoff | INVALID |
| ADV036 | Fitted state substitution | Later fitted state used under same binding | INVALID |
| ADV037 | Resolution ambiguity suppression | Ambiguous outcome forced into resolved state contrary to rule | INVALID |
| ADV038 | Unresolved case deletion | Unresolved forecast omitted from cohort accounting | INVALID EVALUATION INPUT |
| ADV039 | Anchor scheme substitution | Proof uses unadmitted scheme | INVALID |
| ADV040 | Validator version substitution | Report produced under unbound validator contract | INELIGIBLE_TRUST_UNKNOWN |
| ADV041 | Circular event identifier | Event ID included in projection used to derive that same ID | INVALID CANONICALIZATION |
| ADV042 | Mutable forecast lifecycle | IssuedForecast bytes edited from pending to verified | INVALID |
| ADV043 | Mutable anchor upgrade | Existing anchor event overwritten with upgraded proof | INVALID |
| ADV044 | Local latency backdating | Local submission time changed to satisfy service target | No scientific effect |
| ADV045 | External proof after deadline | Verified existence bound later than slot deadline | LATE_OR_INELIGIBLE |
| ADV046 | Unplanned slot insertion | Forecast appears without planned expected slot | INVALID |
| ADV047 | Planned slot omission | Expected slot disappears from cycle accounting | INVALID |
| ADV048 | Output based retry | Retry triggered because first output is undesirable | INVALID |
| ADV049 | Excess retry | Attempt count exceeds precommitted retry budget | INVALID |
| ADV050 | Source contract mutation | Availability rule changes under same version | INVALID |
| ADV051 | Transform definition mutation | Code or parameters change under same version | INVALID |
| ADV052 | Fitted state missing fit evidence | Fitted state lacks bound fit snapshot or cutoff | INELIGIBLE_TRUST_UNKNOWN |
| ADV053 | Unauthorized human override | ReviewDecision attempts to override hash mismatch | INVALID |
| ADV054 | Synthetic human evidence | Machine output labelled independent human review | INVALID |
| ADV055 | Manifest self acceptance | Candidate manifest claims acceptance without ManifestAcceptance | INVALID |
| ADV056 | Acceptance hash mismatch | ManifestAcceptance points to different candidate hash | INVALID |
| ADV057 | Correction self scoring | Correction tries to choose favorable scoring treatment | INVALID |
| ADV058 | Withdrawal cohort deletion | Issued forecast removed after withdrawal | INVALID EVALUATION INPUT |
| ADV059 | Unicode identifier confusable | Non ASCII machine identifier supplied | INVALID CANONICALIZATION |
| ADV060 | Unsorted set array | Set like reference array violates deterministic ordering | INVALID CANONICALIZATION |
| ADV061 | Resolution cutoff misuse | Resolution evidence rejected solely because it arrived after forecast cutoff | INVALID VALIDATOR BEHAVIOR |
| ADV062 | Opaque model overclaim | Partial or opaque method reported as complete provenance | INVALID TRUST REPORT |
| ADV063 | Fragile artifact loss | Missing required bytes leave current report at full verifiability | INVALID CURRENT VERIFIABILITY REPORT |
| ADV064 | Runtime timestamp nondeterminism | ValidationReport hash changes only because run time changes | INVALID VALIDATOR BEHAVIOR |
| ADV065 | Plan committed after plan deadline | Verified plan existence bound exceeds plan commitment deadline | INVALID CYCLE PLAN ELIGIBILITY |
| ADV066 | Zero safety interval | Plan deadline equals execution window open where positive margin is required | INVALID CYCLE PLAN ELIGIBILITY |
| ADV067 | Local attempt time used as ordering proof | Validator accepts backdated started_at as proof plan preceded execution | INVALID VALIDATOR BEHAVIOR |
| ADV068 | Changed plan reuses old proof | Mutated plan inherits prior plan commitment evidence | INVALID |
| ADV069 | Slot cardinality expansion | One version 1 slot emits multiple forecast artifacts | INVALID |
| ADV070 | Output schema substitution | Slot output does not match precommitted output schema | INVALID |
| ADV071 | Hidden stochastic preselection | Operator chooses randomness after inspecting candidates | INVALID |
| ADV072 | Uncontrolled nondeterminism promoted | UNCONTROLLED_NONDETERMINISM receives confirmatory prospective status | INVALID |
| ADV073 | Deterministic replay mismatch | Claimed deterministic method cannot reproduce bound output | INELIGIBLE_TRUST_UNKNOWN or INVALID per policy |
| ADV074 | Incomplete external request accounting | Externally audited method cannot prove complete eligible request set | INELIGIBLE_TRUST_UNKNOWN |
| ADV075 | Bootstrap root substitution | Genesis acceptance validated against different bootstrap governance root | INVALID |
| ADV076 | Bootstrap self authorization | Candidate manifest defines authority used to accept itself | INVALID |
| ADV077 | Governance fork without rule | Competing successor acceptances lack authorized resolution | INELIGIBLE_TRUST_UNKNOWN |
| ADV078 | Policy version substitution | Policy ID matches but full policy hash differs | INVALID |
| ADV079 | Anchor evidence fork conflict | Proof DAG branches attest incompatible subjects | INVALID |
| ADV080 | Operational failure promoted | Local failure record treated as proof external anchor service failed | INVALID TRUST REPORT |
| ADV081 | Historical validation rewritten | Missing bytes cause prior immutable ValidationReport content to change | INVALID |
| ADV082 | Stored prospective self label | Evidence payload asserts prospective eligibility | INVALID SCHEMA |
| ADV083 | Resolution vintage hindsight | Later favorable vintage silently replaces frozen vintage rule | INVALID |
| ADV084 | Resolution deadline discretion | Operator extends deadline after seeing outcome ambiguity | INVALID |
| ADV085 | Undefined dependency root | Validator invents implementation specific dependency root | INVALID SCHEMA |
| ADV086 | Target schedule shift | Cycle plan moves target timing outside target and schedule policy | INVALID |
| ADV087 | Forecast deadline after outcome barrier | External proof deadline exceeds frozen outcome information barrier | INVALID |
| ADV088 | Source acquisition discretion | Operator selects favorable artifact contrary to source selection rule | INVALID |
| ADV089 | Discretionary cycle menu | Operator removes an unfavorable target or method from deterministically required schedule | INVALID |
| ADV090 | Alternate plan shopping | Multiple candidate plans are privately evaluated and a plan inconsistent with schedule policy is committed | INVALID |
| ADV091 | Seed embedded in plan | Operator supplied seed known before external plan commitment is used for stochastic confirmatory forecast | INVALID |
| ADV092 | Public randomness substitution | Different public randomness event is selected after values are known | INVALID |
| ADV093 | Public randomness too early | Randomness event was already available at or before plan commitment deadline | INVALID |
| ADV094 | Source artifact tie discretion | Source contract permits multiple artifacts without deterministic selection | INELIGIBLE_TRUST_UNKNOWN |
| ADV095 | Historical schedule reinterpretation | New schedule policy is applied to an old cycle | INVALID VALIDATOR BEHAVIOR |
| ADV096 | Verifiability report without as of | Current verifiability state lacks declared assessment time | INVALID REPORT |

## Required coverage

FTC_001 freeze requires coverage of Scientific Invariants S1 through S16 plus plan precommitment, cycle completeness, output selection control, governance bootstrap, policy substitution, anchor DAG conflicts, current verifiability, target outcome barriers, source selection, and resolution evidence semantics.

## Synthetic fixture identity

Future implementation fixtures live only under `fixtures/synthetic/` and persist `origin_class = SYNTHETIC`.

They must never carry a self asserted prospective eligibility field.

## Acceptance rule

A test is blocking when an implementation produces a stronger trust classification than the expected result or permits silent evidence loss, cohort deletion, policy substitution, selective omission, output selection, or historical rewrite.

No adversarial failure can be waived silently. A waiver requires an explicit decision record with the affected claim and residual risk.