"""
新闻工具模块
"""

import akshare as ak
from datetime import datetime, timedelta
from collections import Counter
import json
from llm import openai_client


def get_stock_news_by_akshare(stock_code, day = 7, debug=False):
    """
    获取股票新闻、公告、研究报告（东财数据源）
    """
    print(f"📊 获取股票 {stock_code} 的详细信息...")
    result = {
        'company_news': [],
        'announcements': [], # 暂时取不到
        'research_reports': [],
        'news_summary': {}
    }
    try:
        print("   获取公司新闻...")
        company_news = ak.stock_news_em(stock_code)
        if not company_news.empty:
            company_news = company_news.to_dict('records')
            company_news = sorted(company_news, 
                           key=lambda x: datetime.strptime(x.get('发布时间', '1900-01-01 00:00:00'), '%Y-%m-%d %H:%M:%S'), 
                           reverse=True)
            # 时间过滤，保留最近day天的数据，最多20条
            if day > 0:
                cutoff_date = datetime.now() - timedelta(days=day)
                company_news = [news for news in company_news if datetime.strptime(news.get('发布时间', '1900-01-01 00:00:00'), '%Y-%m-%d %H:%M:%S') >= cutoff_date]
            company_news = company_news[:20]
            if debug: # 内容有时取的很短，查看获取情况
                for news in company_news:
                    if '新闻内容' not in news or not news['新闻内容']:
                        news['新闻内容'] = "无内容"
                    else:
                        print(f"   ✓ 成功获取新闻内容: {news['新闻内容']}, len={len(news['新闻内容'])}")
            result['company_news'] = company_news
        print(f"   ✓ 成功获取 {len(result['company_news'])} 条公司新闻")
        if debug:
            print(f"✓ 新闻已按发布时间排序，共 {len(result)} 条")
    except Exception as e:
        print(f"   ⚠️ 获取公司新闻失败: {e}")
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
    if stock_info['company_news']:
        print(f"\n📰 最新公司新闻（前5条）:")
        for i, news in enumerate(stock_info['company_news'][:5], 1):
            title = news.get('新闻标题', news.get('title', '无标题'))
            time = news.get('发布时间', news.get('publish_time', '无时间'))
            print(f"   {i}. {title}")
            print(f"      时间: {time}")
    if stock_info['announcements']:
        print(f"\n📋 最新公司公告（前3条）:")
        for i, announcement in enumerate(stock_info['announcements'][:3], 1):
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
    if stock_info['research_reports']:
        print(f"\n⭐ 研究报告评级分布:")
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


SENTIMENT_ANALYSIS_PROMPT_TEMPLATE = """请分析以下新闻对股票"{stock_name}"的投资情绪影响：

新闻标题: {news_title}
新闻内容: {news_content}

请从该股票投资者的角度分析这条新闻的三项指标：
- 情绪类别：乐观、中性、悲观
- 情绪强度：1-5（1=轻微影响，5=重大影响）
- 预期偏离度：1-5（1=符合预期，5=非常出乎意料）

返回JSON格式：{return_format}"""

def filter_time(news, start_date, end_date):
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
    """
    调用大模型分析新闻情绪
    """
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


def get_market_news_caixin(limit=20, debug=False):
    """
    获取财新网宏观经济和市场新闻（政策面、大盘相关）
    """
    print("📊 获取财新网宏观经济新闻...")
    result = {
        'market_news': [],
        'news_summary': {}
    }
    
    try:
        # 获取财新网数据
        caixin_data = ak.stock_news_main_cx()
        
        if not caixin_data.empty:
            market_news = caixin_data.to_dict('records')
            
            # 过滤出有实际内容的新闻（有summary和url的）
            filtered_news = []
            for news in market_news:
                if news.get('summary') and news.get('url') and str(news.get('summary')).strip():
                    # 统一字段名称以便后续处理
                    formatted_news = {
                        '新闻标题': news.get('tag', '无标题'),
                        '新闻内容': news.get('summary', '无内容'),
                        '发布时间': news.get('pub_time', '无时间'),
                        '相对时间': news.get('interval_time', ''),
                        '新闻链接': news.get('url', ''),
                        '新闻类型': '宏观经济'
                    }
                    filtered_news.append(formatted_news)
            
            # 按发布时间排序（最新的在前面）
            try:
                filtered_news = sorted(filtered_news, 
                                     key=lambda x: datetime.strptime(x.get('发布时间', '1900-01-01 00:00:00.000').split('.')[0], '%Y-%m-%d %H:%M:%S'), 
                                     reverse=True)
            except:
                # 如果时间格式解析失败，保持原有顺序
                pass
            
            result['market_news'] = filtered_news[:limit]
            
            if debug:
                print(f"   ✓ 成功获取 {len(result['market_news'])} 条宏观新闻")
                for i, news in enumerate(result['market_news'][:3]):
                    print(f"   {i+1}. {news['新闻标题']}")
                    print(f"      时间: {news['发布时间']} ({news['相对时间']})")
                    print(f"      内容: {news['新闻内容'][:100]}...")
                    print()
        
        result['news_summary'] = {
            'total_market_news_count': len(result['market_news']),
            'data_source': '财新网',
            'data_freshness': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'news_type': '宏观经济、政策面、大盘相关'
        }
        
        print(f"   ✅ 财新网新闻获取完成，共 {result['news_summary']['total_market_news_count']} 条信息")
        
    except Exception as e:
        print(f"   ⚠️ 获取财新网新闻失败: {e}")
    
    return result

