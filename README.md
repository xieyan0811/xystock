# xystock

一个极简的股票/基金分析工具，支持实时行情获取和大模型分析。

![](./res/img_01.png)

## 安装和使用

克隆仓库并构建Docker镜像

   ```bash
   git clone git@github.com:xieyan0811/xystock.git
   cd xystock
   docker build . -t xystock:latest
   ```

启动Docker Compose容器

生产模式：
   
```bash
 docker compose up -d
 ```
   
 开发模式：
 ```bash
 docker compose -f docker-compose.dev.yml up -d
 docker exec -it xystock-web bash
 python -m streamlit run ui/app.py --server.address=0.0.0.0 --server.port=8811
 ```

打开本机的 8811 端口，先配置大模型相关参数。随后可以依次尝试以下功能：token统计、大盘分析、股票分析。

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
| DeepSeek Reasoner | deepseek-reasoner | 推理模型 |

目前我使用的是 deepseek 系列模型，价格便宜且更了解中国情况。目前 deepseek-reasoner 比 deepseek-chat 贵一倍，2025 年 09 月 06后有调整，具体价格与是否缓存有关，不太好统计。计费方法具体见：https://api-docs.deepseek.com/zh-cn/quick_start/pricing/

### 其他兼容服务

系统也支持 OpenRouter、Ollama 等提供兼容 OpenAI 接口的服务。只需在设置中配置相应的 Base URL 和 API Key 即可。

## 模型使用建议

- **普通模型**：对于快速查询和简单任务，建议使用较轻量的模型，如 GPT-4.1-mini、o4-mini 或通义千问 Turbo。
- **推理模型**：建议使用功能更强大的模型，如 GPT-4o、o3 或通义千问 Max，以获取更深入的股票分析。

## 目录结构
- provider/ 数据获取脚本
- llm/  大模型相关及prompt
- ui/   预留界面
- notebooks/ 实验用notebook
- data/ 过程数据

*如果你觉得项目对你有帮助或能解决你的实际问题，请帮我点亮小星星～*

![](./res/img_02_1.png)

![](./res/img_02_2.png)

![](./res/img_03.png)

![](./res/img_04.png)
