"""A股市场工具 - 统一的数据获取和缓存管理"""

import os
import sys
import warnings
from datetime import datetime
from typing import Dict
from typing import Dict, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

warnings.filterwarnings('ignore')

from market.market_data_fetcher import (
    fetch_current_indices,
    fetch_margin_data_unified,
    fetch_market_sentiment,
    fetch_comprehensive_market_sentiment,
    fetch_money_flow_data,
    fetch_valuation_data,
    fetch_index_technical_indicators
)
from market.market_data_cache import get_cache_manager
from utils.format_utils import judge_rsi_level
from utils.news_tools import get_market_news_caixin
from utils.string_utils import remove_markdown_format            

class MarketTools:
    """统一的市场数据工具类"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        """初始化市场工具"""
        self.cache_manager = get_cache_manager()
        self.cache_file = self.cache_manager.cache_file
        self.cache_configs = self.cache_manager.cache_configs
    
    def get_market_sentiment(self, use_cache: bool = True, force_refresh: bool = False, comprehensive: bool = False) -> Dict:
        """获取市场情绪指标
        
        Args:
            use_cache: 是否使用缓存
            force_refresh: 是否强制刷新
            comprehensive: 是否获取综合情绪分析（包含评分）
        """
        data_type = 'comprehensive_sentiment' if comprehensive else 'market_sentiment'
        
        if use_cache and not force_refresh and self.cache_manager.is_cache_valid(data_type):
            print(f"📋 使用缓存的{self.cache_configs.get(data_type, {}).get('description', '市场情绪数据')}")
            return self.cache_manager.get_cached_data(data_type)
        
        print(f"📡 获取{'综合市场情绪分析' if comprehensive else '基础市场情绪'}...")
        try:
            if comprehensive:
                ret, data = fetch_comprehensive_market_sentiment()
            else:
                ret, data = fetch_market_sentiment()
                
            if use_cache and ret:
                self.cache_manager.save_cached_data(data_type, data)
            return data
        except Exception as e:
            print(f"❌ 获取市场情绪失败: {e}")
            return self.cache_manager.get_cached_data(data_type) if use_cache else {}
    
    def get_valuation_data(self, use_cache: bool = True, force_refresh: bool = False) -> Dict:
        """获取估值指标"""
        data_type = 'valuation_data'
        
        if use_cache and not force_refresh and self.cache_manager.is_cache_valid(data_type):
            print(f"📋 使用缓存的{self.cache_configs[data_type]['description']}")
            return self.cache_manager.get_cached_data(data_type)
        
        print(f"📡 获取{self.cache_configs[data_type]['description']}...")
        try:
            ret, data = fetch_valuation_data()
            if use_cache and ret:
                self.cache_manager.save_cached_data(data_type, data)
            return data
        except Exception as e:
            print(f"❌ 获取估值数据失败: {e}")
            return self.cache_manager.get_cached_data(data_type) if use_cache else {}
    
    def get_index_valuation_data(self, index_name: str, use_cache: bool = True, force_refresh: bool = False) -> Dict:
        """根据指数名称获取对应的估值数据"""
        # 获取全部估值数据
        all_valuation_data = self.get_valuation_data(use_cache, force_refresh)
        
        if not all_valuation_data:
            return {}
        
        # 指数名称到数据key的映射 & 估值参考指数映射
        index_mapping = {
            # 直接支持估值数据的指数
            '沪深300': {
                'key_prefix': 'hs300',
                'reference_index': '沪深300',
                'description': '大盘蓝筹估值'
            },
            '中证500': {
                'key_prefix': 'zz500',
                'reference_index': '中证500', 
                'description': '中盘成长估值'
            },
            '中证1000': {
                'key_prefix': 'zz1000',
                'reference_index': '中证1000',
                'description': '小盘成长估值'
            },
            '中证2000': {
                'key_prefix': 'zz2000',
                'reference_index': '中证2000',
                'description': '小微盘估值'
            },
            '上证50': {
                'key_prefix': '上证50',
                'reference_index': '上证50',
                'description': '超大盘价值估值'
            },
            '科创50': {
                'key_prefix': '科创50',
                'reference_index': '科创50',
                'description': '科创板龙头估值'
            },
            # 需要映射的指数
            '创业板指': {
                'key_prefix': '科创50',
                'reference_index': '科创50',
                'description': '参考科创50（高科技成长股）'
            },
            '上证指数': {
                'key_prefix': 'hs300',
                'reference_index': '沪深300',
                'description': '参考沪深300（大盘蓝筹）'
            },
            '深证成指': {
                'key_prefix': 'zz500',
                'reference_index': '中证500',
                'description': '参考中证500（中盘成长）'
            },
            '北证50': {
                'key_prefix': 'zz1000',
                'reference_index': '中证1000',
                'description': '参考中证1000（小盘成长）'
            },
        }
        
        # 获取映射信息
        mapping_info = index_mapping.get(index_name)
        if not mapping_info:
            # 默认使用沪深300作为参考
            mapping_info = {
                'key_prefix': 'hs300',
                'reference_index': '沪深300',
                'description': '参考沪深300（大盘基准）'
            }
            print(f"⚠️ {index_name}暂无专门估值数据，使用沪深300估值作为参考")
        
        key_prefix = mapping_info['key_prefix']
        
        # 提取对应指数的估值数据
        index_valuation = {}
        for key, value in all_valuation_data.items():
            if key.startswith(key_prefix):
                # 转换为通用格式
                new_key = key.replace(key_prefix, 'index')
                index_valuation[new_key] = value
            elif key in ['update_time']:  # 保留时间信息
                index_valuation[key] = value
        
        # 如果没有找到对应数据，返回沪深300数据作为参考
        if not index_valuation and 'hs300_pe' in all_valuation_data:
            index_valuation = {
                'index_pe': all_valuation_data.get('hs300_pe'),
                'index_dividend_yield': all_valuation_data.get('hs300_dividend_yield'),
                'index_date': all_valuation_data.get('hs300_date'),
                'update_time': all_valuation_data.get('update_time'),
            }
            mapping_info = {
                'reference_index': '沪深300',
                'description': '参考沪深300（默认基准）'
            }
        
        # 添加映射信息
        if index_valuation:
            index_valuation['original_index'] = index_name
            index_valuation['reference_index'] = mapping_info['reference_index']
            index_valuation['valuation_description'] = mapping_info['description']
            
            # 标记是否为直接估值还是参考估值
            index_valuation['is_direct_valuation'] = (index_name == mapping_info['reference_index'])
        
        return index_valuation
    
    def get_money_flow_data(self, use_cache: bool = True, force_refresh: bool = False, debug: bool = False) -> Dict:
        """获取资金流向指标"""
        data_type = 'money_flow_data'
        
        if use_cache and not force_refresh and self.cache_manager.is_cache_valid(data_type):
            print(f"📋 使用缓存的{self.cache_configs[data_type]['description']}")
            return self.cache_manager.get_cached_data(data_type)
        
        print(f"📡 获取{self.cache_configs[data_type]['description']}...")
        try:
            ret, data = fetch_money_flow_data(debug=debug)
            if use_cache and ret:
                self.cache_manager.save_cached_data(data_type, data)
            return data
        except Exception as e:
            print(f"❌ 获取资金流向失败: {e}")
            return self.cache_manager.get_cached_data(data_type) if use_cache else {}
    
    def get_margin_data(self, use_cache: bool = True, force_refresh: bool = False) -> Dict:
        """获取融资融券数据"""
        data_type = 'margin_data'
        
        if use_cache and not force_refresh and self.cache_manager.is_cache_valid(data_type):
            print(f"📋 使用缓存的{self.cache_configs[data_type]['description']}")
            return self.cache_manager.get_cached_data(data_type)
        
        print(f"📡 获取{self.cache_configs[data_type]['description']}...")
        try:
            ret, data = fetch_margin_data_unified(include_historical=True)
            if use_cache and ret:
                self.cache_manager.save_cached_data(data_type, data)
            return data
        except Exception as e:
            print(f"❌ 获取融资融券失败: {e}")
            return self.cache_manager.get_cached_data(data_type) if use_cache else {}

    def get_current_indices(self, use_cache: bool = True, force_refresh: bool = False) -> Dict:
        """获取当前指数实时数据"""
        data_type = 'current_indices'
        
        if use_cache and not force_refresh and self.cache_manager.is_cache_valid(data_type):
            print(f"📋 使用缓存的{self.cache_configs[data_type]['description']}")
            return self.cache_manager.get_cached_data(data_type)
        
        print(f"📡 获取{self.cache_configs[data_type]['description']}...")
        try:
            ret, data = fetch_current_indices()
            if use_cache and ret:
                self.cache_manager.save_cached_data(data_type, data)
            return data
        except Exception as e:
            print(f"❌ 获取当前指数数据失败: {e}")
            return self.cache_manager.get_cached_data(data_type) if use_cache else {}

    def get_market_news_data(self, use_cache: bool = True, force_refresh: bool = False, debug: bool = False) -> Dict:
        """获取市场相关新闻数据"""
        data_type = 'market_news'
        
        if use_cache and not force_refresh and self.cache_manager.is_cache_valid(data_type):
            print(f"📋 使用缓存的市场新闻数据")
            return self.cache_manager.get_cached_data(data_type)
        
        print(f"📡 获取市场新闻数据...")
        try:
            ret, data = get_market_news_caixin(debug=debug)
            if use_cache and ret:
                self.cache_manager.save_cached_data(data_type, data)
            return data
        except Exception as e:
            print(f"❌ 获取市场新闻失败: {e}")
            return self.cache_manager.get_cached_data(data_type) if use_cache else {'error': str(e)}

    def get_index_current_price(self, index_name: str, use_cache: bool = True, force_refresh: bool = False) -> Dict:
        """获取单个指数的当前价格信息"""
        indices_data = self.get_current_indices(use_cache, force_refresh)
        
        if 'indices_dict' in indices_data and index_name in indices_data['indices_dict']:
            return indices_data['indices_dict'][index_name]
        else:
            print(f"❌ 未找到指数: {index_name}")
            return {}
        
    def get_index_technical_indicators(self, index_name: str, use_cache: bool = True, force_refresh: bool = False) -> Dict:
        """获取指数技术指标，优先查缓存，没有再fetch"""
        data_type = f'technical_indicators'
        
        if use_cache and not force_refresh and self.cache_manager.is_cache_valid(data_type, index_name):
            print(f"📋 使用缓存的技术指标: {index_name}")
            return self.cache_manager.get_cached_data(data_type, index_name)
        
        print(f"📡 获取技术指标: {index_name}...")
        try:
            ret, data = fetch_index_technical_indicators(index_name)
            print(f"📊 技术指标数据:")
            # 转换numpy类型为Python原生类型以便JSON序列化
            if data:
                data = self._convert_numpy_types(data)
            if use_cache and ret:
                self.cache_manager.save_cached_data(data_type, data, index_name)
            return data
        except Exception as e:
            print(f"❌ 获取技术指标失败: {e}")
            import traceback
            traceback.print_exc()
            return self.cache_manager.get_cached_data(data_type, index_name) if use_cache else {}

    def get_index_kline_data(self, index_name: str, period: int = 160, use_cache: bool = True, force_refresh: bool = False) -> Dict:
        """获取指数K线数据用于绘图
        
        Args:
            index_name: 指数名称，如'上证指数'
            period: 获取的数据条数
            use_cache: 是否使用缓存
            force_refresh: 是否强制刷新
            
        Returns:
            Dict: 包含K线数据的字典，格式为 {'kline_data': list, 'indicators': dict, 'error': str}
        """
        try:
            # 使用统一的K线数据管理器
            from market.kline_data_manager import get_kline_manager
            
            manager = get_kline_manager()
            df, from_cache = manager.get_index_kline_data(
                index_name, 
                period=period, 
                use_cache=use_cache, 
                force_refresh=force_refresh,
                for_technical_analysis=False
            )
            
            # 添加均线
            df = manager.add_moving_averages(df)
            
            # 获取技术指标
            indicators = self.get_index_technical_indicators(index_name, use_cache, force_refresh)
            
            # 确定数据来源
            data_source = 'cache' if from_cache else 'network'
            update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'kline_data': df.to_dict('records'),
                'indicators': indicators,
                'data_source': data_source,
                'update_time': update_time
            }
        except Exception as e:
            print(f"❌ 处理K线数据失败: {e}")
            return {'error': f"处理K线数据失败: {str(e)}"}

    def _add_moving_averages(self, df):
        """为DataFrame添加移动平均线（已废弃，使用KLineDataManager中的方法）"""
        try:
            from market.kline_data_manager import get_kline_manager
            manager = get_kline_manager()
            return manager.add_moving_averages(df)
        except Exception as e:
            print(f"❌ 计算均线失败: {e}")
            return df

    def _convert_numpy_types(self, data):
        """递归转换numpy类型为Python原生类型"""
        import numpy as np
        
        if isinstance(data, dict):
            return {key: self._convert_numpy_types(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_numpy_types(item) for item in data]
        elif isinstance(data, np.integer):
            return int(data)
        elif isinstance(data, np.floating):
            return float(data)
        elif isinstance(data, np.ndarray):
            return data.tolist()
        else:
            return data

    def get_ai_analysis(self, use_cache: bool = True, index_name: str = '上证指数', force_regenerate: bool = False, user_opinion: str = '') -> Dict:
        """获取AI分析数据"""
        data_type = 'ai_analysis'
        
        # 检查缓存是否有效且不需要强制重新生成
        if use_cache and self.cache_manager.is_cache_valid(data_type, index_name) and not force_regenerate:
            # 获取缓存数据并检查user_opinion是否一致
            cached_data = self.cache_manager.get_cached_data(data_type, index_name)
            cached_user_opinion = cached_data.get('user_opinion', '')
            
            # 如果user_opinion与缓存中的一致，则使用缓存
            if cached_user_opinion == user_opinion:
                print(f"📋 使用缓存的AI分析: {index_name}")
                return cached_data
            else:
                print(f"🔄 用户观点已变化，重新生成AI分析: {index_name}")
                print(f"   缓存观点: '{cached_user_opinion}' -> 当前观点: '{user_opinion}'")
        
        return self._generate_ai_analysis(index_name, user_opinion)
        
    def clear_cache(self, data_type: Optional[str] = None, index_name: str = None):
        self.cache_manager.clear_cache(data_type, index_name)
    
    def get_cache_status(self) -> Dict:
        return self.cache_manager.get_cache_status()
    
    def print_cache_status(self):
        self.cache_manager.print_cache_status()
    
    def refresh_all_cache(self):
        print("🔄 开始刷新所有缓存数据...")
        
        self.get_market_sentiment(use_cache=True, force_refresh=True)
        self.get_valuation_data(use_cache=True, force_refresh=True)
        self.get_money_flow_data(use_cache=True, force_refresh=True)
        self.get_margin_data(use_cache=True, force_refresh=True)
        self.get_current_indices(use_cache=True, force_refresh=True)
        self.get_market_news_data(use_cache=True, force_refresh=True)
        
        print("✅ 所有缓存数据刷新完成!")
        self.print_cache_status()
    
    def get_comprehensive_market_report(self, use_cache: bool = True, index_name: str = '上证指数') -> Dict:
        """获取综合市场报告"""
        print(f"📋 生成{index_name}综合市场报告...")
        print("=" * 60)
        
        report = {
            'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'focus_index': index_name,
            'technical_indicators': {},
            'sentiment_indicators': {},
            'valuation_indicators': {},
            'money_flow_indicators': {},
            'margin_detail': {},
            'market_news_data': {},
            'ai_analysis': {},
            'market_summary': {}
        }
        
        report['technical_indicators'] = self.get_index_technical_indicators(index_name, use_cache=use_cache)
        report['sentiment_indicators'] = self.get_market_sentiment(use_cache=use_cache, comprehensive=True)
        report['valuation_indicators'] = self.get_valuation_data(use_cache)
        report['money_flow_indicators'] = self.get_money_flow_data(use_cache)
        report['margin_detail'] = self.get_margin_data(use_cache)
        report['market_news_data'] = self.get_market_news_data(use_cache)
        
        print("=" * 60)
        print("✅ 综合市场报告生成完成!")
        
        return report
    
    def generate_market_report(self, report: Dict, format_type: str = 'summary', markdown: bool = True):
        """
        生成市场报告
        
        Args:
            report: 原始报告数据
            format_type: 报告格式类型
                - 'summary_formatted': 格式化的摘要markdown字符串
                - 'detailed': 详细字符串报告
                - 'text': 纯文本格式报告
            markdown: 对于detail格式，是否输出为Markdown格式
        
        Returns:
            Dict或str: 根据format_type返回不同格式的报告
        """
        if format_type == 'summary':
            return self._generate_summary_text(report)
        elif format_type == 'detail':
            return self._generate_detailed_text(report, markdown=markdown)
        else:
            raise ValueError(f"不支持的报告格式类型: {format_type}")
    
    def _generate_summary_text(self, report: Dict) -> str:
        """生成格式化的摘要markdown字符串"""
        summary = {}
        
        # 技术指标
        tech = report.get('technical_indicators', {})
        if tech:
            summary['technical_trend'] = f"{tech.get('ma_trend', '未知')} | MACD {tech.get('macd_trend', '未知')}"
            summary['rsi_level'] = judge_rsi_level(tech.get('rsi_14', 50))
        
        # 融资融券
        margin = report.get('margin_detail', {})
        if margin:
            margin_balance = margin.get('margin_buy_balance', 0)
            summary['margin_balance'] = f"融资余额 {margin_balance/100000000:.2f}亿"
        
        # 估值指标
        valuation = report.get('valuation_indicators', {})
        if valuation:
            pe = valuation.get('hs300_pe', 0)
            summary['valuation_level'] = f"沪深300 PE {pe:.2f}"
        
        # 资金流向
        money = report.get('money_flow_indicators', {})
        if money:
            m2_growth = money.get('m2_growth', 0)
            summary['liquidity_condition'] = f"M2同比增长 {m2_growth:.1f}%"
        
        markdown_lines = []
        
        dimension_map = {
            'technical_trend': ('📈', '技术面'),
            'margin_balance': ('💳', '融资面'), 
            'valuation_level': ('💰', '估值面'),
            'liquidity_condition': ('💸', '资金面'),
            'rsi_level': ('📊', 'RSI'),
        }
        
        for key, (icon, label) in dimension_map.items():
            if key in summary and summary[key]:
                markdown_lines.append(f"**{icon} {label}:** {summary[key]}")
        
        return '\n\n'.join(markdown_lines)
    
    def _generate_detailed_text(self, report: Dict, markdown: bool = False) -> str:
        """生成详细文本报告"""
        lines = []
        
        # 添加报告头部
        lines.extend(self._add_report_header(report, markdown))
        
        # 添加各个部分
        lines.extend(self._add_sentiment_section(report.get('sentiment_indicators', {}), markdown))
        lines.extend(self._add_valuation_section(report.get('valuation_indicators', {}), markdown))
        lines.extend(self._add_money_flow_section(report.get('money_flow_indicators', {}), markdown))
        lines.extend(self._add_margin_section(report.get('margin_detail', {}), markdown))
        lines.extend(self._add_news_section(report.get('market_news_data', {}), markdown))
        
        # 添加报告尾部
        lines.extend(self._add_report_footer(markdown))
        
        return '\n'.join(lines)
    
    def _add_report_header(self, report: Dict, markdown: bool) -> list:
        """添加报告头部"""
        lines = []
        if markdown:
            lines.append(f"\n# 📊 A股市场综合报告")
            lines.append(f"**🕐 报告时间:** {report['report_time']}")
            lines.append(f"**🎯 关注指数:** {report['focus_index']}")
            lines.append("\n---\n")
        else:
            lines.append(f"\n📊 A股市场综合报告")
            lines.append(f"🕐 报告时间: {report['report_time']}")
            lines.append(f"🎯 关注指数: {report['focus_index']}")
            lines.append("=" * 80)
        return lines
    
    def generate_sentiment_markdown(self, sentiment: Dict) -> str:
        """生成市场情绪分析的markdown文本（公开方法）"""
        return self._generate_sentiment_markdown(sentiment)
    
    def _generate_sentiment_markdown(self, sentiment: Dict) -> str:
        """生成市场情绪分析的markdown文本"""
        if not sentiment:
            return ""
        
        lines = []
        lines.append("## 😐 市场情绪指标")
        lines.append("")
        
        # 情绪评分部分
        if 'sentiment_score' in sentiment:
            score = sentiment.get('sentiment_score', 0)
            level = sentiment.get('sentiment_level', 'unknown')
            confidence = sentiment.get('confidence', 0)
            
            # 根据情绪等级设置显示
            if level == 'bullish':
                level_display = "🟢 乐观"
            elif level == 'bearish':
                level_display = "🔴 悲观"
            else:
                level_display = "🟡 中性"
            
            lines.append("### 📊 综合情绪评分")
            lines.append(f"- **情绪评分:** {score:.1f} 分 (范围: -100 到 100)")
            lines.append(f"- **情绪等级:** {level_display}")
            lines.append(f"- **数据可信度:** {confidence}%")
            lines.append("")
        
        # 基础涨跌数据概览 - 添加卡片式显示
        basic_sentiment = sentiment.get('basic_sentiment', sentiment)
        if basic_sentiment:
            up_stocks = basic_sentiment.get('up_stocks', 0)
            down_stocks = basic_sentiment.get('down_stocks', 0)
            flat_stocks = basic_sentiment.get('flat_stocks', 0)
            total_stocks = basic_sentiment.get('total_stocks', 0)
            limit_up = basic_sentiment.get('limit_up_stocks', 0)
            limit_down = basic_sentiment.get('limit_down_stocks', 0)
            
            # 涨跌数据概览表格
            lines.append("### 📊 市场涨跌概览")
            lines.append("")
            lines.append("| 指标 | 数量 | 占比 | 备注 |")
            lines.append("|------|------|------|------|")
            
            if total_stocks > 0:
                up_ratio = basic_sentiment.get('up_ratio', up_stocks / total_stocks)
                down_ratio = basic_sentiment.get('down_ratio', down_stocks / total_stocks)
                flat_ratio = flat_stocks / total_stocks if total_stocks > 0 else 0
                
                lines.append(f"| 🟢 上涨股票 | {up_stocks:,} 只 | {up_ratio:.1%} | 市场主流 |")
                lines.append(f"| 🔴 下跌股票 | {down_stocks:,} 只 | {down_ratio:.1%} | 调整压力 |")
                lines.append(f"| ⚪ 平盘股票 | {flat_stocks:,} 只 | {flat_ratio:.1%} | 观望态度 |")
                lines.append(f"| 📊 **总计** | **{total_stocks:,} 只** | **100.0%** | **全市场** |")
            
            # 涨跌停数据
            if limit_up > 0 or limit_down > 0:
                #lines.append("")
                limit_up_ratio = basic_sentiment.get('limit_up_ratio', 0)
                limit_down_ratio = basic_sentiment.get('limit_down_ratio', 0)
                lines.append(f"| 🔥 涨停股票 | {limit_up} 只 | {limit_up_ratio:.2%} | 强势信号 |")
                lines.append(f"| 💥 跌停股票 | {limit_down} 只 | {limit_down_ratio:.2%} | 恐慌信号 |")
            
            lines.append("")
        
        # 资金流向情绪
        fund_flow = sentiment.get('fund_flow', {})
        if fund_flow:
            lines.append("### 💸 资金流向情绪")
            main_inflow = fund_flow.get('main_net_inflow', 0)
            main_ratio = fund_flow.get('main_net_ratio', 0)
            
            if main_inflow or main_ratio:
                lines.append("")
                lines.append("| 资金指标 | 数值 | 说明 |")
                lines.append("|----------|------|------|")
                
                if main_inflow:
                    inflow_text = f"{main_inflow/1e8:.1f}亿"
                    flow_trend = "💰 净流入" if main_inflow > 0 else "💸 净流出"
                    lines.append(f"| 主力资金 | {inflow_text} | {flow_trend} |")
                
                if main_ratio:
                    ratio_trend = "活跃" if abs(main_ratio) > 0.5 else "平稳"
                    lines.append(f"| 流入占比 | {main_ratio:.2f}% | 资金{ratio_trend} |")
                
                lines.append("")
        
        # 情绪分析解读
        if 'sentiment_score' in sentiment:
            lines.append("### 🧠 情绪分析解读")
            lines.append("")
            
            # 评分构成分析
            if 'score_components' in sentiment:
                components = sentiment['score_components']
                lines.append("#### 📋 评分构成分析")
                lines.append("")
                
                for component, value in components.items():
                    if component == 'ratio':
                        desc = f"**涨跌比例贡献:** {value:.1f}分"
                        if value > 10:
                            desc += " - 🟢 上涨股票占优势，市场偏强"
                        elif value < -10:
                            desc += " - 🔴 下跌股票占优势，市场偏弱"
                        else:
                            desc += " - 🟡 涨跌相对均衡，市场震荡"
                    elif component == 'limit':
                        desc = f"**涨跌停贡献:** {value:.1f}分"
                        if value > 5:
                            desc += " - 🔥 涨停股票较多，情绪高涨"
                        elif value < -5:
                            desc += " - 💥 跌停股票较多，恐慌蔓延"
                        else:
                            desc += " - ⚖️ 涨跌停相对均衡"
                    elif component == 'fund':
                        desc = f"**资金流向贡献:** {value:.1f}分"
                        if value > 10:
                            desc += " - 💰 主力大幅净流入，资金追捧"
                        elif value < -10:
                            desc += " - 💸 主力大幅净流出，资金撤离"
                        else:
                            desc += " - 📊 资金流向相对平衡"
                    else:
                        desc = f"**{component}:** {value:.1f}分"
                    
                    lines.append(f"- {desc}")
                lines.append("")
            
            # 总体情绪判断 - 添加更详细的分析
            total_score = sentiment.get('sentiment_score', 0)
            lines.append("#### 🎯 总体情绪判断")
            lines.append("")
            
            if total_score > 30:
                lines.append("> 🚀 **市场情绪极度乐观**")
                lines.append(">")
                lines.append("> 多数指标显示积极信号，市场人气高涨，适合关注强势股票和热点板块。")
                lines.append("> 建议积极参与，但注意风险控制和适时止盈。")
            elif total_score > 10:
                lines.append("> 📈 **市场情绪偏乐观**")
                lines.append(">")
                lines.append("> 整体趋势向好，但需要注意潜在风险点。")
                lines.append("> 建议谨慎乐观，做好风险管理和仓位控制。")
            elif total_score > -10:
                lines.append("> 😐 **市场情绪中性**")
                lines.append(">")
                lines.append("> 多空力量相对均衡，市场处于震荡状态，等待明确方向。")
                lines.append("> 建议保持观望，等待更明确的趋势信号。")
            elif total_score > -30:
                lines.append("> 📉 **市场情绪偏悲观**")
                lines.append(">")
                lines.append("> 下跌压力较大，投资者信心不足，需要注意防守。")
                lines.append("> 建议降低仓位，关注防御性品种和超跌反弹机会。")
            else:
                lines.append("> 💥 **市场情绪极度悲观**")
                lines.append(">")
                lines.append("> 恐慌情绪浓厚，市场风险偏好极低，需要谨慎操作。")
                lines.append("> 建议以观望为主，等待市场企稳信号再考虑介入。")
        
        # 数据源信息
        basic_sentiment = sentiment.get('basic_sentiment', sentiment)
        data_source = basic_sentiment.get('data_source', '未知')
        update_time = sentiment.get('update_time', basic_sentiment.get('update_time', ''))
        if update_time:
            lines.append("")
            lines.append("---")
            lines.append(f"**📅 数据更新时间:** {update_time}")
            lines.append(f"**🔗 数据源:** {data_source}")
        
        return '\n'.join(lines)
    
    def _convert_markdown_to_text(self, markdown_text: str) -> list:
        """将markdown格式转换为纯文本格式，使用 string_utils 中的 remove_markdown_format"""
        # 使用现有的 remove_markdown_format 函数去除 markdown 格式
        plain_text = remove_markdown_format(markdown_text)
        
        # 转换为列表格式，保持基本的层级结构
        lines = []
        for line in plain_text.split('\n'):
            line = line.strip()
            
            # 为了保持某些结构，对特定内容进行简单格式化
            if line and any(keyword in line for keyword in ['市场情绪指标', '综合情绪评分', '涨跌统计', '涨跌比例', '涨跌停统计', '资金流向情绪', '情绪分析解读']):
                # 主要标题加上下划线
                lines.append(f"\n{line}")
                lines.append("-" * len(line))
            elif line.startswith('数据更新时间'):
                # 数据源信息保持原样
                lines.append(f"\n{line}")
            elif line:
                # 普通内容行
                lines.append(line)
            else:
                # 保留空行用于段落分隔
                lines.append('')
                
        return lines

    def _add_sentiment_section(self, sentiment: Dict, markdown: bool) -> list:
        """添加市场情绪部分"""
        lines = []
        
        if not sentiment:
            return lines
            
        # 使用新的markdown生成函数
        sentiment_text = self._generate_sentiment_markdown(sentiment)
        if sentiment_text:
            if markdown:
                lines.extend(sentiment_text.split('\n'))
            else:
                # 转换markdown格式为纯文本格式
                text_lines = self._convert_markdown_to_text(sentiment_text)
                lines.extend(text_lines)
        
        return lines
    
    def _add_valuation_section(self, valuation: Dict, markdown: bool) -> list:
        """添加估值水平部分"""
        lines = []
        if not valuation:
            return lines
            
        if markdown:
            lines.append(f"\n## 💰 估值水平")
            hs300_pe = valuation.get('hs300_pe', 'N/A')
            lines.append(f"- **沪深300 PE:** {hs300_pe:.2f}" if isinstance(hs300_pe, (int, float)) else f"- **沪深300 PE:** {hs300_pe}")
            dividend_yield = valuation.get('hs300_dividend_yield', 'N/A')
            lines.append(f"- **股息率:** {dividend_yield:.2f}%" if isinstance(dividend_yield, (int, float)) else f"- **股息率:** {dividend_yield}%")
        else:
            lines.append(f"\n💰 估值水平:")
            hs300_pe = valuation.get('hs300_pe', 'N/A')
            lines.append(f"   沪深300 PE: {hs300_pe:.2f}" if isinstance(hs300_pe, (int, float)) else f"   沪深300 PE: {hs300_pe}")
            dividend_yield = valuation.get('hs300_dividend_yield', 'N/A')
            lines.append(f"   股息率: {dividend_yield:.2f}%" if isinstance(dividend_yield, (int, float)) else f"   股息率: {dividend_yield}%")
        return lines
    
    def _add_money_flow_section(self, money: Dict, markdown: bool) -> list:
        """添加资金流向部分"""
        lines = []
        if not money:
            return lines
            
        if markdown:
            lines.append(f"\n## 💸 资金流向")
            m2_amount = money.get('m2_amount', 'N/A')
            lines.append(f"- **M2余额:** {m2_amount/10000:.2f}万亿" if isinstance(m2_amount, (int, float)) else f"- **M2余额:** {m2_amount}")
            m2_growth = money.get('m2_growth', 'N/A')
            lines.append(f"- **M2同比增长:** {m2_growth:.2f}%" if isinstance(m2_growth, (int, float)) else f"- **M2同比增长:** {m2_growth}%")
        else:
            lines.append(f"\n💸 资金流向:")
            m2_amount = money.get('m2_amount', 'N/A')
            lines.append(f"   M2余额: {m2_amount/10000:.2f}万亿" if isinstance(m2_amount, (int, float)) else f"   M2余额: {m2_amount}")
            m2_growth = money.get('m2_growth', 'N/A')
            lines.append(f"   M2同比增长: {m2_growth:.2f}%" if isinstance(m2_growth, (int, float)) else f"   M2同比增长: {m2_growth}%")
        return lines
    
    def _add_margin_section(self, margin_data: Dict, markdown: bool) -> list:
        """添加融资融券部分"""
        lines = []
        if not margin_data:
            return lines
            
        if markdown:
            lines.append(f"\n## 💳 融资融券")
            margin_balance = margin_data.get('margin_balance', 'N/A')
            lines.append(f"- **融资余额:** {margin_balance/100000000:.2f}亿" if isinstance(margin_balance, (int, float)) else f"- **融资余额:** {margin_balance}")
            
            margin_buy_balance = margin_data.get('margin_buy_balance', 'N/A')
            lines.append(f"- **融资买入:** {margin_buy_balance/100000000:.2f}亿" if isinstance(margin_buy_balance, (int, float)) else f"- **融资买入:** {margin_buy_balance}")
                
            change_ratio = margin_data.get('change_ratio', 'N/A')
            lines.append(f"- **周变化率:** {change_ratio:.2f}%" if isinstance(change_ratio, (int, float)) else f"- **周变化率:** {change_ratio}%")
        else:
            lines.append(f"\n💳 融资融券:")
            margin_balance = margin_data.get('margin_balance', 'N/A')
            lines.append(f"   融资余额: {margin_balance/100000000:.2f}亿" if isinstance(margin_balance, (int, float)) else f"   融资余额: {margin_balance}")
            
            margin_buy_balance = margin_data.get('margin_buy_balance', 'N/A')
            lines.append(f"   融资买入: {margin_buy_balance/100000000:.2f}亿" if isinstance(margin_buy_balance, (int, float)) else f"   融资买入: {margin_buy_balance}")
                
            change_ratio = margin_data.get('change_ratio', 'N/A')
            lines.append(f"   周变化率: {change_ratio:.2f}%" if isinstance(change_ratio, (int, float)) else f"   周变化率: {change_ratio}%")
        return lines
    
    def _add_news_section(self, news_data: Dict, markdown: bool) -> list:
        """添加市场新闻部分"""
        lines = []
        if not news_data or not news_data.get('market_news'):
            return lines
            
        market_news = news_data['market_news']
        news_summary = news_data.get('news_summary', {})
        
        # 添加新闻概况
        if markdown:
            lines.append(f"\n## 📰 市场资讯")
            lines.append(f"- **新闻数量:** {news_summary.get('total_market_news_count', len(market_news))}条")
            lines.append(f"- **数据源:** {news_summary.get('data_source', '财新网')}")
        else:
            lines.append(f"\n📰 市场资讯:")
            lines.append(f"   新闻数量: {news_summary.get('total_market_news_count', len(market_news))}条")
            lines.append(f"   数据源: {news_summary.get('data_source', '财新网')}")
        
        # 添加重要新闻列表
        if market_news:
            lines.extend(self._format_news_list(market_news[:10], markdown))
        return lines
    
    def _format_news_list(self, news_list: list, markdown: bool) -> list:
        """格式化新闻列表"""
        lines = []
        
        if markdown:
            lines.append(f"\n### 📄 重要资讯")
            for idx, news in enumerate(news_list):
                title = news.get('新闻标题', '无标题')
                time_info = news.get('发布时间', '')
                relative_time = news.get('相对时间', '')
                
                time_display = f"{time_info} ({relative_time})" if relative_time else time_info
                lines.append(f"{idx+1}. **{title}**")
                if time_display:
                    lines.append(f"   *发布时间: {time_display}*")
                
                # 添加新闻内容摘要
                content = news.get('新闻内容', '')
                if content:
                    content_preview = content[:100] + "..." if len(content) > 100 else content
                    lines.append(f"   {content_preview}")
                lines.append("")  # 空行分隔
        else:
            lines.append(f"\n   📄 重要资讯:")
            for idx, news in enumerate(news_list):
                title = news.get('新闻标题', '无标题')
                time_info = news.get('发布时间', '')
                relative_time = news.get('相对时间', '')
                
                time_display = f"{time_info} ({relative_time})" if relative_time else time_info
                lines.append(f"   {idx+1}. {title}")
                if time_display:
                    lines.append(f"      时间: {time_display}")
                
                # 添加新闻内容摘要
                content = news.get('新闻内容', '')
                if content:
                    content_preview = content[:100] + "..." if len(content) > 100 else content
                    lines.append(f"      摘要: {content_preview}")
                lines.append("")  # 空行分隔
        return lines
    
    def _add_report_footer(self, markdown: bool) -> list:
        """添加报告尾部"""
        lines = []
        if markdown:
            lines.append("\n---")
        else:
            lines.append("=" * 80)
        return lines
    
    def _generate_ai_analysis(self, index_name: str, user_opinion: str = '') -> Dict:
        """生成AI分析数据"""
        try:
            from market.market_ai_analysis import generate_index_analysis_report
            
            market_report_data = self.get_comprehensive_market_report(use_cache=True, index_name=index_name)
            
            print(f"🤖 OOOOOO 正在生成{index_name}的AI分析报告...")
            
            ret, ai_report, timestamp = generate_index_analysis_report(
                index_name,
                index_name, 
                market_report_data,
                user_opinion
            )
                        
            ai_data = {
                'report': ai_report,
                'timestamp': timestamp,
                'index_name': index_name,
                'user_opinion': user_opinion,
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            if ret:    
                self.cache_manager.save_cached_data('ai_analysis', ai_data, index_name)
            
            print(f"✅ AI分析报告生成完成")
            return ai_data
            
        except Exception as e:
            print(f"❌ 生成AI分析失败: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'index_name': index_name,
                'user_opinion': user_opinion
            }

# 全局市场工具实例
_market_tools = None

def get_market_tools() -> MarketTools:
    """获取全局市场工具实例"""
    global _market_tools
    if _market_tools is None:
        _market_tools = MarketTools()
    return _market_tools


if __name__ == "__main__":
    print("🧪 测试统一市场工具模块...")
    
    tools = get_market_tools()
    
    print("\n1. 显示缓存状态:")
    tools.print_cache_status()
        
    print("\n4. 显示更新后的缓存状态:")
    tools.print_cache_status()
    
    print("\n✅ 测试完成!")
