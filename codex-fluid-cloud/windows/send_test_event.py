#!/usr/bin/env python3
"""Send a short notification lifecycle to the configured phone."""

from __future__ import annotations

import argparse
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from codex_watcher import Config, TcpJsonSender


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def main() -> int:
    local_config = Path(__file__).with_name("config.local.json")
    default_config = local_config if local_config.is_file() else Path(__file__).with_name("config.json")
    parser = argparse.ArgumentParser(description="Test the Codex Fluid Cloud phone bridge")
    parser.add_argument("--config", type=Path, default=default_config)
    parser.add_argument("--delay", type=float, default=0.8)
    args = parser.parse_args()

    config = Config.load(args.config.resolve())
    sender = TcpJsonSender(config)
    task_id = str(uuid.uuid4())
    lifecycle = (
        ("started", "Codex test started", -1, False),
        ("progress", "Testing live progress", 50, False),
        ("completed", "Codex test completed", 100, True),
    )
    for sequence, (event_type, message, percent, terminal) in enumerate(lifecycle, start=1):
        sender.send(
            {
                "version": 1,
                "event_id": str(uuid.uuid4()),
                "source": "codex-test",
                "task_id": task_id,
                "sequence": sequence,
                "type": event_type,
                "phase": "manual_test",
                "title": config.title,
                "message": message,
                "timestamp": timestamp(),
                "terminal": terminal,
                "percent": percent,
            }
        )
        print(f"sent {event_type}")
        if not terminal:
            time.sleep(max(0.0, args.delay))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
