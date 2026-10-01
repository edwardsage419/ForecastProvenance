from __future__ import annotations

from dataclasses import dataclass

NONCE_DOMAIN = b"FPP_ROUGHTIME_V2\x00"
NONCE_PROFILE = "FPP_ROUGHTIME_NONCE_V2"
NONCE_LENGTH = 32
CLIENT_RANDOM_LENGTH = 32

MAX_ATTEMPTS_PER_PROVIDER = 2
TIMEOUT_PER_ATTEMPT_SECONDS = 2
RETRY_BACKOFF_INITIAL_SECONDS = 1
RETRY_BACKOFF_FACTOR = "1.5"
RETRY_BACKOFF_MAX_SECONDS = 86400

PACKET_PROFILE = "STANDARD_1024_BODY"
TRANSPORT_PROFILE = "UDP_ONLY"

VERIFIER_REPOSITORY = "github.com/tannerryan/roughtime"
VERIFIER_TAG = "v1.27.0"
VERIFIER_COMMIT = "56b346a16cd7e8317bb0d24f1ec15549cf93a4c9"

FAILURE_CODES_V1_1 = frozenset({
    "BACKOFF_ACTIVE",
    "DNS_FAILURE",
    "TRANSPORT_TIMEOUT",
    "TRANSPORT_ERROR",
    "MALFORMED_RESPONSE",
    "WIRE_VERSION_MISMATCH",
    "ROOT_KEY_MISMATCH",
    "DELEGATION_INVALID",
    "SIGNATURE_INVALID",
    "NONCE_MISMATCH",
    "MERKLE_PROOF_INVALID",
    "MIDPOINT_OUTSIDE_DELEGATION",
    "RADIUS_INVALID",
    "UPPER_BOUND_AFTER_DEADLINE",
    "RAW_EVIDENCE_INCOMPLETE",
    "RETRY_STATE_INVALID",
    "PLAN_MISMATCH",
    "AUTHORIZATION_MISMATCH",
    "VERIFIER_ERROR",
})
FAILURE_CODES_V1_2 = FAILURE_CODES_V1_1 | frozenset({
    "RESPONSE_SOURCE_MISMATCH",
    "TYPE_MISMATCH",
})
# Backward-compatible public name for callers that need the current vocabulary.
FAILURE_CODES = FAILURE_CODES_V1_2
VERIFIED_NONQUALIFYING_CODES = frozenset({
    "RADIUS_INVALID",
    "UPPER_BOUND_AFTER_DEADLINE",
})



@dataclass(frozen=True)
class RoughtimeProvider:
    provider_id: str
    operator_identity: str
    host: str
    port: int
    transport: str
    operator_declared_protocol: str
    wire_version_hex: str
    offered_version_hex: str
    wire_profile: str
    require_type: bool
    require_srv: bool
    root_public_key_base64: str


PROVIDERS = (
    RoughtimeProvider(
        provider_id="roughtime.se",
        operator_identity="Marcus Dansarie / roughtime.se hosted by STUPI AB",
        host="roughtime.se",
        port=2002,
        transport="udp",
        operator_declared_protocol="draft-ietf-ntp-roughtime-15",
        wire_version_hex="0x8000000c",
        offered_version_hex="0x8000000c",
        wire_profile="IETF_D14_D19_TYPED_SHARED_WIRE_ACCEPT_BOTH_MERKLE_ORDERS",
        require_type=True,
        require_srv=True,
        root_public_key_base64="S3AzfZJ5CjSdkJ21ZJGbxqdYP/SoE8fXKY0+aicsehI=",
    ),
    RoughtimeProvider(
        provider_id="time.txryan.com",
        operator_identity="Tanner Ryan",
        host="time.txryan.com",
        port=2002,
        transport="udp",
        operator_declared_protocol="IETF-Roughtime public service",
        wire_version_hex="0x8000000c",
        offered_version_hex="0x8000000c",
        wire_profile="IETF_D14_D19_TYPED_SHARED_WIRE_ACCEPT_BOTH_MERKLE_ORDERS",
        require_type=True,
        require_srv=True,
        root_public_key_base64="iBVjxg/1j7y1+kQUTBYdTabxCppesU/07D4PMDJk2WA=",
    ),
    RoughtimeProvider(
        provider_id="TimeNL-Roughtime",
        operator_identity="SIDN Labs / TimeNL",
        host="rough.time.nl",
        port=2002,
        transport="udp",
        operator_declared_protocol="draft-ietf-ntp-roughtime-12 pilot",
        wire_version_hex="0x8000000c",
        offered_version_hex="0x8000000c",
        wire_profile="IETF_D12_D13_UNTYPED_SHARED_WIRE_NODE_FIRST",
        require_type=False,
        require_srv=True,
        root_public_key_base64="v2CievhgKsxzlWPwIkYFUXeA51Akhkv5uhJCj1/kbiY=",
    ),
)
PROVIDER_ORDER = tuple(provider.provider_id for provider in PROVIDERS)
PROVIDER_BY_ID = {provider.provider_id: provider for provider in PROVIDERS}
