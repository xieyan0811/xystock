"""
股票数据工具模块 - 统一的股票数据获取和缓存管理
"""

import sys
import os
import warnings
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# 添加路径以便导入
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

warnings.filterwarnings('ignore')

# 导入必要的模块
from providers.stock_utils import (
    get_stock_name, get_market_info, get_indicators, 
    normalize_stock_input,
    fetch_stock_basic_info, fetch_stock_technical_indicators,
    fetch_stock_news_data, fetch_stock_chip_data
)
from providers.stock_data_fetcher import data_manager, KLineType
from providers.stock_data_cache import get_cache_manager

# 导入AI分析模块
try:
    from providers.stock_ai_analysis import (
        generate_fundamental_analysis_report, generate_stock_analysis_report, 
        generate_news_analysis_report, generate_chip_analysis_report
    )
    AI_ANALYSIS_AVAILABLE = True
except ImportError:
    AI_ANALYSIS_AVAILABLE = False
    print("⚠️ AI分析模块不可用，请检查依赖是否正确安装")


class StockTools:
    """统一的股票数据工具类"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        """初始化股票工具"""
        self.cache_manager = get_cache_manager()
    
    def get_stock_basic_info(self, stock_code: str, use_cache: bool = True, force_refresh: bool = False, include_ai_analysis: bool = False) -> Dict:
        """获取股票基本信息"""
        data_type = 'basic_info'
        
        try:
            stock_code, _ = normalize_stock_input(stock_code, 'stock')
        except:
            pass
        
        if use_cache and not force_refresh and self.cache_manager.is_cache_valid(data_type, stock_code):
            print(f"📋 使用缓存的 {stock_code} {self.cache_manager.cache_configs[data_type]['description']}")
            basic_data = self.cache_manager.get_cached_data(data_type, stock_code)
        else:
            print(f"📡 获取 {stock_code} {self.cache_manager.cache_configs[data_type]['description']}...")
            try:
                basic_data = fetch_stock_basic_info(stock_code)
                if use_cache and 'error' not in basic_data:
                    self.cache_manager.save_cached_data(data_type, stock_code, basic_data)
            except Exception as e:
                print(f"❌ 获取股票基本信息失败: {e}")
                basic_data = self.cache_manager.get_cached_data(data_type, stock_code) if use_cache else {'error': str(e)}
        
        if include_ai_analysis and 'error' not in basic_data:
            try:
                stock_name = get_stock_name(stock_code, 'stock')
                market_info = get_market_info(stock_code)
                
                ai_report, ai_timestamp = self.generate_fundamental_analysis_with_cache(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    market_info=market_info,
                    fundamental_data=basic_data,
                    use_cache=use_cache,
                    force_refresh=force_refresh
                )
                
                basic_data['ai_analysis'] = {
                    'report': ai_report,
                    'timestamp': ai_timestamp
                }
                
            except Exception as e:
                print(f"❌ 生成AI基本面分析失败: {e}")
                basic_data['ai_analysis'] = {
                    'error': str(e),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
        
        return basic_data
    
    def get_stock_technical_indicators(self, stock_code: str, period: int = 160, use_cache: bool = True, force_refresh: bool = False) -> Dict:
        """获取股票技术指标和风险指标（不缓存K线数据本身）"""
        data_type = 'technical_indicators'
        
        try:
            stock_code, _ = normalize_stock_input(stock_code, 'stock')
        except:
            pass
        
        if use_cache and not force_refresh and self.cache_manager.is_cache_valid(data_type, stock_code):
            print(f"📋 使用缓存的 {stock_code} {self.cache_manager.cache_configs[data_type]['description']}")
            return self.cache_manager.get_cached_data(data_type, stock_code)
        
        print(f"📡 获取 {stock_code} {self.cache_manager.cache_configs[data_type]['description']}...")
        try:
            data = fetch_stock_technical_indicators(stock_code, period)
            if use_cache and 'error' not in data:
                self.cache_manager.save_cached_data(data_type, stock_code, data)
            return data
        except Exception as e:
            print(f"❌ 获取技术指标失败: {e}")
            return self.cache_manager.get_cached_data(data_type, stock_code) if use_cache else {'error': str(e)}
    
    def get_stock_kline_data(self, stock_code: str, period: int = 160, use_cache: bool = True, force_refresh: bool = False, include_ai_analysis: bool = False) -> Dict:
        """获取股票K线数据（实时获取，不缓存K线数据本身，但返回包含技术指标的完整信息）"""
        
        try:
            stock_code, _ = normalize_stock_input(stock_code, 'stock')
        except:
            pass
        
        try:
            kline_data = data_manager.get_kline_data(
                stock_code, 
                KLineType.DAY, 
                period
            )
            
            if kline_data and len(kline_data) > 0:
                df = pd.DataFrame([k.__dict__ for k in kline_data])
                df = df.sort_values('datetime')
                
                df['MA5'] = df['close'].rolling(window=5).mean()
                df['MA10'] = df['close'].rolling(window=10).mean()
                df['MA20'] = df['close'].rolling(window=20).mean()
                
                indicators_data = self.get_stock_technical_indicators(
                    stock_code, period, use_cache, force_refresh)
                
                result = {
                    'kline_data': df.to_dict('records'),  # K线数据实时返回
                    'indicators': indicators_data.get('indicators', {}),
                    'risk_metrics': indicators_data.get('risk_metrics', {}),  # 精简风险摘要（来自缓存）
                    'data_length': len(df),
                    'latest_data': df.iloc[-1].to_dict() if len(df) > 0 else {},
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                if include_ai_analysis:
                    try:
                        stock_name = get_stock_name(stock_code, 'stock')
                        market_info = get_market_info(stock_code)
                        indicators = indicators_data.get('indicators', {})
                        risk_metrics = indicators_data.get('risk_metrics', {})
                        
                        ai_report, ai_timestamp = self.generate_tech_analysis_with_cache(
                            stock_code=stock_code,
                            stock_name=stock_name,
                            market_info=market_info,
                            df=df,
                            indicators=indicators,
                            risk_metrics=risk_metrics,
                            use_cache=use_cache,
                            force_refresh=force_refresh
                        )
                        
                        result['ai_analysis'] = {
                            'report': ai_report,
                            'timestamp': ai_timestamp
                        }
                        
                    except Exception as e:
                        print(f"❌ 生成AI技术分析失败: {e}")
                        result['ai_analysis'] = {
                            'error': str(e),
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                
                return result
            else:
                return {'error': f"未获取到股票 {stock_code} 的K线数据"}
                
        except Exception as e:
            return {'error': str(e)}
    
    def get_stock_news_data(self, stock_code: str, use_cache: bool = True, force_refresh: bool = False, include_ai_analysis: bool = False) -> Dict:
        """获取股票新闻数据"""
        data_type = 'news_data'
        
        try:
            stock_code, _ = normalize_stock_input(stock_code, 'stock')
        except:
            pass
        
        if use_cache and not force_refresh and self.cache_manager.is_cache_valid(data_type, stock_code):
            print(f"📋 使用缓存的 {stock_code} {self.cache_manager.cache_configs[data_type]['description']}")
            news_data = self.cache_manager.get_cached_data(data_type, stock_code)
        else:
            print(f"📡 获取 {stock_code} {self.cache_manager.cache_configs[data_type]['description']}...")
            try:
                news_data = fetch_stock_news_data(stock_code)
                if use_cache and 'error' not in news_data:
                    self.cache_manager.save_cached_data(data_type, stock_code, news_data)
            except Exception as e:
                print(f"❌ 获取新闻数据失败: {e}")
                news_data = self.cache_manager.get_cached_data(data_type, stock_code) if use_cache else {'error': str(e)}
        
        # 如果需要AI分析且新闻数据获取成功
        if include_ai_analysis and 'error' not in news_data:
            try:
                stock_name = get_stock_name(stock_code, 'stock')
                market_info = get_market_info(stock_code)
                
                ai_report, ai_timestamp = self.generate_news_analysis_with_cache(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    market_info=market_info,
                    news_data=news_data.get('news_data', []),
                    use_cache=use_cache,
                    force_refresh=force_refresh
                )
                
                news_data['ai_analysis'] = {
                    'report': ai_report,
                    'timestamp': ai_timestamp
                }
                
            except Exception as e:
                print(f"❌ 生成AI新闻分析失败: {e}")
                news_data['ai_analysis'] = {
                    'error': str(e),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
        
        return news_data
    
    def get_stock_chip_data(self, stock_code: str, use_cache: bool = True, force_refresh: bool = False, include_ai_analysis: bool = False) -> Dict:
        """获取股票筹码数据"""
        data_type = 'chip_data'
        
        try:
            stock_code, _ = normalize_stock_input(stock_code, 'stock')
        except:
            pass
        
        if use_cache and not force_refresh and self.cache_manager.is_cache_valid(data_type, stock_code):
            print(f"📋 使用缓存的 {stock_code} {self.cache_manager.cache_configs[data_type]['description']}")
            chip_data = self.cache_manager.get_cached_data(data_type, stock_code)
        else:
            print(f"📡 获取 {stock_code} {self.cache_manager.cache_configs[data_type]['description']}...")
            try:
                chip_data = fetch_stock_chip_data(stock_code)
                if use_cache and 'error' not in chip_data:
                    self.cache_manager.save_cached_data(data_type, stock_code, chip_data)
            except Exception as e:
                print(f"⚠️ 暂不支持拉取筹码数据: {e}")
                chip_data = self.cache_manager.get_cached_data(data_type, stock_code) if use_cache else {'error': str(e)}
        
        # 如果需要AI分析且筹码数据获取成功
        if include_ai_analysis and 'error' not in chip_data:
            try:
                stock_name = get_stock_name(stock_code, 'stock')
                
                ai_report, ai_timestamp = self.generate_chip_analysis_with_cache(
                    stock_code=stock_code,
                    stock_name=stock_name, 
                    chip_data=chip_data,
                    use_cache=use_cache,
                    force_refresh=force_refresh
                )
                
                chip_data['ai_analysis'] = {
                    'report': ai_report,
                    'timestamp': ai_timestamp
                }
                
            except Exception as e:
                print(f"❌ 生成AI分析失败: {e}")
                chip_data['ai_analysis'] = {
                    'error': str(e),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
        
        return chip_data
    
    def get_cached_ai_analysis(self, stock_code: str, analysis_type: str = 'comprehensive', use_cache: bool = True) -> Dict:
        """获取AI分析数据"""
        data_type = 'ai_analysis'
        
        try:
            stock_code, _ = normalize_stock_input(stock_code, 'stock')
        except:
            pass
        
        # 使用分析类型区分不同的AI分析
        cache_key = f"{data_type}_{analysis_type}_{stock_code}"
        
        if use_cache:
            try:
                cache_data = self.cache_manager.load_cache()
                if cache_key in cache_data:
                    cache_meta = cache_data[cache_key].get('cache_meta', {})
                    cache_time = datetime.fromisoformat(cache_meta['timestamp'])
                    expire_time = cache_time + timedelta(minutes=self.cache_manager.cache_configs[data_type]['expire_minutes'])
                    if datetime.now() < expire_time:
                        print(f"📋 使用缓存的 {stock_code} {analysis_type} AI分析")
                        return cache_data[cache_key].get('data', {})
            except Exception:
                pass
        
        return {}
    
    def set_ai_analysis(self, stock_code: str, analysis_type: str, analysis_data: Dict):
        """设置AI分析数据"""
        try:
            stock_code, _ = normalize_stock_input(stock_code, 'stock')
        except:
            pass
            
        cache_key = f"ai_analysis_{analysis_type}_{stock_code}"
        analysis_data['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            cache_data = self.cache_manager.load_cache()
            cache_data[cache_key] = {
                'cache_meta': {
                    'timestamp': datetime.now().isoformat(),
                    'data_type': 'ai_analysis',
                    'stock_code': stock_code,
                    'analysis_type': analysis_type,
                    'expire_minutes': self.cache_manager.cache_configs['ai_analysis']['expire_minutes']
                },
                'data': analysis_data
            }
            self.cache_manager.save_cache(cache_data)
            print(f"💾 {stock_code} {analysis_type} AI分析已缓存")
        except Exception as e:
            print(f"❌ 缓存AI分析失败: {e}")
    
    # =========================
    # AI分析报告方法
    # =========================
    
    def generate_fundamental_analysis_with_cache(self, stock_code: str, stock_name: str = None, 
                                                market_info: Dict = None, fundamental_data: Dict = None,
                                                use_cache: bool = True, force_refresh: bool = False) -> Tuple[str, str]:
        """生成基本面分析报告（带缓存）"""
        analysis_type = "fundamental"
        
        if use_cache and not force_refresh:
            cached_data = self.get_cached_ai_analysis(stock_code, analysis_type, use_cache=True)
            if cached_data and 'report' in cached_data:
                return cached_data['report'], cached_data.get('timestamp', '')
        
        if not AI_ANALYSIS_AVAILABLE:
            error_msg = "AI分析模块不可用，请检查依赖是否正确安装"
            return error_msg, datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            if stock_name is None:
                stock_name = get_stock_name(stock_code, 'stock')
            if market_info is None:
                market_info = get_market_info(stock_code)
            
            report, timestamp = generate_fundamental_analysis_report(
                stock_code=stock_code,
                stock_name=stock_name,
                market_info=market_info,
                fundamental_data=fundamental_data or {}
            )
            
            self.set_ai_analysis(stock_code, analysis_type, {
                'report': report,
                'timestamp': timestamp,
                'stock_name': stock_name
            })
            
            return report, timestamp
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = f"基本面分析失败: {str(e)}"
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return error_msg, timestamp
    
    def generate_tech_analysis_with_cache(self, stock_code: str, stock_name: str = None,
                                         market_info: Dict = None, df=None, indicators: Dict = None,
                                         risk_metrics: Dict = None,
                                         use_cache: bool = True, force_refresh: bool = False) -> Tuple[str, str]:
        """生成股票技术分析报告（带缓存）"""
        analysis_type = "technical"
        
        if use_cache and not force_refresh:
            cached_data = self.get_cached_ai_analysis(stock_code, analysis_type, use_cache=True)
            if cached_data and 'report' in cached_data:
                return cached_data['report'], cached_data.get('timestamp', '')
        
        if not AI_ANALYSIS_AVAILABLE:
            error_msg = "AI分析模块不可用，请检查依赖是否正确安装"
            return error_msg, datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            if stock_name is None:
                stock_name = get_stock_name(stock_code, 'stock')
            if market_info is None:
                market_info = get_market_info(stock_code)
            if df is None:
                kline_data = self.get_stock_kline_data(stock_code)
                if 'data' in kline_data and 'df' in kline_data['data']:
                    df = kline_data['data']['df']
                else:
                    raise ValueError("无法获取K线数据")
            if indicators is None:
                indicators = get_indicators(df)
            
            # 生成技术分析报告（直接传递indicators，包含所有必要数据）
            report = generate_stock_analysis_report(
                stock_code=stock_code,
                stock_name=stock_name,
                market_info=market_info,
                indicators=indicators,
                risk_metrics=risk_metrics
            )
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            self.set_ai_analysis(stock_code, analysis_type, {
                'report': report,
                'timestamp': timestamp,
                'stock_name': stock_name
            })
            return report, timestamp
            
        except Exception as e:
            error_msg = f"技术分析失败: {str(e)}"
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return error_msg, timestamp
    
    def generate_news_analysis_with_cache(self, stock_code: str, stock_name: str = None,
                                        market_info: Dict = None, news_data: List = None,
                                        use_cache: bool = True, force_refresh: bool = False) -> Tuple[str, str]:
        """生成新闻分析报告（带缓存）"""
        analysis_type = "news"
        cache_key = f"ai_analysis_{analysis_type}_{stock_code}"
        
        if use_cache and not force_refresh:
            cached_data = self.get_cached_ai_analysis(stock_code, analysis_type, use_cache=True)
            if cached_data and 'report' in cached_data:
                return cached_data['report'], cached_data.get('timestamp', '')
        
        if not AI_ANALYSIS_AVAILABLE:
            error_msg = "AI分析模块不可用，请检查依赖是否正确安装"
            return error_msg, datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            if stock_name is None:
                stock_name = get_stock_name(stock_code, 'stock')
            if market_info is None:
                market_info = get_market_info(stock_code)
            if news_data is None:
                news_result = self.get_stock_news_data(stock_code)
                if 'data' in news_result and 'news' in news_result['data']:
                    news_data = news_result['data']['news']
                else:
                    news_data = []
            
            report, timestamp = generate_news_analysis_report(
                stock_code=stock_code,
                stock_name=stock_name,
                market_info=market_info,
                news_data=news_data
            )
            
            self.set_ai_analysis(stock_code, analysis_type, {
                'report': report,
                'timestamp': timestamp,
                'stock_name': stock_name
            })
            
            return report, timestamp
            
        except Exception as e:
            error_msg = f"新闻分析失败: {str(e)}"
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return error_msg, timestamp
    
    def generate_chip_analysis_with_cache(self, stock_code: str, stock_name: str = None,
                                        chip_data: Dict = None,
                                        use_cache: bool = True, force_refresh: bool = False) -> Tuple[str, str]:
        """生成筹码分析报告（带缓存）"""
        analysis_type = "chip"
        cache_key = f"ai_analysis_{analysis_type}_{stock_code}"
        
        if use_cache and not force_refresh:
            cached_data = self.get_cached_ai_analysis(stock_code, analysis_type, use_cache=True)
            if cached_data and 'report' in cached_data:
                return cached_data['report'], cached_data.get('timestamp', '')
        
        if not AI_ANALYSIS_AVAILABLE:
            error_msg = "AI分析模块不可用，请检查依赖是否正确安装"
            return error_msg, datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            if stock_name is None:
                stock_name = get_stock_name(stock_code, 'stock')
            if chip_data is None:
                raise ValueError("无法获取筹码数据")
            
            report, timestamp = generate_chip_analysis_report(
                stock_code=stock_code,
                stock_name=stock_name,
                chip_data=chip_data
            )
            
            self.set_ai_analysis(stock_code, analysis_type, {
                'report': report,
                'timestamp': timestamp,
                'stock_name': stock_name
            })
            
            return report, timestamp
            
        except Exception as e:
            error_msg = f"筹码分析失败: {str(e)}"
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return error_msg, timestamp
    
    def get_comprehensive_ai_analysis(self, stock_code: str, user_opinion: str = "", user_position: str="不确定",
                                     use_cache: bool = True, force_refresh: bool = False) -> Dict:
        """获取综合AI分析数据"""
        data_type = 'ai_analysis'
        analysis_type = 'comprehensive'
        
        try:
            stock_code, stock_name = normalize_stock_input(stock_code, 'stock')
        except Exception as e:
            return {
                'error': f'股票代码格式错误: {str(e)}',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        cache_key = f"{data_type}_{analysis_type}_{stock_code}"
        
        # 检查缓存（如果用户观点为空且不强制刷新）
        if use_cache and not force_refresh and not user_opinion.strip():
            try:
                cache_data = self.cache_manager.load_cache()
                if cache_key in cache_data:
                    cache_meta = cache_data[cache_key].get('cache_meta', {})
                    cache_time = datetime.fromisoformat(cache_meta['timestamp'])
                    expire_time = cache_time + timedelta(minutes=self.cache_manager.cache_configs[data_type]['expire_minutes'])
                    
                    if datetime.now() < expire_time:
                        print(f"📋 使用缓存的 {stock_code} 综合分析")
                        return cache_data[cache_key].get('data', {})
            except Exception:
                pass
        
        # 生成新的综合分析
        try:
            if not AI_ANALYSIS_AVAILABLE:
                return {
                    'error': 'AI分析模块不可用，请检查依赖是否正确安装',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            
            print(f"🤖 生成 {stock_code} 综合AI分析...")
            
            from providers.stock_ai_analysis import generate_comprehensive_analysis_report
            from providers.market_data_tools import get_market_tools
            
            market_tools = get_market_tools()
            
            report, data_sources = generate_comprehensive_analysis_report(
                stock_code=stock_code,
                stock_name=stock_name,
                user_opinion=user_opinion,
                user_position=user_position,
                stock_tools=self,
                market_tools=market_tools
            )
            
            analysis_data = {
                'report': report,
                'data_sources': data_sources,
                'analysis_info': {
                    'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data_sources_count': len(data_sources),
                    'user_opinion_included': bool(user_opinion.strip()),
                    'user_opinion': user_opinion.strip() if user_opinion.strip() else None
                },
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'cache_time': datetime.now().isoformat()
            }
            
            try:
                cache_data = self.cache_manager.load_cache()
                cache_data[cache_key] = {
                    'cache_meta': {
                        'timestamp': datetime.now().isoformat(),
                        'data_type': data_type,
                        'stock_code': stock_code,
                        'analysis_type': analysis_type,
                        'expire_minutes': self.cache_manager.cache_configs[data_type]['expire_minutes']
                    },
                    'data': analysis_data
                }
                self.cache_manager.save_cache(cache_data)
                print(f"💾 {stock_code} 综合分析已缓存")
            except Exception as e:
                print(f"❌ 缓存综合分析失败: {e}")
            
            return analysis_data
            
        except Exception as e:
            print(f"❌ 生成综合分析失败: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def get_comprehensive_stock_report(self, stock_code: str, use_cache: bool = True) -> Dict:
        """获取股票综合报告"""
        print(f"📋 生成 {stock_code} 综合股票报告...")
        print("=" * 60)
        
        report = {
            'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'stock_code': stock_code,
            'basic_info': {},
            'kline_data': {},
            'news_data': {},
            'chip_data': {},
            'ai_analysis': {},
            'stock_summary': {}
        }
        
        report['basic_info'] = self.get_stock_basic_info(stock_code, use_cache)
        report['kline_data'] = self.get_stock_kline_data(stock_code, 160, use_cache)
        report['news_data'] = self.get_stock_news_data(stock_code, use_cache)
        report['chip_data'] = self.get_stock_chip_data(stock_code, use_cache)
        
        report['ai_analysis'] = {
            'fundamental': self.get_cached_ai_analysis(stock_code, 'fundamental', use_cache),
            'market': self.get_cached_ai_analysis(stock_code, 'market', use_cache),
            'news': self.get_cached_ai_analysis(stock_code, 'news', use_cache),
            'chip': self.get_cached_ai_analysis(stock_code, 'chip', use_cache),
        }
        
        report['stock_summary'] = self._generate_stock_summary(report)
        
        print("=" * 60)
        print("✅ 综合股票报告生成完成!")
        
        return report
    
    def _generate_stock_summary(self, report: Dict) -> Dict:
        """生成股票摘要"""
        summary = {}
        
        basic = report['basic_info']
        if basic and 'error' not in basic:
            summary['current_price'] = basic.get('current_price', 0)
            summary['change_percent'] = basic.get('change_percent', 0)
            summary['stock_name'] = basic.get('name', '')
            summary['industry'] = basic.get('industry', '')
        
        kline = report['kline_data']
        if kline and 'error' not in kline:
            indicators = kline.get('indicators', {})
            summary['technical_trend'] = f"{indicators.get('ma_trend', '未知')} | MACD {indicators.get('macd_trend', '未知')}"
            summary['rsi_level'] = self._judge_rsi_level(indicators.get('rsi_14', 50))
        
        news = report['news_data']
        if news and 'error' not in news:
            summary['news_count'] = news.get('news_count', 0)
        
        chip = report['chip_data']
        if chip and 'error' not in chip:
            summary['profit_ratio'] = chip.get('profit_ratio', 0)
            summary['avg_cost'] = chip.get('avg_cost', 0)
        
        return summary
    
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
    
    def clear_cache(self, stock_code: str = None, data_type: str = None):
        """清理缓存"""
        self.cache_manager.clear_cache(stock_code, data_type)
    
    def get_cache_status(self, stock_code: str = None) -> Dict:
        """获取缓存状态"""
        return self.cache_manager.get_cache_status(stock_code)
    
    def print_cache_status(self, stock_code: str = None):
        """打印缓存状态"""
        self.cache_manager.print_cache_status(stock_code)


# =========================
# 全局实例和便捷函数
# =========================

# 全局股票工具实例
_stock_tools = None

def get_stock_tools() -> StockTools:
    """获取全局股票工具实例"""
    global _stock_tools
    if _stock_tools is None:
        _stock_tools = StockTools()
    return _stock_tools

def show_stock_cache_status(stock_code: str = None):
    """显示股票缓存状态"""
    tools = get_stock_tools()
    tools.print_cache_status(stock_code)

def clear_stock_cache(stock_code: str = None, data_type: str = None):
    """清理股票数据缓存"""
    tools = get_stock_tools()
    tools.clear_cache(stock_code, data_type)

def set_stock_ai_analysis(stock_code: str, analysis_type: str, analysis_data: Dict):
    """设置股票AI分析数据"""
    tools = get_stock_tools()
    tools.set_ai_analysis(stock_code, analysis_type, analysis_data)

if __name__ == "__main__":
    # 测试用例
    print("🧪 测试统一股票工具模块...")
    
    tools = get_stock_tools()
    test_stock = "000001"  # 平安银行
    
    print(f"\n1. 显示 {test_stock} 缓存状态:")
    tools.print_cache_status(test_stock)
    
    print(f"\n2. 获取 {test_stock} 基本信息:")
    basic_info = tools.get_stock_basic_info(test_stock)
    if 'error' not in basic_info:
        print(f"   当前价格: {basic_info.get('current_price', 'N/A')}")
        print(f"   股票名称: {basic_info.get('name', 'N/A')}")
    else:
        print(f"   错误: {basic_info['error']}")
    
    print(f"\n3. 显示更新后的缓存状态:")
    tools.print_cache_status(test_stock)
    
    print("\n✅ 测试完成!")
    print(f"\n1. 显示 {test_stock} 缓存状态:")
    tools.print_cache_status(test_stock)
    
    print(f"\n2. 获取 {test_stock} 基本信息:")
    basic_info = tools.get_stock_basic_info(test_stock)
    if 'error' not in basic_info:
        print(f"   当前价格: {basic_info.get('current_price', 'N/A')}")
        print(f"   股票名称: {basic_info.get('name', 'N/A')}")
    else:
        print(f"   错误: {basic_info['error']}")
    
    print(f"\n3. 显示更新后的缓存状态:")
    tools.print_cache_status(test_stock)
    
    print("\n✅ 测试完成!")
