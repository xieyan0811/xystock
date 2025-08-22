"""
API使用量统计页面 - 显示OpenAI API的使用情况和成本统计
"""

import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import altair as alt
import numpy as np

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

# 导入相关模块
from llm.usage_logger import UsageLogger

# 配置UsageLogger
usage_logger = UsageLogger()

def format_cost(cost):
    """格式化成本显示"""
    if cost >= 1:
        return f"${cost:.2f}"
    else:
        return f"${cost:.4f}"

def show_usage_overview(days=30):
    """显示使用概览"""
    st.header("API使用概览")

    # 获取使用统计
    stats = usage_logger.get_usage_stats(days=days)
    
    if not stats:
        st.warning("暂无使用数据")
        return
    
    # 显示关键指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总请求数", f"{stats.get('total_requests', 0)}")
    
    with col2:
        st.metric("总Token数", f"{stats.get('total_tokens', 0):,}")
    
    with col3:
        total_cost = stats.get('total_cost', 0)
        st.metric("总成本", format_cost(total_cost))
    
    with col4:
        avg_response_time = stats.get('avg_response_time', 0)
        st.metric("平均响应时间", f"{avg_response_time:.2f}秒")
    
    # 成功率指标
    success_rate = stats.get('success_rate', 0) * 100
    st.progress(success_rate / 100, text=f"成功率: {success_rate:.1f}%")

def show_model_distribution(days=30):
    """显示模型使用分布"""
    # 获取使用统计
    stats = usage_logger.get_usage_stats(days=days)
    
    if not stats or 'model_distribution' not in stats or not stats['model_distribution']:
        st.warning("暂无模型分布数据")
        return
    
    st.subheader("模型使用分布")
    
    model_dist = stats['model_distribution']
    models = list(model_dist.keys())
    counts = list(model_dist.values())
    
    # 创建模型分布图表
    model_df = pd.DataFrame({
        'model': models,
        'count': counts
    })
    
    # 使用Altair创建条形图
    chart = alt.Chart(model_df).mark_bar().encode(
        x=alt.X('model', sort='-y', title='模型'),
        y=alt.Y('count', title='使用次数'),
        color=alt.Color('model', legend=None)
    ).properties(height=300)
    
    st.altair_chart(chart, use_container_width=True)
    
    # 展示模型使用数据表格
    with st.expander("模型使用详细数据", expanded=False):
        st.dataframe(model_df, use_container_width=True)

def show_daily_usage(days=30):
    """显示每日使用情况"""
    # 获取使用统计
    stats = usage_logger.get_usage_stats(days=days)
    
    if not stats or 'daily_usage' not in stats or not stats['daily_usage']:
        st.warning("暂无每日使用数据")
        return
    
    st.subheader("每日Token使用量")
    
    daily_usage = stats['daily_usage']
    dates = [str(date) for date in daily_usage.keys()]
    tokens = list(daily_usage.values())
    
    # 创建每日使用量图表
    daily_df = pd.DataFrame({
        'date': dates,
        'tokens': tokens
    })
    daily_df['date'] = pd.to_datetime(daily_df['date'])
    daily_df = daily_df.sort_values('date')
    
    # 使用折线图显示使用趋势
    chart = alt.Chart(daily_df).mark_line(point=True).encode(
        x=alt.X('date:T', title='日期'),
        y=alt.Y('tokens:Q', title='Token数量'),
        tooltip=['date:T', 'tokens:Q']
    ).properties(height=300)
    
    st.altair_chart(chart, use_container_width=True)

def show_detailed_logs():
    """显示详细日志"""
    st.subheader("详细使用记录")
    
    # 尝试读取CSV文件
    try:
        df = pd.read_csv(usage_logger.log_file)
        
        if df.empty:
            st.warning("暂无使用记录")
            return
        
        # 处理时间戳
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp', ascending=False)
        
        # 简化输入和输出文本显示
        df['input_preview'] = df['input_text'].str[:50] + '...'
        df['output_preview'] = df['output_text'].str[:50] + '...'
        
        # 显示表格
        display_cols = [
            'timestamp', 'model', 'prompt_tokens', 
            'completion_tokens', 'total_tokens', 
            'cost_estimate', 'response_time', 'success'
        ]
        
        st.dataframe(
            df[display_cols],
            use_container_width=True,
            column_config={
                'timestamp': st.column_config.DatetimeColumn('时间'),
                'model': st.column_config.TextColumn('模型'),
                'prompt_tokens': st.column_config.NumberColumn('输入Token'),
                'completion_tokens': st.column_config.NumberColumn('输出Token'),
                'total_tokens': st.column_config.NumberColumn('总Token'),
                'cost_estimate': st.column_config.NumberColumn('成本($)', format="$%.4f"),
                'response_time': st.column_config.NumberColumn('响应时间(秒)'),
                'success': st.column_config.CheckboxColumn('成功')
            }
        )
        
        # 详细查看选项
        with st.expander("查看详细请求内容", expanded=False):
            # 选择一条记录查看详情
            record_idx = st.selectbox(
                "选择记录查看详情:", 
                range(len(df)),
                format_func=lambda i: f"{df.iloc[i]['timestamp']} - {df.iloc[i]['model']} (Tokens: {df.iloc[i]['total_tokens']})"
            )
            
            # 显示选中记录的详情
            record = df.iloc[record_idx]
            
            st.write("#### 请求详情")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**时间:**", record['timestamp'])
                st.write("**模型:**", record['model'])
                st.write("**输入Token:**", record['prompt_tokens'])
                st.write("**输出Token:**", record['completion_tokens'])
                st.write("**总Token:**", record['total_tokens'])
                
            with col2:
                st.write("**成本:**", format_cost(record['cost_estimate']))
                st.write("**响应时间:**", f"{record['response_time']:.2f}秒")
                st.write("**成功:**", "✅" if record['success'] else "❌")
                if not record['success'] and record['error_message']:
                    st.error(f"错误信息: {record['error_message']}")
                st.write("**温度参数:**", record['temperature'])
            
            # 显示输入和输出文本
            st.text_area("输入文本", record['input_text'], height=150)
            st.text_area("输出文本", record['output_text'], height=150)
        
    except Exception as e:
        st.error(f"加载详细日志失败: {str(e)}")

def export_usage_report():
    """导出使用报告"""
    st.subheader("导出报告")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        export_path = st.text_input(
            "导出路径:", 
            value="reports/usage_report.html",
            help="指定导出文件的路径"
        )
    
    with col2:
        st.write("")
        st.write("")
        export_btn = st.button("📊 导出报告", use_container_width=True)
    
    if export_btn:
        try:
            usage_logger.export_usage_report(export_path)
            st.success(f"报告已导出至: {export_path}")
        except Exception as e:
            st.error(f"导出报告失败: {str(e)}")

def main():
    """API使用统计页面主函数"""
    st.title("🔍 API使用统计")
    
    # 选择时间范围
    period_options = {
        "过去7天": 7,
        "过去30天": 30, 
        "过去90天": 90,
        "所有时间": 3650  # 约10年
    }
    
    selected_period = st.selectbox(
        "选择时间范围:",
        list(period_options.keys()),
        index=1,
        help="选择要分析的时间范围"
    )
    
    days = period_options[selected_period]
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📊 使用概览", "📈 使用趋势", "📝 详细记录", "💾 导出报告"])
    
    with tab1:
        show_usage_overview(days)
        show_model_distribution(days)
    
    with tab2:
        show_daily_usage(days)
    
    with tab3:
        show_detailed_logs()
    
    with tab4:
        export_usage_report()


if __name__ == "__main__":
    main()
