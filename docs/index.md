# Script-to-Storyboards

剧本转分镜自动化内容创作系统

## 项目概览

**Script-to-Storyboards** 是一个自动化内容创作流水线，能够将文本剧本转换为带有角色肖像和场景关键帧的可视化分镜。系统结合了大语言模型（Gemini 2.5 Pro）和文本生图模型（Qwen Image、Jimeng），生成结构化的分镜脚本和视觉资产，灵感来源于导演 Alejandro González Iñárritu 的电影风格。

## 核心功能

- **剧本解析**：自动提取角色、场景、对话等元素
- **分镜生成**：使用 LLM 生成详细的场景/镜头/子镜头三层结构
- **角色肖像**：为每个角色生成一致的视觉形象
- **场景关键帧**：为每个场景生成参考图像
- **Web 界面**：React + TypeScript 前端，方便非技术人员使用

## 技术栈

### 后端
- **FastAPI**：高性能异步 API 框架
- **PostgreSQL**：关系型数据库，存储剧本和分镜数据
- **Python 3.12**：AI 模型集成和数据处理

### 前端
- **React 18 + TypeScript**：类型安全的现代前端
- **Vite**：快速的构建工具
- **Zustand**：轻量级状态管理
- **Tailwind CSS**：实用优先的 CSS 框架

### AI 模型
- **Gemini 2.5 Pro**：分镜脚本生成
- **Qwen Image / Jimeng**：文本生成图像
- **RunningHub API**：统一的模型调用接口

### 部署
- **Docker**：容器化部署
- **Kubernetes (K3s)**：生产环境编排
- **GitHub Actions**：CI/CD 自动化

## 快速导航

### 在线文档和工具
- [Swagger UI](/api/docs) - 交互式 API 测试工具 (可直接调用接口)
- [ReDoc](/api/redoc) - 美观的 API 文档阅读界面 (类型定义展示更清晰)

### 开发文档
- [API 文档](api/README.md) - FastAPI 接口完整说明，包含 TypeScript 类型定义
- [前端架构](frontend/architecture.md) - React 组件结构和状态管理

### 部署文档
- [Docker 部署](DOCKER.md) - 本地开发和测试部署
- [K8s 快速开始](k8s/QUICKSTART.md) - Kubernetes 生产部署
- [远程部署](k8s/REMOTE-DEPLOY.md) - 一键部署到远程 K3s 服务器
- [Ingress 配置](k8s/INGRESS-GUIDE.md) - 配置外部访问
- [API 路由](k8s/API-ROUTING.md) - Nginx 路由配置

## 快速开始

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/jsongo/script-to-storyboards.git
cd script-to-storyboards

# 使用 Docker Compose 启动（推荐）
./docker/local-run.sh

# 访问应用
# 前端: http://localhost:5174
# API: http://localhost:8001
# API Docs: http://localhost:8001/api/docs
```

### 生产部署

```bash
# 本地 Kubernetes 部署
./docker/k8s/local-deploy.sh

# 远程服务器部署
./docker/k8s/deploy-to-remote.sh
```

## 项目结构

```
script-to-storyboards/
├── api/                    # FastAPI 后端
│   ├── routes/            # API 路由
│   ├── schemas.py         # Pydantic 数据模型
│   └── main.py            # 应用入口
├── frontend/              # React 前端
│   ├── src/
│   │   ├── api/          # API 客户端
│   │   ├── components/   # React 组件
│   │   ├── pages/        # 页面组件
│   │   └── store/        # Zustand 状态管理
│   └── package.json
├── models/                # AI 模型封装
│   ├── yizhan_llm.py     # LLM 客户端
│   ├── jimeng_t2i_RH.py  # Jimeng 文本生图
│   └── qwen_image_t2i_RH.py  # Qwen 文本生图
├── procedure/             # 核心工作流
│   ├── make_storyboards.py  # 生成分镜脚本
│   ├── generate_character_portraits.py  # 生成角色肖像提示词
│   └── make_portraits_from_t2i.py  # 生成角色图片
├── utils/                 # 工具函数
│   ├── database.py       # 数据库操作
│   └── config.py         # 配置管理
├── docker/                # Docker 和 K8s 配置
└── docs/                  # 项目文档
```

## 工作流程

1. **导入剧本** → 使用 `from_script_to_database.py` 将剧本导入数据库
2. **生成分镜** → 使用 Gemini 2.5 Pro 生成详细的分镜脚本
3. **提取角色** → 自动识别所有角色并生成肖像提示词
4. **提取场景** → 识别所有场景并生成关键帧提示词
5. **生成图片** → 使用文本生图模型批量生成角色和场景图片
6. **Web 查看** → 在 Web 界面查看和编辑分镜内容

## 配置要求

### 开发环境
- Python 3.12+
- Node.js 20+
- PostgreSQL 15+
- Docker & Docker Compose

### API 密钥
需要在 `utils/config.py` 中配置：
- `YIZHAN_API_CONFIG`：LLM API 密钥（Gemini、DeepSeek）
- `RUNNINGHUB_API_CONFIG`：RunningHub API 密钥（文本生图）

## 贡献指南

欢迎提交 Issue 和 Pull Request！

- 提交 PR 前请运行 `pre-commit` 检查
- 前端测试：`cd frontend && pnpm test:run`
- 代码格式化：`pre-commit run --all-files`

## 许可证

MIT License

## 联系方式

如有问题，请提交 [GitHub Issue](https://github.com/jsongo/script-to-storyboards/issues)
