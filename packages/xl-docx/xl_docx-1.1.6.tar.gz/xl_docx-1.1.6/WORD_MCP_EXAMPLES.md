# Word MCP 使用示例

本目录包含了使用 `word_mcp` 模块的完整示例，展示如何通过自然语言指令自动创建和修改 Word 文档。

## 📁 文件说明

### 1. `quick_start_example.py` - 快速入门
最简单的使用示例，展示基本的创建和修改功能。

**运行方式：**
```bash
python quick_start_example.py
```

**功能：**
- 创建一个简单的工作报告
- 修改文档添加总结内容

### 2. `example_word_mcp_usage.py` - 完整示例
包含多个详细示例，展示各种使用场景和高级功能。

**运行方式：**
```bash
python example_word_mcp_usage.py
```

**包含示例：**
- 📝 基础文档创建
- ✏️ 文档修改
- 📚 批量文档创建
- 🚀 复杂文档创建（商业计划书）
- 🔄 迭代修改（多次修改同一文档）

## 🛠️ 环境准备

### 1. 安装依赖
确保已安装所需的Python包：
```bash
pip install python-dotenv openai xl-docx
```

### 2. 设置API密钥
创建 `.env` 文件并设置OpenAI API密钥：
```bash
OPENAI_API_KEY=your_api_key_here
```

### 3. 准备模板文件
确保模板文件存在：
- `src/xl_docx/h.docx` - 横向模板
- `src/xl_docx/v.docx` - 纵向模板

## 🎯 核心函数说明

### `create_word(command, template_path, output_path)`
创建新的Word文档（一次性生成）

**参数：**
- `command`: 自然语言创建指令
- `template_path`: 模板文件路径
- `output_path`: 输出文件路径

**返回值：**
```python
{
    "status": "success",
    "action": "create", 
    "output_path": "output.docx",
    "generated_xml": "<xl-p>...</xl-p>"
}
```

### `modify_word(command, template_path, output_path, existing_xml)`
修改现有的Word文档（一次性生成）

**参数：**
- `command`: 自然语言修改指令
- `template_path`: 模板文件路径
- `output_path`: 输出文件路径
- `existing_xml`: 现有的XML内容

**返回值：**
```python
{
    "status": "success",
    "action": "modify",
    "output_path": "output.docx", 
    "generated_xml": "<xl-p>...</xl-p>"
}
```

## 💡 使用技巧

### 1. 指令编写最佳实践
```python
# ✅ 好的指令 - 具体明确
command = """
创建项目报告，包含：
1. 标题：项目进度报告（居中，粗体，24号字体）
2. 项目概述段落
3. 进度表格（3列：任务、状态、负责人）
4. 总结段落
"""

# ❌ 不好的指令 - 模糊不清
command = "创建一个报告"
```

### 2. 错误处理
```python
try:
    result = create_word(command, template_path, output_path)
    if result["status"] == "success":
        print(f"成功: {result['output_path']}")
    else:
        print(f"失败: {result['error']}")
except Exception as e:
    print(f"异常: {str(e)}")
```

### 3. 迭代修改工作流
```python
# 1. 创建基础文档
result1 = create_word("创建基础内容", template, "v1.docx")

# 2. 第一次修改
result2 = modify_word("添加表格", template, "v2.docx", result1["generated_xml"])

# 3. 第二次修改
result3 = modify_word("添加图表", template, "v3.docx", result2["generated_xml"])
```

## 📋 支持的XML语法

文档使用自定义的xl-xml语法，支持：

- **段落**: `<xl-p>文本内容</xl-p>`
- **文本样式**: `<xl-span style="font-weight:bold;">粗体文本</xl-span>`
- **表格**: `<xl-table>`, `<xl-tr>`, `<xl-tc>`
- **样式属性**: 字体、颜色、对齐、间距等

详细语法参考：`src/xl_docx/mcp/xml_syntax_reference.txt`

## 🔧 常见问题

### Q: API密钥错误
**A:** 检查 `.env` 文件中的 `OPENAI_API_KEY` 设置

### Q: 模板文件不存在
**A:** 确保 `src/xl_docx/h.docx` 文件存在且可访问

### Q: 输出目录不存在
**A:** 使用 `os.makedirs("output", exist_ok=True)` 创建目录

### Q: 生成的文档格式不正确
**A:** 检查指令是否足够具体，包含格式要求

## 📊 示例输出

运行示例后，会在 `output/` 目录生成以下文件：
- `quick_report.docx` - 快速入门示例
- `example_report.docx` - 基础报告
- `modified_report.docx` - 修改后的报告
- `meeting_minutes.docx` - 会议纪要
- `project_plan.docx` - 项目计划
- `technical_doc.docx` - 技术文档
- `advanced_document.docx` - 复杂商业计划书
- `product_v1.docx` ~ `product_final.docx` - 迭代修改示例

## 🚀 开始使用

1. 克隆项目并安装依赖
2. 设置 `.env` 文件中的API密钥
3. 运行快速入门示例：`python quick_start_example.py`
4. 查看生成的文档文件
5. 尝试修改指令创建自己的文档

祝您使用愉快！ 🎉
