# Docker 部署方式

本目录包含两种 Docker 部署方式，根据需求选择：

## 📁 目录结构

```
docker/
├── compose/          # Docker Compose 部署
│   └── docker-compose.yml
├── k8s/              # Kubernetes (K3s) 部署
│   ├── local-deploy.sh
│   ├── package.sh
│   ├── deploy-to-remote.sh
│   └── *.yaml
└── dockerfiles/      # Dockerfile 定义
    ├── api.Dockerfile
    └── frontend.Dockerfile
```

## 🚀 快速开始

### 方式 1: Docker Compose

适合：本地开发、快速测试

```bash
# 方法 A: 使用便捷脚本
./docker/up.sh

# 方法 B: 进入 compose 目录
cd docker/compose
docker-compose up -d
```

访问：
- Frontend: http://localhost:8866
- API: http://localhost:8000

---

### 方式 2: Kubernetes (K3s)

适合：生产部署、集群环境

```bash
# 方法 A: 使用便捷脚本（交互式选择）
./docker/deploy-k8s.sh

# 方法 B: 本地 k3d (Mac)
cd docker/k8s
./local-deploy.sh

# 方法 C: 远程 K3s (Linux Server)
cd docker/k8s
./deploy-to-remote.sh
```

---

## 🎯 选择指南

| 场景 | 推荐方式 | 启动命令 |
|------|---------|----------|
| 本地开发测试 | Compose | `./docker/up.sh` |
| Mac 上 K8s | K3d | `cd docker/k8s && ./local-deploy.sh` |
| 远程服务器 | Remote K3s | `cd docker/k8s && ./deploy-to-remote.sh` |

## 📦 便捷入口

在 `docker/` 根目录提供的便捷脚本：

- **`up.sh`** - 启动 Compose 服务
- **`deploy-k8s.sh`** - 部署到 K8s（交互式）

## 🔧 配置说明

### 环境变量

```bash
# 前端 API URL（在 docker-compose.yml 中配置）
VITE_API_BASE_URL=http://localhost:8000
```

### 端口映射

| 服务 | 容器端口 | 宿主端口 |
|------|----------|----------|
| API | 8000 | 8000 |
| Frontend | 80 | 8866 |

### 数据卷（开发模式）

开发时自动挂载：
- `api/` → `/app/api`
- `utils/` → `/app/utils`
- `models/` → `/app/models`
- `procedure/` → `/app/procedure`

生产部署时注释掉 volumes 配置。

## 📚 完整文档

- [Docker 部署指南](../docs/DOCKER.md)
- [K8s 快速开始](../docs/QUICKSTART.md)
- [远程部署指南](../docs/REMOTE-DEPLOY.md)

## ❓ 常见问题

### Q: 如何切换部署方式？

停止当前方式后直接启动新方式即可：
```bash
# 停止 Compose
docker-compose down

# 切换到 K8s
cd docker/k8s && ./deploy.sh
```

### Q: 镜像在哪里？

- 本地构建的镜像存在 Docker 本地
- K8s 部署会导入到 k3s/k3d 的镜像存储

### Q: 如何查看日志？

```bash
# Compose
docker-compose logs -f api

# K8s
kubectl logs -f deployment/storyboard-api
```

### Q: 如何更新部署？

```bash
# Compose
docker-compose pull
docker-compose up -d

# K8s
cd docker/k8s && ./deploy.sh  # 会自动更新
```
