"""
缓存管理页面组件
"""

import streamlit as st
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)


def main():
    """缓存管理主页面"""
    st.header("🗂️ 缓存管理")
    st.markdown("管理系统中的各类数据缓存，清理后下次查询会重新获取最新数据。")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 股票数据缓存")
        st.markdown("清理股票基本信息、技术指标、新闻、AI分析等数据缓存。")
        
        if st.button("🗑️ 清理股票数据缓存", 
                    type="primary", 
                    width='stretch',
                    help="清理所有股票相关的数据缓存"):
            try:
                from stock.stock_data_tools import clear_stock_cache
                clear_stock_cache()
                st.success("✅ 股票数据缓存已清理完成！")
            except Exception as e:
                st.error(f"❌ 清理股票缓存失败：{str(e)}")
    
    with col2:
        st.subheader("📊 大盘数据缓存")
        st.markdown("清理市场情绪、估值指标、资金流向等大盘数据缓存。")
        
        if st.button("🗑️ 清理大盘数据缓存", 
                    type="primary", 
                    width='stretch',
                    help="清理所有大盘相关的数据缓存"):
            try:
                from market.market_data_tools import get_market_tools
                market_tools = get_market_tools()
                market_tools.clear_cache()
                st.success("✅ 大盘数据缓存已清理完成！")
            except Exception as e:
                st.error(f"❌ 清理大盘缓存失败：{str(e)}")
    
    st.markdown("---")
    
    st.subheader("🧹 批量操作")
    
    col3, col4 = st.columns([1, 3])
    
    with col3:
        # 使用session_state实现确认弹窗
        if st.button("🗑️ 清理所有缓存", 
                    type="secondary", 
                    width='stretch',
                    help="一键清理所有股票和大盘数据缓存"):
            st.session_state['show_clear_all_confirm'] = True

        if st.session_state.get('show_clear_all_confirm', False):
            st.warning(
                "⚠️ 此操作将**删除所有缓存，包括股票名映射、K线缓存等**，后续拉取数据会变慢，请谨慎操作！",
                icon="⚠️"
            )
            if st.button("确认清理", key="confirm_clear_all_cache"):
                try:
                    # 清理所有相关缓存
                    from stock.stock_data_tools import clear_stock_cache, clear_chip_cache
                    clear_stock_cache()
                    clear_chip_cache()  # 清理筹码缓存
                    
                    from market.market_data_tools import get_market_tools
                    market_tools = get_market_tools()
                    market_tools.clear_cache()

                    from utils.kline_cache import cache_manager
                    cache_manager.clear_cache()

                    from stock.stock_code_map import clear_stock_map_cache, clear_hk_stock_map_cache
                    clear_stock_map_cache()
                    clear_hk_stock_map_cache()

                    # 删除data/cache目录下所有txt文件
                    import glob
                    from pathlib import Path
                    cache_dir = os.path.join(Path(__file__).parent.parent.parent, 'data', 'cache')
                    for txt_file in glob.glob(os.path.join(cache_dir, '*.txt')):
                        print("清除文本文件：", txt_file)
                        try:
                            os.remove(txt_file)
                        except Exception as e:
                            print(f"删除文件失败: {txt_file} {e}")

                    st.success("✅ 所有缓存已清理完成！")
                except Exception as e:
                    st.error(f"❌ 清理所有缓存失败：{str(e)}")
                st.session_state['show_clear_all_confirm'] = False
            if st.button("取消", key="cancel_clear_all_cache"):
                st.session_state['show_clear_all_confirm'] = False
    
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
