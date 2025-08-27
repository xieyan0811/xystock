"""
股票AI分析工具
提供基于LLM的股票市场分析功能、筹码分析功能、新闻分析功能和基本面分析功能
"""

from typing import Dict, Any, List, Tuple
from llm.openai_client import OpenAIClient
import datetime
import sys
import os

# 添加项目根目录到Python路径
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from utils.format_utils import format_large_number, format_volume, format_market_value, format_price, format_percentage, format_change
from providers.market_data_tools import get_market_report

def generate_stock_analysis_report(
    stock_code: str,
    stock_name: str,
    market_info: Dict[str, Any],
    df,  # 移除类型注解，避免pd依赖
    indicators: Dict[str, Any] = None
) -> str:
    """
    生成股票技术分析报告
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        market_info: 市场信息
        df: K线数据DataFrame
        indicators: 技术指标数据
        
    Returns:
        str: 分析报告
    """
    # 初始化OpenAI客户端
    client = OpenAIClient()
    
    # 准备数据摘要
    latest_data = df.iloc[-1]
    
    # 计算最近价格变化
    if len(df) > 1:
        prev_close = df.iloc[-2]['close']
        price_change = latest_data['close'] - prev_close
        price_change_pct = (price_change / prev_close) * 100
    else:
        price_change = 0
        price_change_pct = 0
        
    # 提取技术指标数据
    indicators_data = {}
    if indicators:
        indicators_data = indicators
    
    # 构建分析提示
    system_message = f"""你是一位专业的股票技术分析师。你必须对{stock_name}（股票代码：{stock_code}）进行详细的技术分析。

**股票信息：**
- 公司名称：{stock_name}
- 股票代码：{stock_code}
- 市场：{market_info.get('market_name', '未知')}
- 货币：{market_info.get('currency_name', '人民币')}({market_info.get('currency_symbol', '¥')})

**分析要求：**
1. 基于提供的真实数据进行技术分析
2. 分析移动平均线、MACD、RSI、布林带等技术指标
3. 考虑市场特点进行分析
4. 提供具体的数值和专业分析
5. 给出明确的投资建议

**输出格式：**
## 📈 技术指标分析
## 📉 价格趋势分析
## 💭 投资建议

请使用中文，基于真实数据进行分析。确保在分析中正确使用公司名称"{stock_name}"和股票代码"{stock_code}"。"""

    # 构建消息
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"""请基于以下数据对{stock_name}({stock_code})进行技术分析：

1. 前一个交易日数据：
- 日期：{latest_data['datetime']}
- 开盘价：{format_price(latest_data['open'])}
- 最高价：{format_price(latest_data['high'])}
- 最低价：{format_price(latest_data['low'])}
- 收盘价：{format_price(latest_data['close'])}
- 成交量：{format_volume(latest_data['volume'])}
- 价格变化：{format_change(price_change, price_change_pct)}

2. 技术指标数据：
{indicators_data}

请进行详细分析，包括价格趋势、技术指标、支撑阻力位和投资建议。报告应不多于500字，必须基于数据做出专业的分析。"""
        }
    ]
    
    try:
        # 调用LLM生成分析报告
        response = client.chat(
            messages=messages,
            temperature=0.5,  # 使用较低的温度以保持输出一致性
            model_type="inference"  # 使用推理模型
        )
        
        return response
    except Exception as e:
        # 如果API调用失败，返回错误信息
        return f"生成分析报告失败: {str(e)}"


def generate_news_analysis_report(
    stock_code: str,
    stock_name: str,
    market_info: Dict[str, Any],
    news_data: List[Dict]
) -> Tuple[str, str]:
    """
    生成股票新闻分析报告
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        market_info: 市场信息
        news_data: 股票相关新闻数据
        
    Returns:
        Tuple[str, str]: (分析报告, 时间戳)
    """
    # 初始化OpenAI客户端
    client = OpenAIClient()
    
    # 准备新闻数据
    news_text = ""
    if news_data and len(news_data) > 0:
        for idx, news in enumerate(news_data):
            title = news.get('新闻标题', '')
            time = news.get('发布时间', '')
            content = news.get('新闻内容', '')
            url = news.get('新闻链接', '')
            
            news_text += f"新闻 {idx+1}：\n"
            news_text += f"标题: {title}\n"
            news_text += f"时间: {time}\n"
            if content:
                # 取内容的前200个字符作为摘要
                summary = content[:200] + ('...' if len(content) > 200 else '')
                news_text += f"内容摘要: {summary}\n"
            news_text += f"链接: {url}\n\n"
    else:
        news_text = f"未找到关于{stock_name}({stock_code})的新闻数据。"
    
    # 构建分析提示
    system_message = f"""您是一位专业的财经新闻分析师，负责分析最新的市场新闻和事件对股票价格的潜在影响。

**股票信息：**
- 公司名称：{stock_name}
- 股票代码：{stock_code}
- 所属市场：{market_info.get('market_name', '未知')}

您的主要职责包括：
1. 评估新闻事件的紧急程度和市场影响
2. 识别可能影响股价的关键信息
3. 分析新闻的时效性和可靠性
4. 提供基于新闻的交易建议和价格影响评估

重点关注的新闻类型：
- 财报发布和业绩指导
- 重大合作和并购消息
- 政策变化和监管动态
- 突发事件和危机管理
- 行业趋势和技术突破
- 管理层变动和战略调整

分析要点：
- 新闻的时效性（发布时间距离现在多久）
- 新闻的可信度（来源权威性）
- 市场影响程度（对股价的潜在影响）
- 投资者情绪变化（正面/负面/中性）

📊 价格影响分析要求：
- 评估新闻对股价的短期影响（1-3天）
- 分析可能的价格波动幅度（百分比）
- 提供基于新闻的价格调整建议

请用中文撰写分析报告，结构应包含：
## 📰 新闻概述
## 📊 关键信息分析
## 💹 市场影响评估
## 💡 投资建议"""

    # 构建消息
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"""请分析以下关于{stock_name}({stock_code})的最新新闻，评估其对股价的潜在影响：

=== 最新新闻数据 ===
{news_text}

请提供详细分析，包括：
1. 新闻事件的关键信息提取
2. 对股价的潜在影响分析
3. 投资建议和风险评估

报告应不多于800字，必须基于真实新闻数据做出专业的分析。如果新闻数据不足，请明确指出分析的局限性。"""
        }
    ]
    
    try:
        # 调用LLM生成分析报告
        response = client.chat(
            messages=messages,
            temperature=0.7,  # 使用适中的温度
            model_type="default"  # 使用默认分析模型
        )
        
        # 生成时间戳
        now = datetime.datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        
        return response, timestamp
    except Exception as e:
        # 如果API调用失败，返回错误信息
        return f"生成新闻分析报告失败: {str(e)}", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        
def generate_chip_analysis_report(
    stock_code: str,
    stock_name: str,
    chip_data: Dict[str, Any]
) -> Tuple[str, str]:
    """
    生成筹码分析报告
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        chip_data: 筹码分析数据
        
    Returns:
        Tuple[str, str]: (分析报告, 时间戳)
    """
    # 初始化OpenAI客户端
    client = OpenAIClient()
    
    # 构建分析提示
    system_message = """你是一位专业的筹码分析师，专精于A股市场的筹码分布技术分析。你能够深入解读筹码分布背后的主力意图、散户行为和市场博弈格局，为投资决策提供核心依据。

## 核心分析能力
1. **筹码分布解读**：分析单峰/双峰/多峰形态、筹码集中度、筹码迁移
2. **主力行为判断**：识别主力成本区间、控盘程度、获利状况
3. **支撑压力位**：通过筹码峰值确定关键支撑位和阻力位
4. **交易信号**：识别筹码分布变化带来的买入/卖出信号

## 分析方法
1. **主力成本乖离率** = (当前价-主力成本)/主力成本 × 100%
2. **散户套牢深度** = (最高套牢区价格-当前价)/当前价 × 100%
3. **筹码稳定指数** = 长期持有筹码占比
4. **异动转移率** = 近期筹码变动量/总筹码量

## 分析结构
1. 筹码分布概况
2. 主力行为画像
3. 压力支撑分析
4. 交易决策建议

请提供简明扼要、专业且实用的筹码分析，帮助投资者理解当前筹码状态和可能的市场走向。"""

    # 构建消息
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"""请对{stock_name}({stock_code})进行筹码分析，基于以下筹码数据：

**基础筹码数据:**
- 最新日期: {chip_data.get('latest_date', '未知')}
- 获利比例: {format_percentage(chip_data.get('profit_ratio', 0) * 100)}
- 平均成本: {format_price(chip_data.get('avg_cost', 0))}元

**90%筹码分布:**
- 成本区间: {format_price(chip_data.get('cost_90_low', 0))} - {format_price(chip_data.get('cost_90_high', 0))}元
- 集中度: {format_percentage(chip_data.get('concentration_90', 0)*100)}

**70%筹码分布:**
- 成本区间: {format_price(chip_data.get('cost_70_low', 0))} - {format_price(chip_data.get('cost_70_high', 0))}元
- 集中度: {format_percentage(chip_data.get('concentration_70', 0)*100)}

**分析指标:**
- 获利状态: {chip_data.get('analysis', {}).get('profit_status', '未知')}
- 集中度状态: {chip_data.get('analysis', {}).get('concentration_status', '未知')}
- 风险水平: {chip_data.get('analysis', {}).get('risk_level', '未知')}

**技术参考位:**
- 支撑位: {format_price(chip_data.get('support_level', 0))}元
- 阻力位: {format_price(chip_data.get('resistance_level', 0))}元
- 成本中枢: {format_price(chip_data.get('cost_center', 0))}元

请进行专业的筹码分析，包括主力行为判断、套牢盘分析、支撑压力位和交易建议。分析报告不超过500字。"""
        }
    ]
    
    try:
        # 调用LLM生成分析报告
        response = client.chat(
            messages=messages,
            temperature=0.5,  # 使用较低的温度以保持输出一致性
            model_type="default"  # 使用默认分析模型
        )
        
        # 生成时间戳
        now = datetime.datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        
        return response, timestamp
    except Exception as e:
        # 如果API调用失败，返回错误信息
        return f"生成筹码分析报告失败: {str(e)}", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def generate_fundamental_analysis_report(
    stock_code: str,
    stock_name: str,
    market_info: Dict[str, Any],
    fundamental_data: Dict[str, Any]
) -> Tuple[str, str]:
    """
    生成股票基本面分析报告
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        market_info: 市场信息
        fundamental_data: 基本面数据
        
    Returns:
        Tuple[str, str]: (分析报告, 时间戳)
    """

    # akshare里有几个取财报的接口，我还没实现

    # 初始化OpenAI客户端
    client = OpenAIClient()
    
    # 解析货币信息
    currency_name = market_info.get('currency_name', '人民币')
    currency_symbol = market_info.get('currency_symbol', '¥')
    
    # 提取核心财务指标
    company_profile = fundamental_data
    
    # 构建公司简介文本
    profile_text = "**公司简介:**\n"
    # 将StockInfo对象转换为字典形式
    stock_info_dict = {
        "股票代码": company_profile['symbol'],
        "股票名称": company_profile['name'],
        "净利润": format_large_number(company_profile['net_profit']) if company_profile['net_profit'] else None,
        "总市值": f"{format_market_value(company_profile['total_market_value'])}{currency_symbol}" if company_profile['total_market_value'] else None,
        "流通市值": f"{format_market_value(company_profile['circulating_market_value'])}{currency_symbol}" if company_profile['circulating_market_value'] else None,
        "所处行业": company_profile['industry'],
        "市盈率(动)": company_profile['pe_ratio'],
        "市净率": company_profile['pb_ratio'],
        "ROE": company_profile['roe'],
        "毛利率": company_profile['gross_profit_margin'],
        "净利率": company_profile['net_profit_margin'],
        "板块编号": company_profile['sector_code']
    }
    
    # 只显示有值的字段
    for key, value in stock_info_dict.items():
        if value is not None and str(value).strip() != "":
            profile_text += f"- {key}: {value}\n"
        
    # 构建分析提示
    system_message = f"""你是一位专业的股票基本面分析师，专注于{market_info.get('market_name', '股票市场')}。
你的任务是对{stock_name}（股票代码：{stock_code}）进行全面的基本面分析，提供专业、深入且客观的投资建议。

**股票信息：**
- 公司名称：{stock_name}
- 股票代码：{stock_code}
- 市场：{market_info.get('market_name', '未知')}
- 货币：{currency_name}({currency_symbol})

**基本面分析师职责：**
1. 财务健康评估：分析公司资产负债表、现金流和盈利能力
2. 估值分析：计算并解释PE、PB、PEG等关键估值指标
3. 增长潜力评估：分析营收和利润增长趋势、市场份额变化
4. 风险评估：识别财务、经营、行业和市场风险因素
5. 提供投资建议：基于基本面分析给出合理价值区间和投资建议

**分析输出格式：**
## 📊 公司基本面概况
## 💰 财务指标分析
## 📈 估值与增长分析
## ⚖️ 优势与风险分析
## 💎 投资建议

所有分析必须基于真实数据，严禁编造数据或主观臆测。价格区间和投资建议必须有明确依据。
所有货币单位必须使用{currency_name}（{currency_symbol}）。
投资建议必须使用中文：买入、持有或卖出，不要使用英文术语。"""

    # 构建消息
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"""请基于以下真实数据，对{stock_name}({stock_code})进行全面的基本面分析：

{profile_text}

请提供详细的基本面分析报告，包括：
1. 公司基本面概况和主营业务分析
2. 核心财务指标分析（盈利能力、偿债能力、成长性等）
3. 估值分析（PE、PB、PEG等指标与行业比较）
4. 优势与风险分析
5. 合理价值区间估算和投资建议

报告必须基于提供的真实数据，不要编造或假设。请使用专业、客观的语言，报告不超过500字。"""
        }
    ]
    
    try:
        # 调用LLM生成分析报告
        response = client.chat(
            messages=messages,
            temperature=0.6,  # 使用适中的温度以平衡一致性和创造性
            model_type="default"  # 使用默认分析模型
        )
        
        # 生成时间戳
        now = datetime.datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        
        return response, timestamp
    except Exception as e:
        # 如果API调用失败，返回错误信息
        return f"生成基本面分析报告失败: {str(e)}", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def generate_index_analysis_report( ## xieyan 250827
    stock_code: str,
    stock_name: str,
    market_report_data: Dict[str, Any]
):
    """
    生成指数AI分析报告（精简版）
    
    Args:
        stock_code: 指数代码
        stock_name: 指数名称
        market_report_data: 市场综合报告数据
        
    Returns:
        Tuple[str, str]: (分析报告, 时间戳)
    """
    # 初始化OpenAI客户端
    client = OpenAIClient()
    
    # 从market_tools模块导入报告格式化函数
    try:
        market_report_text = get_market_report(market_report_data, has_detail=True)
    except Exception as e:
        market_report_text = f"市场报告数据格式化失败: {str(e)}"
    
    # 构建分析提示（精简版）
    system_message = f"""您是一位资深的市场分析师，专门提供简洁高效的A股指数分析。

**要求：**
- 简洁明了，避免冗长描述
- 突出关键信号和核心结论
- 提供直接可执行的建议
- 控制总字数在800字以内

**分析框架：**
使用简短的段落和要点，重点关注实用性。"""

    user_message = f"""基于以下数据，请对{stock_name}({stock_code})提供精简分析报告：

{market_report_text}

**报告格式要求：**

## 📊 技术面（简述）
- 趋势状态：[多头/空头/震荡]
- 关键信号：[超买/超卖/中性] + [金叉/死叉]
- 重要位置：支撑___ | 阻力___

## 💭 情绪面（要点）
- 市场状态：[过热/冷静/平衡]
- 资金情况：融资余额及影响

## 💰 估值面（核心）
- PE水平：当前值及历史位置
- 投资价值：[高/中/低]

## 🏦 资金面（简要）
- 流动性：M1/M2增速要点
- 政策信号：对市场影响

## 🎯 操作建议
- 短期策略：[积极/谨慎/观望]
- 仓位建议：具体比例
- 关注要点：1-2个核心指标

## ⚠️ 风险提示
列出1-3个主要风险点

请保持内容精炼，每个部分2-3句话即可，总字数控制在800字以内。"""
    
    with open(os.path.join(project_dir, "data", "cache", "req_market.txt"), "w", encoding="utf-8") as f:
        f.write(user_message)
    print(f'req length {len(user_message)}')
    #return user_message, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # 调用OpenAI API
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        response = client.chat(
            messages=messages,
            temperature=0.3,  # 降低温度，确保输出更简洁一致
            model_type="default"
        )
        
        # 生成时间戳
        now = datetime.datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        
        return response, timestamp
    except Exception as e:
        # 如果API调用失败，返回错误信息
        return f"生成指数分析报告失败: {str(e)}", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def generate_comprehensive_analysis_report(
    stock_code: str,
    stock_name: str,
    user_opinion: str = "",
    stock_tools=None,
    market_tools=None,
    truncate_data: bool = False
) -> Tuple[str, List[Dict]]:
    """生成综合分析报告
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称  
        user_opinion: 用户观点
        stock_tools: 股票工具实例
        market_tools: 市场工具实例
        truncate_data: 是否截断数据，默认True。如果为False则使用全文数据
        
    Returns:
        Tuple[str, List[Dict]]: (分析报告, 数据来源列表)
    """
    # 初始化OpenAI客户端
    client = OpenAIClient()
    
    # 收集历史分析数据
    historical_analyses = {}
    data_sources = []
    
    # 获取股票基本信息（包含当前价格、涨跌额、涨跌幅）
    basic_info = {}
    if stock_tools:
        try:
            basic_info = stock_tools.get_stock_basic_info(stock_code, use_cache=True)
            if basic_info and 'error' not in basic_info:
                data_sources.append({
                    'type': '股票基本信息',
                    'description': '包含当前价格、涨跌额、涨跌幅等实时数据',
                    'timestamp': basic_info.get('update_time', '未知时间')
                })
        except Exception as e:
            print(f"获取股票基本信息失败: {e}")
    
    # 收集市场数据
    market_data = {}
    market_report_text = ""
    market_ai_analysis = ""
    
    # 如果没有传入market_tools，尝试导入并获取
    if market_tools is None:
        try:
            from providers.market_data_tools import get_market_tools
            market_tools = get_market_tools()
        except Exception as e:
            print(f"导入market_tools失败: {e}")
    
    # 获取市场数据
    if market_tools:
        try:
            # 获取综合市场报告
            market_report = market_tools.get_comprehensive_market_report(use_cache=True)
            if market_report:
                market_data['comprehensive_report'] = market_report
                data_sources.append({
                    'type': '市场综合报告',
                    'description': '包含技术指标、情绪、估值、资金流向等市场数据',
                    'timestamp': market_report.get('report_time', '未知时间')
                })
                market_report_text = get_market_report(market_report) # 单纯数据
                
        except Exception as e:
            print(f"获取市场综合报告失败: {e}")
        
        try:
            # 获取AI市场分析
            market_ai_data = market_tools.get_ai_analysis(use_cache=True)
            if market_ai_data:
                market_ai_analysis = market_ai_data # ai分析市场
                data_sources.append({
                    'type': 'AI市场分析',
                    'description': '基于AI模型的市场分析报告',
                    'timestamp': market_ai_data.get('analysis_time', '未知时间')
                })
        except Exception as e:
            print(f"获取AI市场分析失败: {e}")
    
    try:
        if stock_tools:
            # 尝试获取各种历史分析结果
            analysis_types = {
                'technical': '技术分析',
                'fundamental': '基本面分析', 
                'news': '新闻分析',
                'chip': '筹码分析'
            }
            
            for analysis_type, description in analysis_types.items():
                try:
                    cached_analysis = stock_tools.get_ai_analysis(stock_code, analysis_type, use_cache=True)
                    if cached_analysis and 'report' in cached_analysis:
                        historical_analyses[analysis_type] = cached_analysis['report']
                        data_sources.append({
                            'type': description,
                            'description': f'缓存的{description}报告',
                            'timestamp': cached_analysis.get('timestamp', '未知时间')
                        })
                except Exception as e:
                    print(f"获取{description}失败: {e}")
                    continue
        
        # 如果没有历史分析数据，添加提示
        if not historical_analyses:
            data_sources.append({
                'type': '提示信息',
                'description': '未找到历史分析数据，将基于基本信息进行分析',
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
    
    except Exception as e:
        print(f"收集历史分析数据时出错: {e}")
        data_sources.append({
            'type': '错误信息',
            'description': f'收集历史数据时出错: {str(e)}',
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # 构建历史分析摘要
    historical_summary = ""
    if historical_analyses:
        historical_summary = "\n\n# 📊 历史分析摘要\n"
        for analysis_type, report in historical_analyses.items():
            # 根据truncate_data参数决定是否截断数据
            if truncate_data:
                # 提取报告的关键信息（前300字符作为摘要）
                summary = report[:300] + "..." if len(report) > 300 else report
            else:
                # 使用全文
                summary = report
            historical_summary += f"\n## {analysis_types.get(analysis_type, analysis_type)}:\n{summary}\n"
    else:
        historical_summary = "\n\n## 📊 历史分析摘要\n未找到相关历史分析数据，将基于股票基本信息进行分析。\n"
    
    # 构建市场数据摘要
    market_summary = ""
    if market_report_text or market_ai_analysis:
        market_summary = "\n\n# 🌐 市场环境分析\n"
        
        if market_report_text:
            # 根据truncate_data参数决定是否截断市场报告
            if truncate_data:
                # 截取市场报告的关键部分（前500字符）
                market_text_summary = market_report_text[:500] + "..." if len(market_report_text) > 500 else market_report_text
            else:
                # 使用全文
                market_text_summary = market_report_text
            market_summary += f"\n## 市场综合报告:\n{market_text_summary}\n"
        
        if market_ai_analysis:
            # 如果有AI市场分析，添加其内容
            if isinstance(market_ai_analysis, dict) and 'analysis' in market_ai_analysis:
                ai_text = market_ai_analysis['analysis']
                if truncate_data:
                    ai_summary = ai_text[:300] + "..." if len(ai_text) > 300 else ai_text
                else:
                    ai_summary = ai_text
                market_summary += f"\n## AI市场分析:\n{ai_summary}\n"
            elif isinstance(market_ai_analysis, str):
                if truncate_data:
                    ai_summary = market_ai_analysis[:300] + "..." if len(market_ai_analysis) > 300 else market_ai_analysis
                else:
                    ai_summary = market_ai_analysis
                market_summary += f"\n### AI市场分析:\n{ai_summary}\n"
    else:
        market_summary = "\n\n## 🌐 市场环境分析\n暂无市场环境数据。\n"
    
    # 构建股票基本信息部分
    basic_info_section = ""
    if basic_info and 'error' not in basic_info:
        current_price = basic_info.get('current_price', 0)
        change = basic_info.get('change', 0)
        change_percent = basic_info.get('change_percent', 0)
        stock_name_info = basic_info.get('name', stock_name)
        
        # 判断涨跌情况
        
        basic_info_section = f"""\n\n# 💹 股票实时信息
- 股票名称：{stock_name_info}（{stock_code}）
- 当前价格：{current_price:.2f}元
- 涨跌金额：{change:+.2f}元
- 涨跌幅度：{change_percent:+.2f}%
- 更新时间：{basic_info.get('timestamp', '未知')}\n"""
    else:
        basic_info_section = f"\n\n# 💹 股票实时信息\n暂无{stock_name}（{stock_code}）的实时价格信息。\n"
    
    # 构建用户观点部分
    user_opinion_section = ""
    if user_opinion.strip():
        user_opinion_section = f"\n\n# 👤 用户观点\n{user_opinion.strip()}\n"
        data_sources.append({
            'type': '用户观点',
            'description': '用户提供的投资观点和看法',
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # 构建分析提示
    system_message = f"""你是一位资深的投资顾问和股票分析师。请基于AI已生成的各类分析（技术面、基本面、消息面、资金面、大盘分析）、股票实时价格信息和用户观点，对{stock_name}（{stock_code}）当前的投资价值进行高度凝练的综合判断。

特别关注：
- 当前股价的涨跌情况及其反映的市场情绪
- 价格变动与技术面、基本面分析的一致性
- 实时表现与历史分析预期的偏差

请严格按照以下结构输出，内容务必精炼、聚焦决策：

## 📄 综合分析报告

1. **个股当前状况**：
- 用简明语言总结该股当前的核心优劣势、主要矛盾或机会（如趋势、估值、资金、消息等，择要突出）。
- 结合当前价格表现分析市场对该股的即时反应。

2. **大盘与行业环境**：
- 简要说明当前大盘和行业对该股的影响（如大盘趋势、流动性、板块轮动等）。

3. **用户观点整合**：
- 如有用户观点，简要评价其合理性与风险点。

4. **后市涨跌可能性**：
- 结合上述，判断短期（1个月）和中期（3-6个月）涨跌概率及主要驱动因素。

5. **操作建议**：
- 针对有仓位和无仓位两类投资者，分别给出具体操作建议（如持有、加仓、减仓、观望、买入区间等）。

6. **风险提示**：
- 明确列出1-3个当前最需警惕的风险。

【要求】
- 全文不超过800字，避免冗余和重复。
- 只输出最有决策价值的内容，避免面面俱到。
- 结论要有明确的操作性。
- 必须考虑当前价格变动情况对投资决策的影响。
"""

    # 构建用户消息
    user_message = f"""请对{stock_name}（{stock_code}）进行综合分析：

{basic_info_section}
{historical_summary}
{market_summary}
{user_opinion_section}

请基于以上信息，结合您的专业知识，给出一个综合的投资分析和建议。特别要关注当前市场环境对该股票的潜在影响。当前股价的涨跌情况也是重要的分析因素。"""

    # 把 user_message 写入 data/cache/req.txt
    with open("data/cache/req.txt", "w", encoding="utf-8") as f:
        f.write(user_message)
    print(f'req length {len(user_message)}')
    #return user_message, data_sources # for test

    try:
        # 调用OpenAI API
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        response = client.chat(
            messages=messages,
            temperature=0.4,  # 适中的创造性，保持客观性
            model_type="default"
        )
        
        return response, data_sources
        
    except Exception as e:
        # 如果API调用失败，返回错误信息
        error_report = f"""# ❌ 综合分析生成失败

**错误信息:** {str(e)}

**时间:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 可能的解决方案：
1. 检查网络连接
2. 确认AI服务配置正确
3. 稍后重试

## 数据来源：
{len(data_sources)}个数据源已收集，但AI分析失败。"""
        
        return error_report, data_sources
