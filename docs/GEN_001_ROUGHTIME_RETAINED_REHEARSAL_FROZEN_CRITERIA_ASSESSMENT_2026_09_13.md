# GEN_001 Roughtime Retained Rehearsal Frozen-Criteria Assessment

Date: 2026-09-13

Classification: `OFFLINE_GAP_ASSESSMENT`

Assessment basis commit: `99699b97572c6e783e20a02ead9be2d3d52d2068`

Criteria ID: `FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1`

Criteria SHA256: `88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e`

Assessment time: `2026-09-13T12:59:08Z`

```text
production qualification execution = NOT PERFORMED
provider live request = NOT PERFORMED
network_authorized = false
retained classification = NON_FORECAST_REHEARSAL
prospective_eligible = false
```

## Scope and method

This assessment maps repository-retained evidence to the frozen production criteria. It is not a `QualificationReview`, `QualificationDecision`, production `ProviderProfile`, or provider state transition. It did not contact a provider, resolve DNS or SRV records, retrieve operator metadata, or access an owner private key.

The assessment used only tracked repository material. `git ls-files`, exact-hash searches, and provider-ID searches found the reviewed narrative records, schemas, validators, tests, and verifier build evidence, but did not locate a tracked Roughtime rehearsal package containing the raw plan, authorization, request bytes, response bytes, nonce material, retry states, execution report, verification transcripts, or complete evidence manifest. The executed plan SHA256 `d307402fafa351aded623f701ab7736fd2658756a0e10d04de61a92e38888d8d` and consumed authorization SHA256 `293979744f5d3494f7b270a1f100020b916971f802f52eab09390470a15a8347` are referenced by `CURRENT_STATE.md`, but their source artifacts are not in the tracked tree.

The exact rehearsal execution timestamp is not established by tracked evidence. The governance freeze records `Date: 2026-09-13` but not an exact freeze timestamp. Consequently, event ordering relative to the freeze and 30-day decision freshness cannot be computed. Historical rehearsal observations are not invalidated by this limitation.

## Assessment status vocabulary

Every criterion result below uses only:

`SATISFIED_BY_RETAINED_EVIDENCE`, `PARTIALLY_SATISFIED`, `CURRENT_EXTERNAL_METADATA_REQUIRED`, `NEW_LIVE_EVENT_REQUIRED`, `OWNER_OR_OPERATOR_EVIDENCE_REQUIRED`, `NOT_APPLICABLE`, `INSUFFICIENT_EVIDENCE`, or `BLOCKED_BY_VALIDATOR_OR_EVIDENCE_DEFECT`.

## Frozen criterion catalog

| ID | Normative requirement | Required evidence class | Applicability | Live freshness | Retained rehearsal may contribute | Owner/operator evidence | Common-dependency evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PQ01 | Bind the exact long-term root public key. | Profile plus raw cryptographic event package | All providers | Event rule applies | Yes | If control facts are not public | No |
| PQ02 | Verify root-signed delegation and supported signature schemes. | Raw response and strict replay transcript | All providers | Event rule applies | Yes | No | No |
| PQ03 | Verify the response signature under the delegated online key. | Raw response and strict replay transcript | All providers | Event rule applies | Yes | No | No |
| PQ04 | Bind the exact provider-specific nonce to the subject and response. | Plan, subject, nonce material, raw request/response, transcript | All providers | Event rule applies | Yes | No | No |
| PQ05 | Verify Merkle inclusion using the exact request-leaf semantics. | Raw request/response and strict replay transcript | All providers | Event rule applies | Yes | No | No |
| PQ06 | Bind offered/selected wire versions, acceptance profile, TYPE, root-derived SRV, packet/transport/Merkle/nonce/verifier profiles, and no fallback. | Frozen profile candidate plus event package | All providers | Current profile required | Yes | Current published identity may be required | No |
| PQ07 | Extract authenticated midpoint/radius, require positive lossless radius, enforce delegation interval and deadline upper bound. | Raw response, deadline inputs, strict replay transcript | All providers | Event rule applies | Yes | No | No |
| PQ08 | Retain raw request/response and independently verify their hashes. | Physical raw artifacts and recomputed SHA256 | All providers | Historical bytes immutable | Yes | No | No |
| PQ09 | Complete strict offline replay through the exact qualified verifier build. | Raw package, verifier binary/build profile, replay transcript | All providers | Historical build identity immutable | Yes | No | No |
| PQ10 | Freeze the complete production ProviderProfile identity; require a versioned profile and scoped requalification on change. | Current metadata capture and final ProviderProfile candidate | All providers | Immediate review before freeze | Partly | Sometimes | No |
| PQ11 | Retain affirmative permission for projected low-volume automated production use and map it to projected volume. | Operator-controlled statement or direct confirmation plus volume calculation | All providers | Current at decision | No | Yes | No |
| PQ12 | Record SLA existence and retained availability/support statements; a contractual SLA is not required. | Package record and any published statement | All providers | Current metadata review | Partly | Sometimes | No |
| PQ13 | Retain two separately authorized qualifying live events under the same exact profile, separated by at least 7 days, with complete evidence and no intervening profile change. | Two complete live-event packages | All providers | One event no older than 30 days | At most one | No | No |
| PQ14 | Ensure at least one qualifying live event occurs after criteria freeze. | Exact event and freeze timestamps plus complete event package | All providers | Yes | At most one if timing proves it | No | No |
| PQ15 | Meet the additional pilot/experimental conditions: permission, 90-day continuity, no current prohibition, current metadata, and transition-risk assessment. | Current operator evidence and dated continuity record | TimeNL-Roughtime only | 90-day metadata and 30-day event rules | Partly | Yes | No |
| PQ16 | Establish current active endpoint and fail-closed operational behavior; retain natural failures and explicit service-risk assessment. | Current operator metadata, live packages, and offline failure fixtures | All providers | Current at review | Partly | Sometimes | No |
| PQ17 | Establish positive pairwise root-secret and timestamp-issuance control independence. | First-party control facts or direct confirmations | All provider pairs | Current at decision | No | Yes when public evidence is insufficient | Yes |
| PQ18 | Classify common dependencies and block any dependency capable of corrupting or suppressing two votes. | Current control, software, hosting, DNS, network, HSM, upstream, and operator evidence | Provider set/pairs | Current at decision | Partly | Sometimes | Yes |
| PQ19 | Retain the complete cross-bound production evidence package and sealed canonical manifest. | Physical package, exact file closure, sizes, SHA256, reports, review, profile, and decision | All providers | Event and metadata rules apply | Partly | Metadata portion | No |
| PQ20 | Qualify the complete fixed three-provider set and bind exact order, profile hashes, policy, and verifier profile; outage never lowers quorum. | Three completed provider qualifications and final trusted configuration | Provider set | Current at set decision | Partly | Indirectly | Yes |
| PQ21 | Perform metadata review every 90 days and immediately before final profile freeze with retained captures and hashes. | Dated source captures, retrieved bytes, identifiers, and SHA256 | All providers | Yes | No | Sometimes | Yes where relevant |
| PQ22 | Demonstrate the prescribed failure paths using synthetic/local offline fixtures. | Deterministic offline test evidence | All providers/engineering | No | Yes | No | No |
| PQ23 | Demonstrate the four-case effective non-empty Merkle-path matrix. | Deterministic offline fixture report | All providers/engineering | No | Yes | No | No |
| PQ24 | Prevent silent standards migration and require new fixtures/requalification/live evidence for a changed profile. | Versioned profiles, current metadata, fixtures, and change review | All providers | Current at review | Partly | Sometimes | No |
| PQ25 | Separate qualification execution from independent review and independently reconstruct hashes, validators, replay, completeness, and criteria findings. | Distinct immutable executor and reviewer events | All providers | At qualification review | Partly | Owner may review as a separate event | No |
| PQ26 | Use the owner-controlled Ed25519 authority for a final bound decision after all gates close. | Final-qualified verification backend, external public-key identity, profile/manifest/review hashes, signed decision | All providers | Decision-time inputs | Engineering only | Yes | No |
| PQ27 | Apply the state machine, requalification triggers, acceptance rules, and fail-closed safety boundary without automatic transition. | Authoritative validation/state evidence | All providers/provider set | Current at decision | Partly | Final decision authority | As applicable |

## Criterion results by provider

| Criterion | roughtime.se | time.txryan.com | TimeNL-Roughtime | Evidence reference | Remaining action |
| --- | --- | --- | --- | --- | --- |
| PQ01 root binding | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | Preflight and verifier-state documents identify provider roots; raw event/profile package is absent | Retain and recompute the exact root binding in a complete package |
| PQ02 delegation | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | Rehearsal review records three qualifying results; raw response/replay artifacts are absent | Independently replay a retained complete event package |
| PQ03 response signature | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | Same reviewed summary; no tracked raw response or transcript | Retain raw response and independently replay |
| PQ04 nonce binding | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | Strict verifier/rehearsal summaries; no tracked nonce/subject/request package | Retain and cross-bind exact nonce material and request |
| PQ05 Merkle inclusion | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | Rehearsal summary plus closed offline Merkle engineering matrix | Retain raw per-provider proof and independently replay |
| PQ06 exact wire/profile semantics | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | Preflight records draft/profile/TYPE/SRV candidates; TimeNL uses an untyped draft-12 profile | Confirm current identity, freeze a candidate, and bind a complete event package |
| PQ07 authenticated time bounds | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | Rehearsal review reports qualifying receipts; raw time/deadline evidence is absent | Recompute from retained raw response and exact deadline inputs |
| PQ08 raw bytes and hashes | INSUFFICIENT_EVIDENCE | INSUFFICIENT_EVIDENCE | INSUFFICIENT_EVIDENCE | No tracked raw Roughtime request/response package located | Retain physical raw artifacts and independently recompute hashes |
| PQ09 strict replay/build binding | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | Strict verifier build/state and reviewed result summaries exist; raw package closure is absent | Replay a complete physical package through the exact qualified build |
| PQ10 production profile freeze/stability | CURRENT_EXTERNAL_METADATA_REQUIRED | CURRENT_EXTERNAL_METADATA_REQUIRED | CURRENT_EXTERNAL_METADATA_REQUIRED | Preflight candidate facts are not an immediate pre-freeze metadata capture or final profile | Conduct a separately authorized current metadata review before profile freeze |
| PQ11 production-use permission | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED | Freeze review notes general/public-use wording, individual-use wording, and TimeNL pilot status; none closes exact projected automated production use | Retain explicit scope/volume-covering operator evidence; TimeNL requires explicit automation permission |
| PQ12 contractual SLA policy | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | Frozen criteria state contractual SLA is not required | Record existence/absence and any current availability/support statement in a future package |
| PQ13 two-event repeatability | NEW_LIVE_EVENT_REQUIRED | NEW_LIVE_EVENT_REQUIRED | NEW_LIVE_EVENT_REQUIRED | Only one retained rehearsal is described; its complete raw package and exact time are unavailable | Obtain at least the missing separately authorized qualifying event(s), at least 7 days apart |
| PQ14 post-freeze event | NEW_LIVE_EVENT_REQUIRED | NEW_LIVE_EVENT_REQUIRED | NEW_LIVE_EVENT_REQUIRED | Exact rehearsal and freeze timestamps are unavailable, so post-freeze ordering is not established | Run a future separately authorized qualifying live event after the frozen criteria |
| PQ15 pilot conditions | NOT_APPLICABLE | NOT_APPLICABLE | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED | Preflight identifies TimeNL as pilot; no 90-day continuity or explicit production automation evidence closes the gate | Retain operator permission, 90-day continuity, current status/no-prohibition capture, and transition review |
| PQ16 operational criteria | CURRENT_EXTERNAL_METADATA_REQUIRED | CURRENT_EXTERNAL_METADATA_REQUIRED | CURRENT_EXTERNAL_METADATA_REQUIRED | Offline failure engineering exists; current endpoint/service evidence and complete live packages do not | Obtain current metadata and future authorized live-event evidence; retain natural failures if any |
| PQ17 root/issuance independence | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED | Different domains and keys do not prove positive control-domain independence | Retain affirmative pairwise root-secret and issuance-control evidence |
| PQ18 common dependencies | CURRENT_EXTERNAL_METADATA_REQUIRED | CURRENT_EXTERNAL_METADATA_REQUIRED | CURRENT_EXTERNAL_METADATA_REQUIRED | Tanner Ryan software-family correlation between time.txryan.com and TimeNL is known; threshold impact and other dependencies are not currently evidenced | Review current dependencies and evaluate the frozen two-vote threshold without guessing |
| PQ19 package/manifest completeness | INSUFFICIENT_EVIDENCE | INSUFFICIENT_EVIDENCE | INSUFFICIENT_EVIDENCE | No tracked physical rehearsal package or production manifest closure was located | Preserve any historical package separately if it exists; construct no production package until authorized evidence exists |
| PQ20 fixed provider-set readiness | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | Fixed order, two-of-three policy, no-lowered-quorum rule, and one-pilot limit are frozen; individual gates remain open | Complete all three provider qualifications and final trusted binding later |
| PQ21 metadata freshness | CURRENT_EXTERNAL_METADATA_REQUIRED | CURRENT_EXTERNAL_METADATA_REQUIRED | CURRENT_EXTERNAL_METADATA_REQUIRED | Preflight summaries are not retained current source captures satisfying the 90-day/immediate-review rule | Perform a separately authorized read-only metadata review with captures and hashes |
| PQ22 offline failure paths | SATISFIED_BY_RETAINED_EVIDENCE | SATISFIED_BY_RETAINED_EVIDENCE | SATISFIED_BY_RETAINED_EVIDENCE | Repository validators/tests and adversarial hardening cover the required fail-closed paths | Preserve exact regression evidence; provider traffic is not required |
| PQ23 Merkle matrix | SATISFIED_BY_RETAINED_EVIDENCE | SATISFIED_BY_RETAINED_EVIDENCE | SATISFIED_BY_RETAINED_EVIDENCE | Verifier build/state records typed hash-first, typed node-first, untyped draft-12 node-first, and wrong-order rejection coverage | Preserve exact fixture/build identities |
| PQ24 standards transition | CURRENT_EXTERNAL_METADATA_REQUIRED | CURRENT_EXTERNAL_METADATA_REQUIRED | CURRENT_EXTERNAL_METADATA_REQUIRED | Frozen no-silent-migration rule and versioned profiles exist; current provider transition state is not captured | Review current operator metadata and requalify on relevant change |
| PQ25 executor/reviewer independence | INSUFFICIENT_EVIDENCE | INSUFFICIENT_EVIDENCE | INSUFFICIENT_EVIDENCE | A separate rehearsal evidence review is documented, but tracked artifacts do not establish immutable distinct executor/reviewer event identities and reconstructed inputs | Establish identities and a separate immutable review during qualification |
| PQ26 decision authority/backend | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED | Verification backend engineering is final-qualified; owner authority public-key identity and signed decisions do not exist | Owner supplies public-key identity only after other gates; private key remains outside tooling |
| PQ27 state/acceptance safety | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | PARTIALLY_SATISFIED | Fail-closed object model and validators exist; no qualification objects or decision are instantiated | Execute the state path only after all evidence and authority gates close |

No criterion is marked `BLOCKED_BY_VALIDATOR_OR_EVIDENCE_DEFECT`. No validator/criteria/object-model inconsistency or retained hash mismatch was established. Because the raw rehearsal package is absent from the tracked tree, its internal consistency could not be checked; that is `INSUFFICIENT_EVIDENCE`, not proof of a defect. A stale status narrative in `CURRENT_STATE.md` and the readiness matrix was corrected alongside this assessment to reflect the already completed repository regression and final-qualified Ed25519 verification backend.

## Provider gap summary

| Provider | Retained repeatability event contribution | Post-freeze event required | Permission evidence status | Independence evidence status | Continuity status | Metadata freshness status |
| --- | --- | --- | --- | --- | --- | --- |
| roughtime.se | NOT ESTABLISHED: raw package and exact event time absent; it may contribute at most one only after exact independent review | REQUIRED | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED | NOT_APPLICABLE beyond ordinary repeatability/operations | CURRENT_EXTERNAL_METADATA_REQUIRED |
| time.txryan.com | NOT ESTABLISHED: raw package and exact event time absent; it may contribute at most one only after exact independent review | REQUIRED | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED | NOT_APPLICABLE beyond ordinary repeatability/operations | CURRENT_EXTERNAL_METADATA_REQUIRED |
| TimeNL-Roughtime | NOT ESTABLISHED: raw package and exact event time absent; it may contribute at most one only after exact independent review | REQUIRED | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED, including explicit automated production use | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED | INSUFFICIENT_EVIDENCE for the pilot-specific 90-day requirement | CURRENT_EXTERNAL_METADATA_REQUIRED |

Per-provider cryptographic evidence is `PARTIALLY_SATISFIED`: the retained review and verifier-state records support the historical three-of-three result, but the missing physical raw package prevents an exact frozen-criteria replay conclusion. No provider's event is currently labeled `ELIGIBLE_AS_EVENT_1`. Current permission and positive root/issuance independence evidence are not sufficient for any provider. Common-dependency evidence requires a current review; the known Tanner Ryan software-family correlation is a recorded risk and is not, by itself, proof of shared root or issuance authority or of a two-vote blocking dependency.

## Remaining blockers and required authority

| Remaining blocker | Requires network | Requires owner action | Requires operator evidence | Requires new authorization |
| --- | --- | --- | --- | --- |
| Locate/preserve an existing historical raw rehearsal package, if one exists outside the tracked tree | No | Yes | No | No |
| Independently review exact retained bytes, hashes, timestamps, profile, retry state, and transcripts | No | Yes | No | No |
| Current operator metadata capture and immediate pre-profile-freeze review | Yes | Yes | Possibly | Yes |
| Exact low-volume automated production-use permission and projected-volume mapping | Possibly | Yes | Yes | Yes if obtained through a networked action |
| Positive pairwise root-secret and issuance-control evidence | Possibly | Yes | Yes when public evidence is insufficient | Yes if obtained through a networked action |
| Current common-dependency threshold review | Possibly | Yes | Possibly | Yes for any networked collection |
| TimeNL 90-day continuity, pilot/no-prohibition status, and transition-risk evidence | Possibly | Yes | Yes | Yes for any networked collection |
| Missing qualifying live repeatability event(s), including a provably post-freeze event | Yes | Yes | No | Yes, separately for every event |
| Complete physical production evidence package and canonical manifest | No after inputs exist | Yes | No | No |
| Separate immutable independent qualification review | No after inputs exist | Yes | No | No |
| Owner authority public-key identity and final signed QualificationDecision | No after inputs exist | Yes | No | No; this assessment does not authorize it |
| Three sealed ProviderProfiles and final provider-set binding | No after inputs exist | Yes | No | No; this assessment does not authorize it |

## Final boundary

The retained rehearsal remains historically classified as `NON_FORECAST_REHEARSAL` with `prospective_eligible = false`. Its reviewed three-of-three result contributes useful engineering and historical evidence but does not establish a production event, does not close current permission or independence, and does not authorize reuse of the consumed authorization.

Offline validation for this assessment recomputed the criteria SHA256 above and ran the Roughtime production-qualification, hardening, verifier-qualification, execution, rehearsal, control, and plan test subset with `PYTHONPATH=src`: `143 passed, 6 skipped, 9 subtests passed`. The tests use synthetic/local transports and did not perform a provider request.

```text
production qualification execution = NOT PERFORMED
production qualified provider count = 0
PRODUCTION_QUALIFIED = NO
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
network_authorized = false
```
