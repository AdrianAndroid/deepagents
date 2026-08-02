# Skill 测试指南

## 快速测试

🎉 已创建测试 Skill: `hello-skill`

## 测试步骤

### 1. 启动 zjcode

```bash
cd /Users/zhaojian/code/deepagents
zjcode
```

### 2. 测试输入词

**方式一：直接触发**
```
使用 hello-skill
```

**方式二：间接触发（推荐，能看到完整流程**
```
测试 hello-skill 看看技能系统，看看技能系统
```

**方式三：查询可用技能**
```
列出可用的技能列表
```

### 3. 预期行为

1.  ✅ Agent 应该会调用 `read_file` 读取 SKILL.md
2.  ✅ 然后按照 SKILL.md 中的指令回复你
3.  ✅ 显示欢迎消息，确认技能系统正常工作

---

## 如何手动验证 Skill 加载

### 查看 Skill 是否被发现

```bash
# 列出所有技能
zjcode skills list

# 查看具体技能
zjcode skills show hello-skill
```

### 手动读取 Skill 内容

```bash
cat /Users/zhaojian/code/deepagents/.zjcode/skills/hello-skill/SKILL.md
```

---

## Skill 工作原理图解

```
┌─────────────────────────────────────────────────────┐
│  系统提示 (System Prompt)                          │
│  ───────────────────────────────────────────────  │
│  ## Skills System                                   │
│  **Project Skills**: `.zjcode/skills/`              │
│  - **hello-skill**: A simple hello world skill...  │
│    -> Read `.zjcode/skills/hello-skill/SKILL.md`     │
└─────────────────────────────────────────────────────┘
                           ↓
                  Agent 判断需要使用 skill
                           ↓
┌─────────────────────────────────────────────────────┐
│  Tool Call: read_file                               │
│  file_path: /path/hello-skill/SKILL.md            │
└─────────────────────────────────────────────────────┘
                           ↓
              Agent 获得完整 SKILL.md 内容
                           ↓
              Agent 按照指令完成任务 🎉
```

---

## 调试技巧

### 1. 查看 Skill 是否被正确加载

在 zjcode 中输入：
```
/show tools
```
或
```
/skills
```

### 2. 手动强制读取 Skill

```
read_file(file_path="/Users/zhaojian/code/deepagents/.zjcode/skills/hello-skill/SKILL.md", limit=1000)
```

### 3. 创建自定义测试用例

| 测试场景 | 输入提示 |
|---------|---------|
| 基本触发 | "使用 hello skill" |
| 模糊匹配 | "测试一下技能系统" |
| 手动调用 | 直接用 read_file 读取 SKILL.md |
| 多轮对话 | "先列出所有技能，然后用 hello skill" |

---

## Skill 目录位置

| 层级 | 路径 | 优先级 |
|------|------|--------|
| 项目技能 (本测试 Skill 位置 | `.zjcode/skills/ | 高 |
| 用户技能 | `~/.zjcode/agent/skills/ | 中 |
| 内置技能 | `<package>/built_in_skills/ | 低 |

> **注意**：项目技能会覆盖同名的用户技能和内置技能

---

## 下一步：创建自己的 Skill

1. 复制 hello-skill 目录
2. 修改 frontmatter 的 name 和 description
3. 编写你的技能指令文档
4. 重启 zjcode 测试

```bash
# 示例：创建新技能
cp -r .zjcode/skills/hello-skill .zjcode/skills/my-awesome-skill
# 编辑 SKILL.md
```
