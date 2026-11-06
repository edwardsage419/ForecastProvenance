"""M1 executable scientific model capability; never real C01 eligibility."""
from dataclasses import dataclass
from pathlib import Path
import platform, sys
from .authority_primitives_v1 import ExactRef, resolve_exact, AuthorityPrimitiveError
from .canonical import sha256_hex, parse_json_strict
from .core import Check
from . import core, lifecycle, evidence, genesis_sources, canonical
from . import scientific_model_engine_v1 as engine
from .scientific_model_pins_v1 import (MODEL_SCIENTIFIC_REFS, MODEL_SCIENTIFIC_RAW_REFS, MODEL_SCIENTIFIC_CONTEXTS, MODEL_SCIENTIFIC_RUNTIME, MODEL_SCIENTIFIC_ENGINE_SHA256)
from .calendar_model_v1 import MODEL_CYCLE_SUBMISSION_REFS
from .replay_model_v1 import MODEL_SOURCE_REFS
from .g10_requirements_v1 import _fixed_basis, reconstruct_requirements
from .qualification_scope_v1 import consume_model_admissions
from .replay_records_v1 import NativeReplay, emit_records, reduce_checks

@dataclass(frozen=True)
class ScientificSlotResult:
    target_name: str
    input_refs: dict
    raw_inputs: dict
    independent_context: dict
    checks: tuple

@dataclass(frozen=True)
class ConfirmatoryReplay:
    slot_results: tuple
    executions: tuple
    scored_squared_errors: tuple
    checks: tuple
    records: tuple
    overall: str
    input_refs: tuple
    model_only: bool = True
    prospective_eligible: bool = False
    real_genesis_readiness: str = 'NOT_ESTABLISHED'
    protocol_state_change: str = 'NONE'

def observed_runtime():
    return {'python':platform.python_version(),'executable_sha256':sha256_hex(Path(sys.executable).read_bytes()), **{m.__name__.split('.')[-1]+'_sha256':sha256_hex(Path(m.__file__).read_bytes()) for m in (core,lifecycle,evidence,genesis_sources,canonical)}}

def replay_confirmatory_checks(basis, cycles, qualifications, resolver):
    checks, refs, slots, executions = [], set(), [], []
    def read(reference):
        reference=ExactRef.from_mapping(reference) if isinstance(reference,dict) else reference
        refs.add(reference)
        try: return resolve_exact(reference,resolver), ()
        except AuthorityPrimitiveError as exc: return None,(Check('scientific-exact-input','UNKNOWN' if str(exc)=='NO_AUTHORITATIVE_RESULT' else 'FAIL',str(exc)),)
        except Exception as exc: return None,(Check('scientific-exact-input','UNKNOWN','SCIENTIFIC_RESOLVER_UNAVAILABLE_'+type(exc).__name__),)
    model=basis==_fixed_basis()
    checks.append(Check('scientific-model-profile','PASS' if model else 'UNKNOWN','M1_SCIENTIFIC_CAPABILITY' if model else 'REAL_C01_AUTHORITY_NOT_ESTABLISHED'))
    if not model:
        return ConfirmatoryReplay((),(),(),tuple(checks),(),'UNKNOWN',())
    requirements=reconstruct_requirements(basis,resolver)
    checks.extend((Check('scientific-requirements',requirements.overall,'SCIENTIFIC_REQUIREMENTS_UNIVERSE'),Check('scientific-cycles',cycles.overall,'SCIENTIFIC_CYCLE_UNIVERSE')))
    fixed = {n:ExactRef.from_mapping(MODEL_CYCLE_SUBMISSION_REFS[n]) for n in ('t1','t2','t3')}
    submission, native_objects, sources={}, {}, {}
    for n,rr in fixed.items():
        obj, errors=read(rr); checks.extend(errors); submission[n]=obj
        native_objects[n]={}
        for kind in ('slot','target','plan','issued','attempt','resolution','manifest'):
            if obj is not None:
                v,errors=read(obj['records'][kind]); checks.extend(errors); native_objects[n][kind]=v
    all_slots=[submission[n]['records']['slot'] for n in fixed if submission[n]]
    all_issued=[submission[n]['records']['issued'] for n in fixed if submission[n]]
    for name in ('method','scientific','schedule',*[k+'-'+n for n in fixed for k in ('target','resolution','measurement')]):
        sources[name], errors=read(MODEL_SOURCE_REFS[name]); checks.extend(errors)
    expected_logical = [submission[n]['slot_ref'] for n in fixed if submission[n]]
    checks.append(Check('scientific-denominator-domain', 'UNKNOWN' if len(expected_logical)!=3 or cycles.overall!='PASS' else 'PASS' if engine.same_refs([s.logical_ref.to_dict() for s in cycles.slots],expected_logical) else 'FAIL','INDEPENDENT_SCIENTIFIC_SLOT_DOMAIN'))
    try:
        runtime=observed_runtime()
        checks.append(Check('scientific-engine-identity','PASS' if sha256_hex(Path(engine.__file__).read_bytes())==MODEL_SCIENTIFIC_ENGINE_SHA256 else 'FAIL','SCIENTIFIC_IMPLEMENTATION_IDENTITY'))
    except Exception as exc:
        runtime=None; checks.append(Check('scientific-engine-identity','UNKNOWN','SCIENTIFIC_RUNTIME_UNAVAILABLE_'+type(exc).__name__))
    for n in fixed:
        localchecks=[]; mappings={k.replace('-','_'):ExactRef.from_mapping(v) for k,v in MODEL_SCIENTIFIC_REFS[n].items()}
        objects={}
        for key,reference in mappings.items():
            objects[key.replace('_','-') if key=='execution_0' else key], errors=read(reference); localchecks.extend(errors)
        # Retained native C06 objects are exact independently pinned submissions.
        objects.update(native_objects[n])
        rawdata={}
        for k in ('older','baseline','outcome'):
            reference=ExactRef.from_mapping(MODEL_SCIENTIFIC_RAW_REFS[n+'-'+k]); refs.add(reference)
            try:
                raw=resolver.resolve_exact(reference)
                if raw is None: localchecks.append(Check('scientific-raw','UNKNOWN','SCIENTIFIC_RAW_UNAVAILABLE'))
                elif not isinstance(raw,bytes) or sha256_hex(raw)!=reference.content_sha256: localchecks.append(Check('scientific-raw','FAIL','SCIENTIFIC_RAW_HASH_INVALID')); raw=None
                rawdata[reference.object_id]=raw
            except Exception as exc: rawdata[reference.object_id]=None; localchecks.append(Check('scientific-raw','UNKNOWN','SCIENTIFIC_RAW_UNAVAILABLE_'+type(exc).__name__))
        inputs={'objects':objects,'raw':rawdata}
        context=dict(MODEL_SCIENTIFIC_CONTEXTS[n])
        sub=submission[n]; target=objects.get('target'); plan=objects.get('plan'); slot=objects.get('slot')
        if sub and target and plan and slot and all(sources[k] for k in ('method','target-'+n,'resolution-'+n,'measurement-'+n)):
            context.update(target_name=n,subject=basis.subject.to_dict(),slot_ref=sub['records']['slot'],plan_ref=sub['records']['plan'],target_ref=sub['records']['target'],issued_ref=sub['records']['issued'],method_ref=MODEL_SOURCE_REFS['method'],measurement_ref=MODEL_SOURCE_REFS['measurement-'+n],
                method=sources['method'],target=sources['target-'+n],resolution_policy=sources['resolution-'+n],policy_refs={k:MODEL_SOURCE_REFS[k] for k in ('scientific','schedule','resolution-'+n,'measurement-'+n)},
                runtime=MODEL_SCIENTIFIC_RUNTIME,cutoff=slot['information_cutoff'],period=target['reference_period'],barrier=target['outcome_information_barrier'],resolution_deadline=target['resolution_deadline'],
                plan_deadline=plan['plan_commitment_deadline'],window_open=plan['execution_window_open'],window_close=plan['execution_window_close'],output_schema=slot['output_schema'],all_slot_refs=all_slots,all_issued_refs=all_issued)
            try:
                ntchecks,execution=engine.evaluate_scientific_slot(inputs,context,runtime)
                localchecks.extend(ntchecks); executions.append(execution)
            except Exception as exc:
                localchecks.extend(Check(k,'UNKNOWN','SCIENTIFIC_EXECUTION_UNAVAILABLE_'+type(exc).__name__) for k in engine.NT_CHECKS)
            # Existing C06 attempt is not replaced by a scientific detail record.
            a=objects.get('attempt'); d=objects.get('execution-0'); ledger=objects.get('attempt_ledger')
            ok=None if a is None or d is None or ledger is None else (d['native_attempt_ref']==engine.ref(a) and ledger['native_attempt_refs']==[engine.ref(a)] and all(d[k]==a[k] for k in ('sequence','started_at','status','output_ref','method_ref','slot_ref')))
            localchecks.append(Check('native-attempt-detail-binding','UNKNOWN' if ok is None else 'PASS' if ok else 'FAIL','NATIVE_ATTEMPT_HISTORY_BINDING'))
        else:
            localchecks.extend(Check(k,'UNKNOWN','SCIENTIFIC_CONTEXT_UNAVAILABLE') for k in engine.NT_CHECKS)
        boundary=next((b.ref for b in qualifications.boundaries if b.role=='cycle-'+n),None)
        if boundary is None: localchecks.append(Check('scientific-qualification','UNKNOWN','QUALIFICATION_BOUNDARY_UNAVAILABLE'))
        else: localchecks.extend(consume_model_admissions(qualifications,('p1','p2','p3'),boundary))
        slots.append(ScientificSlotResult(n,mappings,inputs,context,tuple(localchecks)))
    allchecks=tuple(checks)+tuple(c for slot in slots for c in slot.checks)
    refs=tuple(sorted(refs,key=lambda r:(r.object_id,r.content_sha256)))
    native={name:NativeReplay(tuple(checks)+tuple(c for s in slots for c in s.checks if c.check_id==name or not c.check_id.startswith('NT')),refs,True) for name in engine.NT_CHECKS}
    native['C01_capability_gate']=NativeReplay(allchecks,refs,True)
    # Governance data never enters raw measurement parsing or method inputs.
    native['governance_scientific_exclusion']=NativeReplay(allchecks,refs,True)
    try:
        records=emit_records(requirements,native,__file__)
        wanted={k for clause in requirements.requirements if clause.check in native for k in clause.keys}
        if not isinstance(records,tuple) or len(records)!=len(wanted) or {r.key for r in records}!=wanted or any(not r.raw_result or r.basis!=basis for r in records):
            raise ValueError('scientific raw output unavailable or incomplete')
    except Exception as exc:
        records=(); allchecks+=(Check('scientific-raw-records','UNKNOWN','SCIENTIFIC_RAW_RECORDS_UNAVAILABLE_'+type(exc).__name__),)
    return ConfirmatoryReplay(tuple(slots),tuple(executions),tuple(x.squared_error for x in executions if x.squared_error is not None),allchecks,records,reduce_checks(allchecks),refs)
