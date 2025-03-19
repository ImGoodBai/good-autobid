/**
 * LLM API测试工具
 * 用于测试LLM API连接是否正常
 */

/**
 * 测试LLM API连接
 * 使用当前配置的API密钥、基础URL和模型进行测试
 */
async function testLLMAPI() {
    const testBtn = document.querySelector('button[onclick="testLLMAPI()"]');
    const resultSpan = document.getElementById('api-test-result');
    
    // 获取当前配置
    const apiKey = document.getElementById('llm_api_key').value;
    const apiBase = document.getElementById('llm_api_base').value;
    const model = document.getElementById('llm_model').value;
    
    if (!apiKey || !apiBase || !model) {
        toastr.error('请填写完整的API配置信息');
        return;
    }
    
    // 更改按钮状态
    testBtn.disabled = true;
    testBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 测试中...';
    resultSpan.textContent = '';
    
    try {
        // 构建请求数据
        const requestData = {
            model: model,
            messages: [
                {role: "system", content: "You are a helpful assistant."},
                {role: "user", content: "Hello, this is a test message. Please respond with 'API connection successful'."}
            ],
            temperature: 0.7,
            max_tokens: 50
        };
        
        // 构建请求URL
        let url = apiBase;
        if (!url.endsWith('/')) {
            url += '/';
        }
        url += 'chat/completions';
        
        // 发送请求
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`
            },
            body: JSON.stringify(requestData)
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.choices && data.choices.length > 0) {
                resultSpan.innerHTML = '<span class="text-success"><i class="bi bi-check-circle"></i> API连接成功</span>';
                toastr.success('API连接测试成功');
                
                // 显示模型响应
                const modelResponse = data.choices[0].message.content;
                console.log('模型响应:', modelResponse);
            } else {
                resultSpan.innerHTML = '<span class="text-warning"><i class="bi bi-exclamation-circle"></i> 收到响应但格式异常</span>';
                toastr.warning('收到响应但格式异常');
            }
        } else {
            const errorText = await response.text();
            resultSpan.innerHTML = '<span class="text-danger"><i class="bi bi-x-circle"></i> API连接失败</span>';
            toastr.error(`API连接失败: ${response.status} - ${errorText}`);
        }
    } catch (error) {
        console.error('测试API失败:', error);
        resultSpan.innerHTML = '<span class="text-danger"><i class="bi bi-x-circle"></i> 请求失败</span>';
        toastr.error(`测试API请求失败: ${error.message}`);
    } finally {
        // 恢复按钮状态
        testBtn.disabled = false;
        testBtn.innerHTML = '测试API连接';
    }
}

/**
 * 处理可能的CORS错误
 * 如果API不支持跨域请求，可以考虑使用代理或后端转发
 */
function handleCorsError(error) {
    console.error('CORS错误:', error);
    toastr.error('跨域请求被阻止，请检查API是否支持CORS或考虑使用代理');
}
