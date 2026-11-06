"""T08 formula-free public authentication interface, blocked by independent G02.

No signing contract has been independently supplied/closed for this task.
Caller labels cannot close it. Inputs are deliberately opaque: no projection,
message construction, key handling, cryptographic/backend/resolver invocation.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class InitialPublicAuthentication:
    status: str = 'UNKNOWN'
    reason_codes: tuple = ('BLOCKED_BY_G02', 'INDEPENDENT_INITIAL_SIGNING_CONTRACT_NOT_ESTABLISHED')
    message: bytes | None = None
    message_digest: str | None = None
    prospective_eligible: bool = False
    real_genesis_readiness: str = 'NOT_ESTABLISHED'
    protocol_state_change: str = 'NONE'


def verify_initial_acceptance_public(*, basis, acceptance, resolver, signing_contract=None, backend=None):
    """Fail closed even for caller asserted CLOSED/model/other-family contracts."""
    return InitialPublicAuthentication()
