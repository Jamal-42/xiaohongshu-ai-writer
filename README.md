# 📝 AI 小红书文案生成器

> 基于通义千问大模型 + Agent 多轮迭代架构的小红书爆款文案创作工具。

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.37-red)
![LLM](https://img.shields.io/badge/LLM-通义千问-orange)

## 🎯 产品定位

小红书创作者面临日更压力大、平台风格难把控、标题标签试错成本高等痛点。本工具通过 Agent 架构实现"检索爆款案例 → 生成初稿 → 自动审核 → 精修输出"的智能创作流程。

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🔍 爆款案例检索 | 根据输入主题自动匹配最相关的高互动案例作为参考 |
| 🤖 Agent 多轮迭代 | 生成→评分→审稿→精修，自动优化薄弱环节 |
| 📝 流式文案输出 | 实时展示 AI 思考过程和最终文案 |
| 📊 规则评分引擎 | 5维度量化质量（标题/密度/情绪/互动/适配） |
| 💬 个性化学习 | 用户反馈影响后续生成，越用越懂你 |
| 💾 历史记录 | SQLite 持久化，可查看之前生成的文案 |

## 🎨 创作参数

- **6种文案风格**：种草推荐 / 产品测评 / 教程攻略 / 日常分享 / 避雷吐槽 / 好物合集
- **5种语气调性**：活泼俏皮 / 专业理性 / 温柔治愈 / 犀利直白 / 幽默搞笑
- **4种目标受众**：18-25岁学生党 / 25-30岁职场新人 / 30-35岁精致妈妈 / 泛人群
- **Emoji密度**：5级可调
- **文案长度**：短(100-200字) / 中(200-400字) / 长(400-600字)

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/Jamal-42/xiaohongshu-ai-writer.git
cd xiaohongshu-ai-writer
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

前往 [阿里云百炼平台](https://bailian.console.aliyun.com/) 获取 API Key，然后在项目根目录创建 `.env` 文件：

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

### 4. 运行应用

```bash
streamlit run app.py
```

浏览器自动打开 `http://localhost:8501`，输入关键词即可开始创作。

## 📁 项目结构

```
xiaohongshu-ai-writer/
├── app.py                 # 主程序（Agent引擎 + UI）
├── requirements.txt       # Python依赖
├── .env.example           # API Key 配置模板
├── .gitignore
├── data/
│   └── trending_posts.json   # 爆款案例库（10条真实数据）
└── docs/
    ├── 需求分析.md            # 背景、用户画像、功能拆解
    ├── AI研发过程.md          # Prompt迭代记录 + AI协作过程（重点）
    └── 测试优化记录.md        # 测试用例、问题记录、改进方案
```

## 🧠 技术架构

```
用户输入 → 案例库检索(相关度匹配) → 动态Prompt构建 → Round1:生成初稿
                                                         ↓
用户反馈 → SQLite存储 → 偏好学习                  Round2:规则评分+AI审稿
                                                         ↓
                                              Round3:精修输出(流式展示)
```

## 🛠️ 技术栈

| 组件 | 选型 | 说明 |
|------|------|------|
| 后端语言 | Python 3.8+ | 主力开发语言 |
| Web框架 | Streamlit 1.37 | 数据应用UI框架 |
| 大模型 | 通义千问 qwen-plus | 中文表现优秀 |
| API SDK | DashScope 1.20 | 通义千问官方SDK |
| 数据库 | SQLite | 轻量持久化（历史/反馈/偏好） |
| 数据层 | JSON案例库 | 10条分类爆款案例 |

## 📄 文档

| 文档 | 内容 |
|------|------|
| [需求分析](docs/需求分析.md) | 背景、用户画像、功能拆解、非功能需求 |
| [AI研发过程](docs/AI研发过程.md) | Prompt V1→V4 完整迭代记录、AI协作节点、技术架构演进 |
| [测试优化记录](docs/测试优化记录.md) | 测试用例、问题发现、改进方案、V3深度重构 |

## 作者

Jamal-42
