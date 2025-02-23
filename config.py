from pathlib import Path
import logging

class Config:
    BASE_DIR = Path(__file__).parent  # 修改为 bidding 目录
    
    # 输入输出路径配置
    INPUT_DIR = BASE_DIR / "inputs"  # bidding/inputs
    OUTPUT_DIR = BASE_DIR / "outputs"  # bidding/outputs
    OUTLINE_DIR = OUTPUT_DIR / "outline"  # bidding/outputs/outline
    LOG_DIR = BASE_DIR / "logs"  # bidding/logs
    
    # LLM 配置
    LLM_API_KEY = "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"
    LLM_API_BASE = "https://openrouter.ai/api/v1"
    LLM_MODEL = "google/gemini-2.0-flash-lite-preview-02-05:free"
    
    MAX_RETRIES = 3
    MAX_TOKENS = 8192
    TEMPERATURE = 0.7
    TOP_P = 0.1
    TIMEOUT = 30
    
    # 重试配置
    RETRY_DELAY = 2
    RETRY_BACKOFF = 1.5
    
    # API 配置
    REQUEST_TIMEOUT = 30
    
    # 代理配置
    USE_PROXY = False  # 是否使用代理
    PROXY_URLS = {
        'http': "http://127.0.0.1:33210",
        'https': "http://127.0.0.1:33210"  # HTTPS 也使用 HTTP 代理
    }

# 修改日志级别为 DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_DIR / 'app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
) 