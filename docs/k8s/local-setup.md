# 本地 K8s 环境搭建

本文档介绍如何在本地机器上搭建 Kubernetes 集群，用于开发和测试 Script-to-Storyboards 应用。

## 目录

- [前置要求](#前置要求)
- [Mac/Windows: 使用 k3d](#macwindows-使用-k3d)
- [Linux: 使用 k3s](#linux-使用-k3s)
- [常见问题](#常见问题)
- [下一步](#下一步)

---

## 前置要求

### 必需工具

- **kubectl**: Kubernetes 命令行工具
- **Docker**: 容器构建和运行
- **k3d** (Mac/Windows) 或 **k3s** (Linux): 轻量级 K8s 发行版

### 可选工具

- **k9s**: Kubernetes 终端UI工具（推荐）
- **helm**: Kubernetes 包管理器

---

## Mac/Windows: 使用 k3d

k3d 是 k3s 的 Docker 版本，适合本地开发。

### 1. 安装 k3d

```bash
# Mac (使用 Homebrew)
brew install k3d

# Linux/WSL
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
```

### 2. 创建本地 K8s 集群

```bash
# 使用项目配置文件创建集群
cd docker/k8s
k3d cluster create calvin --config k3d-config.yaml

# 或者手动创建（映射80端口到主机8080）
k3d cluster create calvin \
  --api-port 6550 \
  --servers 1 \
  --agents 0 \
  --port "8080:80@loadbalancer" \
  --volume /tmp/k3d-storage:/var/lib/rancher/k3s/storage@all
```

#### 配置说明

- `--api-port 6550`: Kubernetes API Server 端口
- `--servers 1`: 1 个控制平面节点
- `--agents 0`: 0 个工作节点（单节点集群）
- `--port "8080:80@loadbalancer"`: 将集群 80 端口映射到主机 8080 端口
- `--volume`: 挂载本地目录用于持久化存储

### 3. 验证集群

```bash
# 检查集群状态
kubectl cluster-info

# 查看节点
kubectl get nodes

# 输出示例：
# NAME                  STATUS   ROLES                  AGE   VERSION
# k3d-calvin-server-0   Ready    control-plane,master   1m    v1.27.4+k3s1
```

### 4. 集群管理命令

```bash
# 停止集群
k3d cluster stop calvin

# 启动集群
k3d cluster start calvin

# 删除集群
k3d cluster delete calvin

# 查看所有集群
k3d cluster list
```

---

## Linux: 使用 k3s

k3s 是专为生产环境设计的轻量级 K8s。

### 1. 安装 k3s

```bash
# 安装 k3s
curl -sfL https://get.k3s.io | sh -

# 配置 kubectl 访问权限
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
```

### 2. 验证安装

```bash
# 检查 k3s 服务状态
sudo systemctl status k3s

# 查看节点
kubectl get nodes

# 输出示例：
# NAME        STATUS   ROLES                  AGE   VERSION
# your-host   Ready    control-plane,master   1m    v1.27.4+k3s1
```

### 3. k3s 管理命令

```bash
# 停止 k3s
sudo systemctl stop k3s

# 启动 k3s
sudo systemctl start k3s

# 重启 k3s
sudo systemctl restart k3s

# 查看日志
sudo journalctl -u k3s -f

# 卸载 k3s
sudo /usr/local/bin/k3s-uninstall.sh
```

---

## 常见问题

### Q: k3d 和 k3s 有什么区别？

A: k3d 在 Docker 中运行 k3s，适合 Mac/Windows 本地开发；k3s 直接运行在 Linux 上，适合生产环境。

### Q: kubectl 命令无法连接到集群？

A: 检查 kubeconfig 配置：

```bash
# 查看当前配置
kubectl config view

# 查看当前上下文
kubectl config current-context

# 切换到 k3d 集群
kubectl config use-context k3d-calvin
```

### Q: Ingress 80 端口被占用怎么办？

A: 创建集群时修改端口映射：

```bash
k3d cluster create calvin \
  --port "9090:80@loadbalancer"  # 使用 9090 端口

# 然后访问 http://localhost:9090
```

### Q: 如何使用多个 k3d 集群？

A: 创建时使用不同的集群名称和端口：

```bash
k3d cluster create calvin-dev --port "8080:80@loadbalancer"
k3d cluster create calvin-test --port "8081:80@loadbalancer"

# 切换集群
kubectl config use-context k3d-calvin-dev
kubectl config use-context k3d-calvin-test
```

---

## 下一步

完成集群搭建后，可以继续以下步骤：

- [部署应用到本地 K8s](local-deployment.md)
- [查看常用运维命令](operations.md)
- [故障排查指南](troubleshooting.md)
- [生产环境部署](remote-deployment.md)

---

## 相关文档

- [Kubernetes 部署总览](deployment.md)
- [Docker Compose 部署](../docker/compose/README.md)
- [项目总览](../../README.md)
