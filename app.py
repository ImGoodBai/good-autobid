from quart import Quart, jsonify, request
from quart_cors import cors
from bidding_workflow import BiddingWorkflow
import logging
from config import Config
import json
from datetime import datetime

app = Quart(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 设置最大请求大小为16MB
app = cors(app, allow_origin="*", allow_methods=["GET", "POST"])  # 明确允许GET和POST方法
logger = logging.getLogger(__name__)


@app.route('/generate_outline', methods=['POST', 'GET'])
async def generate_outline():
    try:
        # 获取请求数据
        request_data = await request.get_json()
        
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)