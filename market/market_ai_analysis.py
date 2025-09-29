from typing import Dict, Any, Tuple
from llm.openai_client import OpenAIClient
import datetime
import sys
import os

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from market.market_data_tools import get_market_tools
from market.market_data_utils import format_indices_for_analysis
from utils.data_formatters import format_technical_indicators, format_risk_metrics

def generate_index_analysis_report(
    stock_code: str,
    stock_name: str,
    market_report_data: Dict[str, Any],
    user_opinion: str = ''
) -> Tuple[str, str]:
    """生成指数AI分析报告（包含超短期预测）"""
    client = OpenAIClient()
    
    # 生成市场报告文本    
    try:
        market_tools = get_market_tools()
        market_report_text = market_tools.generate_market_report(
            market_report_data, 
            format_type='detail', 
            markdown=False
        )
    except Exception as e:
        market_report_text = f"市场报告数据格式化失败: {str(e)}"
        return False, market_report_text, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 获取当前指数数据并格式化
    try:
        market_tools = get_market_tools()
        current_indices = market_tools.get_current_indices(use_cache=True, force_refresh=False)
        indices_text = format_indices_for_analysis(current_indices, stock_name)
    except Exception as e:
        indices_text = f"## 当前市场指数情况：\n获取指数数据失败: {str(e)}\n"
    
    # 获取技术指标数据并格式化
    try:
        tech_indicators = market_tools.get_index_technical_indicators(stock_name)
        tech_text = format_technical_indicators(tech_indicators)
        if 'risk_metrics' in tech_indicators:
            risk_metrics = tech_indicators['risk_metrics']
            tech_text += "\n" + format_risk_metrics(risk_metrics)
    except Exception as e:
        tech_text = f"## 主要技术指标：\n获取技术指标失败: {str(e)}\n"
    
    system_message = f"""你是一位资深的投资顾问和市场分析师。请基于市场综合数据、技术指标、市场新闻资讯和用户观点，对{stock_name}（{stock_code}）提供精炼的投资决策分析。

请严格按照以下结构输出，内容务必简洁、聚焦决策：

## 📄 市场分析报告

1. **市场现状与技术面**
- 总结当前市场核心特征和技术指标状态
- 结合指数表现分析市场情绪和资金动向
- 重点关注市场新闻中的政策面、宏观经济动向对市场的影响

2. **新闻面分析**
- 结合最新市场资讯，分析对大盘指数的潜在影响
- 识别政策导向、资金流向等关键信息

3. **用户观点整合**
- 如有用户观点，简要评价其合理性与风险点

4. **涨跌预测**
- 下个交易日：上涨、平盘、下跌的概率分布，预测置信度（±1% 内的波动认为"平盘"）
- 超短期（1周）短期（1个月）和中期（3-6个月）趋势判断

5. **操作建议**
- 针对不同风险偏好给出具体建议（仓位、板块、时机）
- 市场波动时特别提醒保持理性，避免情绪化操作

6. **风险提示**
- 列出1-3个当前最需警惕的市场风险
- 关注新闻中提到的潜在风险因素

【要求】全文不超过700字，只输出最有决策价值的内容，结论要有明确操作性。
"""

    user_message = f"""基于以下数据，请对{stock_name}({stock_code})提供精简分析报告：

{market_report_text}

{indices_text}

{tech_text}"""

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
