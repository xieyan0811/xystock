# xystock

一个极简的股票/基金分析工具，支持实时行情获取和大模型分析。

## 目录结构
- provider/ 数据获取脚本
- llm/  大模型相关及prompt
- ui/   预留界面
- notebooks/ 实验用notebook
- data/ 过程数据

## 快速开始
1. 安装依赖：`pip install -r requirements.txt`
2. 设置OpenAI API Key（环境变量OPENAI_API_KEY）
3. 运行：`python main.py`

## 支持的模型

系统支持所有兼容 OpenAI API 的模型服务，包括但不限于 OpenAI、OpenRouter、阿里百炼、Ollama 等。以下是经过测试和推荐的模型列表：

### OpenAI 模型

| 模型名称 | 模型ID | 推荐用途 |
|---------|--------|---------|
| GPT-4.1-nano | gpt-4.1-nano | 超轻量级模型，适合基础操作 |
| GPT-4.1-mini | gpt-4.1-mini | 紧凑型模型，性能较好 |
| GPT-4o | gpt-4o | 标准模型，功能全面 |
| o4-mini | o4-mini | 专业推理模型（紧凑版） |
| o3-mini | o3-mini | 高级推理模型（轻量级） |
| o3 | o3 | 完整高级推理模型 |
| o1 | o1 | 顶级推理和问题解决模型 |

### 阿里百炼 (DashScope) 模型

| 模型名称 | 模型ID | 推荐用途 |
|---------|--------|---------|
| 通义千问 Turbo | qwen-turbo | 快速响应，适合日常对话 |
| 通义千问 Plus | qwen-plus | 平衡性能和成本 |
| 通义千问 Max | qwen-max | 最强性能 |
| 通义千问 Max 长文本版 | qwen-max-longcontext | 支持超长上下文 |

### DeepSeek v3 模型

| 模型名称 | 模型ID | 推荐用途 |
|---------|--------|---------|
| DeepSeek Chat | deepseek-chat | 通用对话模型，适合股票投资分析 |

### 其他兼容服务

系统也支持 OpenRouter、Ollama 等提供兼容 OpenAI 接口的服务。只需在设置中配置相应的 Base URL 和 API Key 即可。

## 模型使用建议

- **普通模型**：对于快速查询和简单任务，建议使用较轻量的模型，如 GPT-4.1-mini、o4-mini 或通义千问 Turbo。
- **推理模型**：建议使用功能更强大的模型，如 GPT-4o、o3 或通义千问 Max，以获取更深入的股票分析。
