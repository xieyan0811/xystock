"""
A股大盘指标数据收集模块

本模块专门用于收集和计算A股市场的各种大盘指标，包括：
1. 技术指标（移动平均线、MACD、KDJ等）
2. 市场情绪指标（涨跌家数等）
3. 估值指标（沪深300估值等）
4. 资金流向指标（融资融券、M2等）
5. 新闻情绪指标
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import akshare as ak
import efinance as ef
from stockstats import wrap
from typing import Dict, List, Optional, Union
import warnings
warnings.filterwarnings('ignore')
from providers.stock_tools import get_indicators

class MarketIndicators:
    """A股大盘指标收集器"""
    
    def __init__(self):
        """初始化大盘指标收集器"""
        self.indices = {
            '上证指数': '000001',
            '深证成指': '399001', 
            '创业板指': '399006',
            '沪深300': '000300',
            '中证500': '000905',
            '科创50': '000688'
        }
        
    def get_index_technical_indicators(self, index_name: str = '上证指数', period: int = 100):
        """
        获取指数技术指标
        
        Args:
            index_name: 指数名称，支持：上证指数、深证成指、创业板指、沪深300、中证500、科创50
            period: 数据周期（天数）
            
        Returns:
            包含技术指标的字典
        """
        print(f"📊 获取{index_name}技术指标...")
        
        try:
            # 获取指数K线数据
            if index_name in self.indices:
                # 直接使用akshare获取指数数据
                import akshare as ak
                
                # 根据指数名称选择对应的akshare接口
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
                else:
                    raise ValueError(f"不支持的指数名称: {index_name}")
                
                if df_raw.empty:
                    return {}
                
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
                
            else:
                raise ValueError(f"不支持的指数名称: {index_name}")
            
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
    
    def get_market_sentiment_indicators(self) -> Dict:
        """
        获取市场情绪指标
        
        Returns:
            包含市场情绪指标的字典
        """
        print("📈 获取市场情绪指标...")
        
        sentiment_data = {}
        
        try:
            # 1. 涨跌家数统计 - 使用efinance获取实时行情
            print("   获取涨跌家数...")
            df_stocks = ef.stock.get_realtime_quotes()
            
            # 过滤掉涨跌幅为空的数据
            df_stocks = df_stocks.dropna(subset=['涨跌幅'])
            # 修复：将涨跌幅列转为float，避免字符串比较报错
            df_stocks["涨跌幅"] = pd.to_numeric(df_stocks["涨跌幅"], errors="coerce")
            #print(df_stocks)
            
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
            import traceback
            
            traceback.print_exc()
            print(f"   ❌ 获取涨跌家数失败: {e}")
                
        try:
            # 2. 融资融券数据 - 沪深两市
            print("   获取融资融券...")
            margin_data = self._get_margin_data_unified(include_historical=False)
            sentiment_data.update(margin_data)
            print(f"      上交所融资余额: {margin_data['margin_sh_buy']:.2f}亿")
            print(f"      深交所融资余额: {margin_data['margin_sz_buy']:.2f}亿")
            print(f"      两市融资余额合计: {margin_data['margin_buy_balance']:.2f}亿")
            
        except Exception as e:
            print(f"   ❌ 获取融资融券失败: {e}")
        
        # 添加更新时间
        sentiment_data['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print("   ✓ 市场情绪指标获取完成")
        return sentiment_data
    
    def get_valuation_indicators(self, debug=False) -> Dict:
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
    
    def get_money_flow_indicators(self, debug=True) -> Dict:
        """
        获取资金流向指标
        
        Returns:
            包含资金流向指标的字典
        """
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
                print(f"      M2余额: {money_flow_data['m2_amount']:.2f}万亿 | 同比增长: {money_flow_data['m2_growth']:.2f}%")

        except Exception as e:
            print(f"   ❌ 获取M2数据失败: {e}")
        
        # 添加更新时间
        money_flow_data['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print("   ✓ 资金流向指标获取完成")
        return money_flow_data
        
    def get_stock_gainers_losers(self, top_n: int = 10) -> Dict:
        """
        获取涨跌幅排行榜
        
        Args:
            top_n: 获取前N名
            
        Returns:
            包含涨跌幅排行的字典
        """
        print(f"📈 获取涨跌幅排行榜(Top {top_n})...")
        
        try:
            # 获取所有股票数据 - 使用efinance
            df_all_stocks = ef.stock.get_realtime_quotes()
            
            if df_all_stocks.empty:
                return {}
            
            # 过滤掉涨跌幅为空的数据
            df_all_stocks = df_all_stocks.dropna(subset=['涨跌幅'])
            
            # 涨幅榜
            top_gainers = df_all_stocks.nlargest(top_n, '涨跌幅')[['股票名称', '最新价', '涨跌幅', '成交额']]
            # 重命名列以保持兼容性
            top_gainers = top_gainers.rename(columns={'股票名称': '名称'})
            
            # 跌幅榜
            top_losers = df_all_stocks.nsmallest(top_n, '涨跌幅')[['股票名称', '最新价', '涨跌幅', '成交额']]
            # 重命名列以保持兼容性
            top_losers = top_losers.rename(columns={'股票名称': '名称'})
            
            # 成交额排行
            top_volume = df_all_stocks.nlargest(top_n, '成交额')[['股票名称', '最新价', '涨跌幅', '成交额']]
            # 重命名列以保持兼容性
            top_volume = top_volume.rename(columns={'股票名称': '名称'})
            
            result = {
                'top_gainers': top_gainers.to_dict('records'),
                'top_losers': top_losers.to_dict('records'),
                'top_volume': top_volume.to_dict('records'),
                'market_stats': {
                    'total_stocks': len(df_all_stocks),
                    'up_stocks': int((df_all_stocks["涨跌幅"] > 0).sum()),
                    'down_stocks': int((df_all_stocks["涨跌幅"] < 0).sum()),
                    'flat_stocks': int((df_all_stocks["涨跌幅"] == 0).sum()),
                },
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            print(f"   ✓ 涨幅榜首: {top_gainers.iloc[0]['名称']} (+{top_gainers.iloc[0]['涨跌幅']:.2f}%)")
            print(f"   ✓ 跌幅榜首: {top_losers.iloc[0]['名称']} ({top_losers.iloc[0]['涨跌幅']:.2f}%)")
            
            return result
            
        except Exception as e:
            print(f"   ❌ 获取涨跌幅排行失败: {e}")
            return {}
    
    def get_detailed_margin_data(self) -> Dict:
        """
        获取详细融资融券数据（沪深两市）
        
        Returns:
            包含详细融资融券数据的字典
        """
        print("💳 获取详细融资融券数据（沪深两市）...")
        
        try:
            margin_data = self._get_margin_data_unified(include_historical=True)
            
            if margin_data['margin_buy_balance'] == 0:
                return {}
            
            result = {
                'latest_date': margin_data['margin_date'],
                'margin_balance': margin_data['margin_balance'],
                'margin_buy_balance': margin_data['margin_buy_balance'],
                'margin_sell_balance': margin_data['margin_sell_balance'],
                'weekly_change': margin_data.get('weekly_change', 0),
                'change_ratio': margin_data.get('change_ratio', 0),
                'shanghai': margin_data.get('shanghai', {}),
                'shenzhen': margin_data.get('shenzhen', {}),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            print(f"   ✓ 上交所融资余额: {margin_data['margin_sh_buy']:.2f}亿")
            print(f"   ✓ 深交所融资余额: {margin_data['margin_sz_buy']:.2f}亿")
            print(f"   ✓ 两市融资余额合计: {result['margin_buy_balance']:.2f}亿")
            print(f"   ✓ 两市周变化: {result['weekly_change']:+.2f}亿 ({result['change_ratio']:+.2f}%)")
            
            return result
            
        except Exception as e:
            print(f"   ❌ 获取融资融券数据失败: {e}")
            return {}

    def _get_margin_data_unified(self, include_historical: bool = False) -> Dict:
        """
        统一的融资融券数据获取方法（沪深两市）
        
        Args:
            include_historical: 是否包含历史数据和变化趋势
            
        Returns:
            包含融资融券数据的字典
        """
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
                margin_sh_balance = float(latest_sh.get('融资融券余额', 0))
                margin_sh_buy = float(latest_sh.get('融资余额', 0))
                margin_sh_sell = float(latest_sh.get('融券余额', 0))
                margin_date = str(latest_sh.get('日期', result['margin_date']))
                
                result.update({
                    'margin_sh_balance': margin_sh_balance,
                    'margin_sh_buy': margin_sh_buy,
                    'margin_sh_sell': margin_sh_sell,
                    'margin_date': margin_date,
                })
                
                if include_historical:
                    prev_week_sh = df_margin_sh.iloc[-7] if len(df_margin_sh) >= 7 else df_margin_sh.iloc[0]
                    margin_change_sh = margin_sh_buy - prev_week_sh.get('融资余额', 0)
                    
                    sh_data = {
                        'margin_balance': margin_sh_balance,
                        'margin_buy_balance': margin_sh_buy,
                        'margin_sell_balance': margin_sh_sell,
                        'weekly_change': float(margin_change_sh),
                        'change_ratio': float(margin_change_sh / prev_week_sh.get('融资余额', 1) * 100) if prev_week_sh.get('融资余额', 0) > 0 else 0,
                        'historical_data': df_margin_sh.tail(10)[['日期', '融资余额', '融券余额', '融资融券余额']].to_dict('records'),
                    }
                
        except Exception as e:
            print(f"      ❌ 获取上交所融资融券失败: {e}")
        
        try:
            # 获取深交所数据
            df_margin_sz = ak.macro_china_market_margin_sz()
            if not df_margin_sz.empty:
                latest_sz = df_margin_sz.iloc[-1]
                margin_sz_balance = float(latest_sz.get('融资融券余额', 0))
                margin_sz_buy = float(latest_sz.get('融资余额', 0))
                margin_sz_sell = float(latest_sz.get('融券余额', 0))
                
                result.update({
                    'margin_sz_balance': margin_sz_balance,
                    'margin_sz_buy': margin_sz_buy,
                    'margin_sz_sell': margin_sz_sell,
                })
                
                if include_historical:
                    prev_week_sz = df_margin_sz.iloc[-7] if len(df_margin_sz) >= 7 else df_margin_sz.iloc[0]
                    margin_change_sz = margin_sz_buy - prev_week_sz.get('融资余额', 0)
                    
                    sz_data = {
                        'margin_balance': margin_sz_balance,
                        'margin_buy_balance': margin_sz_buy,
                        'margin_sell_balance': margin_sz_sell,
                        'weekly_change': float(margin_change_sz),
                        'change_ratio': float(margin_change_sz / prev_week_sz.get('融资余额', 1) * 100) if prev_week_sz.get('融资余额', 0) > 0 else 0,
                        'historical_data': df_margin_sz.tail(10)[['日期', '融资余额', '融券余额', '融资融券余额']].to_dict('records'),
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
    
    def get_comprehensive_market_report(self, index_name: str = '上证指数') -> Dict:
        """
        获取综合市场报告
        
        Args:
            index_name: 主要关注的指数名称
            
        Returns:
            包含所有大盘指标的综合报告
        """
        print(f"📋 生成{index_name}综合市场报告...")
        print("=" * 60)
        
        report = {
            'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'focus_index': index_name,
            'technical_indicators': {},
            'sentiment_indicators': {},
            'valuation_indicators': {},
            'money_flow_indicators': {},
            'market_summary': {}
        }
        
        # 获取各类指标
        report['technical_indicators'] = self.get_index_technical_indicators(index_name)
        report['sentiment_indicators'] = self.get_market_sentiment_indicators()
        report['valuation_indicators'] = self.get_valuation_indicators()
        report['money_flow_indicators'] = self.get_money_flow_indicators()
        
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

def get_market_indicators_summary(index_name: str = '上证指数') -> Dict:
    """
    获取市场指标摘要（便捷函数）
    
    Args:
        index_name: 指数名称
        
    Returns:
        市场指标摘要字典
    """
    collector = MarketIndicators()
    return collector.get_comprehensive_market_report(index_name)


def quick_market_analysis(index_name: str = '上证指数', show_details: bool = True) -> Dict:
    """
    快速市场分析（便捷函数）
    
    Args:
        index_name: 指数名称
        show_details: 是否显示详细报告
        
    Returns:
        市场分析结果
    """
    collector = MarketIndicators()
    
    print(f"🚀 快速分析{index_name}市场状况...")
    
    # 获取综合报告
    report = collector.get_comprehensive_market_report(index_name)
    
    # 如果需要显示详细信息
    if show_details:
        display_market_report(report)
    
    return report


def get_market_rankings(top_n: int = 10) -> Dict:
    """
    获取市场排行榜（便捷函数）
    
    Args:
        top_n: 排行榜数量
        
    Returns:
        排行榜数据
    """
    collector = MarketIndicators()
    return collector.get_stock_gainers_losers(top_n)


def display_market_report(report: Dict):
    """
    美化显示市场报告
    
    Args:
        report: 市场报告字典
    """
    print(f"\n📊 A股市场综合报告")
    print(f"🕐 报告时间: {report['report_time']}")
    print(f"🎯 关注指数: {report['focus_index']}")
    print("=" * 80)
    
    # 技术指标
    tech = report['technical_indicators']
    if tech:
        print(f"\n📈 技术指标分析:")
        print(f"   当前点位: {tech.get('latest_close', 'N/A'):.2f}")
        print(f"   MA趋势: {tech.get('ma_trend', 'N/A')}")
        print(f"   MACD趋势: {tech.get('macd_trend', 'N/A')}")
        print(f"   RSI(14): {tech.get('rsi_14', 'N/A'):.2f}")
        print(f"   KDJ: K={tech.get('kdj_k', 'N/A'):.2f} D={tech.get('kdj_d', 'N/A'):.2f} J={tech.get('kdj_j', 'N/A'):.2f}")
    
    # 市场情绪
    sentiment = report['sentiment_indicators']
    if sentiment:
        print(f"\n😊 市场情绪指标:")
        print(f"   涨跌家数: ↗{sentiment.get('up_stocks', 'N/A')} | ↘{sentiment.get('down_stocks', 'N/A')} | →{sentiment.get('flat_stocks', 'N/A')}")
        print(f"   上涨占比: {sentiment.get('up_ratio', 0)*100:.1f}%")
        print(f"   融资余额: {sentiment.get('margin_buy_balance', 'N/A'):.2f}")
    
    # 估值水平
    valuation = report['valuation_indicators']
    if valuation:
        print(f"\n💰 估值水平:")
        print(f"   沪深300 PE: {valuation.get('hs300_pe', 'N/A'):.2f}")
        print(f"   股息率: {valuation.get('hs300_dividend_yield', 'N/A'):.2f}%")
    
    # 资金面
    money = report['money_flow_indicators']
    if money:
        print(f"\n💸 资金流向:")
        print(f"   M2余额: {money.get('m2_amount', 'N/A'):.2f}亿")
        print(f"   M2增速: {money.get('m2_growth', 'N/A'):.2f}%")
        print(f"   M1增速: {money.get('m1_growth', 'N/A'):.2f}%")
    
    # 市场摘要
    summary = report['market_summary']
    if summary:
        print(f"\n🎯 市场摘要:")
        for key, value in summary.items():
            print(f"   {key}: {value}")
    
    print("=" * 80)


if __name__ == "__main__":
    # 测试用例
    print("🧪 测试大盘指标收集模块...")
    
    collector = MarketIndicators()
    
    # 测试单个指标
    print("\n1. 测试技术指标:")
    tech_indicators = collector.get_index_technical_indicators('上证指数')
    print(f"技术指标数量: {len(tech_indicators)}")
    
    print("\n2. 测试市场情绪:")
    sentiment_indicators = collector.get_market_sentiment_indicators()
    print(f"情绪指标数量: {len(sentiment_indicators)}")
    
    print("\n3. 测试估值指标:")
    valuation_indicators = collector.get_valuation_indicators()
    print(f"估值指标数量: {len(valuation_indicators)}")
    
    print("\n4. 测试资金流向:")
    money_flow_indicators = collector.get_money_flow_indicators()
    print(f"资金流向指标数量: {len(money_flow_indicators)}")
        
    print("\n6. 测试涨跌榜:")
    rankings = collector.get_stock_gainers_losers(5)
    print(f"排行榜数据可用: {'是' if rankings else '否'}")
        
    print("\n8. 测试综合报告:")
    report = collector.get_comprehensive_market_report('上证指数')
    display_market_report(report)
    
    print("\n9. 测试便捷函数:")
    quick_analysis = quick_market_analysis('上证指数', show_details=False)
    print(f"快速分析完成: {'是' if quick_analysis else '否'}")
    
    print("\n✅ 测试完成!")
