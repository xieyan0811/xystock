"""
数字格式化工具模块
提供统一的数字显示格式化功能
"""

def format_large_number(number, decimal_places=2):
    """
    格式化大数字，自动添加单位（万、亿等）
    
    Args:
        number: 要格式化的数字
        decimal_places: 保留的小数位数，默认为2位
        
    Returns:
        str: 格式化后的字符串
        
    Examples:
        >>> format_large_number(12345678)
        '1234.57万'
        >>> format_large_number(123456789012)
        '1234.57亿'
        >>> format_large_number(1234)
        '1234.00'
    """
    if number is None or number == 0:
        return "0.00"
    
    # 确保输入是数字类型
    try:
        number = float(number)
    except (ValueError, TypeError):
        return str(number)
    
    # 处理负数
    is_negative = number < 0
    number = abs(number)
    
    # 根据数字大小选择单位
    if number >= 100000000:  # 大于等于1亿
        result = f"{number / 100000000:.{decimal_places}f}亿"
    elif number >= 10000:  # 大于等于1万
        result = f"{number / 10000:.{decimal_places}f}万"
    else:
        result = f"{number:.{decimal_places}f}"
    
    # 添加负号
    if is_negative:
        result = "-" + result
        
    return result


def format_volume(volume, decimal_places=2):
    """
    格式化成交量数字
    
    Args:
        volume: 成交量数字
        decimal_places: 保留的小数位数，默认为2位
        
    Returns:
        str: 格式化后的字符串
    """
    return format_large_number(volume, decimal_places)


def format_market_value(value, decimal_places=2):
    """
    格式化市值数字
    
    Args:
        value: 市值数字
        decimal_places: 保留的小数位数，默认为2位
        
    Returns:
        str: 格式化后的字符串
    """
    return format_large_number(value, decimal_places)


def format_price(price, decimal_places=2):
    """
    格式化价格数字
    
    Args:
        price: 价格数字
        decimal_places: 保留的小数位数，默认为2位
        
    Returns:
        str: 格式化后的字符串
    """
    if price is None:
        return "0.00"
    
    try:
        price = float(price)
        return f"{price:.{decimal_places}f}"
    except (ValueError, TypeError):
        return str(price)


def format_percentage(value, decimal_places=2):
    """
    格式化百分比数字
    
    Args:
        value: 百分比数值（如 0.05 表示 5%）
        decimal_places: 保留的小数位数，默认为2位
        
    Returns:
        str: 格式化后的字符串，包含%符号
    """
    if value is None:
        return "0.00%"
    
    try:
        value = float(value)
        return f"{value:.{decimal_places}f}%"
    except (ValueError, TypeError):
        return str(value)


def format_change(change, change_percent, decimal_places=2):
    """
    格式化价格变化和变化百分比
    
    Args:
        change: 价格变化数值
        change_percent: 变化百分比
        decimal_places: 保留的小数位数，默认为2位
        
    Returns:
        str: 格式化后的字符串，如 "1.23 (2.45%)" 或 "-1.23 (-2.45%)"
    """
    if change is None or change_percent is None:
        return "0.00 (0.00%)"
    
    try:
        change = float(change)
        change_percent = float(change_percent)
        
        return f"{change:.{decimal_places}f} ({change_percent:.{decimal_places}f}%)"
    except (ValueError, TypeError):
        return f"{change} ({change_percent}%)"

def format_number(number, decimal_places=2):
    """
    四舍五入格式化数字到指定小数位数
    """
    if number is None:
        return f"0.{''.join(['0' for _ in range(decimal_places)])}"
    
    try:
        number = float(number)
        return f"{number:.{decimal_places}f}"
    except (ValueError, TypeError):
        return str(number)


def judge_rsi_level(rsi: float) -> str:
    """
    判断RSI水平
    
    Args:
        rsi: RSI值
        
    Returns:
        str: RSI水平描述
    """
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
    
def get_section_separator(markdown: bool = False) -> list:
    """获取章节分隔符
    
    Args:
        markdown: 是否为markdown格式
        
    Returns:
        list: 分隔符行列表
    """
    if markdown:
        return ["\n---\n"]
    else:
        return ["\n" + "=" * 40 + "\n"]
