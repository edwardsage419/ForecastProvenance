# Forecast Trust Core Adversarial Review Matrix

Version: 0.1 candidate
Status: FTC_001 REVIEW CANDIDATE

All test material for FTC_001 is synthetic. No test fixture may be represented as genuine prospective history.

| ID | Attack or failure | Required construction | Expected result |
| --- | --- | --- | --- |
| ADV001 | Future information leakage | Evidence member available after information cutoff | INVALID |
| ADV002 | Unknown availability | Required member lacks defensible available_at | INELIGIBLE_TRUST_UNKNOWN |
| ADV003 | Publication time substitution | Known retrieval or publication metadata is incorrectly promoted to availability without source contract support | INELIGIBLE_TRUST_UNKNOWN |
| ADV004 | Revised data substitution | Replace issued snapshot member with later revision | INVALID |
| ADV005 | Snapshot reseal | Mutate one member and recompute snapshot hash | INVALID against trusted dependency |
| ADV006 | Circular trust root | Mutate upstream object, recompute all descendants, provide self selected new manifest | INVALID |
| ADV007 | Manifest substitution | Validate historical object with newest manifest instead of required manifest | INELIGIBLE_TRUST_UNKNOWN |
| ADV008 | Target semantic mutation | Change target semantics under same target ID and version | INVALID |
| ADV009 | Resolution hindsight | Modify source priority after outcome becomes known | INVALID |
| ADV010 | Method mutation | Change consequential prompt, model, fitted state, code, or configuration without method version change | INVALID |
| ADV011 | Hidden retrieval | Method retrieves consequential external information absent from retrieval log | INELIGIBLE_TRUST_UNKNOWN |
| ADV012 | Retry cherry picking | Multiple attempts exist but only favorable successful attempt is retained | INVALID |
| ADV013 | Retry lineage deletion | Delete failed precursor attempt referenced by retry policy | INVALID |
| ADV014 | Probability mutation | Change probability after sealing and recompute forecast hash | INVALID against accepted issuance manifest |
| ADV015 | Local backdating | Edit claimed_issued_at to an earlier value | No prospective upgrade |
| ADV016 | Git time backdating | Use commit metadata as sole time proof | No prospective upgrade |
| ADV017 | Signature as clock | Valid signature with no independent time source | No prospective upgrade |
| ADV018 | Pending anchor promotion | Pending OpenTimestamps receipt is called final prospective verification | INVALID |
| ADV019 | Anchor target mismatch | Valid external proof is for different manifest hash | INVALID |
| ADV020 | Anchor proof loss | Claimed verified anchor has unavailable proof bytes | INELIGIBLE_TRUST_UNKNOWN |
| ADV021 | Late anchor | Proof exceeds Genesis maximum latency | LATE_OR_INELIGIBLE |
| ADV022 | Synthetic contamination | Synthetic fixture is classified as PROSPECTIVE | INVALID |
| ADV023 | Predecessor contamination | Psychohistory artifact is represented as native prospective object | INVALID |
| ADV024 | Non substantive correction abuse | Change probability using metadata correction | INVALID |
| ADV025 | Correction erasure | Correction attempts to delete original forecast | INVALID |
| ADV026 | Replacement overwrite | Substantive replacement reuses original forecast identity | INVALID |
| ADV027 | Hash field inclusion recursion | Self hash is included in its own hash projection | INVALID SCHEMA |
| ADV028 | Unknown extension field | Consequential undeclared field is accepted silently | INVALID SCHEMA |
| ADV029 | Duplicate JSON key | Parser accepts duplicate property names before hashing | INVALID CANONICALIZATION |
| ADV030 | Floating probability | Scientific probability encoded as JSON float | INVALID CANONICALIZATION |
| ADV031 | Noncanonical decimal | Probability uses 1.0, exponent form, leading plus, or negative zero | INVALID CANONICALIZATION |
| ADV032 | Unicode byte mutation | Semantically similar but byte different string is substituted after hashing | HASH MISMATCH |
| ADV033 | Dependency ID only | Dependency ID matches while full expected hash differs | INVALID |
| ADV034 | Missing source contract | Evidence availability claim lacks admitted source contract | INELIGIBLE_TRUST_UNKNOWN |
| ADV035 | Fitted transform leakage | Fit cutoff exceeds forecast information cutoff | INVALID |
| ADV036 | Fitted state substitution | Later fitted state used under same method binding | INVALID |
| ADV037 | Resolution ambiguity suppression | Ambiguous outcome forced into resolved state contrary to rule | INVALID |
| ADV038 | Unresolved case deletion | Unresolved forecast omitted from cohort accounting | INVALID EVALUATION INPUT |
| ADV039 | Anchor scheme substitution | Receipt uses scheme not admitted by trusted manifest | INVALID |
| ADV040 | Validator version substitution | Result produced under unbound validator contract | INELIGIBLE_TRUST_UNKNOWN |

## Required matrix coverage

FTC_001 design review cannot pass unless each invariant S1 through S16 maps to at least one adversarial case or an explicit rationale explaining why the invariant is outside Trust Core automation.

## Synthetic fixture naming

All synthetic files created during implementation must live under a future `fixtures/synthetic/` tree and carry:

```text
classification = SYNTHETIC
prospective_eligible = false
```

These values are immutable fixture properties.

## Acceptance rule

A case is blocking when an implementation under review produces a stronger trust classification than the expected result.

False negatives can also be blocking when they permit silent evidence loss, cohort deletion, or historical rewrite.

No adversarial failure can be waived silently. A waiver requires a decision record stating the affected claim, residual risk, and reason Genesis can still proceed.
