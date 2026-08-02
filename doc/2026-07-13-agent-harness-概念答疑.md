# Agent Harness 概念答疑

本文记录关于 "Agent Harness" 相关的多轮问答内容，帮助理解 harness 与 agent、LLM 之间的关系。

## 轮次 1 - 什么是 Agent Harness

**用户提问**：什么是 Agent Harness？

**结论**：
Agent Harness 是围绕 LLM 构建智能体时所需的"外围机制层"。它是让一个只会预测下一个 token 的大模型，变成"能感知、能行动、能循环工作"的智能体所需要的一整套骨架代码。

在本仓库中，Deep Agents 就是一个 opinionated 的 harness，构建在 LangChain（agent 抽象）+ LangGraph（runtime）之上。

## 轮次 2 - Agent Harness 就是除了大模型之外的东西吗？

**用户提问**：Agent Harness 就是除了大模型之外的东西吗？

**结论**：大致可以这么理解，但更准确的说法是——**harness 特指驱动 agent loop 运转的那层结构**，不是所有非模型代码。

### Harness 包含

- **Agent loop**：模型 → 工具调用 → 观察结果 → 再调模型的循环
- **系统提示词组装**：拼 system prompt、注入上下文
- **工具注册与调度**：暴露函数给模型，解析 tool_call，执行，回传结果
- **上下文/状态管理**：消息历史、checkpoint、压缩、记忆
- **中间件**：权限校验、HITL 审批、日志、限流、总结
- **子智能体调度**：subagent 分发、并发、结果汇总
- **后端能力**：文件系统、沙箱执行、网络访问的接入层

### Harness 不包含

- **模型权重和推理本身**（属于 LLM provider）
- **纯业务逻辑**（除非被封装成工具挂进 harness）

### 本仓库对照

- LangChain：agent 抽象（模型 + 工具 + 中间件 → loop）
- LangGraph：runtime（状态、流式、checkpoint、interrupt）
- Deep Agents：在两者之上的 opinionated harness（预设默认中间件、backend、profile、subagent 机制）

**一句话**：模型是"大脑"，harness 是"身体 + 神经系统 + 工作流程"。

## 轮次 3 - Agent 和 Agent Harness 有啥区别？

**用户提问**：Agent 和 Agent Harness 有啥区别？

### 一句话区分

- **Agent** = 跑起来的**产品/实例**（大脑 + 身体，能对外干活的那个东西）
- **Agent Harness** = 造出 agent 的**框架/骨架**（只有身体，没装大脑之前的那套机制）

### 类比

| 类比 | Harness | Agent |
| --- | --- | --- |
| 汽车 | 底盘 + 传动 + 电控（没发动机） | 装上发动机的整车 |
| 人 | 身体 + 神经系统 | 有意识、能行动的活人 |
| Web | Django/FastAPI 框架 | 用框架写出来的具体网站 |

### 组成关系

```
Agent = Harness + Model + (Tools + Prompt + Config)
```

- **Harness 提供**：agent loop、工具调度、中间件、状态管理、子智能体机制……
- **你提供**：选哪个模型、挂什么工具、写什么 prompt、设什么权限
- **组装出来的**：一个具体的 Agent

### 本仓库示例

```python
from deepagents import create_deep_agent

# create_deep_agent 是 harness 提供的组装函数
agent = create_deep_agent(
    model="anthropic:claude-sonnet-4",   # 大脑
    tools=[search, write_file],           # 能力
    system_prompt="你是研究助手",           # 人格
)

# agent 是可运行实例；create_deep_agent + 中间件栈 + backend + subagent 机制 是 harness
result = agent.invoke({"messages": [...]})
```

### 关键差异对比表

| 维度 | Harness | Agent |
| --- | --- | --- |
| 形态 | 代码库 / 框架 | 运行时实例 |
| 是否绑定模型 | 否（模型无关） | 是（已绑定具体 LLM） |
| 是否面向具体任务 | 通用 | 通常面向特定用途 |
| 可复用性 | 高（可造无数 agent） | 单个实例 |
| 举例 | Deep Agents、LangChain `create_agent`、AutoGPT 框架 | `deepagents-code`（dcode）、具体的研究助手 |

### 常见误区

- ❌ "Agent 就是 LLM" —— 光有模型没有 loop/工具，不算 agent
- ❌ "Harness 和 Agent 是一回事" —— harness 是造 agent 的东西
- ✅ **Agent 是产品，Harness 是生产线**

## 关键要点

1. **LLM ≠ Agent**：LLM 只是预测下一个 token；Agent 需要 loop、工具、状态等外围机制。
2. **Harness 是模型无关的**：同一套 harness 可以换不同的 LLM，造出不同的 Agent。
3. **Deep Agents 的定位**：在 LangChain + LangGraph 之上的 opinionated harness，`create_deep_agent()` 是它的核心组装入口。
4. **组装公式**：`Agent = Harness + Model + Tools + Prompt + Config`。
