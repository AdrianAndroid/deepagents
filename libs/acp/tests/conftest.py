"""Shared pytest fixtures for the deepagents-acp test suite."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _clear_langsmith_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent LangSmith env vars from leaking into tests.

    When `LANGSMITH_TRACING=true` is set in the developer's environment,
    LangSmith's `run_tree.patch()` runs after every model call and serializes
    the chat model via `pydantic.model_dump()`. For test doubles like
    `GenericFakeChatModel` that carry an `Iterator` field, that serialization
    exhausts the iterator, causing the next real `_generate` call to raise
    `StopIteration` (converted to `RuntimeError` by `run_in_executor`). Clear
    the tracing-related vars so the fake models behave deterministically under
    `--disable-socket`.
    """
    for key in (
        "LANGSMITH_API_KEY",
        "LANGCHAIN_API_KEY",
        "LANGSMITH_TRACING",
        "LANGCHAIN_TRACING_V2",
        "LANGSMITH_ENDPOINT",
        "LANGCHAIN_ENDPOINT",
        "LANGSMITH_PROJECT",
        "LANGSMITH_LANGGRAPH_API_VARIANT",
    ):
        monkeypatch.delenv(key, raising=False)
