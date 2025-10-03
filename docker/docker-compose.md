# Docker Compose 部署指南

本指南介绍如何使用 Docker Compose 部署 Script-to-Storyboards 应用。

## 前置要求

- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB+ 可用内存

## 快速开始

### 一键部署

```bash
# 构建并启动所有服务
./docker/local-run.sh --build

# 访问应用
# - 前端: http://localhost:8866
# - API: http://localhost:8000
# - API 文档: http://localhost:8000/api/docs
```

### 分步部署

```bash
# 1. 进入 compose 目录
cd docker/compose

# 2. 构建镜像
docker-compose build

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f

# 5. 停止服务
docker-compose down
```

## 架构

```
┌─────────────────┐      ┌──────────────────┐
│   Frontend      │      │       API        │
│   (Nginx)       │─────▶│    (FastAPI)     │
│   Port 8866     │      │    Port 8000     │
│                 │      │                  │
│ - React App     │      │ - REST API       │
│ - MkDocs Docs   │      │ - Background     │
│   at /docs      │      │   Processing     │
└─────────────────┘      └──────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   PostgreSQL    │
                         │    (External)   │
                         │                 │
                         │ DB: scripts     │
                         │     storyboards │
                         │     characters  │
                         └─────────────────┘
```

## 端口映射

| 服务     | 容器端口 | 宿主端口 | 说明                     |
| -------- | -------- | -------- | ------------------------ |
| Frontend | 80       | 8866     | React 前端 + MkDocs 文档 |
| API      | 8000     | 8000     | FastAPI 后端             |

## 环境配置

### API 环境变量

API 服务使用 `utils/config.py` 中的配置。如需覆盖，可在 `docker-compose.yml` 中添加：

```yaml
services:
  api:
    environment:
      - PYTHONUNBUFFERED=1
      # 数据库配置（可选覆盖）
      - DB_HOST=localhost
      - DB_NAME=your_database
      - DB_USER=your_user
      - DB_PASSWORD=your_password
```

### 前端环境变量

前端在构建时通过 `docker-compose.yml` 的 `args` 配置 API URL：

```yaml
services:
  frontend:
    build:
      args:
        - VITE_API_BASE_URL=http://localhost:8000
```

**不同环境的配置**：

- **本地开发**: `http://localhost:8000`
- **Docker 部署**: `http://localhost:8000`
- **K8s 部署**: `""` (使用相对路径)

## 数据卷挂载

### 开发模式（默认）

开发时自动挂载代码目录，支持热重载：

```yaml
volumes:
  - ../../api:/app/api
  - ../../utils:/app/utils
  - ../../models:/app/models
  - ../../procedure:/app/procedure
```

### 生产模式

生产部署时注释掉 `volumes` 配置，使用容器内部的代码。

## 常用命令

### 服务管理

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose stop

# 重启服务
docker-compose restart

# 删除服务（保留数据）
docker-compose down

# 删除服务和数据
docker-compose down -v
```

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f api
docker-compose logs -f frontend

# 查看最近 100 行日志
docker-compose logs --tail=100 api
```

### 进入容器

```bash
# 进入 API 容器
docker-compose exec api bash

# 进入 Frontend 容器
docker-compose exec frontend sh
```

### 重新构建

```bash
# 重新构建并启动（推荐）
./docker/local-run.sh --build

# 或者手动重建
docker-compose build --no-cache
docker-compose up -d
```

## 更新部署

**重要**: 代码更新后必须重新构建镜像！

```bash
# 方法 1: 使用便捷脚本（推荐）
./docker/local-run.sh --build

# 方法 2: 手动重建
cd docker/compose
docker-compose down
docker-compose build
docker-compose up -d

# 方法 3: 在线更新（不停机）
docker-compose up -d --build
```

## 健康检查

### API 健康检查

```bash
# 检查 API 是否正常运行
curl http://localhost:8000/health

# 预期响应
{"status":"ok"}
```

### Frontend 健康检查

```bash
# 检查前端是否正常运行
curl http://localhost:8866/health

# 预期响应
healthy
```

### 查看容器状态

```bash
docker-compose ps

# 预期输出（健康状态）
NAME                IMAGE                                    STATUS
storyboard-api      script-to-storyboards-api:latest        Up (healthy)
storyboard-frontend script-to-storyboards-frontend:latest   Up (healthy)
```

## 故障排查

### 容器无法启动

```bash
# 查看容器日志
docker-compose logs api

# 检查容器状态
docker-compose ps

# 重新构建并启动
docker-compose down
docker-compose up -d --build
```

### API 无法连接数据库

检查 `utils/config.py` 中的数据库配置：

```python
DB_CONFIG = {
    "host": "localhost",  # 确保数据库可访问
    "port": 5432,
    "database": "your_db",
    "user": "your_user",
    "password": "your_password"
}
```

### 前端无法访问 API

检查 `docker-compose.yml` 中的 `VITE_API_BASE_URL` 配置：

```yaml
args:
  - VITE_API_BASE_URL=http://localhost:8000  # 确保端口正确
```

### 磁盘空间不足

清理未使用的 Docker 资源：

```bash
# 清理停止的容器
docker container prune

# 清理未使用的镜像
docker image prune -a

# 清理所有未使用资源（谨慎使用）
docker system prune -a
```

## 性能优化

### 构建缓存

使用 BuildKit 加速构建：

```bash
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
docker-compose build
```

### 资源限制

在 `docker-compose.yml` 中设置资源限制：

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## 安全建议

1. **生产环境不要挂载代码目录**（注释掉 volumes）
2. **使用环境变量管理敏感信息**（不要硬编码）
3. **定期更新基础镜像**
4. **限制容器权限**（避免使用 root）
5. **配置防火墙**（只开放必要端口）

## 下一步

- [Kubernetes 部署](k8s/QUICKSTART.md) - 生产环境推荐
- [API 文档](api/README.md) - 查看完整 API 接口
- [前端架构](frontend/architecture.md) - 了解前端设计

## 参考链接

- [Docker Compose 官方文档](https://docs.docker.com/compose/)
- [FastAPI 部署指南](https://fastapi.tiangolo.com/deployment/docker/)
- [Nginx 配置参考](https://nginx.org/en/docs/)
