# Skill 系统深度分析

## 一、Skill 系统概述

Skill 系统是 Deep Agents 中的一个模块化扩展机制，允许用户通过定义结构化的技能文件来扩展 agent 的专业能力。系统采用 **渐进式披露（Progressive Disclosure）** 模式：agent 首先看到技能的元数据（名称和描述），只有在需要时才读取完整的指令内容。

## 二、Skill 目录结构

每个 skill 是一个独立的目录，必须包含 `SKILL.md` 文件：

```
skill-name/
├── SKILL.md          # 必填：YAML frontmatter + markdown 指令
└── helper.py         # 可选：辅助脚本或配置文件
```

### SKILL.md 文件格式

```markdown
---
name: skill-name                    # 必填：技能名称
description: 技能描述                # 必填：技能功能描述
license: MIT                        # 可选：许可证
compatibility: Python 3.10+         # 可选：兼容性说明
allowed-tools: tool1 tool2            # 可选：推荐使用的工具
metadata:                         # 可选：自定义元数据
  key: value
---

# Skill 完整指令

## 使用场景
- 何时使用该技能

## 工作流程
1. 步骤一
2. 步骤二
...
```

## 三、Skill 加载流程

### 3.1 加载优先级（从低到高）

| 优先级 | 目录路径 | 说明 |
|--------|----------|------|
| 1 (最低) | `<package>/built_in_skills/` | 内置技能 |
| 2 | `~/.deepagents/{agent}/skills/` | 用户级 Deepagents 技能 |
| 3 | `~/.agents/skills/` | 用户级共享技能 |
| 4 | `.deepagents/skills/` | 项目级 Deepagents 技能 |
| 5 | `.agents/skills/` | 项目级共享技能 |
| 6 | `~/.claude/skills/` | Claude 兼容技能（实验性） |
| 7 (最高) | `.claude/skills/` | 项目级 Claude 技能（实验性） |

**同名覆盖规则**：后面高优先级目录中的技能会覆盖前面低优先级目录中的同名技能。

### 3.2 完整加载流程

```
Agent 启动
    ↓
SkillsMiddleware.before_agent() 执行
    ↓
检查 state 中是否已有 skills_metadata
    ├─ 已有 → 跳过加载（缓存机制）
    └─ 没有 → 继续加载
        ↓
遍历所有 skill source 目录
    ↓
使用 Backend.ls() 扫描子目录
    ↓
检查每个子目录是否包含 SKILL.md
    ↓
Backend.download_files() 批量下载 SKILL.md
    ↓
解析 YAML frontmatter
    ↓
验证技能名称格式
    ↓
合并所有技能（后加载的覆盖先加载的）
    ↓
将 skills_metadata 存入 agent state
    ↓
modify_request() 注入系统提示
```

### 3.3 关键加载函数

**`SkillsMiddleware` 类的核心方法：

- `before_agent()` / `abefore_agent()` - 同步/异步加载技能元数据，只在首次执行一次
- `modify_request()` - 将技能列表注入系统提示
- `_list_skills_with_errors()` - 扫描并解析单个 source 目录
- `_parse_skill_metadata()` - 解析 SKILL.md 的 YAML frontmatter

## 四、Skill 验证规则

### 4.1 名称验证规则

- 长度：1-64 字符
- 字符：小写字母、数字、连字符（-）
- 不能以连字符开头或结尾
- 不能包含连续连字符
- 必须与父目录名称一致

### 4.2 描述验证规则

- 必填字段：name 和 description 不能为空
- 描述长度：最大 1024 字符（超出部分截断）
- compatibility 字段：最大 500 字符

## 五、Skill 使用方式（渐进式披露）

### 5.1 系统提示中的技能展示

系统提示中只展示技能的元数据：

```
**Available Skills:**

- **remember**: Review the current conversation and capture valuable knowledge
  -> Read `/path/to/remember/SKILL.md` for full instructions
- **skill-creator**: Guide for creating effective skills
  -> Read `/path/to/skill-creator/SKILL.md` for full instructions
```

### 5.2 完整使用流程

1. **识别适用场景**：检查用户请求是否匹配某个技能的描述

2. **读取完整指令**：
   ```python
   read_file(file_path="/path/to/skill/SKILL.md", limit=1000)
   ```

3. **遵循技能指令**：按照 SKILL.md 中的步骤执行任务

4. **访问辅助文件**：使用绝对路径访问 skill 目录中的脚本

### 5.3 Skill 调用信封（Invocation Envelope）

当 agent 决定使用某个 skill 时，会构建一个调用信封：

```python
{
  "prompt": "I'm invoking the skill `skill-name`. Below are the full instructions...",
  "message_kwargs": {
    "additional_kwargs": {
      "__skill": {
        "name": "skill-name",
        "description": "...",
        "source": "built-in",
        "args": "用户参数"
      }
    }
  }
}
```

## 六、Skill 源配置

### 6.1 源类型

Skill 源可以是字符串路径或 `(路径, 标签)` 元组：

```python
sources = [
    "/path/to/skills/user/",           # 自动推导标签
    ("/home/me/.claude/skills", "User Claude"),  # 显式指定标签
]
```

### 6.2 标签推导规则

- 内置技能目录名：`built_in_skills` → `Built-in`
- Claude 技能：`~/.claude/skills` → `Claude`
- 普通目录：`/skills/user/` → `User`

## 七、CLI 命令

### 7.1 列出技能列表

```bash
# 列出所有技能
dcode skills list

# 只显示项目级技能
dcode skills list --project

# JSON 格式输出
dcode skills list --json
```

### 7.2 创建新技能

```bash
# 创建用户级技能
dcode skills create my-new-skill

# 创建项目级技能
dcode skills create my-new-skill --project
```

### 7.3 查看技能详情

```bash
dcode skills info skill-name
```

### 7.4 删除技能

```bash
dcode skills delete skill-name
```

## 八、安全机制

### 8.1 路径安全检查

- 技能路径必须在允许的根目录内
- 防止符号链接穿越（symlink traversal）攻击
- 额外允许目录可通过配置添加

### 8.2 文件大小限制

- SKILL.md 最大 10MB
- 防止 DoS 攻击

### 8.3 错误处理

- 单个 skill 加载失败不影响其他技能
- 加载错误记录到日志和系统提示（HTML 转义）
- 最多显示 20 条警告

## 九、与 Agent 集成

### 9.1 Middleware 注册

在 `agent.py` 中注册 SkillsMiddleware：

```python
SkillsMiddleware(
    backend=FilesystemBackend(virtual_mode=False),
    sources=sources,
)
```

### 9.2 State 存储

技能元数据存储在 agent state 中：

```python
state = {
    "skills_metadata": [SkillMetadata, ...],
    "skills_load_errors": ["error1", "error2", ...],
}
```

### 9.3 系统提示注入

技能列表通过 `modify_request()` 注入系统提示，包含：
- 技能源位置
- 加载警告（如有）
- 可用技能列表
- 使用说明

## 十、关键代码模块结构

```
deepagents/
├── middleware/
│   └── skills.py              # SkillsMiddleware 核心实现
│       ├── SkillMetadata         # 技能元数据类型
│       ├── SkillsState         # 技能状态定义
│       ├── SkillsMiddleware  # 技能中间件
│       └── _parse_skill_metadata()  # 解析函数
│
deepagents_code/
├── skills/
│   ├── commands.py            # CLI 命令实现
│   ├── load.py                # 技能加载器（CLI 使用）
│   ├── invocation.py        # 技能调用信封构建
│   └── trust.py             # 技能信任管理
│
└── built_in_skills/          # 内置技能目录
    ├── remember/
    └── skill-creator/
```

## 十一、最佳实践

1. **技能粒度**：每个技能专注于特定领域，保持单一职责

2. **描述清晰**：description 字段要包含触发关键词，帮助 agent 识别使用场景

3. **指令具体**：SKILL.md 要包含明确的步骤、工具使用示例

4. **版本管理**：利用 metadata 字段记录版本信息

5. **兼容性声明**：明确指定依赖的环境和工具

6. **测试验证**：创建后通过 `dcode skills info` 验证格式正确

## 十二、常见问题

### Q: 为什么我的技能没有出现在列表中？
A: 检查以下几点：
- SKILL.md 是否存在于正确的目录
- YAML frontmatter 格式是否正确
- name 字段是否与目录名一致
- 检查日志中的加载错误

### Q: 如何调试技能加载问题？
A: 
1. 查看 agent 日志中的警告信息
2. 使用 `dcode skills info` 验证技能
3. 检查 `skills_load_errors` state 字段

### Q: 技能可以访问哪些工具？
A: 技能可以使用 agent 所有可用工具，`allowed-tools` 只是推荐，不是强制限制。
