# 本地 K8s 部署指南

本文档介绍如何将 Script-to-Storyboards 应用部署到本地 Kubernetes 集群。

## 目录

- [前置要求](#前置要求)
- [自动部署（推荐）](#自动部署推荐)
- [手动部署](#手动部署)
- [访问应用](#访问应用)
- [K8s架构说明](#k8s架构说明)
- [下一步](#下一步)

---

## 前置要求

在开始部署前，请确保：

1. 已完成[本地 K8s 环境搭建](local-setup.md)
2. 已启动 K8s 集群（k3d 或 k3s）
3. kubectl 可以正常连接到集群

验证环境：

```bash
# 检查集群状态
kubectl cluster-info

# 查看节点
kubectl get nodes
```

---

## 自动部署（推荐）

项目提供了一键部署脚本，会自动完成以下步骤：
1. 构建 Docker 镜像
2. 导入镜像到 K8s 集群
3. 部署 Redis、API、Frontend
4. 配置 Nginx ConfigMap
5. 可选部署 Ingress（80端口访问）

```bash
cd docker/k8s
./local-deploy.sh
```

### 脚本执行流程

1. **检查环境**：确认 kubectl 和 k3d/k3s 已安装
2. **构建镜像**：使用 docker-compose 构建最新镜像
3. **导入镜像**：将镜像导入 K8s 集群
4. **应用配置**：
   - `nginx-configmap.yaml`: Nginx 配置
   - `redis-deployment.yaml`: Redis 数据库
   - `api-deployment.yaml`: 后端 API 服务
   - `frontend-deployment.yaml`: 前端 Web 服务
5. **部署 Ingress**：询问是否在 80 端口暴露服务
6. **等待就绪**：等待所有 Pod 启动完成

### 部署输出示例

```
[INFO] Building Docker images...
[INFO] Importing images to k3d cluster...
[INFO] Applying Kubernetes configurations...
configmap/nginx-config created
deployment.apps/storyboard-redis created
service/storyboard-redis created
deployment.apps/storyboard-api created
service/storyboard-api created
deployment.apps/storyboard-frontend created
service/storyboard-frontend created
[INFO] Waiting for deployments to be ready...
deployment.apps/storyboard-redis condition met
deployment.apps/storyboard-api condition met
deployment.apps/storyboard-frontend condition met
[SUCCESS] All deployments are ready!
```

---

## 手动部署

如果需要逐步部署，可以手动执行以下命令：

### 1. 构建 Docker 镜像

```bash
cd docker/k8s

# 返回项目根目录并构建镜像
cd ../..
docker-compose -f docker/compose/docker-compose.yml build

# 验证镜像已构建
docker images | grep script-to-storyboards
```

### 2. 导入镜像到 K8s 集群

#### Mac/Windows (k3d)

```bash
k3d image import script-to-storyboards-api:latest -c calvin
k3d image import script-to-storyboards-frontend:latest -c calvin
```

#### Linux (k3s)

```bash
docker save script-to-storyboards-api:latest | sudo k3s ctr images import -
docker save script-to-storyboards-frontend:latest | sudo k3s ctr images import -
```

### 3. 应用 Kubernetes 配置

```bash
cd docker/k8s

# 按顺序部署各个组件
kubectl apply -f nginx-configmap.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f api-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f ingress.yaml  # 可选，启用 80 端口访问
```

### 4. 等待部署完成

```bash
# 等待所有 Deployment 就绪
kubectl wait --for=condition=available --timeout=120s deployment/storyboard-redis
kubectl wait --for=condition=available --timeout=120s deployment/storyboard-api
kubectl wait --for=condition=available --timeout=120s deployment/storyboard-frontend

# 查看 Pod 状态
kubectl get pods
```

预期输出：

```
NAME                                   READY   STATUS    RESTARTS   AGE
storyboard-redis-xxxxxxxxx-xxxxx      1/1     Running   0          1m
storyboard-api-xxxxxxxxx-xxxxx        1/1     Running   0          1m
storyboard-frontend-xxxxxxxxx-xxxxx   1/1     Running   0          1m
```

---

## 访问应用

### 通过 Ingress (推荐)

如果部署了 Ingress，可以通过以下地址访问：

```bash
# 前端
http://localhost:8080/

# API文档
http://localhost:8080/api/docs

# API端点
http://localhost:8080/api/scripts
```

> **注意**: k3d 默认将集群的 80 端口映射到主机的 8080 端口

### 通过 Port Forward

如果没有部署 Ingress，可以使用端口转发：

```bash
# 转发前端服务
kubectl port-forward svc/storyboard-frontend 5173:80

# 转发 API 服务（新终端）
kubectl port-forward svc/storyboard-api 8001:8000

# 访问地址
# 前端: http://localhost:5173
# API: http://localhost:8001/api/docs
```

### 验证部署

```bash
# 检查所有服务
kubectl get services

# 测试 API 健康检查
curl http://localhost:8080/api/health

# 测试前端访问
curl -I http://localhost:8080/
```

---

## K8s架构说明

### 组件清单

项目包含以下 Kubernetes 资源：

| 资源文件 | 资源类型 | 说明 |
|---------|---------|-----|
| `redis-deployment.yaml` | Deployment + Service | Redis 会话存储，使用 ClusterIP |
| `api-deployment.yaml` | Deployment + Service | FastAPI 后端服务，端口 8000 |
| `frontend-deployment.yaml` | Deployment + Service | Vite 前端服务，端口 80 |
| `nginx-configmap.yaml` | ConfigMap | Nginx 配置（反向代理、CORS等） |
| `ingress.yaml` | Ingress | 统一入口，路由到 API 和 Frontend |

### 服务依赖关系

```
Internet
    ↓
[Ingress] (storyboard-ingress)
    ├─→ / → [Frontend Service] → Frontend Pods (Nginx + React)
    └─→ /api/* → [API Service] → API Pods (FastAPI)
                                      ↓
                            [Redis Service] → Redis Pods
```

### 环境变量配置

#### API Deployment 环境变量

- `DB_HOST`: PostgreSQL 主机地址
- `DB_PORT`: PostgreSQL 端口（默认 5432）
- `DB_NAME`: 数据库名称
- `DB_USER`: 数据库用户
- `DB_PASSWORD`: 数据库密码
- `REDIS_HOST`: Redis 服务名 (storyboard-redis)
- `REDIS_PORT`: Redis 端口（默认 6379）
- `API_BASE_URL`: API 基础 URL（用于 Google OAuth 回调）
- `GOOGLE_CLIENT_ID`: Google OAuth 客户端ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth 客户端密钥

#### Frontend Deployment 环境变量

- `VITE_API_BASE_URL`: API 基础 URL（构建时注入）

> **重要**: 修改环境变量后，需要重新构建镜像并重新部署

### 资源限制

所有组件都配置了资源请求和限制：

| 组件 | CPU 请求 | CPU 限制 | 内存请求 | 内存限制 |
|-----|---------|---------|---------|---------|
| Redis | 100m | 500m | 128Mi | 256Mi |
| API | 200m | 1000m | 256Mi | 512Mi |
| Frontend | 100m | 500m | 128Mi | 256Mi |

---

## 下一步

完成部署后，可以：

- [查看常用运维命令](operations.md)
- [学习故障排查方法](troubleshooting.md)
- [配置 Google OAuth 认证](../dev/google-oauth-authentication.md)
- [了解生产环境部署](remote-deployment.md)

---

## 相关文档

- [本地 K8s 环境搭建](local-setup.md)
- [Kubernetes 部署总览](deployment.md)
- [Docker Compose 部署](../docker/compose/README.md)
- [API 文档](../api/README.md)
