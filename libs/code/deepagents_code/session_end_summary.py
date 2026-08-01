"""Session-end summary writer.

Records why a zjcode session ended (`completed` / `interrupted` / `error`) and
how long it ran, then emits the result to three sinks on shutdown:

1. `stderr` — a human-readable panel printed after all UI teardown.
2. `~/.deepagents/.state/session_end/<thread_id>.txt` — one file per session
   (last-write-wins) for post-mortem inspection.
3. `~/.deepagents/session_end_log.jsonl` — one JSON line appended per session
   for audit/aggregation.

Design constraints:
- **Minimal-invasive**: this module is self-contained. It hooks into shutdown
  via `atexit` + `sys.excepthook`, so mainline code touches only
  `install(...)`, `set_thread_id(...)`, `mark_reason(...)`, and
  `mark_signal(...)` — small entry points that don't collide with upstream
  evolution of `app.py` or `client/non_interactive.py`.
- **Idempotent**: `_finalize()` may fire multiple times; a lock + `_finalized`
  flag makes only the first invocation write anything.
- **Never raises**: any I/O or formatting failure is logged at debug level and
  swallowed. Failing to write the summary must never mask the real exit code
  or crash the shutdown path.
- **Zero heavy imports at import time**: pulls `format_duration` lazily inside
  `_finalize` so this module stays cheap for the `-v` fast path.
"""

from __future__ import annotations

import atexit
import json
import logging
import os
import signal
import sys
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import TracebackType

logger = logging.getLogger(__name__)


REASON_COMPLETED = "completed"
"""Normal exit — `/exit`, Ctrl-D, end of script, `sys.exit(0)`, etc."""

REASON_INTERRUPTED = "interrupted"
"""User or OS terminated the process — Ctrl-C, SIGTERM, SIGHUP, SIGQUIT."""

REASON_ERROR = "error"
"""An unhandled exception propagated out of the program."""


_state_lock = threading.Lock()
"""Guards all mutable module-level state so mark/finalize races are safe."""

_installed = False
"""True after `install()` has run so double-install is a no-op."""

_finalized = False
"""True after `_finalize()` has emitted output so re-entry is a no-op."""

_start_monotonic: float | None = None
"""`time.monotonic()` at install time; used to compute wall-clock duration."""

_thread_id: str = ""
"""Session/thread id, populated by `set_thread_id` when known."""

_reason: str = REASON_COMPLETED
"""Current best guess at the exit reason; upgraded by `mark_reason`."""

_reason_detail: str = ""
"""Optional short human-readable detail (e.g. `SIGINT`, `RuntimeError: foo`)."""


# Upgrade order — higher wins. This lets late-arriving signals overwrite an
# earlier `completed`, but a first-seen `error` isn't clobbered by a later
# atexit-triggered `completed`.
_REASON_PRIORITY = {
    REASON_COMPLETED: 0,
    REASON_INTERRUPTED: 1,
    REASON_ERROR: 2,
}


_SIGNAL_NAMES: dict[int, str] = {}
for _name in ("SIGINT", "SIGTERM", "SIGHUP", "SIGQUIT"):
    _sig = getattr(signal, _name, None)
    if _sig is not None:
        _SIGNAL_NAMES[int(_sig)] = _name


def install(*, thread_id: str = "") -> None:
    """Register shutdown hooks and record the session start time.

    Safe to call more than once; subsequent calls are no-ops except that a
    non-empty `thread_id` will fill an empty slot.

    Args:
        thread_id: Best-known session/thread identifier at install time. May
            be updated later via `set_thread_id` once the client learns the
            real id.
    """
    global _installed, _start_monotonic

    with _state_lock:
        if not _installed:
            _start_monotonic = time.monotonic()
            _installed = True
            # atexit fires for normal termination *and* for `sys.exit()`, and
            # runs after Textual/Rich have torn down, so our stderr print is
            # not swallowed by an alt-screen. It does NOT fire for `os._exit`,
            # `kill -9`, or a fatal signal that bypasses Python — none of
            # which can be caught anywhere in userspace anyway.
            atexit.register(_finalize)
            _install_excepthook()

        if thread_id and not _thread_id:
            _set_thread_id_locked(thread_id)


def _install_excepthook() -> None:
    """Chain a classification wrapper on top of the existing `sys.excepthook`."""
    prev_hook = sys.excepthook

    def _hook(
        exc_type: type[BaseException],
        exc: BaseException,
        tb: TracebackType | None,
    ) -> None:
        # KeyboardInterrupt reaches excepthook when it escapes the main frame;
        # classify it as `interrupted`, not `error`.
        if issubclass(exc_type, KeyboardInterrupt):
            mark_reason(REASON_INTERRUPTED, "KeyboardInterrupt")
        elif issubclass(exc_type, SystemExit):
            # SystemExit is a normal exit path; don't upgrade to error.
            pass
        else:
            detail = f"{exc_type.__name__}: {exc}".strip()
            if len(detail) > 500:  # noqa: PLR2004
                detail = detail[:497] + "..."
            mark_reason(REASON_ERROR, detail)
        prev_hook(exc_type, exc, tb)

    sys.excepthook = _hook


def set_thread_id(thread_id: str) -> None:
    """Record the session/thread id once the client learns it."""
    if not thread_id:
        return
    with _state_lock:
        _set_thread_id_locked(thread_id)


def _set_thread_id_locked(thread_id: str) -> None:
    """Thread-id setter that assumes `_state_lock` is held."""
    global _thread_id
    _thread_id = thread_id


def mark_reason(reason: str, detail: str = "") -> None:
    """Upgrade the recorded exit reason if `reason` has higher priority.

    Args:
        reason: One of `REASON_COMPLETED` / `REASON_INTERRUPTED` /
            `REASON_ERROR`. Unknown values are ignored.
        detail: Short human-readable qualifier (e.g. `"SIGINT"`,
            `"RuntimeError: foo"`).
    """
    if reason not in _REASON_PRIORITY:
        return
    global _reason, _reason_detail
    with _state_lock:
        if _REASON_PRIORITY[reason] >= _REASON_PRIORITY[_reason]:
            _reason = reason
            if detail:
                _reason_detail = detail


def mark_signal(signum: int) -> None:
    """Record that a terminating signal was received.

    Called from `main.py`'s signal handler right before it raises
    `SystemExit`. `SystemExit` itself won't route through `sys.excepthook`, so
    this is the only chance to attach a signal-derived detail.
    """
    name = _SIGNAL_NAMES.get(signum, f"signal {signum}")
    mark_reason(REASON_INTERRUPTED, name)


def _summary_dir() -> Path:
    """`~/.deepagents/.state/session_end/`, created lazily and idempotently."""
    from deepagents_code.model_config import DEFAULT_STATE_DIR

    path = DEFAULT_STATE_DIR / "session_end"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _log_path() -> Path:
    """`~/.deepagents/session_end_log.jsonl`, parent created if missing."""
    from deepagents_code.model_config import DEFAULT_CONFIG_DIR

    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_CONFIG_DIR / "session_end_log.jsonl"


def _format_duration(seconds: float) -> str:
    """Format a duration; try `formatting.format_duration`, fall back locally."""
    try:
        from deepagents_code.formatting import format_duration

        return format_duration(seconds)
    except Exception:
        total = int(seconds)
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        if h:
            return f"{h}h{m:02d}m{s:02d}s"
        if m:
            return f"{m}m{s:02d}s"
        return f"{s}s"


def _sanitize_filename(name: str) -> str:
    """Strip path separators and other unsafe characters from a thread id."""
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)
    return safe or "unknown"


def _print_stderr_panel(
    reason_line: str,
    duration_pretty: str,
    thread_id: str,
) -> None:
    """Print the human-facing summary to stderr as a plain-text panel."""
    log_hint = "~/.deepagents/session_end_log.jsonl"
    lines = [
        "",
        "─────────── Session ended ───────────",
        f"Reason:   {reason_line}",
        f"Duration: {duration_pretty}",
        f"Thread:   {thread_id}",
        f"Log:      {log_hint}",
        "──────────────────────────────────────",
        "",
    ]
    sys.stderr.write("\n".join(lines))
    sys.stderr.flush()


def _finalize() -> None:
    """Emit the session-end summary to all three sinks. Idempotent."""
    global _finalized

    with _state_lock:
        if _finalized or not _installed:
            return
        _finalized = True
        reason = _reason
        detail = _reason_detail
        thread_id = _thread_id or "<unknown>"
        started = _start_monotonic

    duration = time.monotonic() - started if started is not None else 0.0
    duration_pretty = _format_duration(duration)
    reason_line = reason if not detail else f"{reason} ({detail})"

    try:
        _print_stderr_panel(reason_line, duration_pretty, thread_id)
    except Exception:
        logger.debug("session_end_summary stderr print failed", exc_info=True)

    try:
        safe_name = _sanitize_filename(thread_id)
        text_path = _summary_dir() / f"{safe_name}.txt"
        text_path.write_text(
            "Session ended\n"
            f"Reason:   {reason_line}\n"
            f"Duration: {duration_pretty} ({duration:.3f}s)\n"
            f"Thread:   {thread_id}\n"
            f"PID:      {os.getpid()}\n",
            encoding="utf-8",
        )
    except Exception:
        logger.debug("session_end_summary per-thread write failed", exc_info=True)

    try:
        record = {
            "ts": time.time(),
            "thread_id": thread_id,
            "pid": os.getpid(),
            "reason": reason,
            "reason_detail": detail,
            "duration_seconds": round(duration, 3),
            "duration_pretty": duration_pretty,
        }
        # `a` + `write(line + "\n")` in a single call is atomic on POSIX for
        # writes below PIPE_BUF; the JSON line is well under that limit.
        with _log_path().open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        logger.debug("session_end_summary JSONL append failed", exc_info=True)


def _reset_for_tests() -> None:
    """Reset all module state. Test-only; not part of the public API.

    Also unregisters the `atexit` handler installed by `install()` so pytest
    exit does not print a stray summary panel from a prior test's install.
    Tests that want the hooks re-armed should call `install()` again on a
    fresh clock.
    """
    global _installed, _finalized, _start_monotonic, _thread_id, _reason
    global _reason_detail
    try:
        atexit.unregister(_finalize)
    except Exception:
        pass
    with _state_lock:
        _installed = False
        _finalized = False
        _start_monotonic = None
        _thread_id = ""
        _reason = REASON_COMPLETED
        _reason_detail = ""
