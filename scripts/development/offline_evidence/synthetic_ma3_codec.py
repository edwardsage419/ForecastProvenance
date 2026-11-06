"""Fixed-sentinel MA3 codec experiment; cannot accept actual project inputs.

No key, signature, carrier, authority selection or public authentication exists
here. All identity/digest gates run before any envelope or frame is serialized.
"""
import hashlib
from pathlib import Path
import re
from types import ModuleType

HERE = Path(__file__).resolve().parent
path = HERE/'signing_profile.py'
raw = path.read_bytes()
if hashlib.sha256(raw).hexdigest() != 'ea28e595ce0b8d6996ca7dfbf40aa42a60bee19f07cb4755427032e4c74149ff':
    raise RuntimeError('D191_FIXED_PROFILE_CONSUMER_CHANGED')
_P = ModuleType('d191_fixed_profile_consumer'); _P.__file__ = str(path)
exec(compile(raw, str(path), 'exec'), _P.__dict__)
_C = _P.canonical


def _ref(name):
    identity = 'SYNTHETIC_TEST_ONLY:D191:'+name
    return {'object_id': identity,
            'content_sha256': hashlib.sha256(('D191_REF/'+identity).encode('ascii')).hexdigest()}


def encode_synthetic_case(case_bytes, profile_bytes):
    """Encode only the fixed D191 namespace; no operational switch or I/O.

    The non-key digest and exact sentinel references intentionally cannot serve
    as actual root/key/report evidence. This is not a signing/verifier API.
    """
    if type(case_bytes) is not bytes or len(case_bytes) > 1048576:
        raise ValueError('D191_CASE_BYTES_OR_SIZE')
    checked = _P.consume(profile_bytes, None)
    if checked['profile_content_status'] != 'OBSERVED':
        raise ValueError('D191_PROFILE_NOT_EXACT_CANDIDATE')
    try:
        case = _C.parse_json_strict(case_bytes)
    except (ValueError, TypeError, RecursionError) as error:
        raise ValueError('D191_STRICT_CASE_JSON') from error
    if type(case) is not dict or set(case) != {'scope', 'context', 'unsigned'}:
        raise ValueError('D191_CASE_FIELDS')
    if case['scope'] != 'D191_SYNTHETIC_TEST_ONLY':
        raise ValueError('D191_SYNTHETIC_SCOPE_REQUIRED')
    profile = _C.parse_json_strict(profile_bytes)
    rules = profile['signing_rules']
    context, unsigned = case['context'], case['unsigned']
    if type(context) is not dict or set(context) != set(rules['context_fields']):
        raise ValueError('D191_CONTEXT_FIELDS')
    if type(unsigned) is not dict or set(unsigned) != set(rules['unsigned_fields']):
        raise ValueError('D191_UNSIGNED_FIELDS')
    expected_context = dict(rules['context_constants'],
        project_id='SYNTHETIC_TEST_ONLY:D191_PROJECT', actor_id='SYNTHETIC_TEST_ONLY:D191_ACTOR',
        public_key_sha256=hashlib.sha256(b'D191_NOT_A_REAL_PUBLIC_KEY').hexdigest(),
        effective_scope_ref=_ref('ROOT'), validator_contract_ref=_ref('VALIDATOR'))
    if context != expected_context:
        raise ValueError('D191_NON_SYNTHETIC_OR_MISMATCHED_CONTEXT')
    for field, name in [('acceptance_rule_ref', 'RULE'), ('authority_ref', 'ROOT'),
                        ('bootstrap_governance_root_ref', 'ROOT'), ('candidate_manifest_ref', 'MANIFEST')]:
        if unsigned[field] != _ref(name):
            raise ValueError('D191_NON_SYNTHETIC_OR_MISMATCHED_REF')
    if unsigned['object_type'] != 'ManifestAcceptance' or unsigned['schema_version'] != '3.0':
        raise ValueError('D191_MA3_TYPE_VERSION_REQUIRED')
    if unsigned['required_validation_report_refs'] != [_ref('REPORT_'+str(i)) for i in range(5)]:
        raise ValueError('D191_EXACT_SORTED_FIVE_SYNTHETIC_REFS_REQUIRED')
    decision, blockers, reasons = unsigned['decision'], unsigned['blocking_finding_refs'], unsigned['reason_codes']
    if decision not in ('ACCEPT', 'REJECT'):
        raise ValueError('D191_DECISION')
    allowed_blockers = [_ref('BLOCKER_'+str(i)) for i in range(4)]
    if (type(blockers) is not list or len(blockers) > 4
            or any(row not in allowed_blockers for row in blockers)):
        raise ValueError('D191_BLOCKERS_NOT_SYNTHETIC')
    identities = [(row['object_id'], row['content_sha256']) for row in blockers]
    if identities != sorted(identities) or len(set(identities)) != len(identities):
        raise ValueError('D191_NONCANONICAL_BLOCKER_SET')
    if decision == 'ACCEPT' and blockers:
        raise ValueError('D191_ACCEPT_HAS_BLOCKERS')
    if (type(reasons) is not list or not 1 <= len(reasons) <= 32
            or any(type(reason) is not str or len(reason) > 128 or
                   re.fullmatch('SYNTHETIC_TEST_ONLY_D191_[A-Z0-9_]+', reason) is None for reason in reasons)):
        raise ValueError('D191_REASON_NOT_SYNTHETIC')
    if reasons != sorted(reasons) or len(set(reasons)) != len(reasons):
        raise ValueError('D191_NONCANONICAL_REASON_SET')
    # No serialization occurs until every actual-input exclusion above passes.
    envelope = {'acceptance_payload': unsigned, 'algorithm': rules['algorithm'],
                'context': context, 'signing_profile': rules['signing_profile']}
    encoded = _C.canonical_json(envelope)
    if len(encoded) >= 2**64:
        raise ValueError('D191_LENGTH_OVERFLOW')
    domain = rules['framing']['domain_ascii'].encode('ascii')
    framed = domain+b'\x00'+len(encoded).to_bytes(8, 'big')+encoded
    return {'scope': 'SYNTHETIC_CODEC_OBSERVATION', 'envelope_bytes': encoded, 'frame_bytes': framed,
            'public_authentication': 'NOT_IMPLEMENTED', 'signed_or_carrier_created': False,
            'independent_authority_and_applicability': 'NOT_ESTABLISHED', 'real_admission': 'NOT_READY',
            'prospective_eligible': False, 'protocol_state_change': 'NONE'}
