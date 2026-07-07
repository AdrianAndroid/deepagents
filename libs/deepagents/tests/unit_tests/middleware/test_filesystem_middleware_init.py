"""Unit tests for FilesystemMiddleware initialization and configuration."""

from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware.types import ModelRequest, ModelResponse
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.store.memory import InMemoryStore

from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.middleware.filesystem import (
    EXECUTION_SYSTEM_PROMPT,
    WRITE_FILE_TOOL_DESCRIPTION,
    FilesystemMiddleware,
    _accepts_native_absolute_paths,
)
from tests.unit_tests.chat_model import GenericFakeChatModel


def build_composite_state_backend(*, routes: dict[str, Any]) -> CompositeBackend:
    return CompositeBackend(default=StateBackend(), routes=routes)


class TestDynamicSystemPromptCache:
    """`_build_dynamic_system_prompt` caches per `include_execution` flag."""

    def test_returns_identical_cached_object(self) -> None:
        mw = FilesystemMiddleware(backend=StateBackend())
        first = mw._build_dynamic_system_prompt(include_execution=False)
        second = mw._build_dynamic_system_prompt(include_execution=False)
        assert first is second

    def test_execution_flag_changes_output(self) -> None:
        mw = FilesystemMiddleware(backend=StateBackend())
        without = mw._build_dynamic_system_prompt(include_execution=False)
        with_exec = mw._build_dynamic_system_prompt(include_execution=True)
        assert without != with_exec
        assert EXECUTION_SYSTEM_PROMPT not in without
        assert EXECUTION_SYSTEM_PROMPT in with_exec

    async def test_awrap_model_call_emits_dynamic_prompt(self) -> None:
        """`awrap_model_call` appends the same memoized prompt as the sync path.

        The cache call site is duplicated across `wrap_model_call` and
        `awrap_model_call`; this guards the async path against drift.
        """
        mw = FilesystemMiddleware(backend=StateBackend())
        # StateBackend has no execution support, so the execute tool (if any)
        # is filtered out and `include_execution` resolves to False.
        expected = mw._build_dynamic_system_prompt(include_execution=False)

        captured: list[ModelRequest] = []

        async def handler(request: ModelRequest) -> ModelResponse:
            captured.append(request)
            return ModelResponse(result=[AIMessage(content="ok")])

        request = ModelRequest(
            model=GenericFakeChatModel(messages=iter([AIMessage(content="ok")])),
            messages=[HumanMessage(content="hi")],
            tools=[],
        )

        await mw.awrap_model_call(request, handler)

        assert len(captured) == 1
        assert captured[0].system_prompt == expected


class TestFilesystemMiddlewareInit:
    """Tests for FilesystemMiddleware initialization that don't require LLM invocation."""

    def test_filesystem_tool_prompt_override(self) -> None:
        """Test that custom tool descriptions can be set via FilesystemMiddleware."""
        agent = create_agent(
            model=ChatAnthropic(model="claude-sonnet-4-6"),
            middleware=[
                FilesystemMiddleware(
                    backend=StateBackend(),
                    custom_tool_descriptions={
                        "ls": "Charmander",
                        "read_file": "Bulbasaur",
                        "edit_file": "Squirtle",
                    },
                )
            ],
        )
        tools = agent.nodes["tools"].bound._tools_by_name
        assert "ls" in tools
        assert tools["ls"].description == "Charmander"
        assert "read_file" in tools
        assert tools["read_file"].description == "Bulbasaur"
        assert "write_file" in tools
        assert tools["write_file"].description == WRITE_FILE_TOOL_DESCRIPTION.rstrip()
        assert "edit_file" in tools
        assert tools["edit_file"].description == "Squirtle"

    def test_filesystem_tool_prompt_override_with_longterm_memory(self) -> None:
        """Test that custom tool descriptions work with composite backends and longterm memory."""
        agent = create_agent(
            model=ChatAnthropic(model="claude-sonnet-4-6"),
            middleware=[
                FilesystemMiddleware(
                    backend=build_composite_state_backend(routes={"/memories/": StoreBackend()}),
                    custom_tool_descriptions={
                        "ls": "Charmander",
                        "read_file": "Bulbasaur",
                        "edit_file": "Squirtle",
                    },
                )
            ],
            store=InMemoryStore(),
        )
        tools = agent.nodes["tools"].bound._tools_by_name
        assert "ls" in tools
        assert tools["ls"].description == "Charmander"
        assert "read_file" in tools
        assert tools["read_file"].description == "Bulbasaur"
        assert "write_file" in tools
        assert tools["write_file"].description == WRITE_FILE_TOOL_DESCRIPTION.rstrip()
        assert "edit_file" in tools
        assert tools["edit_file"].description == "Squirtle"


class TestAcceptsNativeAbsolutePaths:
    """`_accepts_native_absolute_paths` gates OS-native path pass-through."""

    def test_non_virtual_filesystem_backend_accepts(self) -> None:
        assert _accepts_native_absolute_paths(FilesystemBackend(virtual_mode=False)) is True

    def test_virtual_filesystem_backend_rejects(self) -> None:
        assert _accepts_native_absolute_paths(FilesystemBackend(virtual_mode=True)) is False

    def test_state_backend_rejects(self) -> None:
        assert _accepts_native_absolute_paths(StateBackend()) is False

    def test_composite_follows_default_backend(self) -> None:
        non_virtual = CompositeBackend(
            default=FilesystemBackend(virtual_mode=False),
            routes={"/memories/": StoreBackend()},
        )
        virtual = CompositeBackend(
            default=FilesystemBackend(virtual_mode=True),
            routes={"/memories/": StoreBackend()},
        )
        assert _accepts_native_absolute_paths(non_virtual) is True
        assert _accepts_native_absolute_paths(virtual) is False
