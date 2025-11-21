# AI Chat 中断机制改进实现说明

## 问题描述

原有的中断机制存在一个严重问题：当大模型 API 调用（`ChatOpenAI.invoke()`）因网络原因长时间等待时，中断检查无法及时生效，导致用户中断操作失效。

## 解决方案

通过以下改进实现了真正可中断的 LLM 调用：

### 1. 引入异步 API 调用

- 将同步的 `invoke()` 改为异步的 `ainvoke()`
- 将同步的 `stream()` 改为异步的 `astream()`
- 使用 `asyncio.Task` 包装 LLM 调用，实现可取消的异步任务

### 2. 实现中断检查机制

#### 2.1 添加中断异常类

```python
class InterruptedException(Exception):
    """中断异常，用于处理用户主动中断"""
    pass
```

#### 2.2 在 Agent 基类中添加中断检查

```python
class Base(ABC):
    def __init__(self, ...):
        self.interruption_checker: Optional[Callable[[], bool]] = None

    def set_interruption_checker(self, checker: Callable[[], bool]):
        """设置中断检查函数"""
        self.interruption_checker = checker

    def check_interruption(self):
        """检查是否需要中断执行"""
        if self.interruption_checker and self.interruption_checker():
            raise InterruptedException("任务已被用户中断")
```

#### 2.3 实现带中断检查的异步调用

```python
async def _invoke_with_interruption_check(self, messages: List[BaseMessage]) -> AIMessage:
    """
    带中断检查的异步 invoke
    使用 asyncio.Task 包装，支持中断取消
    """
    # 创建异步调用任务
    task = asyncio.create_task(self.llm.ainvoke(messages))

    # 定期检查中断状态，同时等待任务完成
    check_interval = 0.1  # 每0.1秒检查一次
    while not task.done():
        try:
            # 检查中断
            self.check_interruption()
            # 等待一小段时间或任务完成
            await asyncio.wait({task}, timeout=check_interval)
        except InterruptedException:
            # 取消任务
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            raise

    # 返回结果
    return await task
```

### 3. 修改各个 Agent

将所有 Agent 中的同步调用改为异步调用：

- `IntentRecognitionAgent`: `invoke()` → `ainvoke()`
- `ExtractParametersAgent`: `invoke()` → `ainvoke()`
- `DataAnalyzeAgent`: `invoke()` → `ainvoke()`
- `GeneralChatAgent`: `invoke()` → `ainvoke()`, `stream()` → `astream()`

### 4. 传递中断检查器

#### 4.1 在 ai_chat.py 中创建中断检查器

```python
# 创建中断检查器函数
def check_interruption():
    return interruption_status.get(chat_id, False)

async for message in agent.auto_orchestrate(
    user_query=request.message,
    conversation_history=history_messages,
    action=action,
    interruption_checker=check_interruption,  # 传递中断检查器
):
    ...
```

#### 4.2 在 Agent 中传递检查器

```python
# 在 agent.py 的 auto_orchestrate 方法中
interruption_checker = kwargs.get("interruption_checker")
if interruption_checker:
    self.intent_recognition_agent.set_interruption_checker(interruption_checker)
```

### 5. 处理中断异常

```python
except InterruptedException:
    # 处理用户主动中断
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

## 实现效果

### 改进前
- 用户点击中断按钮后，只有在下次输出流式数据时才会检查中断状态
- 如果 LLM API 调用阻塞（如网络延迟），中断无法生效
- 用户需要等待 API 调用超时或返回后才能中断

### 改进后
- 每 0.1 秒检查一次中断状态，即使 LLM API 正在调用
- 检测到中断后立即取消 asyncio.Task
- LLM API 调用被取消，程序立即响应中断
- 用户体验大幅提升，中断响应时间从可能的几十秒降低到 0.1 秒

## 关键技术点

1. **asyncio.Task**: 将 LLM 调用包装为可取消的任务
2. **asyncio.wait**: 使用超时参数实现定期检查
3. **task.cancel()**: 取消正在进行的 API 调用
4. **InterruptedException**: 统一的中断异常处理
5. **异步调用链**: 确保整个调用链都是异步的，才能实现真正的可中断

## 注意事项

1. 所有 Agent 的 `execute()` 方法必须是异步的
2. 中断检查器必须从外部传入，不能硬编码
3. 中断异常需要在适当的层级捕获并处理
4. 确保在 `finally` 块中清理中断状态

## 测试建议

1. 测试正常流程完成
2. 测试在意图识别阶段中断
3. 测试在数据分析阶段中断
4. 测试在通用聊天阶段中断
5. 测试网络延迟情况下的中断响应时间
6. 测试连续多次中断操作

## 文件修改清单

- `backend/agents/schema/agent.py`: 添加中断异常和检查机制，实现异步 LLM 调用
- `backend/agents/agent.py`: 传递中断检查器
- `backend/app/home/api/v1/chat/ai_chat.py`: 创建和传递中断检查器，处理中断异常
- `backend/agents/agents/intent_recognition_agent.py`: 使用异步调用
- `backend/agents/agents/extract_parameters_agent.py`: 使用异步调用
- `backend/agents/agents/data_analyze_agent.py`: 使用异步调用
- `backend/agents/agents/general_chat_agent.py`: 使用异步调用

## 性能影响

- 中断检查间隔为 0.1 秒，对性能影响极小
- 异步调用相比同步调用，在并发场景下性能更好
- 没有额外的线程或进程开销
