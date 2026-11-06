"""Two proposed D185 typed uses; no rule selection, message or authority."""
import hashlib
from pathlib import Path
from types import ModuleType

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT/'docs/development/mainline-execution-2026-10-19-signing-profile-content-rev-001'
PROFILE_RAW = '870ea01830e8000949f01dc060405d2f8536ad651d642aaf51bde6c029063472'
PROFILE_REF = {'object_id': 'signing-profile:genesis-initial-ma3:a1',
               'content_sha256': '339833cdba8a9143d6ae74c53dd833d21e9a6f23ddc144272760e6b65d705166'}


def _fixed(path, digest):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise RuntimeError('D189_FIXED_DEPENDENCY_CHANGED')
    return raw


path = ROOT/'src/forecast_trust_core/canonical.py'
canonical = ModuleType('d189_fixed_canonical')
exec(compile(_fixed(path, 'f9ef49579a5c54757c6660d377275a0ed5f8afdf646f33130651a711005ac9ba'),
             str(path), 'exec'), canonical.__dict__)
PROFILE_SCHEMA = canonical.parse_json_strict(_fixed(PACKAGE/'PROFILE_SCHEMA_CANDIDATE.json',
    '4bbea6a34351178e4adefe5c31b04e8a2eb4cc9e08bbfadbe8c164d066f68fe1'))
RULE_SCHEMA = canonical.parse_json_strict(_fixed(ROOT/'schemas/acceptance_policy_v3.schema.json',
    'dc861a3da1799f7f7888f15d6b6da97fdb11bb9de6f83e2a081e375b9f4d5d72'))
for schema in (PROFILE_SCHEMA, RULE_SCHEMA):
    Draft202012Validator.check_schema(schema)
PROFILE_VALIDATOR = Draft202012Validator(PROFILE_SCHEMA)
RULE_VALIDATOR = Draft202012Validator(RULE_SCHEMA)


def consume(profile_bytes, rule_bytes=None):
    """Consume exact candidate and optional supplied rule bytes without I/O.

    Even full local consistency is not independent selection, applicability,
    authorization, verification of a signature, or satisfaction of other slots.
    """
    errors, missing = [], []

    def error(code):
        if code not in errors:
            errors.append(code)

    def read(raw, name, validator, identity_key):
        prefix = name.upper()
        if raw is None:
            missing.append(name+'_bytes')
            return None
        if name == 'profile' and (type(raw) is not bytes or hashlib.sha256(raw).hexdigest() != PROFILE_RAW):
            error('PROFILE_RAW_MISMATCH')
        try:
            if type(raw) is not bytes or len(raw) > 1048576:
                raise ValueError('bytes/size')
            obj = canonical.parse_json_strict(raw)
            if type(obj) is not dict:
                raise ValueError('object')
        except (ValueError, TypeError, RecursionError):
            error(prefix+'_JSON_INVALID')
            return None
        if not validator.is_valid(obj):
            error(prefix+'_SHAPE_INVALID')
        try:
            if not canonical.verify_sealed_object(obj):
                error(prefix+'_SEAL_INVALID')
        except (ValueError, TypeError, KeyError, RecursionError):
            error(prefix+'_SEAL_INVALID')
        if obj.get(identity_key) != obj.get('object_id'):
            error(prefix+'_SEMANTIC_ID_MISMATCH')
        return obj

    profile = read(profile_bytes, 'profile', PROFILE_VALIDATOR, 'profile_id')
    rule = read(rule_bytes, 'rule', RULE_VALIDATOR, 'policy_id')
    if profile is not None:
        if {key: profile.get(key) for key in PROFILE_REF} != PROFILE_REF:
            error('PROFILE_FULL_REF_MISMATCH')
    if rule is not None:
        try:
            semantics = rule['rules']['signing_semantics']
            for field in ('profile_ref', 'carrier_profile_ref'):
                if semantics[field] != PROFILE_REF:
                    error('RULE_'+field.upper()+'_MISMATCH')
        except (ValueError, TypeError, KeyError):
            error('RULE_SIGNING_USES_INVALID')
    profile_ok = profile is not None and not any(code.startswith('PROFILE_') for code in errors)
    matched = profile_ok and rule is not None and not errors
    return {'scope': 'EXACT_D185_CONTENT_AND_SUPPLIED_RULE_LOCAL_COMPARISON_ONLY',
            'status': 'REJECTED' if errors else 'MISSING' if missing else 'OBSERVED',
            'verdict': 'REJECT' if errors else 'UNRESOLVED', 'errors': errors, 'missing': missing,
            'profile_content_status': 'OBSERVED' if profile_ok else 'MISSING' if profile_bytes is None else 'REJECTED',
            'proposed_rule_binding_status': 'REJECTED' if errors else 'OBSERVED' if matched else 'MISSING',
            'profile_ref': dict(PROFILE_REF) if profile_ok else None,
            'profile_raw_sha256': PROFILE_RAW if profile_ok else None,
            'rule_raw_sha256': hashlib.sha256(rule_bytes).hexdigest() if rule is not None else None,
            'consumed_sections': ['signing_rules', 'carrier_rules'] if matched else [],
            'operational_bindings_established': 0,
            'independent_authority_and_applicability': 'NOT_ESTABLISHED',
            'effective_boundary': 'NOT_ESTABLISHED', 'public_authentication': 'NOT_ESTABLISHED',
            'separate_verifier_contract': 'NOT_ESTABLISHED', 'complete_profile_inputs': 'NOT_ESTABLISHED',
            'complete_G10': 'NOT_ESTABLISHED', 'real_admission': 'NOT_READY',
            'prospective_eligible': False, 'protocol_state_change': 'NONE'}
