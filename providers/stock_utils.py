import akshare as ak
import os
import pandas as pd
import json
from pathlib import Path
import time
from datetime import datetime
from typing import Dict
from typing import Dict, Any

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

def _load_hk_stock_map(force_download=False):
    """加载港股通股票代码和名称的映射关系"""
    global _HK_STOCK_CODE_NAME_MAP, _HK_STOCK_NAME_CODE_MAP, _HK_LAST_UPDATE_TIME
    
    # 如果已加载且距离上次更新不超过24小时，则直接返回
    current_time = time.time()
    if _HK_STOCK_CODE_NAME_MAP and (current_time - _HK_LAST_UPDATE_TIME < 86400):  # 86400秒 = 24小时
        return
    
    # 尝试从本地文件加载
    try:
        if os.path.exists(_HK_MAP_FILE_PATH) and not force_download:
            with open(_HK_MAP_FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _HK_STOCK_CODE_NAME_MAP = data.get('code_to_name', {})
                _HK_STOCK_NAME_CODE_MAP = data.get('name_to_code', {})
                _HK_LAST_UPDATE_TIME = data.get('update_time', 0)
                
                # 如果距离上次更新不超过7天，则直接返回
                if current_time - _HK_LAST_UPDATE_TIME < 604800:  # 604800秒 = 7天
                    return
    except Exception as e:
        print(f"加载港股通映射文件失败: {e}")
    
    # 如果本地文件不存在或已过期，则重新获取
    try:
        # 获取港股通成分股信息
        print("正在更新港股通股票代码与名称映射表...")
        
        # 获取港股通成分股信息
        hk_stock_info = ak.stock_hk_ggt_components_em()
        
        # 处理港股通数据
        for _, row in hk_stock_info.iterrows():
            code = row['代码']
            name = row['名称']
            _HK_STOCK_CODE_NAME_MAP[code] = name
            _HK_STOCK_NAME_CODE_MAP[name] = code
        
        # 保存到本地文件
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
        'sample_stocks': dict(list(_HK_STOCK_CODE_NAME_MAP.items())[:10])  # 前10个样本
    }

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
    
    # 如果明确指定查找港股通
    elif security_type == 'hk':
        # 确保港股通映射表已加载
        _load_hk_stock_map()
        
        # 检查输入是否已经是港股通代码
        if stock_name_or_code in _HK_STOCK_CODE_NAME_MAP:
            return stock_name_or_code
        
        # 检查输入是否是港股通名称
        if stock_name_or_code in _HK_STOCK_NAME_CODE_MAP:
            return _HK_STOCK_NAME_CODE_MAP[stock_name_or_code]
        
        # 尝试模糊匹配港股通名称
        matched_names = [name for name in _HK_STOCK_NAME_CODE_MAP.keys() 
                        if stock_name_or_code in name]
        
        if matched_names:
            # 返回第一个匹配项
            return _HK_STOCK_NAME_CODE_MAP[matched_names[0]]
    
    # 默认查找所有(A股+港股通+指数)
    # 先尝试加载港股通映射表
    _load_hk_stock_map()
    
    # 检查输入是否已经是代码
    if stock_name_or_code in _STOCK_CODE_NAME_MAP:
        return stock_name_or_code
    if stock_name_or_code in _HK_STOCK_CODE_NAME_MAP:
        return stock_name_or_code
    
    # 检查输入是否是名称
    if stock_name_or_code in _STOCK_NAME_CODE_MAP:
        return _STOCK_NAME_CODE_MAP[stock_name_or_code]
    if stock_name_or_code in _HK_STOCK_NAME_CODE_MAP:
        return _HK_STOCK_NAME_CODE_MAP[stock_name_or_code]
    
    # 尝试模糊匹配A股
    matched_names = [name for name in _STOCK_NAME_CODE_MAP.keys() 
                    if stock_name_or_code in name]
    
    if matched_names:
        # 返回第一个匹配项
        return _STOCK_NAME_CODE_MAP[matched_names[0]]
    
    # 尝试模糊匹配港股通
    matched_hk_names = [name for name in _HK_STOCK_NAME_CODE_MAP.keys() 
                       if stock_name_or_code in name]
    
    if matched_hk_names:
        # 返回第一个匹配项
        return _HK_STOCK_NAME_CODE_MAP[matched_hk_names[0]]
    
    # 如果都没匹配到，返回原始输入
    return stock_name_or_code

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
    
    # 如果明确指定查找港股通
    elif security_type == 'hk':
        # 确保港股通映射表已加载
        _load_hk_stock_map()
        
        # 检查输入是否已经是港股通名称
        if stock_name_or_code in _HK_STOCK_NAME_CODE_MAP:
            return stock_name_or_code
        
        # 检查输入是否是港股通代码
        if stock_name_or_code in _HK_STOCK_CODE_NAME_MAP:
            return _HK_STOCK_CODE_NAME_MAP[stock_name_or_code]
        
        # 尝试模糊匹配港股通代码
        matched_codes = [code for code in _HK_STOCK_CODE_NAME_MAP.keys() 
                        if stock_name_or_code in code]
        
        if matched_codes:
            # 返回第一个匹配项
            return _HK_STOCK_CODE_NAME_MAP[matched_codes[0]]
    
    # 默认查找所有(A股+港股通+指数)
    # 先尝试加载港股通映射表
    _load_hk_stock_map()
    
    # 检查输入是否已经是名称
    if stock_name_or_code in _STOCK_NAME_CODE_MAP:
        return stock_name_or_code
    if stock_name_or_code in _HK_STOCK_NAME_CODE_MAP:
        return stock_name_or_code
    
    # 检查输入是否是代码
    if stock_name_or_code in _STOCK_CODE_NAME_MAP:
        return _STOCK_CODE_NAME_MAP[stock_name_or_code]
    if stock_name_or_code in _HK_STOCK_CODE_NAME_MAP:
        return _HK_STOCK_CODE_NAME_MAP[stock_name_or_code]
    
    # 如果都没匹配到，返回原始输入
    return stock_name_or_code

def normalize_stock_input(stock_input, security_type='stock'):
    """
    标准化证券输入
    
    Args:
        stock_input: 用户输入的证券代码或名称
        security_type: 证券类型，可选值为'stock'(股票)、'index'(指数)或'hk'(港股通)，默认为'stock'
        
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
        print(f"📈 获利比例: {latest['获利比例']*100:.2f}%")
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
        print(f"   集中度: {latest['90集中度']*100:.2f}%")
        
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
        print(f"   集中度: {latest['70集中度']*100:.2f}%")
        
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
            "profit_status": "高获利" if latest['获利比例'] > 0.7 else ("低获利" if latest['获利比例'] < 0.3 else "中性获利"),
            "concentration_status": "高度集中" if latest['90集中度'] < 0.1 else ("分散" if latest['90集中度'] > 0.2 else "适中"),
            "risk_level": "高" if latest['获利比例'] > 0.8 and latest['90集中度'] < 0.15 else ("低" if latest['获利比例'] < 0.2 and latest['90集中度'] < 0.15 else "中"),
        }
        
        return chip_data
        
    except Exception as e:
        print(f"获取筹码数据失败: {str(e)}")
        return {"error": f"该股票暂不支持获取筹码数据"}

from datetime import datetime
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
        'latest_high': stock['high'].iloc[-1],
        'latest_low': stock['low'].iloc[-1],
        'latest_open': stock['open'].iloc[-1],
        'latest_volume': stock['volume'].iloc[-1],
        'latest_date': df.iloc[-1].get('datetime', datetime.now().strftime('%Y-%m-%d')),
        
        # 价格变化（如果有前一日数据）
        'prev_close': stock['close'].iloc[-2] if len(stock) > 1 else None,
        'change_amount': stock['close'].iloc[-1] - stock['close'].iloc[-2] if len(stock) > 1 else 0,
        'change_percent': ((stock['close'].iloc[-1] - stock['close'].iloc[-2]) / stock['close'].iloc[-2] * 100) if len(stock) > 1 and stock['close'].iloc[-2] != 0 else 0,
        
        # 趋势判断
        'ma_trend': _judge_ma_trend(stock),
        'macd_trend': _judge_macd_trend(stock),
    }
    return indicators


# =========================
# 独立的数据获取函数（纯外部API调用）
# =========================

def fetch_stock_basic_info(stock_code: str) -> Dict:
    """获取股票基本信息的具体实现"""
    # 导入必要的模块
    from providers.stock_data_fetcher import data_manager
    
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
            basic_info.update(stock_info)
        
    except Exception as e:
        basic_info['error'] = str(e)
    
    basic_info['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return basic_info


def fetch_stock_technical_indicators(stock_code: str, period: int = 160) -> Dict:
    """获取股票技术指标的具体实现（K线数据不缓存，只缓存计算结果）
    
    Args:
        stock_code: 股票代码
        period: K线周期数
        include_full_risk: 是否包含完整风险指标（用于图表显示）
    """
    # 导入必要的模块
    from providers.stock_data_fetcher import data_manager, KLineType
    from providers.risk_metrics import calculate_portfolio_risk_summary, calculate_portfolio_risk
    
    indicators_info = {}
    
    try:
        # 固定使用日K数据（利用现有的CSV缓存机制）
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
                    risk_metrics = calculate_portfolio_risk_summary(df, price_col='close')                            
                except Exception as e:
                    risk_metrics['error'] = str(e)
                    #full_risk_metrics['error'] = str(e)

            # 获取最新数据摘要（不包含完整K线数据）
            latest_data = {}
            if len(df) > 0:
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
                'risk_metrics': risk_metrics,  # 精简风险摘要（用于缓存）
                'data_length': len(df),
                'latest_data': latest_data,
                'has_ma_data': True  # 标记移动平均线已计算
            })
                
        else:
            indicators_info['error'] = f"未获取到股票 {stock_code} 的K线数据"
            
    except Exception as e:
        indicators_info['error'] = str(e)
    
    indicators_info['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return indicators_info


def fetch_stock_news_data(stock_code: str, day=7) -> Dict:
    """获取股票新闻数据的具体实现"""
    # 导入必要的模块
    from providers.news_tools import get_stock_news_by_akshare
    
    news_info = {}
    
    try:
        # 使用news_tools模块获取新闻
        stock_data = get_stock_news_by_akshare(stock_code, day=day)
        
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