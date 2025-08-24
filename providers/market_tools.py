"""
A股市场工具 - 统一的数据获取和缓存管理

本模块提供A股市场数据的统一接口，包括：
1. 技术指标分析
2. 市场情绪指标
3. 估值指标
4. 资金流向指标
5. 融资融券数据
6. AI分析数据

所有数据都支持智能缓存，避免重复请求
"""

import json
import os
import sys
import warnings
import traceback
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

# 添加路径以便导入
sys.path.append('/app')
warnings.filterwarnings('ignore')

# 导入必要的模块
import akshare as ak
import pandas as pd
import efinance as ef
from providers.stock_tools import get_indicators


# =========================
# 独立的数据获取函数（纯外部API调用）
# =========================

def fetch_market_sentiment() -> Dict:
    """获取市场情绪数据的具体实现"""
    sentiment_data = {}
    #return sentiment_data # for test 250824
    try:
        # 1. 涨跌家数统计
        print("   获取涨跌家数...")
        df_stocks = ef.stock.get_realtime_quotes()
        df_stocks = df_stocks.dropna(subset=['涨跌幅'])
        df_stocks["涨跌幅"] = pd.to_numeric(df_stocks["涨跌幅"], errors="coerce")
        
        up_count = (df_stocks["涨跌幅"] > 0).sum()
        down_count = (df_stocks["涨跌幅"] < 0).sum()
        flat_count = (df_stocks["涨跌幅"] == 0).sum()
        total_count = len(df_stocks)
        
        sentiment_data.update({
            'up_stocks': int(up_count),
            'down_stocks': int(down_count),
            'flat_stocks': int(flat_count),
            'total_stocks': int(total_count),
            'up_ratio': float(up_count / total_count) if total_count > 0 else 0,
            'down_ratio': float(down_count / total_count) if total_count > 0 else 0,
        })
        
        print(f"      上涨: {up_count} | 下跌: {down_count} | 平盘: {flat_count}")
        
    except Exception as e:
        print(f"   ❌ 获取涨跌家数失败: {e}")
            
    sentiment_data['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return sentiment_data


def fetch_valuation_data(debug=False) -> Dict:
    """
    获取估值指标
    
    Returns:
        包含估值指标的字典
    """
    print("💰 获取估值指标...")
    
    valuation_data = {}
    
    try:
        # 沪深300估值
        print("   获取沪深300估值...")
        df_hs300 = ak.stock_zh_index_value_csindex("000300")
        if not df_hs300.empty:
            if debug:
                print(df_hs300)
            latest_hs300 = df_hs300.iloc[-1]
            valuation_data.update({
                'hs300_pe': float(latest_hs300.get('市盈率1', 0)),
                'hs300_dividend_yield': float(latest_hs300.get('股息率1', 0)),
                'hs300_date': str(latest_hs300.get('日期', datetime.now().strftime('%Y-%m-%d'))),
            })
            print(f"      沪深300 PE: {valuation_data['hs300_pe']:.2f}")
        
    except Exception as e:
        print(f"   ❌ 获取沪深300估值失败: {e}")
    
    # 添加更新时间
    valuation_data['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("   ✓ 估值指标获取完成")
    return valuation_data


def fetch_money_flow_data(debug=False) -> Dict:
    """获取资金流向数据的具体实现"""
    print("💸 获取资金流向指标...")
    
    money_flow_data = {}
    
    try:
        # M2货币供应量
        print("   获取M2数据...")
        df_m2 = ak.macro_china_money_supply()
        if debug:
            print(df_m2.head())
        if not df_m2.empty:
            latest_m2 = df_m2.iloc[0]
            if debug:
                print(latest_m2)
            money_flow_data.update({
                'm2_amount': float(latest_m2.get('货币和准货币(M2)-数量(亿元)', 0)),
                'm2_growth': float(latest_m2.get('货币和准货币(M2)-同比增长', 0)),
                'm1_amount': float(latest_m2.get('货币(M1)-数量(亿元)', 0)),
                'm1_growth': float(latest_m2.get('货币(M1)-同比增长', 0)),
                'm2_date': str(latest_m2.get('月份', datetime.now().strftime('%Y-%m'))),
            })
            print(f"      M2余额: {money_flow_data['m2_amount']/10000:.2f}万亿 | 同比增长: {money_flow_data['m2_growth']:.2f}%")

    except Exception as e:
        print(f"   ❌ 获取M2数据失败: {e}")
    
    # 添加更新时间
    money_flow_data['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("   ✓ 资金流向指标获取完成")
    return money_flow_data


def fetch_margin_data_unified(include_historical: bool = False) -> Dict:
    """统一的融资融券数据获取方法"""
    result = {
        'margin_balance': 0,
        'margin_buy_balance': 0,
        'margin_sell_balance': 0,
        'margin_sh_balance': 0,
        'margin_sh_buy': 0,
        'margin_sh_sell': 0,
        'margin_sz_balance': 0,
        'margin_sz_buy': 0,
        'margin_sz_sell': 0,
        'margin_date': datetime.now().strftime('%Y-%m-%d'),
    }
    
    sh_data = {}
    sz_data = {}
    
    try:
        # 获取上交所数据
        df_margin_sh = ak.macro_china_market_margin_sh()
        if not df_margin_sh.empty:
            latest_sh = df_margin_sh.iloc[-1]
            result.update({
                'margin_sh_balance': float(latest_sh.get('融资融券余额', 0)),
                'margin_sh_buy': float(latest_sh.get('融资余额', 0)),
                'margin_sh_sell': float(latest_sh.get('融券余额', 0)),
                'margin_date': str(latest_sh.get('日期', datetime.now().strftime('%Y-%m-%d'))),
            })
            
            if include_historical and len(df_margin_sh) >= 7:
                week_ago_sh = df_margin_sh.iloc[-7]
                weekly_change_sh = result['margin_sh_buy'] - float(week_ago_sh.get('融资余额', 0))
                sh_data = {
                    'weekly_change': float(weekly_change_sh),
                    'change_ratio': float(weekly_change_sh / (result['margin_sh_buy'] - weekly_change_sh) * 100) if (result['margin_sh_buy'] - weekly_change_sh) > 0 else 0
                }
            
    except Exception as e:
        import traceback
        traceback.print_exc()               
        print(f"      ❌ 获取上交所融资融券失败: {e}")
    
    try:
        # 获取深交所数据
        df_margin_sz = ak.macro_china_market_margin_sz()
        if not df_margin_sz.empty:
            latest_sz = df_margin_sz.iloc[-1]
            result.update({
                'margin_sz_balance': float(latest_sz.get('融资融券余额', 0)),
                'margin_sz_buy': float(latest_sz.get('融资余额', 0)),
                'margin_sz_sell': float(latest_sz.get('融券余额', 0)),
            })
            
            if include_historical and len(df_margin_sz) >= 7:
                week_ago_sz = df_margin_sz.iloc[-7]
                weekly_change_sz = result['margin_sz_buy'] - float(week_ago_sz.get('融资余额', 0))
                sz_data = {
                    'weekly_change': float(weekly_change_sz),
                    'change_ratio': float(weekly_change_sz / (result['margin_sz_buy'] - weekly_change_sz) * 100) if (result['margin_sz_buy'] - weekly_change_sz) > 0 else 0
                }
            
    except Exception as e:
        print(f"      ❌ 获取深交所融资融券失败: {e}")
    
    # 汇总两市数据
    total_margin_balance = result['margin_sh_balance'] + result['margin_sz_balance']
    total_margin_buy = result['margin_sh_buy'] + result['margin_sz_buy']
    total_margin_sell = result['margin_sh_sell'] + result['margin_sz_sell']
    
    result.update({
        'margin_balance': float(total_margin_balance),
        'margin_buy_balance': float(total_margin_buy),
        'margin_sell_balance': float(total_margin_sell),
    })
    
    if include_historical:
        total_weekly_change = sh_data.get('weekly_change', 0) + sz_data.get('weekly_change', 0)
        result.update({
            'weekly_change': float(total_weekly_change),
            'change_ratio': float(total_weekly_change / (total_margin_buy - total_weekly_change) * 100) if (total_margin_buy - total_weekly_change) > 0 else 0,
            'shanghai': sh_data,
            'shenzhen': sz_data,
        })
    
    return result


class MarketTools:
    """统一的市场数据工具类"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        """初始化市场工具"""
        self.cache_dir = cache_dir
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.cache_file = os.path.join(project_dir, cache_dir, "market_data.json")
        
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
        
        # 支持的指数
        self.indices = {
            '上证指数': '000001',
            '深证成指': '399001', 
            '创业板指': '399006',
            '沪深300': '000300',
            '中证500': '000905',
            '科创50': '000688'
        }
        
        # 缓存配置
        self.cache_configs = {
            'market_sentiment': {'expire_minutes': 15, 'description': '市场情绪指标'},
            'valuation_data': {'expire_minutes': 1440, 'description': '估值指标'},
            'money_flow_data': {'expire_minutes': 43200, 'description': '资金流向指标'},
            'margin_data': {'expire_minutes': 60, 'description': '融资融券数据'},
            'ai_analysis': {'expire_minutes': 180, 'description': 'AI市场分析'},
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
    
    def _save_cache(self, cache_data: Dict):
        """保存缓存文件"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存缓存失败: {e}")
    
    def _is_cache_valid(self, data_type: str) -> bool:
        """检查缓存是否有效"""
        try:
            cache_data = self._load_cache()
            if data_type not in cache_data:
                return False
            
            cache_meta = cache_data[data_type].get('cache_meta', {})
            cache_time = datetime.fromisoformat(cache_meta['timestamp'])
            expire_minutes = self.cache_configs[data_type]['expire_minutes']
            expire_time = cache_time + timedelta(minutes=expire_minutes)
            
            return datetime.now() < expire_time
        except Exception:
            return False
    
    def _get_cached_data(self, data_type: str) -> Dict:
        """获取缓存数据"""
        try:
            cache_data = self._load_cache()
            return cache_data.get(data_type, {}).get('data', {})
        except Exception:
            return {}
    
    def _save_cached_data(self, data_type: str, data: Dict):
        """保存数据到缓存"""
        try:
            cache_data = self._load_cache()
            cache_data[data_type] = {
                'cache_meta': {
                    'timestamp': datetime.now().isoformat(),
                    'data_type': data_type,
                    'expire_minutes': self.cache_configs[data_type]['expire_minutes']
                },
                'data': data
            }
            self._save_cache(cache_data)
            print(f"💾 {self.cache_configs[data_type]['description']}已缓存")
        except Exception as e:
            print(f"❌ 缓存数据失败: {e}")
    
    # =========================
    # 数据获取方法（带缓存）
    # =========================
    
    def get_market_sentiment(self, use_cache: bool = True, force_refresh: bool = False) -> Dict:
        """获取市场情绪指标"""
        data_type = 'market_sentiment'
        
        # 检查缓存
        if use_cache and not force_refresh and self._is_cache_valid(data_type):
            print(f"📋 使用缓存的{self.cache_configs[data_type]['description']}")
            return self._get_cached_data(data_type)
        
        # 获取新数据
        print(f"📡 获取{self.cache_configs[data_type]['description']}...")
        try:
            data = fetch_market_sentiment()
            if use_cache:
                self._save_cached_data(data_type, data)
            return data
        except Exception as e:
            print(f"❌ 获取市场情绪失败: {e}")
            # 返回缓存数据作为备份
            return self._get_cached_data(data_type) if use_cache else {}
    
    def get_valuation_data(self, use_cache: bool = True, force_refresh: bool = False) -> Dict:
        """获取估值指标"""
        data_type = 'valuation_data'
        
        if use_cache and not force_refresh and self._is_cache_valid(data_type):
            print(f"📋 使用缓存的{self.cache_configs[data_type]['description']}")
            return self._get_cached_data(data_type)
        
        print(f"📡 获取{self.cache_configs[data_type]['description']}...")
        try:
            data = fetch_valuation_data()
            if use_cache:
                self._save_cached_data(data_type, data)
            return data
        except Exception as e:
            print(f"❌ 获取估值数据失败: {e}")
            return self._get_cached_data(data_type) if use_cache else {}
    
    def get_money_flow_data(self, use_cache: bool = True, force_refresh: bool = False, debug: bool = False) -> Dict:
        """获取资金流向指标"""
        data_type = 'money_flow_data'
        
        if use_cache and not force_refresh and self._is_cache_valid(data_type):
            print(f"📋 使用缓存的{self.cache_configs[data_type]['description']}")
            return self._get_cached_data(data_type)
        
        print(f"📡 获取{self.cache_configs[data_type]['description']}...")
        try:
            data = fetch_money_flow_data(debug=debug)
            if use_cache:
                self._save_cached_data(data_type, data)
            return data
        except Exception as e:
            print(f"❌ 获取资金流向失败: {e}")
            return self._get_cached_data(data_type) if use_cache else {}
    
    def get_margin_data(self, use_cache: bool = True, force_refresh: bool = False) -> Dict:
        """获取融资融券数据"""
        data_type = 'margin_data'
        
        if use_cache and not force_refresh and self._is_cache_valid(data_type):
            print(f"📋 使用缓存的{self.cache_configs[data_type]['description']}")
            return self._get_cached_data(data_type)
        
        print(f"📡 获取{self.cache_configs[data_type]['description']}...")
        try:
            data = fetch_margin_data_unified(include_historical=True)
            if use_cache:
                self._save_cached_data(data_type, data)
            return data
        except Exception as e:
            print(f"❌ 获取融资融券失败: {e}")
            return self._get_cached_data(data_type) if use_cache else {}
    
    def get_ai_analysis(self, use_cache: bool = True, index_name: str = None, force_regenerate: bool = False) -> Dict:
        """获取AI分析数据"""
        data_type = 'ai_analysis'
        
        # 如果指定了index_name并且需要重新生成AI分析
        if index_name and force_regenerate:
            return self._generate_ai_analysis(index_name)
        
        if use_cache and self._is_cache_valid(data_type):
            print(f"📋 使用缓存的{self.cache_configs[data_type]['description']}")
            return self._get_cached_data(data_type)
        
        # AI分析数据需要手动设置，这里返回现有缓存
        cached_data = self._get_cached_data(data_type)
        if cached_data:
            print(f"📋 使用现有的{self.cache_configs[data_type]['description']}")
        return cached_data
    
    def set_ai_analysis(self, analysis_data: Dict):
        """设置AI分析数据"""
        analysis_data['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._save_cached_data('ai_analysis', analysis_data)
    
    # =========================
    # 技术指标分析（不缓存）
    # =========================
    
    def get_index_technical_indicators(self, index_name: str = '上证指数', period: int = 100) -> Dict:
        """获取指数技术指标（实时数据，不缓存）"""
        print(f"📊 获取{index_name}技术指标...")
        
        try:
            if index_name not in self.indices:
                raise ValueError(f"不支持的指数名称: {index_name}")
            
            # 根据指数名称获取数据
            if index_name == '上证指数':
                df_raw = ak.stock_zh_index_daily(symbol="sh000001")
            elif index_name == '深证成指':
                df_raw = ak.stock_zh_index_daily(symbol="sz399001")
            elif index_name == '创业板指':
                df_raw = ak.stock_zh_index_daily(symbol="sz399006")
            elif index_name == '沪深300':
                df_raw = ak.stock_zh_index_daily(symbol="sh000300")
            elif index_name == '中证500':
                df_raw = ak.stock_zh_index_daily(symbol="sh000905")
            elif index_name == '科创50':
                df_raw = ak.stock_zh_index_daily(symbol="sh000688")
            
            if df_raw.empty:
                raise ValueError(f"无法获取{index_name}数据")
            
            # 获取最近的数据
            df = df_raw.tail(period).copy()
            
            # 重命名列以符合stockstats要求
            df = df.rename(columns={
                'open': 'open',
                'close': 'close', 
                'high': 'high',
                'low': 'low',
                'volume': 'volume'
            })
            
            # 确保数据类型正确
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            indicators = get_indicators(df)
            
            print(f"   ✓ 成功获取{index_name}技术指标")
            return indicators
            
        except Exception as e:
            print(f"   ❌ 获取{index_name}技术指标失败: {e}")
            return {}
    
    # =========================
    # 缓存管理方法
    # =========================
    
    def clear_cache(self, data_type: Optional[str] = None):
        """清理缓存"""
        if data_type:
            if data_type not in self.cache_configs:
                print(f"❌ 未知的数据类型: {data_type}")
                return
            
            try:
                cache_data = self._load_cache()
                if data_type in cache_data:
                    del cache_data[data_type]
                    self._save_cache(cache_data)
                    print(f"✅ 已清理{self.cache_configs[data_type]['description']}缓存")
                else:
                    print(f"ℹ️ {self.cache_configs[data_type]['description']}缓存不存在")
            except Exception as e:
                print(f"❌ 清理缓存失败: {e}")
        else:
            # 清理所有缓存
            try:
                if os.path.exists(self.cache_file):
                    os.remove(self.cache_file)
                    print("✅ 已清理所有缓存数据")
                else:
                    print("ℹ️ 缓存文件不存在")
            except Exception as e:
                print(f"❌ 清理缓存失败: {e}")
    
    def get_cache_status(self) -> Dict:
        """获取缓存状态"""
        status = {}
        current_time = datetime.now()
        cache_data = self._load_cache()
        
        for data_type, config in self.cache_configs.items():
            if data_type in cache_data:
                is_valid = self._is_cache_valid(data_type)
                
                try:
                    cache_meta = cache_data[data_type].get('cache_meta', {})
                    cache_time_str = cache_meta.get('timestamp', '')
                    cache_time = datetime.fromisoformat(cache_time_str)
                    expire_time = cache_time + timedelta(minutes=config['expire_minutes'])
                    
                    if is_valid:
                        remaining_minutes = int((expire_time - current_time).total_seconds() / 60)
                        remaining_text = f"{remaining_minutes}分钟后过期"
                    else:
                        overdue_minutes = int((current_time - expire_time).total_seconds() / 60)
                        remaining_text = f"已过期{overdue_minutes}分钟"
                        
                except Exception:
                    cache_time_str = "解析失败"
                    remaining_text = "未知"
                
                status[data_type] = {
                    'description': config['description'],
                    'exists': True,
                    'valid': is_valid,
                    'cache_time': cache_time_str,
                    'expire_minutes': config['expire_minutes'],
                    'remaining': remaining_text
                }
            else:
                status[data_type] = {
                    'description': config['description'],
                    'exists': False,
                    'valid': False,
                    'cache_time': None,
                    'expire_minutes': config['expire_minutes'],
                    'remaining': "无缓存"
                }
        
        return status
    
    def print_cache_status(self):
        """打印缓存状态"""
        status = self.get_cache_status()
        
        print("=" * 70)
        print("📊 市场数据缓存状态")
        print(f"📁 缓存文件: {self.cache_file}")
        print("=" * 70)
        
        for data_type, info in status.items():
            print("OOOOOOOOOOOOOOO", data_type, info)
            status_icon = "✅" if info['valid'] else ("📋" if info['exists'] else "❌")
            print(f"{status_icon} {info['description']:<12} | {info['remaining']:<15} | 过期时间: {info['expire_minutes']}分钟")
        
        # 显示缓存文件大小
        try:
            if os.path.exists(self.cache_file):
                file_size = os.path.getsize(self.cache_file)
                size_text = f"{file_size/1024:.1f}KB" if file_size > 1024 else f"{file_size}B"
                print(f"\n📦 缓存文件大小: {size_text}")
            else:
                print(f"\n📦 缓存文件不存在")
        except Exception:
            pass
        
        print("=" * 70)
    
    def refresh_all_cache(self):
        """刷新所有缓存数据"""
        print("🔄 开始刷新所有缓存数据...")
        
        self.get_market_sentiment(use_cache=True, force_refresh=True)
        self.get_valuation_data(use_cache=True, force_refresh=True)
        self.get_money_flow_data(use_cache=True, force_refresh=True)
        self.get_margin_data(use_cache=True, force_refresh=True)
        
        print("✅ 所有缓存数据刷新完成!")
        self.print_cache_status()
    
    # =========================
    # 综合报告方法
    # =========================
    
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
        
        # 获取各类指标
        report['technical_indicators'] = self.get_index_technical_indicators(index_name)
        report['sentiment_indicators'] = self.get_market_sentiment(use_cache)
        report['valuation_indicators'] = self.get_valuation_data(use_cache)
        report['money_flow_indicators'] = self.get_money_flow_data(use_cache)
        report['margin_detail'] = self.get_margin_data(use_cache)
        report['ai_analysis'] = self.get_ai_analysis(use_cache)
        
        # 生成市场摘要
        report['market_summary'] = self._generate_market_summary(report)
        
        print("=" * 60)
        print("✅ 综合市场报告生成完成!")
        
        return report
    
    def _generate_market_summary(self, report: Dict) -> Dict:
        """生成市场摘要"""
        summary = {}
        
        # 技术面摘要
        tech = report['technical_indicators']
        if tech:
            summary['technical_trend'] = f"{tech.get('ma_trend', '未知')} | MACD {tech.get('macd_trend', '未知')}"
            summary['current_price'] = tech.get('latest_close', 0)
            summary['rsi_level'] = self._judge_rsi_level(tech.get('rsi_14', 50))
        
        # 情绪面摘要
        sentiment = report['sentiment_indicators']
        if sentiment:
            up_ratio = sentiment.get('up_ratio', 0) * 100
            summary['market_sentiment'] = f"上涨家数占比 {up_ratio:.1f}%"
        
        # 估值面摘要
        valuation = report['valuation_indicators']
        if valuation:
            pe = valuation.get('hs300_pe', 0)
            summary['valuation_level'] = f"沪深300 PE {pe:.2f}"
        
        # 资金面摘要
        money = report['money_flow_indicators']
        if money:
            m2_growth = money.get('m2_growth', 0)
            summary['liquidity_condition'] = f"M2同比增长 {m2_growth:.1f}%"
        
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
    
    def _generate_ai_analysis(self, index_name: str) -> Dict:
        """生成AI分析数据"""
        try:
            from analysis.stock_ai_analysis import generate_index_analysis_report
            
            # 获取综合市场报告数据
            market_report_data = self.get_comprehensive_market_report(use_cache=True, index_name=index_name)
            
            print(f"🤖 正在生成{index_name}的AI分析报告...")
            
            # 调用AI分析函数
            ai_report, timestamp = generate_index_analysis_report(
                index_name,
                index_name, 
                market_report_data
            )
            
            # 构建AI分析数据
            ai_data = {
                'report': ai_report,
                'timestamp': timestamp,
                'index_name': index_name,
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 保存到缓存
            self._save_cached_data('ai_analysis', ai_data)
            
            print(f"✅ AI分析报告生成完成")
            return ai_data
            
        except Exception as e:
            print(f"❌ 生成AI分析失败: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'index_name': index_name
            }

# =========================
# 全局实例和便捷函数
# =========================

# 全局市场工具实例
_market_tools = None

def get_market_tools() -> MarketTools:
    """获取全局市场工具实例"""
    global _market_tools
    if _market_tools is None:
        _market_tools = MarketTools()
    return _market_tools

def show_cache_status():
    """显示缓存状态"""
    tools = get_market_tools()
    tools.print_cache_status()

def clear_market_cache(data_type: str = None):
    """清理市场数据缓存"""
    tools = get_market_tools()
    tools.clear_cache(data_type)

def refresh_all_cache():
    """刷新所有缓存数据"""
    tools = get_market_tools()
    tools.refresh_all_cache()

def set_ai_market_analysis(analysis_data: Dict):
    """设置AI市场分析数据"""
    tools = get_market_tools()
    tools.set_ai_analysis(analysis_data)

def get_ai_market_analysis() -> Dict:
    """获取AI市场分析数据"""
    tools = get_market_tools()
    return tools.get_ai_analysis()

# =========================
# 报告格式化函数
# =========================

def get_market_report(report: Dict) -> str:
    """生成市场报告字符串"""
    lines = []
    lines.append(f"\n📊 A股市场综合报告")
    lines.append(f"🕐 报告时间: {report['report_time']}")
    lines.append(f"🎯 关注指数: {report['focus_index']}")
    lines.append("=" * 80)
    
    # 技术指标
    tech = report['technical_indicators']
    if tech:
        lines.append(f"\n📈 技术指标分析:")
        latest_close = tech.get('latest_close', 'N/A')
        if isinstance(latest_close, (int, float)):
            lines.append(f"   当前点位: {latest_close:.2f}")
        else:
            lines.append(f"   当前点位: {latest_close}")
        lines.append(f"   MA趋势: {tech.get('ma_trend', 'N/A')}")
        lines.append(f"   MACD趋势: {tech.get('macd_trend', 'N/A')}")
        rsi_14 = tech.get('rsi_14', 'N/A')
        if isinstance(rsi_14, (int, float)):
            lines.append(f"   RSI(14): {rsi_14:.2f}")
        else:
            lines.append(f"   RSI(14): {rsi_14}")
    
    # 市场情绪
    sentiment = report['sentiment_indicators']
    if sentiment:
        lines.append(f"\n😊 市场情绪指标:")
        lines.append(f"   涨跌家数: ↗{sentiment.get('up_stocks', 'N/A')} | ↘{sentiment.get('down_stocks', 'N/A')} | →{sentiment.get('flat_stocks', 'N/A')}")
        up_ratio = sentiment.get('up_ratio', 0)
        lines.append(f"   上涨占比: {up_ratio*100:.1f}%")
    
    # 估值水平
    valuation = report['valuation_indicators']
    if valuation:
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
    
    # 资金面
    money = report['money_flow_indicators']
    if money:
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
    
    # 融资融券数据
    margin_data = report['margin_detail']
    if margin_data:
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
    
    # AI分析
    ai_analysis = report.get('ai_analysis', {})
    if ai_analysis:
        lines.append(f"\n🤖 AI市场分析:")
        lines.append(f"   市场趋势: {ai_analysis.get('market_trend', 'N/A')}")
        lines.append(f"   风险评估: {ai_analysis.get('risk_assessment', 'N/A')}")
        suggestions = ai_analysis.get('suggestions', [])
        if suggestions:
            lines.append(f"   投资建议: {'; '.join(suggestions[:3])}")
    
    lines.append("=" * 80)
    
    return '\n'.join(lines)


if __name__ == "__main__":
    # 测试用例
    print("🧪 测试统一市场工具模块...")
    
    tools = get_market_tools()
    
    print("\n1. 显示缓存状态:")
    tools.print_cache_status()
        
    print("\n4. 显示更新后的缓存状态:")
    tools.print_cache_status()
    
    print("\n✅ 测试完成!")
