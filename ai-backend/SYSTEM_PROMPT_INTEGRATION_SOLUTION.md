# 系统提示词集成解决方案

## 问题描述

你担心数据缩减策略中定义的分析提示词会覆盖或影响原来系统中已有的提示词模板，导致分析结果与系统要求不一致。

## 解决方案

我已经实现了灵活的系统提示词集成机制，让你可以完全控制数据缩减过程中使用的提示词。

### 核心特性

1. **智能提示词集成**: 自动检测并使用原有的系统提示词
2. **多种集成模式**: 提供三种不同的集成方式
3. **配置灵活性**: 可以通过配置完全控制提示词行为
4. **向后兼容**: 不影响现有代码的使用

### 集成模式

#### 1. 合并模式 (merge) - 推荐使用
```python
config = {
    "data_reduce": {
        "use_system_prompt": True,
        "prompt_integration_mode": "merge"
    }
}
```

**工作原理**:
- 保留原有系统提示词的所有要求
- 添加数据分块分析的具体指令
- 确保分析结果与系统要求完全一致

**示例**:
```
[原有系统提示词]
你是一个专业的数据分析助手。
根据用户输入和提供的数据，帮助分析，并给出分析报告。
使用与用户输入**完全相同**的语言进行回复。

请基于以上系统要求，分析以下数据片段：

数据片段：
{text}

请提供：
1. 关键数据点
2. 重要趋势或模式
3. 异常值或值得注意的点
4. 简要总结
```

#### 2. 替换模式 (replace)
```python
config = {
    "data_reduce": {
        "use_system_prompt": True,
        "prompt_integration_mode": "replace"
    }
}
```

**工作原理**:
- 完全使用系统提示词
- 不添加额外的分析指令
- 适合系统提示词已经包含完整分析指令的情况

#### 3. 无模式 (none)
```python
config = {
    "data_reduce": {
        "use_system_prompt": False,
        "prompt_integration_mode": "none"
    }
}
```

**工作原理**:
- 使用独立的数据分析提示词
- 不受系统提示词影响
- 适合特殊场景

### 实现细节

#### 1. 自动系统提示词检测
```python
# 在DataAnalyzeAgent中自动保存系统提示词
async def get_system_prompt(self, user_query: str, **kwargs):
    # ... 原有的系统提示词生成逻辑 ...

    # 保存系统提示词供数据缩减策略使用
    self.current_system_prompt = prompt

    return prompt
```

#### 2. 智能提示词传递
```python
# 在数据缩减过程中传递系统提示词
if self.data_reduce_strategy.should_reduce_data(analyze_data):
    # 获取系统提示词（如果存在）
    system_prompt = None
    if hasattr(self, 'current_system_prompt'):
        system_prompt = self.current_system_prompt

    # 根据数据类型选择缩减策略
    if isinstance(analyze_data, str):
        analyze_data = self.data_reduce_strategy.reduce_text_data(
            analyze_data, analysis_prompt, system_prompt
        )
```

#### 3. 灵活的提示词处理
```python
# 在DataReduceStrategy中根据配置处理提示词
if system_prompt and self.use_system_prompt:
    if self.prompt_integration_mode == "merge":
        # 合并系统提示词和分析指令
        analysis_prompt = f"{system_prompt}\n\n请基于以上系统要求，分析以下数据片段：..."
    elif self.prompt_integration_mode == "replace":
        # 完全使用系统提示词
        analysis_prompt = system_prompt
    # "none" 模式不修改analysis_prompt
```

### 使用示例

#### 基本使用（无需修改现有代码）
```python
# 原有代码无需修改，系统会自动处理
agent = DataAnalyzeAgent(config=config)
async for response in agent.execute(
    user_query="分析交易数据",
    analyze_data=large_data
):
    print(response.message)
```

#### 自定义配置
```python
# 使用合并模式（推荐）
config_merge = {
    "data_reduce": {
        "use_system_prompt": True,
        "prompt_integration_mode": "merge"
    }
}

agent = DataAnalyzeAgent(config=config_merge)
```

#### 完全使用系统提示词
```python
# 使用替换模式
config_replace = {
    "data_reduce": {
        "use_system_prompt": True,
        "prompt_integration_mode": "replace"
    }
}

agent = DataAnalyzeAgent(config=config_replace)
```

### 优势

1. **完全兼容**: 不影响现有代码的使用
2. **灵活配置**: 可以根据需要选择不同的集成模式
3. **智能处理**: 自动检测和使用系统提示词
4. **一致性保证**: 确保分析结果与系统要求一致
5. **降级支持**: 提供多种降级策略

### 推荐配置

对于大多数使用场景，推荐使用合并模式：

```python
config = {
    "data_reduce": {
        "max_tokens": 4000,
        "chunk_size": 2000,
        "chunk_overlap": 200,
        "max_items_per_chunk": 100,
        "use_system_prompt": True,  # 启用系统提示词
        "prompt_integration_mode": "merge",  # 使用合并模式
        "llm": {
            "model": "gpt-4o-mini",
            "temperature": 0,
            "api_key": "your-openai-api-key"
        }
    }
}
```

这样配置可以：
- 保持原有系统提示词的所有要求
- 确保分析结果与系统要求一致
- 提供高效的大数据量处理能力
- 保持代码的简洁性和可维护性

## 总结

通过这个解决方案，你可以：
1. **完全控制**数据缩减过程中使用的提示词
2. **保持一致性**，确保分析结果符合系统要求
3. **灵活配置**，根据实际需求选择不同的集成模式
4. **无需修改**现有代码，系统会自动处理

这个实现完美解决了你担心的系统提示词冲突问题，同时提供了强大的大数据量处理能力。
