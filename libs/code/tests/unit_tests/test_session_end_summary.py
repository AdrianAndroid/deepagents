"""Tests for `session_end_summary`."""

from __future__ import annotations

import io
import json
import signal
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

from deepagents_code import session_end_summary as ses


@pytest.fixture
def _isolated_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> "Generator[Path, None, None]":
    """Redirect config/state dirs to a temp path and reset module state."""
    monkeypatch.setattr(
        "deepagents_code.model_config.DEFAULT_CONFIG_DIR", tmp_path
    )
    monkeypatch.setattr(
        "deepagents_code.model_config.DEFAULT_STATE_DIR", tmp_path / ".state"
    )
    ses._reset_for_tests()
    yield tmp_path
    ses._reset_for_tests()


def test_completed_default(_isolated_state: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ses.install(thread_id="thr_completed")
    ses._finalize()
    err = capsys.readouterr().err
    assert "Session ended" in err
    assert "Reason:   completed" in err
    assert "Thread:   thr_completed" in err

    text_file = _isolated_state / ".state" / "session_end" / "thr_completed.txt"
    assert text_file.exists()
    body = text_file.read_text(encoding="utf-8")
    assert "Reason:   completed" in body

    jsonl = _isolated_state / "session_end_log.jsonl"
    assert jsonl.exists()
    line = jsonl.read_text(encoding="utf-8").strip().splitlines()[-1]
    record = json.loads(line)
    assert record["reason"] == "completed"
    assert record["thread_id"] == "thr_completed"


def test_interrupted_via_signal(
    _isolated_state: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ses.install(thread_id="thr_int")
    ses.mark_signal(int(signal.SIGINT))
    ses._finalize()
    err = capsys.readouterr().err
    assert "Reason:   interrupted (SIGINT)" in err

    jsonl = _isolated_state / "session_end_log.jsonl"
    record = json.loads(jsonl.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert record["reason"] == "interrupted"
    assert record["reason_detail"] == "SIGINT"


def test_error_via_excepthook(
    _isolated_state: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ses.install(thread_id="thr_err")
    exc = RuntimeError("boom")
    # simulate an unhandled exception hitting our chained excepthook.
    import sys

    sys.excepthook(RuntimeError, exc, None)  # type: ignore[arg-type]
    ses._finalize()
    err = capsys.readouterr().err
    assert "Reason:   error (RuntimeError: boom)" in err

    jsonl = _isolated_state / "session_end_log.jsonl"
    record = json.loads(jsonl.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert record["reason"] == "error"
    assert "RuntimeError: boom" in record["reason_detail"]


def test_finalize_is_idempotent(
    _isolated_state: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ses.install(thread_id="thr_idem")
    ses._finalize()
    ses._finalize()
    ses._finalize()
    jsonl = _isolated_state / "session_end_log.jsonl"
    lines = jsonl.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1


def test_reason_priority_error_wins_over_late_completed(
    _isolated_state: Path,
) -> None:
    ses.install(thread_id="thr_prio")
    ses.mark_reason(ses.REASON_ERROR, "X: y")
    # A later mark_reason(completed) should not downgrade.
    ses.mark_reason(ses.REASON_COMPLETED)
    ses._finalize()
    jsonl = _isolated_state / "session_end_log.jsonl"
    record = json.loads(jsonl.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert record["reason"] == "error"
    assert record["reason_detail"] == "X: y"


def test_set_thread_id_updates_before_finalize(_isolated_state: Path) -> None:
    ses.install()  # no thread id yet
    ses.set_thread_id("thr_late")
    ses._finalize()
    jsonl = _isolated_state / "session_end_log.jsonl"
    record = json.loads(jsonl.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert record["thread_id"] == "thr_late"


def test_unknown_reason_ignored(_isolated_state: Path) -> None:
    ses.install(thread_id="thr_bad")
    ses.mark_reason("nonsense", "should be ignored")
    ses._finalize()
    jsonl = _isolated_state / "session_end_log.jsonl"
    record = json.loads(jsonl.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert record["reason"] == "completed"
