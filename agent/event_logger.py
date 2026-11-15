import json
import os
import uuid

from datetime import datetime, timezone

from .config import MODEL

RUN_ID = str(uuid.uuid4())
os.makedirs("logs", exist_ok=True)
LOG_FILE = os.path.join("logs", f"{RUN_ID}.log")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def log_event(
    event: str,
    ok: bool = True,
    tool: str | None = None,
    args: dict | None = None,
    duration_ms: int | None = None,
):
    entry = {
        "ts": now_iso(),
        "run_id": RUN_ID,
        "event": event,
        "tool": tool,
        "args": args,
        "ok": ok,
        "model": MODEL,
        "duration_ms": duration_ms,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
