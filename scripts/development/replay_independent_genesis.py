#!/usr/bin/env python3
"""Offline keyless M1 demo. No real protocol action or user-supplied code."""
import argparse
from pathlib import Path
from datetime import datetime,timezone
from dataclasses import asdict,replace
import json
import sys
try:
    from forecast_trust_core.g10_requirements_v1 import _fixed_basis
    from forecast_trust_core.independent_replay_v1 import CorpusResolver,replay_initial_acceptance,stable_report,development_json,raw_trace
    from forecast_trust_core.canonical import canonical_json,sha256_hex
except ImportError as exc:
    print(json.dumps({'error':'STARTUP_ENVIRONMENT_UNAVAILABLE','detail':type(exc).__name__}),file=sys.stderr)
    sys.exit(3)

class DemoParser(argparse.ArgumentParser):
    def error(self,message):raise ValueError(message)

def main():
    parser=DemoParser(description=__doc__)
    parser.add_argument('--corpus',type=Path,required=True)
    parser.add_argument('--mode',choices=('synthetic-model','public-evidence'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    try:
        args=parser.parse_args()
        if not args.corpus.is_dir() or args.output.exists():raise ValueError('corpus must exist; output must be a new directory')
        basis=replace(_fixed_basis(),mode='SYNTHETIC_MODEL' if args.mode=='synthetic-model' else 'PUBLIC_EVIDENCE')
        result=replay_initial_acceptance(basis,CorpusResolver(args.corpus))
        report=stable_report(result)
        trace={'basis':asdict(basis),**raw_trace(result.raw_results),
            'required_sources':[r.to_dict() for r in result.requirements.required_sources],
            'source_locations':[asdict(x) for x in result.requirements.inventory],
            'clauses':[asdict(x) for x in result.requirements.requirements],
            'M':[asdict(x) for x in result.requirements.mandatory_keys],
            'completeness_derivations':result.requirements.derivations,
            'runtime':result.runtime,'component_reports':{k:[asdict(c) for c in v] for k,v in result.component_reports.items()},
            'component_raw_evidence':result.component_evidence,
            'scientific_executions':result.scientific.executions,'scientific_squared_errors':result.scientific.scored_squared_errors,
            'external_events':[{'name':e.name,'checks':[asdict(c) for c in e.checks],'trace':e.trace,'fresh_execution':e.fresh_execution} for e in result.external.events],
            'qualification_admissions':[{'provider':a.provider,'boundary_ref':a.boundary_ref.to_dict(),'status':a.status,'admitted':a.admitted} for a in result.qualifications.admissions]}
        args.output.mkdir(parents=True,exist_ok=False)
        (args.output/'result.json').write_bytes(canonical_json(report))
        (args.output/'raw-trace.json').write_bytes(development_json(trace))
        (args.output/'audit.json').write_bytes(canonical_json({'generated_at':datetime.now(timezone.utc).isoformat(),'stable_identity':result.stable_identity,'timestamp_is_stable':False}))
        print(json.dumps(report,sort_keys=True))
        return {'PASS':0,'FAIL':1,'UNKNOWN':2}[result.overall]
    except Exception as exc:
        print(json.dumps({'error':type(exc).__name__,'message':str(exc),'real_genesis_readiness':'NOT_ESTABLISHED','prospective_eligible':False,'protocol_state_change':'NONE'}),file=sys.stderr)
        return 3
if __name__=='__main__':sys.exit(main())
