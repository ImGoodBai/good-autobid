# 新增查询接口规范

## 1. 查询大纲接口

### 接口信息
- **路径**: `/query_outline`
- **方法**: GET
- **描述**: 获取已生成的投标文档大纲

### 请求参数
- **task_id**: string (必填)
  - 任务ID，用于标识特定的生成任务

### 响应格式
```json
{
    "code": 0,           // 状态码：0-成功，非0-失败
    "message": "string", // 状态信息
    "data": {
        "outline": "{\n    \"outline\": []\n}",     // 大纲数据，JSON格式
        "task_status": "string",  // 任务状态：pending/running/completed/failed
        "created_at": "string",   // 创建时间
        "updated_at": "string"    // 更新时间
    }
}
```

## 2. 查询文档内容接口

### 接口信息
- **路径**: `/query_document`
- **方法**: GET
- **描述**: 获取已生成的完整投标文档内容

### 请求参数
- **task_id**: string (必填)
  - 任务ID，用于标识特定的生成任务
- **format**: string (可选)
  - 文档格式，支持：text/html/markdown
  - 默认：text

### 响应格式
```json
{
    "code": 0,           // 状态码：0-成功，非0-失败
    "message": "string", // 状态信息
    "data": {
        "content": "string",      // 文档完整内容
        "format": "string",       // 返回的格式
        "task_status": "string",  // 任务状态：pending/running/completed/failed
        "created_at": "string",   // 创建时间
        "updated_at": "string",   // 更新时间
        "word_count": number      // 文档字数
    }
}
```

## 3. 生成大纲接口

### 接口信息
- **路径**: `/generate_outline`
- **方法**: POST
- **描述**: 生成投标文档大纲

### 响应格式
```json
{
    "status": "success",
    "outline": {
        // Outline data
    }
}
```

## 4. 创建大纲（V1）接口

### 接口信息
- **路径**: `/api/v1/outline`
- **方法**: POST
- **描述**: 生成投标文档大纲（V1）

### 响应格式
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "outline": "outline_json_string",
        "task_status": "completed",
        "created_at": "timestamp",
        "updated_at": "timestamp"
    }
}
```

## 5. 生成内容接口

### 接口信息
- **路径**: `/generate_content`
- **方法**: POST
- **描述**: 生成投标文档内容

### 响应格式
```json
{
    "status": "success"
}
```

## 6. 生成文档接口

### 接口信息
- **路径**: `/generate_document`
- **方法**: POST
- **描述**: 生成投标文档

### 响应格式
```json
{
    "status": "success",
    "message": "Document generated successfully"
}
```

## 错误码说明

- 0: 成功
- 1001: 任务不存在
- 1002: 任务尚未完成
- 1003: 格式不支持
- 2001: 系统内部错误

## 注意事项

1. 两个接口都支持异步任务查询，可以通过task_status字段判断任务状态
2. 当任务状态为pending或running时，返回相应的状态信息
3. 文档内容接口支持多种格式输出，方便不同场景使用
4. 所有时间字段均使用ISO 8601格式
