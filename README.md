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
