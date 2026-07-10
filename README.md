# LangChain Chat

> 基于 LangChain 的多轮会话系统（教学项目）

一个以学习企业级 Python 开发流程为目标的项目：从零开始，按步骤搭建一个具备多轮对话、用户管理、会话管理、预设系统、可插拔存储的多功能 AI 对话终端应用。每一步都产出可运行、可验证的最小可用产品（MVP）。

## 项目特性

- 基于 LangChain：使用 langchain 与 langchain-openai 构建，兼容所有 OpenAI 接口格式的模型。
- 多轮对话：基于 Memory 机制保持上下文连贯，逐 token 流式输出。
- 用户管理：多用户隔离，数据互不可见。
- 预设系统：内置角色预设加用户自定义预设。
- 可插拔存储：SQLite、MySQL、文件三种后端，配置文件一键切换。
- 全链路异步：LLM 调用、IO、数据库全部 async/await。
- 教学导向：按 3W1H 框架讲解，每步 Git commit 加 tag 可回退。

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.12（要求 3.10 及以上） |
| LLM 框架 | langchain、langchain-openai |
| 异步数据库 | aiosqlite、aiomysql |
| TUI 终端 | rich、prompt_toolkit |
| 配置校验 | pydantic、pydantic-settings |
| 包管理 | uv |
| 测试 | pytest、pytest-asyncio |
| 代码质量 | ruff |

## 目录结构

langchain-chat/
├── .env.example            环境变量模板（复制为 .env 后填写真实值）
├── .gitignore              Git 忽略规则
├── config.yaml             全局业务配置
├── config/
│   ├── presets.yaml        系统内置预设（角色定义）
│   └── logging.yaml        日志配置
├── pyproject.toml          项目元数据与依赖
├── data/                   运行时数据（gitignore，自动创建）
├── src/                    源码
│   └── main.py             程序入口
├── docs/                   项目文档
└── README.md               本文件

## 快速开始

1. 环境要求：Python 3.12（要求 3.10 及以上）、uv。
2. 检查 uv：`uv --version`。
3. 克隆并配置：

```bash
git clone <仓库地址>
cd langchain-chat
copy .env.example .env
编辑 .env，填入 API_BASE_URL、API_KEY、MODEL_NAME。
```

4. 安装依赖并运行：

```bash
uv sync
uv run python src/main.py
```
