"""
A股市场工具 - 统一的数据获取和缓存管理

所有数据都支持智能缓存，避免重复请求
"""

import os
import sys
import warnings
from datetime import datetime
from typing import Dict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

warnings.filterwarnings('ignore')

import akshare as ak
import pandas as pd
import efinance as ef
from stock.stock_utils import get_indicators
from ui.config import FOCUS_INDICES, INDEX_SYMBOL_MAPPING
from utils.kline_cache import cache_manager, KLineData

def fetch_market_sentiment() -> Dict:
    """获取市场情绪数据"""
    sentiment_data = {}
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
    """获取估值指标"""
    print("💰 获取估值指标...")
    
    valuation_data = {}
    
    try:
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
    
    valuation_data['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("   ✓ 估值指标获取完成")
    return valuation_data


def fetch_money_flow_data(debug=False) -> Dict:
    """获取资金流向数据"""
    print("💸 获取资金流向指标...")
    
    money_flow_data = {}
    
    try:
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
    
    money_flow_data['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("   ✓ 资金流向指标获取完成")
    return money_flow_data


def fetch_current_indices() -> Dict:
    """获取当前指数实时数据"""
    print("📊 获取当前指数实时数据...")
    
    indices_data = {}
    
    try:
        print("   获取沪深重要指数...")
        df_indices = ak.stock_zh_index_spot_em('沪深重要指数')
        
        if not df_indices.empty:
            indices_list = []

            for _, row in df_indices.iterrows():
                if str(row.get('名称', '')) not in FOCUS_INDICES:
                    continue
                index_info = {
                    'code': str(row.get('代码', '')),
                    'name': str(row.get('名称', '')),
                    'current_price': float(row.get('最新价', 0)),
                    'change_percent': float(row.get('涨跌幅', 0)),
                    'change_amount': float(row.get('涨跌额', 0)),
                    'volume': float(row.get('成交量', 0)),
                    'turnover': float(row.get('成交额', 0)),
                    'amplitude': float(row.get('振幅', 0)),
                    'high': float(row.get('最高', 0)),
                    'low': float(row.get('最低', 0)),
                    'open': float(row.get('今开', 0)),
                    'prev_close': float(row.get('昨收', 0)),
                    'volume_ratio': float(row.get('量比', 0))
                }
                indices_list.append(index_info)
            
            indices_dict = {}
            for index in indices_list:
                indices_dict[index['name']] = index
            
            indices_data = {
                'indices_dict': indices_dict,
                'total_count': len(indices_dict),
                'data_source': '东方财富-沪深重要指数',
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            print(f"      成功获取 {len(indices_dict)} 个指数数据")
            
            for name in FOCUS_INDICES:
                if name in indices_dict:
                    idx = indices_dict[name]
                    change_sign = '+' if idx['change_percent'] >= 0 else ''
                    print(f"      - {name}: {idx['current_price']:.2f} ({change_sign}{idx['change_percent']:.2f}%)")
        
    except Exception as e:
        print(f"   ❌ 获取指数数据失败: {e}")
        indices_data = {
            'error': str(e),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    print("   ✓ 指数数据获取完成")
    return indices_data


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
        df_margin_sh = ak.macro_china_market_margin_sh()
        if not df_margin_sh.empty:
            latest_sh = df_margin_sh.iloc[-1]
            result.update({
                'margin_sh_balance': float(latest_sh.get('融资融券余额', 0)),
                'margin_sh_buy': float(latest_sh.get('融资余额', 0)),
                'margin_sh_sell': float(latest_sh.get('融券余额', 0)),
                'margin_date': str(latest_sh.get('日期', datetime.now().strftime('%Y-%m-%d'))),
            })
            
            # 计算一周变化
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

def update_index_cache_data(index_name: str = '上证指数', period: int = 250) -> bool:
    """更新指数缓存数据（用于定期更新缓存）"""
    print(f"🔄 更新{index_name}缓存数据...")
    
    try:
        if index_name not in INDEX_SYMBOL_MAPPING:
            raise ValueError(f"不支持的指数名称: {index_name}")
        
        symbol = INDEX_SYMBOL_MAPPING[index_name]
        df_raw = ak.stock_zh_index_daily(symbol=symbol)
        
        if df_raw.empty:
            raise ValueError(f"无法获取{index_name}数据")
        
        # 取最近的period条数据
        df_raw = df_raw.tail(period).copy()
        
        # 数据类型转换
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df_raw.columns:
                df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce')
        
        # 确保date列是日期时间格式
        if 'date' in df_raw.columns:
            df_raw['date'] = pd.to_datetime(df_raw['date'])
        
        # 转换数据格式用于缓存
        kline_data_list = []
        for _, row in df_raw.iterrows():
            # 使用date列作为日期
            if 'date' in df_raw.columns:
                date_str = row['date'].strftime('%Y-%m-%d')
            else:
                # 备用方案
                date_str = datetime.now().strftime('%Y-%m-%d')
            
            kline_data = KLineData(
                symbol=index_name,
                datetime=date_str,
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row['volume']),
                amount=None,
                data_type="index"
            )
            kline_data_list.append(kline_data)
        
        # 更新缓存（智能合并）
        cache_manager.update_index_kline(index_name, kline_data_list)
        
        print(f"   ✓ 成功更新{index_name}缓存数据: {len(kline_data_list)}条")
        return True
        
    except Exception as e:
        print(f"   ❌ 更新{index_name}缓存数据失败: {e}")
        return False


def batch_update_indices_cache(indices: list = None, period: int = 250) -> Dict:
    """批量更新指数缓存数据"""
    if indices is None:
        indices = FOCUS_INDICES
    
    print(f"📊 批量更新指数缓存数据 ({len(indices)}个指数)...")
    
    results = {
        'success_count': 0,
        'failed_count': 0,
        'results': {}
    }
    
    for index_name in indices:
        success = update_index_cache_data(index_name, period)
        results['results'][index_name] = success
        if success:
            results['success_count'] += 1
        else:
            results['failed_count'] += 1
    
    print(f"   ✓ 批量更新完成: 成功 {results['success_count']} 个，失败 {results['failed_count']} 个")
    return results


def fetch_index_technical_indicators(index_name: str = '上证指数', period: int = 100) -> Dict:
    """获取指数技术指标（使用智能缓存）"""
    print(f"📊 获取{index_name}技术指标...")
        
    try:
        if index_name not in INDEX_SYMBOL_MAPPING:
            raise ValueError(f"不支持的指数名称: {index_name}")
        
        # 先尝试从缓存获取数据
        cached_data = cache_manager.get_cached_index_kline(index_name, period)
        
        if cached_data and len(cached_data) >= period:
            print(f"   ✓ 使用缓存数据: {index_name} ({len(cached_data)}条)")
            
            # 将缓存数据转换为DataFrame
            kline_records = []
            for kdata in cached_data:
                kline_records.append({
                    'date': kdata.datetime.split()[0],  # 只取日期部分
                    'open': kdata.open,
                    'high': kdata.high,
                    'low': kdata.low,
                    'close': kdata.close,
                    'volume': kdata.volume
                })
            
            df = pd.DataFrame(kline_records)
            df['date'] = pd.to_datetime(df['date'])
            # 设置date列为索引，用于技术指标计算
            df = df.set_index('date')
            
        else:
            print(f"   获取最新数据: {index_name}")
            symbol = INDEX_SYMBOL_MAPPING[index_name]
            df_raw = ak.stock_zh_index_daily(symbol=symbol)
            
            if df_raw.empty:
                raise ValueError(f"无法获取{index_name}数据")
            
            # 取最近的period条数据
            df_raw = df_raw.tail(period * 2).copy()  # 多取一些数据以备缓存
            
            # 数据类型转换
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df_raw.columns:
                    df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce')
            
            # 确保date列是日期时间格式
            if 'date' in df_raw.columns:
                df_raw['date'] = pd.to_datetime(df_raw['date'])
            
            # 转换数据格式用于缓存
            kline_data_list = []
            for _, row in df_raw.iterrows():
                # 使用date列作为日期
                if 'date' in df_raw.columns:
                    date_str = row['date'].strftime('%Y-%m-%d')
                else:
                    # 备用方案
                    date_str = datetime.now().strftime('%Y-%m-%d')
                
                kline_data = KLineData(
                    symbol=index_name,
                    datetime=date_str,
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['volume']),
                    amount=None,
                    data_type="index"
                )
                kline_data_list.append(kline_data)
            
            # 缓存数据
            cache_manager.cache_index_kline(index_name, kline_data_list)
            
            # 准备用于计算指标的DataFrame  
            df = df_raw.tail(period).copy()
            # 设置date列为索引，用于技术指标计算
            if 'date' in df.columns:
                df = df.set_index('date')
        
        # 计算技术指标
        indicators = get_indicators(df)
        
        # 风险指标计算
        risk_metrics = {}
        if len(df) >= 5:
            try:
                from utils.risk_metrics import calculate_portfolio_risk_summary
                risk_metrics = calculate_portfolio_risk_summary(df, price_col='close')
                if risk_metrics:
                    indicators['risk_metrics'] = risk_metrics
            except ImportError:
                print("   ⚠️  风险指标模块未找到，跳过风险计算")
            except Exception as e:
                print(f"   ⚠️  风险指标计算失败: {e}")

        print(f"   ✓ 成功获取{index_name}技术指标")
        return indicators
        
    except Exception as e:
        print(f"   ❌ 获取{index_name}技术指标失败: {e}")
        return {}