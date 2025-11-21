# AI聊天接口详细说明文档

## 接口概览

**接口路径**: `/api/v1/home/chat/completion`
**请求方法**: `POST`
**响应类型**: `text/event-stream` (Server-Sent Events)
**功能**: 流式AI聊天完成接口，支持智能代理编排、意图识别、工具调用等功能

---

## 目录

1. [接口基本信息](#接口基本信息)
2. [请求参数](#请求参数)
3. [响应格式](#响应格式)
4. [核心实现流程](#核心实现流程)
5. [关键技术组件](#关键技术组件)
6. [错误处理机制](#错误处理机制)
7. [中断机制](#中断机制)
8. [数据持久化](#数据持久化)
9. [依赖服务](#依赖服务)
10. [代码结构](#代码结构)

---

## 接口基本信息

### 路由注册链

```
FastAPI App
  └── router (backend/app/router.py)
      └── home_v1 (backend/app/home/api/router.py)
          └── /api/v1/home
              └── chat_router (backend/app/home/api/v1/chat/__init__.py)
                  └── /chat
                      └── ai_chat_router (backend/app/home/api/v1/chat/ai_chat.py)
                          └── /completion
```

**完整路径**: `/api/v1/home/chat/completion`

### 接口定义

```python
@router.post("/completion")
async def stream_chat_completion(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_home_user)
) -> StreamingResponse
```

---

## 请求参数

### ChatRequest Schema

定义位置: `backend/app/home/schema/ai_chat.py`

```python
class ChatRequest(BaseModel):
    chat_id: str          # 聊天会话ID (必需，最小长度1)
    message: str          # 用户消息内容 (必需，最小长度1)
    action: Optional[str] # 操作类型: "auto" | "agent" | "chat" (可选，默认"auto")
    channel: Optional[str] # 渠道标识 (可选，用于日志记录)
```

### 字段验证

- `chat_id`: 不能为空或仅包含空白字符，会自动去除首尾空格
- `message`: 不能为空或仅包含空白字符，会自动去除首尾空格
- `action`: 如果提供，必须是 `"auto"`, `"agent"`, `"chat"` 之一，否则默认为 `"auto"`

### 请求示例

```json
{
    "chat_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "查询今天的用户数据",
    "action": "auto",
    "channel": "web"
}
```

---

## 响应格式

### 响应类型

**Content-Type**: `text/event-stream`
**格式**: Server-Sent Events (SSE)

### 消息格式

每条消息以 `data: ` 开头，后跟JSON字符串，以两个换行符 `\n\n` 结尾。

```
data: {"type": "chat", "message": "正在处理您的请求..."}\n\n
data: {"type": "step", "message": "步骤1: 识别意图"}\n\n
data: {"type": "file", "file": {...}, "message": "相关文件"}\n\n
```

### 消息类型

#### 1. 聊天消息 (chat)
```json
{
    "type": "chat",
    "message": "AI回复的文本内容"
}
```

#### 2. 步骤信息 (step)
```json
{
    "type": "step",
    "message": "当前执行步骤的描述"
}
```

#### 3. 文件信息 (file)
```json
{
    "type": "file",
    "file": {
        "filename": "example.csv",
        "content": "...",
        "type": "csv"
    },
    "message": "文件说明"
}
```

#### 4. Markdown信息 (md_info)
```json
{
    "type": "md_info",
    "message": "Markdown格式的内容"
}
```

#### 5. 错误信息 (error)
```json
{
    "type": "error",
    "message": "错误描述"
}
```

#### 6. 中断信息 (interrupted)
```json
{
    "type": "interrupted",
    "message": "\n用户中断"
}
```

#### 7. 日志信息 (log)
```json
{
    "type": "log",
    "title": "日志标题",
    "content": ["日志内容1", "日志内容2"]
}
```

---

## 核心实现流程

### 完整流程图

```
1. 接收请求
   │
   ├─> 验证 chat_id 是否存在
   ├─> 检查用户权限 (chat.user_id == current_user.id)
   │
2. 创建消息记录
   │
   ├─> 创建用户消息 (role="user")
   ├─> 创建AI助手消息 (role="assistant", content="", is_interrupted=False)
   │
3. 初始化中断状态
   │
   └─> interruption_status[chat_id] = False
   │
4. 获取历史消息
   │
   └─> agent_service.get_history_messages(db, chat)
       │
       ├─> 如果存在压缩摘要，添加系统消息
       ├─> 获取最近的消息记录 (默认6条)
       └─> 如果消息达到限制，触发后台压缩任务
   │
5. 获取模型配置
   │
   ├─> 获取系统默认模型ID
   ├─> 查询模型配置 (api_key, base_url, model_name, temperature)
   └─> 构建 llm_config
   │
6. 创建Agent实例
   │
   └─> Agent(config={"llm": llm_config})
   │
7. 流式生成响应 (generate_stream)
   │
   ├─> 提取 crm_user_id (如果存在)
   ├─> 创建中断检查器函数
   │
   └─> 调用 agent.auto_orchestrate()
       │
       ├─> 意图识别 (IntentRecognitionAgent)
       │   ├─> 根据 action 参数选择处理方式
       │   └─> 返回意图识别结果
       │
       ├─> 根据意图创建处理器 (IntentHandlerFactory)
       │   ├─> 根据 selected_service 创建对应的 Handler
       │   └─> 可能包括: MCP查询、数据分析、普通聊天等
       │
       └─> 执行处理器并流式返回消息
           │
           ├─> 格式化消息 (format_message)
           ├─> 收集完整内容
           ├─> 处理文件信息
           └─> 流式输出 (yield)
   │
8. 更新消息内容
   │
   ├─> 成功: 更新 assistant_message 的 content 和 response_data
   ├─> 中断: 标记 is_interrupted=True，追加中断消息
   └─> 错误: 标记 is_interrupted=True，记录错误信息
   │
9. 清理资源
   │
   └─> 删除 interruption_status[chat_id]
```

### 代码执行顺序

```python
# 1. 验证和权限检查
if not request.chat_id:
    raise HTTPException(status_code=400, detail="chat_id is required")

chat = await ai_chat_service.get_chat(db, chat_id=request.chat_id)
if not chat:
    raise HTTPException(status_code=404, detail="Chat not found")
if chat.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Not authorized")

# 2. 创建消息记录
await ai_chat_service.create_user_message(db, chat_id=request.chat_id, content=request.message)
assistant_message = await ai_chat_service.create_assistant_message(
    db, chat_id=request.chat_id, content="", is_interrupted=False
)

# 3. 初始化中断状态
interruption_status[request.chat_id] = False

# 4. 获取历史消息
history_messages = await agent_service.get_history_messages(db, chat)

# 5. 获取模型配置
default_model_id = await ai_model_service.get_default_model_id(db)
model = await ai_model_service.get_model_by_id(db, model_id=default_model_id)
llm_config = {
    "id": model.id,
    "api_key": model.api_key,
    "base_url": model.base_url,
    "name": model.name,
    "model_name": model.model,
    "temperature": model.temperature,
}

# 6. 创建Agent
chat_agent = Agent(config={"llm": llm_config})

# 7. 流式生成
async def generate_stream():
    # 提取 crm_user_id
    crm_user_id = None
    try:
        crm_val = getattr(current_user, "crm_user_id", None)
        if crm_val is not None:
            crm_str = str(crm_val).strip()
            if crm_str.isdigit():
                crm_user_id = int(crm_str)
    except Exception:
        crm_user_id = None

    # 中断检查器
    def check_interruption():
        return interruption_status.get(chat_id, False)

    try:
        # 调用Agent编排
        async for message in chat_agent.auto_orchestrate(
            user_query=request.message,
            conversation_history=history_messages,
            action=action,
            last_confirm_intent_message=confirm_intent_message.get(chat_id),
            crm_user_id=crm_user_id,
            interruption_checker=check_interruption,
        ):
            message = format_message(message)
            full_content.append(message)

            # 处理文件信息
            if message.get("file"):
                files.append(message.get("file"))
                if message.get("message"):
                    file_message += f"{message.get('message')}\n"

            # 处理普通消息
            if message.get("message") and message.get("type") in ["chat", "error", "md_info", "step"]:
                full_message += message.get("message")

            yield f"data: {json.dumps(message, ensure_ascii=False)}\n\n"

        # 追加文件信息
        if file_message:
            full_message += f"\n以下是相关文件\n{file_message}"

        # 更新消息内容
        await ai_chat_service.update_message_content(
            db,
            message_id=assistant_message.id,
            content=full_message,
            response_data=json.dumps(full_content, ensure_ascii=False, cls=CustomJSONEncoder),
            is_interrupted=False,
        )

    except InterruptedException:
        # 处理中断
        if file_message:
            full_message += f"\n以下是相关文件\n{file_message}"
        interrupted_message = "\n用户中断"
        full_message += interrupted_message
        full_content.append({"type": "interrupted", "message": interrupted_message})

        await ai_chat_service.update_message_content(
            db,
            message_id=assistant_message.id,
            content=full_message,
            response_data=json.dumps(full_content, ensure_ascii=False, cls=CustomJSONEncoder),
            is_interrupted=True,
        )
        yield f"data: {json.dumps({'type': 'interrupted', 'message': interrupted_message}, ensure_ascii=False)}\n\n"

    except Exception as e:
        # 处理错误
        await ai_chat_service.update_message_content(
            db,
            message_id=assistant_message.id,
            response_data=json.dumps(full_content, ensure_ascii=False, cls=CustomJSONEncoder),
            content=full_message,
            is_interrupted=True,
        )
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n"

    finally:
        # 清理中断状态
        if chat_id in interruption_status:
            del interruption_status[chat_id]

return StreamingResponse(generate_stream(), media_type="text/event-stream")
```

---

## 关键技术组件

### 1. Agent 智能代理

**位置**: `backend/agents/agent.py`

Agent 是核心的智能编排器，负责：

- **意图识别**: 使用 `IntentRecognitionAgent` 分析用户意图
- **处理器选择**: 根据意图选择对应的处理器（Handler）
- **工具调用**: 支持MCP服务、数据分析等工具调用
- **流式响应**: 通过异步生成器返回流式消息

#### auto_orchestrate 方法

```python
async def auto_orchestrate(
    self,
    user_query: str,
    conversation_history: Optional[List] = None,
    action: str = "auto",
    **kwargs
) -> AsyncGenerator[Dict[str, Any], None]:
```

**参数说明**:
- `user_query`: 用户查询文本
- `conversation_history`: 历史对话列表
- `action`: 操作类型 ("auto", "agent", "chat")
- `**kwargs`: 其他参数，包括:
  - `crm_user_id`: CRM用户ID（用于数据查询）
  - `interruption_checker`: 中断检查函数
  - `last_confirm_intent_message`: 上次确认的意图消息

**执行流程**:
1. 调用意图识别Agent
2. 根据意图结果创建对应的Handler
3. 执行Handler并流式返回消息
4. 返回调试日志信息

### 2. 意图识别 (IntentRecognitionAgent)

**位置**: `backend/agents/agents/intent_recognition_agent.py`

负责识别用户意图，确定需要使用的服务类型。

### 3. 意图处理器工厂 (IntentHandlerFactory)

**位置**: `backend/agents/manager/factories/intent_factory.py`

根据意图识别结果创建对应的处理器：
- MCP查询处理器
- 数据分析处理器
- 普通聊天处理器
- 其他自定义处理器

### 4. 消息格式化 (format_message)

**位置**: `backend/utils/format_output.py`

将各种类型的消息对象转换为可JSON序列化的字典格式。

```python
def format_message(message: Any):
    """格式化消息，确保所有对象都能被JSON序列化"""
    if isinstance(message, YieldResponse):
        return message.model_dump(mode="json")
    elif isinstance(message, (dict, str)):
        return message
    elif hasattr(message, "model_dump"):
        return message.model_dump(mode="json")
    else:
        return convert_to_dict(message)
```

### 5. 历史消息压缩

**位置**: `backend/app/home/service/agent_service.py`

当历史消息达到限制（默认6条）时，会触发后台异步压缩任务：

1. 将历史对话压缩为摘要
2. 提取关键信息点
3. 更新聊天会话的 `history_summary` 和 `summary_time`
4. 后续对话使用压缩摘要替代原始历史消息

**优势**:
- 减少Token消耗
- 保持上下文相关性
- 提高响应速度

---

## 错误处理机制

### 异常类型

#### 1. HTTP异常

```python
# chat_id 验证失败
if not request.chat_id:
    raise HTTPException(status_code=400, detail="chat_id is required")

# 聊天会话不存在
if not chat:
    raise HTTPException(status_code=404, detail="Chat not found")

# 权限不足
if chat.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Not authorized to access this chat")
```

#### 2. InterruptedException

**定义位置**: `backend/agents/schema/agent.py`

当用户主动中断时抛出，处理逻辑：

```python
except InterruptedException:
    interrupted_message = "\n用户中断"
    full_message += interrupted_message
    full_content.append({"type": "interrupted", "message": interrupted_message})

    await ai_chat_service.update_message_content(
        db,
        message_id=assistant_message.id,
        content=full_message,
        response_data=json.dumps(full_content, ensure_ascii=False, cls=CustomJSONEncoder),
        is_interrupted=True,
    )
    yield f"data: {json.dumps({'type': 'interrupted', 'message': interrupted_message}, ensure_ascii=False)}\n\n"
```

#### 3. 通用异常

```python
except Exception as e:
    await ai_chat_service.update_message_content(
        db,
        message_id=assistant_message.id,
        response_data=json.dumps(full_content, ensure_ascii=False, cls=CustomJSONEncoder),
        content=full_message,
        is_interrupted=True,
    )
    yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n"
```

### 错误恢复

- 所有错误都会更新消息记录，标记为已中断
- 完整的响应数据保存在 `response_data` 字段中
- 错误信息会流式返回给客户端

---

## 中断机制

### 中断状态管理

使用全局字典 `interruption_status` 管理中断状态：

```python
interruption_status = {}  # {chat_id: bool}

# 初始化
interruption_status[request.chat_id] = False

# 检查中断
def check_interruption():
    return interruption_status.get(chat_id, False)

# 清理
finally:
    if chat_id in interruption_status:
        del interruption_status[chat_id]
```

### 中断接口

**路径**: `/api/v1/home/chat/interrupt/{chat_id}`
**方法**: `POST`

```python
@router.post("/interrupt/{chat_id}")
async def interrupt_stream(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_home_user),
):
    """中断指定的流式任务"""
    if chat_id in interruption_status:
        interruption_status[chat_id] = True
        return {"status": 1, "message": "Interruption signal sent"}
    else:
        raise HTTPException(status_code=404, detail="Task not found")
```

### 中断检查点

Agent在执行过程中会定期检查中断状态：

```python
# 在Agent的各个执行点检查中断
if interruption_checker():
    raise InterruptedException("任务已被用户中断")
```

### 中断处理流程

```
用户调用中断接口
    │
    └─> interruption_status[chat_id] = True
        │
        └─> Agent 检查中断状态
            │
            └─> 抛出 InterruptedException
                │
                └─> 捕获异常
                    │
                    ├─> 更新消息内容
                    ├─> 标记 is_interrupted=True
                    ├─> 流式返回中断消息
                    └─> 清理中断状态
```

---

## 数据持久化

### 消息记录

每条对话都会创建两条消息记录：

1. **用户消息** (role="user")
   - `chat_id`: 聊天会话ID
   - `role`: "user"
   - `content`: 用户输入的文本
   - `is_interrupted`: False

2. **助手消息** (role="assistant")
   - `chat_id`: 聊天会话ID
   - `role`: "assistant"
   - `content`: AI回复的完整文本
   - `response_data`: 完整的响应数据（JSON格式）
   - `is_interrupted`: 是否被中断

### 数据表结构

#### AIChatMessage 表

```python
class AIChatMessage:
    id: str                    # 消息ID (UUID)
    chat_id: str               # 聊天会话ID
    role: str                  # 角色: "user" | "assistant" | "system"
    content: str               # 消息内容
    response_data: Optional[str]  # 响应数据 (JSON字符串)
    is_interrupted: bool       # 是否被中断
    created_time: datetime     # 创建时间
    updated_time: datetime     # 更新时间
```

### 响应数据格式

`response_data` 字段保存完整的响应数据，包括：

```json
[
    {
        "type": "chat",
        "message": "消息内容"
    },
    {
        "type": "step",
        "message": "步骤信息"
    },
    {
        "type": "file",
        "file": {...},
        "message": "文件说明"
    },
    ...
]
```

### 自定义JSON编码器

为了正确序列化复杂对象，使用了 `CustomJSONEncoder`:

```python
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (AIMessage, HumanMessage, SystemMessage, BaseMessage)):
            return {"type": obj.__class__.__name__, "content": obj.content}
        if hasattr(obj, "value"):
            return obj.value
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        return super().default(obj)
```

---

## 依赖服务

### 1. AIChatService

**位置**: `backend/app/home/service/ai_chat_service.py`

提供聊天和消息的CRUD操作：

- `create_chat()`: 创建聊天会话
- `get_chat()`: 获取聊天会话
- `create_user_message()`: 创建用户消息
- `create_assistant_message()`: 创建助手消息
- `update_message_content()`: 更新消息内容
- `get_chat_messages()`: 获取聊天消息列表

### 2. AgentService

**位置**: `backend/app/home/service/agent_service.py`

提供Agent相关的服务：

- `get_history_messages()`: 获取历史消息（支持压缩摘要）
- `compress_conversation_history()`: 压缩历史对话

### 3. AIModelService

**位置**: `backend/app/home/service/ai_model_service.py`

提供AI模型配置服务：

- `get_default_model_id()`: 获取系统默认模型ID
- `get_model_by_id()`: 根据ID获取模型配置
- `get_all_enabled_models()`: 获取所有启用的模型

### 4. 数据库依赖

```python
db: AsyncSession = Depends(get_db)
```

使用SQLAlchemy异步会话进行数据库操作。

### 5. 用户认证依赖

```python
current_user: User = Depends(get_current_home_user)
```

确保用户已认证，并获取当前用户信息。

---

## 代码结构

### 主要文件

```
backend/
├── app/
│   └── home/
│       ├── api/
│       │   └── v1/
│       │       └── chat/
│       │           ├── __init__.py          # 路由注册
│       │           └── ai_chat.py            # 接口实现 ⭐
│       ├── schema/
│       │   └── ai_chat.py                    # 数据模型定义
│       └── service/
│           ├── ai_chat_service.py            # 聊天服务
│           ├── agent_service.py              # Agent服务
│           └── ai_model_service.py           # 模型服务
├── agents/
│   ├── agent.py                              # Agent主类 ⭐
│   ├── agents/
│   │   └── intent_recognition_agent.py       # 意图识别
│   └── manager/
│       └── factories/
│           └── intent_factory.py             # 处理器工厂
└── utils/
    └── format_output.py                      # 消息格式化
```

### 关键类和方法

#### 1. stream_chat_completion

**位置**: `backend/app/home/api/v1/chat/ai_chat.py:54`

主接口函数，处理完整的请求流程。

#### 2. generate_stream

**位置**: `backend/app/home/api/v1/chat/ai_chat.py:128`

内部异步生成器函数，负责流式生成响应。

#### 3. Agent.auto_orchestrate

**位置**: `backend/agents/agent.py:31`

智能编排主方法，协调意图识别和处理器执行。

---

## 使用示例

### Python客户端示例

```python
import httpx
import json

async def chat_completion(chat_id: str, message: str):
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/api/v1/home/chat/completion",
            json={
                "chat_id": chat_id,
                "message": message,
                "action": "auto",
                "channel": "python_client"
            },
            headers={
                "Authorization": "Bearer your_token_here"
            }
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])  # 去掉 "data: " 前缀
                    print(f"Type: {data.get('type')}, Message: {data.get('message')}")
```

### JavaScript客户端示例

```javascript
async function chatCompletion(chatId, message) {
    const response = await fetch('/api/v1/home/chat/completion', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer your_token_here'
        },
        body: JSON.stringify({
            chat_id: chatId,
            message: message,
            action: 'auto',
            channel: 'web'
        })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                console.log('Type:', data.type, 'Message:', data.message);
            }
        }
    }
}
```

### 中断请求示例

```python
import httpx

async def interrupt_chat(chat_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8000/api/v1/home/chat/interrupt/{chat_id}",
            headers={"Authorization": "Bearer your_token_here"}
        )
        return response.json()
```

---

## 性能优化

### 1. 异步处理

- 所有数据库操作使用异步SQLAlchemy
- 流式响应使用异步生成器
- 历史消息压缩在后台异步执行

### 2. 历史消息压缩

- 当消息数量达到限制时，自动触发压缩
- 压缩在后台异步执行，不阻塞主流程
- 使用压缩摘要替代完整历史，减少Token消耗

### 3. 流式响应

- 使用Server-Sent Events实现流式响应
- 实时返回处理结果，提高用户体验
- 减少内存占用

### 4. 中断机制

- 轻量级中断检查，不影响性能
- 及时响应用户中断请求

---

## 安全考虑

### 1. 用户认证

- 所有请求必须通过 `get_current_home_user` 认证
- 验证用户身份和权限

### 2. 权限检查

- 验证聊天会话的所有权 (`chat.user_id == current_user.id`)
- 防止未授权访问其他用户的聊天

### 3. 输入验证

- 使用Pydantic模型验证请求参数
- 自动去除首尾空格
- 验证必需字段

### 4. 错误信息

- 错误信息不暴露敏感信息
- 详细的错误日志记录在服务端

---

## 监控和日志

### 日志记录

关键操作都会记录日志：

```python
logger.info(f"llm_config: {llm_config}")
logger.error(f"❌ intent result is None: {str(e)}")
```

### 调试信息

Agent会返回调试信息：

```json
{
    "type": "log",
    "title": "bebug信息",
    "content": [
        {
            "title": "耗时信息",
            "content": "执行时间: 1.23s\n查询时间: 0.45s"
        }
    ]
}
```

---

## 扩展点

### 1. 自定义处理器

通过 `IntentHandlerFactory` 可以添加新的处理器类型：

```python
# 在 intent_factory.py 中注册新处理器
@IntentHandlerFactory.register("custom_service")
class CustomHandler:
    async def handle(self, user_query, conversation_history, intent_data, **kwargs):
        # 自定义处理逻辑
        yield {"type": "chat", "message": "自定义响应"}
```

### 2. 自定义消息类型

在Agent的处理逻辑中可以返回自定义消息类型，前端需要相应处理。

### 3. 模型配置

通过 `AIModelService` 可以动态配置和切换AI模型。

---

## 常见问题

### Q1: 为什么使用流式响应？

A: 流式响应可以提供更好的用户体验，实时显示AI的思考过程和处理步骤，而不是等待完整响应。

### Q2: 如何处理超时？

A: 前端可以通过SSE的超时机制或中断接口来处理超时情况。

### Q3: 历史消息压缩会影响上下文吗？

A: 不会。压缩算法会保留关键信息和上下文，确保对话的连贯性。

### Q4: 如何支持多语言？

A: 可以在Agent的提示词中配置语言，或者在模型配置中设置。

### Q5: 如何添加新的工具或服务？

A: 通过创建新的IntentHandler并注册到IntentHandlerFactory即可。

---

## 更新日志

- **2025-06-09**: 初始版本，支持基础聊天功能
- 后续更新请参考代码注释和Git提交记录

---

## 相关文档

- [Agent架构说明](./AGENT_ARCHITECTURE.md)
- [历史消息压缩](./HISTORY_COMPRESSION_CHANGELOG.md)
- [API文档](./README.md)

---

## 联系方式

如有问题或建议，请联系开发团队或提交Issue。
