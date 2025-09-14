#!/usr/bin/env python3
"""
Word MCP 使用示例
展示如何使用 word_mcp 模块创建和修改 Word 文档
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp.word_mcp import create_word, modify_word


def example_create_document():
    template_path = "h.docx"
    output_path = "output/example_report.docx"
    
    os.makedirs("output", exist_ok=True)
    
    command = """
    创建一个项目报告，包含以下内容：
    1. 标题：项目进度报告（居中，粗体，24号字体）
    2. 项目概述段落
    3. 一个包含3列的表格：任务名称、完成状态、负责人
    4. 总结段落
    """
    
    result = create_word(command, template_path, output_path)
    
    if result["status"] == "success":
        return result["generated_xml"]
    else:
        return None
            
   


def example_modify_document(existing_xml):
    if not existing_xml:
        return
    
    template_path = "h.docx"
    output_path = "output/modified_report.docx"
    
    command = """
    在现有文档的基础上添加以下内容：
    1. 在文档末尾添加一个新的章节标题：风险评估
    2. 添加一个风险评估表格，包含风险类型、风险等级、应对措施三列
    3. 添加一个结论段落
    """
    
    try:
        result = modify_word(command, template_path, output_path, existing_xml)
        
    except Exception as e:
        print(e)


def example_batch_creation():
    os.makedirs("output", exist_ok=True)
    
    documents = [
        {
            "name": "会议纪要",
            "command": "创建会议纪要，包含会议主题、参会人员、讨论要点、决议事项",
            "output": "output/meeting_minutes.docx"
        },
        {
            "name": "项目计划",
            "command": "创建项目计划文档，包含项目目标、时间安排、资源分配、里程碑",
            "output": "output/project_plan.docx"
        },
        {
            "name": "技术文档",
            "command": "创建技术文档，包含系统架构图说明、API接口文档、部署指南",
            "output": "output/technical_doc.docx"
        }
    ]
    
    template_path = "h.docx"
    
    for i, doc in enumerate(documents, 1):
        try:
            result = create_word(doc['command'], template_path, doc['output'])
        except Exception as e:
            pass


def example_advanced_usage():
    template_path = "h.docx"
    output_path = "output/advanced_document.docx"
    
    command = """
    创建一个完整的商业计划书，包含：
    
    1. 封面页：
       - 公司名称（大标题，居中）
       - 商业计划书（副标题）
       - 日期
    
    2. 执行摘要（新页面）：
       - 标题：执行摘要
       - 公司概述段落
       - 市场机会段落
       - 竞争优势段落
    
    3. 市场分析（新页面）：
       - 标题：市场分析
       - 市场规模表格（3列：市场细分、规模、增长率）
       - 竞争对手分析表格（4列：公司名称、市场份额、优势、劣势）
    
    4. 财务预测（新页面）：
       - 标题：财务预测
       - 收入预测表格（5列：年份、产品A收入、产品B收入、总收入、增长率）
       - 成本分析段落
    
    请使用适当的字体大小、对齐方式和表格样式。
    """
    
    try:
        result = create_word(command, template_path, output_path)
    except Exception as e:
        pass




def main():
    existing_xml = example_create_document()
    # example_modify_document(existing_xml)


if __name__ == "__main__":
    main()
