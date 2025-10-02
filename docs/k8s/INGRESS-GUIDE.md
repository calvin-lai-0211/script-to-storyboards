# Port 80 Deployment Guide

通过 80 端口来部署和访问应用。

## 架构

```
外部请求 (Port 80)
       ↓
   Traefik Ingress
       ↓
  ┌────┴─────┐
  ↓          ↓
Frontend   API
/          /api
```

所有流量通过 80 端口的 Ingress 统一入口，然后根据路径分发：

- `/api/*` → API Service (ClusterIP)
- `/*` → Frontend Service (ClusterIP)

## Service

- **Frontend**: ClusterIP（通过 Ingress 暴露）
- **API**: ClusterIP（通过 Ingress 暴露）

不使用 NodePort，所有流量统一走 80 端口的 Ingress。

### Nginx 配置

Frontend 的 nginx 不再代理 `/api` 请求，由 Ingress 直接处理。

## 故障排查

### Ingress 未生效

```bash
# 检查 Traefik
kubectl get pods -n kube-system | grep traefik

# 检查 Ingress 状态
kubectl describe ingress storyboard-ingress
```

### 80 端口无法访问

```bash
# 检查防火墙
sudo ufw status

# 允许 80 端口
sudo ufw allow 80/tcp

# 或者检查 iptables
sudo iptables -L -n | grep 80
```

### API 路径返回 404

确保 Ingress 路径顺序正确（/api 在 / 之前）：

```bash
kubectl get ingress storyboard-ingress -o yaml
```

## 高级配置

### 添加 HTTPS (TLS)

1. 安装 cert-manager
2. 创建 ClusterIssuer
3. 修改 Ingress 添加 TLS 配置

### 限制访问 IP

在 Ingress 中添加注释：

```yaml
annotations:
  traefik.ingress.kubernetes.io/router.middlewares: default-ipwhitelist@kubernetescrd
```

### 添加认证

使用 Traefik Middleware 添加 BasicAuth：

```yaml
annotations:
  traefik.ingress.kubernetes.io/router.middlewares: default-basicauth@kubernetescrd
```

## 清理

```bash
./k8s/undeploy.sh
```
