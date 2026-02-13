"""A股市场工具 - 统一的数据获取和缓存管理"""

import os
import sys
import warnings
from datetime import datetime
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
from market.market_formatters import MarketTextFormatter
from utils.news_tools import get_market_news_cls
from config_manager import config


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
        data_type = 'valuation_indicators'
        
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
        data_type = 'money_flow_indicators'
        
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
        data_type = 'margin_detail'
        
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
        # 检查是否启用市场新闻功能
        if not config.is_market_news_enabled():
            print("📰 市场新闻功能已禁用")
            return {'error': '市场新闻功能已禁用', 'disabled': True}
        
        data_type = 'market_news'
        
        if use_cache and not force_refresh and self.cache_manager.is_cache_valid(data_type):
            print(f"📋 使用缓存的市场新闻数据")
            return self.cache_manager.get_cached_data(data_type)
        
        print(f"📡 获取市场新闻数据...")
        try:
            ret, data = get_market_news_cls(debug=debug)
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
        
        # 检查是否启用市场新闻功能
        if config.is_market_news_enabled():
            report['market_news_data'] = self.get_market_news_data(use_cache)
        else:
            report['market_news_data'] = {'disabled': True}
        
        print("=" * 60)
        print("✅ 综合市场报告生成完成!")
        
        return report

    
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
