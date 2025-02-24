# 提示词变量管理页面设计方案

## 功能概述

提供一个Web界面用于管理和配置 prompts.py 中的提示词变量，包括查看、编辑和保存功能。

## 技术方案

### 1. 数据源

- 源文件：`prompts.py`
- 数据结构：Python类变量形式的提示词
- 当前提示词分类：
  - 大纲生成相关：OUTLINE_SYSTEM_ROLE, OUTLINE_TECH_USER, OUTLINE_SCORE_USER, OUTLINE_GENERATE_USER
  - 内容生成相关：CONTENT_SYSTEM_ROLE, CONTENT_INIT_USER, CONTENT_SECTION_USER

### 2. 页面设计

#### 布局
- 左侧：提示词变量列表
  - 按分类显示（大纲生成/内容生成）
  - 显示变量名称
  
- 右侧：编辑区域
  - 变量名称（只读）
  - 多行文本编辑器（用于编辑提示词内容）
  - 保存按钮

### 3. 后端实现

#### API接口
- GET `/api/prompts/variables` - 获取所有提示词变量
- GET `/api/prompts/variable/<name>` - 获取特定提示词变量内容
- POST `/api/prompts/variable/<name>` - 更新提示词变量内容

#### 文件处理
- 使用 Python AST 模块解析和修改 prompts.py
- 保持文件格式和注释不变
- 仅更新变量值

### 4. 前端实现

- 使用 CodeMirror 或 Monaco Editor 作为文本编辑器
- 支持语法高亮
- 自动保存功能
- 编辑历史记录

### 5. 安全措施

- 变量名不可修改，只能修改内容
- 保存前进行格式验证
- 自动备份 prompts.py
- 记录修改历史

## 实现步骤

1. 在 app.py 中添加新的路由 `/prompts`
2. 创建 templates/prompts.html 页面
3. 实现提示词变量的读取和更新API
4. 实现前端编辑器和交互逻辑
5. 添加到导航菜单

## 注意事项

1. 保持 prompts.py 文件的结构不变
2. 确保提示词格式符合要求
3. 避免意外修改其他代码部分
4. 定期备份提示词文件
