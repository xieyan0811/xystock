#!/usr/bin/env python3
"""
用于验证大盘分析模块的各项功能是否正常工作。

测试覆盖范围：
1. 技术指标获取和计算
2. 市场情绪指标
3. 估值指标  
4. 资金流向指标
5. 综合市场报告生成
6. 便捷函数功能
"""

import sys
import os
import unittest
import warnings
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
XYSTOCK_DIR = os.path.dirname(CURRENT_DIR)
if XYSTOCK_DIR not in sys.path:
    sys.path.insert(0, XYSTOCK_DIR)

# 清理代理设置，避免网络问题
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)

# 忽略警告
warnings.filterwarnings('ignore')

# 导入大盘分析模块
from providers.market_tools import (
    get_market_tools,
    get_market_report,
    display_index_info,
    show_cache_status
)


class TestMarketIndicators(unittest.TestCase):
    """大盘指标测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.market_collector = get_market_tools()
        cls.test_index = '上证指数'
        cls.supported_indices = ['上证指数', '深证成指', '创业板指', '沪深300', '中证500', '科创50']
        print(f"\n🚀 开始测试大盘分析模块...")
        print(f"📊 测试指数: {cls.test_index}")
        print("=" * 60)
    
    def test_technical_indicators(self):
        """测试技术指标获取"""
        print(f"\n📈 测试技术指标获取...")
        
        tech_indicators = self.market_collector.get_index_technical_indicators(self.test_index)
        
        # 验证基本结构
        assert isinstance(tech_indicators, dict), "技术指标应返回字典类型"
        
        if tech_indicators:  # 如果成功获取数据
            # 检查必要字段
            required_fields = ['latest_close', 'latest_date', 'ma_trend', 'macd_trend']
            for field in required_fields:
                assert field in tech_indicators, f"缺少必要字段: {field}"
            
            # 检查数据类型
            assert isinstance(tech_indicators['latest_close'], (int, float)), "最新收盘价应为数字"
            assert isinstance(tech_indicators['ma_trend'], str), "MA趋势应为字符串"
            assert isinstance(tech_indicators['macd_trend'], str), "MACD趋势应为字符串"
            
            # 检查技术指标数值的合理性
            if tech_indicators.get('rsi_14') is not None:
                rsi = tech_indicators['rsi_14']
                assert 0 <= rsi <= 100, f"RSI值应在0-100之间，当前值: {rsi}"
            
            print(f"   ✓ 技术指标获取成功，包含 {len(tech_indicators)} 个指标")
            print(f"   ✓ MA趋势: {tech_indicators['ma_trend']}")
            print(f"   ✓ MACD趋势: {tech_indicators['macd_trend']}")
        else:
            print("   ⚠️  技术指标获取失败，可能是网络问题")
    
    def test_multiple_indices_technical_indicators(self):
        """测试多个指数的技术指标"""
        print(f"\n📊 测试多指数技术指标比较...")
        
        results = {}
        for index in self.supported_indices:
            tech = self.market_collector.get_index_technical_indicators(index)
            results[index] = tech
            
            if tech:
                current_price = tech.get('latest_close', 0)
                ma_trend = tech.get('ma_trend', '未知')
                rsi = tech.get('rsi_14', 0)
                print(f"   {index}: {current_price:.2f} | {ma_trend} | RSI {rsi:.1f}")
        
        # 验证至少有一个指数获取成功
        successful_indices = [idx for idx, data in results.items() if data]
        assert len(successful_indices) > 0, "至少应有一个指数获取成功"
        print(f"   ✓ 成功获取 {len(successful_indices)} 个指数数据")
    
    def test_market_sentiment_indicators(self):
        """测试市场情绪指标"""
        print(f"\n😊 测试市场情绪指标...")
        
        sentiment = self.market_collector.get_market_sentiment_indicators()
        
        assert isinstance(sentiment, dict), "市场情绪指标应返回字典类型"
        
        if sentiment:
            # 检查涨跌家数相关字段
            sentiment_fields = ['up_stocks', 'down_stocks', 'total_stocks', 'up_ratio']
            available_fields = [field for field in sentiment_fields if field in sentiment]
            
            if available_fields:
                print(f"   ✓ 涨跌家数统计可用")
                if 'up_stocks' in sentiment and 'down_stocks' in sentiment:
                    up_count = sentiment['up_stocks']
                    down_count = sentiment['down_stocks']
                    total_count = sentiment.get('total_stocks', up_count + down_count)
                    print(f"   ✓ 上涨: {up_count} | 下跌: {down_count} | 总计: {total_count}")
                    
                    # 验证数据合理性
                    assert up_count >= 0, "上涨家数不能为负"
                    assert down_count >= 0, "下跌家数不能为负"
            
            # 检查融资融券数据
            if 'margin_buy_balance' in sentiment:
                margin_balance = sentiment['margin_buy_balance']
                print(f"   ✓ 融资余额: {margin_balance:.2f}")
                assert margin_balance >= 0, "融资余额不能为负"
            
            print(f"   ✓ 市场情绪指标获取成功，包含 {len(sentiment)} 个指标")
        else:
            print("   ⚠️  市场情绪指标获取失败，可能是网络问题")
    
    def test_valuation_indicators(self):
        """测试估值指标"""
        print(f"\n💰 测试估值指标...")
        
        valuation = self.market_collector.get_valuation_indicators()
        
        assert isinstance(valuation, dict), "估值指标应返回字典类型"
        
        if valuation:
            # 检查沪深300估值指标
            hs300_fields = ['hs300_pe', 'hs300_dividend_yield']
            available_fields = [field for field in hs300_fields if field in valuation]
            
            if available_fields:
                print(f"   ✓ 沪深300估值数据可用")
                
                if 'hs300_pe' in valuation:
                    pe = valuation['hs300_pe']
                    print(f"   ✓ 沪深300 PE: {pe:.2f}")
                    
                    # 验证估值合理性
                    assert pe > 0, "PE值应大于0"
                    assert pe < 100, "PE值应在合理范围内"  # 通常不会超过100
            
            print(f"   ✓ 估值指标获取成功，包含 {len(valuation)} 个指标")
        else:
            print("   ⚠️  估值指标获取失败，可能是网络问题")
    
    def test_money_flow_indicators(self):
        """测试资金流向指标"""
        print(f"\n💸 测试资金流向指标...")
        
        money_flow = self.market_collector.get_money_flow_indicators(debug=True)
        
        assert isinstance(money_flow, dict), "资金流向指标应返回字典类型"
        
        if money_flow:
            # 检查M2货币供应量数据
            m2_fields = ['m2_amount', 'm2_growth', 'm1_amount', 'm1_growth']
            available_fields = [field for field in m2_fields if field in money_flow]
            
            if available_fields:
                print(f"   ✓ M2货币供应量数据可用")
                
                if 'm2_amount' in money_flow and 'm2_growth' in money_flow:
                    m2_amount = money_flow['m2_amount']
                    m2_growth = money_flow['m2_growth']
                    print(f"   ✓ M2余额: {m2_amount:.2f}万亿 | 同比增长: {m2_growth:.2f}%")
                    
                    # 验证数据合理性
                    assert m2_amount > 0, "M2余额应大于0"
                    assert -20 < m2_growth < 50, "M2增长率应在合理范围内"  # 通常在-20%到50%之间
            
            print(f"   ✓ 资金流向指标获取成功，包含 {len(money_flow)} 个指标")
        else:
            print("   ⚠️  资金流向指标获取失败，可能是网络问题")
    
    def test_stock_rankings(self):
        """测试涨跌幅排行榜"""
        print(f"\n📈 测试涨跌幅排行榜...")
        
        rankings = self.market_collector.get_stock_gainers_losers(top_n=5)
        
        assert isinstance(rankings, dict), "排行榜应返回字典类型"
        
        if rankings:
            # 检查排行榜结构
            expected_keys = ['top_gainers', 'top_losers', 'top_volume', 'market_stats']
            available_keys = [key for key in expected_keys if key in rankings]
            
            assert len(available_keys) > 0, "应包含至少一个排行榜类型"
            
            # 检查涨幅榜
            if 'top_gainers' in rankings and rankings['top_gainers']:
                top_gainer = rankings['top_gainers'][0]
                print(f"   ✓ 涨幅榜首: {top_gainer.get('名称', 'N/A')} (+{top_gainer.get('涨跌幅', 0):.2f}%)")
                assert isinstance(top_gainer.get('涨跌幅', 0), (int, float)), "涨跌幅应为数字"
            
            # 检查跌幅榜
            if 'top_losers' in rankings and rankings['top_losers']:
                top_loser = rankings['top_losers'][0]
                print(f"   ✓ 跌幅榜首: {top_loser.get('名称', 'N/A')} ({top_loser.get('涨跌幅', 0):.2f}%)")
                assert isinstance(top_loser.get('涨跌幅', 0), (int, float)), "涨跌幅应为数字"
            
            # 检查市场统计
            if 'market_stats' in rankings:
                stats = rankings['market_stats']
                if 'total_stocks' in stats:
                    total = stats['total_stocks']
                    print(f"   ✓ 统计股票总数: {total}")
                    assert total > 0, "股票总数应大于0"
            
            print(f"   ✓ 排行榜数据获取成功")
        else:
            print("   ⚠️  排行榜数据获取失败，可能是网络问题")
    
    def test_detailed_margin_data(self):
        """测试详细融资融券数据"""
        print(f"\n💳 测试详细融资融券数据...")
        
        margin_detail = self.market_collector.get_detailed_margin_data()
        
        assert isinstance(margin_detail, dict), "融资融券详细数据应返回字典类型"
        
        if margin_detail:
            # 检查必要字段
            required_fields = ['margin_buy_balance', 'weekly_change', 'change_ratio']
            available_fields = [field for field in required_fields if field in margin_detail]
            
            if available_fields:
                balance = margin_detail.get('margin_buy_balance', 0)
                weekly_change = margin_detail.get('weekly_change', 0)
                change_ratio = margin_detail.get('change_ratio', 0)
                
                print(f"   ✓ 融资余额: {balance:.2f}")
                print(f"   ✓ 周变化: {weekly_change:+.2f}亿 ({change_ratio:+.2f}%)")
                
                # 验证数据合理性
                assert balance >= 0, "融资余额应大于等于0"
                assert -100 < change_ratio < 100, "变化比例应在合理范围内"
            
            print(f"   ✓ 详细融资融券数据获取成功")
        else:
            print("   ⚠️  详细融资融券数据获取失败，可能是网络问题")
    
    def test_comprehensive_market_report(self):
        """测试综合市场报告"""
        print(f"\n📋 测试综合市场报告...")
        
        comprehensive_report = self.market_collector.get_comprehensive_market_report(self.test_index)
        
        assert isinstance(comprehensive_report, dict), "综合报告应返回字典类型"
        assert 'report_time' in comprehensive_report, "应包含报告时间"
        assert 'focus_index' in comprehensive_report, "应包含关注指数"
        
        # 检查报告结构
        expected_sections = [
            'technical_indicators', 
            'sentiment_indicators',
            'valuation_indicators', 
            'money_flow_indicators',
            'market_summary'
        ]
        
        for section in expected_sections:
            assert section in comprehensive_report, f"应包含 {section} 部分"
        
        # 验证报告内容不为空
        non_empty_sections = []
        for section in expected_sections:
            if comprehensive_report[section]:
                non_empty_sections.append(section)
        
        print(f"   ✓ 报告结构完整，包含 {len(expected_sections)} 个部分")
        print(f"   ✓ 有效数据部分: {len(non_empty_sections)} 个")
        print(f"   ✓ 报告时间: {comprehensive_report['report_time']}")
        print(f"   ✓ 关注指数: {comprehensive_report['focus_index']}")
        
        # 如果有市场摘要，检查其内容
        if comprehensive_report['market_summary']:
            summary = comprehensive_report['market_summary']
            print(f"   ✓ 市场摘要包含 {len(summary)} 项指标")
        
        assert len(non_empty_sections) > 0, "至少应有一个部分包含有效数据"
    
    def test_convenience_functions(self):
        """测试便捷函数"""
        print(f"\n🔧 测试便捷函数...")
        
        # 测试综合市场报告
        print("   测试综合市场报告...")
        quick_report = self.market_collector.get_comprehensive_market_report(self.test_index, use_cache=False)
        assert isinstance(quick_report, dict), "综合报告应返回字典类型"
        print("   ✓ 综合市场报告功能正常")
        
        # 测试缓存状态显示
        print("   测试缓存状态显示...")
        show_cache_status()
        print("   ✓ 缓存状态显示功能正常")
        
        # 测试估值指标
        print("   测试估值指标...")
        valuation_data = self.market_collector.get_valuation_data(use_cache=False)
        assert isinstance(valuation_data, dict), "估值指标应返回字典类型"
        print("   ✓ 估值指标功能正常")
        
        print("   ✓ 所有便捷函数测试通过")
    
    def test_display_market_report(self):
        """测试报告显示功能"""
        print(f"\n🖥️  测试报告显示功能...")
        
        # 生成测试报告
        report = self.market_collector.get_comprehensive_market_report(self.test_index)
        
        # 测试显示功能（不会抛出异常即为成功）
        try:
            print("   测试美化显示功能...")
            from providers.market_tools import get_market_report
            report_str = get_market_report(report)
            assert isinstance(report_str, str), "报告格式化应返回字符串"
            print("   ✓ 报告显示功能正常")
        except Exception as e:
            self.fail(f"报告显示功能出现异常: {e}")
    
    def test_data_validation(self):
        """测试数据验证和边界情况"""
        print(f"\n🧪 测试数据验证和边界情况...")
        
        # 测试不支持的指数
        print("   测试不支持的指数...")
        invalid_result = self.market_collector.get_index_technical_indicators('不存在的指数')
        assert isinstance(invalid_result, dict), "不支持的指数应返回空字典"
        
        # 测试各种参数
        print("   测试不同参数组合...")
        for period in [30, 60, 100]:
            result = self.market_collector.get_index_technical_indicators(self.test_index, period=period)
            assert isinstance(result, dict), f"period={period} 应返回字典类型"
        
        print("   ✓ 数据验证测试通过")
    
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        print("\n" + "=" * 60)
        print("✅ 大盘分析模块测试完成!")
        print(f"📊 测试指数: {cls.test_index}")
        print(f"🕐 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


class TestIntegrationScenarios(unittest.TestCase):
    """集成测试场景"""
    
    def setUp(self):
        """每个测试方法的初始化"""
        self.market_collector = get_market_tools()
    
    def test_daily_market_analysis_workflow(self):
        """测试日常市场分析工作流"""
        print(f"\n🚀 测试日常市场分析工作流...")
        
        # 1. 获取综合分析报告
        print("   步骤1: 获取综合市场分析...")
        comprehensive_report = self.market_collector.get_comprehensive_market_report('上证指数', use_cache=False)
        assert isinstance(comprehensive_report, dict), "综合分析应返回字典"
        
        # 2. 获取主要技术指标
        print("   步骤2: 获取技术指标...")
        tech_indicators = self.market_collector.get_index_technical_indicators('上证指数')
        
        if tech_indicators:
            key_indicators = ['latest_close', 'ma_5', 'ma_20', 'rsi_14', 'macd', 'ma_trend', 'macd_trend']
            for indicator in key_indicators:
                value = tech_indicators.get(indicator)
                if value is not None:
                    print(f"      {indicator}: {value}")
        
        # 3. 比较多个指数
        print("   步骤3: 比较多个指数...")
        indices = ['上证指数', '深证成指', '创业板指']
        index_comparison = {}
        
        for index in indices:
            tech = self.market_collector.get_index_technical_indicators(index)
            if tech:
                index_comparison[index] = {
                    'price': tech.get('latest_close', 0),
                    'trend': tech.get('ma_trend', '未知'),
                    'rsi': tech.get('rsi_14', 0)
                }
        
        assert len(index_comparison) > 0, "应至少成功比较一个指数"
        print(f"      成功比较 {len(index_comparison)} 个指数")
        
        # 4. 获取市场情绪
        print("   步骤4: 获取市场情绪...")
        sentiment = self.market_collector.get_market_sentiment_indicators()
        valuation = self.market_collector.get_valuation_indicators()
        money_flow = self.market_collector.get_money_flow_indicators(debug=True)
        
        available_modules = []
        if sentiment: available_modules.append("情绪")
        if valuation: available_modules.append("估值")
        if money_flow: available_modules.append("资金")
        
        print(f"      可用模块: {', '.join(available_modules)}")
        
        print("   ✅ 日常分析工作流测试完成")
    
    def test_data_consistency(self):
        """测试数据一致性"""
        print(f"\n🔍 测试数据一致性...")
        
        # 多次获取同一指标，验证数据一致性
        index_name = '上证指数'
        
        # 第一次获取
        tech1 = self.market_collector.get_index_technical_indicators(index_name)
        sentiment1 = self.market_collector.get_market_sentiment_indicators()
        
        # 第二次获取
        tech2 = self.market_collector.get_index_technical_indicators(index_name)
        sentiment2 = self.market_collector.get_market_sentiment_indicators()
        
        # 验证基本一致性（同一时间段内数据应该相近）
        if tech1 and tech2:
            price1 = tech1.get('latest_close', 0)
            price2 = tech2.get('latest_close', 0)
            if price1 > 0 and price2 > 0:
                price_diff = abs(price1 - price2) / price1
                assert price_diff < 0.1, f"价格差异过大: {price1} vs {price2}"  # 差异不应超过10%
                print(f"   ✓ 技术指标数据一致性验证通过")
        
        print("   ✅ 数据一致性测试完成")


def run_market_tests():
    """运行所有市场测试的主函数"""
    print("🚀 开始运行 market.ipynb 测试程序")
    print("=" * 80)
    
    # 环境设置检查
    print("🔧 环境设置检查...")
    print(f"   Python路径: {XYSTOCK_DIR}")
    print(f"   当前目录: {CURRENT_DIR}")
    
    # 导入检查
    try:
        from providers.market_tools import get_market_tools
        print("   ✓ 大盘分析模块导入成功")
    except ImportError as e:
        print(f"   ❌ 模块导入失败: {e}")
        return False
    
    print("   ✓ 环境设置完成")
    print("=" * 80)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestMarketIndicators))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout, buffer=False)
    result = runner.run(suite)
    
    print("=" * 80)
    if result.wasSuccessful():
        print("✅ 所有测试通过!")
        print(f"✓ 运行了 {result.testsRun} 个测试")
    else:
        print(f"❌ 测试失败!")
        print(f"✓ 运行了 {result.testsRun} 个测试")
        print(f"❌ 失败: {len(result.failures)} 个")
        print(f"❌ 错误: {len(result.errors)} 个")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    """直接运行时的入口点"""
    success = run_market_tests()
    sys.exit(0 if success else 1)
