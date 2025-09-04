"""股票数据格式化模块"""

import os
import sys
from typing import Dict, Any, List

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from utils.format_utils import format_large_number, format_market_value, format_price, format_percentage
from utils.string_utils import format_indicators_dict


class StockDataFormatter:
    """股票数据格式化器"""
    
    def __init__(self):
        pass
    
    def format_basic_info(self, basic_info: Dict[str, Any], stock_identity: Dict[str, Any]) -> str:
        """格式化基本信息为Markdown格式的文本"""
        if not basic_info or 'error' in basic_info:
            return "## 获取基本信息时出错: 暂无基本信息数据\n"
        
        md_content = ""
        stock_code = stock_identity['code']
        stock_name = stock_identity.get('name', '')
        market_name = stock_identity.get('market_name', '未知')
        currency_symbol = stock_identity.get('currency_symbol', '¥')
                
        # 股票信息
        md_content += f"- 股票名称: {stock_name}\n"
        md_content += f"- 股票代码: {stock_code}\n"
        md_content += f"- 所属市场: {market_name}\n"
        
        # 价格信息
        if 'current_price' in basic_info:
            md_content += f"- 当前价格: {format_price(basic_info['current_price'])}{currency_symbol}\n"
        if 'change_amount' in basic_info:
            md_content += f"- 涨跌额: {format_price(basic_info['change_amount'])}{currency_symbol}\n"
        if 'change_percent' in basic_info:
            md_content += f"- 涨跌幅: {format_percentage(basic_info['change_percent'])}\n"
        
        # 市值信息
        if 'total_market_value' in basic_info and basic_info['total_market_value']:
            md_content += f"- 总市值: {format_market_value(basic_info['total_market_value'])}{currency_symbol}\n"
        if 'circulating_market_value' in basic_info and basic_info['circulating_market_value']:
            md_content += f"- 流通市值: {format_market_value(basic_info['circulating_market_value'])}{currency_symbol}\n"
        
        # 财务比率
        ratio_labels = {
            'pe_ratio': '市盈率',
            'pb_ratio': '市净率',
            'roe': 'ROE',
            'gross_profit_margin': '毛利率',
            'net_profit_margin': '净利率',
            'debt_to_asset_ratio': '资产负债率'
        }
        
        for ratio_key, ratio_label in ratio_labels.items():
            if ratio_key in basic_info and basic_info[ratio_key] is not None and str(basic_info[ratio_key]).strip():
                md_content += f"- {ratio_label}: {basic_info[ratio_key]}\n"
        
        # 公司信息
        if 'industry' in basic_info and basic_info['industry']:
            md_content += f"- 所属行业: {basic_info['industry']}\n"
        if 'net_profit' in basic_info and basic_info['net_profit']:
            md_content += f"- 净利润: {format_large_number(basic_info['net_profit'])}\n"
        
        return md_content


    def format_kline_data(self, kline_info: Dict[str, Any]) -> str:
        """为AI分析格式化K线数据为文本"""
        """
        if not kline_data or 'error' in kline_data:
            return "暂无K线数据"
        """
        text_parts = []
        indicators = kline_info.get('indicators')
        risk_metrics = kline_info.get('risk_metrics')
        if indicators:
            indicators_text = format_indicators_dict(indicators, "技术指标")
            text_parts.append(indicators_text)
        
        if risk_metrics:
            risk_text = format_indicators_dict(risk_metrics, "风险指标")
            text_parts.append(risk_text)

        if 'data_length' in kline_info:
            text_parts.append(f"- 数据周期: {kline_info['data_length']}天")
        if 'update_time' in kline_info:
            text_parts.append(f"- 更新时间: {kline_info['update_time']}")
            
        return "\n\n".join(text_parts)
        
    def format_news_data(self, news_data: List[Dict[str, Any]], has_content: bool, max_item: int = -1) -> str:
        """为AI分析格式化新闻数据为文本"""
        if not news_data or len(news_data) == 0:
            return "暂无相关新闻数据"

        text_parts = [f"共获取到 {len(news_data)} 条相关新闻:\n"]

        for i, news in enumerate(news_data):
            title = news.get('新闻标题', '无标题')
            if has_content:
                text_parts.append(f"{i+1}. 新闻标题: {title}")
                if '发布时间' in news:
                    text_parts.append(f"   发布时间: {news['发布时间']}")
                if has_content and '新闻内容' in news and news['新闻内容']:
                    content = news['新闻内容'][:200] + "..." if len(news['新闻内容']) > 200 else news['新闻内容']
                    text_parts.append(f"   新闻内容: {content}")
            else:
                text_parts.append(f"- [{title}]({news['新闻链接']}) - {news.get('发布时间', '')}")
            text_parts.append("")
            if max_item > 0 and i + 1 >= max_item:
                break

        return "\n".join(text_parts)
        
    def format_chip_data(self, chip_data: Dict[str, Any]) -> str:
        """格式化筹码数据为Markdown格式的文本"""
        if not chip_data or 'error' in chip_data:
            return "获取筹码数据时出错: 暂无筹码数据\n"
        
        md_content = ""
        md_content += "\n筹码概况:\n"
        if 'latest_date' in chip_data:
            md_content += f"- 最新日期: {chip_data['latest_date']}\n"
        if 'profit_ratio' in chip_data:
            md_content += f"- 获利比例: {format_percentage(chip_data['profit_ratio'] * 100)}\n"
        if 'avg_cost' in chip_data:
            md_content += f"- 平均成本: {format_price(chip_data['avg_cost'])}\n"
        
        # 筹码分布
        if 'cost_90_low' in chip_data and 'cost_90_high' in chip_data:
            md_content += f"- 90%筹码区间: {format_price(chip_data['cost_90_low'])} - {format_price(chip_data['cost_90_high'])}元\n"
        if 'concentration_90' in chip_data:
            md_content += f"- 90%集中度: {format_percentage(chip_data['concentration_90']*100)}\n"
        
        if 'cost_70_low' in chip_data and 'cost_70_high' in chip_data:
            md_content += f"- 70%筹码区间: {format_price(chip_data['cost_70_low'])} - {format_price(chip_data['cost_70_high'])}元\n"
        if 'concentration_70' in chip_data:
            md_content += f"- 70%集中度: {format_percentage(chip_data['concentration_70']*100)}\n"
        
        # 分析指标
        if 'analysis' in chip_data:
            analysis = chip_data['analysis']
            md_content += "\n分析指标:\n"
            if 'profit_status' in analysis:
                md_content += f"- 获利状态: {analysis['profit_status']}\n"
            if 'concentration_status' in analysis:
                md_content += f"- 集中度状态: {analysis['concentration_status']}\n"
            if 'risk_level' in analysis:
                md_content += f"- 风险水平: {analysis['risk_level']}\n"
        
        # 技术参考位
        reference_added = False
        if 'support_level' in chip_data:
            if not reference_added:
                md_content += "\n技术参考位:\n"
                reference_added = True
            md_content += f"- 支撑位: {format_price(chip_data['support_level'])}\n"
        if 'resistance_level' in chip_data:
            if not reference_added:
                md_content += "\n技术参考位:\n"
                reference_added = True
            md_content += f"- **阻力位**: {format_price(chip_data['resistance_level'])}\n"
        if 'cost_center' in chip_data:
            if not reference_added:
                md_content += "\n技术参考位:\n"
                reference_added = True
            md_content += f"- 成本中枢: {format_price(chip_data['cost_center'])}\n"

        return md_content
    
    def format_stock_overview(self, stock_identity: Dict[str, Any], basic_info: Dict[str, Any] = None) -> str:
        """为AI分析格式化股票概览信息"""
        parts = []       
        currency_symbol = stock_identity.get('currency_symbol', '元')
        
        parts.append(f"## 股票概览:")
        parts.append(f"- 股票代码: {stock_identity['code']}")
        parts.append(f"- 股票名称: {stock_identity.get('name', '')}")
        parts.append(f"- 所属市场: {stock_identity.get('market_name', '未知市场')}")
        parts.append(f"- 计价货币: {stock_identity.get('currency_name', '人民币')}({currency_symbol})")
        
        if basic_info and 'error' not in basic_info:
            if 'current_price' in basic_info:
                parts.append(f"- 当前价格: {format_price(basic_info['current_price'])}{currency_symbol}")
            if 'change_percent' in basic_info:
                parts.append(f"- 涨跌幅: {format_percentage(basic_info['change_percent'])}")
        
        return "\n".join(parts)


_formatter = None

def get_stock_formatter() -> StockDataFormatter:
    """获取全局股票数据格式化器实例"""
    global _formatter
    if _formatter is None:
        _formatter = StockDataFormatter()
    return _formatter

