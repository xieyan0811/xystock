"""
UI配置文件
"""

# Streamlit 应用配置
STREAMLIT_CONFIG = {
    "port": 8811,
    "host": "0.0.0.0",
    "headless": True,
    "title": "XY Stock 股票分析系统"
}

# 市场类型配置
MARKET_TYPES = [
    "A股",
    "港股", 
    "指数",
    "基金"
]

# 股票代码示例
STOCK_CODE_EXAMPLES = {
    "A股": ["000001", "000002", "600000", "600036"],
    "港股": ["00700", "00941", "02318"],
    "指数": ["000001", "399001", "399006"],
    "基金": ["159915", "510300", "512100"]
}

# UI主题配置
UI_THEME = {
    "primary_color": "#1f77b4",
    "background_color": "#ffffff",
    "secondary_background_color": "#f0f2f6",
    "text_color": "#262730"
}
