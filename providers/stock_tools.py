"""
股票数据工具模块 - 统一的股票数据获取和缓存管理

本模块提供股票数据的统一接口，包括：
1. 股票基本信息和实时行情
2. K线数据和技术指标
3. 新闻资讯数据
4. 筹码分析数据
5. 风险指标计算
6. AI分析报告

所有数据都支持智能缓存，避免重复请求
"""

import sys
import os
import json
import warnings
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List

# 添加路径以便导入
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

warnings.filterwarnings('ignore')

# 导入必要的模块
from providers.stock_utils import (
    get_stock_name, get_market_info, get_indicators, 
    normalize_stock_input, get_chip_analysis_data
)
from providers.stock_data_fetcher import data_manager, KLineType
from providers.news_tools import get_stock_news_by_akshare
from providers.risk_metrics import calculate_portfolio_risk


# =========================
# 独立的数据获取函数（纯外部API调用）
# =========================

def fetch_stock_basic_info(stock_code: str) -> Dict:
    """获取股票基本信息的具体实现"""
    basic_info = {}
    
    try:
        if not data_manager.is_available():
            if not data_manager.initialize():
                raise Exception("数据提供者初始化失败")
                
        # 获取实时行情
        realtime_data = data_manager.get_realtime_quote(stock_code)
        stock_info = data_manager.get_stock_info(stock_code)
        
        if realtime_data:
            basic_info.update({
                'current_price': float(realtime_data.current_price),
                'change': float(realtime_data.change),
                'change_percent': float(realtime_data.change_percent),
                'volume': int(realtime_data.volume),
                'amount': float(realtime_data.amount),
                'high': float(realtime_data.high),
                'low': float(realtime_data.low),
                'open': float(realtime_data.open),
                'prev_close': float(realtime_data.prev_close),
                'timestamp': str(realtime_data.timestamp),
            })
        
        if stock_info:
            basic_info.update({
                'name': str(stock_info.name) if stock_info.name else '',
                'industry': str(stock_info.industry) if stock_info.industry else '',
                'total_market_value': float(stock_info.total_market_value) if stock_info.total_market_value else 0,
                'circulating_market_value': float(stock_info.circulating_market_value) if stock_info.circulating_market_value else 0,
                'pe_ratio': str(stock_info.pe_ratio) if stock_info.pe_ratio else '',
                'pb_ratio': str(stock_info.pb_ratio) if stock_info.pb_ratio else '',
                'roe': str(stock_info.roe) if stock_info.roe else '',
                'gross_profit_margin': str(stock_info.gross_profit_margin) if stock_info.gross_profit_margin else '',
                'net_profit_margin': str(stock_info.net_profit_margin) if stock_info.net_profit_margin else '',
                'net_profit': str(stock_info.net_profit) if stock_info.net_profit else '',
            })
        
    except Exception as e:
        basic_info['error'] = str(e)
    
    basic_info['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return basic_info


def fetch_stock_kline_data(stock_code: str, period: int = 160) -> Dict:
    """获取股票K线数据的具体实现"""
    kline_info = {}
    
    try:
        # 固定使用日K数据
        kline_data = data_manager.get_kline_data(
            stock_code, 
            KLineType.DAY, 
            period
        )
        
        if kline_data and len(kline_data) > 0:
            # 转换为DataFrame
            df = pd.DataFrame([k.__dict__ for k in kline_data])
            df = df.sort_values('datetime')
            
            # 计算移动平均线
            df['MA5'] = df['close'].rolling(window=5).mean()
            df['MA10'] = df['close'].rolling(window=10).mean()
            df['MA20'] = df['close'].rolling(window=20).mean()
            
            # 获取技术指标
            indicators = get_indicators(df)
            
            # 风险指标计算
            risk_metrics = {}
            if len(df) >= 5:
                try:
                    risk_metrics = calculate_portfolio_risk(df, price_col='close')
                    # 确保summary_table是可序列化的
                    if 'summary_table' in risk_metrics and hasattr(risk_metrics['summary_table'], 'to_dict'):
                        risk_metrics['summary_table'] = risk_metrics['summary_table'].to_dict()
                except Exception as e:
                    risk_metrics['error'] = str(e)
            
            # 转换DataFrame为字典列表（确保JSON安全）
            kline_data_list = []
            for _, row in df.iterrows():
                row_dict = {}
                for col, value in row.items():
                    if pd.isna(value):
                        row_dict[col] = None
                    elif hasattr(value, 'isoformat'):  # datetime
                        row_dict[col] = value.isoformat()
                    else:
                        row_dict[col] = value
                kline_data_list.append(row_dict)
            
            # 获取最新数据
            latest_data = {}
            if len(df) > 0:
                latest_row = df.iloc[-1]
                for col, value in latest_row.items():
                    if pd.isna(value):
                        latest_data[col] = None
                    elif hasattr(value, 'isoformat'):
                        latest_data[col] = value.isoformat()
                    else:
                        latest_data[col] = value
            
            kline_info.update({
                'kline_data': kline_data_list,
                'indicators': indicators,
                'risk_metrics': risk_metrics,
                'data_length': len(df),
                'latest_data': latest_data
            })
        else:
            kline_info['error'] = f"未获取到股票 {stock_code} 的K线数据"
            
    except Exception as e:
        kline_info['error'] = str(e)
    
    kline_info['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return kline_info


def fetch_stock_news_data(stock_code: str) -> Dict:
    """获取股票新闻数据的具体实现"""
    news_info = {}
    
    try:
        # 使用news_tools模块获取新闻
        stock_data = get_stock_news_by_akshare(stock_code)
        
        if stock_data and 'company_news' in stock_data:
            news_data = stock_data['company_news']
            
            news_info.update({
                'news_data': news_data,
                'news_count': len(news_data),
                'latest_news': news_data[:5] if len(news_data) >= 5 else news_data  # 前5条最新新闻
            })
        else:
            news_info['error'] = "未能获取到相关新闻"
            
    except Exception as e:
        news_info['error'] = str(e)
    
    news_info['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return news_info


def fetch_stock_chip_data(stock_code: str) -> Dict:
    """获取股票筹码数据的具体实现"""
    chip_info = {}
    
    try:
        # 获取筹码分析数据
        chip_data = get_chip_analysis_data(stock_code)
        
        if "error" not in chip_data:
            chip_info.update(chip_data)
        else:
            chip_info['error'] = chip_data["error"]
            
    except Exception as e:
        chip_info['error'] = str(e)
    
    chip_info['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return chip_info


class StockTools:
    """统一的股票数据工具类"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        """初始化股票工具"""
        self.cache_dir = cache_dir
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.cache_file = os.path.join(project_dir, cache_dir, "stock_data.json")
        
        # 确保缓存目录存在
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
        # 缓存配置
        self.cache_configs = {
            'basic_info': {'expire_minutes': 5, 'description': '股票基本信息'},
            'kline_data': {'expire_minutes': 30, 'description': 'K线数据和技术指标'},
            'news_data': {'expire_minutes': 60, 'description': '新闻资讯数据'},
            'chip_data': {'expire_minutes': 1440, 'description': '筹码分析数据'},  # 1天
            'ai_analysis': {'expire_minutes': 180, 'description': 'AI分析报告'},
        }
    
    # =========================
    # 缓存管理相关方法
    # =========================
    
    def _load_cache(self) -> Dict:
        """加载缓存文件"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}
    
    def _make_json_safe(self, obj):
        """将对象转换为JSON安全的格式"""
        import numpy as np
        import pandas as pd
        
        if isinstance(obj, dict):
            return {key: self._make_json_safe(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_safe(item) for item in obj]
        elif isinstance(obj, pd.Series):
            return obj.tolist()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        elif hasattr(obj, 'isoformat'):  # datetime, date objects
            return obj.isoformat()
        else:
            return obj
    
    def _save_cache(self, cache_data: Dict):
        """保存缓存文件"""
        try:
            # 确保数据是JSON安全的
            safe_cache_data = self._make_json_safe(cache_data)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(safe_cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存股票数据缓存失败: {e}")
    
    def _get_cache_key(self, data_type: str, stock_code: str) -> str:
        """生成缓存键"""
        return f"{data_type}_{stock_code}"
    
    def _is_cache_valid(self, data_type: str, stock_code: str) -> bool:
        """检查缓存是否有效"""
        try:
            cache_data = self._load_cache()
            cache_key = self._get_cache_key(data_type, stock_code)
            
            if cache_key not in cache_data:
                return False
            
            cache_meta = cache_data[cache_key].get('cache_meta', {})
            cache_time = datetime.fromisoformat(cache_meta['timestamp'])
            expire_minutes = self.cache_configs[data_type]['expire_minutes']
            expire_time = cache_time + timedelta(minutes=expire_minutes)
            
            return datetime.now() < expire_time
        except Exception:
            return False
    
    def _get_cached_data(self, data_type: str, stock_code: str) -> Dict:
        """获取缓存数据"""
        try:
            cache_data = self._load_cache()
            cache_key = self._get_cache_key(data_type, stock_code)
            return cache_data.get(cache_key, {}).get('data', {})
        except Exception:
            return {}
    
    def _save_cached_data(self, data_type: str, stock_code: str, data: Dict):
        """保存数据到缓存"""
        try:
            cache_data = self._load_cache()
            cache_key = self._get_cache_key(data_type, stock_code)
            
            cache_data[cache_key] = {
                'cache_meta': {
                    'timestamp': datetime.now().isoformat(),
                    'data_type': data_type,
                    'stock_code': stock_code,
                    'expire_minutes': self.cache_configs[data_type]['expire_minutes']
                },
                'data': data
            }
            self._save_cache(cache_data)
            print(f"💾 {stock_code} {self.cache_configs[data_type]['description']}已缓存")
        except Exception as e:
            print(f"❌ 缓存股票数据失败: {e}")
    
    # =========================
    # 数据获取方法（带缓存）
    # =========================
    
    def get_stock_basic_info(self, stock_code: str, use_cache: bool = True, force_refresh: bool = False) -> Dict:
        """获取股票基本信息"""
        data_type = 'basic_info'
        
        # 标准化股票代码
        try:
            stock_code, _ = normalize_stock_input(stock_code, 'stock')
        except:
            pass
        
        # 检查缓存
        if use_cache and not force_refresh and self._is_cache_valid(data_type, stock_code):
            print(f"📋 使用缓存的 {stock_code} {self.cache_configs[data_type]['description']}")
            return self._get_cached_data(data_type, stock_code)
        
        # 获取新数据
        print(f"📡 获取 {stock_code} {self.cache_configs[data_type]['description']}...")
        try:
            data = fetch_stock_basic_info(stock_code)
            if use_cache and 'error' not in data:
                self._save_cached_data(data_type, stock_code, data)
            return data
        except Exception as e:
            print(f"❌ 获取股票基本信息失败: {e}")
            # 返回缓存数据作为备份
            return self._get_cached_data(data_type, stock_code) if use_cache else {'error': str(e)}
    
    def get_stock_kline_data(self, stock_code: str, period: int = 160, use_cache: bool = True, force_refresh: bool = False) -> Dict:
        """获取股票K线数据和技术指标"""
        data_type = 'kline_data'
        
        # 标准化股票代码
        try:
            stock_code, _ = normalize_stock_input(stock_code, 'stock')
        except:
            pass
        
        # 检查缓存
        if use_cache and not force_refresh and self._is_cache_valid(data_type, stock_code):
            print(f"📋 使用缓存的 {stock_code} {self.cache_configs[data_type]['description']}")
            return self._get_cached_data(data_type, stock_code)
        
        # 获取新数据
        print(f"📡 获取 {stock_code} {self.cache_configs[data_type]['description']}...")
        try:
            data = fetch_stock_kline_data(stock_code, period)
            if use_cache and 'error' not in data:
                self._save_cached_data(data_type, stock_code, data)
            return data
        except Exception as e:
            print(f"❌ 获取K线数据失败: {e}")
            return self._get_cached_data(data_type, stock_code) if use_cache else {'error': str(e)}
    
    def get_stock_news_data(self, stock_code: str, use_cache: bool = True, force_refresh: bool = False) -> Dict:
        """获取股票新闻数据"""
        data_type = 'news_data'
        
        # 标准化股票代码
        try:
            stock_code, _ = normalize_stock_input(stock_code, 'stock')
        except:
            pass
        
        # 检查缓存
        if use_cache and not force_refresh and self._is_cache_valid(data_type, stock_code):
            print(f"📋 使用缓存的 {stock_code} {self.cache_configs[data_type]['description']}")
            return self._get_cached_data(data_type, stock_code)
        
        # 获取新数据
        print(f"📡 获取 {stock_code} {self.cache_configs[data_type]['description']}...")
        try:
            data = fetch_stock_news_data(stock_code)
            if use_cache and 'error' not in data:
                self._save_cached_data(data_type, stock_code, data)
            return data
        except Exception as e:
            print(f"❌ 获取新闻数据失败: {e}")
            return self._get_cached_data(data_type, stock_code) if use_cache else {'error': str(e)}
    
    def get_stock_chip_data(self, stock_code: str, use_cache: bool = True, force_refresh: bool = False) -> Dict:
        """获取股票筹码数据"""
        data_type = 'chip_data'
        
        # 标准化股票代码
        try:
            stock_code, _ = normalize_stock_input(stock_code, 'stock')
        except:
            pass
        
        # 检查缓存
        if use_cache and not force_refresh and self._is_cache_valid(data_type, stock_code):
            print(f"📋 使用缓存的 {stock_code} {self.cache_configs[data_type]['description']}")
            return self._get_cached_data(data_type, stock_code)
        
        # 获取新数据
        print(f"📡 获取 {stock_code} {self.cache_configs[data_type]['description']}...")
        try:
            data = fetch_stock_chip_data(stock_code)
            if use_cache and 'error' not in data:
                self._save_cached_data(data_type, stock_code, data)
            return data
        except Exception as e:
            print(f"❌ 获取筹码数据失败: {e}")
            return self._get_cached_data(data_type, stock_code) if use_cache else {'error': str(e)}
    
    def get_ai_analysis(self, stock_code: str, analysis_type: str = 'comprehensive', use_cache: bool = True) -> Dict:
        """获取AI分析数据"""
        data_type = 'ai_analysis'
        
        # 标准化股票代码
        try:
            stock_code, _ = normalize_stock_input(stock_code, 'stock')
        except:
            pass
        
        # 使用分析类型区分不同的AI分析
        cache_key = f"{data_type}_{analysis_type}_{stock_code}"
        
        if use_cache:
            try:
                cache_data = self._load_cache()
                if cache_key in cache_data:
                    cache_meta = cache_data[cache_key].get('cache_meta', {})
                    cache_time = datetime.fromisoformat(cache_meta['timestamp'])
                    expire_time = cache_time + timedelta(minutes=self.cache_configs[data_type]['expire_minutes'])
                    
                    if datetime.now() < expire_time:
                        print(f"📋 使用缓存的 {stock_code} {analysis_type} AI分析")
                        return cache_data[cache_key].get('data', {})
            except Exception:
                pass
        
        # AI分析数据需要手动设置，这里返回现有缓存
        print(f"📋 使用现有的 {stock_code} {analysis_type} AI分析")
        try:
            cache_data = self._load_cache()
            return cache_data.get(cache_key, {}).get('data', {})
        except Exception:
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
            cache_data = self._load_cache()
            cache_data[cache_key] = {
                'cache_meta': {
                    'timestamp': datetime.now().isoformat(),
                    'data_type': 'ai_analysis',
                    'stock_code': stock_code,
                    'analysis_type': analysis_type,
                    'expire_minutes': self.cache_configs['ai_analysis']['expire_minutes']
                },
                'data': analysis_data
            }
            self._save_cache(cache_data)
            print(f"💾 {stock_code} {analysis_type} AI分析已缓存")
        except Exception as e:
            print(f"❌ 缓存AI分析失败: {e}")
    
    # =========================
    # 综合报告方法
    # =========================
    
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
        
        # 获取各类数据
        report['basic_info'] = self.get_stock_basic_info(stock_code, use_cache)
        report['kline_data'] = self.get_stock_kline_data(stock_code, 160, use_cache)
        report['news_data'] = self.get_stock_news_data(stock_code, use_cache)
        report['chip_data'] = self.get_stock_chip_data(stock_code, use_cache)
        
        # 获取各种AI分析
        report['ai_analysis'] = {
            'fundamental': self.get_ai_analysis(stock_code, 'fundamental', use_cache),
            'market': self.get_ai_analysis(stock_code, 'market', use_cache),
            'news': self.get_ai_analysis(stock_code, 'news', use_cache),
            'chip': self.get_ai_analysis(stock_code, 'chip', use_cache),
        }
        
        # 生成股票摘要
        report['stock_summary'] = self._generate_stock_summary(report)
        
        print("=" * 60)
        print("✅ 综合股票报告生成完成!")
        
        return report
    
    def _generate_stock_summary(self, report: Dict) -> Dict:
        """生成股票摘要"""
        summary = {}
        
        # 基本信息摘要
        basic = report['basic_info']
        if basic and 'error' not in basic:
            summary['current_price'] = basic.get('current_price', 0)
            summary['change_percent'] = basic.get('change_percent', 0)
            summary['stock_name'] = basic.get('name', '')
            summary['industry'] = basic.get('industry', '')
        
        # 技术面摘要
        kline = report['kline_data']
        if kline and 'error' not in kline:
            indicators = kline.get('indicators', {})
            summary['technical_trend'] = f"{indicators.get('ma_trend', '未知')} | MACD {indicators.get('macd_trend', '未知')}"
            summary['rsi_level'] = self._judge_rsi_level(indicators.get('rsi_14', 50))
        
        # 新闻摘要
        news = report['news_data']
        if news and 'error' not in news:
            summary['news_count'] = news.get('news_count', 0)
        
        # 筹码摘要
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
    
    # =========================
    # 缓存管理方法
    # =========================
    
    def clear_cache(self, stock_code: str = None, data_type: str = None):
        """清理缓存"""
        try:
            cache_data = self._load_cache()
            
            if stock_code and data_type:
                # 清理特定股票的特定数据类型
                cache_key = self._get_cache_key(data_type, stock_code)
                if cache_key in cache_data:
                    del cache_data[cache_key]
                    self._save_cache(cache_data)
                    print(f"✅ 已清理 {stock_code} {self.cache_configs.get(data_type, {}).get('description', data_type)} 缓存")
                else:
                    print(f"ℹ️  {stock_code} {data_type} 缓存不存在")
                    
            elif stock_code:
                # 清理特定股票的所有缓存
                keys_to_remove = [key for key in cache_data.keys() if key.endswith(f"_{stock_code}")]
                for key in keys_to_remove:
                    del cache_data[key]
                if keys_to_remove:
                    self._save_cache(cache_data)
                    print(f"✅ 已清理 {stock_code} 所有缓存 ({len(keys_to_remove)}项)")
                else:
                    print(f"ℹ️  {stock_code} 无缓存数据")
                    
            elif data_type:
                # 清理特定数据类型的所有缓存
                keys_to_remove = [key for key in cache_data.keys() if key.startswith(f"{data_type}_")]
                for key in keys_to_remove:
                    del cache_data[key]
                if keys_to_remove:
                    self._save_cache(cache_data)
                    print(f"✅ 已清理所有 {self.cache_configs.get(data_type, {}).get('description', data_type)} 缓存 ({len(keys_to_remove)}项)")
                else:
                    print(f"ℹ️  无 {data_type} 缓存数据")
                    
            else:
                # 清理所有缓存
                if os.path.exists(self.cache_file):
                    os.remove(self.cache_file)
                    print("✅ 已清理所有股票数据缓存")
                else:
                    print("ℹ️  缓存文件不存在")
                    
        except Exception as e:
            print(f"❌ 清理缓存失败: {e}")
    
    def get_cache_status(self, stock_code: str = None) -> Dict:
        """获取缓存状态"""
        status = {}
        current_time = datetime.now()
        cache_data = self._load_cache()
        
        for cache_key, cache_info in cache_data.items():
            try:
                cache_meta = cache_info.get('cache_meta', {})
                cached_stock_code = cache_meta.get('stock_code', '')
                data_type = cache_meta.get('data_type', '')
                analysis_type = cache_meta.get('analysis_type', '')
                
                # 如果指定了股票代码，只显示该股票的缓存
                if stock_code and cached_stock_code != stock_code:
                    continue
                
                cache_time = datetime.fromisoformat(cache_meta['timestamp'])
                expire_minutes = cache_meta.get('expire_minutes', 60)
                expire_time = cache_time + timedelta(minutes=expire_minutes)
                is_valid = current_time < expire_time
                
                remaining_minutes = (expire_time - current_time).total_seconds() / 60
                if remaining_minutes > 0:
                    remaining_text = f"剩余 {int(remaining_minutes)} 分钟"
                else:
                    remaining_text = "已过期"
                
                display_key = cache_key
                if analysis_type:
                    display_key = f"{cached_stock_code}_{analysis_type}_AI分析"
                
                status[display_key] = {
                    'stock_code': cached_stock_code,
                    'data_type': data_type,
                    'analysis_type': analysis_type,
                    'description': self.cache_configs.get(data_type, {}).get('description', data_type),
                    'valid': is_valid,
                    'cache_time': cache_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'expire_minutes': expire_minutes,
                    'remaining': remaining_text
                }
            except Exception:
                continue
        
        return status
    
    def print_cache_status(self, stock_code: str = None):
        """打印缓存状态"""
        status = self.get_cache_status(stock_code)
        
        print("=" * 70)
        if stock_code:
            print(f"📊 股票 {stock_code} 数据缓存状态")
        else:
            print("📊 股票数据缓存状态")
        print(f"📁 缓存文件: {self.cache_file}")
        print("=" * 70)
        
        if not status:
            if stock_code:
                print(f"ℹ️  股票 {stock_code} 无缓存数据")
            else:
                print("ℹ️  无缓存数据")
        else:
            for key, info in status.items():
                status_icon = "✅" if info['valid'] else "❌"
                print(f"{status_icon} {info['stock_code']:<8} | {info['description']:<12} | {info['remaining']:<15} | 过期: {info['expire_minutes']}分钟")
        
        # 显示缓存文件大小
        try:
            if os.path.exists(self.cache_file):
                file_size = os.path.getsize(self.cache_file) / 1024  # KB
                print(f"💾 缓存文件大小: {file_size:.1f} KB")
            else:
                print("💾 缓存文件: 不存在")
        except Exception:
            pass
        
        print("=" * 70)


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

def get_stock_ai_analysis(stock_code: str, analysis_type: str = 'comprehensive') -> Dict:
    """获取股票AI分析数据"""
    tools = get_stock_tools()
    return tools.get_ai_analysis(stock_code, analysis_type)


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
