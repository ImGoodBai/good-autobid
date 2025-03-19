import os
from openai import OpenAI
from config import Config
import logging
import json
from prompts import Prompts
import time
import asyncio
import aiohttp
from typing import List, Dict, Optional
import re
import ssl

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv('LLM_API_KEY', Config.LLM_API_KEY)
        self.base_url = os.getenv('LLM_API_BASE', Config.LLM_API_BASE)
        self.session = None
        self.messages = []
        logger.info("LLM客户端初始化成功")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def _ensure_session(self):
        """确保 session 存在且有效"""
        if self.session is None or self.session.closed:
            # 配置 SSL 上下文
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            
            # 配置连接超时
            timeout = aiohttp.ClientTimeout(
                total=Config.TIMEOUT,
                connect=10,
                sock_read=20
            )
            
            # 确保 base_url 以斜杠结尾
            base_url = self.base_url
            if not base_url.endswith('/'):
                base_url += '/'
            
            # 配置连接器
            connector_kwargs = {
                'ssl': ssl_context,
                'limit': 15,  # 调整并发连接数
                'force_close': True,
                'enable_cleanup_closed': True
            }
            
            connector = aiohttp.TCPConnector(**connector_kwargs)
            
            # 创建会话
            session_kwargs = {
                'base_url': base_url,
                'headers': {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                'timeout': timeout,
                'connector': connector
            }
            
            # 如果使用代理，添加代理配置到会话
            if Config.USE_PROXY:
                session_kwargs['proxy'] = Config.PROXY_URLS['https']
                logger.info(f"使用代理: {Config.PROXY_URLS}")
            
            self.session = aiohttp.ClientSession(**session_kwargs)
            
            logger.info(f"创建新会话，基础URL: {base_url}")

    async def _call_llm_async(self, messages: list, require_json: bool = False, require_outline: bool = False) -> Optional[str]:
        """异步调用 LLM API"""
        await self._ensure_session()
        retry_count = 0
        
        while retry_count <= Config.MAX_RETRIES:
            try:
                request_params = {
                    "model": Config.LLM_MODEL,
                    "messages": messages,
                    "temperature": Config.TEMPERATURE,
                    "max_tokens": Config.MAX_TOKENS,
                    "top_p": Config.TOP_P
                }

                logger.info(f"API调用信息:")
                logger.info(f"Model: {Config.LLM_MODEL}")
                logger.info(f"Request Data: {json.dumps(request_params, ensure_ascii=False)}")
                
                async with self.session.post(
                    "chat/completions",
                    json=request_params,
                    timeout=Config.TIMEOUT,
                    ssl=False  # 禁用 SSL 验证，如果需要的话
                ) as response:
                    # 获取完整的请求URL
                    full_url = str(response.request_info.url)
                    logger.info(f"完整请求URL: {full_url}")
                    logger.info(f"请求Headers: {response.request_info.headers}")
                    
                    # 首先记录原始响应
                    response_text = await response.text()
                    logger.debug(f"原始API响应: {response_text}")
                    
                    # 如果状态码不是 200，记录错误并重试
                    if response.status != 200:
                        logger.error(f"完整的API错误响应: {response_text}")
                        raise ValueError(f"API返回状态{response.status}")

                    # 解析响应
                    result = json.loads(response_text)
                    
                    # 提取内容
                    if "choices" in result and result["choices"] and "message" in result["choices"][0]:
                        content = result["choices"][0]["message"]["content"].strip()
                        
                        # 如果需要 JSON 格式，尝试解析
                        if require_json:
                            try:
                                if content.startswith('```'):
                                    content = re.sub(r'^```(?:json)?\s*|\s*```\s*$', '', content)
                                json_obj = json.loads(content)
                                content = json.dumps(json_obj, ensure_ascii=False, indent=2)
                            except json.JSONDecodeError as e:
                                logger.error(f"响应中的JSON无效: {e}")
                                logger.error(f"导致错误的JSON内容: {content}")
                                print(f"\n\n===== JSON解析错误 =====\n错误位置: 第{e.lineno}行, 第{e.colno}列, 字符位置{e.pos}\n错误信息: {e.msg}\n===================\n\n")
                                raise
                        
                        return content
                    else:
                        logger.error(f"意外的响应结构: {result}")
                        raise ValueError("响应结构无效")

            except asyncio.TimeoutError:
                retry_count += 1
                if retry_count <= Config.MAX_RETRIES:
                    wait_time = Config.RETRY_DELAY * (Config.RETRY_BACKOFF ** (retry_count - 1))
                    logger.warning(f"请求超时。将在{wait_time}秒后重试... (尝试 {retry_count}/{Config.MAX_RETRIES})")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("请求在最大重试次数后因超时而失败")
                    raise TimeoutError("API请求超时")

            except ValueError as e:
                raise ValueError(f"API调用失败: {str(e)}")

            except Exception as e:
                raise Exception(f"API调用发生未知错误: {str(e)}")

    async def generate_section_content_async(self, section: Dict) -> Dict:
        """异步生成单个章节内容"""
        try:
            # 开始生成
            logger.info(f"=== 生成内容为章节: {section['title']} ===")
            #logger.info(f"内容边界: {section['content_summary'][:100]}...")  # 只显示前100个字符
            start_time = time.time()

            prompt = Prompts.CONTENT_SECTION_USER.format(
                title=section['title'],
                content_summary=section['content_summary']
            )
            
            content = await self._call_llm_async([
                {"role": "system", "content": Prompts.CONTENT_SYSTEM_ROLE},
                {"role": "user", "content": prompt}
            ])

            # 完成生成
            elapsed_time = time.time() - start_time
            if content:
                content_length = len(content)
                logger.info(f"✓ 成功生成 {content_length} 个字符为 {section['title']} 在 {elapsed_time:.2f}秒")
            else:
                logger.error(f"✗ 生成内容为 {section['title']} 失败，耗时 {elapsed_time:.2f}秒")

            return {
                'title': section['title'],
                'content': content if content else "生成失败，请手动补充。"
            }
        except Exception as e:
            logger.error(f"✗ 生成内容为 {section['title']} 时出错: {str(e)}")
            return {
                'title': section['title'],
                'content': f"生成失败：{str(e)}"
            }

    async def generate_content_init_async(self, tech_content: str, score_content: str, outline: str) -> bool:
        """初始化内容生成的背景信息"""
        try:
            prompt = Prompts.CONTENT_INIT_USER.format(
                tech_content=tech_content,
                score_content=score_content,
                outline=outline
            )
            self.start_new_chat(Prompts.CONTENT_SYSTEM_ROLE)
            response = await self.generate_chat_text_async(prompt)
            return bool(response)
        except Exception as e:
            logger.error(f"初始化内容生成时出错: {e}")
            return False

    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    def start_new_chat(self, system_role: str):
        """开始新的对话"""
        self.messages = [{"role": "system", "content": system_role}]
        
    def add_message(self, role: str, content: str):
        """添加消息到对话历史"""
        self.messages.append({"role": role, "content": content})
        
    async def generate_text_async(self, prompt=None, system_role=None, messages=None, require_json=False, require_outline=False) -> str:
        """异步生成文本
        :param prompt: 单条提示词
        :param system_role: 系统角色设定
        :param messages: 完整的消息列表（如果提供，则忽略 prompt 和 system_role）
        :param require_json: 是否要求 JSON 格式响应
        :param require_outline: 是否要求大纲格式（包含 body_paragraphs 字段）
        """
        try:
            if messages is None:
                messages = [
                    {"role": "system", "content": system_role or Prompts.OUTLINE_SYSTEM_ROLE},
                    {"role": "user", "content": prompt}
                ]
            
            return await self._call_llm_async(messages, require_json=require_json, require_outline=require_outline)
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析错误: {str(e)}"
            logger.error(f"生成文本时出错: {error_msg}", exc_info=True)
            print(f"\n\n===== 错误信息 =====\n{error_msg}\n===================\n\n如果是在第86行附近出现问题，请检查JSON文件中是否有属性名没有用双引号包裹。\n===================\n\n")
            return None
        except Exception as e:
            error_msg = f"生成文本时出错: {str(e)}"
            logger.error(f"生成文本时出错: {error_msg}", exc_info=True)
            print(f"\n\n===== 错误信息 =====\n{error_msg}\n===================\n\n")
            return None
            
    async def generate_chat_text_async(self, prompt: str) -> str:
        """异步在现有对话中生成文本（用于内容生成）"""
        try:
            self.add_message("user", prompt)
            response = await self._call_llm_async(self.messages, require_json=False)
            if response:
                self.add_message("assistant", response)
            return response
        except Exception as e:
            logger.error(f"生成聊天文本时出错: {e}", exc_info=True)
            return None