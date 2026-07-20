#!/bin/bash
# Build and publish zjcode to public PyPI.
#
# Requirements:
#   - `uv` installed (https://docs.astral.sh/uv/)
#   - Publish credentials for pypi.org, provided via either:
#       * env var `UV_PUBLISH_TOKEN=<pypi-api-token>`, or
#       * `~/.pypirc` with a `[pypi]` section
#
# For a dry run against Test PyPI:
#   UV_PUBLISH_TOKEN=<test-token> ./run-publish.sh --publish-url https://test.pypi.org/legacy/

set -euo pipefail
cd "$(dirname "$0")"

rm -rf dist/
uv build
uv publish "$@"
