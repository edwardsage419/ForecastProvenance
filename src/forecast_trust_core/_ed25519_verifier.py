from __future__ import annotations

import base64
import hashlib
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical import canonical_json, parse_json_strict

REQUEST_SCHEMA_VERSION = "1.0"
REQUEST_OBJECT_TYPE = "Ed25519VerificationRequest"
RESULT_OBJECT_TYPE = "Ed25519VerificationResult"
MAX_MESSAGE_BYTES = 1024 * 1024
MAX_OUTPUT_BYTES = 4096
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bytes(value: Any, name: str, expected_len: int | None = None) -> bytes:
    if not isinstance(value, bytes):
        raise ValueError(f"{name} must be bytes")
    if expected_len is not None and len(value) != expected_len:
        raise ValueError(f"{name} must be exactly {expected_len} bytes")
    return value


def _parse_result(data: bytes) -> bool:
    if len(data) > MAX_OUTPUT_BYTES:
        raise ValueError("Ed25519 verifier output exceeds size limit")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Ed25519 verifier output must be UTF-8") from exc
    result = parse_json_strict(text)
    if not isinstance(result, dict):
        raise ValueError("Ed25519 verifier output must be an object")
    if set(result) != {"schema_version", "object_type", "valid"}:
        raise ValueError("Ed25519 verifier output fields invalid")
    if result["schema_version"] != REQUEST_SCHEMA_VERSION:
        raise ValueError("Ed25519 verifier output schema_version mismatch")
    if result["object_type"] != RESULT_OBJECT_TYPE:
        raise ValueError("Ed25519 verifier output object_type mismatch")
    if not isinstance(result["valid"], bool):
        raise ValueError("Ed25519 verifier output valid must be boolean")
    return result["valid"]


@dataclass(frozen=True)
class PinnedEd25519Verifier:
    binary_path: Path
    binary_sha256: str
    timeout_seconds: int = 5

    def __post_init__(self) -> None:
        path = Path(self.binary_path)
        object.__setattr__(self, "binary_path", path)
        if not isinstance(self.binary_sha256, str) or HEX64_RE.fullmatch(self.binary_sha256) is None:
            raise ValueError("binary_sha256 must be 64 lowercase hex characters")
        if not isinstance(self.timeout_seconds, int) or isinstance(self.timeout_seconds, bool) or not 1 <= self.timeout_seconds <= 30:
            raise ValueError("timeout_seconds must be an integer from 1 through 30")

    def _validate_binary(self) -> None:
        path = self.binary_path
        if path.is_symlink() or not path.is_file():
            raise ValueError("Ed25519 verifier binary must be a regular non-symlink file")
        if _sha256_file(path) != self.binary_sha256:
            raise ValueError("Ed25519 verifier binary SHA256 mismatch")

    def __call__(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        public_key = _bytes(public_key, "public_key", 32)
        message = _bytes(message, "message")
        signature = _bytes(signature, "signature", 64)
        if len(message) > MAX_MESSAGE_BYTES:
            raise ValueError("message exceeds Ed25519 verifier size limit")
        self._validate_binary()
        request = {
            "schema_version": REQUEST_SCHEMA_VERSION,
            "object_type": REQUEST_OBJECT_TYPE,
            "public_key_base64": base64.b64encode(public_key).decode("ascii"),
            "message_base64": base64.b64encode(message).decode("ascii"),
            "signature_base64": base64.b64encode(signature).decode("ascii"),
        }
        request_bytes = canonical_json(request)
        try:
            completed = subprocess.run(
                [os.fspath(self.binary_path)],
                input=request_bytes,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=self.timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ValueError("Ed25519 verifier process failed") from exc
        if len(completed.stderr) > MAX_OUTPUT_BYTES:
            raise ValueError("Ed25519 verifier stderr exceeds size limit")
        if _sha256_file(self.binary_path) != self.binary_sha256:
            raise ValueError("Ed25519 verifier binary changed during execution")
        if completed.returncode != 0:
            raise ValueError("Ed25519 verifier rejected the verification request")
        return _parse_result(completed.stdout)
