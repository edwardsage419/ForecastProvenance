"""Bounded M1 installed-runtime, workflow and physical retention checks.

The installed pinbook is the independent model bootstrap, not self-certified
evidence. Control, offline storage and historical timestamps are explicit model
assumptions; byte equality and completeness of the copies execute here.
"""
from pathlib import Path
import ast
import importlib.metadata
import platform
import sys
import json
import decimal
import datetime
import zoneinfo
import _decimal
import _json
from .canonical import canonical_json, sha256_hex, verify_sealed_object
from .authority_primitives_v1 import ExactRef, resolve_exact, AuthorityPrimitiveError
from .core import Check
from .replay_records_v1 import NativeReplay, reduce_checks
from .replay_model_v1 import MODEL_SOURCE_REFS
from .external_model_engine_v1 import verify_model_bitcoin

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = 'integration_model_pins_v1'
ROOT_MODULES = ('independent_replay_v1', 'independent_replay_inputs_v1',
    'integration_model_v1', 'initial_acceptance_public_auth_v1',
    'claim_authority_v1', 'claim_authority_trust_root_v1')
ASSUMPTIONS = ('MODEL_STORAGE_CONTROL', 'MODEL_OFFLINE_COPY',
    'MODEL_RETENTION_TIMES', 'MODEL_WORKFLOW_AUTHORITY_AND_ACTIONS','MODEL_REPORT_AND_SIGNING_TIMES')
OWNED = ('source_closure','runtime_pairing','parser_pairing','retained_build_identity',
    'target_method_compatibility','source_resolution_binding','offline_backup_rule',
    'retention_corpus','retention_owner_control','retention_offline',
    'retention_before_acceptance','canonicalization_cost','workflow_package_acceptance',
    'workflow_required_review','workflow_candidate_freeze','workflow_exact_manifest_inputs',
    'workflow_retained_evidence')

def check(name, value, reason):
    return Check(name, 'UNKNOWN' if value is None else 'PASS' if value else 'FAIL', reason)

def runtime_modules():
    """AST closure in the fixed installed Python package, never caller code."""
    directory = ROOT/'src/forecast_trust_core'
    pending=[*ROOT_MODULES, '__init__']; found={}
    while pending:
        name=pending.pop()
        if name in found or name==BOOTSTRAP: continue
        path=directory/(name+'.py')
        if not path.is_file(): continue
        raw=path.read_bytes(); found[name]=sha256_hex(raw)
        for node in ast.walk(ast.parse(raw)):
            if isinstance(node,ast.ImportFrom):
                module=node.module or ''
                if node.level==1:
                    if module: pending.append(module.split('.')[0])
                    else: pending.extend(a.name for a in node.names)
                elif module.startswith('forecast_trust_core.'):
                    pending.append(module.split('.')[1])
                elif module=='forecast_trust_core': pending.extend(a.name for a in node.names)
            elif isinstance(node,ast.Import):
                pending.extend(a.name.split('.')[1] for a in node.names if a.name.startswith('forecast_trust_core.'))
    found['__init__']=sha256_hex((directory/'__init__.py').read_bytes())
    found['CLI']=sha256_hex((ROOT/'scripts/development/replay_independent_genesis.py').read_bytes())
    return dict(sorted(found.items()))

def observe_model_runtime():
    return {'python':platform.python_version(),
        'executable_sha256':sha256_hex(Path(sys.executable).read_bytes()),
        'dependencies':{x:importlib.metadata.version(x) for x in ('pytest','jsonschema')},
        'modules':runtime_modules(),
        'stdlib':{m.__name__:sha256_hex(Path(m.__file__).read_bytes()) for m in
            (json, json.decoder,json.encoder,json.scanner,decimal,_decimal,_json,datetime,zoneinfo)},
        'bootstrap':'INSTALLED_INDEPENDENT_MODEL_PINBOOK_NOT_SELF_CERTIFIED'}

def read(reference,resolver,checks):
    rr=ExactRef.from_mapping(reference) if isinstance(reference,dict) else reference
    try: return resolve_exact(rr,resolver)
    except AuthorityPrimitiveError as exc:
        checks.append(Check('integration-input','UNKNOWN' if str(exc)=='NO_AUTHORITATIVE_RESULT' else 'FAIL',str(exc)))
    except Exception as exc: checks.append(Check('integration-input','UNKNOWN','INTEGRATION_UNAVAILABLE_'+type(exc).__name__))
    return None

def verify_copy_sets(resolver,expected):
    checks=[]
    for group,refs in expected.items():
        for data in refs:
            rr=ExactRef(data["object_id"],data["content_sha256"])
            try:
                original=resolver.resolve_exact(rr)
                copy=resolver.resolve_copy_exact(group,rr)
                if original is None or copy is None:
                    checks.append(Check(group,'UNKNOWN','RETAINED_COPY_OR_ORIGINAL_UNAVAILABLE'));continue
                # Copies use the exact current raw bytes, not a label or count.
                valid=original==copy
                if data['kind']=='sealed':
                    obj=json.loads(copy); valid=valid and verify_sealed_object(obj) and obj['object_id']==rr.object_id and obj['content_sha256']==rr.content_sha256
                else: valid=valid and sha256_hex(copy)==rr.content_sha256
                checks.append(check(group,valid,'RETAINED_COPY_EXACT_BYTES'))
            except (ValueError,TypeError,KeyError): checks.append(Check(group,'FAIL','RETAINED_COPY_INVALID'))
            except Exception as exc: checks.append(Check(group,'UNKNOWN','RETAINED_COPY_UNAVAILABLE_'+type(exc).__name__))
        checks.append(check(group,bool(refs),'NONEMPTY_FIXED_COPY_UNIVERSE'))
    return tuple(checks)

def replay_integration_checks(basis,requirements,resolver,runtime):
    from .integration_model_pins_v1 import MODEL_INTEGRATION_REFS,MODEL_RUNTIME,MODEL_COPY_REFS,MODEL_PRESIGN_CONTEXT
    input_errors={};objects={}
    for name,reference in MODEL_INTEGRATION_REFS.items():
        input_errors[name]=[]
        objects[name]=read(reference,resolver,input_errors[name])
    errors=[c for checks in input_errors.values() for c in checks]
    native={}
    def dependencies(names=(),sources=(),extra=()):
        return tuple(dict.fromkeys((*[ExactRef.from_mapping(MODEL_INTEGRATION_REFS[n]) for n in names],
            *[ExactRef.from_mapping(MODEL_SOURCE_REFS[n]) for n in sources],*extra)))
    def errors_for(names):return [c for n in names for c in input_errors[n]]
    def publish(names,checks,input_refs,seam=False):
        for name in names: native[name]=NativeReplay(tuple(checks),input_refs,seam)
    publish(('source_closure',),(Check('source-universe',requirements.proofs[0].status,'INDEPENDENT_SOURCE_DERIVATION'),),requirements.required_sources)
    profile=requirements.source_objects.get(MODEL_SOURCE_REFS['profile']['object_id'])
    build=objects.get('build')
    rt=[*errors_for(('build',)),check('actual-runtime',None if runtime is None else runtime==MODEL_RUNTIME,'WHOLE_INSTALLED_RUNTIME_IDENTITY'),
        check('retained-build',None if build is None else build.get('runtime')==MODEL_RUNTIME,'EXACT_RETAINED_BUILD'),
        check('profile',None if profile is None or runtime is None else profile['python']==runtime.get('python') and profile['pytest']==runtime.get('dependencies',{}).get('pytest') and profile['jsonschema']==runtime.get('dependencies',{}).get('jsonschema') and profile['model_only'] is True,'EXACT_MODEL_PROFILE')]
    runtime_refs=dependencies(('build',),('profile',))
    publish(('runtime_pairing','retained_build_identity'),rt,runtime_refs)
    parser=[]
    for kind in ('schedule','measurement'):
        for n in ('t1','t2','t3'):
            obj=requirements.source_objects.get(MODEL_SOURCE_REFS[kind+'-'+n]['object_id'])
            parser.append(check('parser-'+kind+'-'+n,None if obj is None or profile is None else obj['parser']==profile['parser']=='strict-json-model-v1','EXACT_SOURCE_PARSER_PAIR'))
    source_names=tuple(kind+'-'+n for kind in ('schedule','measurement') for n in ('t1','t2','t3'))
    publish(('parser_pairing',),parser+rt,dependencies(('build',),('profile',*source_names)))
    compatibility=[];binding=[]
    method=requirements.source_objects.get(MODEL_SOURCE_REFS['method']['object_id'])
    for n in ('t1','t2','t3'):
        target=requirements.source_objects.get(MODEL_SOURCE_REFS['target-'+n]['object_id'])
        resolution=requirements.source_objects.get(MODEL_SOURCE_REFS['resolution-'+n]['object_id'])
        compatibility.append(check('target-'+n,None if target is None or method is None else target['method']==method['name']=='last-observed-value-v1' and target['prediction_type']=='DECIMAL' and target['unit']=='model-index','TARGET_METHOD_COMPATIBILITY'))
        for kind in ('schedule','measurement'):
            source=requirements.source_objects.get(MODEL_SOURCE_REFS[kind+'-'+n]['object_id'])
            binding.append(check(kind+'-'+n,None if source is None or resolution is None or target is None else source['target']==target['name']==n and source['source_kind']==kind and target['resolution']==resolution['name'],'EXACT_SOURCE_RESOLUTION_BINDING'))
    target_names=tuple('target-'+n for n in ('t1','t2','t3'))
    resolution_names=tuple('resolution-'+n for n in ('t1','t2','t3'))
    publish(('target_method_compatibility',),compatibility,dependencies(sources=('method',*target_names)))
    publish(('source_resolution_binding',),binding,dependencies(sources=(*source_names,*target_names,*resolution_names)))
    retention=objects.get('retention');rule=objects.get('contract')
    copies=verify_copy_sets(resolver,MODEL_COPY_REFS)
    retention_checks=[*errors_for(('retention','contract')),*copies,
        check('offline-rule',None if rule is None else rule['offline_backup_rule']=={'copies':1,'complete':'VERIFIER_FIXED_PUBLIC_MODEL_INPUTS','pre_signing_scope':'NO_FUTURE_OBSERVATIONS','post_signing_scope':'COMPLETE_REPLAY_INPUTS'},'CONCRETE_OFFLINE_BACKUP_RULE'),
        check('copy-inventory',None if retention is None else retention['copy_inventory']=={group:[entry for entry in entries if entry['object_id']!=MODEL_INTEGRATION_REFS['retention']['object_id']] for group,entries in MODEL_COPY_REFS.items()} and retention['self_copy']=='INDEPENDENT_PINBOOK_AFTER_EVIDENCE_SERIALIZATION','EXACT_RETENTION_UNIVERSE'),
        check('control',None if retention is None else retention['controller']=='MODEL_OWNER' and retention['control_evidence']=='EXPLICIT_MODEL_STORAGE_CONTROL','MODEL_OWNER_CONTROL_ASSUMPTION'),
        check('offline',None if retention is None else retention['offline'] is True and retention['network']=='OFFLINE_ONLY','MODEL_OFFLINE_COPY_ASSUMPTION'),
        check('retention-times',None if retention is None else retention['pre_signing_retained_at']=='2030-01-31T22:00:00Z' and retention['pre_signing_retained_at']<'2030-02-01T00:00:00Z' and retention['post_signing_retained_at']=='2030-03-01T00:00:00Z','MODEL_COPY_TIMES_AND_PRE_SIGNING_SCOPE'),
        check('cost',None if rule is None else rule['cost']=='ZERO_RECURRING_CASH_COST' and rule['network']=='OFFLINE_ONLY','CANONICAL_OFFLINE_NO_RECURRING_CASH_COST')]
    retention_refs=dependencies(('retention','contract'),extra=tuple(ExactRef(e['object_id'],e['content_sha256']) for entries in MODEL_COPY_REFS.values() for e in entries))
    publish(('offline_backup_rule','retention_corpus','retention_owner_control','retention_offline','retention_before_acceptance','canonicalization_cost'),retention_checks,retention_refs,True)
    workflow=[]
    expected_members=[v for k,v in sorted(MODEL_SOURCE_REFS.items())]
    manifest=read(basis.subject,resolver,workflow)
    package=objects.get('package');review=objects.get('review');accept=objects.get('package-acceptance');freeze=objects.get('freeze')
    workflow_names=('contract','package','review','package-acceptance','freeze')
    workflow.extend(errors_for(workflow_names))
    workflow.extend((check('workflow-contract',None if rule is None else rule['roles']=={'PACKAGE_ACCEPT':'MODEL_OWNER','CANDIDATE_REVIEW':'MODEL_REVIEWER','CANDIDATE_FREEZE':'MODEL_OWNER'} and rule['real_authority'] is False,'FIXED_DISTINCT_WORKFLOW_ROLE_MAPPING'),
        check('package-members',None if package is None else package['manifest_ref']==basis.subject.to_dict() and package['source_refs']==expected_members,'COMPLETE_EXACT_PACKAGE_MANIFEST_INPUTS'),
        check('review',None if review is None or package is None else review['package_ref']==MODEL_INTEGRATION_REFS['package'] and review['actor']=='MODEL_REVIEWER' and review['blocking_findings']==[] and review['reviewed_at']=='2030-01-30T00:00:00Z' and review['assumption']=='MODEL_WORKFLOW_AUTHORITY_AND_ACTIONS','INDEPENDENT_MODEL_REQUIRED_REVIEW'),
        check('package-acceptance',None if accept is None else accept['package_ref']==MODEL_INTEGRATION_REFS['package'] and accept['review_ref']==MODEL_INTEGRATION_REFS['review'] and accept['actor']=='MODEL_OWNER' and accept['decision']=='ACCEPT' and accept['accepted_at']=='2030-01-30T12:00:00Z' and accept['contract_ref']==MODEL_INTEGRATION_REFS['contract'],'MODEL_PACKAGE_ACCEPTANCE_BOUND_ROLE'),
        check('freeze',None if freeze is None else freeze['manifest_ref']==basis.subject.to_dict() and freeze['package_ref']==MODEL_INTEGRATION_REFS['package'] and freeze['acceptance_ref']==MODEL_INTEGRATION_REFS['package-acceptance'] and freeze['actor']=='MODEL_OWNER' and freeze['frozen_at']=='2030-01-31T00:00:00Z' and freeze['contract_ref']==MODEL_INTEGRATION_REFS['contract'],'MODEL_CANDIDATE_FREEZE_EXACT_ORDER'),
        check('manifest-inputs',None if manifest is None else len(manifest['dependency_roles'])==24 and all(x['ref']==MODEL_SOURCE_REFS.get(x['role']) for x in manifest['dependency_roles']),'WORKFLOW_EXACT_MANIFEST_INPUTS')))
    # No stateful acceptance/freeze function is invoked. Facts are model seams.
    publish(tuple(n for n in OWNED if n.startswith('workflow_')),workflow+retention_checks,dependencies(workflow_names,extra=(*requirements.required_sources,*retention_refs)),True)
    bitcoin=errors_for(('presign-bundle','presign-chain','presign-proof','presign-observation'))
    data={'objects':{k:objects.get('presign-'+k) for k in ('bundle','chain','proof')},'raw':{}}
    try:
        if any(x is None for x in data['objects'].values()) or objects.get('presign-observation') is None: raise LookupError('pre-signing witness unavailable')
        computed=verify_model_bitcoin(data,MODEL_PRESIGN_CONTEXT)
        bitcoin.append(check('pre-signing-inclusion',computed==objects['presign-observation']['recomputed'],'FRESH_PRE_SIGNING_MANIFEST_INCLUSION'))
    except LookupError: bitcoin.append(Check('pre-signing-inclusion','UNKNOWN','PRE_SIGNING_BITCOIN_WITNESS_UNAVAILABLE'))
    except (ValueError,KeyError,TypeError): bitcoin.append(Check('pre-signing-inclusion','FAIL','PRE_SIGNING_BITCOIN_WITNESS_INVALID'))
    except Exception as exc: bitcoin.append(Check('pre-signing-inclusion','UNKNOWN','PRE_SIGNING_BITCOIN_UNAVAILABLE_'+type(exc).__name__))
    return native,tuple(errors),tuple(bitcoin),objects
