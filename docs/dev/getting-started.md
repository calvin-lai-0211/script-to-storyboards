# 开发入门指南

本文档介绍 Script-to-Storyboards 项目的各种开发和部署模式，帮助开发者快速上手。

## 目录

- [前置要求](#前置要求)
- [模式一：本地开发（前后端分离）](#模式一本地开发前后端分离)
- [模式二：Docker Compose 本地部署](#模式二docker-compose-本地部署)
- [模式三：本地 Kubernetes 环境](#模式三本地-kubernetes-环境)
- [模式四：远程 Kubernetes 部署](#模式四远程-kubernetes-部署)

---

## 前置要求

### 开发环境

- **Python 3.12+**: 后端 API 开发
- **Node.js 20+**: 前端开发
- **pnpm 8+**: 前端包管理器
- **PostgreSQL 15+**: 数据库（可使用远程或本地）

### 容器化环境

- **Docker 20.10+**: 容器运行时
- **Docker Compose 2.0+**: 多容器编排

### Kubernetes 环境

- **kubectl**: Kubernetes 命令行工具
- **k3d** (Mac/Windows): 本地 K8s 集群
- **k3s** (Linux): 轻量级 K8s（生产环境）

---

## 模式一：本地开发（前后端分离）

适合日常开发和调试，前后端独立运行，支持热重载。

### 1. 后端 API 启动

```bash
# 在项目根目录
cd script-to-storyboards

# 确保数据库已创建（仅首次）
python utils/database.py

# 直接运行 API 服务
python -m api.main
```

**访问地址**:

- API: http://localhost:8001
- API 文档: http://localhost:8001/api/docs
- ReDoc: http://localhost:8001/api/redoc

**配置说明**:

- 数据库配置在 `utils/config.py` 中的 `DB_CONFIG`
- API 端口默认 8001（可通过环境变量 `API_PORT` 修改）
- 默认启用热重载（代码修改自动重启）

**常见问题**:

```bash
# 数据库连接失败
# 检查 utils/config.py 中的数据库配置
# 或设置环境变量：
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=storyboards
export DB_USER=your_user
export DB_PASSWORD=your_password
```

### 2. 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖（仅首次）
pnpm install

# 启动开发服务器
pnpm dev
```

**访问地址**:

- 前端: http://localhost:5173

**配置说明**:

- API 地址配置在 `frontend/.env` 或 `frontend/.env.local`
- 默认 API 地址: `http://localhost:8001`
- 支持 Vite 热模块替换（HMR）

**环境变量配置** (`frontend/.env.local`):

```bash
VITE_API_BASE_URL=http://localhost:8001
```

### 3. 开发工作流

```bash
# 终端1: 启动后端
python -m api.main

# 终端2: 启动前端
cd frontend && pnpm dev
```

**调试技巧**:

- 前端: 浏览器 DevTools + Vue/React DevTools
- 后端: FastAPI 自动生成的 `/api/docs` 交互式文档，可以用这个文档来查看及调试 API
- 日志: 使用 `console.debug()` (前端) 和 `logger.info()` (后端)

---

## 模式二：Docker Compose 本地部署

适合测试完整系统，模拟生产环境，无需安装 Python/Node.js。

### 1. 快速启动

```bash
# 方式A: 使用快捷脚本（推荐）
./docker/local-run.sh --build

# 方式B: 手动执行
cd docker
docker-compose build
docker-compose up -d
```

**访问地址**:

- 前端: http://localhost:8866
- API: http://localhost:8000
- API 文档: http://localhost:8000/api/docs

### 2. 服务管理

```bash
cd docker

# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f           # 所有服务
docker-compose logs -f api       # 仅 API
docker-compose logs -f frontend  # 仅前端

# 重启服务
docker-compose restart api
docker-compose restart frontend

# 停止服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 停止并删除容器 + 卷（清除所有数据）
docker-compose down -v
```

### 3. 更新代码

```bash
# 方式A: 重新构建并重启
docker-compose build
docker-compose up -d

# 方式B: 仅重启（不重新构建）
docker-compose restart

# 方式C: 完全清理后重新部署
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 4. 数据库初始化

```bash
# 进入 API 容器执行初始化
docker-compose exec api python utils/database.py

# 或导入测试数据
docker-compose exec api python from_script_to_database.py
```

### 5. 环境配置

编辑 `docker/docker-compose.yml`:

```yaml
services:
  api:
    environment:
      - DB_HOST=your-db-host
      - DB_PORT=5432
      - DB_NAME=storyboards
      - DB_USER=your-user
      - DB_PASSWORD=your-password
      - REDIS_HOST=redis
      - API_BASE_URL=http://localhost:8000
```

---

## 模式三：本地 Kubernetes 环境

适合测试 K8s 部署、学习容器编排，最接近生产环境。

### 1. 环境准备

**Mac/Windows (使用 k3d)**:

```bash
# 安装 k3d
brew install k3d

# 创建集群（使用项目配置）
cd docker/k8s
k3d cluster create calvin --config k3d-config.yaml

# 验证集群
kubectl get nodes
```

**Linux (使用 k3s)**:

```bash
# 安装 k3s
curl -sfL https://get.k3s.io | sh -

# 配置 kubectl
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config

# 验证集群
kubectl get nodes
```

### 2. 一键部署

```bash
cd docker/k8s
./local-deploy.sh
```

**部署流程**:

1. 构建 Docker 镜像
2. 导入镜像到 K8s 集群
3. 部署 Redis (会话存储)
4. 部署 API 服务
5. 部署 Frontend 服务
6. 部署 Nginx ConfigMap
7. 可选部署 Ingress（80 端口访问）

**访问地址**:

- 通过 Ingress: http://localhost:8080
- 或使用 Port Forward:
  ```bash
  kubectl port-forward svc/storyboard-frontend 5173:80
  kubectl port-forward svc/storyboard-api 8001:8000
  ```

### 3. 服务管理

```bash
# 查看所有资源
kubectl get all

# 查看 Pod 状态
kubectl get pods

# 查看日志
kubectl logs -f deployment/storyboard-api
kubectl logs -f deployment/storyboard-frontend
kubectl logs -f deployment/storyboard-redis

# 重启服务
kubectl rollout restart deployment/storyboard-api
kubectl rollout restart deployment/storyboard-frontend

# 进入容器调试
kubectl exec -it deployment/storyboard-api -- /bin/sh
```

### 4. 更新部署

**更新 API**:

```bash
cd docker/k8s
./update-api.sh
```

**更新 Frontend**:

```bash
cd docker/k8s
./update-frontend.sh
```

**更新 ConfigMap**:

```bash
cd docker/k8s
./update-config.sh
```

### 5. 清理环境

```bash
# 删除所有部署（保留集群）
cd docker/k8s
./undeploy.sh

# 或手动删除
kubectl delete -f docker/k8s/

# 删除整个集群
k3d cluster delete calvin
```

### 6. 环境配置

修改 `docker/k8s/api-deployment.yaml`:

```yaml
env:
  - name: API_BASE_URL
    value: "http://localhost:8080"
  - name: REDIS_HOST
    value: "storyboard-redis"
  - name: ENV
    value: "development"
```

修改后应用：

```bash
kubectl apply -f docker/k8s/api-deployment.yaml
kubectl rollout restart deployment/storyboard-api
```

---

## 模式四：远程 Kubernetes 部署

适合生产环境和远程服务器部署。

### 1. 服务器准备

**在远程服务器安装 K3s**:

```bash
# SSH 登录服务器
ssh your-server

# 安装 K3s
curl -sfL https://get.k3s.io | sh -

# 检查状态
sudo systemctl status k3s
sudo k3s kubectl get nodes
```

### 2. 本地配置远程访问

**方式 A: SSH 配置** (`~/.ssh/config`):

```
Host calvin
    HostName 44.213.117.91
    User ubuntu
    IdentityFile ~/.ssh/your-key.pem
```

**方式 B: 获取 kubeconfig**:

```bash
# 从远程服务器复制配置
ssh calvin "sudo cat /etc/rancher/k3s/k3s.yaml" > ~/.kube/calvin-k3s.yaml

# 修改文件中的 server 地址
# From: server: https://127.0.0.1:6443
# To:   server: https://YOUR_SERVER_IP:6443

# 使用配置
export KUBECONFIG=~/.kube/calvin-k3s.yaml
kubectl get nodes
```

### 3. 一键部署到远程

```bash
cd docker/k8s
./deploy-to-remote.sh
```

**部署流程**:

1. 本地构建 Docker 镜像
2. 打包镜像和 K8s 配置（使用生产环境配置）
3. 上传到远程服务器
4. 在远程服务器导入镜像
5. 应用 K8s 配置
6. 部署 Redis、API、Frontend
7. 可选部署 Ingress

**注意**: 远程部署使用 `api-deployment.prod.yaml`，其中:

```yaml
env:
  - name: API_BASE_URL
    value: "https://videos.ethanlyn.com"
  - name: ENV
    value: "production"
```

### 4. 远程管理

```bash
# 查看远程 Pod 状态
ssh calvin 'kubectl get pods'

# 查看远程日志
ssh calvin 'kubectl logs -f deployment/storyboard-api'

# 重启远程服务
ssh calvin 'kubectl rollout restart deployment/storyboard-api'

# 查看 Ingress
ssh calvin 'kubectl get ingress'

# 查看服务
ssh calvin 'kubectl get svc'
```

### 5. 更新远程部署

```bash
# 重新运行部署脚本
./deploy-to-remote.sh

# 或手动更新特定服务
ssh calvin 'cd ~/k8s-deploy/k8s-package && ./update-api.sh'
```

### 6. 生产环境配置

**Google OAuth 回调地址**:

- 本地: `http://localhost:8080/api/user/google/callback`
- 生产: `https://videos.ethanlyn.com/api/user/google/callback`

在 Google Cloud Console 的 OAuth 配置中添加这两个地址。

**环境变量**:

- 生产环境敏感信息应使用 Kubernetes Secrets（不要硬编码在 YAML 中）
- Redis 数据应使用 PersistentVolume（不要使用 emptyDir）
- 启用 HTTPS（通过 cert-manager + Let's Encrypt）

---

## 开发模式对比

| 特性           | 本地开发   | Docker Compose | 本地 K8s | 远程 K8s   |
| -------------- | ---------- | -------------- | -------- | ---------- |
| **启动速度**   | ⭐⭐⭐⭐⭐ | ⭐⭐⭐         | ⭐⭐     | ⭐         |
| **热重载**     | ✅         | ❌             | ❌       | ❌         |
| **调试便利性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐         | ⭐⭐     | ⭐         |
| **环境隔离**   | ❌         | ⭐⭐⭐         | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **生产相似度** | ⭐         | ⭐⭐⭐         | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **资源消耗**   | ⭐⭐       | ⭐⭐⭐         | ⭐⭐⭐⭐ | ⭐         |
| **适用场景**   | 日常开发   | 集成测试       | K8s 学习 | 生产部署   |

---

## 常用开发命令速查

### 前端开发

```bash
cd frontend
pnpm dev          # 启动开发服务器
pnpm build        # 构建生产版本
pnpm test:run     # 运行测试
pnpm lint         # 代码检查
pnpm type-check   # 类型检查
```

### 后端开发

```bash
python -m api.main                    # 启动 API
python utils/database.py              # 初始化数据库
python from_script_to_database.py     # 导入剧本
python demo_make_storyboards_from_scripts.py  # 生成分镜
```

### Docker

```bash
docker-compose up -d      # 启动服务
docker-compose logs -f    # 查看日志
docker-compose restart    # 重启服务
docker-compose down       # 停止服务
```

### Kubernetes

```bash
kubectl get pods              # 查看 Pod
kubectl logs -f <pod>         # 查看日志
kubectl exec -it <pod> -- sh  # 进入容器
kubectl rollout restart deployment/<name>  # 重启部署
```

---

## 下一步

- [Git Hooks 和 CI/CD](git-hooks-and-ci.md) - 代码提交规范和自动化流程
- [Google OAuth 配置](google-oauth-authentication.md) - 配置 Google 登录
- [Kubernetes 部署详细指南](../k8s/deployment.md) - K8s 深入学习

---

## 常见问题

### Q: 前端无法连接后端 API？

A: 检查前端 `.env.local` 中的 `VITE_API_BASE_URL` 是否正确，确保后端 API 已启动。

### Q: Docker Compose 启动失败？

A: 检查端口是否被占用（8866, 8000），使用 `docker-compose logs` 查看错误信息。

### Q: K8s Pod 一直 Pending？

A: 检查镜像是否成功导入 (`kubectl describe pod <pod-name>`)，确保资源限制合理。

### Q: 数据库连接失败？

A: 确认数据库配置正确，网络可达，防火墙允许连接。

### Q: 如何切换不同的开发模式？

A: 确保停止之前的服务，避免端口冲突。各模式可以并存，但需要调整端口。
