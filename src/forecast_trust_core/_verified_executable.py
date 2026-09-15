from __future__ import annotations

import hashlib
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


def _hex64(value: str) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(ch in "0123456789abcdef" for ch in value)
    )


@dataclass(frozen=True)
class PinnedExecutable:
    source_path: Path
    sha256: str
    content: bytes
    suffix: str

    @classmethod
    def load(
        cls,
        path: Path,
        expected_sha256: str,
        *,
        label: str,
    ) -> "PinnedExecutable":
        if not _hex64(expected_sha256):
            raise ValueError(f"{label} expected SHA256 must be 64 lowercase hex characters")
        raw_path = Path(path)
        if raw_path.is_symlink():
            raise ValueError(f"{label} must not be a symlink")
        try:
            resolved = raw_path.resolve(strict=True)
        except OSError as exc:
            raise ValueError(f"{label} path cannot be resolved") from exc
        if resolved.is_symlink() or not resolved.is_file():
            raise ValueError(f"{label} must be a regular non-symlink file")
        try:
            content = resolved.read_bytes()
        except OSError as exc:
            raise ValueError(f"{label} bytes cannot be read") from exc
        actual_sha256 = hashlib.sha256(content).hexdigest()
        if actual_sha256 != expected_sha256:
            raise ValueError(f"{label} SHA256 mismatch")
        return cls(
            source_path=resolved,
            sha256=expected_sha256,
            content=content,
            suffix=resolved.suffix,
        )

    @contextmanager
    def snapshot(self, *, prefix: str) -> Iterator[Path]:
        with tempfile.TemporaryDirectory(prefix=prefix) as directory:
            root = Path(directory)
            name = "verified-executable" + self.suffix
            snapshot = root / name
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            fd = os.open(snapshot, flags, 0o700)
            ok = False
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(self.content)
                    handle.flush()
                    os.fsync(handle.fileno())
                snapshot.chmod(0o700)
                if hashlib.sha256(snapshot.read_bytes()).hexdigest() != self.sha256:
                    raise ValueError("verified executable snapshot SHA256 mismatch")
                ok = True
            finally:
                if not ok:
                    try:
                        snapshot.unlink()
                    except FileNotFoundError:
                        pass
            yield snapshot
