#!/usr/bin/env python3
"""
Word MCP 快速入门示例
简单演示如何使用 word_mcp 模块
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.xl_docx.mcp.word_mcp import create_word, modify_word


def quick_start():
    """快速入门示例"""
    print("🚀 Word MCP 快速入门")
    print("=" * 40)
    
    # 确保输出目录存在
    os.makedirs("output", exist_ok=True)
    
    # 1. 创建一个简单文档
    print("\n📝 步骤1: 创建文档")
    result = create_word(
        command="创建一个简单的工作报告，包含标题、内容段落和一个表格",
        template_path="src/xl_docx/h.docx",
        output_path="output/quick_report.docx"
    )
    
    if result["status"] == "success":
        print("✅ 文档创建成功!")
        print(f"📄 文件: {result['output_path']}")
        
        # 2. 修改文档
        print("\n✏️ 步骤2: 修改文档")
        modify_result = modify_word(
            command="在文档末尾添加总结段落和联系信息",
            template_path="src/xl_docx/h.docx",
            output_path="output/quick_report_modified.docx",
            existing_xml=result["generated_xml"]
        )
        
        if modify_result["status"] == "success":
            print("✅ 文档修改成功!")
            print(f"📄 修改后文件: {modify_result['output_path']}")
        else:
            print(f"❌ 修改失败: {modify_result['error']}")
    else:
        print(f"❌ 创建失败: {result['error']}")


if __name__ == "__main__":
    # 检查API密钥
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ 请设置 OPENAI_API_KEY 环境变量")
        exit(1)
    
    # 检查模板文件
    if not os.path.exists("src/xl_docx/h.docx"):
        print("❌ 模板文件不存在: src/xl_docx/h.docx")
        exit(1)
    
    quick_start()
