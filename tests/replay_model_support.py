"""Only retained, keyless synthetic public model data; no signing fixtures."""
from pathlib import Path
import json
from dataclasses import replace

from forecast_trust_core.authority_primitives_v1 import ExactRef
from forecast_trust_core.g10_replay_v1 import ReplayBasis

CORPUS = Path(__file__).parent / "fixtures" / "independent_replay_v1"


class ModelResolver:
    def __init__(self):
        self.data = {}
        for path in sorted((CORPUS / "sources").glob("*.json")) + sorted((CORPUS / "objects").glob("*.json")):
            raw = path.read_bytes()
            obj = json.loads(raw)
            self.data[ExactRef(obj["object_id"], obj["content_sha256"])] = raw

    def resolve_exact(self, ref):
        return self.data.get(ref)


def model_basis(mode="SYNTHETIC_MODEL"):
    d = json.loads((CORPUS / "model_basis.json").read_text())
    for k, v in tuple(d.items()):
        if isinstance(v, dict):
            d[k] = ExactRef.from_mapping(v)
    d["profile"] = tuple(ExactRef.from_mapping(v) for v in d["profile"])
    d["mode"] = mode
    return ReplayBasis(**d)


def changed_basis(**updates):
    return replace(model_basis(), **updates)
