"""Keyless finite M1 external kernels, enclosed in model-only typed results.

Crypto/wire/CSPRNG and chain-head/PoW assumptions are explicit model facts.
No real signature, packet backend, Bitcoin executable/node or network is used.
All hash, nonce, binding, transcript, retry, admission-consumer and time arithmetic
outside those named assumptions must actually execute; labels are not authority.
"""
from decimal import Decimal, localcontext, ROUND_CEILING
from pathlib import Path
from hashlib import sha256
from .canonical import canonical_json, seal_object, sha256_hex, require_utc_timestamp
from .core import Check
from ._roughtime_support import derive_nonce_v2_hex, _parse_precise_utc_ns
from .claim_authority_v1_legacy import _ceil_ns_to_utc_seconds
from .replay_records_v1 import reduce_checks

WALL_CHECKS=('wall_subject_nonce','wall_signature_delegation','wall_provider_independence',
    'wall_quorum_transcript','wall_conservative_bound','deadline_subject_frozen','deadline_upper_bound',
    'bitcoin_subject_bundle','bitcoin_pin_chain','bitcoin_fresh_execution')

class Unavailable(ValueError):pass

def ref(obj):return {k:obj[k] for k in ('object_id','content_sha256')}
def need(inputs,name):
    obj=inputs['objects'].get(name)
    if obj is None:raise Unavailable(name)
    return obj

def raw(inputs,reference):
    value=inputs['raw'].get(reference['object_id'])
    if value is None:raise Unavailable('raw input')
    if not isinstance(value,bytes) or sha256_hex(value)!=reference['content_sha256']:raise ValueError('raw hash mismatch')
    return value

def merkle_leaf(value):return sha256(b'M1_MODEL_MERKLE_LEAF\x00'+value).hexdigest()
def merkle_parent(left,right):return sha256(b'M1_MODEL_MERKLE_NODE\x00'+bytes.fromhex(left)+bytes.fromhex(right)).hexdigest()

def retry_transition(before,attempts,started_ns):
    """v3 numeric persistence/reset counterpart; no transport side effects."""
    state=dict(before)
    encoded=type(state['retry_not_before_ns']) is str
    if encoded:
        if not state['retry_not_before_ns'].isdigit() or str(int(state['retry_not_before_ns']))!=state['retry_not_before_ns']:raise ValueError('retry state encoding')
        state['retry_not_before_ns']=int(state['retry_not_before_ns'])
    if type(state['failures']) is not int or state['failures']<0 or type(state['retry_not_before_ns']) is not int or state['retry_not_before_ns']<0:raise ValueError('retry state')
    for attempt in attempts:
        if attempt['outcome'] in ('QUALIFYING_VERIFIED_RESPONSE','VERIFIED_NONQUALIFYING_RESPONSE'):
            state={'failures':0,'retry_not_before_ns':0}
        elif attempt['outcome']=='FAILED':
            state['failures']+=1
            with localcontext() as dc:
                dc.prec=50
                delay=min(Decimal(86400),Decimal('1.5')**(state['failures']-1))
                ns=int((delay*Decimal(1_000_000_000)).to_integral_value(rounding=ROUND_CEILING))
            state['retry_not_before_ns']=started_ns+attempt['started_offset_ns']+attempt['duration_ns']+ns
        else:raise ValueError('unknown attempt outcome')
    if encoded:state['retry_not_before_ns']=str(state['retry_not_before_ns'])
    return state


def verify_model_bitcoin(inputs,context):
    """Fresh model inclusion/chain computation, not real strong Bitcoin verification."""
    proof=need(inputs,'proof');chain=need(inputs,'chain');bundle=need(inputs,'bundle')
    bundlebytes=canonical_json(bundle)
    if proof['bundle_ref']!=ref(bundle) or proof['subject_ref']!=context['subject_ref'] or proof['bundle_sha256']!=sha256_hex(bundlebytes):raise ValueError('proof bundle subject')
    leaf=merkle_leaf(bundlebytes)
    if proof['leaf_hash']!=leaf:raise ValueError('proof leaf')
    value=leaf
    for item in proof['path']:
        if set(item)!={'side','hash'} or item['side'] not in ('LEFT','RIGHT'):raise ValueError('proof path')
        value=merkle_parent(item['hash'],value) if item['side']=='LEFT' else merkle_parent(value,item['hash'])
    nodes=chain['nodes']
    if len(nodes)!=context['chain_node_count'] or not nodes:raise ValueError('complete model chain')
    hashes=[]
    for index,node in enumerate(nodes):
        payload={k:v for k,v in node.items() if k!='node_hash'}
        if node['sequence']!=index or node['previous']!=('NONE' if index==0 else hashes[-1]) or node['node_hash']!=sha256_hex(canonical_json(payload)):raise ValueError('chain predecessor/hash')
        hashes.append(node['node_hash'])
    if hashes[-1]!=context['trusted_chain_head'] or chain['head_trust']!='EXPLICIT_MODEL_CHAIN_SEAM' or chain['real_bitcoin_core'] is not False:raise ValueError('independent model chain trust')
    index=proof['anchor_index']
    if type(index) is not int or not(0<=index<len(nodes)) or nodes[index]['merkle_root']!=value or len(nodes)-index<context['minimum_confirmations']:raise ValueError('inclusion/confirmations')
    report={'subject_ref':context['subject_ref'],'bundle_ref':ref(bundle),'proof_ref':ref(proof),'chain_ref':ref(chain),
        'bundle_sha256':sha256_hex(bundlebytes),'root':value,'head':hashes[-1],'confirmations':len(nodes)-index,
        'status':'PASS','model_only':True,'real_bitcoin_verification':False}
    return report


def reconstruct_model_bitcoin_report(inputs,context):
    """Identity derived from current computation, never from persisted PASS."""
    return seal_object({'model_only':True,'status':'PASS','recomputed':verify_model_bitcoin(inputs,context)},
        object_type='SyntheticBitcoinReplayObservation',stable_context='M1_DEVELOPMENT_ONLY',
        semantic_id='model:external:'+context['name']+'-report')


def evaluate_preoutcome_binding(dvr,cycle_inputs,cycle_context,*,frozen_barrier,dvr_upper_bound):
    """X04 model core: an earlier record must commit the exact completed replay."""
    checks=[]
    def record(name,fn):
        try:
            ok=fn();checks.append(Check(name,'PASS' if ok is True else 'FAIL','MODEL_X04_EXACT_BINDING' if ok is True else 'MODEL_X04_BINDING_MISMATCH'))
        except Unavailable:checks.append(Check(name,'UNKNOWN','MODEL_X04_EVIDENCE_UNAVAILABLE'))
        except (ValueError,KeyError,TypeError,AttributeError,IndexError,ArithmeticError):checks.append(Check(name,'FAIL','MODEL_X04_BINDING_INVALID'))
        except Exception as exc:checks.append(Check(name,'UNKNOWN','MODEL_X04_REPLAY_UNAVAILABLE_'+type(exc).__name__))
    def required(key):
        if dvr is None or key not in dvr:raise Unavailable(key)
        return dvr[key]
    # Evaluate conjuncts separately so an absent proof cannot mask a known
    # wrong primary/bundle binding in an otherwise observable record.
    record('dvr_primary_subject',lambda:required('primary_subject_ref')==cycle_context['subject_ref'] and required('cycle_manifest_ref')==cycle_context['subject_ref'] and required('contains_outcome') is False)
    record('dvr_bundle_reference',lambda:required('primary_bundle_ref')==ref(need(cycle_inputs,'bundle')))
    record('dvr_proof_reference',lambda:required('bitcoin_proof_ref')==ref(need(cycle_inputs,'proof')))
    record('dvr_computation_reference',lambda:required('bitcoin_computation_ref')==ref(reconstruct_model_bitcoin_report(cycle_inputs,cycle_context)))
    record('dvr_current_implementation',lambda:sha256_hex(Path(__file__).read_bytes())==cycle_context['runtime']['engine_sha256'])
    def barrier():
        if dvr_upper_bound is None:raise Unavailable('DVR existence bound')
        require_utc_timestamp(frozen_barrier);require_utc_timestamp(dvr_upper_bound)
        return required('outcome_barrier')==frozen_barrier and dvr_upper_bound<=frozen_barrier
    record('dvr_preoutcome_barrier',barrier)
    return tuple(checks)


def evaluate_external_event(inputs,context):
    """Internal raw model kernel; independently fixed context is never a full claim."""
    checks=[];computed_upper=None; fresh=False;bitcoin=None;derived_after={};computed_report_ref=None
    def record(name,fn):
        try:
            ok=fn();checks.append(Check(name,'PASS' if ok is True else 'FAIL','OK' if ok is True else name.upper()+'_MISMATCH'))
        except Unavailable:checks.append(Check(name,'UNKNOWN','MODEL_EXTERNAL_EVIDENCE_UNAVAILABLE'))
        except (ValueError,KeyError,TypeError,AttributeError,IndexError,ArithmeticError):checks.append(Check(name,'FAIL',name.upper()+'_INVALID'))
        except Exception as exc:checks.append(Check(name,'UNKNOWN','MODEL_EXTERNAL_KERNEL_UNAVAILABLE_'+type(exc).__name__))
    def binding():
        b=need(inputs,'bundle');e=need(inputs,'execution')
        if b['subject_ref']!=context['subject_ref'] or b['origin']!='SYNTHETIC_ONLY' or e['subject_ref']!=context['subject_ref']:return False
        challenges=[]
        for row in e['providers']:
            challenge=row['public_challenge_hex'];challenges.append(challenge)
            if len(challenge)!=64 or row['challenge_origin']!='EXPLICIT_MODEL_CSPRNG_SEAM':return False
            nonce=derive_nonce_v2_hex(context['subject_ref']['content_sha256'],challenge)
            if nonce!=row['nonce_hex'] or row['profile_ref']!=context['provider_refs'][row['provider']]:return False
            request=raw(inputs,row['request_ref'])
            from .canonical import parse_json_strict
            decoded=parse_json_strict(request)
            if decoded!={'model_only':True,'provider':row['provider'],'subject_ref':context['subject_ref'],'nonce_hex':nonce,'packet_assumption':'MODEL_LOGICAL_DECODED_PACKET'}:return False
        return len(challenges)==3 and len(set(challenges))==3
    record('wall_subject_nonce',binding)
    def authentication():
        a=need(inputs,'authentication');e=need(inputs,'execution');b=need(inputs,'bundle')
        if b['authentication_ref']!=ref(a) or b['contract_ref']!=context['contract_ref']:return False
        facts={f['provider']:f for f in a['provider_facts']}
        if len(facts)!=len(a['provider_facts']) or a['assumption']!='EXPLICIT_MODEL_AUTH_SEAM':return False
        expected={row['provider'] for row in e['providers'] if any(t['outcome'] in ('QUALIFYING_VERIFIED_RESPONSE','VERIFIED_NONQUALIFYING_RESPONSE') for t in row['attempts'])}
        if set(facts)-expected:return False
        if expected-set(facts):raise Unavailable('authentication provider coverage')
        for row in e['providers']:
            terminal=[t for t in row['attempts'] if t['outcome'] in ('QUALIFYING_VERIFIED_RESPONSE','VERIFIED_NONQUALIFYING_RESPONSE')]
            if not terminal:continue
            fact=facts.get(row['provider'])
            if fact is None:raise Unavailable('authentication fact')
            if fact['model_status']!='VALID' or fact['subject_ref']!=context['subject_ref'] or fact['nonce_hex']!=row['nonce_hex'] or fact['request_ref']!=row['request_ref'] or fact['response_ref']!=terminal[0]['response_ref'] or fact['provider_profile_ref']!=context['provider_refs'][row['provider']]:return False
            response=raw(inputs,fact['response_ref'])
            from .canonical import parse_json_strict
            payload=parse_json_strict(response)
            expected={k:fact[k] for k in ('provider','nonce_hex','midpoint','radius_ns')}
            if payload!={'model_only':True,**expected}:return False
            mid=_parse_precise_utc_ns(fact['midpoint'],'midpoint');start=_parse_precise_utc_ns(fact['delegation_from'],'delegation_from');end=_parse_precise_utc_ns(fact['delegation_until'],'delegation_until')
            if not(start<=mid<=end) or type(fact['radius_ns']) is not int or fact['radius_ns']<0:return False
        return True
    record('wall_signature_delegation',authentication)
    record('wall_provider_independence',lambda: set(context['provider_groups'])=={'p1','p2','p3'} and len(set(context['provider_groups'].values()))==3)
    def transcript():
        nonlocal derived_after
        e=need(inputs,'execution');before=need(inputs,'retry_before');after=need(inputs,'retry_after');b=need(inputs,'bundle')
        if [r['provider'] for r in e['providers']]!=['p1','p2','p3'] or before['providers']!=context['expected_retry_before']:return False
        if e['contract_ref']!=context['contract_ref'] or before['root_ref']!=context['root_ref'] or after['root_ref']!=context['root_ref'] or before['predecessor_ref']!=context['previous_retry_ref'] or after['predecessor_ref']!=ref(before):return False
        core={k:v for k,v in e.items() if k not in {'object_id','object_type','payload_sha256','content_sha256','transcript_sha256'}}
        if e['transcript_sha256']!=sha256_hex(canonical_json(core)) or b['execution_ref']!=ref(e):return False
        for row in e['providers']:
            provider=row['provider'];attempts=row['attempts'];state=before['providers'][provider]
            now=_parse_precise_utc_ns(e['evaluated_at'],'evaluated_at')
            if row['transport']!='UDP' or row['packet_rule']!='STANDARD_1024_BODY_ONLY_ASSUMED' or row['version_offer']!=['MODEL_FROZEN_WIRE'] or len(attempts)>2:return False
            if int(state['retry_not_before_ns'])>now:
                if attempts or row['terminal']!='BACKOFF_ACTIVE':return False
                derived_after[provider]=dict(state);continue
            if not attempts:return False
            seen_terminal=False; earliest=now
            for i,t in enumerate(attempts,1):
                if t['sequence']!=i or t['request_ref']!=row['request_ref'] or type(t['duration_ns']) is not int or not(0<t['duration_ns']<=2_000_000_000) or seen_terminal:return False
                if type(t['started_offset_ns']) is not int or t['started_offset_ns']<0 or now+t['started_offset_ns']<earliest or i==1 and t['started_offset_ns']!=0:return False
                raw(inputs,t['request_ref'])
                if t['outcome'] in ('QUALIFYING_VERIFIED_RESPONSE','VERIFIED_NONQUALIFYING_RESPONSE'):
                    raw(inputs,t['response_ref']);seen_terminal=True
                    if t['failure_code']!='NONE' and t['outcome']=='QUALIFYING_VERIFIED_RESPONSE':return False
                    facts={f['provider']:f for f in need(inputs,'authentication')['provider_facts']}
                    f=facts.get(provider)
                    if f is None:raise Unavailable('receipt classification fact')
                    q=f['model_status']=='VALID' and type(f['radius_ns']) is int and f['radius_ns']>0 and _parse_precise_utc_ns(f['midpoint'],'midpoint')+f['radius_ns']<=_parse_precise_utc_ns(context['frozen_cutoff'],'cutoff')
                    if t['outcome']!=('QUALIFYING_VERIFIED_RESPONSE' if q else 'VERIFIED_NONQUALIFYING_RESPONSE'):return False
                elif t['outcome']=='FAILED':
                    if t['failure_code'] not in ('TIMEOUT','INVALID_RESPONSE') or t['duration_ns']!=2_000_000_000 and t['failure_code']=='TIMEOUT':return False
                else:return False
                expected_trace={'model_only':True,'provider':provider,'sequence':i,'outcome':t['outcome'],'request_ref':row['request_ref'],'response_ref':t['response_ref'],'crypto_verification':'MODEL_AUTH_ASSUMPTION' if seen_terminal else 'NO_VERIFIED_RESPONSE'}
                if t['verification_trace']!=expected_trace or t['verification_trace_sha256']!=sha256_hex(canonical_json(expected_trace)):return False
                earliest=int(retry_transition(state,attempts[:i],now)['retry_not_before_ns'])
            if row['terminal']!=attempts[-1]['outcome']:return False
            if not seen_terminal and len(attempts)!=2:return False
            derived_after[provider]=retry_transition(state,attempts,now)
        return after['providers']==derived_after and e['retry_before_ref']==ref(before) and e['retry_after_ref']==ref(after)
    record('wall_quorum_transcript',transcript)
    def bound():
        nonlocal computed_upper
        e=need(inputs,'execution');a=need(inputs,'authentication');b=need(inputs,'bundle')
        facts={f['provider']:f for f in a['provider_facts']};upper=[]
        authstatus=next(c for c in checks if c.check_id=='wall_signature_delegation').status
        if authstatus=='FAIL':return False
        if authstatus!='PASS':raise Unavailable('authenticated decoded time')
        for row in e['providers']:
            if row['terminal']!='QUALIFYING_VERIFIED_RESPONSE':continue
            f=facts[row['provider']]
            if type(f['radius_ns']) is not int or f['radius_ns']<=0:return False
            ns=_parse_precise_utc_ns(f['midpoint'],'midpoint')+f['radius_ns']
            if ns>_parse_precise_utc_ns(context['frozen_cutoff'],'frozen_cutoff'):return False
            upper.append((row['provider'],ns))
        if len({p for p,_ in upper})<2:return False
        computed_upper=_ceil_ns_to_utc_seconds(max(ns for _,ns in upper))
        return b['reported_upper_bound']==computed_upper
    record('wall_conservative_bound',bound)
    record('deadline_subject_frozen',lambda: need(inputs,'bundle')['subject_ref']==context['subject_ref'] and need(inputs,'bundle')['frozen_cutoff']==context['frozen_cutoff'])
    def deadline():
        value=need(inputs,'bundle')['reported_upper_bound'];require_utc_timestamp(value);require_utc_timestamp(context['frozen_cutoff'])
        return value<=context['frozen_cutoff']
    record('deadline_upper_bound',deadline)
    record('bitcoin_subject_bundle',lambda: need(inputs,'proof')['subject_ref']==context['subject_ref'] and need(inputs,'proof')['bundle_ref']==ref(need(inputs,'bundle')))
    def pinchain():
        chain=need(inputs,'chain')
        actual=sha256_hex(Path(__file__).read_bytes())
        return actual==context['runtime']['engine_sha256'] and chain['scope']==context['chain_scope'] and chain['head_ref']==context['trusted_chain_head'] and chain['head_trust']=='EXPLICIT_MODEL_CHAIN_SEAM'
    record('bitcoin_pin_chain',pinchain)
    def bitcoinfresh():
        nonlocal fresh,bitcoin,computed_report_ref
        if next(c for c in checks if c.check_id=='bitcoin_pin_chain').status!='PASS':raise Unavailable('pinned model chain')
        computed=reconstruct_model_bitcoin_report(inputs,context);bitcoin=computed['recomputed'];computed_report_ref=ref(computed);fresh=True
        persisted=need(inputs,'report')
        return canonical_json(persisted)==canonical_json(computed)
    record('bitcoin_fresh_execution',bitcoinfresh)
    return tuple(checks),{'upper_bound':computed_upper,'fresh_execution':fresh,'bitcoin':bitcoin,'computed_report_ref':computed_report_ref,'retry_after':derived_after,'model_only':True,'real_verification':False}
