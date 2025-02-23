# bidding_workflow.py

from flask import Flask, jsonify, request
from dataclasses import dataclass
from typing import List, Optional, Dict, Union
import json
import yaml
import os
import re
from llmkey import LLMClient
import pathlib
import logging
from config import Config
from prompts import Prompts
import time
import asyncio

app = Flask(__name__)

# 将现有的路径常量替换为配置
BASE_DIR = Config.BASE_DIR
INPUT_DIR = Config.INPUT_DIR
OUTPUT_DIR = Config.OUTPUT_DIR

# 首先创建必要的目录
for path in [
    Config.INPUT_DIR,
    Config.OUTPUT_DIR,
    Config.OUTLINE_DIR,
    Config.LOG_DIR
]:
    path.mkdir(parents=True, exist_ok=True)

# 修改日志配置
logging.basicConfig(level=logging.INFO)  # 设置根日志器级别为 INFO

# 创建文件处理器，用于详细日志
file_handler = logging.FileHandler(Config.LOG_DIR / 'app.log', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# 创建控制台处理器，只显示关键信息
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# 配置根日志器
root_logger = logging.getLogger()
root_logger.handlers = []  # 清除之前的处理器
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# 配置第三方库的日志级别
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

@dataclass
class OutlineNode:
    title: str
    level: int
    content_desc: Optional[str] = None
    children: List['OutlineNode'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
    
    def to_dict(self):
        return {
            'title': self.title,
            'level': self.level,
            'content_desc': self.content_desc,
            'children': [child.to_dict() for child in self.children] if self.children else []
        }

@dataclass
class GenerationProgress:
    total_sections: int = 0
    completed_sections: int = 0
    current_section: str = ""

@dataclass
class SubSection:
    sub_section_title: str
    content_summary: str

    def to_dict(self):
        return {
            'sub_section_title': self.sub_section_title,
            'content_summary': self.content_summary
        }

@dataclass
class Section:
    section_title: str
    sub_sections: List[SubSection]

    def to_dict(self):
        return {
            'section_title': self.section_title,
            'sub_sections': [sub.to_dict() for sub in self.sub_sections]
        }

@dataclass
class Chapter:
    chapter_title: str
    sections: List[Section]

    def to_dict(self):
        return {
            'chapter_title': self.chapter_title,
            'sections': [section.to_dict() for section in self.sections]
        }

@dataclass
class Outline:
    body_paragraphs: List[Chapter]

    def to_dict(self):
        return {
            'body_paragraphs': [chapter.to_dict() for chapter in self.body_paragraphs]
        }

class BiddingWorkflow:
    def __init__(self):
        self.tech_content = ""
        self.score_content = ""
        self.outline = None
        self.generated_contents = {}
        self.llm_client = LLMClient()
        self.progress = GenerationProgress()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if hasattr(self, 'llm_client'):
            await self.llm_client.close()

    def load_input_files(self):
        """加载技术要求和评分标准文件"""
        try:
            tech_file = Config.INPUT_DIR / 'tech.md'
            score_file = Config.INPUT_DIR / 'score.md'
            
            # 检查文件是否存在
            if not tech_file.exists():
                logger.error(f"Tech file not found: {tech_file}")
                raise FileNotFoundError(f"Tech file not found: {tech_file}")
            if not score_file.exists():
                logger.error(f"Score file not found: {score_file}")
                raise FileNotFoundError(f"Score file not found: {score_file}")
            
            # 检查文件是否为空
            if tech_file.stat().st_size == 0:
                logger.error("Tech file is empty")
                raise ValueError("Tech file is empty")
            if score_file.stat().st_size == 0:
                logger.error("Score file is empty")
                raise ValueError("Score file is empty")
            
            with open(tech_file, 'r', encoding='utf-8') as f:
                self.tech_content = f.read()
                logger.info(f"Loaded tech file, size: {len(self.tech_content)} chars")
            
            with open(score_file, 'r', encoding='utf-8') as f:
                self.score_content = f.read()
                logger.info(f"Loaded score file, size: {len(self.score_content)} chars")
            
        except Exception as e:
            logger.error(f"Error loading input files: {e}", exc_info=True)
            raise
            
    def clean_json_response(self, response: str) -> str:
        """清理大模型返回的 JSON 响应"""
        if not response:
            return response
        
        try:
            # 清理代码块标记
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            elif cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            
            cleaned = cleaned.strip()
            
            # 尝试解析和重新格式化 JSON
            try:
                # 先尝试直接解析
                parsed = json.loads(cleaned)
                return json.dumps(parsed, ensure_ascii=False)
            except json.JSONDecodeError as e:
                logger.warning(f"Initial JSON parsing failed: {e}")
                
                # 尝试修复常见的 JSON 格式问题
                # 1. 处理未转义的引号
                cleaned = re.sub(r'(?<!\\)"(?!,|\s*}|\s*]|\s*:)', '\\"', cleaned)
                
                # 2. 处理多行字符串
                cleaned = cleaned.replace('\n', '\\n')
                
                # 3. 处理未闭合的引号
                quote_count = cleaned.count('"')
                if quote_count % 2 != 0:
                    logger.warning("Detected unclosed quotes, attempting to fix")
                    # 找到最后一个完整的 JSON 结构
                    last_brace = cleaned.rfind('}')
                    if last_brace > 0:
                        cleaned = cleaned[:last_brace + 1]
                
                # 4. 处理尾部逗号
                cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
                
                # 再次尝试解析
                try:
                    parsed = json.loads(cleaned)
                    logger.info("Successfully fixed and parsed JSON")
                    return json.dumps(parsed, ensure_ascii=False)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to fix JSON: {e}")
                    logger.error(f"Problematic JSON:\n{cleaned}")
                    raise ValueError(f"Could not parse JSON response: {e}")
                
        except Exception as e:
            logger.error(f"Error cleaning JSON response: {e}")
            logger.error(f"Original response:\n{response}")
            raise

    async def generate_outline(self) -> str:
        """生成大纲"""
        try:
            logger.info("=== Starting Outline Generation ===")
            
            # 初始化对话
            messages = [{"role": "system", "content": Prompts.OUTLINE_SYSTEM_ROLE}]
            
            # 1. 发送技术要求
            messages.append({
                "role": "user", 
                "content": Prompts.OUTLINE_TECH_USER.format(tech_content=self.tech_content)
            })
            
            # 2. 发送评分标准
            messages.append({
                "role": "user", 
                "content": Prompts.OUTLINE_SCORE_USER.format(score_content=self.score_content)
            })
            
            # 3. 要求生成完整大纲
            messages.append({
                "role": "user", 
                "content": Prompts.OUTLINE_GENERATE_USER
            })
            
            # 调用 LLM 生成大纲
            outline_json = await self.llm_client.generate_text_async(
                messages=messages,
                require_json=True,
                require_outline=True
            )
            
            if not outline_json:
                logger.error("Failed to generate outline")
                return None
                
            # 保存大纲
            self.save_outline_json(outline_json)
            
            return outline_json
            
        except Exception as e:
            logger.error(f"Error generating outline: {e}")
            raise

    def split_long_text(self, text: str, max_length: int = 3000) -> List[str]:
        """将长文本分割成较小的块，确保在句子边界处分割"""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        # 按句子分割文本
        sentences = text.replace('\r', '').split('\n')
        for sentence in sentences:
            # 如果单个句子就超过了最大长度，需要强制分割
            if len(sentence) > max_length:
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # 按字符数分割长句子
                for i in range(0, len(sentence), max_length):
                    chunk = sentence[i:i + max_length]
                    chunks.append(chunk)
                continue
            
            # 检查添加当前句子是否会超过最大长度
            if current_length + len(sentence) + 1 > max_length:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [sentence]
                current_length = len(sentence)
            else:
                current_chunk.append(sentence)
                current_length += len(sentence) + 1
        
        # 添加最后一个块
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks

    def parse_outline_json(self, outline_json: Union[str, dict]) -> Outline:
        """解析大模型返回的JSON格式大纲，转换为Outline结构"""
        try:
            # 输入验证
            if not outline_json:
                raise ValueError("Empty input received")
            
            # 如果输入是字符串，则解析为dict
            if isinstance(outline_json, str):
                try:
                    # 记录原始输入
                    logger.debug("=== Input JSON String ===")
                    logger.debug(outline_json)
                    logger.debug("=== End Input JSON String ===")
                    
                    data = json.loads(outline_json)
                    logger.debug("Successfully parsed JSON string")
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response: {e}")
                    logger.debug(f"Problematic JSON: {outline_json}")
                    raise
            else:
                data = outline_json
            
            logger.debug(f"Parsing outline data: {json.dumps(data, ensure_ascii=False)}")
            
            # 验证必要的字段
            if not isinstance(data, dict):
                raise ValueError(f"Expected dict, got {type(data)}")
            
            if 'body_paragraphs' not in data:
                raise ValueError("Missing required field 'body_paragraphs'")
            
            if not isinstance(data['body_paragraphs'], list):
                raise ValueError("'body_paragraphs' must be a list")
            
            chapters = []
            for chapter_data in data['body_paragraphs']:
                if 'chapter_title' not in chapter_data or 'sections' not in chapter_data:
                    raise ValueError("Missing required fields in chapter data")
                
                sections = []
                for section_data in chapter_data['sections']:
                    if 'section_title' not in section_data or 'sub_sections' not in section_data:
                        raise ValueError("Missing required fields in section data")
                    
                    sub_sections = []
                    for sub_section_data in section_data['sub_sections']:
                        if 'sub_section_title' not in sub_section_data or 'content_summary' not in sub_section_data:
                            raise ValueError("Missing required fields in sub_section data")
                        
                        sub_section = SubSection(
                            sub_section_title=sub_section_data['sub_section_title'],
                            content_summary=sub_section_data['content_summary']
                        )
                        sub_sections.append(sub_section)
                    
                    section = Section(
                        section_title=section_data['section_title'],
                        sub_sections=sub_sections
                    )
                    sections.append(section)
                
                chapter = Chapter(
                    chapter_title=chapter_data['chapter_title'],
                    sections=sections
                )
                chapters.append(chapter)
            
            return Outline(body_paragraphs=chapters)
        
        except Exception as e:
            logger.error(f"Error parsing outline JSON: {e}", exc_info=True)
            raise

    def generate_content_prompt(self, section: OutlineNode, context: str) -> str:
        """生成内容生成阶段的prompt"""
        return Prompts.CONTENT_PROMPT.format(
            tech_content=self.tech_content,
            score_content=self.score_content,
            outline=self.outline_to_markdown(),
            context=context,
            section_title=section.title,
            content_desc=section.content_desc
        )

    def outline_to_markdown(self) -> str:
        """将大纲转换为markdown格式"""
        if not self.outline:
            return ""
        
        result = []
        for chapter in self.outline.body_paragraphs:
            result.append(f"# {chapter.chapter_title}")
            for section in chapter.sections:
                result.append(f"## {section.section_title}")
                for sub_section in section.sub_sections:
                    result.append(f"### {sub_section.sub_section_title}")
                    result.append(f"\n{sub_section.content_summary}\n")
        
        return "\n".join(result)

    def get_context_for_section(self, current_section: OutlineNode) -> str:
        """获取当前章节的相关上下文内容"""
        context_parts = []
        
        # 获取当前章节的父章节路径
        parent_titles = []
        current_level = current_section.level
        
        def find_parents(node: OutlineNode, target: OutlineNode, path: List[str]):
            if node == target:
                return True
            for child in node.children:
                if find_parents(child, target, path):
                    path.append(node.title)
                    return True
            return False
        
        if self.outline:
            find_parents(self.outline, current_section, parent_titles)
        
        # 获取相关的已生成内容
        for title in parent_titles:
            if title in self.generated_contents:
                context_parts.append(f"## {title}\n{self.generated_contents[title]}\n")
        
        # 限制上下文长度
        max_context_length = 2000
        context = "\n".join(context_parts)
        if len(context) > max_context_length:
            context = context[-max_context_length:]
        
        return context

    def save_outline(self):
        """保存大纲到文件"""
        if not self.outline:
            logger.error("No outline to save")
            return
            
        try:
            # 保存JSON格式
            outline_dict = self.outline.to_dict()
            json_path = Config.OUTLINE_DIR / 'outline.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(outline_dict, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved outline JSON to {json_path}")
            
            # 保存Markdown格式（用于展示）
            md_content = self.outline_to_markdown()
            md_path = Config.OUTLINE_DIR / 'outline.md'
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            logger.info(f"Saved outline markdown to {md_path}")
            
        except Exception as e:
            logger.error(f"Error saving outline: {e}", exc_info=True)
            raise

    def save_content(self, section_title: str, content: str):
        """保存生成的内容"""
        self.generated_contents[section_title] = content
        
        # 将所有内容按顺序写入一个文件
        content_file = Config.OUTPUT_DIR / 'content.md'
        
        # 如果是第一个章节，先写入大纲
        if len(self.generated_contents) == 1:
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write("# 技术方案\n\n")
                f.write(self.outline_to_markdown())
                f.write("\n\n## 详细内容\n\n")
        
        # 追加新内容
        with open(content_file, 'a', encoding='utf-8') as f:
            f.write(f"### {section_title}\n\n")
            f.write(content)
            f.write("\n\n")

    def count_sections(self, node: OutlineNode) -> int:
        count = 1 if node.level == 3 else 0
        for child in node.children:
            count += self.count_sections(child)
        return count

    async def generate_full_content_async(self) -> bool:
        """异步生成完整文档内容"""
        start_time = time.time()
        try:
            if not self.outline:
                logger.error("No outline available")
                return False

            logger.info("=== Starting Content Generation ===")
            
            # 收集所有需要生成的章节
            sections_to_generate = []
            for chapter in self.outline.body_paragraphs:
                for section in chapter.sections:
                    for sub_section in section.sub_sections:
                        sections_to_generate.append({
                            'title': sub_section.sub_section_title,
                            'content_summary': sub_section.content_summary,
                            'chapter': chapter.chapter_title,
                        })

            total_sections = len(sections_to_generate)
            logger.info(f"Found {total_sections} sections to generate")

            # 使用信号量控制并发数为15（略小于理论值16.67，留出余量）
            semaphore = asyncio.Semaphore(15)
            
            async def process_section_with_semaphore(section):
                async with semaphore:
                    result = await self.llm_client.generate_section_content_async(section)
                    # 每次请求后添加很短的延迟
                    await asyncio.sleep(0.05)  # 50ms 延迟
                    return result

            # 分批处理任务
            results = []
            batch_size = 15  # 每批处理15个请求
            
            for i in range(0, len(sections_to_generate), batch_size):
                batch = sections_to_generate[i:i + batch_size]
                batch_tasks = [process_section_with_semaphore(section) for section in batch]
                
                # 执行当前批次
                batch_results = await asyncio.gather(*batch_tasks)
                results.extend(batch_results)
                
                # 批次间等待
                if i + batch_size < len(sections_to_generate):
                    await asyncio.sleep(0.2)  # 每批次间等待200ms
                
                # 进度报告
                completed = len(results)
                logger.info(f"Progress: {completed}/{total_sections} sections completed")
            
            # 处理结果
            organized_results = self._organize_results(results, sections_to_generate)
            success = await self._save_results_async(organized_results)
            
            elapsed_time = time.time() - start_time
            logger.info(f"Content generation completed in {elapsed_time:.2f} seconds")
            
            return success

        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return False

    def _organize_results(self, results: List[Dict], sections: List[Dict]) -> Dict:
        """将结果按章节组织"""
        organized = {}
        for result, section in zip(results, sections):
            chapter = section['chapter']
            if chapter not in organized:
                organized[chapter] = []
            organized[chapter].append(result)
        return organized

    async def _save_results_async(self, organized_results: Dict) -> bool:
        """异步保存按章节组织的内容"""
        try:
            content_parts = []
            for chapter, sections in organized_results.items():
                # 添加章节标题
                content_parts.append(f"# {chapter}\n\n")
                
                # 按二级标题分组
                section_groups = {}
                for section in sections:
                    # 从标题中提取二级标题
                    # 例如从 "1.1.1 xxx" 中提取 "1.1"
                    section_number = '.'.join(section['title'].split()[:1][0].split('.')[:2])
                    section_title = section['title']
                    
                    # 找到对应的二级标题文本
                    section_prefix = section_number + ' '
                    full_section_title = next(
                        (title for title in section['title'].split('\n') if title.startswith(section_prefix)),
                        section_prefix + '未知标题'
                    )
                    
                    if section_number not in section_groups:
                        section_groups[section_number] = {
                            'title': full_section_title,
                            'subsections': []
                        }
                    section_groups[section_number]['subsections'].append(section)
                
                # 按二级标题顺序输出内容
                for section_number in sorted(section_groups.keys()):
                    group = section_groups[section_number]
                    # 添加二级标题
                    content_parts.append(f"## {group['title']}\n\n")
                    # 添加三级标题和内容
                    for subsection in group['subsections']:
                        content_parts.append(f"### {subsection['title']}\n\n{subsection['content']}\n\n")
            
            content = "\n".join(content_parts)
            
            with open(Config.OUTPUT_DIR / 'content.md', 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return False

    def save_outline_json(self, outline_json: str):
        """保存大纲 JSON 到文件"""
        try:
            # 确保输出目录存在
            Config.OUTLINE_DIR.mkdir(parents=True, exist_ok=True)
            
            # 保存 JSON 文件
            json_file = Config.OUTLINE_DIR / 'outline.json'
            with open(json_file, 'w', encoding='utf-8') as f:
                f.write(outline_json)
            logger.info(f"Saved outline JSON to {json_file}")
            
            # 同时保存一个 Markdown 格式的版本，方便查看
            md_file = Config.OUTLINE_DIR / 'outline.md'
            md_content = self._convert_outline_to_markdown(outline_json)
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            logger.info(f"Saved outline Markdown to {md_file}")
            
        except Exception as e:
            logger.error(f"Error saving outline: {e}")
            raise

    def _convert_outline_to_markdown(self, outline_json: str) -> str:
        """将大纲 JSON 转换为 Markdown 格式"""
        try:
            outline = json.loads(outline_json)
            md_lines = []
            
            for chapter in outline["body_paragraphs"]:
                # 添加章标题
                md_lines.append(f"# {chapter['chapter_title']}\n")
                
                for section in chapter["sections"]:
                    # 添加节标题
                    md_lines.append(f"## {section['section_title']}\n")
                    
                    for sub_section in section["sub_sections"]:
                        # 添加子节标题
                        md_lines.append(f"### {sub_section['sub_section_title']}\n")
                        # 添加内容概要
                        md_lines.append(f"{sub_section['content_summary']}\n")
                
                md_lines.append("\n")  # 章节之间添加空行
            
            return "\n".join(md_lines)
            
        except Exception as e:
            logger.error(f"Error converting outline to markdown: {e}")
            raise

def dict_to_outline(data: dict) -> OutlineNode:
    node = OutlineNode(
        title=data['title'],
        level=data['level'],
        content_desc=data.get('content_desc')
    )
    if data.get('children'):
        node.children = [dict_to_outline(child) for child in data['children']]
    return node

@app.route('/generate_outline', methods=['POST'])
def generate_outline():
    workflow = BiddingWorkflow()
    try:
        logger.info("Starting outline generation")
        
        # 加载输入文件
        logger.info("Loading input files")
        workflow.load_input_files()
        
        # 生成大纲
        logger.info("Generating outline")
        outline_json = workflow.generate_outline()
        if not outline_json:
            logger.error("Failed to generate outline")
            return jsonify({"status": "error", "message": "Failed to generate outline"}), 500
            
        logger.info("Successfully generated outline")
        logger.debug(f"Raw outline JSON:\n{outline_json}")
        
        # 解析大纲
        logger.info("Parsing outline JSON")
        workflow.outline = workflow.parse_outline_json(outline_json)
        
        # 保存大纲
        logger.info("Saving outline")
        workflow.save_outline()
        
        logger.info("Outline generation completed successfully")
        return jsonify({
            "status": "success",
            "outline": workflow.outline.to_dict()
        })
    except Exception as e:
        logger.error(f"Error in generate_outline: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/generate_content', methods=['POST'])
async def generate_content():
    workflow = BiddingWorkflow()
    try:
        success = await workflow.generate_full_content_async()
        if success:
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Content generation failed"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        await workflow.llm_client.close()

@app.route('/generate_document', methods=['POST'])
def generate_document():
    workflow = BiddingWorkflow()
    try:
        # 加载输入文件
        workflow.load_input_files()
        
        # 加载大纲
        with open(Config.OUTLINE_DIR / 'outline.json', 'r', encoding='utf-8') as f:
            outline_dict = json.load(f)  # 这里已经得到了 dict
            workflow.outline = workflow.parse_outline_json(outline_dict)  # 直接传入 dict
        
        # 生成完整内容
        content = workflow.generate_full_content_async()
        if not content:
            return jsonify({"status": "error", "message": "Failed to generate content"}), 500
        
        return jsonify({
            "status": "success",
            "message": "Document generated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error generating document: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)