from typing import Dict, Any, Tuple
from llm.openai_client import OpenAIClient
import datetime
import sys
import os

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from market.market_formatters import MarketTextFormatter
from config_manager import config

def generate_index_analysis_report(
    stock_code: str,
    stock_name: str,
    market_report_data: Dict[str, Any],
    user_opinion: str = ''
) -> Tuple[str, str]:
    """生成指数AI分析报告"""
    client = OpenAIClient()
    core_data = market_report_data
    
    # 使用统一的格式化函数
    try:
        analysis_data = MarketTextFormatter.format_data_for_ai_analysis(
            core_data, stock_name
        )
    except Exception as e:
        error_msg = f"格式化市场数据失败: {str(e)}"
        return False, error_msg, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 根据新闻功能是否启用调整系统消息
    news_enabled = config.is_market_news_enabled()
    
    if news_enabled:
        data_sources = "市场综合数据、技术指标、市场新闻资讯和用户观点"
        analysis_sections = """1. **市场现状与技术面**
- 总结当前市场核心特征和技术指标状态
- 结合指数表现分析市场情绪和资金动向
- 重点关注市场新闻中的政策面、宏观经济动向对市场的影响

2. **新闻面分析**
- 结合最新市场资讯，分析对大盘指数的潜在影响
- 识别政策导向、资金流向等关键信息

3. **用户观点整合**
- 如有用户观点，简要评价其合理性与风险点"""
    else:
        data_sources = "市场综合数据、技术指标和用户观点"
        analysis_sections = """1. **市场现状与技术面**
- 总结当前市场核心特征和技术指标状态
- 结合指数表现分析市场情绪和资金动向
- 基于技术指标分析市场趋势和动向

2. **用户观点整合**
- 如有用户观点，简要评价其合理性与风险点"""
    
    system_message = f"""你是一位资深的投资顾问和市场分析师。请基于{data_sources}，对{stock_name}（{stock_code}）提供精炼的投资决策分析。

请严格按照以下结构输出，内容务必简洁、聚焦决策：

## 📄 市场分析报告

{analysis_sections}

{"3" if news_enabled else "2"}. **涨跌预测**
- 下个交易日：上涨、平盘、下跌的概率分布，预测置信度（±1% 内的波动认为"平盘"）
- 超短期（1周）短期（1个月）和中期（3-6个月）趋势判断

{"4" if news_enabled else "3"}. **操作建议**
- 针对不同风险偏好给出具体建议（仓位、板块、时机）
- 市场波动时特别提醒保持理性，避免情绪化操作

6. **风险提示**
- 列出1-3个当前最需警惕的市场风险
- 关注新闻中提到的潜在风险因素

【要求】全文不超过700字，只输出最有决策价值的内容，结论要有明确操作性。
"""

    user_message = f"""基于以下数据，请对{stock_name}({stock_code})提供精简分析报告：

{analysis_data}"""

    if user_opinion and user_opinion.strip():
        user_message += f"""

## 用户观点及关注点

{user_opinion.strip()}

请在分析中特别关注用户提到的观点和关注点，并针对性地给出建议。
"""
    
    with open(os.path.join(project_dir, "data", "cache", "req_market.txt"), "w", encoding="utf-8") as f:
        f.write(system_message + "\n\n")
        f.write(user_message)
    print(f'req length {len(user_message)}')
    # return False, user_message, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 注释掉调试返回 

    try:
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        response = client.chat(
            messages=messages,
            temperature=0.3,  # 降低温度，确保输出更简洁一致
            model_type="inference"
        )
        
        now = datetime.datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        
        return True, response, timestamp
        
    except Exception as e:
        error_msg = f"生成{stock_name}AI分析报告失败: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
