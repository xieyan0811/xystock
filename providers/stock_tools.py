import akshare as ak
import os
import pandas as pd
import json
from pathlib import Path
import time

# 全局变量，用于缓存股票代码和名称的映射关系
_STOCK_CODE_NAME_MAP = {}
_STOCK_NAME_CODE_MAP = {}
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
_MAP_FILE_PATH = os.path.join(Path(__file__).parent.parent, 'data', 'cache', 'stock_code_name_map.json')

def _ensure_dir_exists(file_path):
    """确保文件目录存在"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

def _load_stock_map(force_download = False):
    """加载股票代码和名称的映射关系"""
    global _STOCK_CODE_NAME_MAP, _STOCK_NAME_CODE_MAP, _LAST_UPDATE_TIME
    
    # 如果已加载且距离上次更新不超过24小时，则直接返回
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
                
                # 如果距离上次更新不超过7天，则直接返回
                if current_time - _LAST_UPDATE_TIME < 604800:  # 604800秒 = 7天
                    return
    except Exception as e:
        print(f"加载股票映射文件失败: {e}")
    
    # 如果本地文件不存在或已过期，则重新获取
    try:
        # 获取A股上市公司基本信息
        print("正在更新股票代码与名称映射表...")
        
        # 获取A股上市公司信息
        stock_info_a = ak.stock_info_a_code_name()
        # 获取港股上市公司信息
        #stock_info_hk = ak.stock_hk_info_hk_name()
        
        # 处理A股数据
        for _, row in stock_info_a.iterrows():
            code = row['code']
            name = row['name']
            _STOCK_CODE_NAME_MAP[code] = name
            _STOCK_NAME_CODE_MAP[name] = code
        
        # 合并指数映射数据到股票映射中
        for code, name in _INDEX_CODE_NAME_MAP.items():
            _STOCK_CODE_NAME_MAP[code] = name
        for name, code in _INDEX_NAME_CODE_MAP.items():
            _STOCK_NAME_CODE_MAP[name] = code
        
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

def get_stock_code(stock_name_or_code, security_type='stock'):
    """
    获取证券代码
    
    Args:
        stock_name_or_code: 证券名称或代码
        security_type: 证券类型，可选值为'stock'(股票)或'index'(指数)，默认为'stock'
        
    Returns:
        证券代码，如果输入已经是代码则直接返回，如果是名称则转换为代码
    """
    if not stock_name_or_code:
        return None
    
    # 确保映射表已加载
    _load_stock_map()
    
    # 如果明确指定查找指数
    if security_type == 'index':
        # 检查输入是否已经是指数代码
        if stock_name_or_code in _INDEX_CODE_NAME_MAP:
            return stock_name_or_code
        
        # 检查输入是否是指数名称
        if stock_name_or_code in _INDEX_NAME_CODE_MAP:
            return _INDEX_NAME_CODE_MAP[stock_name_or_code]
        
        # 尝试模糊匹配指数名称
        matched_names = [name for name in _INDEX_NAME_CODE_MAP.keys() 
                        if stock_name_or_code in name]
        
        if matched_names:
            # 返回第一个匹配项
            return _INDEX_NAME_CODE_MAP[matched_names[0]]
    
    # 默认查找所有(股票+指数)
    # 检查输入是否已经是代码
    if stock_name_or_code in _STOCK_CODE_NAME_MAP:
        return stock_name_or_code
    
    # 检查输入是否是名称
    if stock_name_or_code in _STOCK_NAME_CODE_MAP:
        return _STOCK_NAME_CODE_MAP[stock_name_or_code]
    
    # 尝试模糊匹配
    matched_names = [name for name in _STOCK_NAME_CODE_MAP.keys() 
                    if stock_name_or_code in name]
    
    if matched_names:
        # 返回第一个匹配项
        return _STOCK_NAME_CODE_MAP[matched_names[0]]
    
    # 如果都没匹配到，返回原始输入
    return stock_name_or_code

def get_stock_name(stock_name_or_code, security_type='stock'):
    """
    获取证券名称
    
    Args:
        stock_name_or_code: 证券名称或代码
        security_type: 证券类型，可选值为'stock'(股票)或'index'(指数)，默认为'stock'
        
    Returns:
        证券名称，如果输入已经是名称则直接返回，如果是代码则转换为名称
    """
    if not stock_name_or_code:
        return None
    
    # 确保映射表已加载
    _load_stock_map()
    
    # 如果明确指定查找指数
    if security_type == 'index':
        # 检查输入是否已经是指数名称
        if stock_name_or_code in _INDEX_NAME_CODE_MAP:
            return stock_name_or_code
        
        # 检查输入是否是指数代码
        if stock_name_or_code in _INDEX_CODE_NAME_MAP:
            return _INDEX_CODE_NAME_MAP[stock_name_or_code]
        
        # 尝试模糊匹配指数代码
        matched_codes = [code for code in _INDEX_CODE_NAME_MAP.keys() 
                        if stock_name_or_code in code]
        
        if matched_codes:
            # 返回第一个匹配项
            return _INDEX_CODE_NAME_MAP[matched_codes[0]]
    
    # 默认查找所有(股票+指数)
    # 检查输入是否已经是名称
    if stock_name_or_code in _STOCK_NAME_CODE_MAP:
        return stock_name_or_code
    
    # 检查输入是否是代码
    if stock_name_or_code in _STOCK_CODE_NAME_MAP:
        return _STOCK_CODE_NAME_MAP[stock_name_or_code]
    
    # 如果都没匹配到，返回原始输入
    return stock_name_or_code

def normalize_stock_input(stock_input, security_type='stock'):
    """
    标准化证券输入
    
    Args:
        stock_input: 用户输入的证券代码或名称
        security_type: 证券类型，可选值为'stock'(股票)或'index'(指数)，默认为'stock'
        
    Returns:
        元组 (stock_code, stock_name)
    """
    code = get_stock_code(stock_input, security_type)
    name = get_stock_name(code, security_type)  # 确保使用代码获取准确的名称
    
    return code, name

def explain_cyq_data(stock_code):
    """解释筹码集中度数据"""
    "demo: explain_cyq_data('000977')"
    try:
        # 获取筹码数据
        cyq_data = ak.stock_cyq_em(stock_code)
        
        if cyq_data is None or cyq_data.empty:
            print(f"无法获取 {stock_code} 的筹码数据")
            return
        
        # 获取最新数据
        latest = cyq_data.iloc[-1]
        
        print(f"📊 {stock_code} 筹码集中度分析")
        print("=" * 50)
        
        # 基础指标
        print(f"📈 获利比例: {latest['获利比例']:.2f}%")
        if latest['获利比例'] > 0.7:
            print("   → 获利盘较重，上涨可能遇到抛售压力")
        elif latest['获利比例'] < 0.3:
            print("   → 获利盘较轻，上涨阻力相对较小")
        else:
            print("   → 获利盘适中")
        
        print(f"💰 平均成本: {latest['平均成本']:.2f}元")
        
        # 90%筹码分布
        print(f"\n🎯 90%筹码分布:")
        print(f"   成本区间: {latest['90成本-低']:.2f} - {latest['90成本-高']:.2f}元")
        print(f"   集中度: {latest['90集中度']:.2f}%")
        
        range_90 = latest['90成本-高'] - latest['90成本-低']
        if latest['90集中度'] < 0.1:
            print("   → 筹码高度集中，可能形成重要支撑/阻力")
        elif latest['90集中度'] > 0.2:
            print("   → 筹码较为分散，成本分布较广")
        else:
            print("   → 筹码集中度适中")
        
        # 70%筹码分布
        print(f"\n🎯 70%筹码分布:")
        print(f"   成本区间: {latest['70成本-低']:.2f} - {latest['70成本-高']:.2f}元")
        print(f"   集中度: {latest['70集中度']:.2f}%")
        
        # 交易策略建议
        print(f"\n💡 交易策略参考:")
        
        # 支撑阻力分析
        support_level = latest['90成本-低']
        resistance_level = latest['90成本-高']
        avg_cost = latest['平均成本']
        
        print(f"   🛡️ 重要支撑位: {support_level:.2f}元 (90%筹码下边界)")
        print(f"   ⚡ 重要阻力位: {resistance_level:.2f}元 (90%筹码上边界)")
        print(f"   ⚖️ 成本中枢: {avg_cost:.2f}元 (平均成本)")
        
        # 风险提示
        if latest['获利比例'] > 0.8 and latest['90集中度'] < 0.15:
            print("\n⚠️ 风险提示: 获利盘重且筹码集中，注意高位回调风险")
        elif latest['获利比例'] < 0.2 and latest['90集中度'] < 0.15:
            print("\n💎 机会提示: 套牢盘重且筹码集中，可能形成强支撑")
        
        return latest
        
    except Exception as e:
        print(f"获取筹码数据失败: {e}")
        return None

def get_chip_analysis_data(stock_code):
    """
    获取股票筹码分析数据
    
    Args:
        stock_code: 股票代码
        
    Returns:
        dict: 包含筹码分布和关键指标的字典
    """
    try:
        # 获取筹码数据
        cyq_data = ak.stock_cyq_em(stock_code)
        
        if cyq_data is None or cyq_data.empty:
            return {"error": f"无法获取 {stock_code} 的筹码数据"}
        
        # 获取最新数据
        latest = cyq_data.iloc[-1]
        
        # 获取历史数据
        historical_data = {
            "dates": cyq_data['日期'].tolist()[-30:],  # 最近30天
            "profit_ratio": cyq_data['获利比例'].tolist()[-30:],  # 获利比例
            "avg_cost": cyq_data['平均成本'].tolist()[-30:],  # 平均成本
        }
        
        # 构建筹码数据字典
        chip_data = {
            "latest_date": latest['日期'],
            "profit_ratio": latest['获利比例'],
            "avg_cost": latest['平均成本'],
            "cost_90_low": latest['90成本-低'],
            "cost_90_high": latest['90成本-高'],
            "concentration_90": latest['90集中度'],
            "cost_70_low": latest['70成本-低'],
            "cost_70_high": latest['70成本-高'],
            "concentration_70": latest['70集中度'],
            "historical": historical_data,
            
            # 分析结果
            "support_level": latest['90成本-低'],  # 支撑位
            "resistance_level": latest['90成本-高'],  # 阻力位
            "cost_center": latest['平均成本'],  # 成本中枢
        }
        
        # 添加简单的分析指标
        chip_data["analysis"] = {
            "profit_status": "高获利" if latest['获利比例'] > 70 else ("低获利" if latest['获利比例'] < 30 else "中性获利"),
            "concentration_status": "高度集中" if latest['90集中度'] < 0.1 else ("分散" if latest['90集中度'] > 0.2 else "适中"),
            "risk_level": "高" if latest['获利比例'] > 80 and latest['90集中度'] < 0.15 else ("低" if latest['获利比例'] < 20 and latest['90集中度'] < 0.15 else "中"),
        }
        
        return chip_data
        
    except Exception as e:
        return {"error": f"获取筹码数据失败: {str(e)}"}

from datetime import datetime, timedelta
from stockstats import wrap

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
    """
    获取股票市场信息
    
    Args:
        stock_code: 股票代码
    
    Returns:
        dict: 包含市场类型、货币等信息的字典
    """
    # 简单判断市场类型
    is_china = stock_code.isdigit() and len(stock_code) == 6
    is_hk = '.HK' in stock_code or stock_code.startswith('HK')
    is_us = not is_china and not is_hk
    
    market_info = {
        'is_china': is_china,
        'is_hk': is_hk,
        'is_us': is_us,
        'market_name': '中国A股' if is_china else ('港股' if is_hk else '美股'),
        'currency_name': '人民币' if is_china else ('港币' if is_hk else '美元'),
        'currency_symbol': '¥' if is_china else ('HK$' if is_hk else '$')
    }
    
    return market_info

def get_indicators(df):
    # 使用stockstats计算技术指标
    stock = wrap(df)
    
    # 计算主要技术指标
    indicators = {
        # 移动平均线
        'ma_5': stock['close_5_sma'].iloc[-1] if len(stock) > 5 else None,
        'ma_10': stock['close_10_sma'].iloc[-1] if len(stock) > 10 else None,
        'ma_20': stock['close_20_sma'].iloc[-1] if len(stock) > 20 else None,
        'ma_60': stock['close_60_sma'].iloc[-1] if len(stock) > 60 else None,
        
        # 指数移动平均
        'ema_12': stock['close_12_ema'].iloc[-1] if len(stock) > 12 else None,
        'ema_26': stock['close_26_ema'].iloc[-1] if len(stock) > 26 else None,
        
        # MACD指标
        'macd': stock['macd'].iloc[-1] if len(stock) > 26 else None,
        'macd_signal': stock['macds'].iloc[-1] if len(stock) > 26 else None,
        'macd_histogram': stock['macdh'].iloc[-1] if len(stock) > 26 else None,
        
        # KDJ指标
        'kdj_k': stock['kdjk'].iloc[-1] if len(stock) > 9 else None,
        'kdj_d': stock['kdjd'].iloc[-1] if len(stock) > 9 else None,
        'kdj_j': stock['kdjj'].iloc[-1] if len(stock) > 9 else None,
        
        # RSI指标
        'rsi_14': stock['rsi_14'].iloc[-1] if len(stock) > 14 else None,
        
        # 布林带
        'boll_upper': stock['boll_ub'].iloc[-1] if len(stock) > 20 else None,
        'boll_middle': stock['boll'].iloc[-1] if len(stock) > 20 else None,
        'boll_lower': stock['boll_lb'].iloc[-1] if len(stock) > 20 else None,
        
        # 威廉指标
        'wr_14': stock['wr_14'].iloc[-1] if len(stock) > 14 else None,
        
        # CCI指标
        'cci_14': stock['cci_14'].iloc[-1] if len(stock) > 14 else None,
        
        # 基础数据
        'latest_close': stock['close'].iloc[-1],
        'latest_volume': stock['volume'].iloc[-1],
        'latest_date': df.iloc[-1].get('datetime', datetime.now().strftime('%Y-%m-%d')),
        
        # 趋势判断
        'ma_trend': _judge_ma_trend(stock),
        'macd_trend': _judge_macd_trend(stock),
    }
    return indicators