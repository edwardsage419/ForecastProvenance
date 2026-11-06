"""Internal, development-only MA3 byte and local-reference preflight.

This stage has no authorization, message, resolver, loader or backend API.
Independent role/effectivity, full report semantics and runtime applicability
must still be established elsewhere before any real authentication operation.
"""
import hashlib
from jsonschema import Draft202012Validator

from ._initial_acceptance_auth_inputs_v1 import InputSpec, freeze_inputs
from .canonical import parse_json_strict, validate_ref
from .claim_authority_contract_gate_v1 import validate_manifest_acceptance_v3_contract

_REQUIRED = {
    'root': ('BootstrapGovernanceRoot', '1.0'),
    'rule': ('PolicyDefinition', '3.0'),
    'acceptance': ('ManifestAcceptance', '3.0'),
    'manifest': ('TrustedManifest', None),
    'profile': ('InitialAcceptanceSigningProfile', '1.0'),
    'verifier': ('InitialAcceptanceVerifierContract', '1.0'),
}


def preflight_initial_inputs(specs, supplied):
    """Freeze all declared inputs, then inspect local links in the same bytes.

    Specs are finite developer comparison inputs, not an independent universe or
    trust basis. Even an entirely matching synthetic graph grants zero authority.
    Missing references and known failures coexist. No latest/path fallback exists.
    The result's immutable snapshot is reusable by later admitted consumers.
    """
    snapshots = freeze_inputs(specs, supplied)
    failures = [list(item) for item in snapshots.failures]
    missing = list(snapshots.missing)
    objects, index = {}, {}

    def fail(role, code):
        if [role, code] not in failures:
            failures.append([role, code])

    def absent(name):
        if name not in missing:
            missing.append(name)

    for item in snapshots.items:
        if item.object_ref is not None:
            index[item.object_ref] = item.raw
        if item.role not in _REQUIRED:
            continue
        if item.data_format != 'SEALED_JSON':
            fail(item.role, 'REQUIRED_SEALED_INPUT')
            continue
        # freeze_inputs has already enforced byte/depth/seal/raw/full limits.
        obj = parse_json_strict(item.raw)
        kind, version = _REQUIRED[item.role]
        if obj['object_type'] != kind or (version is not None and obj.get('schema_version') != version):
            fail(item.role, 'REQUIRED_TYPE_OR_VERSION_MISMATCH')
            continue
        objects[item.role] = obj
    for role in _REQUIRED:
        if role not in objects:
            absent(role)
    for role, field in [('root', 'bootstrap_root_id'), ('rule', 'policy_id'),
                        ('profile', 'profile_id'), ('verifier', 'contract_id')]:
        if role in objects and objects[role].get(field) != objects[role]['object_id']:
            fail(role, 'SEMANTIC_ID_MISMATCH')
    acceptance = objects.get('acceptance')
    if acceptance is not None:
        try:
            validate_manifest_acceptance_v3_contract(acceptance)
        except (ValueError, TypeError, KeyError):
            fail('acceptance', 'MA3_LOCAL_CONTRACT_INVALID')

    checked = []
    def reference(role, obj, field, target=None):
        value = obj.get(field)
        try:
            if type(value) is not dict:
                raise ValueError('reference')
            validate_ref(value)
        except (ValueError, TypeError, KeyError):
            fail(role, field.upper()+'_INVALID')
            return
        pair = (value['object_id'], value['content_sha256'])
        checked.append([role, field, *pair])
        if pair not in index:
            absent('ref:'+pair[0]+'@'+pair[1])
        if target in objects:
            expected = objects[target]
            if pair != (expected['object_id'], expected['content_sha256']):
                fail(role, field.upper()+'_MISMATCH')

    if acceptance is not None:
        for field, target in [('bootstrap_governance_root_ref', 'root'), ('authority_ref', 'root'),
                              ('acceptance_rule_ref', 'rule'), ('candidate_manifest_ref', 'manifest'),
                              ('signature_ref', None)]:
            reference('acceptance', acceptance, field, target)
        for field in ['required_validation_report_refs', 'blocking_finding_refs']:
            values = acceptance.get(field)
            if type(values) is list:
                for n, value in enumerate(values):
                    reference('acceptance', {field: value}, field)
    if 'root' in objects:
        reference('root', objects['root'], 'acceptance_rule_ref', 'rule')
    if 'rule' in objects:
        try:
            semantics = objects['rule']['rules']['signing_semantics']
            if type(semantics) is not dict:
                raise ValueError('signing_semantics')
        except (ValueError, TypeError, KeyError):
            fail('rule', 'SIGNING_USES_INVALID')
        else:
            for field, target in [('profile_ref', 'profile'), ('carrier_profile_ref', 'profile'),
                                  ('verifier_contract_ref', 'verifier')]:
                reference('rule', semantics, field, target)
    if 'verifier' in objects:
        reference('verifier', objects['verifier'], 'profile_ref', 'profile')
    return {
        'status': 'REJECTED' if failures else 'MISSING' if missing else 'OBSERVED',
        'scope': 'DEVELOPMENT_RESOURCE_AND_LOCAL_REFERENCE_PREFLIGHT_ONLY',
        'failures': failures, 'missing': missing, 'snapshots': snapshots,
        'checked_references': checked,
        'independent_authority_and_applicability': 'NOT_ESTABLISHED',
        'full_report_semantics': 'NOT_CHECKED', 'full_runtime': 'NOT_ESTABLISHED',
        'may_construct_message': False, 'may_load_backend': False,
        'public_authentication': 'NOT_ESTABLISHED', 'real_admission': 'NOT_READY',
        'prospective_eligible': False, 'protocol_state_change': 'NONE',
    }


# Fixed developer definitions; not an independent governing selection.
_CONTRACT_SCHEMAS = {'root': {'path': 'schemas/bootstrap_governance_root_v1.schema.json', 'bytes': 3859, 'sha256': '5eb1ed5cc7944b7af285b53338cf2491978451b2e070e7b17d1d03b85a1c3438'}, 'rule': {'path': 'schemas/acceptance_policy_v3.schema.json', 'bytes': 17344, 'sha256': 'dc861a3da1799f7f7888f15d6b6da97fdb11bb9de6f83e2a081e375b9f4d5d72'}, 'acceptance': {'path': 'schemas/manifest_acceptance_v3.schema.json', 'bytes': 4295, 'sha256': '768b4a1078b01f3e17c512ebb608e4e451d3227c488c0b83342e6d88b9c79d9e'}, 'carrier': {'path': 'docs/development/mainline-execution-2026-10-09-rev-001/carrier-shape-candidate-2026-10-15-rev-001/candidate-schemas/manifest_acceptance_signature_carrier_shape.schema.json', 'bytes': 2846, 'sha256': 'da2213ed8ce41bc5d32badfb3b042772de87565ff26c215c1766712ead2b72de'}, 'profile': {'path': 'docs/development/mainline-execution-2026-10-19-signing-profile-content-rev-001/PROFILE_SCHEMA_CANDIDATE.json', 'bytes': 8525, 'sha256': '4bbea6a34351178e4adefe5c31b04e8a2eb4cc9e08bbfadbe8c164d066f68fe1'}, 'verifier': {'path': 'docs/development/three-argument-verifier-contract-2026-10-28-rev-001/CONTRACT_SCHEMA_CANDIDATE.json', 'bytes': 11648, 'sha256': '4f207b14cd96a84884e9b3d3a77e955fe65b24bff4efe4a9c7e62c0ce9b3e34d'}}


def preflight_initial_contracts(specs, supplied, schema_bytes):
    """Consume fixed existing schemas and metadata in the same bounded snapshot.

    Schema bytes are charged first to freeze_inputs' existing total budget.
    Carrier selection uses only the acceptance's full signature_ref. No context,
    projection, envelope, message or message digest is built, and no public math
    runs. Matching role/forward literals are syntax facts, not actual authority.
    """
    schema_failures = []
    if schema_bytes is None:
        schemas = {}
    elif type(schema_bytes) is not dict or any(type(key) is not str for key in schema_bytes):
        schemas = {}
        schema_failures.append(['schemas', 'SCHEMA_MAPPING_INVALID'])
    else:
        schemas = schema_bytes
        if set(schemas) - set(_CONTRACT_SCHEMAS):
            schema_failures.append(['schemas', 'UNEXPECTED_SCHEMA_ROLE'])
    if (type(specs) is not tuple or type(supplied) is not dict
            or any(type(key) is not str for key in supplied)):
        result = preflight_initial_inputs(specs, supplied)
    else:
        reserved = {'schema:'+name for name in _CONTRACT_SCHEMAS}
        if (set(supplied) & reserved or any(type(s) is InputSpec and type(s.role) is str and s.role in reserved for s in specs)):
            schema_failures.append(['schemas', 'RESERVED_SCHEMA_ROLE'])
        schema_specs = tuple(InputSpec('schema:'+role, 'BYTES', row['bytes'], row['sha256'])
                             for role, row in _CONTRACT_SCHEMAS.items())
        combined = dict(supplied)
        for role in _CONTRACT_SCHEMAS:
            combined['schema:'+role] = schemas.get(role)
        result = preflight_initial_inputs(schema_specs + specs, combined)
    failures, missing = result['failures'], result['missing']
    for item in schema_failures:
        if item not in failures:
            failures.append(item)
    def fail(role, code):
        if [role, code] not in failures:
            failures.append([role, code])
    def absent(name):
        if name not in missing:
            missing.append(name)

    over_budget = any(code in {'TOTAL_BYTE_LIMIT', 'INPUT_COUNT_LIMIT'} for _, code in failures)
    raw = {item.role: item.raw for item in result['snapshots'].items}
    objects = {item.role: parse_json_strict(item.raw) for item in result['snapshots'].items
               if not over_budget and item.data_format == 'SEALED_JSON' and item.role in _REQUIRED}
    index = {item.object_ref: item.raw for item in result['snapshots'].items
             if item.object_ref is not None and item.data_format == 'SEALED_JSON'}
    validators = {}
    # A raw hash/size failure already retained by freeze_inputs is reported here
    # in the specific schema namespace as well; there is no alternate schema.
    for role, row in _CONTRACT_SCHEMAS.items():
        if over_budget:
            break
        name = 'schema:'+role
        body = raw.get(name)
        if body is None:
            if any(label == name for label, _ in failures):
                fail(name, 'SCHEMA_IDENTITY_MISMATCH')
            else:
                absent(name)
            continue
        definition = parse_json_strict(body)
        Draft202012Validator.check_schema(definition)
        validators[role] = Draft202012Validator(definition)
    carrier = None
    acceptance = objects.get('acceptance')
    if acceptance is not None and not over_budget:
        reference = acceptance.get('signature_ref')
        if type(reference) is dict:
            try:
                validate_ref(reference)
                body = index.get((reference['object_id'], reference['content_sha256']))
                if body is not None:
                    carrier = parse_json_strict(body)
            except (ValueError, TypeError, KeyError):
                fail('carrier', 'SIGNATURE_REFERENCE_INVALID')
    if carrier is None:
        absent('carrier_for_signature_ref')
    else:
        objects['carrier'] = carrier
    validated = []
    for role, validator in validators.items():
        obj = objects.get(role)
        if obj is None:
            continue
        if not validator.is_valid(obj):
            fail(role, 'SCHEMA_CONTENT_INVALID')
        else:
            validated.append(role)
    key_status, carrier_status = 'NOT_CHECKED', 'NOT_CHECKED'
    if 'root' in validated:
        root = objects['root']
        # The existing schema guarantees exactly 32 lowercase hex public bytes.
        digest = hashlib.sha256(bytes.fromhex(root['authority_public_key'])).hexdigest()
        if digest != root['authority_public_key_sha256']:
            fail('root', 'PUBLIC_KEY_HASH_MISMATCH')
            key_status = 'REJECTED'
        else:
            key_status = 'OBSERVED'
        if 'carrier' in validated and objects['carrier']['public_key_sha256'] != digest:
            fail('carrier', 'ROOT_PUBLIC_KEY_BINDING_MISMATCH')
    if 'profile' in validated:
        profile = objects['profile']
        for name, role in [('manifest_acceptance', 'acceptance'), ('carrier_shape', 'carrier')]:
            if profile['schema_bindings'][name]['schema_raw_sha256'] != _CONTRACT_SCHEMAS[role]['sha256']:
                fail('profile', 'SCHEMA_BINDING_MISMATCH')
        if 'carrier' in validated:
            expected = profile['carrier_rules']
            for field in ['schema_version', 'object_type', 'signing_profile', 'algorithm', 'signature_encoding']:
                if objects['carrier'][field] != expected[field]:
                    fail('carrier', 'PROFILE_'+field.upper()+'_MISMATCH')
            carrier_status = ('REJECTED' if any(role == 'carrier' for role, _ in failures)
                              else 'OBSERVED' if key_status == 'OBSERVED' else 'NOT_CHECKED')
    result.update(
        status='REJECTED' if failures else 'MISSING' if missing else 'OBSERVED',
        scope='DEVELOPMENT_BOUNDED_INPUT_LOCAL_REFS_AND_FIXED_CONTRACT_CONTENT_ONLY',
        content_check_blocked_by_resource_limit=over_budget,
        schema_inputs_admitted=len(validators), validated_object_roles=validated,
        schema_content_status=('REJECTED' if any(role.startswith('schema') or code == 'SCHEMA_CONTENT_INVALID'
                                               for role, code in failures)
                               else 'OBSERVED' if len(validated) == len(_CONTRACT_SCHEMAS) else 'MISSING'),
        public_key_hash_binding=key_status, carrier_metadata_binding=carrier_status,
        message_binding='NOT_CHECKED', public_key_point_validity='NOT_CHECKED',
        execution_source_admission='NOT_CHECKED',
        schema_selection_is_development_only=True,
        verifier_contract_development_only=objects.get('verifier', {}).get('development_only'),
    )
    return result
