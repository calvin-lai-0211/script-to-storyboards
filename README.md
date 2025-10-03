# Script-to-Storyboards: 剧本到分镜自动化流程

本项目是一个自动化的内容创作管线，旨在将文本剧本转换为包含角色肖像、场景关键帧和详细分镜的视觉故事板。通过结合大型语言模型（LLM）和图像生成模型，该项目实现了从剧本分析、资源生成到最终分镜输出的全流程自动化。

## ✨ 项目特性

### 核心功能

-   **自动化剧本分析**: 自动从剧本中提取剧集、角色、场景等关键信息
-   **LLM驱动的分镜生成**: 利用大型语言模型（Gemini 2.5 Pro）将剧本转化为结构化的、符合导演风格（例如：亚利桑德罗·冈萨雷斯·伊纳里图）的JSON格式分镜脚本
-   **角色肖像自动生成**: 分析剧本并为每个角色生成高质量的图像，支持 Qwen Image 和 Jimeng 模型
-   **场景关键帧自动生成**: 从分镜脚本中提取场景并生成关键帧图片
-   **道具图片生成**: 支持道具描述编辑和一键生成道具图片
-   **剧集记忆管理**: 自动生成和存储剧集摘要，支持跨集引用
-   **Google OAuth 认证**: 安全的用户登录系统，基于 Redis 会话管理

### 技术架构

-   **前端**: React 18 + TypeScript + Vite + Tailwind CSS 4
-   **后端**: FastAPI + Python
-   **数据库**: PostgreSQL + Redis
-   **AI模型**: Gemini 2.5 Pro (LLM) + Qwen/Jimeng (图像生成)
-   **部署**: Docker + Kubernetes

## 📁 项目结构

```
script-to-storyboards/
├── frontend/                   # React 前端应用
│   ├── src/
│   │   ├── api/               # API 层（请求去重、端点定义）
│   │   ├── store/             # Zustand 状态管理（6个 Store）
│   │   ├── pages/             # 页面组件
│   │   ├── components/        # 可复用组件
│   │   └── __tests__/         # 单元测试（54个测试）
│   ├── docs/                  # 前端文档
│   └── package.json
│
├── api/                        # FastAPI 后端服务
│   ├── main.py                # 应用入口
│   ├── routers/               # API 路由
│   └── requirements.txt
│
├── models/                     # AI 模型封装
│   ├── yizhan_llm.py          # LLM 客户端（Gemini、DeepSeek）
│   ├── jimeng_t2i_RH.py       # Jimeng 文生图
│   ├── qwen_image_t2i_RH.py   # Qwen 文生图
│   └── flux_kontext_img2img_RH.py
│
├── procedure/                  # 核心处理流程
│   ├── make_storyboards.py    # 生成分镜脚本
│   ├── generate_character_portraits.py
│   ├── generate_scene_definitions.py
│   ├── generate_memory_for_episodes.py
│   ├── make_portraits_from_t2i.py
│   └── generate_scene_images.py
│
├── utils/                      # 工具类
│   ├── config.py              # 配置管理
│   └── database.py            # 数据库操作
│
├── .githooks/                  # Git pre-commit hooks
├── docs/                       # 项目文档
│   ├── frontend/              # 前端架构文档
│   ├── api/                   # API 文档
│   ├── k8s/                   # K8s 部署文档
│   └── DOCKER.md
│
├── docker/                     # Docker 配置
├── k8s/                        # Kubernetes 配置
└── scripts/                    # 原始剧本文件
```

## 🚀 快速开始

### 前置要求

- Node.js 18+
- Python 3.10+
- PostgreSQL 14+
- Redis 6+ (用于会话管理)
- Docker (可选，用于容器化部署)

### 1. 克隆项目

```bash
git clone https://github.com/calvin-lai-0211/script-to-storyboards.git
cd script-to-storyboards
```

### 2. 配置环境

```bash
# 启动 Redis
redis-server

# 初始化数据库表
python utils/database.py
```

在 `utils/config.py` 中配置：
- 数据库连接信息
- Google OAuth 凭证（CLIENT_ID、CLIENT_SECRET）
- Redis 连接信息
- AI 模型 API Keys

### 3. 启动后端 API

```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

访问 API 文档：http://localhost:8001/api/docs

### 4. 启动前端

```bash
cd frontend
pnpm install

# 启用 Git hooks（推荐）
git config core.hooksPath .githooks

# 启动开发服务器
pnpm run dev
```

访问前端：http://localhost:5173

**首次访问需要 Google 登录**，系统会自动跳转到 OAuth 授权页面。

### 5. 运行测试

```bash
cd frontend

# 运行所有测试
pnpm test:run

# 类型检查
pnpm type-check

# Lint 检查
pnpm lint

# 格式化检查
pnpm pretty:check
```

## 📖 使用流程

### 完整工作流

1. **导入剧本** → 2. **生成分镜** → 3. **生成角色Prompt** → 4. **生成场景Prompt** → 5. **生成图片** → 6. **生成剧集记忆**

### 详细步骤

#### 步骤 1: 导入剧本

```bash
python from_script_to_database.py
```

将 `.txt` 格式的剧本导入数据库。

#### 步骤 2: 生成分镜脚本

```bash
python demo_make_storyboards_from_scripts.py
```

使用 LLM 生成结构化的分镜脚本（JSON 格式）。

#### 步骤 3: 生成角色肖像 Prompt

```bash
python demo_create_character_portraits.py
```

#### 步骤 4: 生成场景定义 Prompt

```bash
python demo_create_scene_definitions.py
```

#### 步骤 5: 生成视觉素材

```bash
# 生成角色肖像
python procedure/make_portraits_from_t2i.py "剧本名" 1 -m jimeng

# 生成场景关键帧
python procedure/generate_scene_images.py "剧本名" 1 -m qwen
```

#### 步骤 6: 生成剧集记忆

```bash
python procedure/generate_memory_for_episodes.py
```

生成的图片保存在 `images/剧本名/集数/` 目录。

## 🎨 前端功能

### 核心特性

- **🔐 Google 登录**: OAuth 2.0 认证，基于 Redis 会话管理
- **📝 剧本管理**: 查看所有剧集、原文内容
- **🎬 分镜浏览**: 层级化展示场景→镜头→子镜头
- **👤 角色资产**: 管理角色肖像和描述，支持编辑和生成图片
- **🎭 道具资产**: 管理道具图片，支持编辑描述和一键生成
- **🏞️ 场景资产**: 管理场景关键帧
- **🧠 剧集记忆**: 查看剧集摘要
- **🔄 智能缓存**: 双重缓存策略（请求去重 + Zustand Store）
- **📱 响应式设计**: 适配各种屏幕尺寸

### 技术亮点

- **请求去重**: 自动合并并发的相同 API 请求
- **状态持久化**: URL 参数保存 Tab 状态
- **手动刷新**: 每个 Tab 都有刷新按钮
- **类型安全**: 完整的 TypeScript 类型定义
- **测试覆盖**: 59 个单元测试，100% 通过率
- **代码质量**: Pre-commit hooks 自动检查（测试、类型检查、Lint）

详见：[前端开发文档](docs/frontend/README.md)

## 🔌 API 文档

### 快速访问

- **Swagger UI**: http://localhost:8001/api/docs
- **ReDoc**: http://localhost:8001/api/redoc

### 主要端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/user/google/login` | GET | Google OAuth 登录 |
| `/api/user/info` | GET | 获取当前用户信息 |
| `/api/scripts` | GET | 获取所有剧本 |
| `/api/scripts/{key}` | GET | 获取剧本详情 |
| `/api/storyboards/{key}` | GET | 获取分镜数据 |
| `/api/characters/all` | GET | 获取所有角色 |
| `/api/character/{id}/generate-image` | POST | 生成角色肖像 |
| `/api/props/all` | GET | 获取所有道具 |
| `/api/prop/{id}/generate-image` | POST | 生成道具图片 |
| `/api/scenes/all` | GET | 获取所有场景 |
| `/api/memory/{key}` | GET | 获取剧集摘要 |

**注意**: 除了 OAuth 相关端点外，所有 API 都需要登录认证。

详见：[API 文档](docs/api/README.md)

## 🐳 Docker 部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

详见：[Docker 部署文档](docs/DOCKER.md)

## ☸️ Kubernetes 部署

```bash
# 部署到 K8s 集群
kubectl apply -f k8s/

# 查看状态
kubectl get pods -n storyboards
```

详见：[K8s 部署文档](docs/k8s/README.md)

## 🧪 测试

### 前端测试

```bash
cd frontend

# 运行所有测试
pnpm test:run

# 测试 UI
pnpm test:ui

# 测试覆盖率
pnpm test:cov
```

**测试覆盖**:
- API 层: 33 个测试
- Store 层: 26 个测试
- 总计: 59 个测试 ✅

### 代码质量

项目使用 Git pre-commit hooks 确保代码质量：

```bash
# 启用 hooks
git config core.hooksPath .githooks
```

每次提交前自动运行：
1. 单元测试（59 个测试）
2. TypeScript 类型检查
3. ESLint 代码规范检查
4. Prettier 格式化检查

## 📚 文档

### 开发文档
- [快速开始](docs/dev/getting-started.md) - 4 种开发模式详解
- [Git Hooks & CI](docs/dev/git-hooks-and-ci.md) - 代码质量保障

### 前端文档
- [前端开发指南](docs/frontend/README.md)
- [项目结构](docs/frontend/project-structure.md)
- [状态管理](docs/frontend/state-management.md)
- [API 集成](docs/frontend/api-integration.md)
- [测试指南](docs/frontend/testing.md)

### 部署文档
- [K8s 部署](docs/k8s/README.md)
- [本地 K8s 设置](docs/k8s/local-setup.md)
- [远程部署](docs/k8s/remote-deployment.md)
- [运维手册](docs/k8s/operations.md)

### 其他
- [CLAUDE.md](CLAUDE.md) - AI 开发助手指南

## 🛠️ 技术栈

### 前端

- React 18
- TypeScript
- Vite 7
- Tailwind CSS 4
- React Router v7
- Zustand (状态管理)
- Vitest (测试)

### 后端

- FastAPI
- Python 3.10+
- PostgreSQL
- Redis (会话管理)
- Google OAuth 2.0

### AI 模型

- Gemini 2.5 Pro (LLM)
- Qwen Image (文生图)
- Jimeng (文生图)

### DevOps

- Docker & Docker Compose
- Kubernetes (k3d/k3s)
- GitHub Actions (CI/CD)
- Git Hooks (Pre-commit)

## 🔄 开发工作流

### Git 分支策略

- `main`: 生产环境
- `feat/*`: 功能分支
- `fix/*`: 修复分支

### 提交规范

使用 Conventional Commits：

```
feat: 添加新功能
fix: 修复 bug
docs: 更新文档
test: 添加测试
chore: 杂项改动
```

## 🤝 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feat/amazing-feature`)
3. 提交改动 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feat/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

- [Gemini API](https://ai.google.dev/)
- [RunningHub](https://runninghub.cn/) - 图像生成 API
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)

## 📮 联系方式

- 项目主页: https://github.com/calvin-lai-0211/script-to-storyboards
- 问题反馈: https://github.com/calvin-lai-0211/script-to-storyboards/issues

---

*本项目由 AI 辅助开发和优化。*
