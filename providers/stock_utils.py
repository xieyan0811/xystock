import akshare as ak
import os
import pandas as pd
import json
from pathlib import Path
import time
from datetime import datetime
from typing import Dict, Any
from stockstats import wrap

# 全局变量，用于缓存股票代码和名称的映射关系
_STOCK_CODE_NAME_MAP = {}
_STOCK_NAME_CODE_MAP = {}
_HK_STOCK_CODE_NAME_MAP = {}
_HK_STOCK_NAME_CODE_MAP = {}
_INDEX_CODE_NAME_MAP = {
    '000001': '上证指数',
    '399001': '深证成指', 
    '399006': '创业板指',
    '000300': '沪深300',
    '000905': '中证500',
    '000688': '科创50'
}
_INDEX_NAME_CODE_MAP = {
    '上证指数': '000001',
    '深证成指': '399001', 
    '创业板指': '399006',
    '沪深300': '000300',
    '中证500': '000905',
    '科创50': '000688'
}
_LAST_UPDATE_TIME = 0
_HK_LAST_UPDATE_TIME = 0
_MAP_FILE_PATH = os.path.join(Path(__file__).parent.parent, 'data', 'cache', 'stock_code_name_map.json')
_HK_MAP_FILE_PATH = os.path.join(Path(__file__).parent.parent, 'data', 'cache', 'hk_stock_code_name_map.json')

def _ensure_dir_exists(file_path):
    """确保文件目录存在"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

def _load_stock_map(force_download=False):
    """加载股票代码和名称的映射关系"""
    global _STOCK_CODE_NAME_MAP, _STOCK_NAME_CODE_MAP, _LAST_UPDATE_TIME
    
    current_time = time.time()
    if _STOCK_CODE_NAME_MAP and (current_time - _LAST_UPDATE_TIME < 86400):  # 86400秒 = 24小时
        return
    
    # 尝试从本地文件加载
    try:
        if os.path.exists(_MAP_FILE_PATH) and not force_download:
            with open(_MAP_FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _STOCK_CODE_NAME_MAP = data.get('code_to_name', {})
                _STOCK_NAME_CODE_MAP = data.get('name_to_code', {})
                _LAST_UPDATE_TIME = data.get('update_time', 0)
                
                if current_time - _LAST_UPDATE_TIME < 604800:
                    return
    except Exception as e:
        print(f"加载股票映射文件失败: {e}")
    
    # 重新获取股票映射数据
    try:
        print("正在更新股票代码与名称映射表...")
        
        stock_info_a = ak.stock_info_a_code_name()
        
        for _, row in stock_info_a.iterrows():
            code = row['code']
            name = row['name']
            _STOCK_CODE_NAME_MAP[code] = name
            _STOCK_NAME_CODE_MAP[name] = code
        
        # 合并指数映射数据
        _STOCK_CODE_NAME_MAP.update(_INDEX_CODE_NAME_MAP)
        _STOCK_NAME_CODE_MAP.update(_INDEX_NAME_CODE_MAP)
        
        # 保存到本地文件
        _ensure_dir_exists(_MAP_FILE_PATH)
        with open(_MAP_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump({
                'code_to_name': _STOCK_CODE_NAME_MAP,
                'name_to_code': _STOCK_NAME_CODE_MAP,
                'update_time': current_time
            }, f, ensure_ascii=False, indent=2)
            
        _LAST_UPDATE_TIME = current_time
        print(f"股票映射表更新完成，共有 {len(_STOCK_CODE_NAME_MAP)} 个股票信息")
    except Exception as e:
        print(f"获取股票映射关系失败: {e}")

def _load_hk_stock_map(force_download=False):
    """加载港股通股票代码和名称的映射关系"""
    global _HK_STOCK_CODE_NAME_MAP, _HK_STOCK_NAME_CODE_MAP, _HK_LAST_UPDATE_TIME
    
    current_time = time.time()
    if _HK_STOCK_CODE_NAME_MAP and (current_time - _HK_LAST_UPDATE_TIME < 86400):
        return
    
    # 尝试从本地文件加载
    try:
        if os.path.exists(_HK_MAP_FILE_PATH) and not force_download:
            with open(_HK_MAP_FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _HK_STOCK_CODE_NAME_MAP = data.get('code_to_name', {})
                _HK_STOCK_NAME_CODE_MAP = data.get('name_to_code', {})
                _HK_LAST_UPDATE_TIME = data.get('update_time', 0)
                
                if current_time - _HK_LAST_UPDATE_TIME < 604800:
                    return
    except Exception as e:
        print(f"加载港股通映射文件失败: {e}")
    
    # 重新获取港股通数据
    try:
        print("正在更新港股通股票代码与名称映射表...")
        
        hk_stock_info = ak.stock_hk_ggt_components_em()
        
        for _, row in hk_stock_info.iterrows():
            code = row['代码']
            name = row['名称']
            _HK_STOCK_CODE_NAME_MAP[code] = name
            _HK_STOCK_NAME_CODE_MAP[name] = code
        
        _ensure_dir_exists(_HK_MAP_FILE_PATH)
        with open(_HK_MAP_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump({
                'code_to_name': _HK_STOCK_CODE_NAME_MAP,
                'name_to_code': _HK_STOCK_NAME_CODE_MAP,
                'update_time': current_time
            }, f, ensure_ascii=False, indent=2)
            
        _HK_LAST_UPDATE_TIME = current_time
        print(f"港股通映射表更新完成，共有 {len(_HK_STOCK_CODE_NAME_MAP)} 个港股通股票信息")
    except Exception as e:
        print(f"获取港股通映射关系失败: {e}")

def update_hk_stock_map():
    """手动更新港股通股票映射表"""
    print("开始更新港股通股票映射表...")
    _load_hk_stock_map(force_download=True)
    print("港股通股票映射表更新完成")

def get_hk_stock_info():
    """获取当前港股通映射信息"""
    _load_hk_stock_map()
    return {
        'total_count': len(_HK_STOCK_CODE_NAME_MAP),
        'update_time': _HK_LAST_UPDATE_TIME,
        'sample_stocks': dict(list(_HK_STOCK_CODE_NAME_MAP.items())[:10])
    }

def _find_fuzzy_match(target, mapping_dict):
    """模糊匹配辅助函数"""
    matched_items = [key for key in mapping_dict.keys() if target in key]
    return mapping_dict[matched_items[0]] if matched_items else None

def get_stock_code(stock_name_or_code, security_type='stock'):
    """
    获取证券代码
    
    Args:
        stock_name_or_code: 证券名称或代码
        security_type: 证券类型，可选值为'stock'(股票)、'index'(指数)或'hk'(港股通)，默认为'stock'
        
    Returns:
        证券代码，如果输入已经是代码则直接返回，如果是名称则转换为代码
    """
    if not stock_name_or_code:
        return None
    
    _load_stock_map()
    
    # 处理指数类型
    if security_type == 'index':
        return (stock_name_or_code if stock_name_or_code in _INDEX_CODE_NAME_MAP 
                else _INDEX_NAME_CODE_MAP.get(stock_name_or_code) 
                or _find_fuzzy_match(stock_name_or_code, _INDEX_NAME_CODE_MAP)
                or stock_name_or_code)
    
    # 处理港股通类型
    elif security_type == 'hk':
        _load_hk_stock_map()
        return (stock_name_or_code if stock_name_or_code in _HK_STOCK_CODE_NAME_MAP 
                else _HK_STOCK_NAME_CODE_MAP.get(stock_name_or_code)
                or _find_fuzzy_match(stock_name_or_code, _HK_STOCK_NAME_CODE_MAP)
                or stock_name_or_code)
    
    # 默认查找所有类型
    _load_hk_stock_map()
    
    # 直接查找代码映射
    if stock_name_or_code in _STOCK_CODE_NAME_MAP or stock_name_or_code in _HK_STOCK_CODE_NAME_MAP:
        return stock_name_or_code
    
    # 查找名称映射
    return (_STOCK_NAME_CODE_MAP.get(stock_name_or_code) 
            or _HK_STOCK_NAME_CODE_MAP.get(stock_name_or_code)
            or _find_fuzzy_match(stock_name_or_code, _STOCK_NAME_CODE_MAP)
            or _find_fuzzy_match(stock_name_or_code, _HK_STOCK_NAME_CODE_MAP)
            or stock_name_or_code)

def get_stock_name(stock_name_or_code, security_type='stock'):
    """
    获取证券名称
    
    Args:
        stock_name_or_code: 证券名称或代码
        security_type: 证券类型，可选值为'stock'(股票)、'index'(指数)或'hk'(港股通)，默认为'stock'
        
    Returns:
        证券名称，如果输入已经是名称则直接返回，如果是代码则转换为名称
    """
    if not stock_name_or_code:
        return None
    
    _load_stock_map()
    
    # 处理指数类型
    if security_type == 'index':
        return (stock_name_or_code if stock_name_or_code in _INDEX_NAME_CODE_MAP 
                else _INDEX_CODE_NAME_MAP.get(stock_name_or_code)
                or _find_fuzzy_match(stock_name_or_code, _INDEX_CODE_NAME_MAP)
                or stock_name_or_code)
    
    # 处理港股通类型
    elif security_type == 'hk':
        _load_hk_stock_map()
        return (stock_name_or_code if stock_name_or_code in _HK_STOCK_NAME_CODE_MAP
                else _HK_STOCK_CODE_NAME_MAP.get(stock_name_or_code)
                or _find_fuzzy_match(stock_name_or_code, _HK_STOCK_CODE_NAME_MAP)
                or stock_name_or_code)
    
    # 默认查找所有类型
    _load_hk_stock_map()
    
    # 直接查找名称映射
    if stock_name_or_code in _STOCK_NAME_CODE_MAP or stock_name_or_code in _HK_STOCK_NAME_CODE_MAP:
        return stock_name_or_code
    
    # 查找代码映射
    return (_STOCK_CODE_NAME_MAP.get(stock_name_or_code)
            or _HK_STOCK_CODE_NAME_MAP.get(stock_name_or_code)
            or stock_name_or_code)

def normalize_stock_input(stock_input, security_type='stock'):
    """标准化证券输入，返回 (stock_code, stock_name)"""
    code = get_stock_code(stock_input, security_type)
    name = get_stock_name(code, security_type)
    return code, name

def explain_cyq_data(stock_code):
    """解释筹码集中度数据"""
    try:
        cyq_data = ak.stock_cyq_em(stock_code)
        
        if cyq_data is None or cyq_data.empty:
            print(f"无法获取 {stock_code} 的筹码数据")
            return
        
        latest = cyq_data.iloc[-1]
        
        print(f"📊 {stock_code} 筹码集中度分析")
        print("=" * 50)
        
        # 基础指标
        profit_ratio = latest['获利比例']
        print(f"📈 获利比例: {profit_ratio*100:.2f}%")
        if profit_ratio > 0.7:
            print("   → 获利盘较重，上涨可能遇到抛售压力")
        elif profit_ratio < 0.3:
            print("   → 获利盘较轻，上涨阻力相对较小")
        else:
            print("   → 获利盘适中")
        
        print(f"💰 平均成本: {latest['平均成本']:.2f}元")
        
        # 90%筹码分布
        concentration_90 = latest['90集中度']
        print(f"\n🎯 90%筹码分布:")
        print(f"   成本区间: {latest['90成本-低']:.2f} - {latest['90成本-高']:.2f}元")
        print(f"   集中度: {concentration_90*100:.2f}%")
        
        if concentration_90 < 0.1:
            print("   → 筹码高度集中，可能形成重要支撑/阻力")
        elif concentration_90 > 0.2:
            print("   → 筹码较为分散，成本分布较广")
        else:
            print("   → 筹码集中度适中")
        
        # 70%筹码分布
        print(f"\n🎯 70%筹码分布:")
        print(f"   成本区间: {latest['70成本-低']:.2f} - {latest['70成本-高']:.2f}元")
        print(f"   集中度: {latest['70集中度']*100:.2f}%")
        
        # 交易策略建议
        print(f"\n💡 交易策略参考:")
        support_level = latest['90成本-低']
        resistance_level = latest['90成本-高']
        avg_cost = latest['平均成本']
        
        print(f"   🛡️ 重要支撑位: {support_level:.2f}元 (90%筹码下边界)")
        print(f"   ⚡ 重要阻力位: {resistance_level:.2f}元 (90%筹码上边界)")
        print(f"   ⚖️ 成本中枢: {avg_cost:.2f}元 (平均成本)")
        
        # 风险提示
        if profit_ratio > 0.8 and concentration_90 < 0.15:
            print("\n⚠️ 风险提示: 获利盘重且筹码集中，注意高位回调风险")
        elif profit_ratio < 0.2 and concentration_90 < 0.15:
            print("\n💎 机会提示: 套牢盘重且筹码集中，可能形成强支撑")
        
        return latest
        
    except Exception as e:
        print(f"获取筹码数据失败: {e}")
        return None

def get_chip_analysis_data(stock_code):
    """获取股票筹码分析数据"""
    try:
        cyq_data = ak.stock_cyq_em(stock_code)
        
        if cyq_data is None or cyq_data.empty:
            return {"error": f"无法获取 {stock_code} 的筹码数据"}
        
        latest = cyq_data.iloc[-1]
        profit_ratio = latest['获利比例']
        concentration_90 = latest['90集中度']
        
        # 获取历史数据（最近30天）
        historical_data = {
            "dates": cyq_data['日期'].tolist()[-30:],
            "profit_ratio": cyq_data['获利比例'].tolist()[-30:],
            "avg_cost": cyq_data['平均成本'].tolist()[-30:],
        }
        
        chip_data = {
            "latest_date": latest['日期'],
            "profit_ratio": profit_ratio,
            "avg_cost": latest['平均成本'],
            "cost_90_low": latest['90成本-低'],
            "cost_90_high": latest['90成本-高'],
            "concentration_90": concentration_90,
            "cost_70_low": latest['70成本-低'],
            "cost_70_high": latest['70成本-高'],
            "concentration_70": latest['70集中度'],
            "historical": historical_data,
            "support_level": latest['90成本-低'],
            "resistance_level": latest['90成本-高'],
            "cost_center": latest['平均成本'],
        }
        
        # 添加分析指标
        chip_data["analysis"] = {
            "profit_status": "高获利" if profit_ratio > 0.7 else ("低获利" if profit_ratio < 0.3 else "中性获利"),
            "concentration_status": "高度集中" if concentration_90 < 0.1 else ("分散" if concentration_90 > 0.2 else "适中"),
            "risk_level": "高" if profit_ratio > 0.8 and concentration_90 < 0.15 else ("低" if profit_ratio < 0.2 and concentration_90 < 0.15 else "中"),
        }
        
        return chip_data
        
    except Exception as e:
        print(f"获取筹码数据失败: {str(e)}")
        return {"error": f"该股票暂不支持获取筹码数据"}

def _judge_ma_trend(stock_data) -> str:
    """判断移动平均线趋势"""
    try:
        ma5 = stock_data['close_5_sma'].iloc[-1]
        ma10 = stock_data['close_10_sma'].iloc[-1]
        ma20 = stock_data['close_20_sma'].iloc[-1]
        current_price = stock_data['close'].iloc[-1]
        
        if current_price > ma5 > ma10 > ma20:
            return "多头排列"
        elif current_price < ma5 < ma10 < ma20:
            return "空头排列"
        else:
            return "震荡整理"
    except:
        return "无法判断"

def _judge_macd_trend(stock_data) -> str:
    """判断MACD趋势"""
    try:
        macd = stock_data['macd'].iloc[-1]
        macd_signal = stock_data['macds'].iloc[-1]
        macd_hist = stock_data['macdh'].iloc[-1]
        
        if macd > macd_signal and macd_hist > 0:
            return "金叉向上"
        elif macd < macd_signal and macd_hist < 0:
            return "死叉向下"
        else:
            return "震荡调整"
    except:
        return "无法判断"

def get_market_info(stock_code):
    """获取股票市场信息"""
    is_china = stock_code.isdigit() and len(stock_code) == 6
    is_hk = '.HK' in stock_code or stock_code.startswith('HK')
    is_us = not is_china and not is_hk
    
    return {
        'is_china': is_china,
        'is_hk': is_hk,
        'is_us': is_us,
        'market_name': '中国A股' if is_china else ('港股' if is_hk else '美股'),
        'currency_name': '人民币' if is_china else ('港币' if is_hk else '美元'),
        'currency_symbol': '¥' if is_china else ('HK$' if is_hk else '$')
    }

def get_indicators(df):
    """使用stockstats计算技术指标"""
    stock = wrap(df)
    stock_len = len(stock)
    
    indicators = {
        # 移动平均线
        'ma_5': stock['close_5_sma'].iloc[-1] if stock_len > 5 else None,
        'ma_10': stock['close_10_sma'].iloc[-1] if stock_len > 10 else None,
        'ma_20': stock['close_20_sma'].iloc[-1] if stock_len > 20 else None,
        'ma_60': stock['close_60_sma'].iloc[-1] if stock_len > 60 else None,
        
        # 指数移动平均
        'ema_12': stock['close_12_ema'].iloc[-1] if stock_len > 12 else None,
        'ema_26': stock['close_26_ema'].iloc[-1] if stock_len > 26 else None,
        
        # MACD指标
        'macd': stock['macd'].iloc[-1] if stock_len > 26 else None,
        'macd_signal': stock['macds'].iloc[-1] if stock_len > 26 else None,
        'macd_histogram': stock['macdh'].iloc[-1] if stock_len > 26 else None,
        
        # KDJ指标
        'kdj_k': stock['kdjk'].iloc[-1] if stock_len > 9 else None,
        'kdj_d': stock['kdjd'].iloc[-1] if stock_len > 9 else None,
        'kdj_j': stock['kdjj'].iloc[-1] if stock_len > 9 else None,
        
        # RSI指标
        'rsi_14': stock['rsi_14'].iloc[-1] if stock_len > 14 else None,
        
        # 布林带
        'boll_upper': stock['boll_ub'].iloc[-1] if stock_len > 20 else None,
        'boll_middle': stock['boll'].iloc[-1] if stock_len > 20 else None,
        'boll_lower': stock['boll_lb'].iloc[-1] if stock_len > 20 else None,
        
        # 威廉指标
        'wr_14': stock['wr_14'].iloc[-1] if stock_len > 14 else None,
        
        # CCI指标
        'cci_14': stock['cci_14'].iloc[-1] if stock_len > 14 else None,
        
        # 基础数据
        'latest_close': stock['close'].iloc[-1],
        'latest_high': stock['high'].iloc[-1],
        'latest_low': stock['low'].iloc[-1],
        'latest_open': stock['open'].iloc[-1],
        'latest_volume': stock['volume'].iloc[-1],
        'latest_date': df.iloc[-1].get('datetime', datetime.now().strftime('%Y-%m-%d')),
        
        # 趋势判断
        'ma_trend': _judge_ma_trend(stock),
        'macd_trend': _judge_macd_trend(stock),
    }
    
    # 价格变化计算
    if stock_len > 1:
        prev_close = stock['close'].iloc[-2]
        indicators.update({
            'prev_close': prev_close,
            'change_amount': stock['close'].iloc[-1] - prev_close,
            'change_percent': ((stock['close'].iloc[-1] - prev_close) / prev_close * 100) if prev_close != 0 else 0,
        })
    else:
        indicators.update({
            'prev_close': None,
            'change_amount': 0,
            'change_percent': 0,
        })
    
    return indicators

def fetch_stock_basic_info(stock_code: str) -> Dict:
    """获取股票基本信息的具体实现"""
    from providers.stock_data_fetcher import data_manager
    
    basic_info = {}
    
    try:
        if not data_manager.is_available() and not data_manager.initialize():
            raise Exception("数据提供者初始化失败")
                
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
            basic_info.update(stock_info)
        
    except Exception as e:
        basic_info['error'] = str(e)
    
    basic_info['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return basic_info

def fetch_stock_technical_indicators(stock_code: str, period: int = 160) -> Dict:
    """获取股票技术指标的具体实现（K线数据不缓存，只缓存计算结果）"""
    from providers.stock_data_fetcher import data_manager, KLineType
    from providers.risk_metrics import calculate_portfolio_risk_summary
    
    indicators_info = {}
    
    try:
        kline_data = data_manager.get_kline_data(stock_code, KLineType.DAY, period)
        
        if not kline_data:
            indicators_info['error'] = f"未获取到股票 {stock_code} 的K线数据"
        else:
            df = pd.DataFrame([k.__dict__ for k in kline_data]).sort_values('datetime')
            
            # 计算移动平均线
            for period in [5, 10, 20]:
                df[f'MA{period}'] = df['close'].rolling(window=period).mean()
            
            indicators = get_indicators(df)
            
            # 风险指标计算
            risk_metrics = {}
            if len(df) >= 5:
                try:
                    risk_metrics = calculate_portfolio_risk_summary(df, price_col='close')                            
                except Exception as e:
                    risk_metrics['error'] = str(e)

            # 获取最新数据摘要
            latest_row = df.iloc[-1]
            latest_data = {
                'date': latest_row['datetime'].isoformat() if hasattr(latest_row['datetime'], 'isoformat') else str(latest_row['datetime']),
                'open': float(latest_row['open']) if pd.notna(latest_row['open']) else None,
                'high': float(latest_row['high']) if pd.notna(latest_row['high']) else None,
                'low': float(latest_row['low']) if pd.notna(latest_row['low']) else None,
                'close': float(latest_row['close']) if pd.notna(latest_row['close']) else None,
                'volume': int(latest_row['volume']) if pd.notna(latest_row['volume']) else None,
            }
            
            indicators_info.update({
                'indicators': indicators,
                'risk_metrics': risk_metrics,
                'data_length': len(df),
                'latest_data': latest_data,
                'has_ma_data': True
            })
            
    except Exception as e:
        indicators_info['error'] = str(e)
    
    indicators_info['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return indicators_info

def fetch_stock_news_data(stock_code: str, day=7) -> Dict:
    """获取股票新闻数据的具体实现"""
    from providers.news_tools import get_stock_news_by_akshare
    
    news_info = {}
    
    try:
        stock_data = get_stock_news_by_akshare(stock_code, day=day)
        
        if stock_data and 'company_news' in stock_data:
            news_data = stock_data['company_news']
            news_info.update({
                'news_data': news_data,
                'news_count': len(news_data),
                'latest_news': news_data[:5] if len(news_data) >= 5 else news_data
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
        chip_data = get_chip_analysis_data(stock_code)
        chip_info.update(chip_data if "error" not in chip_data else {'error': chip_data["error"]})
    except Exception as e:
        chip_info['error'] = str(e)
    
    chip_info['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return chip_info

def _clear_cache_files_and_vars(file_path, code_map, name_map, update_time_var, var_names):
    """清除缓存文件和全局变量的通用函数"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"已删除缓存文件: {file_path}")
        else:
            print(f"缓存文件不存在: {file_path}")
        
        # 清空全局变量
        globals()[var_names[0]].clear()
        globals()[var_names[1]].clear()
        globals()[var_names[2]] = 0
        
    except Exception as e:
        print(f"清除缓存失败: {e}")

def clear_stock_map_cache():
    """清除A股股票代码与名称映射缓存文件"""
    _clear_cache_files_and_vars(
        _MAP_FILE_PATH, 
        _STOCK_CODE_NAME_MAP, 
        _STOCK_NAME_CODE_MAP, 
        _LAST_UPDATE_TIME,
        ['_STOCK_CODE_NAME_MAP', '_STOCK_NAME_CODE_MAP', '_LAST_UPDATE_TIME']
    )

def clear_hk_stock_map_cache():
    """清除港股通股票代码与名称映射缓存文件"""
    _clear_cache_files_and_vars(
        _HK_MAP_FILE_PATH,
        _HK_STOCK_CODE_NAME_MAP,
        _HK_STOCK_NAME_CODE_MAP,
        _HK_LAST_UPDATE_TIME,
        ['_HK_STOCK_CODE_NAME_MAP', '_HK_STOCK_NAME_CODE_MAP', '_HK_LAST_UPDATE_TIME']
    )