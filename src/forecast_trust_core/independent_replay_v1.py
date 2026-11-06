"""Full finite M1 replay. Model PASS never establishes real acceptance.

No caller-supplied universe, result vector, eligibility or callback is accepted.
The installed model basis/pins select inputs; the resolver only supplies bytes.
"""
from dataclasses import dataclass, asdict, replace,fields,field
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from .authority_primitives_v1 import ExactRef, verify_sealed_identity
from .canonical import canonical_json, sha256_hex, parse_json_strict
from .claim_authority_contract_gate_v1 import validate_manifest_acceptance_v3_contract
from .architecture_compression_v1 import check_manifest_acceptance_v3_bindings
from .core import Check
from .g10_replay_v1 import _aggregate_g10, PredicateResult
from .g10_requirements_v1 import reconstruct_requirements, _fixed_basis
from .replay_records_v1 import NativeReplay, emit_records, reduce_checks
from .cycle_universe_v1 import reconstruct_cycle_universe
from .qualification_scope_v1 import replay_qualification_scope, consume_model_admissions
from .confirmatory_replay_v1 import replay_confirmatory_checks
from .g10_external_evidence_v1 import replay_external_evidence, ExternalReplay, SEAMS
from .g10_acceptance_v1 import replay_acceptance_bindings, REPORT_CHECKS, _replay_findings
from .integration_model_v1 import observe_model_runtime, replay_integration_checks, read, ASSUMPTIONS
from .independent_replay_inputs_v1 import CorpusResolver

def development_json(value):
    """Explicit absent-field markers for development trace, not signed bytes."""
    def tree(v):
        if v is None:return {'development_unavailable':True}
        if hasattr(v,'__dataclass_fields__'):return tree(asdict(v))
        if isinstance(v,(tuple,list)):return [tree(x) for x in v]
        if isinstance(v,dict):return {k:tree(x) for k,x in v.items()}
        return v
    return canonical_json(tree(value))

def raw_trace(rows):
    """Lossless pooling; raw rows are neither deduplicated nor overwritten."""
    raw_pool={};input_pool={};raw_ids={};input_ids={};output=[]
    for row in rows:
        if row.raw_result not in raw_ids:
            ident=sha256_hex((row.raw_result or '').encode());raw_ids[row.raw_result]=ident;raw_pool[ident]=row.raw_result
        if row.input_refs not in input_ids:
            inputs=[r.to_dict() for r in row.input_refs];ident=sha256_hex(canonical_json(inputs));input_ids[row.input_refs]=ident;input_pool[ident]=inputs
        data={f.name:asdict(getattr(row,f.name)) if hasattr(getattr(row,f.name),'__dataclass_fields__') else getattr(row,f.name) for f in fields(row) if f.name not in ('basis','raw_result','input_refs')}
        data['raw_result_ref']=raw_ids[row.raw_result];data['input_refs_ref']=input_ids[row.input_refs]
        # Basis bindings remain individually visible, including a wrong basis.
        data['basis']=asdict(row.basis) if row.basis else None
        output.append(data)
    return {'raw_O':output,'raw_payloads':raw_pool,'input_ref_sets':input_pool}

@dataclass(frozen=True)
class IndependentReplay:
    reduced: object
    requirements: object
    cycles: object
    qualifications: object
    scientific: object
    external: object
    component_reports: dict
    runtime: dict | None
    stable_identity: str
    input_refs: tuple
    model_only: bool
    seams: tuple
    component_evidence: dict = field(default_factory=dict)
    comparison_checks: tuple = ()
    prospective_eligible: bool = False
    real_genesis_readiness: str = 'NOT_ESTABLISHED'
    protocol_state_change: str = 'NONE'
    @property
    def overall(self):
        public_checks=self.component_evidence.get('public_input_observation',{}).get('checks',())
        checks=(*self.comparison_checks,*public_checks)
        if self.reduced.overall=='FAIL' or any(c.status=='FAIL' for c in checks):return 'FAIL'
        if self.reduced.overall=='UNKNOWN' or any(c.status!='PASS' for c in checks):return 'UNKNOWN'
        return 'PASS'
    @property
    def raw_results(self):return self.reduced.raw_results
    @property
    def records(self):return self.reduced.records
    @property
    def coverage_diagnostics(self):return self.reduced.coverage_diagnostics
    @property
    def mandatory_set_identity(self):return self.reduced.mandatory_set_identity

def _reports(basis,requirements,resolver,native,bitcoin,qualifications):
    from .external_model_pins_v1 import MODEL_EXTERNAL_ALL_REFS
    from .integration_model_pins_v1 import MODEL_INTEGRATION_REFS
    def normalized(kind,statuses):
        return tuple(Check(name,status,'MODEL_REPLAY_'+name.upper().replace('-','_')) for name,status in zip(REPORT_CHECKS[kind],statuses))
    reports={'runtime':normalized('runtime',(reduce_checks(native['runtime_pairing'].checks),reduce_checks(native['runtime_pairing'].checks))),
        'sources':normalized('sources',tuple(p.status for p in requirements.proofs)),
        'bitcoin-pre-signing':normalized('bitcoin-pre-signing',(reduce_checks(bitcoin),))}
    # Independent past-only report scope is distinct from all final admission boundaries.
    from .presigning_model_v1 import replay_presigning_qualification
    history,admission,qualification_evidence=replay_presigning_qualification(basis,requirements,resolver)
    reports['qualification']=normalized('qualification',(reduce_checks(history),reduce_checks(admission)))
    # Structural candidate review reads all mandatory report finding inputs.
    # It does not inspect its own PASS label or final replay verdict.
    errors=[];findings=[];closures=[];complete=True
    manifest=read(basis.subject,resolver,errors)
    for role in REPORT_CHECKS:
        obj=read(MODEL_EXTERNAL_ALL_REFS['report-'+role],resolver,errors)
        if obj is None:complete=False;continue
        for field,destination in (('finding_refs',findings),('finding_closure_refs',closures)):
            values=obj.get(field,[] if field=='finding_closure_refs' else None)
            if not isinstance(values,list) or any(not isinstance(x,dict) for x in values):complete=False
            else:destination.extend(values)
    findingchecks,_=_replay_findings(basis,resolver,findings,closures,complete)
    from .replay_model_v1 import MODEL_SOURCE_REFS
    wanted={k:v for k,v in MODEL_SOURCE_REFS.items() if k not in ('root','scope','selection')}
    role_status='UNKNOWN' if manifest is None else 'PASS' if len(manifest.get('dependency_roles',[]))==len(wanted) and {x['role']:x['ref'] for x in manifest['dependency_roles']}==wanted else 'FAIL'
    reports['candidate-review']=normalized('candidate-review',(reduce_checks((*errors,Check('roles',role_status,'ACTUAL_MANIFEST_ROLE_CLOSURE'))),reduce_checks(findingchecks)))
    candidate_refs=[basis.subject,*[ExactRef.from_mapping(MODEL_EXTERNAL_ALL_REFS['report-'+r]) for r in REPORT_CHECKS]]
    for rr in findings+closures:
        try:candidate_refs.append(ExactRef.from_mapping(rr))
        except (ValueError,TypeError):pass  # The existing finding replay retains the known schema failure.
    candidate_refs=tuple(dict.fromkeys(candidate_refs))
    return reports,{'pre-signing-qualification':qualification_evidence,'pre-signing-bitcoin':{'checks':bitcoin,'input_refs':tuple(ExactRef.from_mapping(MODEL_INTEGRATION_REFS['presign-'+n]) for n in ('bundle','chain','proof','observation'))},'runtime':{'checks':native['runtime_pairing'].checks,'input_refs':native['runtime_pairing'].input_refs},'sources':{'derivations':requirements.derivations,'input_refs':requirements.required_sources},'candidate-review':{'checks':tuple(errors)+tuple(findingchecks),'input_refs':candidate_refs}}

def _meta(requirements,rows):
    impl=ExactRef('development:implementation:independent_replay_v1',sha256_hex(Path(__file__).read_bytes()))
    result=[]
    for key in requirements.mandatory_keys:
        if key.role!='CLASS_COMPLETENESS':continue
        members=tuple(r for r in rows if r.key.predicate_id==key.predicate_id)
        expected=tuple(k for k in requirements.mandatory_keys if k.predicate_id==key.predicate_id and k.role!='CLASS_COMPLETENESS')
        coverage='PASS' if expected and Counter(r.key for r in members)==Counter(expected) else 'FAIL' if requirements.overall=='PASS' else 'UNKNOWN'
        checks=(Check('class-key-coverage',coverage,'CLASS_EXACT_MEMBER_COVERAGE'),Check('derivation',requirements.overall,'CLASS_INDEPENDENT_REQUIREMENTS'),Check('conjunction',reduce_checks(tuple(Check('member',r.normalized if r.normalized!='NOT_APPLICABLE' else r.exclusion_result or 'UNKNOWN','RAW_CLASS_CONJUNCT') for r in members)),'CLASS_ALL_CONJUNCTS'))
        result.append(PredicateResult(key,requirements.basis,'FIXED_MODEL_CLASS_DERIVATION',requirements.basis.rule_ref,'/requirements',(key.predicate_id,),requirements.basis.rule_ref,impl,tuple(dict.fromkeys(r.source_ref for r in members if r.source_ref)) or (requirements.basis.rule_ref,),canonical_json([asdict(c) for c in checks]).decode(),reduce_checks(checks),'APPLICABLE',tuple(c.reason_code for c in checks),model_seam=True))
    return tuple(result)

def _observe_public_inputs(basis,resolver,request):
    """Supplemental local diagnostics, never authority or mandatory coverage.

    Controls are comparison inputs only. Reports receive generic exact identity
    checks, not kind/stage/subject/support/Strong replay. No signature lookup,
    signing projection, message construction or backend invocation occurs here.
    """
    checks=[];refs=[];declarations=[];observations=[];cache={}

    def check(role,status,reason):
        checks.append(Check('public-inputs.'+role,status,reason))

    def typed_ref(value,role):
        if value is None:
            check(role,'UNKNOWN','PUBLIC_REFERENCE_MISSING')
            return None
        try:
            if not isinstance(value,ExactRef):raise ValueError
            verified=ExactRef.from_mapping(value.to_dict())
        except (ValueError,TypeError,KeyError):
            check(role,'FAIL','PUBLIC_REFERENCE_INVALID')
            return None
        refs.append(verified)
        declarations.append({'role':role,'ref':verified.to_dict()})
        check(role,'PASS','PUBLIC_REFERENCE_TYPED_ONLY')
        return verified

    def read(ref,role):
        if ref is None:return None
        if ref not in cache:
            obj=None;metadata={}
            try:raw=resolver.resolve_exact(ref)
            except Exception:raw=None
            if raw is None:
                status,reason='UNKNOWN','PUBLIC_SOURCE_UNAVAILABLE'
            elif not isinstance(raw,bytes):
                status,reason='FAIL','PUBLIC_SOURCE_NOT_BYTES'
            else:
                metadata={'raw_sha256':sha256_hex(raw),'raw_size':len(raw)}
                if len(raw)>1024*1024:
                    status,reason='UNKNOWN','PUBLIC_LOCAL_SIZE_LIMIT'
                else:
                    try:parsed=parse_json_strict(raw)
                    except ValueError:
                        status,reason='FAIL','PUBLIC_JSON_INVALID'
                    else:
                        if not isinstance(parsed,dict):
                            status,reason='FAIL','PUBLIC_OBJECT_INVALID'
                        else:
                            try:verify_sealed_identity(parsed,ref)
                            except (ValueError,TypeError,RecursionError):
                                status,reason='FAIL','PUBLIC_IDENTITY_INVALID'
                            else:
                                obj=parsed
                                status,reason='PASS','PUBLIC_EXACT_IDENTITY_ONLY'
            cache[ref]=(obj,status,reason,metadata)
        obj,status,reason,metadata=cache[ref]
        check(role,status,reason)
        observations.append({'role':role,'ref':ref.to_dict(),'status':status,
                             'reason_code':reason,**metadata})
        return obj

    acceptance=None
    if not isinstance(request,Mapping) or set(request)-{'acceptance_ref','required_report_refs'}:
        check('request','FAIL','PUBLIC_INPUT_REQUEST_INVALID')
    else:
        acceptance_ref=typed_ref(request.get('acceptance_ref'),'acceptance')
        manifest_ref=typed_ref(basis.subject,'manifest')
        root_ref=typed_ref(basis.root_ref,'root-control')
        rule_ref=typed_ref(basis.rule_ref,'rule-control')
        expected=request.get('required_report_refs')
        if expected is None:
            check('expected-reports','UNKNOWN','PUBLIC_REQUIRED_REPORT_REFS_MISSING')
        elif not isinstance(expected,(list,tuple)) or len(expected)!=5:
            check('expected-reports','FAIL','PUBLIC_REQUIRED_REPORT_REFS_INVALID')
            expected=None
        else:
            try:
                if any(not isinstance(r,ExactRef) for r in expected):raise ValueError
                pairs=[(ExactRef.from_mapping(r.to_dict()).object_id,r.content_sha256) for r in expected]
                if len(set(pairs))!=5 or pairs!=sorted(pairs):raise ValueError
            except (ValueError,TypeError,KeyError):
                check('expected-reports','FAIL','PUBLIC_REQUIRED_REPORT_REFS_INVALID')
                expected=None
            else:
                expected=tuple(expected)
                check('expected-reports','PASS','PUBLIC_EXPECTED_COMPARISON_SET_ONLY')
                for n,r in enumerate(expected):typed_ref(r,'report-'+str(n))

        candidate=read(acceptance_ref,'acceptance')
        manifest=read(manifest_ref,'manifest')
        if candidate is not None:
            try:validate_manifest_acceptance_v3_contract(candidate)
            except ValueError:
                check('contract','FAIL','PUBLIC_MA3_CONTRACT_INVALID')
            else:
                acceptance=candidate
                check('contract','PASS','PUBLIC_MA3_LOCAL_CONTRACT_ONLY')
                if candidate['decision']=='REJECT':
                    check('decision','FAIL','PUBLIC_MA3_DECISION_REJECT')
        if acceptance is not None and manifest is not None and root_ref is not None and rule_ref is not None and expected is not None:
            checks.extend(check_manifest_acceptance_v3_bindings(manifest,acceptance,
                bootstrap_root_ref=root_ref.to_dict(),acceptance_rule_ref=rule_ref.to_dict(),
                required_validation_report_refs=[r.to_dict() for r in expected]))
        else:
            check('bindings','UNKNOWN','PUBLIC_BINDING_PREREQUISITES_UNAVAILABLE')
        if expected is not None:
            for n,r in enumerate(expected):read(r,'report-'+str(n))

    return {'checks':tuple(checks),'input_refs':tuple(dict.fromkeys(refs)),
            'declarations':tuple(declarations),'observations':tuple(observations),
            'limitations':('COMPARISON_CONTROLS_NOT_INDEPENDENT_AUTHORITY',
                'REPORT_IDENTITY_ONLY_NOT_CONTENT_OR_STRONG_REPLAY',
                'RAW_OBSERVATION_NOT_SIGNING_PROJECTION',
                'LOCAL_SIZE_LIMIT_NOT_PROTOCOL_INVALIDITY',
                'G02_AND_PUBLIC_CORE_AUTHORITY_NOT_ESTABLISHED')},acceptance


def replay_initial_acceptance(basis,resolver,*,public_inputs=None):
    if public_inputs is not None and basis.mode!='PUBLIC_EVIDENCE':
        raise ValueError('PUBLIC_INPUTS_REQUIRE_PUBLIC_EVIDENCE')
    requirements=reconstruct_requirements(basis,resolver)
    cycles=reconstruct_cycle_universe(basis,resolver)
    qualifications=replay_qualification_scope(basis,cycles,requirements,resolver)
    scientific=replay_confirmatory_checks(basis,cycles,qualifications,resolver)
    public=basis!=_fixed_basis()
    runtime=None;reports={};report_evidence={}
    if public:
        # Actual structural derivations still run. Unestablished real semantics
        # are explicit unresolved facts, never missing-input-as-empty PASS.
        from .initial_acceptance_public_auth_v1 import verify_initial_acceptance_public
        acceptance=None
        if public_inputs is not None:
            observation,acceptance=_observe_public_inputs(basis,resolver,public_inputs)
            report_evidence['public_input_observation']=observation
        auth=verify_initial_acceptance_public(basis=basis,acceptance=acceptance,resolver=resolver)
        external=ExternalReplay((),(),tuple(Check('public',auth.status,reason) for reason in auth.reason_codes),(),'UNKNOWN',(),model_only=False)
        missing_basis=tuple(c for c in requirements.diagnostics if c.reason_code=='INDEPENDENT_BASIS_MISSING')
        native={c.check:NativeReplay((Check(c.check,'UNKNOWN','PUBLIC_CORE_AUTHORITY_NOT_ESTABLISHED'),*missing_basis),requirements.required_sources) for c in requirements.requirements}
        rows=emit_records(requirements,native,__file__)
    else:
        external=replay_external_evidence(basis,cycles,qualifications,scientific,resolver)
        try:runtime=observe_model_runtime()
        except Exception:runtime=None
        native,errors,bitcoin,objects=replay_integration_checks(basis,requirements,resolver,runtime)
        reports,report_evidence=_reports(basis,requirements,resolver,native,bitcoin,qualifications)
        from .presigning_model_v1 import verify_presigning_chronology
        chronology=verify_presigning_chronology(basis,resolver,external,reports)
        retained=native['retention_before_acceptance']
        native['retention_before_acceptance']=NativeReplay(retained.checks+chronology.checks,tuple(dict.fromkeys(retained.input_refs+chronology.input_refs)),True)
        report_evidence['final-model-chronology']={'checks':chronology.checks,'input_refs':chronology.input_refs}
        from .external_model_pins_v1 import MODEL_EXTERNAL_ALL_REFS
        acceptance=replay_acceptance_bindings(basis,requirements,resolver,acceptance_ref=ExactRef.from_mapping(MODEL_EXTERNAL_ALL_REFS['complete-initial-acceptance']),report_refs=tuple(ExactRef.from_mapping(MODEL_EXTERNAL_ALL_REFS['report-'+r]) for r in REPORT_CHECKS),component_reports=reports)
        rows=tuple(cycles.records)+tuple(qualifications.records)+tuple(scientific.records)+tuple(external.records)+tuple(acceptance)+emit_records(requirements,native,__file__)
        # Output checks inspect actual raw key/provenance structure. They never
        # certify upstream missing rows by adding diagnostic UNKNOWN padding.
        output_names=('raw_result_coverage','raw_result_precedence','output_exact_bindings','output_independent_replay')
        control_clauses=tuple(c for c in requirements.requirements if c.check in output_names)
        control_keys=tuple(k for c in control_clauses for k in c.keys)
        expected=tuple(k for k in requirements.mandatory_keys if k.role!='CLASS_COMPLETENESS' and k not in control_keys)
        observed=Counter(r.key for r in rows)
        coverage=Check('raw-key-set','PASS' if observed==Counter(expected) else 'FAIL' if requirements.overall=='PASS' else 'UNKNOWN','RAW_OUTPUT_EXACT_COVERAGE')
        binding=Check('raw-bindings','PASS' if rows and all(r.basis==basis and r.raw_result and r.source_ref and r.implementation_ref and r.input_refs for r in rows) else 'FAIL','RAW_OUTPUT_CURRENT_BASIS_AND_PROVENANCE')
        # FAIL priority is tested by T01 and this exact same reducer, not an
        # alternate latest-wins/cache reducer. Current outputs retain all rows.
        execution=(Check('requirements-current',requirements.overall,'CURRENT_RAW_SOURCE_DERIVATION'),
            Check('cycle-current',cycles.overall if len(cycles.cycles)!=3 else 'PASS','CURRENT_INDEPENDENT_CYCLE_REPLAY'),
            Check('qualification-current',qualifications.overall if len(qualifications.admissions)!=33 else reduce_checks(tuple(Check('admission',a.status,'ACTUAL_ADMISSION') for a in qualifications.admissions)),'CURRENT_NATIVE_ADMISSION_REPLAY'),
            Check('method-current',scientific.overall if len(scientific.executions)!=3 else 'PASS','CURRENT_THREE_METHOD_EXECUTIONS'),
            Check('external-current',external.overall if len(external.events)!=10 or not all(e.fresh_execution for e in external.events) else 'PASS','CURRENT_TEN_EXTERNAL_EXECUTIONS'))
        controls={name:NativeReplay((coverage,binding),requirements.required_sources,True) for name in output_names}
        controls['output_independent_replay']=NativeReplay((coverage,binding,*execution),requirements.required_sources,True)
        rows+=emit_records(requirements,controls,__file__)
    rows+=_meta(requirements,rows)
    reduced=_aggregate_g10(requirements.reducer_input(rows))
    public_refs=report_evidence.get('public_input_observation',{}).get('input_refs',())
    refs=tuple(sorted(set(requirements.required_sources+cycles.input_refs+qualifications.input_refs+scientific.input_refs+external.input_refs+tuple(rr for row in rows for rr in row.input_refs)+public_refs),key=lambda x:(x.object_id,x.content_sha256)))
    stable=sha256_hex(development_json({'basis':asdict(basis),'overall':reduced.overall,'mandatory_set_identity':reduced.mandatory_set_identity,'coverage':[asdict(c) for c in reduced.coverage_diagnostics],'raw':raw_trace(reduced.raw_results),'runtime':runtime,'component_evidence':report_evidence,'inputs':[r.to_dict() for r in refs]}))
    return IndependentReplay(reduced,requirements,cycles,qualifications,scientific,external,reports,runtime,stable,refs,not public,SEAMS+ASSUMPTIONS if not public else (),component_evidence=report_evidence)

def stable_report(result):
    report={'overall':result.overall,'fresh_replay_overall':result.reduced.overall,'comparison_checks':[asdict(c) for c in result.comparison_checks],'model_only':result.model_only,'stable_identity':result.stable_identity,'mandatory_set_identity':result.mandatory_set_identity,'raw_count':len(result.raw_results),'coverage':[asdict(c) for c in result.coverage_diagnostics],'seams':list(result.seams),'real_genesis_readiness':result.real_genesis_readiness,'prospective_eligible':False,'protocol_state_change':'NONE'}
    if 'public_input_observation' in result.component_evidence:
        report['public_input_observation']=parse_json_strict(development_json(result.component_evidence['public_input_observation']))
    return report

def validate_persisted_independent_replay(basis,resolver,persisted,*,public_inputs=None):
    current=replay_initial_acceptance(basis,resolver,public_inputs=public_inputs)
    # Comparison cannot erase fresh FAIL/UNKNOWN. Even a cached PASS is not
    # usable without this entire reconstruction from the independent basis.
    if stable_report(current)!=persisted:
        known_marker_mismatch=not isinstance(persisted,dict) or any(persisted.get(k)!=stable_report(current)[k] for k in ('model_only','real_genesis_readiness','prospective_eligible','protocol_state_change'))
        unavailable=current.overall=='UNKNOWN' and not known_marker_mismatch
        check=Check('persisted-output','UNKNOWN' if unavailable else 'FAIL','PERSISTED_CURRENT_REPLAY_UNAVAILABLE' if unavailable else 'PERSISTED_OUTPUT_DIFFERS_FROM_FRESH_REPLAY')
        return replace(current,comparison_checks=(check,))
    return current
