# Autobid

## 简介

本项目旨在自动化生成投标文件，通过集成大模型来快速生成符合招标要求的技术文档和评分标准。

这个项目主要是应付八股文的写作，几分钟即可生成10万字技术文档。非常节省时间。


## 运行环境

- Python 3.x
- Flask
- 大模型API（推荐使用OpenRouter的API）

## 安装与配置

1. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```

2. **准备输入文件**

   在 `bidding/inputs/` 目录下准备以下文件：

   - `tech.md`：将招标文件的技术要求手动复制粘贴到这里。
   - `score.md`：将招标文件的评分标准手动复制粘贴到这里。

3. **配置大模型API**

   本项目推荐使用OpenRouter的API，因其支持Gemini FLash模型，生成速度快且内容信息密度高。请按照以下步骤配置：

   - 注册OpenRouter账户并获取API Key。
   - 将API Key填入 `config.py` 文件的相应位置。

## 运行程序

1. **启动Flask服务器**

   ```bash
   python app.py
   ```

   服务器默认运行在 `http://localhost:5000`。

2. **生成投标文件**

   生成投标文件分为两个步骤：生成大纲和生成完整文档。

   - **生成大纲**

     ```bash
     curl -X POST http://localhost:5000/generate_outline
     ```

     此操作会：
     - 读取 `tech.md` 和 `score.md` 文件。
     - 调用大模型生成大纲。
     - 将大纲保存到 `outputs/outline.json` 和 `outputs/outline.md`。

   - **生成完整文档**

     ```bash
     curl -X POST http://localhost:5000/generate_document
     ```

     此操作会：
     - 读取已生成的大纲。
     - 生成指定章节的内容。
     - 保存到 `outputs/content/` 目录。

## 实测

以下为作者实测数据：

a. 生成大纲一般在30s-1min以内；

b. 生成10万+文字的完整文档，用时约220s;

c. 以上单次任务完成，消费Gemini约0.09美元。

## 实现思路

本项目主要核心是`prompts.py`中几个prompt的构造，简单说下过程：

1、首先是让大模型根据评分标准和技术要求，生成一篇符合要求的大纲，区分了system和user来做
2、生成详细章节内容时候，单独开一个上下文窗口，预置一个system role，然后通过user不断的提交每个章节大纲、content summary来确保生成内容在边界范围内。

其次还有文档章节生成、全部拼接以及同一时间多次请求的工程上的考虑和处理

注：本项目是一个粗暴实现，个人本地可以玩玩，也可以应付八股文的投标文件写作，如果是正式投标文件，还是需要谨慎对待；

项目也还有很多细节没时间充分打磨，可以按我这个思路为引子，自己在完成一个独立的投标文件撰写工具

## 贡献

欢迎提交Issue和Pull Request来改进本项目。

