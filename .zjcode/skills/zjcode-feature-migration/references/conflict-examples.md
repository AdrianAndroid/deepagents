# Conflict Resolution Examples

## Example 1: Import Conflicts

### Scenario
Upstream added new imports, custom branch also added imports in same location.

### Conflict
```python
<<<<<<< HEAD
from deepagents_code.new_upstream_feature import NewFeature
from deepagents_code.another_module import AnotherModule
=======
from deepagents_code.clipboard import ClipboardManager
from deepagents_code.custom_provider import CustomProviderModal
>>>>>>> migrate-zjcode-features
```

### Resolution
```python
# Keep both - order by category
from deepagents_code.new_upstream_feature import NewFeature
from deepagents_code.another_module import AnotherModule
from deepagents_code.clipboard import ClipboardManager
from deepagents_code.custom_provider import CustomProviderModal
```

## Example 2: Function Signature Changes

### Scenario
Upstream changed function signature, custom branch added optional parameter.

### Conflict
```python
<<<<<<< HEAD
def load_config(config_path: Path, validate: bool = True) -> Config:
    """Load and validate configuration."""
    raw = read_config(config_path)
    if validate:
        return validate_config(raw)
    return raw
=======
def load_config(config_path: Path, use_cache: bool = False) -> Config:
    """Load configuration with optional caching."""
    if use_cache:
        return get_cached_config(config_path)
    return read_config(config_path)
>>>>>>> migrate-zjcode-features
```

### Resolution
```python
# Merge both parameters, combine logic
def load_config(
    config_path: Path, 
    validate: bool = True,
    use_cache: bool = False
) -> Config:
    """Load and validate configuration with optional caching."""
    if use_cache:
        raw = get_cached_config(config_path)
    else:
        raw = read_config(config_path)
    
    if validate:
        return validate_config(raw)
    return raw
```

## Example 3: Path Constant Conflicts

### Scenario
Both branches modified path constants.

### Conflict
```python
<<<<<<< HEAD
CONFIG_DIR = Path.home() / ".deepagents" / "config"
STATE_DIR = Path.home() / ".deepagents" / "state"
NEW_DIR = Path.home() / ".deepagents" / "new_feature"
=======
CONFIG_DIR = Path.home() / ".zjcode" / "config"
STATE_DIR = Path.home() / ".zjcode" / "state"
>>>>>>> migrate-zjcode-features
```

### Resolution
```python
# Always use .zjcode, keep all directories
CONFIG_DIR = Path.home() / ".zjcode" / "config"
STATE_DIR = Path.home() / ".zjcode" / "state"
NEW_DIR = Path.home() / ".zjcode" / "new_feature"
```

## Example 4: Class Method Conflicts

### Scenario
Upstream refactored method, custom branch added feature to same method.

### Conflict
```python
<<<<<<< HEAD
class ConfigManager:
    def load(self) -> Config:
        """Load configuration with new validation."""
        self._validate_environment()
        raw = self._read_file()
        return self._parse_config(raw)
=======
class ConfigManager:
    def load(self) -> Config:
        """Load configuration with custom defaults."""
        raw = self._read_file()
        if not raw:
            raw = self._load_defaults()
        return self._parse_config(raw)
>>>>>>> migrate-zjcode-features
```

### Resolution
```python
class ConfigManager:
    def load(self) -> Config:
        """Load configuration with validation and custom defaults."""
        self._validate_environment()
        raw = self._read_file()
        if not raw:
            raw = self._load_defaults()
        return self._parse_config(raw)
```

## Example 5: Dependency Version Conflicts

### Scenario
Both branches updated same dependency to different versions.

### Conflict (pyproject.toml)
```toml
<<<<<<< HEAD
dependencies = [
    "textual>=8.2.8,<9.0.0",
    "langchain>=1.3.15,<2.0.0",
]
=======
dependencies = [
    "textual>=8.2.5,<9.0.0",
    "langchain>=1.3.14,<2.0.0",
]
>>>>>>> migrate-zjcode-features
```

### Resolution
```toml
# Always prefer upstream (main) versions
dependencies = [
    "textual>=8.2.8,<9.0.0",
    "langchain>=1.3.15,<2.0.0",
]
```

## Example 6: Test Snapshot Conflicts

### Scenario
Upstream changed output format, custom branch modified same output.

### Conflict
```markdown
<<<<<<< HEAD
## Tool Calls
- `read_file`: `/path/to/file`
- `execute`: `ls -la`
=======
## 工具调用
- `read_file`: `/path/to/file`
- `execute`: `ls -la`
- `clipboard`: `paste_image`
>>>>>>> migrate-zjcode-features
```

### Resolution
```markdown
## Tool Calls
- `read_file`: `/path/to/file`
- `execute`: `ls -la`
- `clipboard`: `paste_image`
```

Note: Keep English headers for consistency with upstream, but include custom tools.

## Example 7: Configuration Default Conflicts

### Scenario
Both branches changed same default value.

### Conflict
```python
<<<<<<< HEAD
DEFAULT_TIMEOUT = 30  # Increased from 10
MAX_RETRIES = 5  # Increased from 3
=======
DEFAULT_TIMEOUT = 60  # Custom value
MAX_RETRIES = 3  # Keep original
>>>>>>> migrate-zjcode-features
```

### Resolution
```python
# Evaluate each change, prefer custom if justified
DEFAULT_TIMEOUT = 60  # Custom value for slower networks
MAX_RETRIES = 5  # Upstream improvement
```

## Example 8: UI String Conflicts

### Scenario
Upstream improved error message, custom branch changed branding.

### Conflict
```python
<<<<<<< HEAD
raise ValueError("Deep Agents configuration is invalid. Check ~/.deepagents/config.toml")
=======
raise ValueError("zjcode configuration is invalid. Check ~/.zjcode/config.toml")
>>>>>>> migrate-zjcode-features
```

### Resolution
```python
# Apply both: custom branding + upstream improvements
raise ValueError("zjcode configuration is invalid. Check ~/.zjcode/config.toml")
```

## Example 9: Import Path Conflicts in Tests

### Scenario
Test file imports changed in both branches.

### Conflict
```python
<<<<<<< HEAD
from deepagents_code.new_test_utils import MockConfig
from deepagents_code.config import ConfigManager
=======
from deepagents_code.custom_test_helpers import CustomMock
from deepagents_code.config import ConfigManager
>>>>>>> migrate-zjcode-features
```

### Resolution
```python
# Keep both test utilities
from deepagents_code.new_test_utils import MockConfig
from deepagents_code.custom_test_helpers import CustomMock
from deepagents_code.config import ConfigManager
```

## Example 10: Documentation Conflicts

### Scenario
Both branches updated same documentation section.

### Conflict
```markdown
<<<<<<< HEAD
## Installation

Install via pip:
```bash
pip install deepagents-code
```
=======
## Installation

Install via uv:
```bash
uv tool install zjcode
```
>>>>>>> migrate-zjcode-features
```

### Resolution
```markdown
## Installation

Install via uv (recommended):
```bash
uv tool install zjcode
```

Or via pip:
```bash
pip install zjcode
```
```

## General Principles

1. **Preserve upstream improvements**: Don't lose bug fixes or performance improvements
2. **Maintain custom branding**: Always use zjcode for user-facing strings
3. **Keep custom features**: Preserve clipboard, model selector, etc.
4. **Test after resolution**: Always run tests after resolving conflicts
5. **Document decisions**: Note why you chose one version over another

## Common Patterns

### Pattern 1: Additive Changes
When both branches add different things, keep both:
```python
# Upstream added A, custom added B
# Result: Keep A and B
```

### Pattern 2: Overlapping Changes
When both branches modify same thing differently:
```python
# Upstream: X → Y
# Custom: X → Z
# Result: Evaluate Y vs Z, choose best or merge
```

### Pattern 3: Conflicting Changes
When changes are incompatible:
```python
# Upstream: Refactored function
# Custom: Added feature to old function
# Result: Add feature to new refactored function
```
