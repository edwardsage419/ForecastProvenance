"""Replay explicitly supplied candidate-binding bytes, never protocol admission.

Only call with an authorized directory containing safe public/development inputs.
No discovery, globbing, recursive reads, signature handling or external actions.
"""
import sys
from pathlib import Path
from consumer import consume, SLOTS, canonical_json, parse_json_strict

def replay(directory):
    base = Path(directory)
    expected = parse_json_strict((base / 'expected.json').read_bytes())
    records = {}
    for slot in SLOTS:
        path = base / (slot + '.json')
        if path.is_file():
            records[slot] = path.read_bytes()
    return consume(expected, records)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: replay.py <explicit-authorized-input-directory>')
    result = replay(sys.argv[1])
    sys.stdout.buffer.write(canonical_json(result) + b'\n')
    # Exit 0 means the limited local binding checks passed, never real readiness.
    raise SystemExit(2 if result['verdict'] == 'REJECT' else
                     (0 if result['binding_verdict'] == 'LOCAL_CANDIDATE_BINDINGS_VERIFIED' else 1))
