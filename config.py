from pathlib import Path
import logging
import json
import os

class Config:
    # 基础路径配置
    BASE_DIR = Path(__file__).parent
    INPUT_DIR = BASE_DIR / "inputs"
    OUTPUT_DIR = BASE_DIR / "outputs"
    OUTLINE_DIR = OUTPUT_DIR / "outline"
    LOG_DIR = BASE_DIR / "logs"
    
    # 配置文件路径
    CONFIG_FILE = BASE_DIR / "config.json"

    # LLM配置
    LLM_API_KEY = None
    LLM_API_BASE = None
    LLM_MODEL = None
    MAX_TOKENS = None
    TEMPERATURE = None
    TOP_P = None
    TIMEOUT = None
    
    # 重试配置
    MAX_RETRIES = None
    RETRY_DELAY = None
    RETRY_BACKOFF = None
    
    # API配置
    REQUEST_TIMEOUT = None
    
    # 代理配置
    USE_PROXY = None
    PROXY_URLS = None

    # 提示词配置
    PROMPTS_CONFIG = {
        'outline': {
            'system_role': '',
            'tech_user': '',
            'score_user': '',
            'generate_user': ''
        },
        'content': {
            'system_role': '',
            'init_user': '',
            'section_user': ''
        }
    }

    @classmethod
    def _ensure_directories(cls):
        """确保必要的目录存在"""
        for directory in [cls.INPUT_DIR, cls.OUTPUT_DIR, cls.OUTLINE_DIR, cls.LOG_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _create_default_config(cls):
        """创建默认配置文件"""
        default_config = {
            'llm': {
                'api_key': "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",
                'api_base': "https://openrouter.ai/api/v1",
                'model': "google/gemini-2.0-flash-lite-preview-02-05:free",
                'max_tokens': 8192,
                'temperature': 0.7,
                'top_p': 0.1,
                'timeout': 30
            },
            'retry': {
                'max_retries': 3,
                'delay': 2,
                'backoff': 1.5
            },
            'api': {
                'request_timeout': 30
            },
            'proxy': {
                'enabled': False,
                'urls': {
                    'http': "http://127.0.0.1:33210",
                    'https': "http://127.0.0.1:33210"
                }
            }
        }
        
        with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        
        return default_config

    @classmethod
    def load_config(cls):
        """从JSON文件加载配置"""
        cls._ensure_directories()
        
        # 如果配置文件不存在，创建默认配置
        if not cls.CONFIG_FILE.exists():
            config = cls._create_default_config()
        else:
            with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)

        # 加载LLM配置
        llm_config = config.get('llm', {})
        cls.LLM_API_KEY = llm_config.get('api_key')
        cls.LLM_API_BASE = llm_config.get('api_base')
        cls.LLM_MODEL = llm_config.get('model')
        cls.MAX_TOKENS = llm_config.get('max_tokens')
        cls.TEMPERATURE = llm_config.get('temperature')
        cls.TOP_P = llm_config.get('top_p')
        cls.TIMEOUT = llm_config.get('timeout')

        # 加载重试配置
        retry_config = config.get('retry', {})
        cls.MAX_RETRIES = retry_config.get('max_retries')
        cls.RETRY_DELAY = retry_config.get('delay')
        cls.RETRY_BACKOFF = retry_config.get('backoff')

        # 加载API配置
        api_config = config.get('api', {})
        cls.REQUEST_TIMEOUT = api_config.get('request_timeout')

        # 加载代理配置
        proxy_config = config.get('proxy', {})
        cls.USE_PROXY = proxy_config.get('enabled')
        cls.PROXY_URLS = proxy_config.get('urls')

        # 加载提示词配置
        prompts_config = config.get('prompts', {})
        cls.PROMPTS_CONFIG = prompts_config

    @classmethod
    def save_config(cls):
        """保存配置到JSON文件"""
        config = {
            'llm': {
                'api_key': cls.LLM_API_KEY,
                'api_base': cls.LLM_API_BASE,
                'model': cls.LLM_MODEL,
                'max_tokens': cls.MAX_TOKENS,
                'temperature': cls.TEMPERATURE,
                'top_p': cls.TOP_P,
                'timeout': cls.TIMEOUT
            },
            'retry': {
                'max_retries': cls.MAX_RETRIES,
                'delay': cls.RETRY_DELAY,
                'backoff': cls.RETRY_BACKOFF
            },
            'api': {
                'request_timeout': cls.REQUEST_TIMEOUT
            },
            'proxy': {
                'enabled': cls.USE_PROXY,
                'urls': cls.PROXY_URLS
            },
            'prompts': cls.PROMPTS_CONFIG
        }
        
        with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)

    @classmethod
    def get_config(cls):
        """获取当前配置"""
        return {
            'llm': {
                'api_key': cls.LLM_API_KEY,
                'api_base': cls.LLM_API_BASE,
                'model': cls.LLM_MODEL,
                'max_tokens': cls.MAX_TOKENS,
                'temperature': cls.TEMPERATURE,
                'top_p': cls.TOP_P,
                'timeout': cls.TIMEOUT
            },
            'retry': {
                'max_retries': cls.MAX_RETRIES,
                'delay': cls.RETRY_DELAY,
                'backoff': cls.RETRY_BACKOFF
            },
            'api': {
                'request_timeout': cls.REQUEST_TIMEOUT
            },
            'proxy': {
                'enabled': cls.USE_PROXY,
                'urls': cls.PROXY_URLS
            },
            'prompts': cls.PROMPTS_CONFIG
        }

# 初始化配置
Config.load_config()

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_DIR / 'app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)