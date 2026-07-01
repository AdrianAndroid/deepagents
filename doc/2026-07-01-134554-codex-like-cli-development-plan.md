# Codex Like CLI Development Plan

- Time: 2026-07-01T13:45:54+08:00
- Project: deepagents

## Prompt

帮我列一个开发计划

## AI Response

## 开发计划

### 阶段 1：现有能力调研

目标：确认 Deep Agents 已提供哪些能力，避免重复造轮子。

任务：
- 阅读 `libs/code/deepagents_code/main.py`
- 阅读 `libs/code/deepagents_code/agent.py`
- 阅读 `libs/code/deepagents_code/app.py`
- 阅读 `libs/code/deepagents_code/command_registry.py`
- 梳理 CLI、TUI、Agent、权限、会话、MCP、skills 的现有实现

产出：
- 架构分析文档
- 可复用模块清单
- 需要重写或扩展的模块清单

---

### 阶段 2：定义 MVP

目标：先做一个可用的最小版本。

MVP 功能：
- `mycode "任务描述"` 一次性执行任务
- 读取当前项目上下文
- 调用 Deep Agents coding agent
- 支持文件读取、文件修改、命令执行
- 输出执行摘要
- 输出修改过的文件列表
- 不自动 commit、不自动 push

验收标准：
- 可以在真实 Python/JS 项目中完成简单代码修改
- 可以运行测试或 lint 命令
- 失败时能把错误反馈给 agent 继续修复

---

### 阶段 3：CLI 包结构

建议新建独立包：

```txt
libs/mycode/
├── pyproject.toml
├── mycode/
│   ├── __init__.py
│   ├── main.py
│   ├── agent.py
│   ├── config.py
│   ├── context.py
│   ├── permissions.py
│   ├── commands.py
│   ├── session.py
│   └── system_prompt.md
└── tests/
```

模块职责：
- `main.py`：CLI 入口
- `agent.py`：创建 Deep Agents coding agent
- `config.py`：模型、权限、项目配置
- `context.py`：读取项目上下文
- `permissions.py`：shell 和文件权限控制
- `commands.py`：slash commands
- `session.py`：会话保存和恢复
- `system_prompt.md`：coding agent 行为规范

---

### 阶段 4：Agent 核心实现

目标：基于 `create_deep_agent()` 封装自己的 coding agent。

任务：
- 配置模型选择
- 加载系统提示词
- 注入项目上下文
- 启用文件工具
- 启用 shell 执行工具
- 启用 todo 工具
- 启用子 agent
- 接入权限策略

验收标准：
- agent 能理解项目规则
- agent 能规划任务
- agent 能修改文件
- agent 能执行验证命令

---

### 阶段 5：项目上下文系统

目标：让工具进入项目后自动理解项目。

需要读取：
- `AGENTS.md`
- `README.md`
- `pyproject.toml`
- `package.json`
- `Cargo.toml`
- `go.mod`
- `.gitignore`
- 常见测试配置

能力：
- 自动识别语言和框架
- 自动识别测试命令
- 自动识别 lint/typecheck 命令
- 将项目规则注入 prompt

---

### 阶段 6：权限与安全

目标：达到接近 Codex/Claude Code 的安全体验。

权限等级：
- `read-only`：只能读文件和分析
- `workspace-write`：可修改当前工作区
- `danger-full-access`：可执行高风险操作

必须确认的操作：
- 删除文件
- 工作区外写入
- `git push`
- `git reset --hard`
- `rm -rf`
- `sudo`
- 安装依赖
- 执行远程脚本

验收标准：
- 默认不能破坏用户仓库
- 危险命令必须用户确认
- 不会自动提交或推送代码

---

### 阶段 7：交互模式

目标：支持类似 Codex 的连续对话。

命令：
- `mycode` 进入交互模式
- `/help`
- `/model`
- `/diff`
- `/status`
- `/resume`
- `/clear`
- `/exit`

验收标准：
- 支持多轮任务
- 支持会话恢复
- 支持查看 diff
- 支持切换模型

---

### 阶段 8：测试与质量保障

测试范围：
- CLI 参数解析
- 配置加载
- 项目上下文读取
- 权限判断
- slash commands
- session 保存恢复
- agent 创建逻辑

验证命令：
- `make lint`
- `make test`
- 包级别 `uv run pytest`

验收标准：
- 新功能有单元测试
- lint 通过
- typecheck 通过
- 不引入网络依赖测试

---

### 阶段 9：AI 协作分工

可以用多个 AI agent 并行开发：

1. 架构分析 agent
   - 分析 `libs/code`
   - 输出复用方案

2. CLI MVP agent
   - 创建包结构
   - 实现入口命令

3. Agent 核心 agent
   - 封装 `create_deep_agent()`
   - 接入 prompt 和上下文

4. 权限 agent
   - 实现命令风险识别
   - 实现文件边界检查

5. 交互 agent
   - 实现 slash commands
   - 实现 session 管理

6. 测试 agent
   - 补测试
   - 跑 lint/typecheck/test

---

### 推荐里程碑

| 里程碑 | 目标 | 时间 |
|---|---|---|
| M1 | 完成架构调研 | 1-2 天 |
| M2 | 完成非交互 CLI MVP | 3-5 天 |
| M3 | 接入权限系统 | 2-3 天 |
| M4 | 支持交互模式和 slash commands | 3-5 天 |
| M5 | 支持会话恢复、模型配置、项目上下文 | 3-5 天 |
| M6 | 完善测试、文档、发布流程 | 2-4 天 |

最终目标：先做一个稳定的非 TUI CLI，再逐步演进成交互式 coding agent。
