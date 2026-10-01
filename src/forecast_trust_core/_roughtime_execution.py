from __future__ import annotations

import base64
import hashlib
import json
import os
import socket
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from .canonical import canonical_json, parse_json_strict, seal_object
from ._verified_executable import PinnedExecutable
from ._roughtime_control import (
    record_failure,
    reset_root_state,
    validate_authorization_control_binding, validate_report_control_binding,
    validate_retry_state,
    validate_verifier_build_profile,
)
from ._roughtime_plan import validate_authorization_record, validate_plan
from ._roughtime_profile import (
    FAILURE_CODES,
    PACKET_PROFILE,
    PROVIDERS,
    PROVIDER_ORDER,
    VERIFIED_NONQUALIFYING_CODES,
    VERIFIER_COMMIT,
    VERIFIER_REPOSITORY,
    VERIFIER_TAG,
)
from ._roughtime_receipt import validate_receipt
from ._roughtime_report import validate_rehearsal_report
from ._roughtime_support import _format_precise_utc_ns, _parse_utc, _provider_public_fields, _sha256_hex


@dataclass(frozen=True)
class PreparedDestination:
    family: int
    address: str
    port: int


@dataclass(frozen=True)
class TransportOutcome:
    status: str
    destination: PreparedDestination
    sent: bool
    send_utc: str
    receive_utc: str | None = None
    response_bytes: bytes | None = None
    source_address: str | None = None
    source_port: int | None = None
    detail: str = ""


@dataclass(frozen=True)
class VerifyResult:
    verified: bool
    failure_code: str | None
    detail: str
    transcript: Mapping[str, Any]
    midpoint_utc: str | None = None
    radius_nanoseconds: int | None = None


class UDPTransport(Protocol):
    def prepare_destination(self, host: str, port: int) -> PreparedDestination: ...

    def send_and_receive(
        self, destination: PreparedDestination, request_bytes: bytes, timeout_seconds: int
    ) -> TransportOutcome: ...


class VerifierBackend(Protocol):
    binary_sha256: str

    def build_request(self, provider: Mapping[str, Any]) -> tuple[bytes, Mapping[str, Any]]: ...

    def verify_response(
        self, provider: Mapping[str, Any], request_bytes: bytes, response_bytes: bytes
    ) -> VerifyResult: ...


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_text(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("clock must return a timezone-aware datetime")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _unix_ms(value: datetime) -> int:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("clock must return a timezone-aware datetime")
    return int(value.timestamp() * 1000)


def _root_hash(provider: Mapping[str, Any]) -> str:
    raw = base64.b64decode(provider["root_public_key_base64"], validate=True)
    return hashlib.sha256(raw).hexdigest()


def _write_bytes_exclusive(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    ok = False
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        ok = True
    finally:
        if not ok:
            try:
                path.unlink()
            except FileNotFoundError:
                pass


def _write_json_exclusive(path: Path, value: Mapping[str, Any]) -> None:
    _write_bytes_exclusive(path, canonical_json(dict(value)) + b"\n")


def _assert_safe_new_root(root: Path) -> None:
    if root.exists() and root.is_symlink():
        raise ValueError("execution root must not be a symlink")
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("execution root must be a real directory")
    for parent in (root / "events", root / "consumed"):
        if parent.exists() and parent.is_symlink():
            raise ValueError("execution control directory must not be a symlink")
        parent.mkdir(exist_ok=True)
        if parent.is_symlink() or not parent.is_dir():
            raise ValueError("execution control directory must be a real directory")


class RealUDPTransport:
    """Single-destination UDP transport. No endpoint or protocol fallback is performed."""

    def __init__(self, *, now: Callable[[], datetime] = _utc_now) -> None:
        self._now = now

    def prepare_destination(self, host: str, port: int) -> PreparedDestination:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
        choices = sorted({(family, sockaddr[0], int(sockaddr[1])) for family, _, _, _, sockaddr in infos})
        if not choices:
            raise OSError("DNS returned no UDP destinations")
        family, address, resolved_port = choices[0]
        if resolved_port != port:
            raise OSError("resolved destination changed the frozen port")
        return PreparedDestination(family=family, address=address, port=resolved_port)

    def send_and_receive(
        self, destination: PreparedDestination, request_bytes: bytes, timeout_seconds: int
    ) -> TransportOutcome:
        sent_at = _utc_text(self._now())
        sock = None
        sent = False
        try:
            sock = socket.socket(destination.family, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.settimeout(timeout_seconds)
            sock.connect((destination.address, destination.port))
            written = sock.send(request_bytes)
            if written != len(request_bytes):
                raise OSError("UDP socket reported a partial datagram send")
            sent = True
            try:
                response, source = sock.recvfrom(65535)
            except socket.timeout:
                return TransportOutcome("TIMEOUT", destination, True, sent_at, detail="UDP receive timeout")
            received_at = _utc_text(self._now())
            source_address, source_port = str(source[0]), int(source[1])
            status = "RESPONSE" if (source_address, source_port) == (destination.address, destination.port) else "SOURCE_MISMATCH"
            detail = "" if status == "RESPONSE" else "response source does not equal the resolved frozen destination"
            return TransportOutcome(
                status, destination, True, sent_at, received_at, response, source_address, source_port, detail
            )
        except OSError as exc:
            return TransportOutcome("ERROR", destination, sent, sent_at, detail=f"{type(exc).__name__}: {exc}")
        finally:
            if sock is not None:
                sock.close()


class QualifiedVerifierBackend:
    PROCESS_TIMEOUT_SECONDS = 10

    def __init__(self, binary: Path, build_profile: Mapping[str, Any]) -> None:
        validate_verifier_build_profile(build_profile)
        self.binary_sha256 = build_profile["binary_sha256"]
        self._pinned_executable = PinnedExecutable.load(
            Path(binary),
            self.binary_sha256,
            label="qualified Roughtime verifier binary",
        )

    def _run(self, action: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        with tempfile.TemporaryDirectory(prefix="fpp-roughtime-verifier-") as directory:
            input_path = Path(directory) / "input.json"
            output_path = Path(directory) / "output.json"
            input_path.write_bytes(canonical_json(dict(payload)) + b"\n")
            try:
                with self._pinned_executable.snapshot(prefix="fpp-roughtime-verifier-bin-") as executable:
                    completed = subprocess.run(
                        [str(executable), action, "--input", str(input_path), "--output", str(output_path)],
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=False,
                        timeout=self.PROCESS_TIMEOUT_SECONDS,
                    )
            except subprocess.TimeoutExpired as exc:
                raise ValueError("qualified Roughtime verifier process timed out") from exc
            if completed.returncode != 0:
                detail = completed.stderr.decode("utf-8", errors="replace").strip()
                raise ValueError(detail or f"verifier exited {completed.returncode}")
            output = parse_json_strict(output_path.read_text(encoding="utf-8"))
            if not isinstance(output, dict):
                raise ValueError("verifier output must be an object")
            return output

    def build_request(self, provider: Mapping[str, Any]) -> tuple[bytes, Mapping[str, Any]]:
        output = self._run("build-request", {
            "schema_version": "1.0", "action": "build-request",
            "provider_id": provider["provider_id"], "nonce_hex": provider["nonce_hex"],
        })
        try:
            request = base64.b64decode(output["request_base64"], validate=True)
        except Exception as exc:
            raise ValueError("verifier build output contains invalid request_base64") from exc
        expected = {
            "schema_version": "1.0", "action": "build-request", "provider_id": provider["provider_id"],
            "wire_version": provider["wire_version_hex"], "wire_profile": provider["wire_profile"],
            "require_type": provider["require_type"], "require_srv": provider["require_srv"],
            "packet_profile": PACKET_PROFILE, "packet_size": 1036, "nonce_hex": provider["nonce_hex"],
            "request_base64": base64.b64encode(request).decode("ascii"), "request_sha256": _sha256_hex(request),
        }
        if output != expected or len(request) != 1036:
            raise ValueError("verifier build output does not exactly match the frozen plan")
        return request, output

    def verify_response(
        self, provider: Mapping[str, Any], request_bytes: bytes, response_bytes: bytes
    ) -> VerifyResult:
        payload = {
            "schema_version": "1.0", "action": "verify-response",
            "provider_id": provider["provider_id"], "nonce_hex": provider["nonce_hex"],
            "request_base64": base64.b64encode(request_bytes).decode("ascii"),
            "response_base64": base64.b64encode(response_bytes).decode("ascii"),
        }
        try:
            output = self._run("verify-response", payload)
        except ValueError as exc:
            detail = str(exc)
            lowered = detail.lower()
            if "authenticated radius must be positive" in lowered:
                return VerifyResult(True, "RADIUS_INVALID", detail,
                                    {"verified": True, "failure_code": "RADIUS_INVALID", "detail": detail})
            mapping = (
                ("midpoint outside delegation", "MIDPOINT_OUTSIDE_DELEGATION"),
                ("merkle", "MERKLE_PROOF_INVALID"), ("type", "TYPE_MISMATCH"),
                ("srv", "ROOT_KEY_MISMATCH"), ("root key", "ROOT_KEY_MISMATCH"),
                ("delegation", "DELEGATION_INVALID"), ("signature", "SIGNATURE_INVALID"),
                ("nonce", "NONCE_MISMATCH"), ("version", "WIRE_VERSION_MISMATCH"),
                ("shorter", "MALFORMED_RESPONSE"), ("framing", "MALFORMED_RESPONSE"),
                ("decode response", "MALFORMED_RESPONSE"), ("decode reply", "MALFORMED_RESPONSE"),
                ("malformed", "MALFORMED_RESPONSE"),
            )
            code = next((code for marker, code in mapping if marker in lowered), "VERIFIER_ERROR")
            return VerifyResult(False, code, detail, {"verified": False, "failure_code": code, "detail": detail})
        expected = {
            "schema_version": "1.0", "action": "verify-response", "provider_id": provider["provider_id"],
            "verified": True, "wire_version": provider["wire_version_hex"], "wire_profile": provider["wire_profile"],
            "require_type": provider["require_type"], "require_srv": provider["require_srv"],
            "nonce_hex": provider["nonce_hex"], "request_sha256": _sha256_hex(request_bytes),
            "response_sha256": _sha256_hex(response_bytes),
        }
        expected_keys = frozenset(expected) | {"midpoint_utc", "radius_nanoseconds"}
        if frozenset(output) != expected_keys:
            return VerifyResult(False, "VERIFIER_ERROR", "verifier output keys mismatch", output)
        if any(type(output[key]) is not type(value) or output[key] != value for key, value in expected.items()):
            return VerifyResult(False, "VERIFIER_ERROR", "verifier output binding mismatch", output)
        midpoint = output.get("midpoint_utc")
        radius_ns = output.get("radius_nanoseconds")
        if not isinstance(midpoint, str) or type(radius_ns) is not int:
            return VerifyResult(False, "VERIFIER_ERROR", "verifier time output malformed", output)
        return VerifyResult(True, None, "", output, midpoint, radius_ns)


def _attempt_record(number: int, request: bytes, outcome: str, *, response: bytes | None = None,
                    failure_code: str | None = None, detail: str = "") -> dict[str, Any]:
    item: dict[str, Any] = {
        "attempt_number": number,
        "request_sha256": _sha256_hex(request),
        "request_base64": base64.b64encode(request).decode("ascii"),
        "outcome": outcome,
    }
    if response:
        item["response_sha256"] = _sha256_hex(response)
        item["response_base64"] = base64.b64encode(response).decode("ascii")
    if failure_code is not None:
        item["failure_code"] = failure_code
    if detail:
        item["detail"] = detail
    return item


def _receipt(plan: Mapping[str, Any], authorization: Mapping[str, Any], profile: Mapping[str, Any],
             provider: Mapping[str, Any], request: bytes, response: bytes, verified: VerifyResult) -> dict[str, Any]:
    assert verified.midpoint_utc is not None and verified.radius_nanoseconds is not None
    radius_ns = verified.radius_nanoseconds
    midpoint_ns_text = verified.midpoint_utc
    from ._roughtime_support import _parse_precise_utc_ns
    upper = _format_precise_utc_ns(_parse_precise_utc_ns(midpoint_ns_text, "midpoint_utc") + radius_ns)
    deadline_ns = _parse_precise_utc_ns(plan["frozen_deadline_utc"], "frozen_deadline_utc")
    qualifies = 1 <= radius_ns <= (2**53 - 1) and _parse_precise_utc_ns(upper, "upper") <= deadline_ns
    if not qualifies:
        raise ValueError("nonqualifying verification cannot produce a receipt")
    payload = {
        "schema_version": "1.2", "classification": "NON_FORECAST_REHEARSAL", "prospective_eligible": False,
        "rehearsal_plan_sha256": plan["plan_sha256"],
        "authorization_record_sha256": authorization["authorization_sha256"],
        **_provider_public_fields(next(item for item in PROVIDERS if item.provider_id == provider["provider_id"])),
        "packet_profile": provider["packet_profile"], "transport_profile": provider["transport_profile"],
        "subject_sha256": plan["subject_sha256"], "client_random_hex": provider["client_random_hex"],
        "nonce_profile": provider["nonce_profile"], "nonce_hex": provider["nonce_hex"],
        "request_sha256": _sha256_hex(request), "request_base64": base64.b64encode(request).decode("ascii"),
        "response_sha256": _sha256_hex(response), "response_base64": base64.b64encode(response).decode("ascii"),
        "verifier_repository": VERIFIER_REPOSITORY, "verifier_tag": VERIFIER_TAG, "verifier_commit": VERIFIER_COMMIT,
        "verifier_source_sha256": profile["verifier_source_bundle_sha256"],
        "verifier_binary_sha256": profile["binary_sha256"],
        "verifier_build_profile_sha256": profile["profile_sha256"],
        "verification_transcript_sha256": _sha256_hex(canonical_json(dict(verified.transcript))),
        "midpoint_utc": midpoint_ns_text, "radius_seconds": (radius_ns + 999_999_999) // 1_000_000_000,
        "radius_nanoseconds": radius_ns, "verified_receipt_upper_bound_utc": upper,
        "frozen_deadline_utc": plan["frozen_deadline_utc"],
        "root_key_match": True, "wire_profile_match": True, "delegation_verified": True,
        "signature_verified": True, "nonce_verified": True, "merkle_proof_verified": True,
        "midpoint_inside_delegation": True, "upper_bound_at_or_before_deadline": True, "qualifies": True,
    }
    receipt = seal_object(payload, object_type="RoughtimeReceipt",
                          stable_context=f"{authorization['authorization_sha256'][:12]}:{provider['provider_id']}")
    validate_receipt(receipt, plan=plan, authorization=authorization)
    return receipt


def execute_rehearsal(
    *, plan: Mapping[str, Any], authorization: Mapping[str, Any], build_profile: Mapping[str, Any],
    retry_state_before: Mapping[str, Any], evidence_root: Path, verifier: VerifierBackend,
    transport: UDPTransport, now: Callable[[], datetime] = _utc_now,
    sleeper: Callable[[float], None] = time.sleep,
    fault_hook: Callable[[str], None] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], Path]:
    """Execute one exact authorized rehearsal. The caller must provide the explicit network transport."""
    validate_plan(plan)
    validate_authorization_record(authorization, plan)
    validate_authorization_control_binding(authorization, plan, build_profile, retry_state_before)
    validate_retry_state(retry_state_before)
    if verifier.binary_sha256 != build_profile["binary_sha256"]:
        raise ValueError("verifier binary does not match the qualified build profile")
    if now() >= _parse_utc(plan["frozen_deadline_utc"], "frozen_deadline_utc"):
        raise ValueError("frozen deadline has expired")

    _assert_safe_new_root(evidence_root)
    auth_sha = authorization["authorization_sha256"]
    event = evidence_root / "events" / auth_sha
    event.mkdir(exist_ok=False)
    _write_json_exclusive(event / "plan.json", plan)
    _write_json_exclusive(event / "authorization.json", authorization)
    _write_json_exclusive(event / "verifier-build-profile.json", build_profile)
    _write_json_exclusive(event / "retry-state-before.json", retry_state_before)
    _write_json_exclusive(evidence_root / "consumed" / f"{auth_sha}.json", {
        "authorization_sha256": auth_sha, "event_relative_path": f"events/{auth_sha}",
        "classification": "NON_FORECAST_REHEARSAL", "prospective_eligible": False,
    })
    if fault_hook:
        fault_hook("authorization_consumed")

    state = dict(retry_state_before)
    provider_results: list[dict[str, Any]] = []
    transcript_results: list[dict[str, Any]] = []
    for provider_contract, provider in zip(PROVIDERS, plan["providers"]):
        provider_dir = event / "providers" / provider["provider_id"]
        root_hash = _root_hash(provider)
        root_state = next(item for item in state["root_states"] if item["root_public_key_sha256"] == root_hash)
        current_ms = _unix_ms(now())
        if current_ms < root_state["next_eligible_unix_ms"]:
            provider_results.append({"provider_id": provider["provider_id"], "attempts": [], "qualifies": False,
                                     "final_failure_code": "BACKOFF_ACTIVE"})
            transcript_results.append({"provider_id": provider["provider_id"], "attempts": [],
                                       "decision": "BACKOFF_ACTIVE"})
            continue
        request, build_transcript = verifier.build_request(provider)
        if len(request) != 1036:
            raise ValueError("request builder did not return a STANDARD_1024_BODY packet")
        request_hash = _sha256_hex(request)
        attempts: list[dict[str, Any]] = []
        transcript_attempts: list[dict[str, Any]] = []
        terminal = False
        qualifies = False
        receipt: dict[str, Any] | None = None
        final_failure = "VERIFIER_ERROR"
        destination: PreparedDestination | None = None
        for attempt_number in range(1, provider["maximum_attempts"] + 1):
            if attempt_number > 1:
                root_state = next(item for item in state["root_states"] if item["root_public_key_sha256"] == root_hash)
                wait_ms = max(0, root_state["next_eligible_unix_ms"] - _unix_ms(now()))
                if wait_ms:
                    sleeper(wait_ms / 1000)
            if now() >= _parse_utc(plan["frozen_deadline_utc"], "frozen_deadline_utc"):
                raise ValueError("frozen deadline expired before send reservation")
            attempt_dir = provider_dir / f"attempt-{attempt_number}"
            attempt_dir.mkdir(parents=True, exist_ok=False)
            _write_bytes_exclusive(attempt_dir / "request.bin", request)
            _write_bytes_exclusive(attempt_dir / "request.sha256", (request_hash + "\n").encode("ascii"))
            _write_json_exclusive(attempt_dir / "request-builder.json", build_transcript)
            if fault_hook:
                fault_hook("request_persisted")
            try:
                if destination is None:
                    destination = transport.prepare_destination(provider["host"], provider["port"])
                if destination.port != provider["port"]:
                    raise OSError("transport destination changed frozen port")
            except OSError as exc:
                final_failure = "DNS_FAILURE"
                detail = f"{type(exc).__name__}: {exc}"
                attempts.append(_attempt_record(attempt_number, request, "FAILED", failure_code=final_failure, detail=detail))
                transcript_attempts.append({"attempt_number": attempt_number, "request_sha256": request_hash,
                                            "sent": False, "failure_code": final_failure, "detail": detail})
                state = record_failure(state, root_hash, _unix_ms(now()))
                _write_json_exclusive(attempt_dir / "retry-state-reserved.json", state)
                if attempt_number == provider["maximum_attempts"]:
                    break
                continue
            reservation_time = now()
            state = record_failure(state, root_hash, _unix_ms(reservation_time))
            _write_json_exclusive(attempt_dir / "send-reservation.json", {
                "state": "SEND_RESERVED", "request_sha256": request_hash,
                "expected_host": provider["host"], "expected_port": provider["port"],
                "resolved_destination": asdict(destination), "reserved_utc": _utc_text(reservation_time),
                "warning": "packet may or may not have left after this durable reservation",
            })
            _write_json_exclusive(attempt_dir / "retry-state-reserved.json", state)
            if fault_hook:
                fault_hook("send_reserved")
            if now() >= _parse_utc(plan["frozen_deadline_utc"], "frozen_deadline_utc"):
                _write_json_exclusive(attempt_dir / "deadline-abort.json", {
                    "state": "SEND_ABORTED_DEADLINE_EXPIRED", "request_sha256": request_hash,
                    "checked_utc": _utc_text(now()), "sent": False,
                })
                raise ValueError("frozen deadline expired immediately before send")
            outcome = transport.send_and_receive(destination, request, provider["timeout_per_attempt_seconds"])
            if fault_hook:
                fault_hook("send_returned")
            if outcome.destination != destination:
                raise ValueError("transport outcome destination binding mismatch")
            if outcome.status not in {"RESPONSE", "TIMEOUT", "ERROR", "SOURCE_MISMATCH"}:
                raise ValueError("transport returned an unknown status")
            if outcome.status != "ERROR" and outcome.sent is not True:
                raise ValueError("transport reported a result without sending the reserved datagram")
            metadata = {
                "attempt_number": attempt_number, "expected_host": provider["host"], "expected_port": provider["port"],
                "resolved_destination": asdict(outcome.destination),
                "actual_source_address": outcome.source_address or "NOT_OBSERVED",
                "actual_source_port": outcome.source_port or 0, "sent": outcome.sent, "send_utc": outcome.send_utc,
                "receive_utc": outcome.receive_utc or "NOT_OBSERVED", "transport_status": outcome.status,
                "detail": outcome.detail,
            }
            _write_json_exclusive(attempt_dir / "transport.json", metadata)
            response = outcome.response_bytes
            if response is not None:
                _write_bytes_exclusive(attempt_dir / "response.bin", response)
                _write_bytes_exclusive(attempt_dir / "response.sha256", (_sha256_hex(response) + "\n").encode("ascii"))
            if fault_hook:
                fault_hook("response_persisted")
            if outcome.status == "TIMEOUT":
                final_failure = "TRANSPORT_TIMEOUT"
                attempts.append(_attempt_record(attempt_number, request, "FAILED", failure_code=final_failure, detail=outcome.detail))
            elif outcome.status == "ERROR":
                final_failure = "TRANSPORT_ERROR"
                attempts.append(_attempt_record(attempt_number, request, "FAILED", failure_code=final_failure, detail=outcome.detail))
            elif outcome.status == "SOURCE_MISMATCH":
                final_failure = "RESPONSE_SOURCE_MISMATCH"
                attempts.append(_attempt_record(attempt_number, request, "FAILED", response=response,
                                                failure_code=final_failure, detail=outcome.detail))
            elif response is None or len(response) == 0:
                final_failure = "MALFORMED_RESPONSE"
                attempts.append(_attempt_record(attempt_number, request, "FAILED", failure_code=final_failure,
                                                detail="empty UDP datagram"))
            else:
                verified = verifier.verify_response(provider, request, response)
                _write_json_exclusive(attempt_dir / "verification.json", dict(verified.transcript))
                if fault_hook:
                    fault_hook("verification_persisted")
                if verified.verified:
                    if verified.failure_code in VERIFIED_NONQUALIFYING_CODES:
                        final_failure = verified.failure_code
                    else:
                        if verified.radius_nanoseconds is None or verified.midpoint_utc is None:
                            raise ValueError("verified response omitted authenticated time fields")
                        radius_valid = 1 <= verified.radius_nanoseconds <= 2**53 - 1
                        if not radius_valid:
                            final_failure = "RADIUS_INVALID"
                        else:
                            from ._roughtime_support import _parse_precise_utc_ns
                            upper_ns = _parse_precise_utc_ns(verified.midpoint_utc, "midpoint_utc") + verified.radius_nanoseconds
                            deadline_ns = _parse_precise_utc_ns(plan["frozen_deadline_utc"], "deadline")
                            final_failure = "UPPER_BOUND_AFTER_DEADLINE" if upper_ns > deadline_ns else ""
                    state = reset_root_state(state, root_hash)
                    if final_failure:
                        attempts.append(_attempt_record(attempt_number, request, "VERIFIED_NONQUALIFYING_RESPONSE",
                                                        response=response, failure_code=final_failure, detail=verified.detail))
                    else:
                        receipt = _receipt(plan, authorization, build_profile, provider, request, response, verified)
                        attempts.append(_attempt_record(attempt_number, request, "QUALIFYING_VERIFIED_RESPONSE", response=response))
                        qualifies = True
                    terminal = True
                else:
                    final_failure = verified.failure_code or "VERIFIER_ERROR"
                    if final_failure not in FAILURE_CODES or final_failure in VERIFIED_NONQUALIFYING_CODES:
                        final_failure = "VERIFIER_ERROR"
                    attempts.append(_attempt_record(attempt_number, request, "FAILED", response=response,
                                                    failure_code=final_failure, detail=verified.detail))
            transcript_attempts.append({**metadata, "request_sha256": request_hash,
                                        "response_sha256": _sha256_hex(response) if response is not None else "NOT_OBSERVED",
                                        "outcome": attempts[-1]["outcome"],
                                        "failure_code": attempts[-1].get("failure_code", "NONE")})
            if terminal or attempt_number == provider["maximum_attempts"]:
                break
        result: dict[str, Any] = {"provider_id": provider["provider_id"], "attempts": attempts, "qualifies": qualifies}
        if qualifies:
            result["receipt"] = receipt
        else:
            result["final_failure_code"] = final_failure
        provider_results.append(result)
        transcript_results.append({"provider_id": provider_contract.provider_id, "attempts": transcript_attempts,
                                   "qualifies": qualifies, "final_failure_code": "NONE" if qualifies else final_failure})

    if fault_hook:
        fault_hook("before_retry_state_after")
    _write_json_exclusive(event / "retry-state-after.json", state)
    transcript_core = {
        "schema_version": "1.0", "classification": "NON_FORECAST_REHEARSAL", "prospective_eligible": False,
        "plan_sha256": plan["plan_sha256"], "authorization_sha256": auth_sha,
        "subject_sha256": plan["subject_sha256"], "verifier_build_profile_sha256": build_profile["profile_sha256"],
        "retry_state_before_sha256": retry_state_before["state_sha256"],
        "retry_state_after_sha256": state["state_sha256"], "provider_order": list(PROVIDER_ORDER),
        "provider_results": transcript_results,
    }
    transcript = dict(transcript_core)
    transcript["execution_transcript_sha256"] = _sha256_hex(canonical_json(transcript_core))
    _write_json_exclusive(event / "execution-transcript.json", transcript)
    qualifying_count = sum(bool(item["qualifies"]) for item in provider_results)
    report_payload = {
        "schema_version": "1.2", "classification": "NON_FORECAST_REHEARSAL", "prospective_eligible": False,
        "network_authorized_by_report": False, "rehearsal_plan_sha256": plan["plan_sha256"],
        "authorization_record_sha256": auth_sha, "subject_sha256": plan["subject_sha256"],
        "provider_attempt_order": list(PROVIDER_ORDER), "quorum_threshold": 2,
        "verifier_repository": VERIFIER_REPOSITORY, "verifier_tag": VERIFIER_TAG, "verifier_commit": VERIFIER_COMMIT,
        "verifier_build_profile_sha256": build_profile["profile_sha256"],
        "retry_state_before_sha256": retry_state_before["state_sha256"],
        "retry_state_after_sha256": state["state_sha256"],
        "execution_transcript_sha256": transcript["execution_transcript_sha256"],
        "provider_results": provider_results, "qualifying_provider_count": qualifying_count,
        "final_rehearsal_status": "REHEARSAL_VERIFIED" if qualifying_count >= 2 else "REHEARSAL_FAILED",
    }
    report = seal_object(report_payload, object_type="RoughtimeRehearsalReport", stable_context=auth_sha[:12])
    validate_rehearsal_report(report, plan=plan, authorization=authorization)
    validate_report_control_binding(report, plan, authorization, build_profile, retry_state_before, state)
    _write_json_exclusive(event / "report.json", report)
    if fault_hook:
        fault_hook("completed")
    return report, state, event
