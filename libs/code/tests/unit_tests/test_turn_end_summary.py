"""Tests for `turn_end_summary`."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

from deepagents_code import turn_end_summary as tes


@pytest.fixture
def _isolated_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> "Generator[Path, None, None]":
    """Redirect the config dir and reset module state."""
    monkeypatch.setattr(
        "deepagents_code.model_config.DEFAULT_CONFIG_DIR", tmp_path
    )
    # Prevent project-root walk from finding the real repo `doc/` folder.
    monkeypatch.chdir(tmp_path)
    tes._reset_for_tests()
    yield tmp_path
    tes._reset_for_tests()


# --------------------------------------------------------------------------- #
# classify_finish_reason
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("stop", tes.REASON_COMPLETED),
        ("end_turn", tes.REASON_COMPLETED),
        ("length", tes.REASON_LENGTH_CAPPED),
        ("max_tokens", tes.REASON_LENGTH_CAPPED),
        ("max_output_tokens", tes.REASON_LENGTH_CAPPED),
        ("content_filter", tes.REASON_CONTENT_FILTERED),
        ("safety", tes.REASON_CONTENT_FILTERED),
        ("tool_calls", None),
        ("tool_use", None),
        ("mystery_finish", None),
        ("", None),
        (None, None),
    ],
)
def test_classify_finish_reason(raw: str | None, expected: str | None) -> None:
    assert tes.classify_finish_reason(raw) == expected


# --------------------------------------------------------------------------- #
# classify_exception
# --------------------------------------------------------------------------- #


def test_classify_exception_keyboard_interrupt() -> None:
    reason, detail = tes.classify_exception(KeyboardInterrupt())
    assert reason == tes.REASON_USER_INTERRUPTED
    assert "KeyboardInterrupt" in detail


def test_classify_exception_cancelled() -> None:
    reason, _ = tes.classify_exception(asyncio.CancelledError())
    assert reason == tes.REASON_USER_INTERRUPTED


def test_classify_exception_timeout() -> None:
    reason, _ = tes.classify_exception(TimeoutError("slow"))
    assert reason == tes.REASON_TIMEOUT


def test_classify_exception_recursion() -> None:
    class GraphRecursionError(Exception):
        pass

    reason, _ = tes.classify_exception(GraphRecursionError("too deep"))
    assert reason == tes.REASON_RECURSION_LIMIT


def test_classify_exception_provider_transport() -> None:
    class ConnectError(Exception):
        pass

    reason, _ = tes.classify_exception(ConnectError("refused"))
    assert reason == tes.REASON_PROVIDER_ERROR


def test_classify_exception_stream_default() -> None:
    reason, _ = tes.classify_exception(RuntimeError("boom"))
    assert reason == tes.REASON_STREAM_ERROR


# --------------------------------------------------------------------------- #
# Priority upgrade rules
# --------------------------------------------------------------------------- #


def test_priority_upgrade_length_beats_completed(_isolated_state: Path) -> None:
    tes.mark_turn_start(thread_id="t1")
    tes.observe_finish_reason("stop")
    assert tes._snapshot_for_tests().reason == tes.REASON_COMPLETED
    tes.observe_finish_reason("length")
    assert tes._snapshot_for_tests().reason == tes.REASON_LENGTH_CAPPED


def test_priority_upgrade_error_beats_length(_isolated_state: Path) -> None:
    tes.mark_turn_start(thread_id="t1")
    tes.observe_finish_reason("length")
    tes.mark_turn_reason(tes.REASON_STREAM_ERROR, "boom")
    assert tes._snapshot_for_tests().reason == tes.REASON_STREAM_ERROR


def test_priority_lower_reason_does_not_downgrade(_isolated_state: Path) -> None:
    tes.mark_turn_start(thread_id="t1")
    tes.mark_turn_reason(tes.REASON_STREAM_ERROR, "boom")
    tes.observe_finish_reason("stop")
    # `completed` must not overwrite `stream_error`.
    assert tes._snapshot_for_tests().reason == tes.REASON_STREAM_ERROR


def test_default_is_unknown_truncation(_isolated_state: Path) -> None:
    tes.mark_turn_start(thread_id="t1")
    record = tes.finalize_turn()
    assert record is not None
    assert record.reason == tes.REASON_UNKNOWN_TRUNCATION


# --------------------------------------------------------------------------- #
# finalize_turn: sinks + idempotency
# --------------------------------------------------------------------------- #


def test_finalize_writes_jsonl(_isolated_state: Path) -> None:
    tes.mark_turn_start(thread_id="thr_x", turn_id="u1", turn_number=3)
    tes.observe_finish_reason("length")
    record = tes.finalize_turn()
    assert record is not None
    assert record.reason == tes.REASON_LENGTH_CAPPED
    assert record.thread_id == "thr_x"
    assert record.turn_number == 3

    jsonl = _isolated_state / "turn_end_log.jsonl"
    assert jsonl.exists()
    row = json.loads(jsonl.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert row["reason"] == "length_capped"
    assert row["thread_id"] == "thr_x"
    assert row["turn_number"] == 3
    assert row["finish_reason_raw"] == "length"


def test_finalize_is_idempotent(_isolated_state: Path) -> None:
    tes.mark_turn_start(thread_id="t1")
    first = tes.finalize_turn()
    second = tes.finalize_turn()
    assert first is not None
    assert second is None
    # Only one line written.
    jsonl = _isolated_state / "turn_end_log.jsonl"
    assert len(jsonl.read_text(encoding="utf-8").strip().splitlines()) == 1


def test_finalize_no_op_when_not_started(_isolated_state: Path) -> None:
    assert tes.finalize_turn() is None
    jsonl = _isolated_state / "turn_end_log.jsonl"
    assert not jsonl.exists()


# --------------------------------------------------------------------------- #
# doc/ auto-append
# --------------------------------------------------------------------------- #


def test_doc_append_writes_line_to_todays_doc(
    _isolated_state: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Anchor the project root.
    (_isolated_state / "AGENTS.md").write_text("root marker", encoding="utf-8")
    doc_dir = _isolated_state / "doc"
    doc_dir.mkdir()
    today = datetime.now().strftime("%Y-%m-%d")
    doc_file = doc_dir / f"{today}-notes.md"
    doc_file.write_text("# notes\n\ncontent", encoding="utf-8")

    tes.mark_turn_start(thread_id="doc_thr")
    tes.observe_finish_reason("stop")
    record = tes.finalize_turn()
    assert record is not None

    updated = doc_file.read_text(encoding="utf-8")
    # Missing trailing newline was patched in, marker starts on its own line.
    assert updated.startswith("# notes\n\ncontent")
    assert "> \u23f9" in updated  # ⏹ marker prefix in blockquote form.
    assert record.reason == tes.REASON_COMPLETED


def test_doc_append_silent_when_no_doc_dir(_isolated_state: Path) -> None:
    (_isolated_state / "AGENTS.md").write_text("root marker", encoding="utf-8")
    # No `doc/` created.
    tes.mark_turn_start(thread_id="doc_thr")
    record = tes.finalize_turn()
    assert record is not None
    # JSONL still writes; the absence of doc/ must not break the sink.
    assert (_isolated_state / "turn_end_log.jsonl").exists()


def test_doc_append_silent_when_no_matching_doc(_isolated_state: Path) -> None:
    (_isolated_state / "AGENTS.md").write_text("root marker", encoding="utf-8")
    doc_dir = _isolated_state / "doc"
    doc_dir.mkdir()
    # Different day, must not be touched.
    other = doc_dir / "2000-01-01-old.md"
    other.write_text("stable content", encoding="utf-8")

    tes.mark_turn_start(thread_id="doc_thr")
    tes.finalize_turn()
    assert other.read_text(encoding="utf-8") == "stable content"


# --------------------------------------------------------------------------- #
# render_marker_text
# --------------------------------------------------------------------------- #


def test_render_marker_text_shape(_isolated_state: Path) -> None:
    tes.mark_turn_start(thread_id="t1")
    tes.observe_finish_reason("length")
    record = tes.finalize_turn()
    assert record is not None
    text = tes.render_marker_text(record)
    # Contains the three sections: status, duration, timestamp.
    assert "\u23f9" in text  # ⏹
    assert "\u23f1" in text  # ⏱
    assert "\U0001f552" in text  # 🕒
    assert "length_capped" not in text  # renders the label, not the constant.


def test_render_marker_text_for_unknown_truncation(_isolated_state: Path) -> None:
    tes.mark_turn_start(thread_id="t1")
    record = tes.finalize_turn()
    assert record is not None
    text = tes.render_marker_text(record)
    assert "\u2754" in text  # ❔ emoji for the default bucket.
