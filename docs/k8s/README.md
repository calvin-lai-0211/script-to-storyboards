# Kubernetes 部署文档

Script-to-Storyboards 的 Kubernetes 部署完整指南。

## 📚 文档导航

### 快速开始

- **[本地环境搭建](local-setup.md)** - 安装 k3d/k3s 和配置本地 K8s 集群
- **[本地部署](local-deployment.md)** - 在本地 K8s 环境部署应用
- **[远程部署](remote-deployment.md)** - 部署到生产环境 K3s 服务器

### 运维管理

- **[日常运维](operations.md)** - 查看日志、重启服务、扩缩容等常用操作
- **[故障排查](troubleshooting.md)** - 常见问题诊断和解决方案

## 🎯 快速链接

### 一键部署

```bash
# 本地 K8s 部署
cd docker/k8s
./local-deploy.sh

# 远程生产部署
./deploy-to-remote.sh
```

### K8s 架构

```
┌──────────────────────────────────────────────┐
│            Ingress (Port 80)                 │
│   - /        → Frontend Service              │
│   - /api/*   → API Service                   │
└──────────────────────────────────────────────┘
                      │
        ┌─────────────┴──────────────┐
        ▼                            ▼
┌───────────────┐            ┌──────────────┐
│   Frontend    │            │     API      │
│  Deployment   │            │  Deployment  │
│               │            │              │
│ - Nginx       │            │ - FastAPI    │
│ - React App   │            │ - Python 3.12│
│ - Replicas: 1 │            │ - Replicas: 1│
└───────────────┘            └──────────────┘
                                     │
                                     ▼
                             ┌──────────────┐
                             │    Redis     │
                             │  Deployment  │
                             │              │
                             │ - Session    │
                             │ - Replicas: 1│
                             └──────────────┘
```

## 📦 K8s 资源清单

| 文件 | 资源类型 | 说明 |
|------|---------|------|
| `api-deployment.yaml` | Deployment + Service | API 后端服务（本地开发） |
| `api-deployment.prod.yaml` | Deployment + Service | API 后端服务（生产环境） |
| `frontend-deployment.yaml` | Deployment + Service | Frontend 前端服务 |
| `redis-deployment.yaml` | Deployment + Service | Redis 会话存储 |
| `nginx-configmap.yaml` | ConfigMap | Nginx 配置文件 |
| `ingress.yaml` | Ingress | 统一入口和路由规则 |
| `k3d-config.yaml` | k3d 配置 | 本地集群创建配置 |

## 🚀 快速命令参考

### 查看状态
```bash
kubectl get all                          # 所有资源
kubectl get pods                         # Pod 列表
kubectl get svc                          # 服务列表
kubectl get ingress                      # Ingress 列表
```

### 查看日志
```bash
kubectl logs -f deployment/storyboard-api        # API 日志
kubectl logs -f deployment/storyboard-frontend   # Frontend 日志
kubectl logs -f deployment/storyboard-redis      # Redis 日志
```

### 重启服务
```bash
kubectl rollout restart deployment/storyboard-api
kubectl rollout restart deployment/storyboard-frontend
```

### 更新部署
```bash
cd docker/k8s
./update-api.sh          # 仅更新 API
./update-frontend.sh     # 仅更新 Frontend
./update-config.sh       # 仅更新配置
```

### 清理资源
```bash
./undeploy.sh            # 删除所有部署
k3d cluster delete calvin # 删除整个集群
```

## 🔧 环境要求

### 本地开发
- **kubectl**: K8s 命令行工具
- **k3d** (Mac/Windows): 本地 K8s 集群
- **Docker**: 容器运行时

### 生产环境
- **K3s**: 轻量级 K8s（已安装在服务器）
- **kubectl**: 本地通过 SSH 访问远程集群

## 📖 相关文档

- [开发入门指南](../dev/getting-started.md) - 所有开发模式对比
- [Docker Compose 部署](../../docker/docker-compose.md) - 本地容器化部署
- [Google OAuth 配置](../dev/google-oauth-authentication.md) - 认证配置

## ❓ 常见问题

**Q: 本地和生产环境有什么区别？**
A: 主要是环境变量不同：
- 本地: `API_BASE_URL=http://localhost:8080`, `ENV=development`
- 生产: `API_BASE_URL=https://videos.ethanlyn.com`, `ENV=production`

**Q: 如何在本地和生产之间切换？**
A: 使用不同的部署脚本和配置文件：
- 本地: `./local-deploy.sh` 使用 `api-deployment.yaml`
- 生产: `./deploy-to-remote.sh` 使用 `api-deployment.prod.yaml`

**Q: 需要手动管理镜像吗？**
A: 不需要，部署脚本会自动：
- 构建 Docker 镜像
- 导入到 K8s 集群（本地）或打包上传（远程）
- 应用配置并重启服务

**Q: 部署失败怎么办？**
A: 参考 [故障排查文档](troubleshooting.md) 查看常见问题和解决方案。
