"""
股票AI分析工具
提供基于LLM的股票市场分析功能、筹码分析功能、新闻分析功能和基本面分析功能
"""

from typing import Dict, Any, List, Tuple
from llm.openai_client import OpenAIClient
import datetime

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
    
    # 获取近期价格数据
    recent_prices = df.tail(10)[['datetime', 'open', 'high', 'low', 'close', 'volume']].to_dict('records')
    
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
## 📊 股票基本信息
## 📈 技术指标分析
## 📉 价格趋势分析
## 💭 投资建议

请使用中文，基于真实数据进行分析。确保在分析中正确使用公司名称"{stock_name}"和股票代码"{stock_code}"。"""

    # 构建消息
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"""请基于以下数据对{stock_name}({stock_code})进行技术分析：

1. 最新交易日数据：
- 日期：{latest_data['datetime']}
- 开盘价：{latest_data['open']:.2f}
- 最高价：{latest_data['high']:.2f}
- 最低价：{latest_data['low']:.2f}
- 收盘价：{latest_data['close']:.2f}
- 成交量：{latest_data['volume']}
- 价格变化：{price_change:.2f}({price_change_pct:.2f}%)

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
            model_type="default"  # 使用默认分析模型
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
        for idx, news in enumerate(news_data[:10]):  # 只处理前10条
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
- 获利比例: {chip_data.get('profit_ratio', 0):.2f}%
- 平均成本: {chip_data.get('avg_cost', 0):.2f}元

**90%筹码分布:**
- 成本区间: {chip_data.get('cost_90_low', 0):.2f} - {chip_data.get('cost_90_high', 0):.2f}元
- 集中度: {chip_data.get('concentration_90', 0)*100:.2f}%

**70%筹码分布:**
- 成本区间: {chip_data.get('cost_70_low', 0):.2f} - {chip_data.get('cost_70_high', 0):.2f}元
- 集中度: {chip_data.get('concentration_70', 0)*100:.2f}%

**分析指标:**
- 获利状态: {chip_data.get('analysis', {}).get('profit_status', '未知')}
- 集中度状态: {chip_data.get('analysis', {}).get('concentration_status', '未知')}
- 风险水平: {chip_data.get('analysis', {}).get('risk_level', '未知')}

**技术参考位:**
- 支撑位: {chip_data.get('support_level', 0):.2f}元
- 阻力位: {chip_data.get('resistance_level', 0):.2f}元
- 成本中枢: {chip_data.get('cost_center', 0):.2f}元

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
        "股票代码": company_profile.symbol,
        "股票名称": company_profile.name,
        "净利润": company_profile.net_profit,
        "总市值": f"{company_profile.total_market_value:.2f}{currency_symbol}" if company_profile.total_market_value else None,
        "流通市值": f"{company_profile.circulating_market_value:.2f}{currency_symbol}" if company_profile.circulating_market_value else None,
        "所处行业": company_profile.industry,
        "市盈率(动)": company_profile.pe_ratio,
        "市净率": company_profile.pb_ratio,
        "ROE": company_profile.roe,
        "毛利率": company_profile.gross_profit_margin,
        "净利率": company_profile.net_profit_margin,
        "板块编号": company_profile.sector_code
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
