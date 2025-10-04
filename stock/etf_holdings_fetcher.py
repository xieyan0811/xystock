"""
ETF持仓数据获取器
"""
import akshare as ak
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime


class ETFHoldingsFetcher:
    """ETF持仓数据获取器"""
    
    def __init__(self):
        self.name = "ETF Holdings Fetcher"
        self.description = "基于akshare获取ETF持仓数据"
    
    def get_etf_holdings(self, etf_code: str, date: str = None, top_n: int = -1) -> Dict[str, Any]:
        """
        获取ETF持仓信息
        
        Args:
            etf_code: ETF代码，如 '510300'
            date: 查询年份，默认为当前年份
            top_n: 返回前N大持仓，-1表示返回全部
            
        Returns:
            Dict: 包含持仓信息的字典
        """
        try:
            # 如果没有指定日期，使用当前年份
            if date is None:
                date = str(datetime.now().year)
            
            print(f"📊 获取 {etf_code} ETF持仓数据（{date}年）...")
            
            # 获取持仓数据
            df_holdings = ak.fund_portfolio_hold_em(symbol=etf_code, date=date)
            
            if df_holdings.empty:
                return {
                    'error': f'未获取到 {etf_code} 的持仓数据',
                    'etf_code': etf_code,
                    'holdings_count': 0,
                    'holdings': []
                }
            
            # 按季度分组，找到最新的季度
            quarters = df_holdings['季度'].unique()
            print(f"📅 发现的季度: {list(quarters)}")
            
            # 字符串比较找到最新季度（最大的季度字符串）
            latest_quarter = max(quarters)
            print(f"📅 最新季度: {latest_quarter}")
            
            # 筛选最新季度的数据
            df_latest = df_holdings[df_holdings['季度'] == latest_quarter].copy()
            
            if df_latest.empty:
                return {
                    'error': f'未获取到 {etf_code} 最新季度的持仓数据',
                    'etf_code': etf_code,
                    'holdings_count': 0,
                    'holdings': []
                }
            
            # 按占净值比例降序排序
            df_latest = df_latest.sort_values('占净值比例', ascending=False)
            
            # 处理持仓数据（使用最新季度的数据）
            holdings = []
            total_holdings = len(df_latest)
            
            # 如果指定了top_n，则只取前N条
            display_df = df_latest.head(top_n) if top_n > 0 else df_latest
            
            for _, row in display_df.iterrows():
                holding = {
                    '序号': int(row.get('序号', 0)),
                    '股票代码': str(row.get('股票代码', '')),
                    '股票名称': str(row.get('股票名称', '')),
                    '占净值比例': float(row.get('占净值比例', 0)),
                    '持股数': row.get('持股数'),
                    '持仓市值': row.get('持仓市值'),
                    '季度': str(row.get('季度', ''))
                }
                holdings.append(holding)
            
            # 统计信息
            top_10_weight = sum([h['占净值比例'] for h in holdings[:10]])
            top_20_weight = sum([h['占净值比例'] for h in holdings[:20]])
            
            result = {
                'etf_code': etf_code,
                'data_date': date,
                'latest_quarter': latest_quarter,
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_holdings_count': total_holdings,
                'returned_holdings_count': len(holdings),
                'holdings': holdings,
                'statistics': {
                    'top_10_weight': round(top_10_weight, 2),
                    'top_20_weight': round(top_20_weight, 2),
                    'concentration_analysis': self._analyze_concentration(holdings)
                }
            }
            
            print(f"✅ 成功获取 {etf_code} 持仓数据，{latest_quarter}，共 {total_holdings} 只股票")
            return result
            
        except Exception as e:
            print(f"❌ 获取 {etf_code} 持仓数据失败: {e}")
            return {
                'error': str(e),
                'etf_code': etf_code,
                'holdings_count': 0,
                'holdings': []
            }
    
    def _analyze_concentration(self, holdings: List[Dict]) -> Dict[str, Any]:
        """分析持仓集中度"""
        if not holdings:
            return {}
        
        # 计算不同层级的集中度
        top_5_weight = sum([h['占净值比例'] for h in holdings[:5]])
        top_10_weight = sum([h['占净值比例'] for h in holdings[:10]])
        top_20_weight = sum([h['占净值比例'] for h in holdings[:20]])
        
        # 集中度分析
        concentration_level = "低"
        if top_10_weight > 50:
            concentration_level = "高"
        elif top_10_weight > 30:
            concentration_level = "中"
        
        return {
            'top_5_weight': round(top_5_weight, 2),
            'top_10_weight': round(top_10_weight, 2),
            'top_20_weight': round(top_20_weight, 2),
            'concentration_level': concentration_level,
            'analysis': f"前10大持仓占比{top_10_weight:.1f}%，集中度{concentration_level}"
        }
    
    def get_multiple_etf_holdings(self, etf_codes: List[str], date: str = None, top_n: int = 10) -> Dict[str, Any]:
        """
        批量获取多个ETF的持仓信息
        
        Args:
            etf_codes: ETF代码列表
            date: 查询年份
            top_n: 每个ETF返回前N大持仓
            
        Returns:
            Dict: 包含所有ETF持仓信息的字典
        """
        print(f"📊 批量获取 {len(etf_codes)} 个ETF的持仓数据...")
        
        results = {}
        success_count = 0
        
        for etf_code in etf_codes:
            holding_data = self.get_etf_holdings(etf_code, date, top_n)
            results[etf_code] = holding_data
            
            if 'error' not in holding_data:
                success_count += 1
        
        summary = {
            'total_etfs': len(etf_codes),
            'success_count': success_count,
            'failed_count': len(etf_codes) - success_count,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'etf_data': results
        }
        
        print(f"✅ 批量获取完成，成功 {success_count}/{len(etf_codes)} 个ETF")
        return summary
    
    def format_holdings_for_display(self, holdings_data: Dict[str, Any], max_display: int = 20) -> str:
        """
        格式化持仓数据为可显示的文本
        
        Args:
            holdings_data: 持仓数据字典
            max_display: 最多显示的持仓数量
            
        Returns:
            str: 格式化后的文本
        """
        if 'error' in holdings_data:
            return f"❌ 获取持仓数据失败: {holdings_data['error']}"
        
        etf_code = holdings_data['etf_code']
        holdings = holdings_data['holdings']
        statistics = holdings_data.get('statistics', {})
        
        # 构建显示文本
        lines = []
        lines.append(f"📊 ETF {etf_code} 持仓分析")
        lines.append("=" * 50)
        lines.append(f"📅 数据年份: {holdings_data.get('data_date', '')}")
        lines.append(f"📆 最新季度: {holdings_data.get('latest_quarter', '')}")
        lines.append(f"📈 持仓股票总数: {holdings_data.get('total_holdings_count', 0)}")
        
        # 集中度分析
        if statistics and 'concentration_analysis' in statistics:
            conc = statistics['concentration_analysis']
            lines.append(f"🎯 集中度分析: {conc.get('analysis', '')}")
        
        lines.append("")
        lines.append("🏆 主要持仓股票:")
        lines.append("-" * 50)
        
        # 显示持仓明细
        display_count = min(len(holdings), max_display)
        for i in range(display_count):
            holding = holdings[i]
            lines.append(f"{holding['序号']:2d}. {holding['股票代码']} {holding['股票名称']:10s} {holding['占净值比例']:6.2f}%")
        
        if len(holdings) > max_display:
            lines.append(f"... 还有 {len(holdings) - max_display} 只股票")
        
        return "\n".join(lines)
    
    def get_etf_info(self, etf_code: str) -> Dict[str, Any]:
        """
        获取ETF基本信息
        
        Args:
            etf_code: ETF代码
            
        Returns:
            Dict: ETF基本信息
        """
        try:
            print(f"📊 获取 {etf_code} ETF基本信息...")
            
            # 获取ETF现货数据
            df_spot = ak.fund_etf_spot_em()
            
            # 查找对应的ETF
            etf_info = df_spot[df_spot['代码'] == etf_code]
            
            if etf_info.empty:
                return {'error': f'未找到ETF {etf_code} 的基本信息'}
            
            info = etf_info.iloc[0]
            
            result = {
                'etf_code': etf_code,
                'etf_name': str(info.get('名称', '')),
                'current_price': float(info.get('最新价', 0)),
                'change_percent': float(info.get('涨跌幅', 0)),
                'change_amount': float(info.get('涨跌额', 0)),
                'volume': float(info.get('成交量', 0)),
                'turnover': float(info.get('成交额', 0)),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            print(f"✅ 成功获取 {etf_code} 基本信息")
            return result
            
        except Exception as e:
            print(f"❌ 获取 {etf_code} 基本信息失败: {e}")
            return {'error': str(e), 'etf_code': etf_code}


# 全局实例
etf_holdings_fetcher = ETFHoldingsFetcher()
