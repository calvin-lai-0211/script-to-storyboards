# 远程部署到 K3s 服务器

本文介绍如何从本地 Mac 一键部署到远程 Ubuntu K3s 服务器。

## 方案说明

采用 **Docker 镜像打包方案**：

1. 本地构建前端 dist 和 Docker 镜像
2. 导出镜像为 tar 文件
3. 上传到服务器
4. 在服务器上导入镜像并部署

**优势**：
- 不需要在服务器上安装 Node/pnpm
- 构建环境一致（都在本地）
- 部署快速（无需重新构建）
- 依赖已打包在镜像中

## 前提条件

### 本地 Mac

- Docker Desktop 已安装并运行
- SSH 已配置好连接到服务器（`~/.ssh/config` 中有 `calvin` host）

### 远程服务器

- Ubuntu 系统
- K3s 已安装
- SSH 访问权限

## 快速开始

### 一键部署（推荐）

```bash
./k8s/deploy-to-remote.sh
```

脚本会自动完成：
1. ✅ 构建前端（使用 .env.k8s 配置）
2. ✅ 构建 Docker 镜像
3. ✅ 导出镜像为 tar 文件
4. ✅ 打包 K8s 配置文件
5. ✅ 上传到服务器
6. ✅ 在服务器上导入镜像
7. ✅ 部署到 K3s

部署完成后访问：
```
http://<server-ip>/              # Frontend
http://<server-ip>/api/          # API
http://<server-ip>/api/docs      # API Documentation
```

## 分步部署

如果需要更细粒度的控制，可以分步执行：

### 步骤 1: 打包

```bash
./k8s/package.sh
```

生成 `k8s-package.tar.gz`，包含：
- `api-image.tar` - API Docker 镜像
- `frontend-image.tar` - Frontend Docker 镜像
- K8s YAML 配置文件
- `deploy.sh` - 服务器端部署脚本
- `undeploy.sh` - 清理脚本

### 步骤 2: 上传

```bash
scp k8s-package.tar.gz calvin:~/
```

### 步骤 3: 服务器端部署

```bash
ssh calvin
tar -xzf k8s-package.tar.gz
cd k8s-package
./deploy.sh
```

部署脚本会：
1. 导入 Docker 镜像到 k3s
2. 应用 K8s 配置
3. 询问是否部署 Ingress（推荐选择 Y）
4. 等待部署完成
5. 显示访问地址

## 管理命令

### 查看状态

```bash
# 从本地查看（需要先设置 SSH tunnel）
ssh -L 6443:localhost:6443 calvin -N -f
kubectl get pods
kubectl get ingress

# 直接在服务器上查看
ssh calvin 'kubectl get pods'
ssh calvin 'kubectl get ingress'
```

### 查看日志

```bash
# API 日志
ssh calvin 'kubectl logs -f deployment/storyboard-api'

# Frontend 日志
ssh calvin 'kubectl logs -f deployment/storyboard-frontend'
```

### 重启服务

```bash
ssh calvin 'kubectl rollout restart deployment/storyboard-api'
ssh calvin 'kubectl rollout restart deployment/storyboard-frontend'
```

### 卸载部署

```bash
ssh calvin 'cd ~/k8s-deploy/k8s-package && ./undeploy.sh'
```

## 更新部署

当代码有更新时：

```bash
# 重新打包和部署
./k8s/deploy-to-remote.sh
```

脚本会覆盖之前的部署。

## 故障排查

### 镜像导入失败

```bash
# 在服务器上检查镜像
ssh calvin 'sudo k3s ctr images list | grep storyboard'

# 手动导入
ssh calvin
cd ~/k8s-deploy/k8s-package
sudo k3s ctr images import api-image.tar
sudo k3s ctr images import frontend-image.tar
```

### Pod 启动失败

```bash
# 查看 Pod 详情
ssh calvin 'kubectl describe pod <pod-name>'

# 查看日志
ssh calvin 'kubectl logs <pod-name>'
```

### Ingress 无法访问

```bash
# 检查 Ingress 状态
ssh calvin 'kubectl get ingress'
ssh calvin 'kubectl describe ingress storyboard-ingress'

# 从服务器本地测试
ssh calvin 'curl http://localhost/'
ssh calvin 'curl http://localhost/api/health'
```

## 包结构

`k8s-package.tar.gz` 内容：
```
k8s-package/
├── api-image.tar              # API Docker 镜像（~500MB）
├── frontend-image.tar         # Frontend Docker 镜像（~50MB）
├── api-deployment.yaml        # API 部署配置
├── frontend-deployment.yaml   # Frontend 部署配置
├── ingress.yaml              # Ingress 配置
├── nginx-configmap.yaml      # Nginx 配置
├── deploy.sh                 # 部署脚本
└── undeploy.sh              # 清理脚本
```

## 相关文档

- [快速开始](QUICKSTART.md) - Mac 和 Linux 快速部署
- [完整部署指南](README.md) - 详细部署说明
- [API 路由配置](API-ROUTING.md) - Ingress 路由原理
- [Ingress 配置](INGRESS-GUIDE.md) - 端口 80 配置详解
