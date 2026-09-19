# GEN_001 Roughtime Provider Metadata and Governance Evidence Review

Date: 2026-09-13

Classification: `READ_ONLY_PUBLIC_METADATA_GOVERNANCE_REVIEW`

Assessment basis commit: `efd463b71066f0dcdec039162ceb6a4fc7568a79`

Criteria ID: `FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1`

Criteria SHA256: `88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e`

```text
metadata_research_network_authorized = true
Roughtime live request = NOT PERFORMED
RFC3161 request = NOT PERFORMED
production qualification execution = NOT PERFORMED
provider qualification state change = NONE
network_authorized = false
```

## Research scope and authorization boundary

This review used the one-time authorization for public metadata and governance research only. It retrieved official provider/operator pages, official GitHub material, IETF status, public DNS records, and RIPE NCC routing metadata. It did not send UDP or TCP data to a Roughtime endpoint, did not probe a port, did not execute a repeatability event, did not contact an operator, and did not access a private key.

The research plan was fixed before browsing: close or characterize production-use permission, provider identity, root/issuance control, pairwise independence, common dependencies, current endpoint/root publication, TimeNL pilot continuity, standards transition, production prohibitions, and 90-day freshness. Public endpoint or key publication alone was not treated as permission or control evidence.

## Evidence methodology

Public response bodies were saved without browser credentials, cookies, or session state under `docs/evidence/roughtime-provider-metadata-governance-review-2026-09-13/`. The directory contains 42 captured evidence files and `SHA256SUMS.txt`, which lists one SHA256 for every capture. The SHA256 of `SHA256SUMS.txt` is `7009696807e65a3e0a84a9b6ef272c0954497aa98e3c84416e485442f9bce496`.

DNS was queried only as metadata through Cloudflare 1.1.1.1 DNS over HTTPS. The raw JSON records the query, response, TTL, DNSSEC AD flag, and any negative answer. RIPEstat prefix-overview JSON supplied public BGP origin/holder attribution. No service availability inference is made from an HTTP page, DNS answer, or route announcement.

## Source register

| ID | Provider/criterion | URL | Title | Publisher | Retrieved UTC | Published/updated | Type | Factual contribution | First party | Retained evidence/hash | Assessment and limitations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S01 | roughtime.se identity, use, endpoint, root, upstream | https://roughtime.se/ | roughtime.se | roughtime.se | 2026-09-13T13:21:35.467Z | Not stated | Official HTML | Draft-19, `roughtime.se:2002`, root key, STUPI hosting, atomic-clock connection, broad invitation to use | Yes | `roughtime-se.html`, `87ca38e...914e` | Current and authoritative; does not say automated production use, projected volume, or secret-control identity |
| S02 | time.txryan.com identity, permission, endpoint, root, hosting | https://time.txryan.com/ | Public NTP, NTS, and Roughtime Server | Tanner Ryan | 2026-09-13T13:21:37.445Z | Published 2026-04-21; modified 2026-09-12 | Official HTML | Tanner Ryan, endpoint/key, AS16276/OVH, monitored service, individual-client permission, high-volume contact rule | Yes | `time-txryan-com.html`, `c5cb164d...ce1c` | Current; automation and the project's projected production volume are not explicit |
| S03 | TimeNL operator, pilot, endpoint, root, fair use | https://time.nl/index_en.html | TimeNL Public NTP/NTS service | SIDN Labs | 2026-09-13T13:21:39.027Z | Current Git source last changed 2026-09-04 | Official HTML | SIDN Labs service, TimeNL-Roughtime pilot, endpoint/key, possible port change, fair-use/disclaimer context | Yes | `timenl-index-en.html`, `a59c4e8d...c860` | Current; general NTP terms do not explicitly grant automated Roughtime production use |
| S04 | TimeNL Roughtime profile and software | https://nts.time.nl/ | SIDN Labs TimeNL NTS server | SIDN Labs | 2026-09-13T13:21:40.546Z | Not stated | Official HTML | TimeNL Roughtime draft-12, Tanner Ryan implementation v1.14.0, experimental/pilot risk, endpoint/key | Yes | `timenl-nts.html`, `980fd73b...75d8` | Current; expressly experimental and at-own-risk, but not an explicit production prohibition |
| S05 | Provider provisioning and dependency cross-check | https://github.com/cloudflare/roughtime/blob/master/ecosystem.md | The Roughtime ecosystem | Cloudflare | 2026-09-13T13:21:42.023Z | Commit 460d233, 2026-04-20 | Official repository text | roughtime.se provisioning; time.txryan.com upstreams, software, service statement | No for these operators | `cloudflare-roughtime-ecosystem.md`, `b8be454f...a429` | High-quality ecosystem record; not permission or root-control evidence |
| S06 | Published server identity list | https://github.com/cloudflare/roughtime/blob/master/ecosystem.json | Roughtime ecosystem server list | Cloudflare | 2026-09-13T13:21:43.301Z | Not separately established | Official repository JSON | Public server names, keys, endpoints | No for these operators | `cloudflare-roughtime-ecosystem.json`, `e2526273...53b5` | Cross-check only |
| S07 | Tanner software lineage and protocol behavior | https://github.com/tannerryan/roughtime | tannerryan/roughtime README | Tanner Ryan | 2026-09-13T13:21:44.286Z | Commit 56b346a, 2026-09-07 | Official repository text | Drafts 01-19, server behavior, TYPE/Merkle compatibility, time.txryan example | Yes for software/time.txryan | `tannerryan-roughtime-readme.md`, `7b6d7a38...9a3f` | Software facts only; does not establish control independence |
| S08 | Tanner ecosystem identities | https://github.com/tannerryan/roughtime/blob/main/ecosystem.json | Tanner Roughtime ecosystem | Tanner Ryan | 2026-09-13T13:21:45.067Z | Not separately established | Official repository JSON | Provider keys/endpoints and common software ecosystem | Yes for Tanner material | `tannerryan-roughtime-ecosystem.json`, `b7ad4428...ebdf` | Cross-check only |
| S09 | TimeNL current source | https://github.com/SIDN/TimeNL/blob/master/index_en.html | TimeNL index_en.html | SIDN | 2026-09-13T13:21:45.847Z | 2026-09-04 | Official repository source | Current operator-controlled page source and Roughtime identity | Yes | `sidn-timenl-index-en.html`, `0068d671...bb9` | Current source capture |
| S10 | TimeNL Roughtime introduction | https://github.com/SIDN/TimeNL/commit/462312aec160c3ab34db92a2003aebe4eba86ed1 | Hello Roughtime | SIDN | 2026-09-13T13:24:08.139Z | 2026-03-01T14:46:17Z | Official commit JSON | Identifies the commit that introduced TimeNL Roughtime | Yes | `sidn-timenl-roughtime-introduction-commit.json`, `6b4cad04...1992` | Authenticated Git history, not a root-secret-control statement |
| S11 | TimeNL historical continuity | https://raw.githubusercontent.com/SIDN/TimeNL/462312aec160c3ab34db92a2003aebe4eba86ed1/index_en.html | Historical TimeNL index_en.html | SIDN | 2026-09-13T13:24:08.855Z | 2026-03-01T14:46:17Z | Official historical source | Same provider name, endpoint, root key, pilot state, and SIDN page | Yes | `sidn-timenl-index-en-2026-03-01.html`, `aa981fcd...ecd1` | Establishes 196-day identity continuity to assessment date; root-secret controller is not explicit |
| S12 | TimeNL current source chronology | https://github.com/SIDN/TimeNL/commit/98bd37e401797bf279f94f1874d9c5c4cd6f5ff9 | Current index_en.html commit | GitHub/SIDN | 2026-09-13T13:32:13.455Z | 2026-09-04T11:01:52Z | Official commit API JSON | Completes the dated continuity endpoints with the 2026-03-01 introduction commit | Yes | `sidn-timenl-current-index-commit.json`, `7e27e325...65ac` | Exact current commit retained; unrelated history omitted |
| S13 | Current protocol revision | https://www.ietf.org/archive/id/draft-ietf-ntp-roughtime-19.txt | Roughtime draft-19 | IETF | 2026-09-13T13:21:47.211Z | 2026-03-17 | Standard text | Current draft bytes and Experimental intended status | Yes | `ietf-roughtime-draft-19.txt`, `68076589...d533` | Standards source, not provider permission |
| S14 | Standards-transition status | https://datatracker.ietf.org/doc/draft-ietf-ntp-roughtime/ | Roughtime datatracker status | IETF | 2026-09-13T13:25:35.561Z | Last updated 2026-03-30; revision 2026-03-17 | Official status HTML | Active draft-19, intended Experimental, IESG approved, RFC Editor queue | Yes | `ietf-roughtime-datatracker-status.html`, `6320b81d...ae4a` | Current retrieval; RFC publication not yet complete |
| S15 | roughtime.se accountable operator attribution | https://www.netnod.se/blog/roughtime-securing-time-iot-devices | Roughtime: securing time for IoT devices | Netnod | 2026-09-13T13:25:36.633Z | 2024-08-27 | Operator-adjacent official HTML | Marcus Dansarie identified as Roughtime co-author/developer; complements official RIPE material attributing roughtime.se to him | No | `netnod-roughtime-iot.html`, `a2213e06...8c61` | Supports accountable-person attribution, not root-secret custody |
| S16 | Cloudflare ecosystem source time | https://api.github.com/repos/cloudflare/roughtime/commits?path=ecosystem.md&per_page=1 | ecosystem.md latest commit | GitHub/Cloudflare | 2026-09-13T13:25:38.289Z | 2026-04-20T23:36:33Z | Official commit JSON | Dates the provider provisioning text | No for providers | `github-cloudflare-ecosystem-latest-commit.json`, `2e08746c...b0e1` | Freshness provenance only |
| S17 | Tanner README source time | https://api.github.com/repos/tannerryan/roughtime/commits?path=README.md&per_page=1 | README latest commit | GitHub/Tanner Ryan | 2026-09-13T13:25:38.867Z | 2026-09-07T23:54:18Z | Official commit JSON | Dates current Tanner software documentation | Yes for Tanner software | `github-tannerryan-readme-latest-commit.json`, `bd904dd9...b9b1` | Software freshness only |
| S18 | Endpoint/root/DNS dependencies | https://cloudflare-dns.com/dns-query | Public DNS JSON | Cloudflare 1.1.1.1 | 2026-09-13T13:22:22.950Z through 13:22:30.773Z | Query-time data | DNS metadata | A, AAAA, TXT, NS, SOA, and conventional SRV queries for the three identities | No | 18 `dns-*.json` captures; individual hashes in `SHA256SUMS.txt` | DNS only; no Roughtime endpoint traffic; conventional SRV names returned NXDOMAIN |
| S19 | ASN/hosting attribution | https://stat.ripe.net/docs/data_api#prefix-overview | RIPEstat prefix overview | RIPE NCC | 2026-09-13T13:22:57.004Z through 13:23:03.561Z | Query-time data | BGP/RIR metadata | AS1880/STUPI, AS16276/OVH, AS1140/SIDN for IPv4 and IPv6 prefixes | No | 6 `ripe-prefix-*.json` captures; individual hashes in `SHA256SUMS.txt` | Route-origin/holder evidence, not application control or availability proof |
| S20 | roughtime.se accountable operator | https://www.ripe.net/media/documents/RIPE_Open_House_May_2024_Netnod_Roughtime_v.1.pdf | RIPE Open House May 2024: Netnod Roughtime | RIPE NCC / Netnod | 2026-09-13T13:35:32.608Z | May 2024 | Official presentation | Explicitly lists `Marcus Dansarie: roughtime.se` | No | `ripe-open-house-2024-netnod-roughtime.pdf`, `b8958952...7bff` | Strong accountable-operator attribution; not secret-custody evidence |

Source-register count: 20 logical entries. Retained evidence captures with individual SHA256 entries: 42.

## DNS metadata

| Provider | Query UTC | Resolver | Results and TTL |
| --- | --- | --- | --- |
| roughtime.se | 2026-09-13T13:22:22.950Z-13:22:25.557Z | Cloudflare 1.1.1.1 DoH | A `192.36.143.134` TTL 7200; AAAA `2001:440:1880:7373::2` TTL 7200; TXT exact root key TTL 300; NS `ns1/ns2.loopiagroup.com` TTL 3600; SOA TTL 86400; `_roughtime._udp.roughtime.se` SRV NXDOMAIN with authority TTL 2560 |
| time.txryan.com | 2026-09-13T13:22:26.234Z-13:22:29.105Z | Cloudflare 1.1.1.1 DoH | A `148.113.167.187` TTL 900; AAAA `2607:5300:205:200::a806` TTL 900; TXT exact root key TTL 900; `txryan.com` NS `ns.txryan.com/.ca/.org` TTL 10800; SOA TTL 10800; conventional SRV NXDOMAIN with authority TTL 3600 |
| TimeNL-Roughtime | 2026-09-13T13:22:29.683Z-13:22:30.773Z | Cloudflare 1.1.1.1 DoH | A `94.198.159.11` TTL 123; AAAA `2a00:d78:0:712:94:198:159:11` TTL 123; TXT exact root key TTL 123; `time.nl` NS `ns1/ns2.sidn.nl` and `ns1/ns2.sidnlabs.nl` TTL 3600; SOA TTL 3600; conventional SRV NXDOMAIN with authority TTL 300 |

All retained DNS responses set the resolver's authenticated-data flag. This is a recorded resolver result, not an independent DNSSEC validation performed by this review.

## Provider assessments

### roughtime.se

| Gap | Status | Evidence and limitation |
| --- | --- | --- |
| Current provider identity | CONFLICT_FOUND | Endpoint `roughtime.se:2002/udp`, root key, STUPI hosting, AS1880, and atomic-clock source are current. The official page now declares draft-19, while the repository candidate still freezes `operator_declared_protocol = draft-ietf-ntp-roughtime-15`. The shared wire code covers drafts 14-19, but the exact declared-profile field still requires versioned reconciliation. |
| Production-use permission | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED | “Feel free to use ... as needed” expressly covers synchronization and timestamping, but does not expressly bind automated production use or the frozen projected volume. |
| Production prohibition | SATISFIED_BY_CURRENT_PUBLIC_EVIDENCE | No provider-specific production prohibition was found. This is not affirmative permission. |
| Root-secret control | PARTIALLY_SATISFIED | Current root key and accountable-person attribution exist; secret custody/control is not stated. |
| Delegation/issuance control | INSUFFICIENT_EVIDENCE | Operator, host, and software facts do not establish who controls online delegation or issuance. |
| Hosting/DNS/software/upstream | SATISFIED_BY_CURRENT_PUBLIC_EVIDENCE | AS1880/STUPI, Loopia DNS, `roughtimed`, and direct atomic-clock connection are published. These are dependency facts, not control independence. |
| Standards transition | CONFLICT_FOUND | Operator declaration changed from repository draft-15 to current draft-19. A profile review is required before any live plan. |

Operator contact required: `YES`.

### time.txryan.com

| Gap | Status | Evidence and limitation |
| --- | --- | --- |
| Current provider identity | SATISFIED_BY_CURRENT_PUBLIC_EVIDENCE | Tanner Ryan's current page binds endpoint `time.txryan.com:2002`, exact root key, IPv4/IPv6, AS16276/OVH, and Tanner's implementation. |
| Production-use permission | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED | Individual clients are expressly allowed and high-volume infrastructure requires contact. Automated low-volume production use and the project's exact projected volume are not explicit. |
| Production prohibition | SATISFIED_BY_CURRENT_PUBLIC_EVIDENCE | No provider-specific production prohibition was found. The Cloudflare repository's general warning is not a Tanner operator prohibition. |
| Root-secret control | PARTIALLY_SATISFIED | Tanner is the accountable operator and publishes the key and software; root-secret custody/control is not explicit. |
| Delegation/issuance control | PARTIALLY_SATISFIED | Tanner's server implementation and operator role are attributable, but public evidence does not explicitly identify issuance-control authority. |
| Hosting/DNS/software/upstream | SATISFIED_BY_CURRENT_PUBLIC_EVIDENCE | AS16276/OVH, operator-branded DNS, Tanner software, and stratum-1 GNSS/NIST/NRC upstream description are current. |
| Standards transition | SATISFIED_BY_CURRENT_PUBLIC_EVIDENCE | Current Tanner material covers IETF drafts through 19 and documents shared-wire TYPE/Merkle behavior. Exact event profile still requires a later qualification review. |

Operator contact required: `YES`.

### TimeNL-Roughtime

| Gap | Status | Evidence and limitation |
| --- | --- | --- |
| Current provider identity | PARTIALLY_SATISFIED | SIDN Labs currently publishes the exact endpoint/key and dedicated draft-12/Tanner v1.14.0 identity, but still calls the service pilot/experimental and warns that the port/protocol may change. |
| Production-use permission | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED | TimeNL invites public use and publishes fair-use guidance, but Roughtime-specific automated low-volume production permission is not explicit. NTP/vendor rules cannot be silently transferred to the Roughtime pilot. |
| Production prohibition | SATISFIED_BY_CURRENT_PUBLIC_EVIDENCE | No explicit Roughtime production prohibition was found; experimental/at-own-risk wording is a risk, not affirmative permission. |
| Pilot status | SATISFIED_BY_CURRENT_PUBLIC_EVIDENCE | Current first-party pages expressly label Roughtime pilot/experimental and subject to change. |
| 90-day continuity | PARTIALLY_SATISFIED | Official SIDN Git history shows the same name, endpoint, key, operator page, and pilot status from 2026-03-01 to 2026-09-13, 196 days. The root-secret control domain is not affirmatively identified, so the frozen continuity gate is not fully closed. |
| Root-secret control | PARTIALLY_SATISFIED | SIDN Labs is the service operator and publishes the key, but secret custody/control is not explicit. |
| Delegation/issuance control | INSUFFICIENT_EVIDENCE | Tanner software lineage does not prove that Tanner controls TimeNL issuance; SIDN operation does not itself prove the exact issuance controller. |
| Hosting/DNS/software/upstream | SATISFIED_BY_CURRENT_PUBLIC_EVIDENCE | AS1140/SIDN, SIDN/SIDN Labs DNS, Tanner v1.14.0 software, and TimeNL's multi-source clocks are published. |
| Standards transition | PARTIALLY_SATISFIED | Dedicated page remains draft-12 while the IETF document is in the RFC Editor queue as Experimental; TimeNL expressly warns of possible changes. |

Operator contact required: `YES`.

## Permission matrix

| Provider | Public-use statement | Automated use explicit | Low-volume production explicit | Rate/use boundary | Status |
| --- | --- | --- | --- | --- | --- |
| roughtime.se | Broad invitation for synchronization, timestamping, testing, and development | No | No | No published Roughtime-specific cap located | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED |
| time.txryan.com | Individual clients allowed | No | No | High-volume infrastructure requires contact | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED |
| TimeNL-Roughtime | Public pilot config and general TimeNL invitation/fair-use guidance | No | No | General NTP fair-use language; Roughtime-specific cap absent | OWNER_OR_OPERATOR_EVIDENCE_REQUIRED |

## Control-independence matrix

| Provider | Accountable operator | Root public key | Root-secret controller | Delegation/issuance controller | Hosting controller | DNS controller | Software maintainer | Upstream time controller | Evidence strength |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| roughtime.se | Marcus Dansarie / roughtime.se | `S3Az...sehI=` | Not explicitly published | Not explicitly published | STUPI AB / AS1880 | Loopia Group | Marcus Dansarie (`roughtimed`) | STUPI-connected atomic clocks; exact control not published | PARTIAL_EVIDENCE |
| time.txryan.com | Tanner Ryan | `iBVj...2WA=` | Not explicitly published | Tanner operation is attributable, exact authority not explicit | OVH / AS16276 | Tanner-branded authoritative DNS; underlying hosting not fully assessed | Tanner Ryan | Published GNSS/NIST/NRC stratum-1 set; exact control not published | PARTIAL_EVIDENCE |
| TimeNL-Roughtime | SIDN Labs / TimeNL | `v2Ci...kbiY=` | Not explicitly published | Not explicitly published | SIDN / AS1140 | SIDN and SIDN Labs | Tanner Ryan v1.14.0; deployed by TimeNL | SIDN Labs/TimeNL multi-source clock infrastructure | PARTIAL_EVIDENCE |

The public evidence supports distinct accountable operators, root public keys, ASNs, hosting organizations, and DNS namespaces. It does not affirmatively prove distinct root-secret and issuance-control domains for every quorum pair. Therefore the frozen pairwise independence gate remains `OWNER_OR_OPERATOR_EVIDENCE_REQUIRED`; no row is upgraded to `AFFIRMATIVE_INDEPENDENCE_EVIDENCE`.

## Common-dependency matrix

| Dependency | roughtime.se | time.txryan.com | TimeNL-Roughtime | Potential simultaneous vote impact | Evidence | Result |
| --- | --- | --- | --- | --- | --- | --- |
| Software | `roughtimed` | `tannerryan/roughtime` | `tannerryan/roughtime` v1.14.0 | 2 | First-party and ecosystem sources | POTENTIAL_BLOCKING_COMMON_DEPENDENCY |
| Hosting | STUPI AB | OVH | SIDN | 1 per named dependency | RIPEstat and official pages | SATISFIED_BY_CURRENT_PUBLIC_EVIDENCE |
| ASN | AS1880 | AS16276 | AS1140 | 1 | RIPEstat IPv4/IPv6 results | SATISFIED_BY_CURRENT_PUBLIC_EVIDENCE |
| DNS | Loopia Group | Tanner-branded authoritative names | SIDN/SIDN Labs | No shared authority discovered; underlying hosting incomplete | DNS NS/SOA responses | PARTIALLY_SATISFIED |
| Root control | Unknown | Unknown | Unknown | Cannot determine | Public keys differ; controllers not stated | INSUFFICIENT_EVIDENCE |
| Issuance control | Unknown | Attributable to Tanner operation but not explicit | Unknown | Cannot determine | Public operator/software facts | INSUFFICIENT_EVIDENCE |
| Upstream time | Direct atomic clocks | GNSS/NIST/NRC-backed stratum 1 | GNSS/Galileo/DCF77/VSL/other atomic clocks | Some source-family overlap possible; no single two-vote controller established | Official/ecosystem descriptions | PARTIALLY_SATISFIED |
| Control plane | Unknown | Unknown | Unknown | Cannot determine | No affirmative administrative-control disclosures | INSUFFICIENT_EVIDENCE |
| Operator | Marcus Dansarie / roughtime.se | Tanner Ryan | SIDN Labs | Distinct named operators; exact root/issuance authority unresolved | First-party and official institutional sources | PARTIALLY_SATISFIED |

The shared Tanner software lineage can plausibly affect two votes through a common implementation defect, so it is conservatively marked `POTENTIAL_BLOCKING_COMMON_DEPENDENCY`. Frozen criteria say software-family correlation alone is not a confirmed blocking control dependency. No confirmed dependency capable of creating accepted false receipts or suppressing two votes for the full evidence window was established.

## Continuity and metadata freshness

| Item | Status | Finding |
| --- | --- | --- |
| TimeNL identity continuity | PARTIALLY_SATISFIED | Same official name, endpoint, root key, operator page, and pilot state persisted for 196 days; root-control-domain continuity remains unproven |
| Current operator metadata age | SATISFIED_BY_CURRENT_PUBLIC_EVIDENCE | All current page/DNS/routing captures were retrieved on 2026-09-13, within the 90-day interval |
| Immediate pre-ProviderProfile review | CURRENT_EXTERNAL_METADATA_REQUIRED | This review is a candidate input only; frozen criteria require another immediate read-only review before final profile freeze |
| Live interoperability freshness | NOT_APPLICABLE | No live event was authorized or performed; the separate 30-day live-event rule remains open |
| Standards transition | PARTIALLY_SATISFIED | IETF draft-19 is IESG-approved in the RFC Editor queue with intended Experimental status; provider profiles must not migrate silently |

## Unresolved governance gaps

1. `roughtime.se` draft-15 candidate versus current official draft-19 declaration must be reconciled through a versioned profile review.
2. All three providers still lack explicit evidence covering the project's projected low-volume automated production use.
3. All three providers lack affirmative root-secret and delegation/issuance-control disclosures sufficient for pairwise independence.
4. TimeNL's 196-day public identity continuity does not prove continuity of the root-secret control domain.
5. Tanner software shared by time.txryan.com and TimeNL remains a two-vote potential common-mode risk requiring threshold review.
6. Control-plane and exact upstream-control relationships remain insufficiently evidenced.
7. Immediate current metadata review must be repeated before any final ProviderProfile freeze.
8. No live repeatability evidence was created or authorized by this review.

## Minimal operator questions

Operator contact is required for every provider, but no contact was made. The minimum questions for each are:

1. Do you permit this project's stated maximum volume of low-volume automated production Roughtime queries?
2. Who controls the long-term root secret?
3. Who controls delegation and online timestamp issuance?
4. Is any other organization or control plane able to change the root, signer, endpoint, or issuance behavior?
5. Is the service intended to remain available for production use, and are there applicable rate or acceptable-use limits?

For roughtime.se, also ask whether draft-19 supersedes the published draft-15 profile without any endpoint/key or acceptance-semantic change. For TimeNL, also ask whether the pilot may be used for automated production, who has controlled its root since 2026-03-01, and what transition/retirement plan applies.

## Impact on the next qualification step

```text
LIVE_REPEATABILITY_AUTHORIZATION_RECOMMENDATION = NOT_READY_TO_REQUEST
```

The recommendation is not ready because permission, positive root/issuance independence, TimeNL root-control continuity, common-dependency threshold review, and the roughtime.se profile conflict remain unresolved. The successful retained rehearsal does not alter this decision.

No paid source was used, no purchase was made, and no criterion was found to require a paid data source before free operator clarification and public evidence avenues are exhausted.

Local consistency verification recomputed all 42 evidence hashes with zero mismatch, recomputed the frozen criteria SHA256 exactly, and ran the reviewed offline Roughtime production-qualification, hardening, verifier, execution, rehearsal, control, and plan test subset: `143 passed, 6 skipped, 9 subtests passed`.

## Final boundary

The temporary metadata-research authorization is consumed by completion of this review and is not reusable. Any future metadata refresh or live repeatability event requires new, separate, exact authorization.

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production qualified provider count = 0
PRODUCTION_QUALIFIED = NO
production qualification execution = NOT PERFORMED
provider qualification state change = NONE
network_authorized = false
```
