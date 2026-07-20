"""Version information and lightweight constants for `zjcode`."""

# Keep the `x-release-please-version` annotation — release-please uses it to
# bump `__version__` in sync with `pyproject.toml` on every release PR.
__version__ = "0.0.6"  # x-release-please-version

DISTRIBUTION_NAME = "zjcode"
"""Distribution (wheel/PyPI) name for this private-branded build.

Kept as a single constant so every place that would otherwise hard-code the
name (`uv tool install <name>`, `importlib.metadata.version(<name>)`, URL
paths on PyPI, extras-preserving upgrade commands) can import this one
string. Changing the brand is a one-line edit here; keeping the Python
package directory `deepagents_code/` unchanged minimizes upstream merge
conflicts.
"""

BRAND_NAME = "zjcode"
"""Short user-visible command name shown in CLI help, splash, and errors.

Currently equal to `DISTRIBUTION_NAME` but kept separate: if you ever want
to ship a distribution named `zjcode-code` while users still type `zjcode`,
these two diverge. Only user-facing strings should read `BRAND_NAME` — never
`uv tool` commands or metadata lookups.
"""

DOCS_URL = "https://docs.langchain.com/oss/python/deepagents/code"
"""URL for `deepagents-code` documentation (upstream — kept for now)."""

PYPI_URL = f"https://pypi.org/pypi/{DISTRIBUTION_NAME}/json"
"""PyPI JSON API endpoint for version checks."""

SDK_PYPI_URL = "https://pypi.org/pypi/deepagents/json"
"""PyPI JSON API endpoint for reading `deepagents` SDK release metadata.

The CLI only reads release-age metadata from this endpoint; it never
performs SDK update checks.
"""

CHANGELOG_URL = (
    "https://github.com/langchain-ai/deepagents/blob/main/libs/code/CHANGELOG.md"
)
"""URL for the full changelog."""

USER_AGENT = f"{DISTRIBUTION_NAME}/{__version__} update-check"
"""User-Agent header sent with PyPI requests."""
