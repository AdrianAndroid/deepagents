"""Tests for image clipboard functionality."""

import base64
import subprocess
from unittest import mock

import pytest

from deepagents_code.media_utils import ImageData


class TestCopyImageToClipboard:
    """Tests for copy_image_to_clipboard."""

    def test_macos_success(self, monkeypatch):
        """Test successful image copy on macOS."""
        # Import after setting up patches
        import deepagents_code.clipboard as cb

        img = ImageData(
            base64_data=base64.b64encode(b"fake png data").decode(),
            format="png",
            placeholder="[img_001]",
        )

        monkeypatch.setattr(cb.sys, "platform", "darwin")
        monkeypatch.setattr(cb.shutil, "which", lambda x: "/usr/bin/osascript")

        run_calls = []

        def fake_run(*args, **kwargs):
            run_calls.append((args, kwargs))
            return mock.Mock(returncode=0)

        monkeypatch.setattr(cb.subprocess, "run", fake_run)

        write_calls = []

        def fake_write(self, data):
            write_calls.append(data)
            return len(data)

        monkeypatch.setattr(cb.pathlib.Path, "write_bytes", fake_write)

        unlink_calls = []

        def fake_unlink(self, *args, **kwargs):
            unlink_calls.append(True)

        monkeypatch.setattr(cb.pathlib.Path, "exists", lambda self: True)
        monkeypatch.setattr(cb.pathlib.Path, "unlink", fake_unlink)
        monkeypatch.setattr(cb.tempfile, "mkstemp", lambda suffix=None: (3, "/tmp/test.png"))
        monkeypatch.setattr(cb.os, "close", lambda fd: None)

        success, error = cb.copy_image_to_clipboard(img)
        assert success is True
        assert error is None
        assert len(run_calls) > 0

    def test_macos_subprocess_failure(self, monkeypatch):
        """Test subprocess failure on macOS."""
        import deepagents_code.clipboard as cb

        img = ImageData(
            base64_data=base64.b64encode(b"fake png data").decode(),
            format="png",
            placeholder="[img_001]",
        )

        monkeypatch.setattr(cb.sys, "platform", "darwin")
        monkeypatch.setattr(cb.shutil, "which", lambda x: "/usr/bin/osascript")

        def fake_run(*args, **kwargs):
            return mock.Mock(returncode=1, stderr="osascript error")

        monkeypatch.setattr(cb.subprocess, "run", fake_run)
        monkeypatch.setattr(cb.pathlib.Path, "write_bytes", lambda self, data: len(data))
        monkeypatch.setattr(cb.pathlib.Path, "exists", lambda self: True)
        monkeypatch.setattr(cb.pathlib.Path, "unlink", lambda self: None)
        monkeypatch.setattr(cb.tempfile, "mkstemp", lambda suffix=None: (3, "/tmp/test.png"))
        monkeypatch.setattr(cb.os, "close", lambda fd: None)

        success, error = cb.copy_image_to_clipboard(img)
        assert success is False
        assert "osascript error" in error if error else False

    def test_unsupported_platform(self, monkeypatch):
        """Test unsupported platform returns appropriate error."""
        import deepagents_code.clipboard as cb

        img = ImageData(
            base64_data=base64.b64encode(b"fake png data").decode(),
            format="png",
            placeholder="[img_001]",
        )

        monkeypatch.setattr(cb.sys, "platform", "freebsd")

        success, error = cb.copy_image_to_clipboard(img)
        assert success is False
        assert "only supported on macOS" in error if error else False

    def test_windows_returns_error(self, monkeypatch):
        """Test Windows returns not supported error."""
        import deepagents_code.clipboard as cb

        img = ImageData(
            base64_data=base64.b64encode(b"fake png data").decode(),
            format="png",
            placeholder="[img_001]",
        )

        monkeypatch.setattr(cb.sys, "platform", "win32")

        success, error = cb.copy_image_to_clipboard(img)
        assert success is False
        assert "only supported on macOS" in error if error else False

    def test_linux_returns_error(self, monkeypatch):
        """Test Linux returns not supported error."""
        import deepagents_code.clipboard as cb

        img = ImageData(
            base64_data=base64.b64encode(b"fake png data").decode(),
            format="png",
            placeholder="[img_001]",
        )

        monkeypatch.setattr(cb.sys, "platform", "linux")

        success, error = cb.copy_image_to_clipboard(img)
        assert success is False
        assert "only supported on macOS" in error if error else False

    def test_macos_osascript_not_found(self, monkeypatch):
        """Test case where osascript is not found on macOS."""
        import deepagents_code.clipboard as cb

        img = ImageData(
            base64_data=base64.b64encode(b"fake png data").decode(),
            format="png",
            placeholder="[img_001]",
        )

        monkeypatch.setattr(cb.sys, "platform", "darwin")
        monkeypatch.setattr(cb.shutil, "which", lambda x: None)

        success, error = cb.copy_image_to_clipboard(img)
        assert success is False
        assert "osascript not found" in error if error else False

    def test_macos_timeout(self, monkeypatch):
        """Test subprocess timeout on macOS."""
        import deepagents_code.clipboard as cb

        img = ImageData(
            base64_data=base64.b64encode(b"fake png data").decode(),
            format="png",
            placeholder="[img_001]",
        )

        monkeypatch.setattr(cb.sys, "platform", "darwin")
        monkeypatch.setattr(cb.shutil, "which", lambda x: "/usr/bin/osascript")

        def fake_timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="osascript", timeout=5)

        monkeypatch.setattr(cb.subprocess, "run", fake_timeout)
        monkeypatch.setattr(cb.pathlib.Path, "write_bytes", lambda self, data: len(data))
        monkeypatch.setattr(cb.pathlib.Path, "exists", lambda self: True)
        monkeypatch.setattr(cb.pathlib.Path, "unlink", lambda self: None)
        monkeypatch.setattr(cb.tempfile, "mkstemp", lambda suffix=None: (3, "/tmp/test.png"))
        monkeypatch.setattr(cb.os, "close", lambda fd: None)

        success, error = cb.copy_image_to_clipboard(img)
        assert success is False
        assert "Timeout" in error if error else False
