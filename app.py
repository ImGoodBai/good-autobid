from quart import Quart, jsonify, request, render_template, send_file
from quart_cors import cors
from bidding_workflow import BiddingWorkflow
import logging
from config import Config
import json
from datetime import datetime
import os
import webbrowser
import asyncio

app = Quart(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 设置最大请求大小为16MB
app = cors(app, allow_origin="*", allow_methods=["GET", "POST"])  # 明确允许GET和POST方法
logger = logging.getLogger(__name__)

@app.route('/')
async def index():
    return await render_template('index.html', active_page='index')

@app.route('/generate_outline', methods=['POST', 'GET'])
async def generate_outline():
    try:
        # 获取请求数据 (make it optional)
        try:
            request_data = await request.get_json()
        except:
            request_data = {}
        
        async with BiddingWorkflow() as workflow:
            logger.info("开始生成大纲")
            
            # 加载输入文件
            logger.info("加载输入文件")
            workflow.load_input_files()
            
            # 生成大纲
            logger.info("生成大纲")
            outline_json = await workflow.generate_outline()
            if not outline_json:
                return jsonify({
                    "code": 1,
                    "message": "生成大纲失败",
                    "data": None
                }), 500
            
            # 解析大纲并转换为字符串格式
            outline_str = json.dumps({"outline": []})  # 这里替换为实际的大纲数据
            
            current_time = datetime.now().isoformat()
            
            response_data = {
                "code": 0,
                "message": "success",
                "data": {
                    "outline": outline_str,
                    "task_status": "completed",
                    "created_at": current_time,
                    "updated_at": current_time
                }
            }
            
            return jsonify(response_data)
            
    except Exception as e:
        logger.error(f"创建大纲时出错: {str(e)}", exc_info=True)
        return jsonify({
            "code": 1,
            "message": str(e),
            "data": None
        }), 500

@app.route('/generate_document', methods=['POST','GET'])
async def generate_document():
    workflow = BiddingWorkflow()
    try:
        # 加载输入文件
        workflow.load_input_files()
        
        # 加载大纲
        with open(Config.OUTLINE_DIR / 'outline.json', 'r', encoding='utf-8') as f:
            outline_dict = json.load(f)
            workflow.outline = workflow.parse_outline_json(outline_dict)
        
        # 生成完整内容
        success = await workflow.generate_full_content_async()
        if not success:
            return jsonify({"status": "error", "message": "生成文档失败"}), 500
        
        return jsonify({
            "status": "success",
            "message": "文档生成成功"
        })
        
    except Exception as e:
        logger.error(f"生成文档时出错: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        await workflow.llm_client.close()

@app.route('/show_outline', methods=['GET'])
async def show_outline():
    try:
        with open(Config.OUTLINE_DIR / 'outline.json', 'r', encoding='utf-8') as f:
            outline_content = json.load(f)
        return jsonify({
            "code": 0,
            "message": "success",
            "data": outline_content
        })
    except Exception as e:
        logger.error(f"读取outline.json时出错: {str(e)}", exc_info=True)
        return jsonify({
            "code": 1,
            "message": str(e),
            "data": None
        }), 500

@app.route('/show_document', methods=['GET'])
async def show_document():
    try:
        with open(Config.OUTPUT_DIR / 'content.md', 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({
            "code": 0,
            "message": "success",
            "data": content
        })
    except Exception as e:
        logger.error(f"读取content.md时出错: {str(e)}", exc_info=True)
        return jsonify({
            "code": 1,
            "message": str(e),
            "data": None
        }), 500

@app.route('/show_input', methods=['GET'])
async def show_input():
    try:
        score_path = Config.INPUT_DIR / 'score.md'
        tech_path = Config.INPUT_DIR / 'tech.md'
        
        score_content = ''
        tech_content = ''
        
        if score_path.exists():
            with open(score_path, 'r', encoding='utf-8') as f:
                score_content = f.read()
                
        if tech_path.exists():
            with open(tech_path, 'r', encoding='utf-8') as f:
                tech_content = f.read()
        
        return jsonify({
            "code": 0,
            "message": "success",
            "data": {
                "score_md": score_content,
                "tech_md": tech_content
            }
        })
    except Exception as e:
        logger.error(f"读取输入文件时出错: {str(e)}", exc_info=True)
        return jsonify({
            "code": 1,
            "message": str(e),
            "data": None
        }), 500

@app.route('/save_input', methods=['POST'])
async def save_input():
    try:
        request_data = await request.get_json()
        score_content = request_data.get('score_md', '')
        tech_content = request_data.get('tech_md', '')
        
        score_path = Config.INPUT_DIR / 'score.md'
        tech_path = Config.INPUT_DIR / 'tech.md'
        
        with open(score_path, 'w', encoding='utf-8') as f:
            f.write(score_content)
            
        with open(tech_path, 'w', encoding='utf-8') as f:
            f.write(tech_content)
        
        return jsonify({
            "code": 0,
            "message": "输入文件保存成功",
            "data": None
        })
    except Exception as e:
        logger.error(f"保存输入文件时出错: {str(e)}", exc_info=True)
        return jsonify({
            "code": 1,
            "message": str(e),
            "data": None
        }), 500

# 配置相关的路由
@app.route('/api/config', methods=['GET'])
def get_config():
    """获取当前配置"""
    return jsonify(Config.get_config())

@app.route('/api/config', methods=['POST'])
async def update_config():
    """更新配置"""
    try:
        new_config = await request.get_json()
        
        # 更新LLM配置
        if 'llm' in new_config:
            llm_config = new_config['llm']
            Config.LLM_API_KEY = llm_config.get('api_key', Config.LLM_API_KEY)
            Config.LLM_API_BASE = llm_config.get('api_base', Config.LLM_API_BASE)
            Config.LLM_MODEL = llm_config.get('model', Config.LLM_MODEL)
            Config.MAX_TOKENS = llm_config.get('max_tokens', Config.MAX_TOKENS)
            Config.TEMPERATURE = llm_config.get('temperature', Config.TEMPERATURE)
            Config.TOP_P = llm_config.get('top_p', Config.TOP_P)
            Config.TIMEOUT = llm_config.get('timeout', Config.TIMEOUT)
        
        # 更新重试配置
        if 'retry' in new_config:
            retry_config = new_config['retry']
            Config.MAX_RETRIES = retry_config.get('max_retries', Config.MAX_RETRIES)
            Config.RETRY_DELAY = retry_config.get('delay', Config.RETRY_DELAY)
            Config.RETRY_BACKOFF = retry_config.get('backoff', Config.RETRY_BACKOFF)
        
        # 更新API配置
        if 'api' in new_config:
            api_config = new_config['api']
            Config.REQUEST_TIMEOUT = api_config.get('request_timeout', Config.REQUEST_TIMEOUT)
        
        # 更新代理配置
        if 'proxy' in new_config:
            proxy_config = new_config['proxy']
            Config.USE_PROXY = proxy_config.get('enabled', Config.USE_PROXY)
            if 'urls' in proxy_config:
                Config.PROXY_URLS = proxy_config['urls']
        
        # 保存到配置文件
        Config.save_config()
        
        return jsonify({
            'status': 'success',
            'config': Config.get_config()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/config')
async def config_page():
    """配置页面"""
    return await render_template('config.html', active_page='config')

@app.route('/prompts')
async def prompts_page():
    """提示词配置页面"""
    return await render_template('prompts.html', active_page='prompts')

@app.route('/api/prompts/variables', methods=['GET'])
async def get_prompts():
    """获取提示词配置"""
    try:
        config = Config.get_config()
        prompts = config.get('prompts', {})
        # 将配置中的 prompts 部分转换为前端需要的格式
        variables = {
            'OUTLINE_SYSTEM_ROLE': prompts.get('outline', {}).get('system_role', ''),
            'OUTLINE_TECH_USER': prompts.get('outline', {}).get('tech_user', ''),
            'OUTLINE_SCORE_USER': prompts.get('outline', {}).get('score_user', ''),
            'OUTLINE_GENERATE_USER': prompts.get('outline', {}).get('generate_user', ''),
            'CONTENT_SYSTEM_ROLE': prompts.get('content', {}).get('system_role', ''),
            'CONTENT_INIT_USER': prompts.get('content', {}).get('init_user', ''),
            'CONTENT_SECTION_USER': prompts.get('content', {}).get('section_user', '')
        }
        return jsonify(variables)
    except Exception as e:
        logger.error(f"获取提示词时出错: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/prompts/variables', methods=['POST'])
async def save_prompts():
    """保存提示词配置"""
    try:
        data = await request.get_json()
        
        # 更新提示词配置
        Config.PROMPTS_CONFIG = {
            'outline': {
                'system_role': data.get('OUTLINE_SYSTEM_ROLE', ''),
                'tech_user': data.get('OUTLINE_TECH_USER', ''),
                'score_user': data.get('OUTLINE_SCORE_USER', ''),
                'generate_user': data.get('OUTLINE_GENERATE_USER', '')
            },
            'content': {
                'system_role': data.get('CONTENT_SYSTEM_ROLE', ''),
                'init_user': data.get('CONTENT_INIT_USER', ''),
                'section_user': data.get('CONTENT_SECTION_USER', '')
            }
        }
        
        # 保存配置
        Config.save_config()
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"保存提示词时出错: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/outline', methods=['GET'])
async def get_outline():
    try:
        outline_file = Config.OUTLINE_DIR / 'outline.json'
        if not outline_file.exists():
            return jsonify({"outline": []}), 200
            
        with open(outline_file, 'r', encoding='utf-8') as f:
            outline_data = json.load(f)
            
        return jsonify(outline_data)
    except Exception as e:
        logger.error(f"读取大纲时出错: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/save_outline', methods=['POST'])
async def save_outline():
    try:
        outline_data = await request.get_json()
        if not isinstance(outline_data, dict):
            return jsonify({"error": "Invalid outline format"}), 400

        # 确保输出目录存在
        os.makedirs(Config.OUTLINE_DIR, exist_ok=True)
        
        # 保存大纲文件
        outline_file = Config.OUTLINE_DIR / 'outline.json'
        with open(outline_file, 'w', encoding='utf-8') as f:
            json.dump(outline_data, f, ensure_ascii=False, indent=2)
            
        return jsonify({"message": "大纲保存成功"})
    except Exception as e:
        logger.error(f"保存大纲时出错: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/res/<path:filename>')
async def serve_resource(filename):
    try:
        return await send_file(f'res/{filename}')
    except Exception as e:
        logger.error(f"提供资源 {filename} 时出错: {e}")
        return "资源未找到", 404

if __name__ == '__main__':
    # 检查webui目录是否存在
    if not os.path.exists('templates'):
        logger.warning("未找到模板目录。")
    
    # 在服务器启动前打开浏览器
    @app.before_serving
    async def open_browser():
        webbrowser.open('http://127.0.0.1:5005')
    
    app.run(debug=False, use_reloader=False,port=5005)