import akshare as ak
import os
import json
from pathlib import Path
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ui.config import INDEX_CODE_MAPPING

# 全局变量，用于缓存股票代码和名称的映射关系
_STOCK_CODE_NAME_MAP = {}
_STOCK_NAME_CODE_MAP = {}
_HK_STOCK_CODE_NAME_MAP = {}
_HK_STOCK_NAME_CODE_MAP = {}

_INDEX_CODE_NAME_MAP = {code: name for name, code in INDEX_CODE_MAPPING.items()}
_INDEX_NAME_CODE_MAP = INDEX_CODE_MAPPING.copy()

_LAST_UPDATE_TIME = 0
_HK_LAST_UPDATE_TIME = 0
_MAP_FILE_PATH = os.path.join(Path(__file__).parent.parent, 'data', 'cache', 'stock_code_name_map.json')
_HK_MAP_FILE_PATH = os.path.join(Path(__file__).parent.parent, 'data', 'cache', 'hk_stock_code_name_map.json')


def get_stock_identity(stock_code, market_type='A股'):
    """
    获取股票身份信息，包括代码、名称、市场类型、币种等
    """
    stock_name = get_stock_name(stock_code, market_type)
    stock_code = get_stock_code(stock_code, market_type)
    # 判断如果stock_code格式不是6位以下的数字，则返回空
    if not stock_code or not stock_code.isdigit() or len(stock_code) > 6:
        return None

    market_name = market_type
    currency_name = '人民币' if market_type in ['A股', 'ETF'] else '港币'
    currency_symbol = '元' if market_type in ['A股', 'ETF'] else 'HK$'
    return {
        'code': stock_code,
        'name': stock_name,
        'market_name': market_name,
        'currency_name': currency_name,
        'currency_symbol': currency_symbol
    }

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

def _find_fuzzy_match(target, mapping_dict):
    """模糊匹配辅助函数"""
    matched_items = [key for key in mapping_dict.keys() if target in key]
    return mapping_dict[matched_items[0]] if matched_items else None

def get_stock_code(stock_name_or_code, market_type='A股'):
    """
    获取证券代码
    
    Args:
        stock_name_or_code: 证券名称或代码
        market_type: 证券类型，可选值为'A股'、'ETF'、'港股'，默认为'A股'

    Returns:
        证券代码，如果输入已经是代码则直接返回，如果是名称则转换为代码
    """
    if not stock_name_or_code:
        return None
    
    _load_stock_map()
    _load_hk_stock_map()
    
    if stock_name_or_code in _STOCK_CODE_NAME_MAP or stock_name_or_code in _HK_STOCK_CODE_NAME_MAP:
        return stock_name_or_code
    
    return (_STOCK_NAME_CODE_MAP.get(stock_name_or_code) 
            or _HK_STOCK_NAME_CODE_MAP.get(stock_name_or_code)
            or _find_fuzzy_match(stock_name_or_code, _STOCK_NAME_CODE_MAP)
            or _find_fuzzy_match(stock_name_or_code, _HK_STOCK_NAME_CODE_MAP)
            or stock_name_or_code)

def get_stock_name(stock_name_or_code, market_type='A股'):
    """
    获取证券名称
    
    Args:
        stock_name_or_code: 证券名称或代码
        market_type: 证券类型，可选值为'A股'、'ETF'、'港股'，默认为'A股'
        
    Returns:
        证券名称，如果输入已经是名称则直接返回，如果是代码则转换为名称
    """
    if not stock_name_or_code:
        return None
    
    _load_stock_map()
    _load_hk_stock_map()
    
    if stock_name_or_code in _STOCK_NAME_CODE_MAP or stock_name_or_code in _HK_STOCK_NAME_CODE_MAP:
        return stock_name_or_code
    
    return (_STOCK_CODE_NAME_MAP.get(stock_name_or_code)
            or _HK_STOCK_CODE_NAME_MAP.get(stock_name_or_code)
            or stock_name_or_code)

def _clear_cache_files_and_vars(file_path, var_names):
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
        ['_STOCK_CODE_NAME_MAP', '_STOCK_NAME_CODE_MAP', '_LAST_UPDATE_TIME']
    )

def clear_hk_stock_map_cache():
    """清除港股通股票代码与名称映射缓存文件"""
    _clear_cache_files_and_vars(
        _HK_MAP_FILE_PATH,
        ['_HK_STOCK_CODE_NAME_MAP', '_HK_STOCK_NAME_CODE_MAP', '_HK_LAST_UPDATE_TIME']
    )

