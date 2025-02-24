from pathlib import Path
import json

class Prompts:
    # 1. 大纲生成相关提示词
    OUTLINE_SYSTEM_ROLE = None
    OUTLINE_TECH_USER = None
    OUTLINE_SCORE_USER = None
    OUTLINE_GENERATE_USER = None

    # 2. 内容生成相关提示词
    CONTENT_SYSTEM_ROLE = None
    CONTENT_INIT_USER = None
    CONTENT_SECTION_USER = None

    @classmethod
    def load_prompts(cls):
        """从配置文件加载提示词模板"""
        config_file = Path(__file__).parent / "config.json"
        
        if not config_file.exists():
            raise FileNotFoundError("配置文件不存在")
            
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # 从配置中加载prompts部分
        prompts_config = config.get('prompts', {})
        
        # 加载outline相关提示词
        outline_config = prompts_config.get('outline', {})
        cls.OUTLINE_SYSTEM_ROLE = outline_config.get('system_role')
        cls.OUTLINE_TECH_USER = outline_config.get('tech_user')
        cls.OUTLINE_SCORE_USER = outline_config.get('score_user')
        cls.OUTLINE_GENERATE_USER = outline_config.get('generate_user')
        
        # 加载content相关提示词
        content_config = prompts_config.get('content', {})
        cls.CONTENT_SYSTEM_ROLE = content_config.get('system_role')
        cls.CONTENT_INIT_USER = content_config.get('init_user')
        cls.CONTENT_SECTION_USER = content_config.get('section_user')

# 初始化时自动加载提示词
Prompts.load_prompts()