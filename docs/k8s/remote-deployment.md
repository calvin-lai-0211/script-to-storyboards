# 生产环境部署指南

本文档介绍如何将 Script-to-Storyboards 部署到生产环境的 Kubernetes 集群。

## 目录

- [前置要求](#前置要求)
- [服务器准备](#服务器准备)
- [一键部署](#一键部署)
- [远程管理](#远程管理)
- [安全最佳实践](#安全最佳实践)
- [生产环境注意事项](#生产环境注意事项)

---

## 前置要求

### 服务器要求

- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **CPU**: 最低 2 核，推荐 4 核+
- **内存**: 最低 4GB，推荐 8GB+
- **存储**: 最低 20GB，推荐 50GB+
- **网络**: 公网 IP 或域名，开放端口 80/443/6443

### 工具准备

- **kubectl**: Kubernetes 命令行工具
- **k3s**: 生产环境轻量级 K8s
- **ssh**: 远程服务器访问

---

## 服务器准备

### 1. 安装 k3s

在远程服务器上执行：

```bash
# SSH 登录到远程服务器
ssh user@your-server-ip

# 安装 k3s
curl -sfL https://get.k3s.io | sh -

# 配置 kubectl 访问权限
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config

# 验证安装
kubectl get nodes
```

### 2. 配置防火墙

```bash
# 允许 HTTP/HTTPS 流量
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 允许 Kubernetes API（如需远程访问）
sudo ufw allow 6443/tcp

# 启用防火墙
sudo ufw enable
```

### 3. 配置域名（推荐）

将域名 A 记录指向服务器 IP：

```
yourdomain.com  →  your-server-ip
```

---

## 一键部署

### 方式1: 在服务器上直接部署

```bash
# 1. 克隆项目到服务器
git clone https://github.com/your-org/script-to-storyboards.git
cd script-to-storyboards

# 2. 修改环境变量配置
vim docker/k8s/api-deployment.yaml
# 修改 DB_HOST, GOOGLE_CLIENT_ID 等环境变量

# 3. 构建镜像
docker-compose -f docker/compose/docker-compose.yml build

# 4. 导入镜像到 k3s
docker save script-to-storyboards-api:latest | sudo k3s ctr images import -
docker save script-to-storyboards-frontend:latest | sudo k3s ctr images import -

# 5. 部署应用
cd docker/k8s
kubectl apply -f nginx-configmap.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f api-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f ingress.yaml

# 6. 等待部署完成
kubectl wait --for=condition=available --timeout=180s deployment/storyboard-api
```

### 方式2: 从本地推送镜像到服务器

```bash
# 1. 本地构建镜像
docker-compose -f docker/compose/docker-compose.yml build

# 2. 保存镜像为文件
docker save script-to-storyboards-api:latest > api.tar
docker save script-to-storyboards-frontend:latest > frontend.tar

# 3. 传输到服务器
scp api.tar frontend.tar user@your-server-ip:/tmp/

# 4. 在服务器上导入镜像
ssh user@your-server-ip
sudo k3s ctr images import /tmp/api.tar
sudo k3s ctr images import /tmp/frontend.tar

# 5. 部署应用（同方式1步骤5-6）
```

### 方式3: 使用私有镜像仓库（推荐）

```bash
# 1. 本地推送镜像到私有仓库
docker tag script-to-storyboards-api:latest your-registry.com/storyboard-api:latest
docker tag script-to-storyboards-frontend:latest your-registry.com/storyboard-frontend:latest
docker push your-registry.com/storyboard-api:latest
docker push your-registry.com/storyboard-frontend:latest

# 2. 在服务器上创建镜像拉取凭证
kubectl create secret docker-registry regcred \
  --docker-server=your-registry.com \
  --docker-username=your-username \
  --docker-password=your-password

# 3. 修改 deployment YAML 文件
# 将 imagePullPolicy: Never 改为 imagePullPolicy: Always
# 将 image: script-to-storyboards-api:latest 改为 image: your-registry.com/storyboard-api:latest
# 添加 imagePullSecrets: [name: regcred]

# 4. 部署应用
kubectl apply -f docker/k8s/
```

---

## 远程管理

### 配置本地 kubectl 访问远程集群

```bash
# 1. 从服务器复制 kubeconfig
ssh user@your-server-ip "sudo cat /etc/rancher/k3s/k3s.yaml" > k3s-remote.yaml

# 2. 修改服务器地址
# 将 k3s-remote.yaml 中的 127.0.0.1 替换为实际服务器 IP
sed -i 's/127.0.0.1/your-server-ip/g' k3s-remote.yaml

# 3. 合并到本地 kubeconfig
export KUBECONFIG=~/.kube/config:k3s-remote.yaml
kubectl config view --flatten > ~/.kube/config.new
mv ~/.kube/config.new ~/.kube/config

# 4. 切换到远程集群
kubectl config use-context default

# 5. 验证连接
kubectl get nodes
```

### 常用远程管理命令

```bash
# 查看应用状态
kubectl get pods

# 查看日志
kubectl logs -f deployment/storyboard-api

# 更新配置
kubectl apply -f api-deployment.yaml

# 重启服务
kubectl rollout restart deployment/storyboard-api

# 进入容器调试
kubectl exec -it deployment/storyboard-api -- /bin/sh
```

---

## 安全最佳实践

### 1. 使用 Kubernetes Secrets 管理敏感信息

**不要**在 YAML 文件中硬编码敏感信息：

```bash
# 创建 Secret
kubectl create secret generic storyboard-secrets \
  --from-literal=db-password=your-db-password \
  --from-literal=google-client-secret=your-google-secret \
  --from-literal=redis-password=your-redis-password

# 在 Deployment 中引用
# vim api-deployment.yaml
```

修改 `api-deployment.yaml`:

```yaml
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: storyboard-secrets
        key: db-password
  - name: GOOGLE_CLIENT_SECRET
    valueFrom:
      secretKeyRef:
        name: storyboard-secrets
        key: google-client-secret
```

### 2. 配置 HTTPS / TLS

使用 cert-manager 自动管理 SSL 证书：

```bash
# 1. 安装 cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# 2. 创建 Let's Encrypt Issuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: traefik
EOF

# 3. 修改 Ingress 配置
# vim ingress.yaml
```

修改 `ingress.yaml`:

```yaml
metadata:
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - yourdomain.com
      secretName: storyboard-tls
  rules:
    - host: yourdomain.com
      http:
        paths:
          - path: /
            ...
```

### 3. 限制网络访问

```bash
# 创建 NetworkPolicy 限制 Pod 间通信
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
spec:
  podSelector:
    matchLabels:
      app: storyboard-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: storyboard-frontend
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: storyboard-redis
EOF
```

---

## 生产环境注意事项

### 1. 持久化存储

Redis 使用 `emptyDir`（临时存储），重启后数据会丢失。生产环境应使用 PersistentVolumeClaim：

```yaml
# redis-deployment.yaml
volumes:
  - name: redis-data
    persistentVolumeClaim:
      claimName: redis-pvc
```

创建 PVC:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
EOF
```

### 2. 资源监控

建议部署 Prometheus + Grafana 监控资源使用：

```bash
# 使用 Helm 部署
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack

# 访问 Grafana
kubectl port-forward svc/prometheus-grafana 3000:80
# 访问 http://localhost:3000 (默认用户名/密码: admin/prom-operator)
```

### 3. 日志聚合

使用 Loki 收集和查询日志：

```bash
# 使用 Helm 部署 Loki
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack

# 在 Grafana 中添加 Loki 数据源
# URL: http://loki:3100
```

### 4. 自动扩缩容

配置 HorizontalPodAutoscaler (HPA):

```bash
# 为 API 服务配置自动扩缩容
kubectl autoscale deployment storyboard-api \
  --cpu-percent=70 \
  --min=2 \
  --max=10

# 查看 HPA 状态
kubectl get hpa
```

### 5. 备份策略

定期备份关键数据：

```bash
# 备份 PostgreSQL 数据库
kubectl exec -it deployment/storyboard-api -- \
  pg_dump -h $DB_HOST -U $DB_USER $DB_NAME > backup.sql

# 备份 Kubernetes 配置
kubectl get all --all-namespaces -o yaml > k8s-backup.yaml
```

### 6. 健康检查

确保所有 Deployment 配置了 livenessProbe 和 readinessProbe（已在项目 YAML 中配置）。

### 7. 滚动更新策略

配置零停机更新：

```yaml
# api-deployment.yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

---

## 相关文档

- [本地 K8s 环境搭建](local-setup.md)
- [本地 K8s 部署](local-deployment.md)
- [常用运维命令](operations.md)
- [故障排查指南](troubleshooting.md)
- [Google OAuth 认证配置](../dev/google-oauth-authentication.md)
