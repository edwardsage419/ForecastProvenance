# Genesis External Time Provider Snapshot

Snapshot date: 2026-09-11
Status: REVIEW INPUT ONLY

This file records current official provider information used to plan non-forecast Genesis rehearsals.

It is not a frozen ProviderProfile and does not make any provider quorum eligible.

A provider becomes eligible only after owner-controlled rehearsal captures and independently verifies the exact response, signer material, policy, time-bound semantics, and required revocation evidence.

## Minimal Genesis v1 provider plan

The minimum operating plan is to qualify two independent RFC 3161 provider groups:

1. FreeTSA.
2. DigiCert.

This satisfies the current design requirement for two independent groups while ensuring at least one RFC 3161 provider because both candidates use RFC 3161.

Cloudflare Roughtime is optional and is not a minimum Genesis dependency.

## FreeTSA RFC 3161

Provider group candidate: `freetsa_rfc3161`

Official endpoint:

```text
https://freetsa.org/tsr
```

FreeTSA's official documentation currently states that its TSA certificate was updated for timestamps from 2026-03-16 and publishes these certificate fingerprints:

```text
TSA certificate SHA256
8bfb0305bb64e2571ca507552ef3245cb1c2fee8728e0ff8689225081ea13467

CA certificate SHA256
2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438
```

Official source:

```text
https://freetsa.org/index_en.php
```

Rehearsal must still capture the exact token signer, included or required chain, policy OID, nonce behavior, accuracy semantics, and revocation material. Published website fingerprints are comparison evidence, not a substitute for token verification.

## DigiCert RFC 3161

Provider group candidate: `digicert_rfc3161`

Official RFC 3161 endpoint:

```text
http://timestamp.digicert.com
```

DigiCert's official knowledge base currently identifies that endpoint for RFC 3161 timestamping and publishes responder certificate-chain material.

DigiCert also states that TSA certificates are updated at least every 15 months. Genesis therefore must not permanently hard-code certificate filenames or a chain merely because they were current during design review.

Official sources:

```text
https://knowledge.digicert.com/general-information/rfc3161-compliant-time-stamp-authority-server
https://knowledge.digicert.com/solution/troubleshooting-timestamping-problems
```

The endpoint uses HTTP transport in the provider's current documentation. Genesis trust therefore comes from successful RFC 3161 token signature, subject-imprint, nonce, chain, policy, and time-bound verification. Transport metadata is retained as operational evidence and is not itself the trust proof.

Rehearsal must freeze the exact response signer and chain actually observed and verify that the accepted time-bound semantics apply to that exact token and policy.

## Cloudflare Roughtime

Provider group candidate: `cloudflare_roughtime`

Current official service address:

```text
roughtime.cloudflare.com:2003
```

Current official root public key snapshot:

```text
0GD7c3yP8xEc4Zl2zeuN2SlLvDVVocjsPSL8/Rl/7zg=
```

Official source:

```text
https://developers.cloudflare.com/time-services/roughtime/usage/
```

Cloudflare currently labels the service beta and explicitly warns that the root key may change.

Genesis v1 therefore treats Roughtime as optional. It can become quorum eligible only after a successful nonce-bound rehearsal freezes the exact protocol implementation, root key, verifier version, and response semantics.

## OpenTimestamps

OpenTimestamps remains the candidate Bitcoin durability layer rather than the precise wall-clock deadline authority.

Official source:

```text
https://opentimestamps.org/
```

The project uses free public calendars for rehearsal submission only. Final Genesis readiness requires retained proof bytes and strong verification against owner-controlled Bitcoin Core under the frozen verifier profile.

## Snapshot expiration rule

This file is a historical design snapshot.

Before any final ProviderProfile is sealed, the project must compare live rehearsal evidence to this snapshot and current official provider information.

A changed endpoint, certificate, root key, policy, or verification behavior is handled as new evidence. The project never edits this snapshot to make past rehearsal evidence look current.