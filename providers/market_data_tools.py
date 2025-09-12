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

from providers.market_data_fetcher import (
    fetch_current_indices,
    fetch_margin_data_unified,
    fetch_market_sentiment,
    fetch_money_flow_data,
    fetch_valuation_data,
    fetch_index_technical_indicators
)
from providers.market_data_cache import get_cache_manager            

class MarketTools:
    """统一的市场数据工具类"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        """初始化市场工具"""
        self.cache_manager = get_cache_manager()
        self.cache_file = self.cache_manager.cache_file
        self.cache_configs = self.cache_manager.cache_configs
    
    def get_market_sentiment(self, use_cache: bool = True, force_refresh: bool = False) -> Dict:
        """获取市场情绪指标"""
        data_type = 'market_sentiment'
        
        if use_cache and not force_refresh and self.cache_manager.is_cache_valid(data_type):
            print(f"📋 使用缓存的{self.cache_configs[data_type]['description']}")
            return self.cache_manager.get_cached_data(data_type)
        
        print(f"📡 获取{self.cache_configs[data_type]['description']}...")
        try:
            data = fetch_market_sentiment()
            if use_cache:
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
            data = fetch_valuation_data()
            if use_cache:
                self.cache_manager.save_cached_data(data_type, data)
            return data
        except Exception as e:
            print(f"❌ 获取估值数据失败: {e}")
            return self.cache_manager.get_cached_data(data_type) if use_cache else {}
    
    def get_money_flow_data(self, use_cache: bool = True, force_refresh: bool = False, debug: bool = False) -> Dict:
        """获取资金流向指标"""
        data_type = 'money_flow_data'
        
        if use_cache and not force_refresh and self.cache_manager.is_cache_valid(data_type):
            print(f"📋 使用缓存的{self.cache_configs[data_type]['description']}")
            return self.cache_manager.get_cached_data(data_type)
        
        print(f"📡 获取{self.cache_configs[data_type]['description']}...")
        try:
            data = fetch_money_flow_data(debug=debug)
            if use_cache:
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
            data = fetch_margin_data_unified(include_historical=True)
            if use_cache:
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
            data = fetch_current_indices()
            if use_cache:
                self.cache_manager.save_cached_data(data_type, data)
            return data
        except Exception as e:
            print(f"❌ 获取当前指数数据失败: {e}")
            return self.cache_manager.get_cached_data(data_type) if use_cache else {}

    def get_index_current_price(self, index_name: str, use_cache: bool = True, force_refresh: bool = False) -> Dict:
        """获取单个指数的当前价格信息"""
        indices_data = self.get_current_indices(use_cache, force_refresh)
        
        if 'indices_dict' in indices_data and index_name in indices_data['indices_dict']:
            return indices_data['indices_dict'][index_name]
        else:
            print(f"❌ 未找到指数: {index_name}")
            return {}
        
    def get_ai_analysis(self, use_cache: bool = True, index_name: str = '上证指数', force_regenerate: bool = False, user_opinion: str = '') -> Dict:
        """获取AI分析数据"""
        data_type = 'ai_analysis'
                
        if use_cache and self.cache_manager.is_cache_valid(data_type) and not force_regenerate:
            print(f"📋 使用缓存的{self.cache_configs[data_type]['description']}")
            return self.cache_manager.get_cached_data(data_type)
        
        return self._generate_ai_analysis(index_name, user_opinion)
        
    def clear_cache(self, data_type: Optional[str] = None):
        self.cache_manager.clear_cache(data_type)
    
    def get_cache_status(self) -> Dict:
        return self.cache_manager.get_cache_status()
    
    def print_cache_status(self):
        self.cache_manager.print_cache_status()
    
    def refresh_all_cache(self):
        print("🔄 开始刷新所有缓存数据...")
        
        #self.get_market_sentiment(use_cache=True, force_refresh=True)
        self.get_valuation_data(use_cache=True, force_refresh=True)
        self.get_money_flow_data(use_cache=True, force_refresh=True)
        self.get_margin_data(use_cache=True, force_refresh=True)
        self.get_current_indices(use_cache=True, force_refresh=True)
        
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
            'ai_analysis': {},
            'market_summary': {}
        }
        
        report['technical_indicators'] = fetch_index_technical_indicators(index_name)
        report['valuation_indicators'] = self.get_valuation_data(use_cache)
        report['money_flow_indicators'] = self.get_money_flow_data(use_cache)
        report['margin_detail'] = self.get_margin_data(use_cache)
        
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
        
        tech = report['technical_indicators']
        if tech:
            summary['technical_trend'] = f"{tech.get('ma_trend', '未知')} | MACD {tech.get('macd_trend', '未知')}"
            #summary['current_price'] = tech.get('latest_close', 0)
            summary['rsi_level'] = self._judge_rsi_level(tech.get('rsi_14', 50))
        
        margin = report['margin_detail']
        if margin:
            summary['margin_balance'] = f"融资余额 {margin.get('margin_buy_balance', 0)/100000000:.2f}亿"
        
        valuation = report['valuation_indicators']
        if valuation:
            pe = valuation.get('hs300_pe', 0)
            summary['valuation_level'] = f"沪深300 PE {pe:.2f}"
        
        money = report['money_flow_indicators']
        if money:
            m2_growth = money.get('m2_growth', 0)
            summary['liquidity_condition'] = f"M2同比增长 {m2_growth:.1f}%"
        
        markdown_lines = []
        
        dimension_map = {
            'technical_trend': ('📈', '技术面'),
            'margin_balance': ('💳', '融资面'),
            'valuation_level': ('💰', '估值面'),
            'liquidity_condition': ('💸', '资金面'),
            'money_flow_indicators': ('💵', '资金流向'),
            'rsi_level': ('📊', 'RSI'),
            #'current_price': ('💹', '当前价格')
        }
        
        for key, (icon, label) in dimension_map.items():
            if key in summary and summary[key]:
                markdown_lines.append(f"**{icon} {label}:** {summary[key]}")
        
        return '\n\n'.join(markdown_lines)
    
    def _generate_detailed_text(self, report: Dict, markdown: bool = False) -> str:
        """生成详细文本报告"""
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
        
        tech = report['technical_indicators']
        if tech:
            if markdown:
                lines.append(f"\n## 📈 技术指标分析")
                lines.append(f"- **MA趋势:** {tech.get('ma_trend', 'N/A')}")
                lines.append(f"- **MACD趋势:** {tech.get('macd_trend', 'N/A')}")
                rsi_14 = tech.get('rsi_14', 'N/A')
                if isinstance(rsi_14, (int, float)):
                    lines.append(f"- **RSI(14):** {rsi_14:.2f}")
                else:
                    lines.append(f"- **RSI(14):** {rsi_14}")
            else:
                lines.append(f"\n📈 技术指标分析:")
                lines.append(f"   MA趋势: {tech.get('ma_trend', 'N/A')}")
                lines.append(f"   MACD趋势: {tech.get('macd_trend', 'N/A')}")
                rsi_14 = tech.get('rsi_14', 'N/A')
                if isinstance(rsi_14, (int, float)):
                    lines.append(f"   RSI(14): {rsi_14:.2f}")
                else:
                    lines.append(f"   RSI(14): {rsi_14}")
        
        sentiment = report['sentiment_indicators']
        if sentiment:
            if markdown:
                lines.append(f"\n## 😊 市场情绪指标")
                lines.append(f"- **涨跌家数:** ↗{sentiment.get('up_stocks', 'N/A')} | ↘{sentiment.get('down_stocks', 'N/A')} | →{sentiment.get('flat_stocks', 'N/A')}")
                up_ratio = sentiment.get('up_ratio', 0)
                lines.append(f"- **上涨占比:** {up_ratio*100:.1f}%")
            else:
                lines.append(f"\n😊 市场情绪指标:")
                lines.append(f"   涨跌家数: ↗{sentiment.get('up_stocks', 'N/A')} | ↘{sentiment.get('down_stocks', 'N/A')} | →{sentiment.get('flat_stocks', 'N/A')}")
                up_ratio = sentiment.get('up_ratio', 0)
                lines.append(f"   上涨占比: {up_ratio*100:.1f}%")
        
        valuation = report['valuation_indicators']
        if valuation:
            if markdown:
                lines.append(f"\n## 💰 估值水平")
                hs300_pe = valuation.get('hs300_pe', 'N/A')
                if isinstance(hs300_pe, (int, float)):
                    lines.append(f"- **沪深300 PE:** {hs300_pe:.2f}")
                else:
                    lines.append(f"- **沪深300 PE:** {hs300_pe}")
                dividend_yield = valuation.get('hs300_dividend_yield', 'N/A')
                if isinstance(dividend_yield, (int, float)):
                    lines.append(f"- **股息率:** {dividend_yield:.2f}%")
                else:
                    lines.append(f"- **股息率:** {dividend_yield}%")
            else:
                lines.append(f"\n💰 估值水平:")
                hs300_pe = valuation.get('hs300_pe', 'N/A')
                if isinstance(hs300_pe, (int, float)):
                    lines.append(f"   沪深300 PE: {hs300_pe:.2f}")
                else:
                    lines.append(f"   沪深300 PE: {hs300_pe}")
                dividend_yield = valuation.get('hs300_dividend_yield', 'N/A')
                if isinstance(dividend_yield, (int, float)):
                    lines.append(f"   股息率: {dividend_yield:.2f}%")
                else:
                    lines.append(f"   股息率: {dividend_yield}%")
        
        money = report['money_flow_indicators']
        if money:
            if markdown:
                lines.append(f"\n## 💸 资金流向")
                m2_amount = money.get('m2_amount', 'N/A')
                if isinstance(m2_amount, (int, float)):
                    lines.append(f"- **M2余额:** {m2_amount/10000:.2f}万亿")
                else:
                    lines.append(f"- **M2余额:** {m2_amount}")
                m2_growth = money.get('m2_growth', 'N/A')
                if isinstance(m2_growth, (int, float)):
                    lines.append(f"- **M2增速:** {m2_growth:.2f}%")
                else:
                    lines.append(f"- **M2增速:** {m2_growth}%")
            else:
                lines.append(f"\n💸 资金流向:")
                m2_amount = money.get('m2_amount', 'N/A')
                if isinstance(m2_amount, (int, float)):
                    lines.append(f"   M2余额: {m2_amount/10000:.2f}万亿")
                else:
                    lines.append(f"   M2余额: {m2_amount}")
                m2_growth = money.get('m2_growth', 'N/A')
                if isinstance(m2_growth, (int, float)):
                    lines.append(f"   M2增速: {m2_growth:.2f}%")
                else:
                    lines.append(f"   M2增速: {m2_growth}%")
        
        margin_data = report['margin_detail']
        if margin_data:
            if markdown:
                lines.append(f"\n## 💳 融资融券")
                margin_balance = margin_data.get('margin_balance', 'N/A')
                if isinstance(margin_balance, (int, float)):
                    lines.append(f"- **融资余额:** {margin_balance/100000000:.2f}亿")
                else:
                    lines.append(f"- **融资余额:** {margin_balance}")
                
                margin_buy_balance = margin_data.get('margin_buy_balance', 'N/A')
                if isinstance(margin_buy_balance, (int, float)):
                    lines.append(f"- **融资买入:** {margin_buy_balance/100000000:.2f}亿")
                else:
                    lines.append(f"- **融资买入:** {margin_buy_balance}")
                    
                change_ratio = margin_data.get('change_ratio', 'N/A')
                if isinstance(change_ratio, (int, float)):
                    lines.append(f"- **周变化率:** {change_ratio:.2f}%")
                else:
                    lines.append(f"- **周变化率:** {change_ratio}%")
            else:
                lines.append(f"\n💳 融资融券:")
                margin_balance = margin_data.get('margin_balance', 'N/A')
                if isinstance(margin_balance, (int, float)):
                    lines.append(f"   融资余额: {margin_balance/100000000:.2f}亿")
                else:
                    lines.append(f"   融资余额: {margin_balance}")
                
                margin_buy_balance = margin_data.get('margin_buy_balance', 'N/A')
                if isinstance(margin_buy_balance, (int, float)):
                    lines.append(f"   融资买入: {margin_buy_balance/100000000:.2f}亿")
                else:
                    lines.append(f"   融资买入: {margin_buy_balance}")
                    
                change_ratio = margin_data.get('change_ratio', 'N/A')
                if isinstance(change_ratio, (int, float)):
                    lines.append(f"   周变化率: {change_ratio:.2f}%")
                else:
                    lines.append(f"   周变化率: {change_ratio}%")
                
        if markdown:
            lines.append("\n---")
        else:
            lines.append("=" * 80)
        
        return '\n'.join(lines)
    
    def _judge_rsi_level(self, rsi: float) -> str:
        """判断RSI水平"""
        if rsi >= 80:
            return "超买"
        elif rsi >= 70:
            return "强势"
        elif rsi >= 30:
            return "正常"
        elif rsi >= 20:
            return "弱势"
        else:
            return "超卖"
    
    def _generate_ai_analysis(self, index_name: str, user_opinion: str = '') -> Dict:
        """生成AI分析数据"""
        try:
            from providers.market_ai_analysis import generate_index_analysis_report
            
            market_report_data = self.get_comprehensive_market_report(use_cache=True, index_name=index_name)
            
            print(f"🤖 OOOOOO 正在生成{index_name}的AI分析报告...")
            
            ai_report, timestamp = generate_index_analysis_report(
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
            
            self.cache_manager.save_cached_data('ai_analysis', ai_data)
            
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
