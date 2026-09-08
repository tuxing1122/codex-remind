import json
import os
import socket
import sys
import tempfile
import threading
import unittest
from pathlib import Path


WINDOWS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WINDOWS_DIR))

from codex_watcher import (  # noqa: E402
    CodexEventParser,
    Config,
    SessionPoller,
    TcpJsonSender,
    Watcher,
    command_name,
)


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.parser = CodexEventParser("Codex Test")
        self.path = Path("rollout-2026-09-08T00-00-00-12345678-1234-1234-1234-123456789abc.jsonl")

    def event(self, payload, ordinal=1):
        return {"timestamp": "2026-09-08T00:00:00Z", "type": "event_msg", "ordinal": ordinal, "payload": payload}

    def test_task_lifecycle(self):
        started = self.parser.parse(self.event({"type": "task_started", "turn_id": "turn-1"}), self.path)[0]
        completed = self.parser.parse(self.event({"type": "task_complete", "turn_id": "turn-1"}, 2), self.path)[0]
        aborted = self.parser.parse(
            self.event({"type": "turn_aborted", "turn_id": "turn-2", "reason": "interrupted"}, 3), self.path
        )[0]
        self.assertEqual((started["type"], started["phase"], started["terminal"]), ("started", "task_started", False))
        self.assertEqual((completed["type"], completed["percent"], completed["terminal"]), ("completed", 100, True))
        self.assertEqual((aborted["type"], aborted["terminal"]), ("cancelled", True))
        self.assertEqual(started["task_id"], "turn-1")

    def test_command_completion_sends_only_executable_name(self):
        record = self.event(
            {
                "type": "item_completed",
                "turn_id": "turn-1",
                "item": {
                    "type": "CommandExecution",
                    "id": "item-1",
                    "status": "completed",
                    "exit_code": 0,
                    "command": '"C:\\private\\tools\\tool.exe" --token very-secret --name demo',
                    "stdout": "must-not-leak",
                },
            }
        )
        event = self.parser.parse(record, self.path)[0]
        encoded = json.dumps(event)
        self.assertIn("tool.exe", event["message"])
        self.assertNotIn("private", encoded)
        self.assertNotIn("--token", encoded)
        self.assertNotIn("very-secret", encoded)
        self.assertNotIn("must-not-leak", encoded)

    def test_file_change_sends_only_count(self):
        record = self.event(
            {
                "type": "item_completed",
                "turn_id": "turn-1",
                "item": {
                    "type": "FileChange",
                    "id": "item-2",
                    "changes": {"C:\\private\\src\\main.py": {"type": "update", "unified_diff": "secret diff"}},
                },
            }
        )
        encoded = json.dumps(self.parser.parse(record, self.path)[0])
        self.assertIn("Changed 1 file(s)", encoded)
        self.assertNotIn("main.py", encoded)
        self.assertNotIn("private", encoded)
        self.assertNotIn("secret diff", encoded)

    def test_subagent_activity(self):
        record = self.event(
            {
                "type": "item_completed",
                "turn_id": "turn-1",
                "item": {"type": "SubAgentActivity", "id": "item-3", "kind": "spawn", "agent_path": "/root/tests"},
            }
        )
        event = self.parser.parse(record, self.path)[0]
        self.assertEqual(event["phase"], "subagent_activity")
        self.assertIn("spawn", event["message"])

    def test_response_tool_call_and_safe_command_extraction(self):
        self.parser.parse(self.event({"type": "task_started", "turn_id": "turn-live"}), self.path)
        record = {
            "timestamp": "2026-09-08T00:00:00Z",
            "type": "response_item",
            "ordinal": 5,
            "payload": {
                "type": "function_call",
                "name": "exec_command",
                "call_id": "call-1",
                "arguments": json.dumps({"cmd": "build --password hidden"}),
            },
        }
        event = self.parser.parse(record, self.path)[0]
        self.assertEqual(event["phase"], "tool_started")
        self.assertEqual(event["type"], "command_started")
        self.assertEqual(event["task_id"], "turn-live")
        self.assertEqual(event["message"], "Command started: build")
        self.assertNotIn("password", json.dumps(event))
        self.assertNotIn("hidden", json.dumps(event))

    def test_non_allowlisted_records_are_ignored(self):
        record = {"type": "response_item", "payload": {"type": "message", "content": "private"}}
        self.assertEqual(self.parser.parse(record, self.path), [])

    def test_subagent_session_file_is_ignored_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rollout-subagent.jsonl"
            path.write_text(
                json.dumps({"type": "session_meta", "payload": {"agent_path": "/root/review"}}) + "\n",
                encoding="utf-8",
            )
            record = self.event({"type": "task_started", "turn_id": "subagent-turn"})
            self.assertEqual(self.parser.parse(record, path), [])

    def test_command_name_omits_paths_and_all_argument_forms(self):
        self.assertEqual(command_name('"C:\\Program Files\\Tool\\tool.exe" --token secret'), "tool.exe")
        self.assertEqual(command_name(["C:\\private\\curl.exe", "-u", "alice:secret"]), "curl.exe")
        self.assertEqual(command_name("DATABASE_URL=postgres://alice:secret@host/db tool"), "shell command")


class PollerTests(unittest.TestCase):
    def test_existing_files_start_at_end_and_new_files_start_at_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            existing = root / "existing.jsonl"
            existing.write_text('{"old":true}\n', encoding="utf-8")
            poller = SessionPoller(root, start_at_end=True)
            self.assertEqual(poller.poll(), [])
            with existing.open("a", encoding="utf-8") as handle:
                handle.write('{"new":true}\n')
            rows = poller.poll()
            self.assertEqual(json.loads(rows[0][1]), {"new": True})
            created = root / "created.jsonl"
            created.write_text('{"first":true}\n', encoding="utf-8")
            rows = poller.poll()
            self.assertEqual(json.loads(rows[0][1]), {"first": True})

    def test_partial_line_is_buffered(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "session.jsonl"
            path.write_bytes(b"")
            poller = SessionPoller(root, start_at_end=False)
            poller.poll()
            path.write_bytes(b'{"type":"event')
            self.assertEqual(poller.poll(), [])
            with path.open("ab") as handle:
                handle.write(b'_msg"}\n')
            rows = poller.poll()
            self.assertEqual(json.loads(rows[0][1])["type"], "event_msg")


class SenderTests(unittest.TestCase):
    def test_tcp_jsonl_and_acknowledgement(self):
        received = []
        ready = threading.Event()

        def server(listener):
            ready.set()
            connection, _ = listener.accept()
            with connection:
                data = b""
                while not data.endswith(b"\n"):
                    data += connection.recv(1024)
                received.append(json.loads(data.decode("utf-8")))
                connection.sendall(b'{"ok":true}\n')
            listener.close()

        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        thread = threading.Thread(target=server, args=(listener,), daemon=True)
        thread.start()
        ready.wait(1)
        config = Config(Path("."), "127.0.0.1", phone_port=port, token="shared", retries=0)
        TcpJsonSender(config).send({"type": "progress", "message": "test"})
        thread.join(2)
        self.assertEqual(received[0]["token"], "shared")
        self.assertEqual(received[0]["message"], "test")

    def test_missing_acknowledgement_is_not_treated_as_success(self):
        def server(listener):
            connection, _ = listener.accept()
            with connection:
                data = b""
                while not data.endswith(b"\n"):
                    chunk = connection.recv(1024)
                    if not chunk:
                        break
                    data += chunk
            listener.close()

        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        threading.Thread(target=server, args=(listener,), daemon=True).start()
        config = Config(Path("."), "127.0.0.1", phone_port=port, token="shared", retries=0)
        with self.assertRaises(ConnectionError):
            TcpJsonSender(config).send({"type": "progress", "message": "test"})


class WatcherTests(unittest.TestCase):
    class UnavailableSender:
        def send(self, event):
            raise ConnectionError("offline")

    class RecordingSender:
        def __init__(self):
            self.events = []

        def send(self, event):
            self.events.append(dict(event))

    @staticmethod
    def event(event_id, task_id, sequence, *, terminal=False):
        return {
            "event_id": event_id,
            "task_id": task_id,
            "sequence": sequence,
            "type": "completed" if terminal else "progress",
            "terminal": terminal,
        }

    def test_pending_event_is_restored_and_removed_only_after_ack(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spool = root / "spool" / "pending.json"
            session = root / "session.jsonl"
            session.write_text(
                json.dumps(
                    {
                        "timestamp": "2026-09-08T00:00:00Z",
                        "ordinal": 1,
                        "type": "event_msg",
                        "payload": {"type": "task_started", "turn_id": "turn-1"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            config = Config(
                root,
                "127.0.0.1",
                start_at_end=False,
                spool_path=spool,
                max_pending_events=10,
            )

            first = Watcher(config, self.UnavailableSender())
            self.assertEqual(first.tick(), (1, 0))
            saved = json.loads(spool.read_text(encoding="utf-8"))
            self.assertEqual(saved["events"][0]["task_id"], "turn-1")

            sender = self.RecordingSender()
            restarted = Watcher(config, sender, start_at_end=True)
            self.assertEqual(restarted.tick(), (0, 1))
            self.assertEqual(sender.events[0]["task_id"], "turn-1")
            self.assertEqual(json.loads(spool.read_text(encoding="utf-8"))["events"], [])

    def test_terminal_replaces_same_task_progress_and_has_queue_priority(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Config(Path(directory), "127.0.0.1", max_pending_events=2)
            watcher = Watcher(config, self.RecordingSender())
            watcher._enqueue_event(self.event("a-progress", "task-a", 1))
            watcher._enqueue_event(self.event("b-progress", "task-b", 1))
            watcher._enqueue_event(self.event("a-terminal", "task-a", 2, terminal=True))
            self.assertEqual([event["event_id"] for event in watcher.pending], ["a-terminal", "b-progress"])

            watcher._enqueue_event(self.event("c-terminal", "task-c", 1, terminal=True))
            self.assertEqual([event["event_id"] for event in watcher.pending], ["a-terminal", "c-terminal"])

    def test_new_progress_can_replace_stale_progress_for_same_task(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Config(Path(directory), "127.0.0.1", max_pending_events=2)
            watcher = Watcher(config, self.RecordingSender())
            watcher._enqueue_event(self.event("a-old", "task-a", 1))
            watcher._enqueue_event(self.event("b-terminal", "task-b", 1, terminal=True))
            self.assertTrue(watcher._enqueue_event(self.event("a-new", "task-a", 2)))
            self.assertEqual([event["event_id"] for event in watcher.pending], ["b-terminal", "a-new"])


class ConfigTests(unittest.TestCase):
    def test_load_expands_percent_environment_variable(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            old = os.environ.get("WATCHER_TEST_HOME")
            os.environ["WATCHER_TEST_HOME"] = directory
            try:
                config_path.write_text(
                    json.dumps(
                        {
                            "sessions_dir": "%WATCHER_TEST_HOME%/sessions",
                            "phone_host": "127.0.0.1",
                            "token": "x" * 32,
                        }
                    ),
                    encoding="utf-8",
                )
                config = Config.load(config_path)
                self.assertEqual(config.sessions_dir, Path(directory) / "sessions")
            finally:
                if old is None:
                    os.environ.pop("WATCHER_TEST_HOME", None)
                else:
                    os.environ["WATCHER_TEST_HOME"] = old

    def test_load_rejects_placeholder_token(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            config_path.write_text(
                json.dumps({"phone_host": "127.0.0.1", "token": "codex-fluid-change-me"}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "token"):
                Config.load(config_path)


if __name__ == "__main__":
    unittest.main()
