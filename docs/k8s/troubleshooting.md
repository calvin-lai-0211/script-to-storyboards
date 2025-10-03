# Kubernetes 故障排查指南

本文档提供 Script-to-Storyboards 在 Kubernetes 环境中常见问题的排查和解决方案。

## 目录

- [Pod 启动失败](#pod-启动失败)
- [数据库连接问题](#数据库连接问题)
- [Redis 连接问题](#redis-连接问题)
- [Ingress 访问问题](#ingress-访问问题)
- [镜像更新不生效](#镜像更新不生效)
- [网络连接问题](#网络连接问题)
- [资源不足问题](#资源不足问题)
- [配置问题](#配置问题)
- [查看完整状态](#查看完整状态)

---

## Pod 启动失败

### 诊断步骤

```bash
# 1. 查看 Pod 状态
kubectl get pods

# 可能的状态：
# - Pending: 等待调度或拉取镜像
# - CrashLoopBackOff: 容器反复崩溃
# - ImagePullBackOff: 镜像拉取失败
# - Error: 容器启动失败

# 2. 查看 Pod 详细信息
kubectl describe pod <pod-name>

# 3. 查看容器日志
kubectl logs <pod-name>

# 4. 查看之前崩溃的日志
kubectl logs --previous <pod-name>
```

### 常见错误及解决方案

#### ImagePullBackOff - 镜像拉取失败

**症状**：

```
Events:
  Failed to pull image "script-to-storyboards-api:latest": rpc error: code = Unknown desc = failed to pull and unpack image
```

**原因**：
- 镜像未导入到 k3d/k3s 集群
- 镜像名称或标签错误
- 镜像仓库连接失败

**解决方案**：

```bash
# 检查本地镜像是否存在
docker images | grep script-to-storyboards

# 重新导入镜像到 k3d
k3d image import script-to-storyboards-api:latest -c calvin
k3d image import script-to-storyboards-frontend:latest -c calvin

# 或导入到 k3s
docker save script-to-storyboards-api:latest | sudo k3s ctr images import -
docker save script-to-storyboards-frontend:latest | sudo k3s ctr images import -

# 验证镜像已导入（k3d）
docker exec k3d-calvin-server-0 crictl images | grep script-to-storyboards

# 验证镜像已导入（k3s）
sudo k3s crictl images | grep script-to-storyboards

# 删除 Pod 强制重新拉取
kubectl delete pod <pod-name>
```

#### CrashLoopBackOff - 配置错误

**症状**：

```
State:          Waiting
  Reason:       CrashLoopBackOff
Last State:     Terminated
  Reason:       Error
  Exit Code:    1
```

**原因**：
- 环境变量配置错误
- 依赖服务未就绪（如 Redis、数据库）
- 应用代码错误

**解决方案**：

```bash
# 1. 查看完整日志
kubectl logs <pod-name>

# 2. 检查环境变量配置
kubectl describe deployment/storyboard-api | grep -A 20 "Environment"

# 3. 验证依赖服务状态
kubectl get pods
kubectl logs deployment/storyboard-redis

# 4. 进入容器调试（如果容器能短暂运行）
kubectl exec -it <pod-name> -- /bin/sh

# 5. 检查配置文件
kubectl get configmap nginx-config -o yaml

# 6. 修复配置后重新部署
kubectl apply -f docker/k8s/api-deployment.yaml
```

#### Pending - 资源不足

**症状**：

```
Status: Pending
Events:
  0/1 nodes are available: 1 Insufficient cpu.
```

**解决方案**：

```bash
# 1. 查看节点资源使用情况
kubectl top nodes
kubectl describe nodes

# 2. 降低资源请求（修改 YAML）
vim docker/k8s/api-deployment.yaml

# 修改 resources.requests 为更小的值
resources:
  requests:
    cpu: 100m        # 从 200m 降低
    memory: 128Mi    # 从 256Mi 降低

# 3. 应用更改
kubectl apply -f docker/k8s/api-deployment.yaml
```

---

## 数据库连接问题

### 诊断步骤

```bash
# 1. 检查环境变量配置
kubectl describe deployment/storyboard-api | grep -A 20 "Environment"

# 预期输出：
# DB_HOST: your-db-host
# DB_PORT: 5432
# DB_NAME: your-db-name
# DB_USER: your-db-user
# DB_PASSWORD: your-db-password

# 2. 进入 API Pod 测试连接
kubectl exec -it deployment/storyboard-api -- /bin/sh

# 在容器内测试
python -c "
from utils.database import Database
from utils.config import DB_CONFIG
print('DB_CONFIG:', DB_CONFIG)
db = Database(DB_CONFIG)
print('Database connection successful')
"
```

### 常见错误及解决方案

#### 连接超时

**错误信息**：

```
psycopg2.OperationalError: could not connect to server: Connection timed out
```

**解决方案**：

```bash
# 1. 检查数据库主机是否可达
kubectl exec -it deployment/storyboard-api -- ping -c 3 <db-host>

# 2. 检查数据库端口是否开放
kubectl exec -it deployment/storyboard-api -- nc -zv <db-host> 5432

# 3. 检查防火墙规则（在数据库服务器上）
sudo ufw status
sudo ufw allow from <k8s-node-ip> to any port 5432

# 4. 验证数据库配置
kubectl exec -it deployment/storyboard-api -- env | grep DB_
```

#### 认证失败

**错误信息**：

```
psycopg2.OperationalError: FATAL: password authentication failed for user "xxx"
```

**解决方案**：

```bash
# 1. 验证数据库凭证
# 在数据库服务器上测试
psql -h <db-host> -U <db-user> -d <db-name>

# 2. 使用 Secret 更新敏感信息
kubectl create secret generic storyboard-secrets \
  --from-literal=db-password=correct-password \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. 修改 Deployment 使用 Secret
vim docker/k8s/api-deployment.yaml

# 添加：
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: storyboard-secrets
        key: db-password

# 4. 重启服务
kubectl rollout restart deployment/storyboard-api
```

#### 数据库不存在

**错误信息**：

```
psycopg2.OperationalError: FATAL: database "xxx" does not exist
```

**解决方案**：

```bash
# 1. 在数据库服务器创建数据库
psql -h <db-host> -U postgres
CREATE DATABASE your_db_name;

# 2. 初始化数据表
kubectl exec -it deployment/storyboard-api -- python utils/database.py
```

---

## Redis 连接问题

### 诊断步骤

```bash
# 1. 检查 Redis 服务状态
kubectl get svc storyboard-redis

# 预期输出：
# NAME               TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
# storyboard-redis   ClusterIP   10.43.x.x      <none>        6379/TCP   10m

# 2. 检查 Redis Pod 状态
kubectl get pods -l app=storyboard-redis

# 3. 测试 Redis 连接
kubectl exec -it deployment/storyboard-redis -- redis-cli ping

# 预期输出：PONG
```

### 常见错误及解决方案

#### Redis 连接被拒绝

**错误信息**：

```
redis.exceptions.ConnectionError: Error 111 connecting to storyboard-redis:6379. Connection refused.
```

**解决方案**：

```bash
# 1. 检查 Redis Pod 是否运行
kubectl get pods -l app=storyboard-redis

# 2. 查看 Redis 日志
kubectl logs deployment/storyboard-redis

# 3. 重启 Redis
kubectl rollout restart deployment/storyboard-redis

# 4. 验证 Service 配置
kubectl describe svc storyboard-redis

# 5. 从 API Pod 测试 Redis 连接
kubectl exec -it deployment/storyboard-api -- python -c "
import redis
r = redis.Redis(host='storyboard-redis', port=6379)
print(r.ping())
"
```

#### Redis 服务名解析失败

**错误信息**：

```
redis.exceptions.ConnectionError: Error -2 connecting to storyboard-redis:6379. Name or service not known.
```

**解决方案**：

```bash
# 1. 检查 DNS 解析
kubectl exec -it deployment/storyboard-api -- nslookup storyboard-redis

# 2. 检查 Service 是否存在
kubectl get svc storyboard-redis

# 3. 重新部署 Redis Service
kubectl apply -f docker/k8s/redis-deployment.yaml

# 4. 验证环境变量
kubectl describe deployment/storyboard-api | grep REDIS
```

---

## Ingress 访问问题

### 诊断步骤

```bash
# 1. 检查 Ingress 状态
kubectl get ingress storyboard-ingress

# 预期输出：
# NAME                 CLASS     HOSTS   ADDRESS         PORTS   AGE
# storyboard-ingress   traefik   *       192.168.x.x     80      10m

# 2. 查看 Ingress 详细信息
kubectl describe ingress storyboard-ingress

# 3. 检查 k3d 端口映射（Mac）
k3d cluster list
docker ps | grep k3d-calvin

# 4. 测试服务内部可达性
kubectl run -it --rm debug --image=busybox --restart=Never -- wget -O- http://storyboard-frontend
kubectl run -it --rm debug --image=busybox --restart=Never -- wget -O- http://storyboard-api:8000/api/health
```

### 常见错误及解决方案

#### 无法访问 http://localhost:8080

**症状**：浏览器显示 "Connection refused" 或 "This site can't be reached"

**解决方案**：

```bash
# 1. 检查 k3d 集群端口映射
k3d cluster list

# 应该看到类似输出：
# NAME     SERVERS   AGENTS   LOADBALANCER
# calvin   1/1       0/0      true

docker ps | grep k3d-calvin-serverlb

# 应该看到端口映射：
# 0.0.0.0:8080->80/tcp

# 2. 如果端口映射不存在，重新创建集群
k3d cluster delete calvin
k3d cluster create calvin --port "8080:80@loadbalancer"

# 3. 重新部署应用
cd docker/k8s
./local-deploy.sh

# 4. 测试访问
curl http://localhost:8080
```

#### 404 Not Found

**症状**：可以访问 localhost:8080，但返回 404

**解决方案**：

```bash
# 1. 检查 Ingress 路由规则
kubectl get ingress storyboard-ingress -o yaml

# 2. 验证 Service 端点
kubectl get endpoints storyboard-frontend
kubectl get endpoints storyboard-api

# 3. 测试后端服务
kubectl port-forward svc/storyboard-frontend 5173:80
curl http://localhost:5173

# 4. 检查 Nginx 配置
kubectl get configmap nginx-config -o yaml

# 5. 重新部署 Ingress
kubectl delete -f docker/k8s/ingress.yaml
kubectl apply -f docker/k8s/ingress.yaml
```

#### API 请求 CORS 错误

**症状**：浏览器控制台显示 CORS 错误

**解决方案**：

```bash
# 1. 检查 Nginx ConfigMap
kubectl get configmap nginx-config -o yaml

# 确保包含 CORS 配置：
# add_header 'Access-Control-Allow-Origin' '*';
# add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';

# 2. 更新 ConfigMap
kubectl apply -f docker/k8s/nginx-configmap.yaml

# 3. 重启 Frontend
kubectl rollout restart deployment/storyboard-frontend

# 4. 清除浏览器缓存并重试
```

---

## 镜像更新不生效

### 诊断步骤

```bash
# 1. 确认镜像已重新构建
docker images | grep script-to-storyboards

# 检查镜像创建时间（应该是最新的）

# 2. 检查 Pod 使用的镜像
kubectl describe pod <pod-name> | grep Image:

# 3. 查看镜像拉取策略
kubectl get deployment storyboard-api -o yaml | grep imagePullPolicy
```

### 解决方案

```bash
# 方式1: 重新导入并强制重启
# 1. 重新构建镜像
docker-compose -f docker/compose/docker-compose.yml build

# 2. 导入到集群
k3d image import script-to-storyboards-api:latest -c calvin --overwrite

# 3. 删除旧 Pod（会自动创建新 Pod）
kubectl delete pods -l app=storyboard-api

# 方式2: 使用镜像摘要
# 1. 获取镜像 ID
docker images script-to-storyboards-api:latest --format "{{.ID}}"

# 2. 修改 Deployment 使用具体镜像 ID
kubectl set image deployment/storyboard-api \
  api=script-to-storyboards-api@sha256:<image-hash>

# 方式3: 强制滚动更新
kubectl rollout restart deployment/storyboard-api

# 方式4: 删除并重新创建 Deployment
kubectl delete -f docker/k8s/api-deployment.yaml
kubectl apply -f docker/k8s/api-deployment.yaml
```

---

## 网络连接问题

### Pod 之间无法通信

**诊断**：

```bash
# 从 API Pod 测试 Redis 连接
kubectl exec -it deployment/storyboard-api -- ping storyboard-redis
kubectl exec -it deployment/storyboard-api -- nc -zv storyboard-redis 6379

# 检查 NetworkPolicy（如果配置了）
kubectl get networkpolicies
```

**解决方案**：

```bash
# 1. 检查 Service 配置
kubectl get svc
kubectl describe svc storyboard-redis

# 2. 验证 DNS 解析
kubectl exec -it deployment/storyboard-api -- nslookup storyboard-redis

# 3. 检查 Pod 标签和 Service 选择器匹配
kubectl get pods --show-labels
kubectl get svc storyboard-redis -o yaml | grep selector

# 4. 临时删除 NetworkPolicy（如果存在）
kubectl delete networkpolicy --all
```

---

## 资源不足问题

### 诊断

```bash
# 查看节点资源使用
kubectl top nodes

# 查看 Pod 资源使用
kubectl top pods

# 查看资源配额（如果配置了）
kubectl describe resourcequotas
```

### 解决方案

```bash
# 方式1: 降低资源请求
vim docker/k8s/api-deployment.yaml

# 修改 resources 部分
resources:
  requests:
    cpu: 100m        # 降低 CPU 请求
    memory: 128Mi    # 降低内存请求
  limits:
    cpu: 500m
    memory: 256Mi

kubectl apply -f docker/k8s/api-deployment.yaml

# 方式2: 删除不必要的 Pod
kubectl delete pod <unused-pod-name>

# 方式3: 扩展集群（生产环境）
# 添加更多节点到集群
```

---

## 配置问题

### ConfigMap 更新不生效

**解决方案**：

```bash
# 1. 更新 ConfigMap
kubectl apply -f docker/k8s/nginx-configmap.yaml

# 2. 重启使用该 ConfigMap 的 Pod
kubectl rollout restart deployment/storyboard-frontend

# 3. 验证 ConfigMap 已更新
kubectl get configmap nginx-config -o yaml
```

### 环境变量错误

**解决方案**：

```bash
# 1. 检查当前环境变量
kubectl describe deployment/storyboard-api | grep -A 30 "Environment"

# 2. 修改 Deployment YAML
vim docker/k8s/api-deployment.yaml

# 3. 应用更改
kubectl apply -f docker/k8s/api-deployment.yaml

# 4. 验证 Pod 内环境变量
kubectl exec -it deployment/storyboard-api -- env | grep DB_
```

---

## 查看完整状态

### 一键查看所有资源

```bash
# 查看特定应用的所有资源
kubectl get all -l app=storyboard-api
kubectl get all -l app=storyboard-frontend
kubectl get all -l app=storyboard-redis

# 查看所有 Pod 事件
kubectl get events --sort-by=.metadata.creationTimestamp

# 查看所有资源状态
kubectl get all
```

### 使用 k9s 可视化调试

```bash
# 启动 k9s
k9s

# 常用操作：
# 1. 按 :pods 查看所有 Pod
# 2. 选择 Pod 后按 l 查看日志
# 3. 按 d 查看详细信息
# 4. 按 s 进入 Shell
# 5. 按 Ctrl+C 退出
```

### 完整诊断脚本

创建 `diagnose.sh`:

```bash
#!/bin/bash
echo "=== Cluster Info ==="
kubectl cluster-info
echo ""

echo "=== Nodes ==="
kubectl get nodes
echo ""

echo "=== Deployments ==="
kubectl get deployments
echo ""

echo "=== Pods ==="
kubectl get pods
echo ""

echo "=== Services ==="
kubectl get services
echo ""

echo "=== Ingress ==="
kubectl get ingress
echo ""

echo "=== Events (Last 20) ==="
kubectl get events --sort-by=.metadata.creationTimestamp | tail -20
echo ""

echo "=== Pod Logs (API) ==="
kubectl logs --tail=50 deployment/storyboard-api
echo ""

echo "=== Pod Logs (Frontend) ==="
kubectl logs --tail=50 deployment/storyboard-frontend
```

---

## 相关文档

- [常用运维命令](operations.md)
- [本地 K8s 部署](local-deployment.md)
- [生产环境部署](remote-deployment.md)
- [Kubernetes 部署总览](deployment.md)
