"""
新闻工具模块

提供股票新闻、公告、研究报告等信息的获取和分析功能。

设计架构：
akshare 东财数据源 - 来自东方财富（新闻/公告/研报）
   └── get_stock_news_by_akshare() - 获取股票完整信息

主要功能：
- 股票新闻、公告、研究报告获取
- 多搜索引擎新闻搜索
- 数据分析和展示功能
"""

import akshare as ak
from datetime import datetime
from collections import Counter


def get_stock_news_by_akshare(stock_code, day = 7, debug=False):
    """
    使用akshare获取股票新闻、公告、研究报告（东财数据源）
    
    Args:
        stock_code: 股票代码，如 "000001", "600036"
    
    Returns:
        dict: 包含所有信息的字典
    """
    print(f"📊 获取股票 {stock_code} 的详细信息...")
    
    # 初始化结果字典
    result = {
        'company_news': [],
        'announcements': [],
        'research_reports': [],
        'news_summary': {}
    }
    
    # 获取公司新闻
    try:
        print("   获取公司新闻...")
        company_news = ak.stock_news_em(stock_code)
        if not company_news.empty:
            company_news = company_news.to_dict('records')
            company_news = sorted(company_news, 
                           key=lambda x: datetime.strptime(x.get('发布时间', '1900-01-01 00:00:00'), '%Y-%m-%d %H:%M:%S'), 
                           reverse=True)
            # 对新闻做时间过滤，过滤掉当前日期之前day天的数据，且最多保留20条
            if day > 0:
                from datetime import timedelta
                cutoff_date = datetime.now() - timedelta(days=day)
                company_news = [news for news in company_news if datetime.strptime(news.get('发布时间', '1900-01-01 00:00:00'), '%Y-%m-%d %H:%M:%S') >= cutoff_date]
            company_news = company_news[:20]
            result['company_news'] = company_news
        print(f"   ✓ 成功获取 {len(result['company_news'])} 条公司新闻")

        if debug:
            print(f"✓ 新闻已按发布时间排序，共 {len(result)} 条")

    except Exception as e:
        print(f"   ⚠️ 获取公司新闻失败: {e}")
    
    """
    # 获取公司公告
    try:
        print("   获取公司公告...")
        announcements = ak.stock_notice_report(stock_code) # 这个参数应该是代码，且只能取某一天的，返回的是当天所有公司的公告
        if not announcements.empty:
            result['announcements'] = announcements.to_dict('records')
        print(f"   ✓ 成功获取 {len(result['announcements'])} 条公告")
    except Exception as e:
        print(f"   ⚠️ 获取公司公告失败: {e}")
    
    
    # 获取研究报告
    try:
        print("   获取研究报告...")
        # 使用不同的akshare函数尝试获取研究报告
        try:
            research_reports = ak.stock_research_report_em(stock_code)
            if not research_reports.empty:
                result['research_reports'] = research_reports.to_dict('records')
        except:
            # 如果第一个函数失败，尝试备用函数
            research_reports = ak.stock_analyst_rank_em(stock_code)
            if not research_reports.empty:
                result['research_reports'] = research_reports.to_dict('records')
        
        print(f"   ✓ 成功获取 {len(result['research_reports'])} 条研究报告")
    except Exception as e:
        print(f"   ⚠️ 获取研究报告失败: {e}")
    """
    # 生成摘要信息
    result['news_summary'] = {
        'total_news_count': len(result['company_news']) + len(result['announcements']) + len(result['research_reports']),
        'company_news_count': len(result['company_news']),
        'announcements_count': len(result['announcements']),
        'research_reports_count': len(result['research_reports']),
        'data_freshness': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'stock_code': stock_code
    }
    
    print(f"   ✅ 股票信息获取完成，共 {result['news_summary']['total_news_count']} 条信息")
    return result


def show_stock_by_ak_summary(stock_info):
    """
    美化显示股票信息摘要
    
    Args:
        stock_info: get_stock_news_by_akshare返回的股票信息字典
    """
    print(f"📈 股票信息摘要报告")
    print("=" * 60)
    
    summary = stock_info['news_summary']
    stock_code = summary['stock_code']
    
    print(f"🎯 股票代码: {stock_code}")
    print(f"📅 数据更新时间: {summary['data_freshness']}")
    
    print(f"\n📊 数据概览:")
    print(f"   📰 公司新闻: {summary['company_news_count']} 条")
    print(f"   📋 公司公告: {summary['announcements_count']} 条")
    print(f"   📄 研究报告: {summary['research_reports_count']} 条")
    print(f"   📈 总计: {summary['total_news_count']} 条")
    
    # 显示最新新闻标题
    if stock_info['company_news']:
        print(f"\n📰 最新公司新闻（前5条）:")
        for i, news in enumerate(stock_info['company_news'][:5], 1):
            title = news.get('新闻标题', news.get('title', '无标题'))
            time = news.get('发布时间', news.get('publish_time', '无时间'))
            print(f"   {i}. {title}")
            print(f"      时间: {time}")
    
    # 显示最新公告标题
    if stock_info['announcements']:
        print(f"\n📋 最新公司公告（前3条）:")
        for i, announcement in enumerate(stock_info['announcements'][:3], 1):
            # 公告的列名可能不同，尝试多种可能的列名
            title = (announcement.get('公告标题') or 
                    announcement.get('标题') or 
                    announcement.get('title') or 
                    '无标题')
            time = (announcement.get('公告日期') or 
                   announcement.get('发布时间') or 
                   announcement.get('日期') or 
                   '无时间')
            print(f"   {i}. {title}")
            print(f"      时间: {time}")
    
    # 显示研究报告评级分布
    if stock_info['research_reports']:
        print(f"\n⭐ 研究报告评级分布:")
        # 尝试提取评级信息
        ratings = []
        for report in stock_info['research_reports']:
            rating = (report.get('投资评级') or 
                     report.get('评级') or 
                     report.get('rating') or 
                     report.get('最新评级'))
            if rating and rating != 'nan':
                ratings.append(rating)
        
        if ratings:
            rating_count = Counter(ratings)
            for rating, count in rating_count.most_common():
                print(f"   • {rating}: {count} 个机构")
        else:
            print("   暂无评级信息")

import json
from llm import openai_client

# 情绪分析提示词模板
SENTIMENT_ANALYSIS_PROMPT_TEMPLATE = """请分析以下新闻对股票"{stock_name}"的投资情绪影响：

新闻标题: {news_title}
新闻内容: {news_content}

请从该股票投资者的角度分析这条新闻的三项指标：
- 情绪类别：乐观、中性、悲观
- 情绪强度：1-5（1=轻微影响，5=重大影响）
- 预期偏离度：1-5（1=符合预期，5=非常出乎意料）

返回JSON格式：{return_format}"""

def filter_time(news, start_date, end_date):
    # 时间过滤
    filtered_news = []
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    for news in news:
        publish_time_str = news.get('发布时间', '')
        if publish_time_str:
            news_date_str = publish_time_str.split(' ')[0]
            news_dt = datetime.strptime(news_date_str, '%Y-%m-%d')
            if start_dt <= news_dt <= end_dt:
                filtered_news.append(news)
    return filtered_news

def analyze_news_sentiment(news_base, stock_name, start_date=None, end_date=None, limit=-1, debug=False):
    client = openai_client.OpenAIClient()
    ret_array = []

    if start_date is not None and end_date is not None:
        news = filter_time(news_base, start_date, end_date)
        if debug:
            print(f"✓ 新闻已按时间范围过滤，{len(news_base)} -> {len(news)} 条")
    
    for idx, item in enumerate(news):
        if '新闻标题' not in item or '新闻内容' not in item:
            print("新闻数据不完整，跳过该条新闻")
            continue
        
        return_format = "{'sentiment':'xx', 'intensity': 5, 'deviation': 3}"
        
        # 使用提示词模板
        query = SENTIMENT_ANALYSIS_PROMPT_TEMPLATE.format(
            stock_name=stock_name,
            news_title=item['新闻标题'],
            news_content=item['新闻内容'],
            return_format=return_format
        )
        
        try:
            # 使用JSON模式
            ai_result = client.ask(query, json_mode=True, debug=debug)
            if debug:
                print(f"新闻标题: {item['新闻标题']}")
                print(f"新闻内容: {item['新闻内容']}")
                print(f"\nJSON模式返回: {ai_result}")
            
            # 直接解析JSON，不需要额外的字符串处理
            sentiment_data = json.loads(ai_result)
            item['情绪类型'] = sentiment_data.get('sentiment', '中性')
            item['情绪级别'] = sentiment_data.get('intensity', 3)
            item['预期偏离度'] = sentiment_data.get('deviation', 3)
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            print(f"返回内容: {ai_result}")
        except Exception as e:
            print(f"其他错误: {e}")
        if limit != -1 and idx >= limit:
            break
        ret_array.append(item)

    return ret_array

