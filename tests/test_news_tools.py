"""
新闻功能测试模块

测试股票新闻、公告、研究报告等信息的获取和分析功能。

重构后的测试架构：
1. FinGenius WebSearch 数据源测试 (搜索引擎)
2. akshare 东财数据源测试 (官方数据)
3. 综合功能测试
"""

import pytest
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from providers.news_tools import (
    get_stock_info_by_akshare,
    display_stock_by_ak_summary,
    search_stock_news_by_fg_smart
)


class TestNewsTools:
    """新闻工具测试类"""
    
    @pytest.fixture
    def test_stock_a(self):
        """A股测试股票"""
        return {
            'code': '000001',
            'name': '平安银行'
        }
    
    @pytest.fixture
    def test_stock_us(self):
        """美股测试股票"""
        return {
            'code': 'AAPL',
            'name': 'Apple'
        }
    
    def test_akshare_stock_info(self, test_stock_a):
        """测试akshare股票信息获取"""
        stock_code = test_stock_a['code']
        
        stock_data = get_stock_info_by_akshare(stock_code)
        
        assert isinstance(stock_data, dict)
        assert 'company_news' in stock_data
        assert 'announcements' in stock_data
        assert 'research_reports' in stock_data
        assert 'news_summary' in stock_data
        
        # 检查摘要信息
        summary = stock_data['news_summary']
        assert 'total_news_count' in summary
        assert 'company_news_count' in summary
        assert 'announcements_count' in summary
        assert 'research_reports_count' in summary
        assert 'data_freshness' in summary
        
        # 验证数据一致性
        total_calculated = (summary['company_news_count'] + 
                          summary['announcements_count'] + 
                          summary['research_reports_count'])
        assert summary['total_news_count'] == total_calculated
    
    def test_display_stock_summary(self, test_stock_a, capsys):
        """测试股票信息摘要显示"""
        stock_code = test_stock_a['code']
        
        stock_data = get_stock_info_by_akshare(stock_code)
        
        # 调用显示函数
        display_stock_by_ak_summary(stock_data)
        
        # 检查输出
        captured = capsys.readouterr()
        assert "股票信息摘要报告" in captured.out
        assert "数据概览" in captured.out
        assert stock_data['news_summary']['total_news_count'] > 0 or "0 条" in captured.out
    
    def test_fingenius_search_chinese(self, test_stock_a):
        """测试FinGenius中文搜索"""
        stock_name = test_stock_a['name']
        stock_code = test_stock_a['code']
        
        result = search_stock_news_by_fg_smart(
            stock_name=stock_name,
            stock_code=stock_code,
            num_results=3,
            search_type="chinese"
        )
        
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'used_version' in result
        
        if result['success']:
            assert 'total_results' in result
            assert 'results' in result
            assert 'query' in result
            assert isinstance(result['results'], list)
            
            # 检查结果格式
            if result['results']:
                first_result = result['results'][0]
                assert 'title' in first_result
                assert 'url' in first_result
                assert 'source' in first_result
    
    def test_fingenius_search_english(self, test_stock_us):
        """测试FinGenius英文搜索"""
        stock_name = test_stock_us['name']
        stock_code = test_stock_us['code']
        
        result = search_stock_news_by_fg_smart(
            stock_name=stock_name,
            stock_code=stock_code,
            num_results=3,
            search_type="english"
        )
        
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'used_version' in result
        
        if result['success']:
            assert 'total_results' in result
            assert 'results' in result
            assert 'query' in result
    
    def test_news_data_consistency(self, test_stock_a):
        """测试新闻数据一致性"""
        stock_code = test_stock_a['code']
        
        # 获取akshare股票信息
        stock_data = get_stock_info_by_akshare(stock_code)
        
        # 数据应该是字典格式
        assert isinstance(stock_data, dict)
        
        # 应该有有效的摘要信息
        assert stock_data['news_summary']['total_news_count'] >= 0
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效股票代码
        invalid_code = "INVALID999"
        
        # akshare股票信息
        stock_data = get_stock_info_by_akshare(invalid_code)
        assert isinstance(stock_data, dict)
        assert 'news_summary' in stock_data
        
        # FinGenius搜索
        search_result = search_stock_news_by_fg_smart(
            stock_name="无效股票",
            stock_code=invalid_code,
            num_results=1
        )
        assert isinstance(search_result, dict)
        assert 'success' in search_result


class TestComprehensiveNews:
    """综合新闻功能测试"""
    
    @pytest.fixture
    def test_stocks(self):
        """测试股票列表"""
        return [
            {'code': '000001', 'name': '平安银行'},
            {'code': '000002', 'name': '万科A'},
            {'code': '600036', 'name': '招商银行'}
        ]
    
    def test_multiple_stocks_news(self, test_stocks):
        """测试多个股票的新闻获取"""
        results = {}
        
        for stock in test_stocks[:2]:  # 只测试前2个，避免测试时间过长
            stock_code = stock['code']
            stock_name = stock['name']
            
            # 获取股票信息
            stock_data = get_stock_info_by_akshare(stock_code)
            
            results[stock_code] = {
                'stock_data': stock_data
            }
            
            # 基本验证
            assert isinstance(stock_data, dict)
        
        # 确保处理了预期数量的股票
        assert len(results) == 2
    
    def test_news_search_fallback(self):
        """测试新闻搜索的fallback机制"""
        # 测试智能搜索的版本fallback
        result = search_stock_news_by_fg_smart(
            stock_name="测试股票",
            stock_code="TEST001",
            num_results=1,
            search_type="chinese"
        )
        
        # 应该返回结果，即使失败也应该有明确的错误信息
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'used_version' in result
        
        # 版本信息应该是已知的值之一
        valid_versions = ['async', 'sync', 'sync_failed', 'all_failed']
        assert result['used_version'] in valid_versions


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
