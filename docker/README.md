# Docker 部署

> 📚 **完整文档**: 查看 [docs/DOCKER.md](../docs/DOCKER.md) 获取详细部署指南

本目录包含 Docker Compose 和 Kubernetes 两种部署方式。

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
# 🔄 更新并重新部署（最常用）
./docker/local-run.sh --build

# 🚀 不加编译的部署（正常用不到）
./docker/local-run.sh

# 📊 查看日志
docker-compose -f docker/docker-compose.yml logs -f

# 🛑 停止服务
docker-compose -f docker/docker-compose.yml down
```

访问：

- Frontend: http://localhost:8866
- API: http://localhost:8000

---

### 方式 2: Kubernetes (K3s)

适合：生产部署、集群环境，本地如果有 k8s 的环境也可以用这个，选本地即可

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

运行在 80 端口。如果是在 mac os 上运行，需要加个 port-forward:

```bash
kubectl port-forward -n kube-system service/traefik 8080:80
```

这样就可以在本地的 8080 端口上访问。

---

## 🎯 选择指南

| 场景         | 推荐方式   | 启动命令                                 |
| ------------ | ---------- | ---------------------------------------- |
| 本地开发测试 | Compose    | `./docker/local-run.sh`                  |
| Mac 上 K8s   | K3d        | `cd docker/k8s && ./local-deploy.sh`     |
| 远程服务器   | Remote K3s | `cd docker/k8s && ./deploy-to-remote.sh` |

## 📦 便捷入口

在 `docker/` 根目录提供的便捷脚本：

- **`local-run.sh`** - 启动 Compose 服务
- **`deploy-k8s.sh`** - 部署到 K8s（交互式）

## 🔧 配置说明

### 环境变量

```bash
# 前端 API URL（在 docker-compose.yml 中配置）
VITE_API_BASE_URL=http://localhost:8000
```

### 端口映射

| 服务     | 容器端口 | 宿主端口 |
| -------- | -------- | -------- |
| API      | 8000     | 8000     |
| Frontend | 80       | 8866     |

### 数据卷（开发模式）

开发时自动挂载：

- `api/` → `/app/api`
- `utils/` → `/app/utils`
- `models/` → `/app/models`
- `procedure/` → `/app/procedure`

生产部署时注释掉 volumes 配置。

## 📚 完整文档

- [Docker Compose 部署](../docs/DOCKER.md) - 详细的 Docker Compose 配置和使用
- [K8s 快速开始](../docs/k8s/QUICKSTART.md) - 本地 K3s/K3d 部署
- [K8s 远程部署](../docs/k8s/REMOTE-DEPLOY.md) - 远程服务器部署
- [Ingress 配置](../docs/k8s/INGRESS-GUIDE.md) - 外部访问配置
- [API 路由](../docs/k8s/API-ROUTING.md) - Nginx 路由配置

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

**重要：代码更新后需要重新构建镜像！**

```bash
# Compose - 方法 1（推荐）
./docker/local-run.sh --build

# Compose - 方法 2
cd docker
docker-compose up -d --build

# K8s - 本地 k3d/k3s
cd docker/k8s
./local-deploy.sh  # 会自动构建并导入新镜像

# K8s - 远程服务器
cd docker/k8s
./deploy-to-remote.sh  # 会自动构建并传输新镜像
```

**常见错误：**

- ❌ 只运行 `./docker/local-run.sh` → 不会更新镜像
- ✅ 运行 `./docker/local-run.sh --build` → 重新构建镜像
