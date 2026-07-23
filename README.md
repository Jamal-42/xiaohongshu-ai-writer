# AI 小红书文案生成器

一款基于通义千问大模型的小红书风格文案自动生成工具，输入关键词即可生成标题、正文和标签。

## 功能特性

- 多风格选择：种草推荐 / 产品测评 / 教程攻略 / 日常分享
- 语气调节：活泼俏皮 / 专业理性 / 温柔治愈
- Emoji 密度控制
- 文案长度可调
- 一键生成标题（3个备选）+ 正文 + 标签推荐
- 支持下载生成结果

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 获取 API Key

前往 [阿里云百炼平台](https://bailian.console.aliyun.com/) 注册并获取 API Key。

### 3. 运行应用

```bash
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`，在左侧输入 API Key 即可使用。

## 项目结构

```
xiaohongshu-ai-writer/
├── app.py              # 主程序
├── requirements.txt    # 依赖
├── README.md           # 说明文档
└── docs/
    └── 需求分析.md      # 需求分析文档
```

## 技术栈

- Python 3.8+
- Streamlit（Web UI 框架）
- DashScope（通义千问 API SDK）
- 模型：qwen-plus

## 作者

[你的名字]
