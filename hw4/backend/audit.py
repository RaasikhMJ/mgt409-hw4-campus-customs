"""Append-only log of one stylist run. output/audit_trail.json is never replaced with a shorter file."""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path

from models import ProductLookup, StockLookup

HERE = Path(__file__).resolve().parent
AUDIT_PATH = HERE.parent / "output" / "audit_trail.json"
_LOCK = threading.Lock()
_LIMIT = 180


def _clip(text: str) -> str:
    text = " ".join((text or "").split())
    if len(text) <= _LIMIT:
        return text
    return text[: _LIMIT - 1] + "…"


def _short(value) -> str:
    if value is None:
        return ""
    if isinstance(value, ProductLookup):
        price = value.shown[0].price if value.shown else ""
        return _clip(
            f"found={value.found} matches={value.match_count} price={price} cards={len(value.cards)}"
        )
    if isinstance(value, StockLookup):
        return _clip(
            f"{value.name} size={value.size or 'all'} qty={value.quantity} in_stock={value.in_stock}"
        )
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    if isinstance(value, (dict, list)):
        return _clip(json.dumps(value, default=str))
    return _clip(str(value))


def steps_from_result(result) -> list[dict]:
    """One row per tool return, with the arguments from the matching call."""

    args_by_id: dict[str, str] = {}
    steps: list[dict] = []
    for message in result.new_messages():
        for part in getattr(message, "parts", ()):
            kind = getattr(part, "part_kind", "")
            name = getattr(part, "tool_name", "") or ""
            call_id = getattr(part, "tool_call_id", "") or name
            if kind == "tool-call":
                args_by_id[call_id] = _short(getattr(part, "args", ""))
            elif kind == "tool-return":
                steps.append(
                    {
                        "tool": name,
                        "args": args_by_id.get(call_id, ""),
                        "result": _short(getattr(part, "content", None)),
                    }
                )
    return steps


def append_run(steps: list[dict], stop: str, message: str, outcome: str) -> None:
    """Add this run to the trail. Existing rows stay at the top of the file."""

    now = datetime.now().astimezone().isoformat(timespec="seconds")
    rows = list(steps)
    if not rows:
        rows = [{"tool": "", "args": _clip(message), "result": _clip(outcome)}]
    for row in rows:
        row["time"] = now
        row["stop"] = stop
    with _LOCK:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        prior: list = []
        if AUDIT_PATH.is_file() and AUDIT_PATH.stat().st_size > 0:
            raw = AUDIT_PATH.read_text(encoding="utf-8")
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                prior = parsed
            else:
                prior = [
                    {
                        "time": now,
                        "tool": "audit_trail",
                        "args": "",
                        "result": _clip(raw),
                        "stop": "kept-previous-file",
                    }
                ]
        payload = prior + rows
        temporary = AUDIT_PATH.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary.replace(AUDIT_PATH)
