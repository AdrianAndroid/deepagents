"""Tests for agent error body formatting."""

from __future__ import annotations

from deepagents_code.app import _build_agent_error_body


class TestBuildAgentErrorBody:
    """Tests for `_build_agent_error_body` error enrichment."""

    def test_bad_request_error_gets_guidance(self) -> None:
        """BadRequestError should get actionable guidance appended."""
        exc = Exception("Bad request")
        exc.args = ({"error": "BadRequestError", "message": "An internal error occurred"},)
        result = _build_agent_error_body("Agent error: BadRequestError: An internal error occurred", exc)
        text = str(result)
        assert "too large" in text.lower() or "unsupported" in text.lower()
        assert "removed from the conversation" in text

    def test_permission_denied_error_gets_gateway_link(self) -> None:
        """PermissionDeniedError should get gateway guidance."""
        exc = Exception("Permission denied")
        exc.args = ({"error": "PermissionDeniedError", "message": "Forbidden"},)
        result = _build_agent_error_body("Agent error: PermissionDeniedError: Forbidden", exc)
        text = str(result)
        assert "API key" in text or "key" in text.lower()

    def test_other_error_returns_text_unchanged(self) -> None:
        """Non-BadRequest/PermissionDenied errors should return text unchanged."""
        exc = Exception("Some other error")
        exc.args = ({"error": "RateLimitError", "message": "Too many requests"},)
        text = "Agent error: RateLimitError: Too many requests"
        result = _build_agent_error_body(text, exc)
        assert result == text
