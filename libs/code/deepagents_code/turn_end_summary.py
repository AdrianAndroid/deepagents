"""Per-turn end-status summary.

Records why a single agent turn ended and how long it ran, and always
emits a compact marker after the turn — no matter how the turn ended
(normal reply, truncated stream, tool error, user Ctrl-C, provider timeout).

Sibling `session_end_summary` covers process-level shutdown. This module
covers the per-turn level, where "the answer just cut off" happens while
the dcode process is still alive.

Design constraints:
- **Zero configuration**: always on; no env vars, no toml switch.
- **Never raises**: any I/O or formatting failure is logged at debug/warning
  and swallowed. Missing a marker must never mask the real exit code.
- **Idempotent per turn**: `finalize_turn` may fire more than once
  (finally-blocks stacked with explicit calls); only the first invocation
  between `mark_turn_start`/`finalize_turn` writes anything.
- **Cheap import**: no heavy dependencies at import time.

Sinks (best-effort, independent):

1. TUI / console — the caller mounts `render_marker_text(record)` after
   the assistant reply (or prints it to stderr in headless mode).
2. `~/.deepagents/turn_end_log.jsonl` — one JSON line per turn.
3. `<project_root>/doc/YYYY-MM-DD-*.md` — when a `doc/` folder exists in
   the project root, append a status line to the most recently modified
   doc file for the current day. Silent no-op if no such folder or file
   exists.
"""

from __future__ import annotations
import sys

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Reason constants
# --------------------------------------------------------------------------- #

REASON_COMPLETED = "completed"
REASON_LENGTH_CAPPED = "length_capped"
REASON_CONTENT_FILTERED = "content_filtered"
REASON_TOOL_REJECTED = "tool_rejected"
REASON_USER_INTERRUPTED = "user_interrupted"
REASON_STREAM_ERROR = "stream_error"
REASON_PROVIDER_ERROR = "provider_error"
REASON_TIMEOUT = "timeout"
REASON_RECURSION_LIMIT = "recursion_limit"
REASON_UNKNOWN_TRUNCATION = "unknown_truncation"

ALL_REASONS: frozenset[str] = frozenset(
    {
        REASON_COMPLETED,
        REASON_LENGTH_CAPPED,
        REASON_CONTENT_FILTERED,
        REASON_TOOL_REJECTED,
        REASON_USER_INTERRUPTED,
        REASON_STREAM_ERROR,
        REASON_PROVIDER_ERROR,
        REASON_TIMEOUT,
        REASON_RECURSION_LIMIT,
        REASON_UNKNOWN_TRUNCATION,
    }
)


_REASON_PRIORITY: dict[str, int] = {
    # `unknown_truncation` is the default and the least informative — any
    # explicit signal should be able to upgrade over it.
    REASON_UNKNOWN_TRUNCATION: 0,
    REASON_COMPLETED: 1,
    REASON_LENGTH_CAPPED: 2,
    REASON_CONTENT_FILTERED: 2,
    REASON_TOOL_REJECTED: 3,
    REASON_TIMEOUT: 3,
    REASON_PROVIDER_ERROR: 3,
    REASON_RECURSION_LIMIT: 3,
    REASON_STREAM_ERROR: 4,
    REASON_USER_INTERRUPTED: 5,
}


_REASON_EMOJI: dict[str, str] = {
    REASON_COMPLETED: "\u2705",
    REASON_LENGTH_CAPPED: "\u2702\ufe0f",
    REASON_CONTENT_FILTERED: "\U0001f6e1",
    REASON_TOOL_REJECTED: "\U0001f6ab",
    REASON_USER_INTERRUPTED: "\u23f8",
    REASON_STREAM_ERROR: "\u26a0\ufe0f",
    REASON_PROVIDER_ERROR: "\u26a0\ufe0f",
    REASON_TIMEOUT: "\u23f1",
    REASON_RECURSION_LIMIT: "\U0001f501",
    REASON_UNKNOWN_TRUNCATION: "\u2754",
}


_REASON_LABEL: dict[str, str] = {
    REASON_COMPLETED: "\u6b63\u5e38\u7ed3\u675f",
    REASON_LENGTH_CAPPED: "\u8f93\u51fa\u88ab\u622a\u65ad(max_tokens)",
    REASON_CONTENT_FILTERED: "\u5185\u5bb9\u88ab\u8fc7\u6ee4",
    REASON_TOOL_REJECTED: "\u5de5\u5177\u88ab\u62d2\u7edd",
    REASON_USER_INTERRUPTED: "\u7528\u6237\u4e2d\u65ad",
    REASON_STREAM_ERROR: "\u6d41\u5f02\u5e38",
    REASON_PROVIDER_ERROR: "\u63d0\u4f9b\u65b9\u9519\u8bef",
    REASON_TIMEOUT: "\u8d85\u65f6",
    REASON_RECURSION_LIMIT: "\u9012\u5f52\u4e0a\u9650",
    REASON_UNKNOWN_TRUNCATION: "\u7591\u4f3c\u622a\u65ad(\u65e0 finish_reason)",
}


_FINISH_REASON_MAP: dict[str, str] = {
    "stop": REASON_COMPLETED,
    "end_turn": REASON_COMPLETED,
    "complete": REASON_COMPLETED,
    "finished": REASON_COMPLETED,
    "eos": REASON_COMPLETED,
    "length": REASON_LENGTH_CAPPED,
    "max_tokens": REASON_LENGTH_CAPPED,
    "model_length": REASON_LENGTH_CAPPED,
    "model_max_tokens": REASON_LENGTH_CAPPED,
    "output_length": REASON_LENGTH_CAPPED,
    "max_output_tokens": REASON_LENGTH_CAPPED,
    "content_filter": REASON_CONTENT_FILTERED,
    "safety": REASON_CONTENT_FILTERED,
    "blocked": REASON_CONTENT_FILTERED,
}


_TOOL_CALL_FINISH_REASONS = frozenset({"tool_calls", "tool_use", "function_call"})


# --------------------------------------------------------------------------- #
# Module state
# --------------------------------------------------------------------------- #

_state_lock = threading.RLock()


@dataclass
class _TurnState:
    start_monotonic: float | None = None
    thread_id: str = ""
    turn_id: str = ""
    turn_number: int | None = None
    reason: str = REASON_UNKNOWN_TRUNCATION
    detail: str = ""
    finish_reason_raw: str = ""
    finalized: bool = False
    started: bool = False


_current: _TurnState = _TurnState()


@dataclass
class TurnEndRecord:
    """Immutable snapshot returned by `finalize_turn`."""

    reason: str
    detail: str
    duration_seconds: float
    duration_pretty: str
    thread_id: str
    turn_id: str
    turn_number: int | None
    finish_reason_raw: str
    ended_at: float = field(default_factory=time.time)


# --------------------------------------------------------------------------- #
# Public API — state mutation
# --------------------------------------------------------------------------- #


def mark_turn_start(
    *,
    thread_id: str = "",
    turn_id: str | None = None,
    turn_number: int | None = None,
) -> None:
    """Reset per-turn state and record the start time."""
    global _current
    with _state_lock:
        _current = _TurnState()
        _current.started = True
        _current.start_monotonic = time.monotonic()
        _current.thread_id = thread_id or ""
        _current.turn_id = turn_id or ""
        _current.turn_number = turn_number


def classify_finish_reason(finish_reason: str | None) -> str | None:
    """Classify a raw provider `finish_reason` into a normalized reason.

    Returns `None` for tool-call handoff or unrecognized values.
    """
    if not finish_reason or not isinstance(finish_reason, str):
        return None
    normalized = finish_reason.strip().lower()
    if not normalized or normalized in _TOOL_CALL_FINISH_REASONS:
        return None
    return _FINISH_REASON_MAP.get(normalized)


def observe_finish_reason(finish_reason: str | None) -> None:
    """Update the classified reason from a raw `finish_reason` observation."""
    if not finish_reason or not isinstance(finish_reason, str):
        return
    with _state_lock:
        _current.finish_reason_raw = finish_reason
    classified = classify_finish_reason(finish_reason)
    if classified is not None:
        mark_turn_reason(classified, detail=f"finish_reason={finish_reason}")


def mark_turn_reason(reason: str, detail: str = "") -> None:
    """Upgrade the current turn's reason if `reason` has higher priority."""
    if reason not in _REASON_PRIORITY:
        return
    with _state_lock:
        if _REASON_PRIORITY[reason] >= _REASON_PRIORITY[_current.reason]:
            _current.reason = reason
            if detail:
                _current.detail = detail


def classify_exception(exc: BaseException) -> tuple[str, str]:
    """Classify an in-flight exception into a `(reason, detail)` pair.

    Uses only class name + message so this module stays free of heavy imports.
    """
    name = type(exc).__name__
    msg = str(exc).strip()
    detail = f"{name}: {msg}" if msg else name
    if len(detail) > 500:
        detail = detail[:497] + "..."

    if isinstance(exc, KeyboardInterrupt):
        return REASON_USER_INTERRUPTED, "KeyboardInterrupt"
    try:
        import asyncio

        if isinstance(exc, asyncio.CancelledError):
            return REASON_USER_INTERRUPTED, "CancelledError"
    except Exception:
        pass

    lowered = name.lower()
    if "timeout" in lowered:
        return REASON_TIMEOUT, detail
    if "graphrecursion" in lowered or "recursionerror" in lowered:
        return REASON_RECURSION_LIMIT, detail
    if "httpstatus" in lowered or "clientresponse" in lowered:
        return REASON_PROVIDER_ERROR, detail
    if "connect" in lowered or "transport" in lowered or "network" in lowered:
        return REASON_PROVIDER_ERROR, detail
    return REASON_STREAM_ERROR, detail


def is_active() -> bool:
    """Return whether a turn has been started but not yet finalized."""
    with _state_lock:
        return _current.started and not _current.finalized


# --------------------------------------------------------------------------- #
# Public API — finalize
# --------------------------------------------------------------------------- #


def _format_duration(seconds: float) -> str:
    """Format a duration; try `formatting.format_duration`, fall back locally."""
    try:
        from deepagents_code.formatting import format_duration

        return format_duration(seconds)
    except Exception:
        rounded = round(seconds, 1)
        if rounded < 60:
            return f"{rounded:.1f}s" if rounded % 1 else f"{int(rounded)}s"
        total = int(seconds)
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        if h:
            return f"{h}h{m:02d}m{s:02d}s"
        return f"{m}m{s:02d}s"


def finalize_turn() -> TurnEndRecord | None:
    """Emit sinks and return the record. Idempotent.

    Returns `None` if no turn was ever started, or if the turn has already
    been finalized (double-finalize is a no-op).
    """
    with _state_lock:
        if not _current.started or _current.finalized:
            return None
        _current.finalized = True
        started = _current.start_monotonic
        reason = _current.reason
        detail = _current.detail
        thread_id = _current.thread_id
        turn_id = _current.turn_id
        turn_number = _current.turn_number
        finish_raw = _current.finish_reason_raw

    duration = time.monotonic() - started if started is not None else 0.0
    record = TurnEndRecord(
        reason=reason,
        detail=detail,
        duration_seconds=round(duration, 3),
        duration_pretty=_format_duration(duration),
        thread_id=thread_id,
        turn_id=turn_id,
        turn_number=turn_number,
        finish_reason_raw=finish_raw,
    )

    # Sink 2: JSONL audit log — always attempted.
    try:
        _append_jsonl(record)
    except Exception:
        logger.debug("turn_end_summary JSONL append failed", exc_info=True)

    # Sink 3: doc/ auto-append — best-effort, silent when doc/ absent.
    try:
        _append_to_doc(record)
    except Exception:
        logger.debug("turn_end_summary doc append failed", exc_info=True)

    return record


# --------------------------------------------------------------------------- #
# Public API — rendering
# --------------------------------------------------------------------------- #


def render_marker_text(record: TurnEndRecord) -> str:
    """Render the single-line human-readable marker.

    Format:
      "⏹ 结束状态：<emoji> <label>[ (detail)] | ⏱ 总耗时：<pretty> | 🕒 结束时间：<ts>"
    """
    emoji = _REASON_EMOJI.get(record.reason, "\u2754")
    label = _REASON_LABEL.get(record.reason, record.reason)
    reason_part = f"{emoji} {label}"
    if record.detail:
        reason_part = f"{reason_part} ({record.detail})"
    ended_at = datetime.fromtimestamp(record.ended_at).strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"\u23f9 \u7ed3\u675f\u72b6\u6001\uff1a{reason_part} | "
        f"\u23f1 \u603b\u8017\u65f6\uff1a{record.duration_pretty} | "
        f"\U0001f552 \u7ed3\u675f\u65f6\u95f4\uff1a{ended_at}"
    )


def render_marker_line(record: TurnEndRecord) -> str:
    """Marker prefixed with `> ` for Markdown-blockquote appending."""
    return f"> {render_marker_text(record)}"


# --------------------------------------------------------------------------- #
# Sinks
# --------------------------------------------------------------------------- #


def _log_path() -> Path:
    """`~/.deepagents/turn_end_log.jsonl`, parent created if missing."""
    from deepagents_code.model_config import DEFAULT_CONFIG_DIR

    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_CONFIG_DIR / "turn_end_log.jsonl"


def _append_jsonl(record: TurnEndRecord) -> None:
    payload = {
        "ts": record.ended_at,
        "thread_id": record.thread_id,
        "turn_id": record.turn_id,
        "turn_number": record.turn_number,
        "pid": os.getpid(),
        "reason": record.reason,
        "reason_detail": record.detail,
        "finish_reason_raw": record.finish_reason_raw,
        "duration_seconds": record.duration_seconds,
        "duration_pretty": record.duration_pretty,
    }
    # POSIX atomic append: one `write` on a small line stays below PIPE_BUF.
    with _log_path().open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------- #
# Sink: doc/ auto-append (project-root detected, silent fallback)
# --------------------------------------------------------------------------- #

# Files a directory must contain to qualify as a project root. Order matters
# only for readability; any single hit anchors the root.
_PROJECT_ROOT_MARKERS: tuple[str, ...] = (
    "AGENTS.md",
    ".git",
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "go.mod",
)


def _find_project_root(start: Path | None = None) -> Path | None:
    """Walk upward from `start` until a project-root marker is found.

    Returns `None` if no marker is found before the filesystem root. Uses a
    bounded upward walk to avoid pathological infinite loops in tests.
    """
    try:
        cur = (start or Path.cwd()).resolve()
    except Exception:
        return None
    # Bound the walk. 40 levels is deeper than any realistic project path.
    for _ in range(40):
        for marker in _PROJECT_ROOT_MARKERS:
            if (cur / marker).exists():
                return cur
        if cur.parent == cur:
            return None
        cur = cur.parent
    return None


def _pick_today_doc(doc_dir: Path) -> Path | None:
    """Pick the newest doc file matching today's date prefix.

    Returns the file with the largest mtime whose name starts with
    `YYYY-MM-DD-` for today's date. `None` if no such file exists.
    """
    if not doc_dir.is_dir():
        return None
    today = datetime.now().strftime("%Y-%m-%d")
    prefix = f"{today}-"
    candidates: list[Path] = []
    try:
        for entry in doc_dir.iterdir():
            if entry.is_file() and entry.name.startswith(prefix) and entry.suffix == ".md":
                candidates.append(entry)
    except Exception:
        return None
    if not candidates:
        return None
    try:
        return max(candidates, key=lambda p: p.stat().st_mtime)
    except Exception:
        return None


def _append_to_doc(record: TurnEndRecord) -> None:
    """Append the marker line to the most-recent same-day doc, if any."""
    root = _find_project_root()
    if root is None:
        return
    doc_dir = root / "doc"
    target = _pick_today_doc(doc_dir)
    if target is None:
        return
    line = render_marker_line(record)
    try:
        # Ensure the marker starts on its own line even if the file did not
        # end with a newline. Read the last byte cheaply rather than the
        # whole file.
        needs_leading_newline = False
        try:
            with target.open("rb") as fp:
                fp.seek(0, os.SEEK_END)
                if fp.tell() > 0:
                    fp.seek(-1, os.SEEK_END)
                    last = fp.read(1)
                    needs_leading_newline = last not in (b"\n", b"\r")
        except Exception:
            needs_leading_newline = False
        with target.open("a", encoding="utf-8") as fp:
            if needs_leading_newline:
                fp.write("\n")
            fp.write(line + "\n")
    except Exception:
        logger.debug("turn_end_summary doc write failed for %s", target, exc_info=True)


# --------------------------------------------------------------------------- #
# Test helpers
# --------------------------------------------------------------------------- #


def _reset_for_tests() -> None:
    """Reset all module state. Test-only; not part of the public API."""
    global _current
    with _state_lock:
        _current = _TurnState()


def _snapshot_for_tests() -> _TurnState:
    """Return a shallow copy of the current in-progress turn state."""
    with _state_lock:
        return _TurnState(
            start_monotonic=_current.start_monotonic,
            thread_id=_current.thread_id,
            turn_id=_current.turn_id,
            turn_number=_current.turn_number,
            reason=_current.reason,
            detail=_current.detail,
            finish_reason_raw=_current.finish_reason_raw,
            finalized=_current.finalized,
            started=_current.started,
        )
