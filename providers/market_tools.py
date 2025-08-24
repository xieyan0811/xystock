"""
A股大盘指标数据收集模块

本模块专门用于收集和计算A股市场的各种大盘指标，包括：
1. 技术指标（移动平均线、MACD、KDJ等）
2. 市场情绪指标（涨跌家数等）
3. 估值指标（沪深300估值等）
4. 资金流向指标（融资融券、M2等）
5. 新闻情绪指标
"""

import sys # for test
sys.path.append('/app')

import pandas as pd
from datetime import datetime
import akshare as ak
import efinance as ef
from typing import Dict
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
    
    def get_market_sentiment_indicators(self):
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
    
    def get_valuation_indicators(self, debug=False):
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
    
    def get_money_flow_indicators(self, debug=True):
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
                print(f"      M2余额: {money_flow_data['m2_amount']/10000:.2f}万亿 | 同比增长: {money_flow_data['m2_growth']:.2f}%")

        except Exception as e:
            print(f"   ❌ 获取M2数据失败: {e}")
        
        # 添加更新时间
        money_flow_data['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print("   ✓ 资金流向指标获取完成")
        return money_flow_data
            
    def get_detailed_margin_data(self):
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

    def _get_margin_data_unified(self, include_historical: bool = False):
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
    
    def get_comprehensive_market_report(self, index_name: str = '上证指数'):
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
    
    def _generate_market_summary(self, report: Dict):
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
        
    def _judge_rsi_level(self, rsi: float):
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
        

def get_market_report(report: Dict):
    """
    生成市场报告字符串
    
    Args:
        report: 市场报告字典
        
    Returns:
        str: 格式化的市场报告字符串
    """
    lines = []
    lines.append(f"\n📊 A股市场综合报告")
    lines.append(f"🕐 报告时间: {report['report_time']}")
    lines.append(f"🎯 关注指数: {report['focus_index']}")
    lines.append("=" * 80)
    
    # 技术指标
    tech = report['technical_indicators']
    if tech:
        lines.append(f"\n📈 技术指标分析:")
        latest_close = tech.get('latest_close', 'N/A')
        if isinstance(latest_close, (int, float)):
            lines.append(f"   当前点位: {latest_close:.2f}")
        else:
            lines.append(f"   当前点位: {latest_close}")
        lines.append(f"   MA趋势: {tech.get('ma_trend', 'N/A')}")
        lines.append(f"   MACD趋势: {tech.get('macd_trend', 'N/A')}")
        rsi_14 = tech.get('rsi_14', 'N/A')
        if isinstance(rsi_14, (int, float)):
            lines.append(f"   RSI(14): {rsi_14:.2f}")
        else:
            lines.append(f"   RSI(14): {rsi_14}")
        kdj_k = tech.get('kdj_k', 'N/A')
        kdj_d = tech.get('kdj_d', 'N/A')
        kdj_j = tech.get('kdj_j', 'N/A')
        k_str = f"{kdj_k:.2f}" if isinstance(kdj_k, (int, float)) else str(kdj_k)
        d_str = f"{kdj_d:.2f}" if isinstance(kdj_d, (int, float)) else str(kdj_d)
        j_str = f"{kdj_j:.2f}" if isinstance(kdj_j, (int, float)) else str(kdj_j)
        lines.append(f"   KDJ: K={k_str} D={d_str} J={j_str}")
    
    # 市场情绪
    sentiment = report['sentiment_indicators']
    if sentiment:
        lines.append(f"\n😊 市场情绪指标:")
        lines.append(f"   涨跌家数: ↗{sentiment.get('up_stocks', 'N/A')} | ↘{sentiment.get('down_stocks', 'N/A')} | →{sentiment.get('flat_stocks', 'N/A')}")
        up_ratio = sentiment.get('up_ratio', 0)
        lines.append(f"   上涨占比: {up_ratio*100:.1f}%")
        margin_buy = sentiment.get('margin_buy_balance', 'N/A')
        if isinstance(margin_buy, (int, float)):
            lines.append(f"   融资余额: {margin_buy:.2f}")
        else:
            lines.append(f"   融资余额: {margin_buy}")
    
    # 估值水平
    valuation = report['valuation_indicators']
    if valuation:
        lines.append(f"\n💰 估值水平:")
        hs300_pe = valuation.get('hs300_pe', 'N/A')
        if isinstance(hs300_pe, (int, float)):
            lines.append(f"   沪深300 PE: {hs300_pe:.2f}")
        else:
            lines.append(f"   沪深300 PE: {hs300_pe}")
        dividend_yield = valuation.get('hs300_dividend_yield', 'N/A')
        if isinstance(dividend_yield, (int, float)):
            lines.append(f"   股息率: {dividend_yield:.2f}%")
        else:
            lines.append(f"   股息率: {dividend_yield}%")
    
    # 资金面
    money = report['money_flow_indicators']
    if money:
        lines.append(f"\n💸 资金流向:")
        m2_amount = money.get('m2_amount', 'N/A')
        if isinstance(m2_amount, (int, float)):
            lines.append(f"   M2余额: {m2_amount:.2f}亿")
        else:
            lines.append(f"   M2余额: {m2_amount}亿")
        m2_growth = money.get('m2_growth', 'N/A')
        if isinstance(m2_growth, (int, float)):
            lines.append(f"   M2增速: {m2_growth:.2f}%")
        else:
            lines.append(f"   M2增速: {m2_growth}%")
        m1_growth = money.get('m1_growth', 'N/A')
        if isinstance(m1_growth, (int, float)):
            lines.append(f"   M1增速: {m1_growth:.2f}%")
        else:
            lines.append(f"   M1增速: {m1_growth}%")
    
    # 市场摘要
    summary = report['market_summary']
    if summary:
        lines.append(f"\n🎯 市场摘要:")
        for key, value in summary.items():
            lines.append(f"   {key}: {value}")
    
    lines.append("=" * 80)
    
    return '\n'.join(lines)


def display_index_info(index_name: str = '上证指数', use_cache: bool = True, force_refresh: bool = False):
    """
    显示指数信息（使用缓存）
    
    Args:
        index_name: 指数名称
        use_cache: 是否使用缓存
        force_refresh: 是否强制刷新缓存
    
    Returns:
        格式化的市场信息字符串
    """
    if use_cache:
        # 使用缓存管理器
        from market_data_cache import get_cache_manager
        cache_manager = get_cache_manager()
        
        print("=" * 80)
        print(f"📊 {index_name} 市场信息 (缓存模式)")
        print("=" * 80)
        
        # 获取技术指标（不缓存，因为指数相关）
        collector = MarketIndicators()
        tech_data = collector.get_index_technical_indicators(index_name)
        
        # 获取缓存的基础市场数据
        sentiment_data = cache_manager.get_market_sentiment(force_refresh)
        valuation_data = cache_manager.get_valuation_data(force_refresh)
        money_flow_data = cache_manager.get_money_flow_data(force_refresh)
        margin_data = cache_manager.get_margin_data(force_refresh)
        ai_analysis_data = cache_manager.get_ai_analysis(force_refresh)
        
        # 构建报告
        report = {
            'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'focus_index': index_name,
            'technical_indicators': tech_data,
            'sentiment_indicators': sentiment_data,
            'valuation_indicators': valuation_data,
            'money_flow_indicators': money_flow_data,
            'margin_detail': margin_data,
            'ai_analysis': ai_analysis_data,
            'market_summary': {}
        }
        
        # 生成市场摘要
        collector = MarketIndicators()
        report['market_summary'] = collector._generate_market_summary(report)
        
        return get_market_report(report)
    else:
        # 使用原始方法（不缓存）
        collector = MarketIndicators()
        report = collector.get_comprehensive_market_report(index_name)
        return get_market_report(report)


def show_cache_status():
    """显示缓存状态"""
    from providers.market_data_cache import get_cache_manager
    cache_manager = get_cache_manager()
    cache_manager.print_cache_status()


def clear_market_cache(data_type: str = None):
    """
    清理市场数据缓存
    
    Args:
        data_type: 数据类型，可选值：
                  - market_sentiment: 市场情绪
                  - valuation: 估值指标  
                  - money_flow: 资金流向
                  - margin_detail: 融资融券
                  - ai_analysis: AI分析
                  - None: 清理所有缓存
    """
    from providers.market_data_cache import get_cache_manager
    cache_manager = get_cache_manager()
    cache_manager.clear_cache(data_type)


def refresh_all_cache():
    """刷新所有缓存数据"""
    from providers.market_data_cache import get_cache_manager
    cache_manager = get_cache_manager()
    
    print("🔄 开始刷新所有缓存数据...")
    
    # 强制刷新所有数据
    cache_manager.get_market_sentiment(force_refresh=True)
    cache_manager.get_valuation_data(force_refresh=True) 
    cache_manager.get_money_flow_data(force_refresh=True)
    cache_manager.get_margin_data(force_refresh=True)
    
    print("✅ 所有缓存数据刷新完成!")
    show_cache_status()


def set_ai_market_analysis(analysis_data: Dict):
    """
    设置AI市场分析数据
    
    Args:
        analysis_data: AI分析数据字典，建议包含以下字段：
            - market_trend: 市场趋势判断
            - confidence_level: 信心度
            - risk_assessment: 风险评估
            - suggestions: 投资建议
            - analysis_time: 分析时间
    """
    from market_data_cache import get_cache_manager
    cache_manager = get_cache_manager()
    
    # 添加时间戳
    analysis_data['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cache_manager.set_ai_analysis(analysis_data)
    print("✅ AI市场分析数据已更新")


def get_ai_market_analysis() -> Dict:
    """获取AI市场分析数据"""
    from market_data_cache import get_cache_manager
    cache_manager = get_cache_manager()
    return cache_manager.get_ai_analysis()


def update_ai_analysis_example():
    """设置AI分析数据的示例"""
    example_analysis = {
        'market_trend': '震荡上涨',
        'confidence_level': 0.75,
        'risk_assessment': '中等风险',
        'technical_summary': '技术指标显示多空分歧',
        'sentiment_summary': '市场情绪偏谨慎',
        'suggestions': [
            '建议关注权重股表现',
            '注意控制仓位风险',
            '关注政策面变化'
        ],
        'key_factors': [
            '宏观经济数据',
            '资金流向变化',
            '政策预期'
        ]
    }
    
    set_ai_market_analysis(example_analysis)
    print("📝 AI分析示例数据已设置")


if __name__ == "__main__":
    # 测试用例
    print("🧪 测试大盘指标收集模块...")
    
    # 测试缓存功能
    print("\n=== 缓存功能测试 ===")
    
    print("\n1. 显示缓存状态:")
    show_cache_status()
    
    print("\n2. 测试缓存模式的市场信息:")
    market_info = display_index_info('上证指数', use_cache=True)
    print(market_info)
    
    print("\n3. 再次获取（应使用缓存）:")
    market_info2 = display_index_info('上证指数', use_cache=True)
    
    print("\n4. 显示更新后的缓存状态:")
    show_cache_status()
    
    # 测试原始功能（不使用缓存）
    print("\n=== 原始功能测试 ===")
    collector = MarketIndicators()
    
    print("\n5. 测试技术指标:")
    tech_indicators = collector.get_index_technical_indicators('上证指数')
    print(f"技术指标数量: {len(tech_indicators)}")
    
    print("\n6. 测试无缓存模式:")
    market_info_no_cache = display_index_info('上证指数', use_cache=False)
    
    print("\n✅ 测试完成!")
