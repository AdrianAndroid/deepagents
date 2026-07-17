# 飞书接入 Deep Agents 调研

## 轮次 1 - 是否可以通过飞书聊天让 deepagents 工作

### 用户问题
调研是否可以接入飞书,通过飞书的聊天来让 deepagents 进行工作。

### 结论
**完全可行**,飞书官方提供机器人 + 事件订阅 + Python SDK,Deep Agents 侧最合适的接入点是 `libs/talon/deepagents_talon/channels/`,新增一个 `feishu.py` 通道即可复用现有的 host/exposure/cron/HITL 能力。

### 飞书侧关键信息

**两种机器人形态**
- **群自定义 Webhook**:只能单向推送,不能接收消息,不符合"聊天让 agent 工作"的需求。
- **企业自建应用 + 机器人**:双向对话,可订阅事件、调用 API 回复。**本次场景必选**。

**接入步骤**
1. 开放平台创建自建应用 → 拿 `App ID` / `App Secret` / `Encrypt Key` / `Verification Token`。
2. 添加"机器人"能力,开权限:`im:message`、`im:message.group_at_msg`、`im:message.p2p_msg`、`im:message:send_as_bot`。
3. 订阅事件 `im.message.receive_v1`(v2.0 对应 `P2ImMessageReceiveV1`)。
4. 两种事件传输:
   - **长连接 / WebSocket**(推荐本地/内网):`lark.ws.Client`,无需公网 IP、无需 ngrok。
   - **HTTP 回调**:飞书 POST 到公网 URL,需 URL 校验 + 事件解密。
5. 回复:调用 `im.v1.message.reply/create`,支持文本、富文本、**交互卡片**(有按钮回调,天然适配 HITL 审批)、图片、文件。

**Python SDK**:`larksuite/oapi-sdk-python`,`pip install lark-oapi`。

### Deep Agents 侧接入点对比

| 方案 | 工作量 | 复用度 | 备注 |
|---|---|---|---|
| **Talon 新增 Feishu channel(推荐)** | 中 | 高 | `channels/base.py` 已抽象 `ChannelMessage`/`ChannelExposure`/`dispatch_message`;已有 telegram、whatsapp 参考 |
| 独立 FastAPI + `create_deep_agent` | 小-中 | 低 | 简单 POC 可用,会话/中断/审批要自己写 |
| ACP (`libs/acp`) | 高 | 低 | ACP 是 Zed 编辑器 stdio 协议,不适合 IM |
| Managed 部署 + Webhook 转发 | 小 | 中 | 用 `deepagents-cli deploy`,再写飞书回调转发 HTTP |

### 推荐路径

**方案 A(长期)**:在 `libs/talon/deepagents_talon/channels/feishu.py` 实现 channel adapter
- 参考 `channels/telegram.py` 结构
- 用 `lark.ws.Client` 建立长连接
- 在 `register_p2_im_message_receive_v1` 回调里把事件转成 `ChannelMessage`,调 `dispatch_message(handler, message, provider="feishu")`
- `send()` 调 `im.v1.message.reply/create`
- 加配置:`DEEPAGENTS_TALON_FEISHU_ENABLED/APP_ID/APP_SECRET/EXPOSURE/ALLOWLIST_CHATS/OPERATOR_ID`
- 补测参考 `tests/channels/test_telegram.py`

**方案 B(今天可跑 POC)**:约 100 行 Python 桥接
```python
import lark_oapi as lark
from deepagents import create_deep_agent

agent = create_deep_agent(model="...", tools=[...])

def on_msg(data):
    text = data.event.message.content
    chat_id = data.event.message.chat_id
    result = agent.invoke({"messages":[{"role":"user","content":text}]})
    reply = result["messages"][-1].content
    client.im.v1.message.create(...)

handler = lark.EventDispatcherHandler.builder("","") \
    .register_p2_im_message_receive_v1(on_msg).build()
lark.ws.Client(APP_ID, APP_SECRET, event_handler=handler).start()
```

### 关键注意点

1. **权限与发版**:自建应用需管理员发版审核;测试用"测试企业与人员"绕开。
2. **消息内容格式**:`im.message.receive_v1` 收到的 `content` 是 JSON 字符串,需 `json.loads`(`text`/`image`/`file`)。
3. **HITL 天然契合飞书卡片**:`interrupt_on` 审批可做成"允许/拒绝"按钮卡片,UX 比 Telegram 好。
4. **多会话隔离**:用 `chat_id + user_id` 作为 Talon `conversation_id`,契合 per-conversation serialization。
5. **安全**:长连接模式无需暴露公网端口;HTTP 模式需要 Encrypt Key + Verification Token 校验。

### 后续 TODO(待用户确认后再动)
- [ ] 方案 B POC 脚本落地
- [ ] 方案 A 骨架:`libs/talon/deepagents_talon/channels/feishu.py`
- [ ] 单测参考 `tests/channels/test_telegram.py`
- [ ] 卡片式 HITL 审批的 PoC
