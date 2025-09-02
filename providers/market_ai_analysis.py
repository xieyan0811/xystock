from typing import Dict, Any, Tuple
from llm.openai_client import OpenAIClient
import datetime
import sys
import os

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from providers.market_data_tools import get_market_tools

def generate_index_analysis_report(
    stock_code: str,
    stock_name: str,
    market_report_data: Dict[str, Any],
    user_opinion: str = ''
) -> Tuple[str, str]:
    """生成指数AI分析报告（包含超短期预测）"""
    client = OpenAIClient()
    
    try:
        market_tools = get_market_tools()
        market_report_text = market_tools.generate_market_report(market_report_data, 
                                                                 format_type='detail', 
                                                                 markdown=False)
    except Exception as e:
        market_report_text = f"市场报告数据格式化失败: {str(e)}"
    
    try:
        current_indices = market_tools.get_current_indices(use_cache=True, force_refresh=False)
        indices_text = "## 当前市场指数情况：\n"
        target_indices = ["上证指数", "深证成指", "北证50", "创业板指", "科创综指"]
        if 'indices_dict' in current_indices:
            for index_name in target_indices:
                if index_name in current_indices['indices_dict']:
                    index_data = current_indices['indices_dict'][index_name]
                    indices_text += f"- {index_name}: {index_data['current_price']:.2f} "
                    indices_text += f"({index_data['change_percent']:+.2f}%) "
                    indices_text += f"涨跌额: {index_data['change_amount']:+.2f}\n"
        else:
            indices_text += "无法获取指数数据\n"
    except Exception as e:
        indices_text = f"## 当前市场指数情况：\n获取指数数据失败: {str(e)}\n"
    
    try:
        from providers.market_data_fetcher import fetch_index_technical_indicators
        tech_indicators = fetch_index_technical_indicators(stock_name)
        
        if tech_indicators:
            tech_text = f"## 主要技术指标（{stock_name}）：\n"
            
            for key, value in tech_indicators.items():
                if isinstance(value, (int, float)):
                    formatted_value = round(float(value), 2)
                    tech_text += f"- {key}: {formatted_value}\n"
                elif isinstance(value, str):
                    tech_text += f"- {key}: {value}\n"
                elif isinstance(value, dict):
                    tech_text += f"- {key}:\n"
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, (int, float)):
                            formatted_sub_value = round(float(sub_value), 2)
                            tech_text += f"  • {sub_key}: {formatted_sub_value}\n"
                        else:
                            tech_text += f"  • {sub_key}: {sub_value}\n"
                elif isinstance(value, list):
                    if len(value) > 0 and isinstance(value[0], (int, float)):
                        formatted_values = [round(float(v), 2) for v in value[:3]]
                        tech_text += f"- {key}: {formatted_values}{'...' if len(value) > 3 else ''}\n"
                    else:
                        tech_text += f"- {key}: {value}\n"
                else:
                    tech_text += f"- {key}: {value}\n"
        else:
            tech_text = "## 主要技术指标：\n无法获取技术指标数据\n"
            
    except Exception as e:
        tech_text = f"## 主要技术指标：\n获取技术指标失败: {str(e)}\n"
    
    system_message = f"""你是一位资深的投资顾问和市场分析师。请基于市场综合数据、技术指标和用户观点，对{stock_name}（{stock_code}）当前的市场状况进行高度凝练的综合判断。

特别关注：
- 当前指数的涨跌情况及其反映的市场情绪
- 价格变动与技术面分析的一致性
- 实时表现与历史趋势的偏差
- 超短期（1-3天）的市场预测

请严格按照以下结构输出，内容务必精炼、聚焦决策：

## 📄 市场分析报告

1. **市场当前状况**：
- 用简明语言总结当前市场的核心特征、主要矛盾或机会（如趋势、估值、资金、政策等，择要突出）。
- 结合当前指数表现分析市场的即时情绪和资金动向。

2. **技术面与资金面环境**：
- 简要说明当前技术指标、流动性、政策环境对市场的影响（如趋势形态、成交量、融资情况等）。

3. **用户观点整合**：
- 如有用户观点，简要评价其合理性与风险点。

4. **后市涨跌可能性**：
- 结合上述，判断超短期（1-3天）、短期（1个月）和中期（3-6个月）涨跌概率及主要驱动因素。

5. **操作建议**：
- 针对不同风险偏好的投资者，分别给出具体操作建议（如仓位配置、板块选择、进出场时机等）。
- 特别提示：在市场大涨大跌、波动剧烈时，务必提醒用户避免因情绪波动而临时起意地操作，保持理性决策。

6. **风险提示**：
- 明确列出1-3个当前最需警惕的市场风险。

【要求】
- 全文不超过600字，避免冗余和重复。
- 只输出最有决策价值的内容，避免面面俱到。
- 结论要有明确的操作性。
- 必须考虑当前市场变动情况对投资决策的影响。
- 特别强调超短期（1-3天）的预测和操作建议。
- 如遇市场大幅波动，需特别提醒用户不要因情绪波动而冲动操作。
"""

    user_message = f"""基于以下数据，请对{stock_name}({stock_code})提供精简分析报告：

{market_report_text}

{indices_text}

{tech_text}"""

    if user_opinion and user_opinion.strip():
        user_message += f"""

**用户观点及关注点：**
{user_opinion.strip()}

请在分析中特别关注用户提到的观点和关注点，并针对性地给出建议。
"""
    
    with open(os.path.join(project_dir, "data", "cache", "req_market.txt"), "w", encoding="utf-8") as f:
        f.write(user_message)
    print(f'req length {len(user_message)}')
    # return user_message, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 注释掉调试返回

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
        
        return response, timestamp
        
    except Exception as e:
        error_msg = f"生成{stock_name}AI分析报告失败: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
