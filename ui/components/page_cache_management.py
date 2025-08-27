"""
缓存管理页面组件
"""

import streamlit as st
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)


def main():
    """缓存管理主页面"""
    st.header("🗂️ 缓存管理")
    st.markdown("管理系统中的各类数据缓存，清理后下次查询会重新获取最新数据。")
    
    # 创建两列布局
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 股票数据缓存")
        st.markdown("清理股票基本信息、技术指标、新闻、筹码、AI分析等数据缓存。")
        
        # 清理股票缓存按钮
        if st.button("🗑️ 清理股票数据缓存", 
                    type="primary", 
                    use_container_width=True,
                    help="清理所有股票相关的数据缓存"):
            try:
                from providers.stock_data_tools import clear_stock_cache
                clear_stock_cache()
                st.success("✅ 股票数据缓存已清理完成！")
            except Exception as e:
                st.error(f"❌ 清理股票缓存失败：{str(e)}")
    
    with col2:
        st.subheader("📊 大盘数据缓存")
        st.markdown("清理市场情绪、估值指标、资金流向等大盘数据缓存。")
        
        # 清理大盘缓存按钮
        if st.button("🗑️ 清理大盘数据缓存", 
                    type="primary", 
                    use_container_width=True,
                    help="清理所有大盘相关的数据缓存"):
            try:
                from providers.market_data_tools import get_market_tools
                market_tools = get_market_tools()
                market_tools.clear_cache()
                st.success("✅ 大盘数据缓存已清理完成！")
            except Exception as e:
                st.error(f"❌ 清理大盘缓存失败：{str(e)}")
    
    st.markdown("---")
    
    # 全部清理区域
    st.subheader("🧹 批量操作")
    
    col3, col4 = st.columns([1, 3])
    
    with col3:
        if st.button("🗑️ 清理所有缓存", 
                    type="secondary", 
                    use_container_width=True,
                    help="一键清理所有股票和大盘数据缓存"):
            try:
                # 清理股票缓存
                from providers.stock_data_tools import clear_stock_cache
                clear_stock_cache()
                
                # 清理大盘缓存
                from providers.market_data_tools import get_market_tools
                market_tools = get_market_tools()
                market_tools.clear_cache()
                
                st.success("✅ 所有缓存已清理完成！")
            except Exception as e:
                st.error(f"❌ 清理所有缓存失败：{str(e)}")
    
    # 缓存说明
    st.markdown("---")
    st.subheader("ℹ️ 缓存说明")
    
    st.markdown("""
    **股票数据缓存包括：**
    - 📋 基本信息：股票价格、涨跌幅等基础数据
    - 📈 技术指标：移动平均线、MACD、RSI等技术分析指标
    - 📰 新闻资讯：相关新闻和公告信息
    - 🧮 筹码分析：筹码分布和成本分析数据
    - 🤖 AI分析：各类AI分析报告
    
    **大盘数据缓存包括：**
    - 💭 市场情绪：情绪指标和市场热度
    - 💰 估值指标：市场整体估值水平
    - 💸 资金流向：资金进出和流向分析
    - 📊 融资融券：详细的融资融券数据
    - 🤖 AI分析：市场AI分析报告
    
    **注意事项：**
    - 清理缓存后，下次查询会重新获取最新数据
    - K线数据有独立的缓存机制，不会被此处清理影响
    - 过期的缓存数据会自动更新，无需手动清理
    """)


if __name__ == "__main__":
    main()
