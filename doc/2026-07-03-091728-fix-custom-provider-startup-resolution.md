# Fix Custom Provider Startup Resolution

- Time: 2026-07-03T09:17:28+08:00
- Project: deepagents

## Prompt

Error: Server failed to start: MissingCredentialsError: No credentials found for provider 'openai'. Please set the OPENAI_API_KEY environment variable.

Hint: run `/auth` to add a key for this provider, then `/model <provider>:<model>` to retry startup. Or pick a different provider directly with `/model`.

运行lib/code下的项目
我设置了自定义厂商, 并且配置文件中也有相关的配置,为什么没有生效. 帮我查找并解决

## AI Response

已定位并修复。原因是 `~/.deepagents/config.toml` 中 `[models].recent = "openai:gpt-5.5"` 优先于自定义厂商配置，启动时仍尝试使用 OpenAI；同时自定义厂商缺少 `api_key_env`，导致 `DEEPAGENTS_CODE_OPENAI_API_KEY` 不会传给 `langchain_openai:ChatOpenAI`。

处理内容：

1. 更新 `~/.deepagents/config.toml`：
   - 添加 `[models].default = "huoshan:ark-code-latest"`
   - 添加 `api_key_env = "OPENAI_API_KEY"`
2. 修复 `libs/code/deepagents_code/config.py`：
   - 支持 provider 级别 `default_model`
   - 跳过缺少凭据的 stale `recent` 模型
3. 修复 `libs/code/deepagents_code/model_config.py`：
   - 合并重复的 `save_custom_provider`
   - OpenAI-compatible 自定义 provider 默认写入 `api_key_env = "OPENAI_API_KEY"`
4. 增加 `libs/code/tests/unit_tests/test_model_config.py` 覆盖 provider 默认模型和 api_key_env 行为。

验证通过：

```bash
DEEPAGENTS_CODE_OPENAI_API_KEY=test-key uv --directory libs/code run python - <<'PY'
from deepagents_code.config import _get_default_model_spec, create_model
spec = _get_default_model_spec()
print(spec)
result = create_model(spec)
print(result.provider, result.model_name)
PY
```

输出：

```text
huoshan:ark-code-latest
huoshan ark-code-latest
```

也通过了针对性测试和改动文件 lint/typecheck：

```bash
uv --directory libs/code run --group test pytest tests/unit_tests/test_model_config.py -q -k "provider_default or save_custom_provider_defaults_openai_key_env or recent_takes_priority or default_takes_priority"
make lint PYTHON_FILES="deepagents_code/config.py deepagents_code/model_config.py tests/unit_tests/test_model_config.py"
```

注意：完整 `make lint` 仍会因为此前 `widgets/model_selector.py`/`test_model_selector.py` 中既有自定义 provider UI 代码存在大量 lint 问题而失败，本次修复范围未展开处理这些 UI 代码。