# Kubernetes 运维命令指南

本文档提供 Script-to-Storyboards 应用在 Kubernetes 环境中的常用运维命令。

## 目录

- [查看资源状态](#查看资源状态)
- [查看日志](#查看日志)
- [重启服务](#重启服务)
- [更新部署](#更新部署)
- [缩放副本数](#缩放副本数)
- [进入容器调试](#进入容器调试)
- [清理资源](#清理资源)
- [快捷脚本](#快捷脚本)

---

## 查看资源状态

### 基础查询

```bash
# 查看所有部署
kubectl get deployments

# 输出示例：
# NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
# storyboard-api        1/1     1            1           10m
# storyboard-frontend   1/1     1            1           10m
# storyboard-redis      1/1     1            1           10m
```

```bash
# 查看所有 Pod
kubectl get pods

# 输出示例：
# NAME                                   READY   STATUS    RESTARTS   AGE
# storyboard-api-xxxxxxxxx-xxxxx        1/1     Running   0          10m
# storyboard-frontend-xxxxxxxxx-xxxxx   1/1     Running   0          10m
# storyboard-redis-xxxxxxxxx-xxxxx      1/1     Running   0          10m
```

```bash
# 查看所有服务
kubectl get services

# 输出示例：
# NAME                  TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
# storyboard-api        ClusterIP   10.43.123.45    <none>        8000/TCP   10m
# storyboard-frontend   ClusterIP   10.43.123.46    <none>        80/TCP     10m
# storyboard-redis      ClusterIP   10.43.123.47    <none>        6379/TCP   10m
```

```bash
# 查看 Ingress
kubectl get ingress

# 输出示例：
# NAME                 CLASS     HOSTS   ADDRESS       PORTS   AGE
# storyboard-ingress   traefik   *       192.168.1.1   80      10m
```

### 详细信息查询

```bash
# 查看 Deployment 详细信息
kubectl describe deployment storyboard-api

# 查看 Pod 详细信息
kubectl describe pod <pod-name>

# 查看 Service 详细信息
kubectl describe service storyboard-api

# 查看 ConfigMap 内容
kubectl describe configmap nginx-config
```

### 按标签过滤

```bash
# 查看特定应用的所有资源
kubectl get all -l app=storyboard-api
kubectl get all -l app=storyboard-frontend
kubectl get all -l app=storyboard-redis

# 查看所有带特定标签的 Pod
kubectl get pods -l app=storyboard-api
```

### 使用 k9s 可视化管理

```bash
# 启动 k9s（推荐）
k9s

# 常用快捷键：
# :pods      - 查看 Pod
# :deploy    - 查看 Deployment
# :svc       - 查看 Service
# :logs      - 查看日志
# d          - 删除资源
# l          - 查看日志
# s          - 进入 Shell
# Ctrl+C     - 退出
```

---

## 查看日志

### 实时日志

```bash
# 查看 API 日志（实时跟踪）
kubectl logs -f deployment/storyboard-api

# 查看 Frontend 日志
kubectl logs -f deployment/storyboard-frontend

# 查看 Redis 日志
kubectl logs -f deployment/storyboard-redis
```

### 特定 Pod 日志

```bash
# 查看特定 Pod 的日志
kubectl logs <pod-name>

# 实时跟踪特定 Pod 日志
kubectl logs -f <pod-name>

# 查看最近 100 行日志
kubectl logs --tail=100 <pod-name>

# 查看最近 1 小时的日志
kubectl logs --since=1h <pod-name>
```

### 崩溃 Pod 日志

```bash
# 查看之前崩溃的 Pod 日志
kubectl logs --previous <pod-name>

# 查看之前崩溃的 Pod 最后 50 行日志
kubectl logs --previous --tail=50 <pod-name>
```

### 多容器 Pod 日志

```bash
# 如果 Pod 有多个容器，指定容器名称
kubectl logs <pod-name> -c <container-name>

# 查看所有容器的日志
kubectl logs <pod-name> --all-containers=true
```

### 保存日志到文件

```bash
# 保存日志到文件
kubectl logs deployment/storyboard-api > api.log

# 保存最近 1000 行日志
kubectl logs --tail=1000 deployment/storyboard-api > api-recent.log
```

---

## 重启服务

### 滚动重启（推荐）

```bash
# 重启 API（会拉取最新镜像）
kubectl rollout restart deployment/storyboard-api

# 重启 Frontend
kubectl rollout restart deployment/storyboard-frontend

# 重启 Redis
kubectl rollout restart deployment/storyboard-redis

# 重启所有服务
kubectl rollout restart deployment/storyboard-api deployment/storyboard-frontend deployment/storyboard-redis
```

### 查看重启状态

```bash
# 查看重启进度
kubectl rollout status deployment/storyboard-api

# 输出示例：
# Waiting for deployment "storyboard-api" rollout to finish: 1 old replicas are pending termination...
# deployment "storyboard-api" successfully rolled out
```

### 删除 Pod 强制重启

```bash
# 删除特定 Pod（Kubernetes 会自动创建新 Pod）
kubectl delete pod <pod-name>

# 删除所有 API Pod
kubectl delete pods -l app=storyboard-api

# 删除所有 Pod（会自动重建）
kubectl delete pods --all
```

---

## 更新部署

### 使用更新脚本（推荐）

项目提供了快捷更新脚本：

```bash
cd docker/k8s

# 仅更新 API
./update-api.sh

# 仅更新 Frontend
./update-frontend.sh

# 更新 ConfigMap（Nginx 配置）
./update-config.sh
```

### 重新运行部署脚本

```bash
cd docker/k8s
./local-deploy.sh
```

### 手动更新

```bash
# 1. 修改 YAML 文件
vim docker/k8s/api-deployment.yaml

# 2. 应用更改
kubectl apply -f docker/k8s/api-deployment.yaml

# 3. 重启服务
kubectl rollout restart deployment/storyboard-api
```

### 更新镜像

```bash
# 1. 重新构建镜像
docker-compose -f docker/compose/docker-compose.yml build

# 2. 导入镜像到集群
k3d image import script-to-storyboards-api:latest -c calvin

# 3. 删除旧 Pod（会自动创建新 Pod）
kubectl delete pods -l app=storyboard-api
```

### 更新环境变量

```bash
# 1. 修改 Deployment YAML
vim docker/k8s/api-deployment.yaml

# 2. 应用更改
kubectl apply -f docker/k8s/api-deployment.yaml

# 3. 等待更新完成
kubectl rollout status deployment/storyboard-api
```

### 回滚部署

```bash
# 查看部署历史
kubectl rollout history deployment/storyboard-api

# 回滚到上一个版本
kubectl rollout undo deployment/storyboard-api

# 回滚到特定版本
kubectl rollout undo deployment/storyboard-api --to-revision=2
```

---

## 缩放副本数

### 手动缩放

```bash
# 扩展 API 到 3 个副本
kubectl scale deployment/storyboard-api --replicas=3

# 缩减到 1 个副本
kubectl scale deployment/storyboard-api --replicas=1

# 扩展 Frontend 到 2 个副本
kubectl scale deployment/storyboard-frontend --replicas=2
```

### 查看缩放状态

```bash
# 查看副本数
kubectl get deployment storyboard-api

# 输出示例：
# NAME             READY   UP-TO-DATE   AVAILABLE   AGE
# storyboard-api   3/3     3            3           20m

# 实时监控缩放过程
watch kubectl get pods
```

### 自动缩放（HPA）

```bash
# 配置基于 CPU 的自动扩缩容
kubectl autoscale deployment storyboard-api \
  --cpu-percent=70 \
  --min=1 \
  --max=5

# 查看 HPA 状态
kubectl get hpa

# 输出示例：
# NAME             REFERENCE                   TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
# storyboard-api   Deployment/storyboard-api   45%/70%   1         5         2          5m

# 删除 HPA
kubectl delete hpa storyboard-api
```

---

## 进入容器调试

### 进入容器 Shell

```bash
# 进入 API Pod
kubectl exec -it deployment/storyboard-api -- /bin/sh

# 进入特定 Pod
kubectl exec -it <pod-name> -- /bin/sh

# 进入 Frontend Pod（使用 bash）
kubectl exec -it deployment/storyboard-frontend -- /bin/bash
```

### 执行单次命令

```bash
# 在 API Pod 中执行 Python 命令
kubectl exec -it deployment/storyboard-api -- python -c "import sys; print(sys.version)"

# 检查环境变量
kubectl exec -it deployment/storyboard-api -- env | grep DB_

# 测试数据库连接
kubectl exec -it deployment/storyboard-api -- python -c "
from utils.database import Database
from utils.config import DB_CONFIG
db = Database(DB_CONFIG)
print('Database connection successful')
"
```

### 进入 Redis 调试

```bash
# 进入 Redis CLI
kubectl exec -it deployment/storyboard-redis -- redis-cli

# 执行 Redis 命令
kubectl exec -it deployment/storyboard-redis -- redis-cli ping
kubectl exec -it deployment/storyboard-redis -- redis-cli info
kubectl exec -it deployment/storyboard-redis -- redis-cli keys '*'
```

### 从容器复制文件

```bash
# 从 Pod 复制文件到本地
kubectl cp <pod-name>:/path/to/file ./local-file

# 从本地复制文件到 Pod
kubectl cp ./local-file <pod-name>:/path/to/file

# 示例：复制日志文件
kubectl cp storyboard-api-xxx:/app/logs/app.log ./app.log
```

---

## 清理资源

### 删除部署

```bash
# 删除单个 Deployment
kubectl delete deployment storyboard-api

# 删除所有相关资源
kubectl delete -f docker/k8s/api-deployment.yaml
```

### 删除所有应用资源

```bash
# 使用卸载脚本
cd docker/k8s
./undeploy.sh

# 或手动删除所有配置
kubectl delete -f docker/k8s/
```

### 删除 K8s 集群

```bash
# 删除 k3d 集群
k3d cluster delete calvin

# 删除 k3s（Linux）
sudo /usr/local/bin/k3s-uninstall.sh
```

### 清理未使用的资源

```bash
# 删除已完成的 Pod
kubectl delete pods --field-selector=status.phase==Succeeded

# 删除失败的 Pod
kubectl delete pods --field-selector=status.phase==Failed

# 强制删除卡住的 Pod
kubectl delete pod <pod-name> --grace-period=0 --force
```

---

## 快捷脚本

项目在 `docker/k8s/` 目录下提供了以下运维脚本：

### 部署脚本

```bash
# 一键本地部署
./local-deploy.sh

# 卸载应用
./undeploy.sh
```

### 更新脚本

```bash
# 更新 API 服务
./update-api.sh

# 更新 Frontend 服务
./update-frontend.sh

# 更新 Nginx 配置
./update-config.sh
```

### 自定义运维脚本示例

创建 `restart-all.sh`:

```bash
#!/bin/bash
echo "Restarting all services..."
kubectl rollout restart deployment/storyboard-redis
kubectl rollout restart deployment/storyboard-api
kubectl rollout restart deployment/storyboard-frontend
echo "Waiting for rollout to complete..."
kubectl rollout status deployment/storyboard-redis
kubectl rollout status deployment/storyboard-api
kubectl rollout status deployment/storyboard-frontend
echo "All services restarted successfully!"
```

创建 `status.sh`:

```bash
#!/bin/bash
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
```

---

## 相关文档

- [本地 K8s 部署](local-deployment.md)
- [故障排查指南](troubleshooting.md)
- [生产环境部署](remote-deployment.md)
- [Kubernetes 部署总览](deployment.md)
