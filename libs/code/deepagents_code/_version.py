"""Version information and lightweight constants for `deepagents-code`."""

# Keep the `x-release-please-version` annotation — release-please uses it to
# bump `__version__` in sync with `pyproject.toml` on every release PR.
__version__ = "0.0.17"  # x-release-please-version

DISTRIBUTION_NAME = "deepagents-code"
"""PyPI distribution name (also the on-disk editable project name).

Hardcoded to the upstream project name on `main` so `pkg_version(...)` and
`distribution(...)` resolve to the installed package. A future zjcode
rebrand touches this constant (and the matching string in `pyproject.toml`),
nothing else.
"""

BRAND_NAME = "deepagents-code"
"""User-facing brand name (CLI invocations, splash text, error messages).

Separate from `DISTRIBUTION_NAME` so a brand-only rename (e.g. an alias
wheel) does not require touching every place the package name is queried.
"""

DOCS_URL = "https://docs.langchain.com/oss/python/deepagents/code"
"""URL for `deepagents-code` documentation."""

PYPI_URL = "https://pypi.org/pypi/deepagents-code/json"
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

USER_AGENT = f"deepagents-code/{__version__} update-check"
"""User-Agent header sent with PyPI requests."""
