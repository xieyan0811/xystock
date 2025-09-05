"""
股票AI分析工具
提供基于LLM的股票市场分析功能、筹码分析功能、新闻分析功能和基本面分析功能
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from llm.openai_client import OpenAIClient
import datetime
import sys
import os
import traceback

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from utils.string_utils import remove_markdown_format
from providers.data_formatters import get_stock_formatter


@dataclass
class AnalysisResult:
    """AI分析结果的统一格式"""
    success: bool
    report: str
    timestamp: str
    error_message: Optional[str] = None
    analysis_type: str = ""
    stock_code: str = ""
    data_sources: Optional[List[Dict]] = None


class AnalysisConfig:
    """AI分析配置管理器"""
    
    def __init__(self):
        try:
            from config_manager import config
            self.config = config
        except Exception as e:
            print(f"加载配置失败，使用默认配置: {e}")
            self.config = None
    
    def get_analysis_config(self, analysis_type: str) -> Dict[str, Any]:
        """获取指定分析类型的配置"""
        if not self.config:
            return self._get_default_config(analysis_type)
        
        try:
            config_key = f"AI_ANALYSIS.{analysis_type.upper()}"
            return {
                'temperature': self.config.get(f'{config_key}.TEMPERATURE', 0.5),
                'model_type': self.config.get(f'{config_key}.MODEL_TYPE', 'default'),
                'max_length': self.config.get(f'{config_key}.MAX_LENGTH', 500),
                'cache_filename': self.config.get(f'{config_key}.CACHE_FILENAME', f'req_{analysis_type}.txt')
            }
        except Exception as e:
            print(f"获取{analysis_type}配置失败，使用默认配置: {e}")
            return self._get_default_config(analysis_type)
    
    def _get_default_config(self, analysis_type: str) -> Dict[str, Any]:
        """获取默认配置"""
        defaults = {
            'technical': {'temperature': 0.5, 'model_type': 'inference', 'max_length': 500, 'cache_filename': 'req_tech.txt'},
            'news': {'temperature': 0.7, 'model_type': 'default', 'max_length': 800, 'cache_filename': 'req_news.txt'},
            'chip': {'temperature': 0.5, 'model_type': 'default', 'max_length': 500, 'cache_filename': 'req_chip.txt'},
            'fundamental': {'temperature': 0.6, 'model_type': 'default', 'max_length': 500, 'cache_filename': 'req_basic_info.txt'},
            'comprehensive': {'temperature': 0.4, 'model_type': 'default', 'max_length': 800, 'cache_filename': 'req.txt'}
        }
        return defaults.get(analysis_type, defaults['comprehensive'])


class DataCollector:
    """数据收集器 - 负责收集各种分析所需的数据"""
    
    def __init__(self):
        self.formatter = get_stock_formatter()
    
    def collect_stock_basic_info(self, stock_identity: Dict[str, Any]) -> Tuple[str, Optional[Dict]]:
        """收集股票基本信息"""
        try:
            from providers.stock_data_tools import get_stock_tools
            stock_tools = get_stock_tools()
            basic_info = stock_tools.get_basic_info(stock_identity, use_cache=True)
            
            if basic_info and 'error' not in basic_info:
                formatted_info = self.formatter.format_basic_info(basic_info, stock_identity)
                data_source = {
                    'type': '股票基本信息',
                    'description': '包含当前价格、涨跌额、涨跌幅等实时数据',
                    'timestamp': basic_info.get('update_time', '未知时间')
                }
                return formatted_info, data_source
        except Exception as e:
            print(f"获取股票基本信息失败: {e}")
        
        return "", None
    
    def collect_historical_analyses(self, stock_code: str, stock_tools=None) -> Tuple[Dict[str, str], List[Dict]]:
        """收集历史分析数据"""
        historical_analyses = {}
        data_sources = []
        
        if not stock_tools:
            return historical_analyses, data_sources
        
        analysis_types = {
            'technical': '技术分析',
            'fundamental': '基本面分析',
            'news': '新闻分析',
            'chip': '筹码分析'
        }
        
        for analysis_type, description in analysis_types.items():
            try:
                cached_analysis = stock_tools.get_cached_ai_analysis(stock_code, analysis_type, use_cache=True)
                if cached_analysis and 'report' in cached_analysis:
                    historical_analyses[analysis_type] = cached_analysis['report']
                    data_sources.append({
                        'type': description,
                        'description': f'缓存的{description}报告',
                        'timestamp': cached_analysis.get('timestamp', '未知时间')
                    })
            except Exception as e:
                print(f"获取{description}失败: {e}")
        
        return historical_analyses, data_sources
    
    def collect_market_data(self, market_tools=None) -> Tuple[str, str, List[Dict]]:
        """收集市场数据"""
        market_report_text = ""
        market_ai_analysis = ""
        data_sources = []
        
        if not market_tools:
            try:
                from providers.market_data_tools import get_market_tools
                market_tools = get_market_tools()
            except Exception as e:
                print(f"导入market_tools失败: {e}")
                return market_report_text, market_ai_analysis, data_sources
        
        # 收集市场综合报告
        try:
            market_report = market_tools.get_comprehensive_market_report(use_cache=True)
            if market_report:
                data_sources.append({
                    'type': '市场综合报告',
                    'description': '包含技术指标、情绪、估值、资金流向等市场数据',
                    'timestamp': market_report.get('report_time', '未知时间')
                })
                market_report_text = market_tools.generate_market_report(market_report, format_type='summary')
        except Exception as e:
            print(f"获取市场综合报告失败: {e}")
        
        # 收集AI大盘分析
        try:
            market_ai_data = market_tools.get_ai_analysis(use_cache=True)
            if market_ai_data:
                if isinstance(market_ai_data, dict) and 'report' in market_ai_data:
                    market_ai_analysis = market_ai_data['report']
                data_sources.append({
                    'type': 'AI大盘分析',
                    'description': '基于AI模型的市场分析报告',
                    'timestamp': market_ai_data.get('analysis_time', '未知时间')
                })
        except Exception as e:
            print(f"获取大盘分析失败: {e}")
        
        return market_report_text, market_ai_analysis, data_sources
    
    def collect_user_profile(self) -> Tuple[str, str, List[Dict]]:
        """收集用户画像数据"""
        user_profile_section = ""
        user_mistakes_section = ""
        data_sources = []
        
        try:
            from config_manager import config
            
            # 用户画像
            user_profile_raw = config.get('USER_PROFILE.RAW', '').strip()
            if user_profile_raw:
                user_profile_section = f"\n# 用户画像\n{user_profile_raw}\n"
                data_sources.append({
                    'type': '用户画像',
                    'description': '用户的投资偏好、风险承受能力等信息',
                    'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # 用户常犯错误
            user_mistakes = config.get('USER_PROFILE.MISTAKES', '')
            if user_mistakes:
                user_mistakes_section = f"\n# 用户常犯错误\n{user_mistakes}\n"
                data_sources.append({
                    'type': '用户常犯错误',
                    'description': '用户在投资过程中常犯的错误和误区',
                    'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        except Exception as e:
            print(f"获取用户配置失败: {e}")
        
        return user_profile_section, user_mistakes_section, data_sources


class ReportFormatter:
    """报告格式化器 - 负责格式化各种数据为报告格式"""
    
    @staticmethod
    def format_historical_summary(historical_analyses: Dict[str, str], truncate_data: bool = False) -> str:
        """格式化历史分析摘要"""
        if not historical_analyses:
            return "\n\n## 📊 历史分析摘要\n未找到相关历史分析数据，将基于股票基本信息进行分析。\n"
        
        analysis_types = {
            'technical': '技术分析',
            'fundamental': '基本面分析',
            'news': '新闻分析',
            'chip': '筹码分析'
        }
        
        historical_summary = "\n\n# 📊 历史分析摘要\n"
        for analysis_type, report in historical_analyses.items():
            if truncate_data:
                summary = report[:300] + "..." if len(report) > 300 else report
            else:
                summary = report
            summary = remove_markdown_format(summary)
            historical_summary += f"\n## {analysis_types.get(analysis_type, analysis_type)}:\n\n{summary}\n"
        
        return historical_summary
    
    @staticmethod
    def format_market_summary(market_report_text: str, market_ai_analysis: str, truncate_data: bool = False) -> str:
        """格式化市场环境分析"""
        if not market_report_text and not market_ai_analysis:
            return "\n\n## 🌐 市场环境分析\n暂无市场环境数据。\n\n"
        
        market_summary = "\n\n# 🌐 市场环境分析\n"
        
        if market_report_text:
            market_text_summary = market_report_text[:500] + "..." if truncate_data and len(market_report_text) > 500 else market_report_text
            market_summary += f"\n## 市场综合报告:\n\n{market_text_summary}\n\n"
        
        if market_ai_analysis:
            ai_summary = market_ai_analysis[:300] + "..." if truncate_data and len(market_ai_analysis) > 300 else market_ai_analysis
            market_summary += f"\n### AI大盘分析:\n\n{ai_summary}\n\n"
        
        return market_summary
    
    @staticmethod
    def format_user_opinion_section(user_opinion: str, user_position: str) -> Tuple[str, List[Dict]]:
        """格式化用户观点部分"""
        user_opinion_section = ""
        data_sources = []
        
        if user_opinion.strip():
            user_opinion_section = f"\n# 用户观点\n{user_opinion.strip()}\n"
            data_sources.append({
                'type': '用户观点',
                'description': '用户提供的投资观点和看法',
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        if user_position and user_position.strip() and user_position.strip() != "不确定":
            user_opinion_section += f"\n# 用户当前持仓状态\n{user_position.strip()}\n"
            data_sources.append({
                'type': '用户持仓',
                'description': f'用户当前持仓状态：{user_position.strip()}',
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return user_opinion_section, data_sources


def _save_request_to_cache(content: str, filename: str):
    """保存请求内容到缓存文件"""
    try:
        cache_path = os.path.join(project_dir, "data", "cache", filename)
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"保存请求文件{filename}失败: {e}")


def _handle_analysis_error(error: Exception, analysis_type: str = "分析") -> Tuple[str, str]:
    """统一的错误处理"""
    error_msg = f"生成{analysis_type}报告失败: {str(error)}"
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return error_msg, timestamp


class BaseAnalysisGenerator:
    """基础分析生成器 - 提供通用的分析生成功能"""
    
    def __init__(self):
        self.client = OpenAIClient()
        self.config_manager = AnalysisConfig()
    
    def generate_analysis(self, analysis_type: str, messages: List[Dict], stock_code: str = "") -> AnalysisResult:
        """通用的分析生成方法"""
        config = self.config_manager.get_analysis_config(analysis_type)
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if len(messages) > 1:
            _save_request_to_cache(messages[1]['content'], config['cache_filename'])
        
        try:
            response = self.client.chat(
                messages=messages,
                temperature=config['temperature'],
                model_type=config['model_type']
            )
            
            return AnalysisResult(
                success=True,
                report=response,
                timestamp=timestamp,
                analysis_type=analysis_type,
                stock_code=stock_code
            )
            
        except Exception as e:
            error_msg = f"生成{analysis_type}分析报告失败: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            
            return AnalysisResult(
                success=False,
                report=error_msg,
                timestamp=timestamp,
                error_message=str(e),
                analysis_type=analysis_type,
                stock_code=stock_code
            )

def get_stock_info(stock_identity):
    from providers.stock_data_tools import get_stock_tools
    stock_tools = get_stock_tools()
    return stock_tools.get_basic_info(stock_identity, use_cache=True)

def generate_stock_analysis_report(
    stock_identity: Dict[str, Any],
    kline_info: Dict[str, Any] = None,
) -> AnalysisResult:
    """生成股票技术分析报告"""
    stock_code = stock_identity['code']
    stock_name = stock_identity.get('name', '')

    generator = BaseAnalysisGenerator()
    formatter = get_stock_formatter()
    basic_info_section = formatter.format_stock_overview(stock_identity, get_stock_info(stock_identity))
    kline_text = formatter.format_kline_data(kline_info)

    # 构建分析提示
    system_message = f"""你是一位专业的股票技术分析师。你必须对{stock_name}（股票代码：{stock_code}）进行详细的技术分析。

**股票信息：**
- 公司名称：{stock_name}
- 股票代码：{stock_code}
- 市场：{stock_identity.get('market_name', '未知')}
- 货币：{stock_identity.get('currency_name', '人民币')}({stock_identity.get('currency_symbol', '¥')})

**分析要求：**
1. 基于提供的真实数据进行技术分析
2. 分析移动平均线、MACD、RSI、布林带等技术指标
3. 考虑市场特点进行分析
4. 提供具体的数值和专业分析
5. 给出明确的投资建议
6. 重点关注当前股价变动对技术分析的影响

**输出格式：**
## 📈 技术指标分析
## 📉 价格趋势分析
## 💭 投资建议

请使用中文，基于真实数据进行分析。确保在分析中正确使用公司名称"{stock_name}"和股票代码"{stock_code}"。"""

    # 构建消息
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"""请基于以下数据对{stock_name}({stock_code})进行技术分析：

{basic_info_section}

{kline_text}

请进行详细分析，包括价格趋势、技术指标、支撑阻力位和投资建议。报告应不多于500字，必须基于数据做出专业的分析。请关注当前股价表现的影响。"""
        }
    ]

    return generator.generate_analysis("technical", messages, stock_code)


def generate_news_analysis_report(
    stock_identity: Dict[str, Any],
    news_data: List[Dict]
) -> AnalysisResult:
    """生成股票新闻分析报告"""
    stock_code = stock_identity['code']
    stock_name = stock_identity.get('name', '')

    generator = BaseAnalysisGenerator()
    formatter = get_stock_formatter()
    basic_info_section = formatter.format_stock_overview(stock_identity, get_stock_info(stock_identity))
    news_text = formatter.format_news_data(news_data, has_content=True)
    
    # 构建分析提示
    system_message = f"""您是一位专业的财经新闻分析师，负责分析最新的市场新闻和事件对股票价格的潜在影响。

**股票信息：**
- 公司名称：{stock_name}
- 股票代码：{stock_code}
- 所属市场：{stock_identity.get('market_name', '未知')}

您的主要职责包括：
1. 评估新闻事件的紧急程度和市场影响
2. 识别可能影响股价的关键信息
3. 分析新闻的时效性和可靠性
4. 提供基于新闻的交易建议和价格影响评估
5. 参考当前股价表现分析做出分析和预测

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

{basic_info_section}

=== 最新新闻数据 ===

{news_text}

请提供详细分析，包括：
1. 新闻事件的关键信息提取
2. 对股价的潜在影响分析
3. 投资建议和风险评估

报告应不超过800字，必须基于真实新闻数据做出专业的分析。如果新闻数据不足，请明确指出分析的局限性。"""
        }
    ]
    
    return generator.generate_analysis("news", messages, stock_code)
        
        
def generate_chip_analysis_report(
    stock_identity: Dict[str, Any],
    chip_data: Dict[str, Any]
) -> AnalysisResult:
    """生成筹码分析报告"""
    stock_code = stock_identity['code']
    stock_name = stock_identity.get('name', '')

    generator = BaseAnalysisGenerator()
    formatter = get_stock_formatter()
    basic_info_section = formatter.format_stock_overview(stock_identity, get_stock_info(stock_identity))
    chip_text = formatter.format_chip_data(chip_data)
    
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

{basic_info_section}

{chip_text}

请进行专业的筹码分析，包括主力行为判断、套牢盘分析、支撑压力位和交易建议。分析报告不超过500字。"""
        }
    ]
    
    return generator.generate_analysis("chip", messages, stock_code)


def generate_fundamental_analysis_report(
    stock_identity: Dict[str, Any],
    fundamental_data: Dict[str, Any]
) -> AnalysisResult:
    """生成股票基本面分析报告"""
    
    stock_code = stock_identity['code']
    stock_name = stock_identity.get('name', '')

    generator = BaseAnalysisGenerator()
    formatter = get_stock_formatter()
    basic_info_section = formatter.format_basic_info(fundamental_data, stock_identity)
    currency_name = stock_identity.get('currency_name', '人民币')
    currency_symbol = stock_identity.get('currency_symbol', '¥')
    
    system_message = f"""你是一位专业的股票基本面分析师，专注于{stock_identity.get('market_name', '股票市场')}。
你的任务是对{stock_name}（股票代码：{stock_code}）进行全面的基本面分析，提供专业、深入且客观的投资建议。

**股票信息：**
- 公司名称：{stock_name}
- 股票代码：{stock_code}
- 市场：{stock_identity.get('market_name', '未知')}
- 货币：{currency_name}({currency_symbol})

**基本面分析师职责：**
1. 财务健康评估：分析公司资产负债表、现金流和盈利能力
2. 估值分析：计算并解释PE、PB、PEG等关键估值指标
3. 增长潜力评估：分析营收和利润增长趋势、市场份额变化
4. 风险评估：识别财务、经营、行业和市场风险因素
5. 提供投资建议：基于基本面分析给出合理价值区间和投资建议

**分析输出格式：**
## 📊 基本面概况
## 💰 财务指标分析
## 📈 估值与增长分析
## ⚖️ 优势与风险分析
## 💎 投资建议

所有分析必须基于真实数据，严禁编造数据或主观臆测。价格区间和投资建议必须有明确依据。
所有货币单位必须使用{currency_name}（{currency_symbol}）。
投资建议必须使用中文：买入、持有或卖出，不要使用英文术语。"""

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"""请基于以下真实数据，对{stock_name}({stock_code})进行全面的基本面分析：

{basic_info_section}

请提供详细的基本面分析报告，包括：
1. 基本面概况和主营业务分析
2. 核心财务指标分析（盈利能力、偿债能力、成长性等）
3. 估值分析（PE、PB、PEG等指标与行业比较）
4. 优势与风险分析
5. 合理价值区间估算和投资建议

报告必须基于提供的真实数据，不要编造或假设。请使用专业、客观的语言，报告不超过500字。"""
        }
    ]

    return generator.generate_analysis("fundamental", messages, stock_code)



def generate_comprehensive_analysis_report(
    stock_identity: Dict[str, Any],
    user_opinion: str = "",
    user_position: str = "不确定",
    stock_tools=None,
    market_tools=None,
    truncate_data: bool = False
) -> AnalysisResult:
    """生成综合分析报告"""
    stock_code = stock_identity['code']
    stock_name = stock_identity.get('name', '')
    
    # 初始化数据收集器和格式化器
    collector = DataCollector()
    formatter = ReportFormatter()
    all_data_sources = []
    
    try:
        # 1. 收集股票基本信息
        basic_info_section, basic_info_source = collector.collect_stock_basic_info(stock_identity)
        if basic_info_source:
            all_data_sources.append(basic_info_source)
        
        # 2. 收集历史分析数据
        historical_analyses, historical_sources = collector.collect_historical_analyses(stock_code, stock_tools)
        all_data_sources.extend(historical_sources)
        
        # 如果没有历史分析数据，添加提示信息
        if not historical_analyses:
            all_data_sources.append({
                'type': '提示信息',
                'description': '未找到历史分析数据，将基于基本信息进行分析',
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # 3. 收集市场数据
        market_report_text, market_ai_analysis, market_sources = collector.collect_market_data(market_tools)
        all_data_sources.extend(market_sources)
        
        # 4. 收集用户画像数据
        user_profile_section, user_mistakes_section, user_sources = collector.collect_user_profile()
        all_data_sources.extend(user_sources)
        
        # 5. 格式化用户观点和持仓信息
        user_opinion_section, user_opinion_sources = formatter.format_user_opinion_section(user_opinion, user_position)
        all_data_sources.extend(user_opinion_sources)
        
        # 6. 格式化各部分内容
        historical_summary = formatter.format_historical_summary(historical_analyses, truncate_data)
        market_summary = formatter.format_market_summary(market_report_text, market_ai_analysis, truncate_data)
        
        # 7. 构建系统消息（保持原有内容）
        system_message = f"""你是一位资深的投资顾问和股票分析师。请基于AI已生成的各类分析（技术面、基本面、消息面、资金面、大盘分析）、股票实时价格信息和用户情况，对{stock_name}（{stock_code}）当前的投资价值进行高度凝练的综合判断。

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
- 请根据用户常犯的错误，根据当前行情，给出有针对性的提醒。
"""
        
        # 8. 构建用户消息
        user_message = f"""请对{stock_name}（{stock_code}）进行综合分析：

{basic_info_section}
{historical_summary}
{market_summary}
{user_profile_section}
{user_mistakes_section}
{user_opinion_section}

请基于以上信息，结合您的专业知识，给出一个综合的投资分析和建议。特别要关注当前市场环境对该股票的潜在影响。当前股价的涨跌情况也是重要的分析因素。"""
        
        # 9. 构建消息并生成分析
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        print(f'req length {len(user_message)}')
        
        # 使用统一的分析生成器
        generator = BaseAnalysisGenerator()
        result = generator.generate_analysis("comprehensive", messages, stock_code)
        result.data_sources = all_data_sources
        
        return result
        
    except Exception as e:
        # 统一的错误处理
        error_report = f"""# ❌ 综合分析生成失败

**错误信息:** {str(e)}

**时间:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 可能的解决方案：
1. 检查网络连接
2. 确认AI服务配置正确
3. 稍后重试

## 数据来源：
{len(all_data_sources)}个数据源已收集，但AI分析失败。"""
        
        # 记录详细错误信息
        print(f"生成综合分析报告失败: {e}")
        traceback.print_exc()
        
        return AnalysisResult(
            success=False,
            report=error_report,
            timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            error_message=str(e),
            analysis_type="comprehensive",
            stock_code=stock_code,
            data_sources=all_data_sources
        )
