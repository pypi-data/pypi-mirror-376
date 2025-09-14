
import os
from dotenv import load_dotenv
from xl_docx.sheet import Sheet
import openai
import re

# Load environment variables from .env file
load_dotenv()

def _get_xml_reference():
    """获取XML语法参考"""
    reference_file_path = os.path.join(os.path.dirname(__file__), "xml_syntax_reference.txt")
    try:
        with open(reference_file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        raise ValueError(f"XML syntax reference file not found: {reference_file_path}")


def _generate_xml_with_ai(command, existing_xml=None):
    """
    使用AI生成XML
    
    Args:
        command: 用户指令
        existing_xml: 现有的XML内容（用于修改）
    
    Returns:
        str: 生成的XML
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        raise ValueError("OpenAI API key not found. Please set it in the .env file.")
    
    xml_reference = _get_xml_reference()
    
    if existing_xml:
        # 修改模式：基于现有XML进行修改
        system_prompt = f"""
        You are an expert assistant that modifies existing XML structure for a .docx file based on user commands.
        You will be given an existing XML structure and a modification command.
        Your output MUST be only the raw XML, with no explanations, comments, or markdown formatting.
        
        XML Syntax Reference:
        {xml_reference}
        
        Current XML structure:
        {existing_xml}
        
        Now, modify the XML according to the user's command. Remember, ONLY output the complete modified XML code.
        """
    else:
        # 创建模式：创建新的XML
        system_prompt = f"""
        You are an expert assistant that generates a custom XML structure for a .docx file based on user commands.
        Your output MUST be only the raw XML, with no explanations, comments, or markdown formatting.
        The user will provide a command, and you will translate it into the following XML format.

        {xml_reference}

        Now, generate the XML for the user's command. Remember, ONLY output the XML code.
        """
    
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.laozhang.ai/v1"
    )
    
    response = client.chat.completions.create(
        model="qwen-turbo-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": command}
        ],
        temperature=0.1,
    )
    
    ai_generated_xml = response.choices[0].message.content.strip()
    
    # Clean up potential markdown code fences
    if ai_generated_xml.startswith("```xml"):
        ai_generated_xml = ai_generated_xml[6:]
    if ai_generated_xml.startswith("```"):
        ai_generated_xml = ai_generated_xml[3:]
    if ai_generated_xml.endswith("```"):
        ai_generated_xml = ai_generated_xml[:-3]
    
    return ai_generated_xml.strip()


def _compile_xml_to_word(xml_content, template_path, output_path):
    """
    将XML编译为Word文档，并返回Sheet对象
    
    Args:
        xml_content: XML内容
        template_path: 模板文件路径
        output_path: 输出文件路径
    
    Returns:
        Sheet: 处理后的Sheet对象
    """
    if not os.path.exists(template_path):
        raise ValueError(f"Template file not found: {template_path}")
    
    sheet = Sheet(tpl_path=template_path)
    
    # 编译XML到WordprocessingML
    wrapped_xml = f"<root>{xml_content}</root>"
    compiled_body_content = sheet.render_template(wrapped_xml, {})
    compiled_body_content = compiled_body_content.replace("<root>", "").replace("</root>", "").strip()
    
    doc_xml_str = sheet['word/document.xml'].decode('utf-8')
    
    # 找到body标签并替换其内容
    body_pattern = re.compile(r'(<w:body>)(.*)(</w:body>)', re.DOTALL)
    if body_pattern.search(doc_xml_str):
        new_doc_xml_str = body_pattern.sub(f'{compiled_body_content}', doc_xml_str)
    else:
        raise ValueError("Invalid template: <w:body> tag not found in document.xml.")
    
    sheet['word/document.xml'] = new_doc_xml_str.encode('utf-8')
    sheet.save(output_path)
    return sheet


def create_word(command, template_path, output_path):
    """
    创建新的Word文档（一次性生成），返回Sheet对象
    
    Args:
        command: 创建指令
        template_path: 模板文件路径
        output_path: 输出文件路径
    
    Returns:
        Sheet: 处理后的Sheet对象
    """
    try:
        # 生成XML
        xml_content = _generate_xml_with_ai(command)
        
        # 编译为Word文档并返回Sheet对象
        sheet = _compile_xml_to_word(xml_content, template_path, output_path)
        return sheet
        
    except Exception as e:
        raise


def modify_word(command, template_path, output_path, existing_xml):
    """
    修改现有的Word文档（一次性生成），返回Sheet对象
    
    Args:
        command: 修改指令
        template_path: 模板文件路径
        output_path: 输出文件路径
        existing_xml: 现有的XML内容
    
    Returns:
        Sheet: 处理后的Sheet对象
    """
    try:
        # 基于现有XML生成新的XML
        new_xml_content = _generate_xml_with_ai(command, existing_xml)
        
        # 编译为Word文档并返回Sheet对象
        sheet = _compile_xml_to_word(new_xml_content, template_path, output_path)
        return sheet
        
    except Exception as e:
        raise
