# K8s Quick Start

> 本文基于 k3s/k3d 来介绍

## Mac (k3d) 快速开始

### 1. 创建 k3d 集群

```bash
# 使用配置文件创建集群
k3d cluster create --config k3d-config.yaml

# 或者简单命令
k3d cluster create calvin -p "80:80@loadbalancer"
```

### 2. 部署

```bash
./k8s/deploy.sh
# 脚本会自动检测 k3d 环境
```

### 3. 访问

```bash
http://localhost/              # Frontend
http://localhost/api/health    # API
```

---

## Linux Server (k3s) 快速开始

### 1. Setup Connection

```bash
# SSH tunnel (easiest)
ssh -L 6443:localhost:6443 calvin -N -f
```

### 2. Deploy

```bash
./k8s/deploy.sh
# 当询问 "Deploy Ingress on port 80?" 时，按 Y (默认)
```

## 3. Access

```bash
# Frontend (通过 80 端口 Ingress)
http://<server-ip>/

# API (通过 80 端口 Ingress)
http://<server-ip>/api/

# API Docs
http://<server-ip>/api/docs

# Check status
kubectl get ingress
kubectl get pods
kubectl get svc
```

## Common Commands

```bash
# Logs
kubectl logs -f deployment/storyboard-api

# Restart
kubectl rollout restart deployment/storyboard-api

# Remove
./k8s/undeploy.sh
```

## Troubleshooting

```bash
# Check Ingress
kubectl describe ingress storyboard-ingress

# Check images
sudo k3s ctr images list | grep storyboard

# Reimport images
docker save script-to-storyboards-api:latest | sudo k3s ctr images import -
docker save script-to-storyboards-frontend:latest | sudo k3s ctr images import -

# Test from server
curl http://localhost/
curl http://localhost/api/health
```
