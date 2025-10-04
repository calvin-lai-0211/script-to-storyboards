# Background Task Processor 部署指南

## 概述

Background Task Processor 是处理异步图片生成任务的后台进程。它已集成到 API 容器中，通过 supervisor 进行管理，无需单独部署。

## 部署方式

### Docker Compose（本地开发）

```bash
cd docker
docker-compose up -d
```

容器启动后，supervisor 会自动启动以下进程：
- **API**: FastAPI 服务（端口 8000）
- **Task Processor**: 后台任务处理器

### Kubernetes（生产环境）

```bash
cd docker/k8s
./local-deploy.sh
```

同样，supervisor 会在 Pod 中管理两个进程。

## 进程管理

### 查看进程状态

```bash
# Docker
docker exec -it storyboard-api supervisorctl status

# K8s
kubectl exec -it deployment/storyboard-api -- supervisorctl status
```

预期输出：
```
api               RUNNING   pid 10, uptime 0:05:23
task-processor    RUNNING   pid 11, uptime 0:05:22
```

### 查看日志

#### 所有日志

```bash
# Docker
docker logs -f storyboard-api

# K8s
kubectl logs -f deployment/storyboard-api
```

#### Task Processor 专用日志

**Supervisor 日志**（容器内）：

```bash
# Docker
docker exec -it storyboard-api tail -f /var/log/supervisor/task-processor.out.log

# K8s
kubectl exec -it deployment/storyboard-api -- tail -f /var/log/supervisor/task-processor.out.log
```

**应用日志**（推荐查看）：

```bash
# Docker Compose - 宿主机直接查看
tail -f logs/task_processor.log

# Docker Compose - 容器内查看
docker exec -it storyboard-api tail -f /app/logs/task_processor.log

# K8s - 容器内查看
kubectl exec -it deployment/storyboard-api -- tail -f /app/logs/task_processor.log

# K8s 本地 - 宿主机查看（k3d 映射）
tail -f /tmp/storyboard-logs/task_processor.log
```

#### API 专用日志

```bash
# Docker
docker exec -it storyboard-api tail -f /var/log/supervisor/api.out.log

# K8s
kubectl exec -it deployment/storyboard-api -- tail -f /var/log/supervisor/api.out.log
```

### 重启进程

#### 重启单个进程

```bash
# Docker
docker exec -it storyboard-api supervisorctl restart task-processor
docker exec -it storyboard-api supervisorctl restart api

# K8s
kubectl exec -it deployment/storyboard-api -- supervisorctl restart task-processor
kubectl exec -it deployment/storyboard-api -- supervisorctl restart api
```

#### 重启整个容器

```bash
# Docker
docker restart storyboard-api

# K8s
kubectl rollout restart deployment/storyboard-api
```

## 健壮性特性

### Supervisor 自动恢复

- **自动重启**: 如果 task processor 崩溃，supervisor 会在 5 秒后自动重启
- **最大重试**: `startretries=10`，最多尝试 10 次启动
- **独立运行**: Task processor 失败不会影响 API 服务

### Task Processor 自愈机制

1. **连续错误检测**: 连续 10 次错误后自动重新初始化数据库连接
2. **指数退避**: 错误后等待时间递增（3s → 6s → 9s → ... 最多 30s）
3. **数据库重连**: 连接失败时自动重建 Database 和 AITaskManager 实例
4. **信号处理**: 正确响应 SIGTERM/SIGINT 信号优雅退出

## 配置参数

### Supervisor 配置

位于 `docker/supervisor/supervisord.conf`：

```ini
[program:task-processor]
command=python background/task_processor.py
autostart=true
autorestart=true
startretries=10
startsecs=5
stopwaitsecs=30
stopsignal=TERM
```

### Task Processor 配置

位于 `utils/config.py` 的 `TASK_PROCESSOR_CONFIG`（已统一配置）：

```python
TASK_PROCESSOR_CONFIG = {
    'poll_interval': 3,          # 轮询间隔（秒）
    'task_timeout': 10,          # 任务超时时间（分钟）
    'max_pending_batch': 5,      # 每次处理的 PENDING 任务数
    'max_active_batch': 20,      # 每次查询的 ACTIVE 任务数
    'max_consecutive_errors': 10 # 连续错误阈值
}
```

## 故障排查

### Task Processor 未启动

```bash
# 检查 supervisor 状态
kubectl exec -it deployment/storyboard-api -- supervisorctl status

# 查看错误日志
kubectl exec -it deployment/storyboard-api -- tail -100 /var/log/supervisor/task-processor.err.log
```

常见原因：
1. 数据库连接失败（检查 `utils/config.py` 中的 DB_CONFIG）
2. Python 依赖缺失（检查 `api/requirements.txt`）
3. 环境变量未设置

### Task Processor 频繁重启

```bash
# 查看重启次数
kubectl exec -it deployment/storyboard-api -- supervisorctl tail -1000 task-processor stderr
```

常见原因：
1. 数据库连接不稳定
2. RunningHub API 配置错误
3. 内存不足（检查 K8s limits）

### 任务卡在 PENDING 状态

```bash
# 检查 task processor 是否运行
kubectl exec -it deployment/storyboard-api -- supervisorctl status task-processor

# 检查日志中是否有提交任务的记录
kubectl exec -it deployment/storyboard-api -- grep "提交任务" /var/log/supervisor/task-processor.out.log
```

可能原因：
1. Task processor 未运行
2. RunningHub 并发控制限制（max 3 concurrent）
3. 数据库查询失败

### 查看数据库中的任务状态

```bash
# 进入 API 容器
kubectl exec -it deployment/storyboard-api -- bash

# 连接数据库并查询
psql -h <DB_HOST> -U <DB_USER> -d <DB_NAME> -c "SELECT id, status, entity_name, created_at FROM ai_tasks ORDER BY created_at DESC LIMIT 10;"
```

## 本地调试（不使用 Docker）

### 方式 A：使用一键启动脚本（推荐）

```bash
# 同时启动 API 和 Task Processor
./dev_start.py

# 查看 Task Processor 日志
tail -f logs/task_processor.log
```

### 方式 B：单独启动 Task Processor

```bash
# 启动（前台运行，便于查看日志）
python background/task_processor.py

# 查看日志
tail -f logs/task_processor.log
```

### 日志路径说明

| 环境 | 宿主机路径 | 容器内路径 | 查看方式 |
|------|-----------|-----------|---------|
| **本地开发** | `logs/task_processor.log` | N/A | `tail -f logs/task_processor.log` |
| **Docker Compose** | `logs/task_processor.log` | `/app/logs/task_processor.log` | `tail -f logs/task_processor.log` 或 `docker exec ... tail -f /app/logs/...` |
| **K8s 本地** | `/tmp/storyboard-logs/task_processor.log` | `/app/logs/task_processor.log` | `kubectl exec ... tail -f /app/logs/...` |
| **K8s 生产** | N/A | `/app/logs/task_processor.log` | `kubectl logs -f deployment/storyboard-api` |

## 监控建议

### 关键指标

1. **进程运行时间**: `supervisorctl status` 中的 uptime
2. **任务处理速度**: 日志中每分钟处理的任务数
3. **错误率**: stderr 日志中的错误频率
4. **数据库任务积压**: `SELECT COUNT(*) FROM ai_tasks WHERE status = 'PENDING'`

### 日志监控

```bash
# 实时监控关键日志
kubectl exec -it deployment/storyboard-api -- tail -f /var/log/supervisor/task-processor.out.log | grep -E "(错误|失败|超时|重试)"
```

### 告警建议

- Task processor 停止运行 > 5 分钟
- PENDING 任务数 > 100
- 连续错误 > 5 次
- 容器重启次数 > 3 次/小时

## 参考文档

- [异步图片生成架构](./async-image-generation.md)
- [Kubernetes 部署指南](../k8s/README.md)
- [Supervisor 官方文档](http://supervisord.org/)
