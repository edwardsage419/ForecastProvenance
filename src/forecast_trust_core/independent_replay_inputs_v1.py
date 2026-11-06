"""Fixed installed model catalogue; a caller directory only locates bytes."""
from pathlib import Path
from .authority_primitives_v1 import ExactRef

def _read_safe(root,relative):
    candidate=root/relative
    if Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise ValueError('unsafe corpus path')
    current=root
    if root.is_symlink(): raise ValueError('symlink corpus')
    for part in Path(relative).parts:
        current=current/part
        if current.is_symlink(): raise ValueError('symlink corpus input')
    try: return candidate.read_bytes()
    except FileNotFoundError: return None

class CorpusResolver:
    def __init__(self,corpus):
        from .integration_model_pins_v1 import MODEL_FILE_CATALOG,MODEL_COPY_REFS
        self.root=Path(corpus).absolute()
        self.data={};self.copies={};self.file_bytes={}
        for entry in MODEL_FILE_CATALOG:
            ref=ExactRef(entry["object_id"],entry["content_sha256"]);raw=_read_safe(self.root,entry['path'])
            self.file_bytes[entry['path']]=raw
            if raw is not None: self.data[ref]=raw
        for group,entries in MODEL_COPY_REFS.items():
            for entry in entries:
                ref=ExactRef(entry["object_id"],entry["content_sha256"])
                raw=_read_safe(self.root,entry['copy_path'])
                if raw is not None:self.copies[(group,ref)]=raw
    def resolve_exact(self,ref):return self.data.get(ref)
    def resolve_copy_exact(self,group,ref):return self.copies.get((group,ref))
