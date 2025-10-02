"""
导出功能组件 - 专门用于实现各种报告的导出界面
"""

import streamlit as st
import datetime
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.report_utils import PDF_SUPPORT_AVAILABLE


def get_format_config():
    """获取导出格式配置信息"""
    support_pdf = PDF_SUPPORT_AVAILABLE
    
    if support_pdf:
        format_options = ["pdf", "docx", "markdown"]
        format_labels = {
            "pdf": "📄 PDF格式", 
            "docx": "📝 Word文档", 
            "markdown": "📝 Markdown"
        }
        format_descriptions = {
            "pdf": "专业格式，适合打印和正式分享",
            "docx": "Word文档，可编辑修改",
            "markdown": "Markdown格式，适合程序员和技术人员"
        }
    else:
        format_options = ["docx", "markdown", "html"]
        format_labels = {
            "docx": "📝 Word文档", 
            "markdown": "📝 Markdown", 
            "html": "🌐 HTML"
        }
        format_descriptions = {
            "docx": "Word文档，可编辑修改",
            "markdown": "Markdown格式，适合程序员和技术人员",
            "html": "HTML格式，适合网页浏览"
        }
    
    format_info = {
        "pdf": {"ext": "pdf", "mime": "application/pdf"},
        "docx": {"ext": "docx", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        "markdown": {"ext": "md", "mime": "text/markdown"},
        "html": {"ext": "html", "mime": "text/html"}
    }
    
    return format_options, format_labels, format_descriptions, format_info


def display_format_selector(entity_id, report_type="report"):
    """
    显示格式选择器组件
    
    Args:
        entity_id: 实体ID（股票代码或指数名称）
        report_type: 报告类型，用于区分不同类型的报告
    
    Returns:
        selected_format: 选择的格式
    """
    format_options, format_labels, format_descriptions, _ = get_format_config()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # 安全处理None值
        safe_report_type = str(report_type) if report_type is not None else "report"
        safe_entity_id = str(entity_id) if entity_id is not None else "unknown"
        
        format_type = st.selectbox(
            "选择导出格式",
            format_options,
            format_func=lambda x: format_labels[x],
            key=f"{safe_report_type}_format_select_{safe_entity_id}"
        )
    
    with col2:
        st.caption(format_descriptions[format_type])
    
    return format_type


def display_generate_button(entity_id, report_type="report", button_text="🔄 生成报告"):
    """
    显示生成报告按钮
    
    Args:
        entity_id: 实体ID（股票代码或指数名称）
        report_type: 报告类型
        button_text: 按钮文本
    
    Returns:
        bool: 是否点击了生成按钮
    """
    # 安全处理None值
    safe_report_type = str(report_type) if report_type is not None else "report"
    safe_entity_id = str(entity_id) if entity_id is not None else "unknown"
    
    button_key = f"generate_{safe_report_type}_{safe_entity_id}"
    return st.button(button_text, key=button_key, width='stretch')


def handle_report_generation(entity_id, format_type, report_type="report", 
                           generate_func=None, generate_args=None, filename_prefix="报告"):
    """
    处理报告生成逻辑
    
    Args:
        entity_id: 实体ID（股票代码或指数名称）
        format_type: 选择的格式类型
        report_type: 报告类型
        generate_func: 生成报告的函数
        generate_args: 生成函数的参数
        filename_prefix: 文件名前缀
    
    Returns:
        bool: 是否生成成功
    """
    if not generate_func:
        st.error("未提供报告生成函数")
        return False
    
    # 安全处理None值
    safe_report_type = str(report_type) if report_type is not None else "report"
    safe_entity_id = str(entity_id) if entity_id is not None else "unknown"
    
    generating_key = f"generating_{safe_report_type}_{safe_entity_id}"
    
    # 设置生成状态
    st.session_state[generating_key] = format_type
    
    # 获取spinner文本
    spinner_texts = {
        "pdf": "正在收集数据并生成PDF报告...",
        "docx": "正在收集数据并生成Word文档...",
        "markdown": "正在收集数据并生成Markdown文件...",
        "html": "正在收集数据并生成HTML文件..."
    }
    
    with st.spinner(spinner_texts.get(format_type, f"正在生成{format_type.upper()}报告...")):
        try:
            # 调用生成函数
            if generate_args:
                report_content = generate_func(*generate_args, format_type=format_type)
            else:
                report_content = generate_func(format_type=format_type)
            
            # 生成时间戳
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S') 
            
            # 获取格式信息
            _, _, _, format_info = get_format_config()
            ext = format_info[format_type]["ext"]
            mime = format_info[format_type]["mime"]
            
            # 安全的文件名生成，处理None值
            safe_filename_prefix = str(filename_prefix) if filename_prefix is not None else "报告"
            safe_entity_id = str(entity_id) if entity_id is not None else "未知"
            safe_timestamp = str(timestamp) if timestamp is not None else "unknown"
            filename = f"{safe_filename_prefix}_{safe_entity_id}_{safe_timestamp}.{ext}"
            
            # 保存到session_state，安全处理None值
            safe_report_type = str(report_type) if report_type is not None else "report"
            safe_entity_for_key = str(entity_id) if entity_id is not None else "unknown"
            
            content_key = f"{safe_report_type}_content_{safe_entity_for_key}"
            filename_key = f"{safe_report_type}_filename_{safe_entity_for_key}"
            mime_key = f"{safe_report_type}_mime_{safe_entity_for_key}"
            format_key = f"{safe_report_type}_format_{safe_entity_for_key}"
            timestamp_key = f"{safe_report_type}_timestamp_{safe_entity_for_key}"
            
            st.session_state[content_key] = report_content
            st.session_state[filename_key] = filename
            st.session_state[mime_key] = mime
            st.session_state[format_key] = format_type
            st.session_state[timestamp_key] = timestamp
            
            # 清除生成状态
            st.session_state[generating_key] = None
            
            # 显示成功消息
            format_names = {"pdf": "PDF", "docx": "Word", "markdown": "Markdown", "html": "HTML"}
            st.success(f"✅ {format_names.get(format_type, format_type.upper())}报告生成成功！")
            
            return True
            
        except Exception as e:
            st.error(f"❌ 生成{format_type.upper()}报告失败: {str(e)}")
            st.session_state[generating_key] = None
            return False


def display_download_button(entity_id, report_type="report"):
    """
    显示下载按钮
    
    Args:
        entity_id: 实体ID（股票代码或指数名称）
        report_type: 报告类型
    
    Returns:
        bool: 是否有可下载的内容
    """
    # 安全处理None值
    safe_report_type = str(report_type) if report_type is not None else "report"
    safe_entity_id = str(entity_id) if entity_id is not None else "unknown"
    
    content_key = f"{safe_report_type}_content_{safe_entity_id}"
    filename_key = f"{safe_report_type}_filename_{safe_entity_id}"
    mime_key = f"{safe_report_type}_mime_{safe_entity_id}"
    format_key = f"{safe_report_type}_format_{safe_entity_id}"
    timestamp_key = f"{safe_report_type}_timestamp_{safe_entity_id}"
    
    if st.session_state.get(content_key):
        format_icons = {"pdf": "📄", "docx": "📝", "markdown": "📝", "html": "🌐"}
        current_format = st.session_state.get(format_key, "pdf")
        
        st.download_button(
            label=f"{format_icons.get(current_format, '📄')} 下载{current_format.upper()}文件",
            data=st.session_state[content_key],
            file_name=st.session_state[filename_key],
            mime=st.session_state[mime_key],
            key=f"download_{safe_report_type}_{safe_entity_id}",
            width='stretch',
            help=f"点击下载生成的{current_format.upper()}报告文件"
        )
        
        timestamp = st.session_state.get(timestamp_key, '')
        st.caption(f"✅ 已生成 {current_format.upper()} | {timestamp}")
        return True
    
    return False


def display_report_export_section(entity_id, report_type="report", 
                                title="📋 导出报告", info_text="💡 可以导出完整的分析报告",
                                generate_func=None, generate_args=None, filename_prefix="报告"):
    """
    显示完整的报告导出区域
    
    Args:
        entity_id: 实体ID（股票代码或指数名称）
        report_type: 报告类型
        title: 标题
        info_text: 信息文本
        generate_func: 生成报告的函数
        generate_args: 生成函数的参数
        filename_prefix: 文件名前缀
    """
    st.markdown("---")
    st.subheader(title)
    st.info(info_text)
    
    # 显示格式选择器
    format_type = display_format_selector(entity_id, report_type)
    
    # 显示生成按钮
    if display_generate_button(entity_id, report_type):
        handle_report_generation(
            entity_id, format_type, report_type, 
            generate_func, generate_args, filename_prefix
        )
    
    # 检查是否有正在生成的报告
    safe_report_type = str(report_type) if report_type is not None else "report"
    safe_entity_id = str(entity_id) if entity_id is not None else "unknown"
    generating_key = f"generating_{safe_report_type}_{safe_entity_id}"
    if st.session_state.get(generating_key):
        # 这里会由handle_report_generation处理
        pass
    
    # 显示下载按钮
    display_download_button(entity_id, report_type)


def display_quick_export_buttons(entity_id, report_type="report", 
                                generate_func=None, generate_args=None, filename_prefix="报告"):
    """
    显示快速导出按钮组（一键导出多种格式）
    
    Args:
        entity_id: 实体ID（股票代码或指数名称）
        report_type: 报告类型
        generate_func: 生成报告的函数
        generate_args: 生成函数的参数
        filename_prefix: 文件名前缀
    """
    st.markdown("#### 🚀 快速导出")
    
    format_options, _, _, _ = get_format_config()
    
    cols = st.columns(len(format_options))
    
    format_icons = {"pdf": "📄", "docx": "📝", "markdown": "📝", "html": "🌐"}
    format_names = {"pdf": "PDF", "docx": "Word", "markdown": "Markdown", "html": "HTML"}
    
    for i, format_type in enumerate(format_options):
        with cols[i]:
            button_key = f"quick_export_{format_type}_{report_type}_{entity_id}"
            if st.button(
                f"{format_icons.get(format_type, '📄')} {format_names.get(format_type, format_type.upper())}", 
                key=button_key,
                width='stretch'
            ):
                handle_report_generation(
                    entity_id, format_type, report_type, 
                    generate_func, generate_args, filename_prefix
                )
                st.rerun()


def display_batch_export_options(entities, report_type="report", 
                                generate_func=None, generate_args_func=None, filename_prefix="报告"):
    """
    显示批量导出选项
    
    Args:
        entities: 实体列表（股票代码或指数名称列表）
        report_type: 报告类型
        generate_func: 生成报告的函数
        generate_args_func: 为每个实体生成参数的函数
        filename_prefix: 文件名前缀
    """
    if not entities:
        st.warning("没有可导出的实体")
        return
    
    st.markdown("#### 📦 批量导出")
    
    # 选择要导出的实体
    selected_entities = st.multiselect(
        "选择要导出的项目",
        entities,
        default=entities[:3] if len(entities) > 3 else entities,  # 默认选择前3个
        key=f"batch_select_{report_type}"
    )
    
    if not selected_entities:
        st.info("请选择要导出的项目")
        return
    
    # 选择导出格式
    format_type = display_format_selector("batch", f"batch_{report_type}")
    
    # 批量导出按钮
    if st.button("🔄 批量生成报告", key=f"batch_generate_{report_type}", width='stretch'):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        success_count = 0
        total_count = len(selected_entities)
        
        for i, entity_id in enumerate(selected_entities):
            status_text.text(f"正在处理: {entity_id} ({i+1}/{total_count})")
            progress_bar.progress((i + 1) / total_count)
            
            try:
                # 获取该实体的生成参数
                if generate_args_func:
                    generate_args = generate_args_func(entity_id)
                else:
                    generate_args = None
                
                # 生成报告
                if handle_report_generation(
                    entity_id, format_type, f"batch_{report_type}", 
                    generate_func, generate_args, filename_prefix
                ):
                    success_count += 1
                    
            except Exception as e:
                st.error(f"处理 {entity_id} 时出错: {str(e)}")
        
        status_text.text(f"批量导出完成: 成功 {success_count}/{total_count}")
        
        if success_count > 0:
            st.success(f"✅ 成功生成 {success_count} 个报告")
            
            # 显示批量下载链接
            st.markdown("#### 📥 下载生成的报告")
            for entity_id in selected_entities:
                if display_download_button(entity_id, f"batch_{report_type}"):
                    pass  # 下载按钮已经显示


def display_export_history(entity_id, report_type="report", max_history=5):
    """
    显示导出历史记录
    
    Args:
        entity_id: 实体ID
        report_type: 报告类型
        max_history: 最大历史记录数
    """
    history_key = f"export_history_{report_type}_{entity_id}"
    
    if history_key not in st.session_state:
        st.session_state[history_key] = []
    
    history = st.session_state[history_key]
    
    if not history:
        st.info("暂无导出历史")
        return
    
    st.markdown("#### 📚 导出历史")
    
    for i, record in enumerate(history[-max_history:]):  # 只显示最近的记录
        with st.expander(f"{record['format'].upper()} - {record['timestamp']}", expanded=False):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**文件名**: {record['filename']}")
                st.write(f"**生成时间**: {record['timestamp']}")
                st.write(f"**文件大小**: {record.get('size', '未知')}")
            
            with col2:
                if st.button(f"重新下载", key=f"redownload_{i}_{entity_id}"):
                    # 这里可以实现重新下载逻辑
                    st.info("重新下载功能待实现")


def add_to_export_history(entity_id, report_type, format_type, filename, content_size=None):
    """
    添加导出记录到历史
    
    Args:
        entity_id: 实体ID
        report_type: 报告类型
        format_type: 格式类型
        filename: 文件名
        content_size: 内容大小
    """
    history_key = f"export_history_{report_type}_{entity_id}"
    
    if history_key not in st.session_state:
        st.session_state[history_key] = []
    
    record = {
        'format': format_type,
        'filename': filename,
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'size': f"{len(str(content_size)) if content_size else 0} bytes" if content_size else "未知"
    }
    
    st.session_state[history_key].append(record)
    
    # 只保留最近的10条记录
    if len(st.session_state[history_key]) > 10:
        st.session_state[history_key] = st.session_state[history_key][-10:]
