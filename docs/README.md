# 文档系统

本项目使用 [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) 构建项目文档。

## 本地预览

```bash
# 安装 mkdocs-material
pip install mkdocs-material

# 实时预览（自动重载）
mkdocs serve

# 访问 http://127.0.0.1:8000
```

## 构建文档

```bash
# 构建静态文档到 site/ 目录
mkdocs build
```

## 部署后访问

文档会在 Docker 构建时自动生成，并通过前端 Nginx 提供服务：

### MkDocs 项目文档

- **本地开发**: `mkdocs serve` 然后访问 http://127.0.0.1:8000
- **Docker 部署**: http://localhost:8866/docs/
- **K8s 部署**: http://<server-ip>/docs/

### API 接口文档（Swagger/OpenAPI）

- **本地开发**: http://localhost:8001/api/docs
- **Docker 部署**: http://localhost:8000/api/docs
- **K8s 部署**: http://<server-ip>/api/docs

## 文档结构

```
docs/
├── index.md              # 首页
├── api/
│   └── README.md         # API 文档
├── frontend/
│   └── architecture.md   # 前端架构
├── k8s/
│   ├── QUICKSTART.md     # K8s 快速开始
│   ├── REMOTE-DEPLOY.md  # 远程部署
│   ├── INGRESS-GUIDE.md  # Ingress 配置
│   ├── API-ROUTING.md    # API 路由
│   └── README.md         # K8s 概览
└── DOCKER.md             # Docker 部署
```

## 添加新文档

1. 在 `docs/` 目录下创建 `.md` 文件
2. 在 `mkdocs.yml` 的 `nav` 部分添加导航链接
3. 运行 `mkdocs build` 重新构建

## 主题特性

- 🌓 亮色/暗色主题切换
- 🔍 全文搜索
- 📱 响应式设计
- 💾 代码高亮和复制
- 🧭 自动目录导航
- 🌏 中文支持

## 自动部署

文档会在以下情况自动构建：

- **Docker 构建**: `./docker/local-run.sh --build`
- **K8s 部署**: `./docker/k8s/local-deploy.sh`
- **远程部署**: `./docker/k8s/deploy-to-remote.sh`

构建过程在 `docker/dockerfiles/frontend.Dockerfile` 中定义（多阶段构建）：

```dockerfile
# Documentation build stage
FROM python:3.12-alpine AS docs-builder

WORKDIR /docs-build

# Install mkdocs-material
RUN pip install --no-cache-dir mkdocs-material

# Copy documentation files from project root context
COPY docs ./docs
COPY mkdocs.yml .

# Build documentation
RUN mkdocs build

# Production stage
FROM nginx:alpine

# Copy built dist from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy documentation from docs-builder stage
COPY --from=docs-builder /docs-build/site /usr/share/nginx/html/docs
```

## 配置文件

主配置文件是项目根目录的 `mkdocs.yml`，包含：

- 站点元数据
- Material 主题配置
- 导航结构
- Markdown 扩展
- 搜索插件配置
