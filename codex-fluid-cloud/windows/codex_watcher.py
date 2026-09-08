#!/usr/bin/env python3
"""Watch Codex Desktop session JSONL files and send progress to a phone.

Only Python's standard library is used. The watcher deliberately forwards a
small allow-list of status fields and never sends conversation text, tool
outputs, or complete tool arguments.
"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import hashlib
import json
import logging
import os
import re
import shlex
import socket
import sys
import time
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Iterable, Mapping, Optional


LOGGER = logging.getLogger("codex-fluid-cloud")
PROTOCOL_VERSION = 1
MAX_SEEN_EVENT_IDS = 20_000
DEFAULT_SPOOL_PATH = "%LOCALAPPDATA%\\CodexFluidCloud\\pending-events.json"


def expand_environment(value: str) -> str:
    """Expand both Windows %NAME% and conventional $NAME variables."""

    def replace(match: re.Match[str]) -> str:
        return os.environ.get(match.group(1), match.group(0))

    return os.path.expandvars(re.sub(r"%([^%]+)%", replace, value))


def clipped(value: Any, limit: int = 240) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def command_name(command: Any) -> str:
    """Return only the executable basename, never command arguments."""

    if isinstance(command, list):
        parts = [str(part) for part in command if str(part).strip()]
    elif isinstance(command, str):
        try:
            parts = shlex.split(command, posix=False)
        except ValueError:
            parts = []
    else:
        parts = []
    if not parts:
        return "command"
    index = 1 if parts[0] in {"&", "."} and len(parts) > 1 else 0
    candidate = parts[index].strip().strip("\"'")
    if not candidate or "=" in candidate or candidate[0] in "$({[":
        return "shell command"
    return clipped(basename(candidate), 80) or "command"


def basename(value: Any) -> str:
    text = str(value or "")
    if not text:
        return "file"
    if "\\" in text:
        return PureWindowsPath(text).name or "file"
    return PurePosixPath(text).name or "file"


@dataclasses.dataclass(frozen=True)
class Config:
    sessions_dir: Path
    phone_host: str
    phone_port: int = 24680
    token: str = ""
    title: str = "Codex"
    poll_interval_seconds: float = 0.5
    connect_timeout_seconds: float = 3.0
    retries: int = 2
    retry_delay_seconds: float = 0.5
    start_at_end: bool = True
    include_subagent_sessions: bool = False
    spool_path: Optional[Path] = None
    max_pending_events: int = 1000
    log_level: str = "INFO"

    @classmethod
    def load(cls, path: Path) -> "Config":
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        if not isinstance(raw, dict):
            raise ValueError("configuration root must be a JSON object")
        sessions = Path(expand_environment(str(raw.get("sessions_dir", "%USERPROFILE%\\.codex\\sessions"))))
        phone_host = str(raw.get("phone_host", "")).strip()
        if not phone_host:
            raise ValueError("phone_host is required in config.json")
        token = str(raw.get("token", "")).strip()
        if len(token) < 32 or token == "codex-fluid-change-me":
            raise ValueError("token must contain at least 32 characters and must not use the example value")
        phone_port = int(raw.get("phone_port", 24680))
        if not 1 <= phone_port <= 65535:
            raise ValueError("phone_port must be between 1 and 65535")
        poll_interval = float(raw.get("poll_interval_seconds", 0.5))
        if poll_interval <= 0:
            raise ValueError("poll_interval_seconds must be positive")
        return cls(
            sessions_dir=sessions,
            phone_host=phone_host,
            phone_port=phone_port,
            token=token,
            title=clipped(raw.get("title", "Codex"), 80) or "Codex",
            poll_interval_seconds=poll_interval,
            connect_timeout_seconds=max(0.1, float(raw.get("connect_timeout_seconds", 3.0))),
            retries=max(0, int(raw.get("retries", 2))),
            retry_delay_seconds=max(0.0, float(raw.get("retry_delay_seconds", 0.5))),
            start_at_end=bool(raw.get("start_at_end", True)),
            include_subagent_sessions=bool(raw.get("include_subagent_sessions", False)),
            spool_path=Path(expand_environment(str(raw.get("spool_path", DEFAULT_SPOOL_PATH)))),
            max_pending_events=max(1, int(raw.get("max_pending_events", 1000))),
            log_level=str(raw.get("log_level", "INFO")).upper(),
        )


class CodexEventParser:
    """Convert the documented Codex session records into safe phone events."""

    def __init__(self, title: str = "Codex", include_subagent_sessions: bool = False) -> None:
        self.title = title
        self.include_subagent_sessions = include_subagent_sessions
        self.active_turns: dict[str, str] = {}
        self.session_allowed: dict[Path, bool] = {}

    def parse(self, record: Mapping[str, Any], session_file: Path) -> list[dict[str, Any]]:
        if not self._session_is_allowed(session_file):
            return []
        outer_type = record.get("type")
        payload = record.get("payload")
        if not isinstance(payload, Mapping):
            return []
        if outer_type == "event_msg":
            return self._event_message(record, payload, session_file)
        if outer_type == "response_item":
            event = self._tool_call(record, payload, session_file)
            return [event] if event else []
        return []

    def _session_is_allowed(self, session_file: Path) -> bool:
        if self.include_subagent_sessions:
            return True
        if session_file in self.session_allowed:
            return self.session_allowed[session_file]
        allowed = True
        try:
            with session_file.open("r", encoding="utf-8", errors="replace") as handle:
                first = json.loads(handle.readline())
            payload = first.get("payload") if isinstance(first, Mapping) else None
            if isinstance(payload, Mapping) and first.get("type") == "session_meta":
                agent_path = str(payload.get("agent_path", "")).strip()
                allowed = agent_path in {"", "/root"}
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            # Synthetic tests and future session formats remain visible rather
            # than being silently discarded.
            allowed = True
        self.session_allowed[session_file] = allowed
        return allowed

    def _base(
        self,
        record: Mapping[str, Any],
        payload: Mapping[str, Any],
        session_file: Path,
        event_type: str,
        phase: str,
        message: str,
        *,
        terminal: bool = False,
        percent: int = -1,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> dict[str, Any]:
        turn_id = clipped(payload.get("turn_id"), 100)
        session_id = self._session_id(session_file)
        ordinal = record.get("ordinal")
        identity = f"{session_file}|{ordinal}|{record.get('timestamp')}|{phase}|{payload.get('id', '')}"
        event_id = hashlib.sha256(identity.encode("utf-8", "replace")).hexdigest()[:32]
        event: dict[str, Any] = {
            "version": PROTOCOL_VERSION,
            "event_id": event_id,
            "source": "codex-desktop",
            "session_id": session_id,
            "task_id": turn_id or session_id,
            "sequence": ordinal if isinstance(ordinal, int) else 0,
            "type": event_type,
            "phase": phase,
            "title": self.title,
            "message": clipped(message),
            "timestamp": clipped(record.get("timestamp"), 64),
            "terminal": terminal,
            "percent": percent,
        }
        if metadata:
            event["metadata"] = dict(metadata)
        return event

    def _event_message(
        self, record: Mapping[str, Any], payload: Mapping[str, Any], session_file: Path
    ) -> list[dict[str, Any]]:
        kind = payload.get("type")
        if kind == "task_started":
            turn_id = clipped(payload.get("turn_id"), 100)
            if turn_id:
                self.active_turns[self._session_id(session_file)] = turn_id
            return [self._base(record, payload, session_file, "started", "task_started", "Codex task started")]
        if kind == "task_complete":
            events = [
                self._base(
                    record,
                    payload,
                    session_file,
                    "completed",
                    "task_complete",
                    "Codex task completed",
                    terminal=True,
                    percent=100,
                )
            ]
            self.active_turns.pop(self._session_id(session_file), None)
            return events
        if kind == "turn_aborted":
            reason = clipped(payload.get("reason"), 80)
            message = "Codex task aborted" + (f": {reason}" if reason else "")
            event = self._base(record, payload, session_file, "cancelled", "turn_aborted", message, terminal=True)
            self.active_turns.pop(self._session_id(session_file), None)
            return [event]
        if kind != "item_completed":
            return []
        item = payload.get("item")
        if not isinstance(item, Mapping):
            return []
        item_type = item.get("type")
        if item_type == "CommandExecution":
            return [self._command_completed(record, payload, item, session_file)]
        if item_type == "FileChange":
            return [self._file_change(record, payload, item, session_file)]
        if item_type == "SubAgentActivity":
            return [self._subagent(record, payload, item, session_file)]
        return []

    def _command_completed(
        self,
        record: Mapping[str, Any],
        payload: Mapping[str, Any],
        item: Mapping[str, Any],
        session_file: Path,
    ) -> dict[str, Any]:
        status = clipped(item.get("status"), 32).lower() or "completed"
        exit_code = item.get("exit_code")
        executable = command_name(item.get("command"))
        failed = status == "failed" or (isinstance(exit_code, int) and exit_code != 0)
        prefix = "Command failed" if failed else "Command completed"
        if isinstance(exit_code, int):
            prefix += f" ({exit_code})"
        return self._base(
            record,
            payload,
            session_file,
            "progress",
            "command_completed",
            f"{prefix}: {executable}",
            metadata={"item_id": clipped(item.get("id"), 100), "status": status},
        )

    def _file_change(
        self,
        record: Mapping[str, Any],
        payload: Mapping[str, Any],
        item: Mapping[str, Any],
        session_file: Path,
    ) -> dict[str, Any]:
        changes = item.get("changes")
        file_count = len(changes) if isinstance(changes, Mapping) else 1
        return self._base(
            record,
            payload,
            session_file,
            "progress",
            "file_change",
            f"Changed {file_count} file(s)",
            metadata={"item_id": clipped(item.get("id"), 100), "file_count": file_count},
        )

    def _subagent(
        self,
        record: Mapping[str, Any],
        payload: Mapping[str, Any],
        item: Mapping[str, Any],
        session_file: Path,
    ) -> dict[str, Any]:
        kind = clipped(item.get("kind"), 50) or "updated"
        path = clipped(item.get("agent_path"), 100)
        message = f"Sub-agent {kind}" + (f": {path}" if path else "")
        return self._base(
            record,
            payload,
            session_file,
            "progress",
            "subagent_activity",
            message,
            metadata={"item_id": clipped(item.get("id"), 100), "activity": kind},
        )

    def _tool_call(
        self, record: Mapping[str, Any], payload: Mapping[str, Any], session_file: Path
    ) -> Optional[dict[str, Any]]:
        call_type = payload.get("type")
        if call_type not in {"function_call", "custom_tool_call"}:
            return None
        name = clipped(payload.get("name"), 100) or "tool"
        namespace = clipped(payload.get("namespace"), 100)
        display_name = f"{namespace}.{name}" if namespace else name
        message = f"Tool started: {display_name}"
        # Function-call arguments are parsed only to identify the executable.
        # Arguments and input content are intentionally never forwarded.
        if call_type == "function_call" and name == "exec_command":
            arguments = payload.get("arguments")
            try:
                decoded = json.loads(arguments) if isinstance(arguments, str) else arguments
            except (TypeError, ValueError, json.JSONDecodeError):
                decoded = None
            if isinstance(decoded, Mapping) and "cmd" in decoded:
                message = f"Command started: {command_name(decoded.get('cmd'))}"
        synthetic_payload = dict(payload)
        synthetic_payload.setdefault(
            "turn_id", record.get("turn_id") or self.active_turns.get(self._session_id(session_file), "")
        )
        return self._base(
            record,
            synthetic_payload,
            session_file,
            "command_started",
            "tool_started",
            message,
            metadata={"call_id": clipped(payload.get("call_id"), 100), "tool": display_name},
        )

    @staticmethod
    def _session_id(session_file: Path) -> str:
        match = re.search(r"([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})", session_file.stem, re.I)
        return match.group(1) if match else session_file.stem


@dataclasses.dataclass
class TailState:
    offset: int = 0
    pending: bytes = b""


class SessionPoller:
    """Poll append-only session files without holding handles between scans."""

    def __init__(self, sessions_dir: Path, start_at_end: bool = True) -> None:
        self.sessions_dir = sessions_dir
        self.start_at_end = start_at_end
        self.states: dict[Path, TailState] = {}
        self.initialized = False

    def poll(self) -> list[tuple[Path, str]]:
        if not self.sessions_dir.is_dir():
            raise FileNotFoundError(f"Codex sessions directory not found: {self.sessions_dir}")
        files = sorted(self.sessions_dir.rglob("*.jsonl"))
        records: list[tuple[Path, str]] = []
        known_before = set(self.states)
        for path in files:
            if path not in self.states:
                offset = path.stat().st_size if self.start_at_end and not self.initialized else 0
                self.states[path] = TailState(offset=offset)
            state = self.states[path]
            size = path.stat().st_size
            if size < state.offset:
                state.offset = 0
                state.pending = b""
            if size == state.offset:
                continue
            with path.open("rb") as handle:
                handle.seek(state.offset)
                chunk = handle.read()
            state.offset += len(chunk)
            data = state.pending + chunk
            parts = data.split(b"\n")
            state.pending = parts.pop()
            for raw in parts:
                if raw.strip():
                    records.append((path, raw.decode("utf-8", "replace")))
        # Forget removed files so a later file at the same path is treated new.
        for stale in known_before.difference(files):
            self.states.pop(stale, None)
        self.initialized = True
        return records


class TcpJsonSender:
    def __init__(self, config: Config) -> None:
        self.host = config.phone_host
        self.port = config.phone_port
        self.token = config.token
        self.timeout = config.connect_timeout_seconds
        self.retries = config.retries
        self.retry_delay = config.retry_delay_seconds

    def send(self, event: Mapping[str, Any]) -> None:
        value = dict(event)
        if self.token:
            value["token"] = self.token
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"
        last_error: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                with socket.create_connection((self.host, self.port), self.timeout) as client:
                    client.settimeout(self.timeout)
                    client.sendall(payload)
                    reply = self._read_line(client, 4096)
                    if not reply:
                        raise RuntimeError("phone closed the connection without an acknowledgement")
                    acknowledgement = json.loads(reply.decode("utf-8", "replace"))
                    if not isinstance(acknowledgement, Mapping) or acknowledgement.get("ok") is not True:
                        error = acknowledgement.get("error", "unknown") if isinstance(acknowledgement, Mapping) else "invalid_ack"
                        raise RuntimeError(f"phone rejected event: {error}")
                    return
            except (OSError, TimeoutError, ValueError, json.JSONDecodeError, RuntimeError) as error:
                last_error = error
                if attempt < self.retries:
                    time.sleep(self.retry_delay * (2**attempt))
        raise ConnectionError(f"could not send to {self.host}:{self.port}: {last_error}")

    @staticmethod
    def _read_line(client: socket.socket, limit: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < limit:
            piece = client.recv(min(1024, limit - len(chunks)))
            if not piece:
                break
            chunks.extend(piece)
            newline = chunks.find(b"\n")
            if newline >= 0:
                return bytes(chunks[:newline])
        return bytes(chunks)


class DryRunSender:
    def send(self, event: Mapping[str, Any]) -> None:
        print(json.dumps(dict(event), ensure_ascii=False, separators=(",", ":")), flush=True)


class PendingEventSpool:
    """Atomically persist events that have not received a phone acknowledgement."""

    def __init__(self, path: Optional[Path]) -> None:
        self.path = path

    def load(self) -> list[dict[str, Any]]:
        if self.path is None or not self.path.is_file():
            return []
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                value = json.load(handle)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
            raise ValueError(f"could not load pending-event spool {self.path}: {error}") from error
        if not isinstance(value, Mapping) or value.get("version") != 1:
            raise ValueError(f"pending-event spool has an unsupported format: {self.path}")
        events = value.get("events")
        if not isinstance(events, list) or not all(isinstance(event, Mapping) for event in events):
            raise ValueError(f"pending-event spool contains invalid events: {self.path}")
        return [dict(event) for event in events]

    def save(self, events: Iterable[Mapping[str, Any]]) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f"{self.path.name}.{os.getpid()}.tmp")
        value = {"version": 1, "events": [dict(event) for event in events]}
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(value, handle, ensure_ascii=False, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


class Watcher:
    def __init__(
        self,
        config: Config,
        sender: Any,
        *,
        start_at_end: Optional[bool] = None,
    ) -> None:
        self.config = config
        self.sender = sender
        self.parser = CodexEventParser(config.title, config.include_subagent_sessions)
        self.poller = SessionPoller(config.sessions_dir, config.start_at_end if start_at_end is None else start_at_end)
        self.spool = PendingEventSpool(config.spool_path)
        self.pending: collections.deque[dict[str, Any]] = collections.deque()
        self.seen_event_ids: set[str] = set()
        self.seen_event_order: collections.deque[str] = collections.deque()
        self.spool_dirty = False
        restored = self.spool.load()
        for event in restored:
            self._enqueue_event(event)
            event_id = str(event.get("event_id", ""))
            if event_id:
                self._remember_event_id(event_id)
        self.spool_dirty = list(self.pending) != restored

    def tick(self) -> tuple[int, int]:
        if not self._persist_pending():
            return 0, 0
        parsed_count = 0
        for path, line in self.poller.poll():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                LOGGER.warning("ignored malformed JSONL record in %s", path.name)
                continue
            if not isinstance(record, Mapping):
                continue
            for event in self.parser.parse(record, path):
                event_id = str(event.get("event_id", ""))
                if event_id and event_id in self.seen_event_ids:
                    continue
                if event_id:
                    self._remember_event_id(event_id)
                if self._enqueue_event(event):
                    parsed_count += 1
        if not self._persist_pending():
            return parsed_count, 0
        sent_count = self.flush()
        return parsed_count, sent_count

    def flush(self) -> int:
        sent = 0
        while self.pending:
            try:
                self.sender.send(self.pending[0])
            except ConnectionError as error:
                LOGGER.warning("phone unavailable; %d event(s) pending: %s", len(self.pending), error)
                break
            self.pending.popleft()
            self.spool_dirty = True
            sent += 1
        self._persist_pending()
        return sent

    def _enqueue_event(self, event: Mapping[str, Any]) -> bool:
        value = dict(event)
        task_id = str(value.get("task_id", ""))
        terminal = bool(value.get("terminal", False))

        if terminal and task_id:
            kept = collections.deque(
                pending for pending in self.pending if str(pending.get("task_id", "")) != task_id
            )
            if len(kept) != len(self.pending):
                self.pending = kept
                self.spool_dirty = True

        if len(self.pending) >= self.config.max_pending_events:
            replacement = self._replacement_index(task_id, terminal)
            if replacement is None:
                LOGGER.error("pending queue is full; dropping progress event %s", value.get("event_id", "without-id"))
                return False
            evicted = self.pending[replacement]
            del self.pending[replacement]
            LOGGER.warning(
                "pending queue is full; replacing event %s with %s",
                evicted.get("event_id", "without-id"),
                value.get("event_id", "without-id"),
            )

        if terminal:
            insert_at = next(
                (index for index, pending in enumerate(self.pending) if not bool(pending.get("terminal", False))),
                len(self.pending),
            )
            self.pending.insert(insert_at, value)
        else:
            self.pending.append(value)
        self.spool_dirty = True
        return True

    def _replacement_index(self, task_id: str, terminal: bool) -> Optional[int]:
        if not terminal:
            for index, pending in enumerate(self.pending):
                if (
                    task_id
                    and str(pending.get("task_id", "")) == task_id
                    and not bool(pending.get("terminal", False))
                ):
                    return index
            return None
        for index, pending in enumerate(self.pending):
            if not bool(pending.get("terminal", False)):
                return index
        return 0 if self.pending else None

    def _persist_pending(self) -> bool:
        if not self.spool_dirty:
            return True
        try:
            self.spool.save(self.pending)
        except OSError as error:
            LOGGER.error("could not persist %d pending event(s): %s", len(self.pending), error)
            return False
        self.spool_dirty = False
        return True

    def _remember_event_id(self, event_id: str) -> None:
        self.seen_event_ids.add(event_id)
        self.seen_event_order.append(event_id)
        while len(self.seen_event_order) > MAX_SEEN_EVENT_IDS:
            expired = self.seen_event_order.popleft()
            self.seen_event_ids.discard(expired)


def build_argument_parser() -> argparse.ArgumentParser:
    default_config = Path(__file__).with_name("config.local.json")
    if not default_config.is_file():
        default_config = Path(__file__).with_name("config.json")
    parser = argparse.ArgumentParser(description="Forward Codex Desktop task progress to ColorOS")
    parser.add_argument(
        "--config",
        type=Path,
        default=default_config,
        help="path to watcher configuration JSON",
    )
    parser.add_argument("--once", action="store_true", help="perform one poll and exit")
    parser.add_argument("--dry-run", action="store_true", help="print safe events instead of connecting to the phone")
    parser.add_argument("--replay-existing", action="store_true", help="read existing session files from the beginning")
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = build_argument_parser().parse_args(argv)
    try:
        config = Config.load(args.config.resolve())
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 2
    logging.basicConfig(
        level=getattr(logging, config.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    sender = DryRunSender() if args.dry_run else TcpJsonSender(config)
    if args.dry_run:
        config = dataclasses.replace(config, spool_path=None)
    try:
        watcher = Watcher(config, sender, start_at_end=False if args.replay_existing else None)
    except (OSError, ValueError) as error:
        LOGGER.error("could not initialize watcher: %s", error)
        return 2
    LOGGER.info("watching %s", config.sessions_dir)
    try:
        while True:
            watcher.tick()
            if args.once:
                return 0
            time.sleep(config.poll_interval_seconds)
    except KeyboardInterrupt:
        LOGGER.info("stopped")
        return 0
    except FileNotFoundError as error:
        LOGGER.error("%s", error)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
