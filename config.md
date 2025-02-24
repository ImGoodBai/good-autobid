# 配置系统设计方案

## 1. 设计目标

1. 将配置从Python代码迁移到JSON文件，便于动态修改
2. 保持现有Config类的所有变量名和接口不变，确保兼容性
3. 添加Web界面用于查看和修改配置

## 2. 配置文件设计

### 2.1 JSON配置文件结构 (config.json)
```json
{
    "llm": {
        "api_key": "sk-xxxxx",
        "api_base": "https://openrouter.ai/api/v1",
        "model": "google/gemini-2.0-flash-lite-preview-02-05:free",
        "max_tokens": 8192,
        "temperature": 0.7,
        "top_p": 0.1,
        "timeout": 30
    },
    "retry": {
        "max_retries": 3,
        "delay": 2
    },
    "api": {
        "request_timeout": 30
    },
    "proxy": {
        "enabled": false,
        "urls": {
            "http": "http://127.0.0.1:33210",
            "https": "http://127.0.0.1:33210"
        }
    }
}
```

### 2.2 Config类设计
```python
class Config:
    # 重要：类变量只声明不赋值，所有配置值从配置文件加载
    LLM_API_KEY = None
    LLM_API_BASE = None
    LLM_MODEL = None
    # ...

    @classmethod
    def load_config(cls):
        # 从配置文件加载所有配置值
        # 如果配置文件不存在，创建默认配置文件
        pass

    @classmethod
    def save_config(cls):
        # 保存当前配置到配置文件
        pass
```

#### 设计要点
1. 配置驱动原则：
   - 所有配置值必须从配置文件读取，而不是硬编码在代码中
   - 类变量只用于声明，不应该包含默认值
   - 默认值应该写在配置文件中，而不是代码里

2. 配置加载流程：
   - 程序启动时，首先检查配置文件是否存在
   - 如果不存在，创建包含默认值的配置文件
   - 加载配置文件的值到类变量中

3. 配置更新流程：
   - 通过API或页面更新配置时，先更新配置文件
   - 然后重新加载配置到类变量中

## 3. API接口设计

### 3.1 获取配置
```
GET /api/config
返回：当前配置信息
```

### 3.2 更新配置
```
POST /api/config
请求体：要更新的配置项
返回：更新后的配置
```

## 4. 前端界面设计

### 4.1 配置页面布局
- LLM配置区域
  - API密钥（带掩码显示）
  - API基础URL
  - 模型选择
  - 其他LLM参数
- 重试配置区域
- API配置区域
- 代理配置区域

### 4.2 界面功能
- 配置项编辑
- 保存按钮
- 重置按钮
- 配置修改状态提示

## 5. 实现步骤

1. 创建config.json，迁移现有配置
2. 修改Config类实现JSON配置的读写
3. 添加配置相关的API路由
4. 实现配置页面
5. 添加前端交互逻辑
