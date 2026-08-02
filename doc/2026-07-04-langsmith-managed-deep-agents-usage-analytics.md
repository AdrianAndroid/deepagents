# LangSmith Managed Deep Agents 用户使用量统计方案

日期:2026-07-04
主题:如何在把 deepagents 部署到 LangSmith Managed Deep Agents 后,统计每个最终用户的使用量(对外发布产品级 usage analytics)。

---

## 轮次 1 - 需求澄清

### 用户提问
"帮我思考,我如何知道用户的使用量?"(问题过于宽泛)

### 澄清结果(用户回答)
- **统计对象**:部署到 LangSmith Managed Deep Agents 后的线上调用量。
- **使用场景**:对外发布产品,想做正式的 usage analytics。
- **约束**:必须走 LangSmith(不引入外部 telemetry)。

### 关键结论
Managed Deep Agents 本身不知道最终用户是谁,必须由调用方在请求侧显式打上 user 标签,才能后续做分用户统计。

---

## 轮次 2 - 方案设计

### 一、指标分层
对外产品的 usage analytics 通常拆三层,每层数据源不同:

| 层级 | 典型指标 | 数据源 |
|---|---|---|
| 业务层 | DAU/MAU、每人会话数、留存、功能使用分布 | 自建聚合,基于 Threads metadata |
| 消耗层 | 每用户 token、费用、按 model 拆分 | LangSmith Traces + Cost Tracking |
| 运行层 | 每用户 run 次数、成功率、延迟、错误率 | LangSmith Traces / Deployment 指标 |

### 二、关键前提:注入 user_id 到两个位置(缺一不可)

1. **Thread metadata**(建 thread 时):
   ```python
   client.threads.create(
       agent_id=agent_id,
       metadata={
           "user_id": "u_123",
           "tenant_id": "acme",
           "plan": "pro",
           "client": "web",
       },
   )
   ```
   之后用 `POST /v1/deepagents/threads/search` 按 `metadata.user_id` 过滤/统计。

2. **Run 的 config.metadata**(每次 stream/invoke 时):
   ```python
   client.threads.stream(
       thread_id, agent_id=agent_id,
       messages=[...],
       config={"metadata": {"user_id": "u_123", "tenant_id": "acme"}},
   )
   ```
   这份 metadata 会流到 LangSmith trace,后续可以在 UI 里按 `metadata_key=user_id` 过滤,cost tracking 也能按 user 维度切。

**关键坑**:只打在 thread 上、不打在 run 的 config 上,LangSmith trace 里就没有 user_id,token/cost 无法按用户拆分。

**补充**:
- 启用 Managed Deep Agents custom auth 时,LangSmith 会自动写入 `langgraph_auth_user_id` 到 thread metadata,业务层 user 可省略,但 run metadata 仍建议显式传。
- 内部 / test / QA 调用必须带 `options.test_run=true`,官方会将其从 usage/analytics 剔除,防止污染指标。

### 三、三条落地路线

**Route A — 只用 LangSmith 内置(上线初期)**
- Prebuilt dashboards:trace 数、token、错误率、latency 开箱可用。
- LangSmith UI 查询语法:`and(eq(metadata_key,"user_id"), eq(metadata_value,"u_123"))`。
- Cost tracking 自动按 usage_metadata 算钱,可按 metadata group by。
- 局限:原生无"按用户 group by"看板,自定义 chart 灵活度有限。

**Route B — 定期拉数据自建仪表盘(推荐)**
- 每天/每小时执行:
  - `POST /v1/deepagents/threads/search` 分页拉,得到每 user 的 thread/活跃数/最近活动。
  - LangSmith Runs API 按 `metadata.user_id` 过滤,聚合 token、cost、run 数、错误率。
- 落 Postgres / BigQuery / ClickHouse,前端做 dashboard。
- 优点:任意维度切分;可做出账、限流、tier 分析。

**Route C — OTel / Prometheus 指标流(规模化)**
- Self-hosted Agent Server 支持 Prometheus scrape + Datadog OTLP push,**Managed 版托管不适用**。
- 托管场景替代:LangSmith 支持 OpenTelemetry 属性(`langsmith.trace.session_id`、`langsmith.metadata.user_id`),在应用侧复制一份 OTel span 到自有观测平台。

### 四、最小可行方案(建议顺序)
1. **立刻**:定义 user 标识策略(登录 user_id / 匿名 device_id / tenant_id),在 API 网关强制注入 thread metadata + run config.metadata。
2. **一周内**:一个每日 job,从 Threads Search + LangSmith Runs API 聚合出:
   ```
   usage_daily(user_id, date, threads, runs, input_tokens, output_tokens, cost, errors)
   ```
3. **隔离测试流量**:内部 QA/eval 全部走 `test_run=true` 或独立 tenant_id,防止污染计费。
4. **长期**:接入 LangSmith cost tracking 做定价对齐,自建 tier/限流/出账。

### 后续 TODO(如需)
- [ ] 起草 metadata schema 规范(字段命名、必填 vs 可选、示例)。
- [ ] 写从 Threads API + LangSmith 聚合 usage 的 Python 脚本雏形。

---

## 轮次 3 - 保存规则确认

### 用户提问
"本项目每次问答都需要保存到 `~/code/deepagents/doc` 方便查看。"

### 结论
- 该规则已存在于 `~/.deepagents/agent/AGENTS.md` 的"文档留存规则"章节。
- 目标目录 `/Users/zhaojian/code/deepagents/doc/` 已存在并在持续积累历史问答。
- 命名沿用 `YYYY-MM-DD-主题-内容摘要.md`。
- 本次问答已按规则保存为本文件。
