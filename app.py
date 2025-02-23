from quart import Quart, jsonify, request, render_template
from quart_cors import cors
from bidding_workflow import BiddingWorkflow
import logging
from config import Config
import json
from datetime import datetime
import os

app = Quart(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 设置最大请求大小为16MB
app = cors(app, allow_origin="*", allow_methods=["GET", "POST"])  # 明确允许GET和POST方法
logger = logging.getLogger(__name__)

@app.route('/')
async def index():
    return await render_template('index.html')

@app.route('/generate_outline', methods=['POST', 'GET'])
async def generate_outline():
    try:
        # 获取请求数据 (make it optional)
        try:
            request_data = await request.get_json()
        except:
            request_data = {}
        
        async with BiddingWorkflow() as workflow:
            logger.info("Starting outline generation")
            
            # 加载输入文件
            logger.info("Loading input files")
            workflow.load_input_files()
            
            # 生成大纲
            logger.info("Generating outline")
            outline_json = await workflow.generate_outline()
            if not outline_json:
                return jsonify({
                    "code": 1,
                    "message": "Failed to generate outline",
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
        logger.error(f"Error in create_outline: {str(e)}", exc_info=True)
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
            return jsonify({"status": "error", "message": "Failed to generate content"}), 500
        
        return jsonify({
            "status": "success",
            "message": "Document generated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error generating document: {e}", exc_info=True)
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
        logger.error(f"Error reading outline.json: {str(e)}", exc_info=True)
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
        logger.error(f"Error reading content.md: {str(e)}", exc_info=True)
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
        logger.error(f"Error reading input files: {str(e)}", exc_info=True)
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
            "message": "Input files saved successfully",
            "data": None
        })
    except Exception as e:
        logger.error(f"Error saving input files: {str(e)}", exc_info=True)
        return jsonify({
            "code": 1,
            "message": str(e),
            "data": None
        }), 500

if __name__ == '__main__':
    # 检查webui目录是否存在
    if not os.path.exists('templates'):
        logger.warning("Templates directory not found.")
    app.run(host='0.0.0.0', debug=True, port=5001)