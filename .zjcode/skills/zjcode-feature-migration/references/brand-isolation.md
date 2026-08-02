# Brand Isolation Guide

## Overview

zjcode is a fork of deepagents-code with custom branding. All user-facing references must use zjcode branding while preserving upstream compatibility.

## Brand Mapping

| Upstream (deepagents-code) | Custom (zjcode) |
|---------------------------|-----------------|
| `deepagents-code` | `zjcode` |
| `Deep Agents` | `zjcode` |
| `DeepAgents` | `zjcode` |
| `~/.deepagents` | `~/.zjcode` |
| `.deepagents/` | `.zjcode/` |
| `deepagents_code` (package) | Keep as-is (import path) |

## Files Requiring Updates

### 1. pyproject.toml

```toml
# Before
name = "deepagents-code"
description = "Terminal coding agent built on the Deep Agents SDK"

[project.scripts]
deepagents-code = "deepagents_code:cli_main"

# After
name = "zjcode"
description = "Terminal coding agent built on the zjcode SDK"

[project.scripts]
zjcode = "deepagents_code:cli_main"
```

### 2. config.py

```python
# Before
CODING_AGENT_INTEGRATION = "deepagents-code"
CODING_AGENT_RUNTIME = "Deep Agents Code"
_GLOBAL_DOTENV_PATH = Path.home() / ".deepagents" / ".env"

# After
CODING_AGENT_INTEGRATION = "zjcode"
CODING_AGENT_RUNTIME = "zjcode"
_GLOBAL_DOTENV_PATH = Path.home() / ".zjcode" / ".env"
```

### 3. model_config.py

```python
# Before
DEFAULT_CONFIG_DIR = Path.home() / ".deepagents"
"""Path to the user's model configuration file (`~/.deepagents/config.toml`)."""

# After
DEFAULT_CONFIG_DIR = Path.home() / ".zjcode"
"""Path to the user's model configuration file (`~/.zjcode/config.toml`)."""
```

### 4. update_check.py

```python
# Before
FALLBACK_UPGRADE_COMMAND = "uv tool install -U deepagents-code"
"""Fetch the latest deepagents-code version from PyPI"""

# After
FALLBACK_UPGRADE_COMMAND = "uv tool install -U zjcode"
"""Fetch the latest zjcode version from PyPI"""
```

### 5. app.py

```python
# Before
"Reinstalling Deep Agents Code should restore cost estimates"
"`uv tool upgrade deepagents-code`"

# After
"Reinstalling zjcode should restore cost estimates"
"`uv tool upgrade zjcode`"
```

### 6. UI Strings

```python
# Before
"Deep Agents requires tool calling for agent functionality."
"Check permissions for ~/.deepagents/"

# After
"zjcode requires tool calling for agent functionality."
"Check permissions for ~/.zjcode/"
```

## What NOT to Change

### Package Import Paths

Keep `deepagents_code` as the Python package name:

```python
# Correct - keep as-is
from deepagents_code.config import CONFIG_DOTDIR
import deepagents_code.agent

# Wrong - don't change
from zjcode.config import CONFIG_DOTDIR  # ❌
```

### Internal Identifiers

Keep internal identifiers that reference upstream SDK:

```python
# Correct - internal SDK reference
settings.deepagents_langchain_project
lc_versions.deepagents

# Wrong - don't change
settings.zjcode_langchain_project  # ❌
```

### Test Files

Don't change test file references:

```python
# Correct - keep test paths
tests/unit_tests/test_config.py
tests/integration_tests/

# Wrong - don't change
tests/unit_tests/test_zjcode_config.py  # ❌
```

## Verification Commands

### Check for Remaining References

```bash
# Should return 0 or only internal identifiers
grep -r "deepagents-code\|DeepAgents\|Deep Agents\|\.deepagents" \
  libs/code/ --include="*.py" --include="*.md" --include="*.toml" \
  | grep -v "test_\|tests/\|CHANGELOG\|uv\.lock\|\.venv\|upstream\|original" \
  | grep -v "deepagents_langchain\|lc_versions\.deepagents"
```

### Check Path Constants

```bash
# Should all show .zjcode
grep -r "Path.home() / \"\.deepagents\"" libs/code/ --include="*.py"
grep -r "project_root / \"\.deepagents\"" libs/code/ --include="*.py"
```

### Check Distribution Names

```bash
# Should all show zjcode
grep -r "distribution(\"deepagents-code\")" libs/code/ --include="*.py"
grep -r "pkg_version(\"deepagents-code\")" libs/code/ --include="*.py"
```

## Common Mistakes

### 1. Changing Package Import Paths

```python
# Wrong
from zjcode.config import CONFIG_DOTDIR  # ❌ Package is still deepagents_code

# Correct
from deepagents_code.config import CONFIG_DOTDIR  # ✓
```

### 2. Missing Docstring Updates

```python
# Wrong - docstring still mentions old brand
def get_config():
    """Load config from ~/.deepagents/config.toml"""  # ❌
    return load_config()

# Correct
def get_config():
    """Load config from ~/.zjcode/config.toml"""  # ✓
    return load_config()
```

### 3. Inconsistent Error Messages

```python
# Wrong - mixed branding
raise ValueError("Deep Agents configuration error in ~/.zjcode/")  # ❌

# Correct - consistent branding
raise ValueError("zjcode configuration error in ~/.zjcode/")  # ✓
```

## Testing Brand Isolation

### 1. CLI Help Text

```bash
cd libs/code
uv run python -m deepagents_code.main --help
# Should show "zjcode" not "deepagents-code"
```

### 2. Config Directory Creation

```bash
# Remove existing config
rm -rf ~/.zjcode

# Run zjcode
uv run python -m deepagents_code.main

# Verify directory created
ls -la ~/.zjcode
# Should exist with correct structure
```

### 3. Error Messages

Trigger an error and verify branding:

```bash
# Example: invalid config
echo "invalid" > ~/.zjcode/config.toml
uv run python -m deepagents_code.main
# Error message should mention "zjcode" not "Deep Agents"
```
