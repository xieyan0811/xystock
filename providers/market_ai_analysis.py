from typing import Dict, Any, Tuple
from llm.openai_client import OpenAIClient
import datetime
import sys
import os

# 添加项目根目录到Python路径
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from providers.market_data_tools import get_market_tools

def generate_index_analysis_report( ## xieyan 250827
    stock_code: str,
    stock_name: str,
    market_report_data: Dict[str, Any],
    user_opinion: str = ''
) -> Tuple[str, str]:
    """
    生成指数AI分析报告（包含超短期预测）
    
    Args:
        stock_code: 指数代码
        stock_name: 指数名称
        market_report_data: 市场综合报告数据
        user_opinion: 用户观点
        
    Returns:
        Tuple[str, str]: (分析报告, 时间戳)
    """
    # 初始化OpenAI客户端
    client = OpenAIClient()
    
    # 从market_tools模块导入报告格式化函数
    try:
        market_tools = get_market_tools()
        market_report_text = market_tools.generate_market_report(market_report_data, 
                                                                 format_type='detail', 
                                                                 markdown=False)
    except Exception as e:
        market_report_text = f"市场报告数据格式化失败: {str(e)}"
    
    # 获取当前市场指数数据（只保留指定指数）
    try:
        current_indices = market_tools.get_current_indices(use_cache=True, force_refresh=False)
        indices_text = "## 当前市场指数情况：\n"
        # 只保留指定的指数
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
    
    # 获取主要指数的技术指标（MACD, RSI等）- 格式化后传给AI
    try:
        from providers.market_data_fetcher import fetch_index_technical_indicators
        tech_indicators = fetch_index_technical_indicators(stock_name)
        
        if tech_indicators:
            tech_text = f"## 主要技术指标（{stock_name}）：\n"
            
            # 格式化技术指标数据，让其更易读
            for key, value in tech_indicators.items():
                if isinstance(value, (int, float)):
                    # 数值型数据保留2位小数
                    formatted_value = round(float(value), 2)
                    tech_text += f"- {key}: {formatted_value}\n"
                elif isinstance(value, str):
                    # 字符串直接显示
                    tech_text += f"- {key}: {value}\n"
                elif isinstance(value, dict):
                    # 嵌套字典数据
                    tech_text += f"- {key}:\n"
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, (int, float)):
                            formatted_sub_value = round(float(sub_value), 2)
                            tech_text += f"  • {sub_key}: {formatted_sub_value}\n"
                        else:
                            tech_text += f"  • {sub_key}: {sub_value}\n"
                elif isinstance(value, list):
                    # 列表数据
                    if len(value) > 0 and isinstance(value[0], (int, float)):
                        # 数值列表，只显示前几个值
                        formatted_values = [round(float(v), 2) for v in value[:3]]
                        tech_text += f"- {key}: {formatted_values}{'...' if len(value) > 3 else ''}\n"
                    else:
                        tech_text += f"- {key}: {value}\n"
                else:
                    # 其他类型数据
                    tech_text += f"- {key}: {value}\n"
        else:
            tech_text = "## 主要技术指标：\n无法获取技术指标数据\n"
            
    except Exception as e:
        tech_text = f"## 主要技术指标：\n获取技术指标失败: {str(e)}\n"
    
    # 构建分析提示（参考综合分析报告的prompt）
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

6. **风险提示**：
- 明确列出1-3个当前最需警惕的市场风险。

【要求】
- 全文不超过600字，避免冗余和重复。
- 只输出最有决策价值的内容，避免面面俱到。
- 结论要有明确的操作性。
- 必须考虑当前市场变动情况对投资决策的影响。
- 特别强调超短期（1-3天）的预测和操作建议。
"""

    user_message = f"""基于以下数据，请对{stock_name}({stock_code})提供精简分析报告：

{market_report_text}

{indices_text}

{tech_text}"""

    # 如果有用户观点，添加到prompt中
    if user_opinion and user_opinion.strip():
        user_message += f"""

**用户观点及关注点：**
{user_opinion.strip()}

请在分析中特别关注用户提到的观点和关注点，并针对性地给出建议。
"""
    
    # 保存请求到文件（用于调试）
    with open(os.path.join(project_dir, "data", "cache", "req_market.txt"), "w", encoding="utf-8") as f:
        f.write(user_message)
    print(f'req length {len(user_message)}')
    # return user_message, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 注释掉调试返回

    try:
        # 调用OpenAI API
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        response = client.chat(
            messages=messages,
            temperature=0.3,  # 降低温度，确保输出更简洁一致
            model_type="inference"
        )
        
        # 生成时间戳
        now = datetime.datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        
        return response, timestamp
        
    except Exception as e:
        # 如果API调用失败，返回错误信息
        error_msg = f"生成{stock_name}AI分析报告失败: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    

