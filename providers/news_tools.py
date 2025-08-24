"""
新闻工具模块

提供股票新闻、公告、研究报告等信息的获取和分析功能。

设计架构：
1. FinGenius WebSearch 数据源 - 来自搜索引擎（百度/Google/Bing/DuckDuckGo）
   └── search_stock_news_by_fg_smart() - 智能搜索股票新闻
2. akshare 东财数据源 - 来自东方财富（新闻/公告/研报）
   └── get_stock_news_by_akshare() - 获取股票完整信息

主要功能：
- 股票新闻、公告、研究报告获取
- 多搜索引擎新闻搜索
- 数据分析和展示功能
"""

import akshare as ak
from datetime import datetime
import re
from collections import Counter
import asyncio
import sys


def run_async_in_notebook(coro):
    """
    在Jupyter notebook环境中安全运行异步函数的辅助函数
    
    Args:
        coro: 协程对象
    
    Returns:
        异步函数的结果
    """
    try:
        # 检查是否在Jupyter环境中
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果已有运行的事件循环，尝试使用nest_asyncio
            try:
                import nest_asyncio
                nest_asyncio.apply()
                return asyncio.run(coro)
            except ImportError:
                # 如果没有nest_asyncio，提供替代方案
                print("⚠️ 建议安装 nest_asyncio: pip install nest_asyncio")
                print("   当前使用备用方案...")
                # 创建任务并在当前循环中运行
                task = asyncio.create_task(coro)
                return loop.run_until_complete(task)
        else:
            # 没有运行的事件循环，正常使用asyncio.run
            return asyncio.run(coro)
    except RuntimeError:
        # 如果没有事件循环，创建一个新的
        return asyncio.run(coro)


class FinGeniusWebSearch:
    """
    FinGenius Web搜索工具封装类
    """
    def __init__(self):
        self.web_search = None
        self._setup_fingenius_path()
        self._initialize_web_search()
    
    def _setup_fingenius_path(self):
        """设置FinGenius项目路径"""
        fingenius_dir = "/exports/stock/git/FinGenius"
        if fingenius_dir not in sys.path:
            sys.path.insert(0, fingenius_dir)
    
    def _initialize_web_search(self):
        """初始化WebSearch工具"""
        try:
            FINGENIUS_DIR = "/exports/stock/git/FinGenius"
            if FINGENIUS_DIR not in sys.path:
                sys.path.insert(0, FINGENIUS_DIR)            
            from src.tool.web_search import WebSearch
            self.web_search = WebSearch()
            print("✓ FinGenius WebSearch工具初始化成功")
        except ImportError as e:
            print(f"❌ 导入FinGenius WebSearch失败: {e}")
            self.web_search = None
        except Exception as e:
            print(f"❌ 创建WebSearch实例失败: {e}")
            self.web_search = None
    
    async def search_news(self, query, num_results=5, lang="zh", country="cn", fetch_content=False):
        """
        搜索新闻
        
        Args:
            query: 搜索关键词
            num_results: 返回结果数量
            lang: 语言 ("zh" 或 "en")
            country: 国家代码 ("cn", "us" 等)
            fetch_content: 是否获取详细内容
        
        Returns:
            搜索结果对象
        """
        if not self.web_search:
            print("❌ WebSearch工具未初始化")
            return None
        
        try:
            result = await self.web_search.execute(
                query=query,
                num_results=num_results,
                lang=lang,
                country=country,
                fetch_content=fetch_content
            )
            return result
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return None
    
    def is_available(self):
        """检查工具是否可用"""
        return self.web_search is not None


def search_stock_news_web(stock_name, stock_code=None, num_results=5, search_type="chinese"):
    """
    使用FinGenius web_search搜索股票相关新闻
    
    Args:
        stock_name: 股票名称，如 "招商银行", "Apple"
        stock_code: 股票代码，如 "600036", "AAPL"（可选）
        num_results: 返回结果数量
        search_type: 搜索类型 ("chinese" 或 "english")
    
    Returns:
        dict: 包含搜索结果的字典
    """
    print(f"🔍 使用FinGenius web_search搜索股票新闻: {stock_name}")
    
    # 初始化搜索工具
    search_tool = FinGeniusWebSearch()
    
    if not search_tool.is_available():
        print("❌ FinGenius WebSearch工具不可用")
        return {
            'success': False,
            'error': 'WebSearch工具不可用',
            'results': []
        }
    
    # 构建搜索查询
    if search_type == "chinese":
        if stock_code:
            query = f"{stock_name} {stock_code} 最新新闻 股票"
        else:
            query = f"{stock_name} 最新新闻 股票"
        lang = "zh"
        country = "cn"
    else:
        if stock_code:
            query = f"{stock_name} {stock_code} latest news stock"
        else:
            query = f"{stock_name} latest news stock"
        lang = "en"
        country = "us"
    
    try:
        # 运行异步搜索 - 使用辅助函数处理Jupyter环境兼容性
        result = run_async_in_notebook(search_tool.search_news(
            query=query,
            num_results=num_results,
            lang=lang,
            country=country,
            fetch_content=False
        ))
        
        if result and hasattr(result, 'results'):
            processed_results = []
            for item in result.results:
                processed_item = {
                    'title': item.title,
                    'url': item.url,
                    'description': getattr(item, 'description', ''),
                    'source': getattr(item, 'source', ''),
                    'position': getattr(item, 'position', 0),
                    'relevance_score': 0.8  # 默认相关性评分
                }
                processed_results.append(processed_item)
            
            return {
                'success': True,
                'query': query,
                'total_results': len(processed_results),
                'results': processed_results,
                'metadata': {
                    'language': lang,
                    'country': country,
                    'search_engine': 'FinGenius WebSearch'
                }
            }
        else:
            return {
                'success': False,
                'error': '未找到搜索结果',
                'results': []
            }
            
    except Exception as e:
        print(f"❌ 搜索过程中发生错误: {e}")
        return {
            'success': False,
            'error': str(e),
            'results': []
        }


def search_stock_news_web_sync(stock_name, stock_code=None, num_results=5, search_type="chinese"):
    """
    使用FinGenius web_search搜索股票相关新闻（同步版本，避免异步问题）
    
    Args:
        stock_name: 股票名称，如 "招商银行", "Apple"
        stock_code: 股票代码，如 "600036", "AAPL"（可选）
        num_results: 返回结果数量
        search_type: 搜索类型 ("chinese" 或 "english")
    
    Returns:
        dict: 包含搜索结果的字典
    """
    print(f"🔍 使用FinGenius web_search搜索股票新闻（同步版本）: {stock_name}")
    
    # 初始化搜索工具
    search_tool = FinGeniusWebSearch()
    
    if not search_tool.is_available():
        print("❌ FinGenius WebSearch工具不可用")
        return {
            'success': False,
            'error': 'WebSearch工具不可用',
            'results': []
        }
    
    # 构建搜索查询
    if search_type == "chinese":
        if stock_code:
            query = f"{stock_name} {stock_code} 最新新闻 股票"
        else:
            query = f"{stock_name} 最新新闻 股票"
        lang = "zh"
        country = "cn"
    else:
        if stock_code:
            query = f"{stock_name} {stock_code} latest news stock"
        else:
            query = f"{stock_name} latest news stock"
        lang = "en"
        country = "us"
    
    try:
        # 创建新的事件循环来运行异步函数
        import threading
        import queue
        
        result_queue = queue.Queue()
        exception_queue = queue.Queue()
        
        def run_search():
            try:
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(search_tool.search_news(
                    query=query,
                    num_results=num_results,
                    lang=lang,
                    country=country,
                    fetch_content=False
                ))
                
                result_queue.put(result)
                loop.close()
            except Exception as e:
                exception_queue.put(e)
        
        search_thread = threading.Thread(target=run_search)
        search_thread.start()
        search_thread.join(timeout=30)  # 30秒超时
        
        if not exception_queue.empty():
            raise exception_queue.get()
        
        if result_queue.empty():
            raise TimeoutError("搜索超时")
        
        result = result_queue.get()
        
        if result and hasattr(result, 'results'):
            processed_results = []
            for item in result.results:
                processed_item = {
                    'title': item.title,
                    'url': item.url,
                    'description': getattr(item, 'description', ''),
                    'source': getattr(item, 'source', ''),
                    'position': getattr(item, 'position', 0),
                    'relevance_score': 0.8  # 默认相关性评分
                }
                processed_results.append(processed_item)
            
            return {
                'success': True,
                'query': query,
                'total_results': len(processed_results),
                'results': processed_results,
                'metadata': {
                    'language': lang,
                    'country': country,
                    'search_engine': 'FinGenius WebSearch (同步版本)'
                }
            }
        else:
            return {
                'success': False,
                'error': '未找到搜索结果',
                'results': []
            }
            
    except Exception as e:
        print(f"❌ 搜索过程中发生错误: {e}")
        return {
            'success': False,
            'error': str(e),
            'results': []
        }


def search_stock_news_by_fg_smart(stock_name, stock_code=None, num_results=5, search_type="chinese"):
    """
    智能搜索股票新闻 - 自动处理异步问题
    
    先尝试异步版本，如果失败则自动切换到同步版本
    
    Args:
        stock_name: 股票名称，如 "招商银行", "Apple"
        stock_code: 股票代码，如 "600036", "AAPL"（可选）
        num_results: 返回结果数量
        search_type: 搜索类型 ("chinese" 或 "english")
    
    Returns:
        dict: 包含搜索结果的字典，包含使用的版本信息
    """
    print(f"🧠 智能搜索股票新闻: {stock_name}")
    
    try:
        # 首先尝试异步版本
        print("   尝试异步版本...")
        result = search_stock_news_web(stock_name, stock_code, num_results, search_type)
        
        if result['success']:
            result['used_version'] = 'async'
            print("   ✅ 异步版本成功")
            return result
        else:
            print(f"   ⚠️ 异步版本失败: {result['error']}")
            raise Exception("异步版本失败")
            
    except Exception as e:
        print(f"   🔧 切换到同步版本...")
        
        try:
            # 使用同步版本作为备选
            result = search_stock_news_web_sync(stock_name, stock_code, num_results, search_type)
            
            if result['success']:
                result['used_version'] = 'sync'
                print("   ✅ 同步版本成功")
                return result
            else:
                result['used_version'] = 'sync_failed'
                print(f"   ❌ 同步版本也失败: {result['error']}")
                return result
                
        except Exception as sync_e:
            print(f"   ❌ 同步版本异常: {sync_e}")
            return {
                'success': False,
                'error': f'所有版本都失败 - 异步: {str(e)[:100]}, 同步: {str(sync_e)[:100]}',
                'results': [],
                'used_version': 'all_failed'
            }


def get_stock_news_by_akshare(stock_code, debug=False):
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

