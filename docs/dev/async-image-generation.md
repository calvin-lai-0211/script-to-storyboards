# 异步图片生成架构文档

## 概述

本项目实现了两种图片生成模式：

1. **同步模式**：脚本直接调用，适合批量处理
2. **异步模式**：API 调用，通过任务表和后台处理器，适合用户交互

## 架构图

```
┌─────────────────────────────────────────────────────────┐
│                   使用场景                               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  【脚本调用】                    【API 调用】            │
│                                                         │
│  python procedure/              前端点击"生成图片"      │
│    make_portraits_from_t2i.py                          │
│         │                              │               │
│         │                              │               │
│         ↓                              ↓               │
│  ┌──────────────┐              ┌──────────────┐       │
│  │ generate_    │              │ POST /submit-│       │
│  │ image()      │              │ task         │       │
│  │              │              │              │       │
│  │ 直接轮询等待  │              │ 创建任务记录  │       │
│  │ 不使用任务表  │              │ 返回 task_id │       │
│  └──────────────┘              └──────┬───────┘       │
│         │                              │               │
│         │                              ↓               │
│         │                      ┌──────────────┐       │
│         │                      │ ai_tasks     │       │
│         │                      │ 表           │       │
│         │                      └──────┬───────┘       │
│         │                              │               │
│         │                              ↓               │
│         │                      ┌──────────────┐       │
│         │                      │ 后台处理器    │       │
│         │                      │ task_        │       │
│         │                      │ processor.py │       │
│         │                      └──────┬───────┘       │
│         │                              │               │
│         └──────────────┬───────────────┘               │
│                        │                               │
│                        ↓                               │
│              ┌────────────────────┐                    │
│              │ RunningHub API     │                    │
│              │ (Jimeng T2I)       │                    │
│              └────────────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

## 数据库表结构

### ai_tasks 表

用于 API 异步任务管理，脚本调用**不使用**此表。

```sql
CREATE TABLE ai_tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE,           -- RunningHub task_id
    task_type VARCHAR(50) NOT NULL,        -- character_image/scene_image/prop_image
    entity_type VARCHAR(50) NOT NULL,      -- character/scene/prop
    entity_id INTEGER NOT NULL,

    status VARCHAR(20) DEFAULT 'PENDING',  -- 任务状态

    prompt TEXT NOT NULL,
    result_url TEXT,                       -- CDN URL
    r2_key TEXT,
    error_message TEXT,

    drama_name VARCHAR(255),
    episode_number INTEGER,
    entity_name VARCHAR(255),

    created_at TIMESTAMP DEFAULT NOW(),
    submitted_at TIMESTAMP,
    completed_at TIMESTAMP,
    last_poll_at TIMESTAMP,

    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3
);

-- 关键索引
CREATE INDEX idx_ai_tasks_status ON ai_tasks(status);
CREATE INDEX idx_ai_tasks_task_id ON ai_tasks(task_id);
CREATE INDEX idx_ai_tasks_entity ON ai_tasks(entity_type, entity_id);
CREATE INDEX idx_ai_tasks_created_at ON ai_tasks(created_at);
```

### 任务状态流转

```
PENDING → SUBMITTED → QUEUED → RUNNING → SUCCESS
   ↓          ↓          ↓         ↓          ↓
FAILED ← ─────┴──────────┴─────────┘          (完成)
   ↓
TIMEOUT (超过10分钟)
   ↓
重试 (retry_count < max_retries) → PENDING
```

## 时间限制策略

为避免处理器处理过期任务，所有查询都加上了 **30 天**时间限制：

```python
# 只处理 30 天内创建的任务
SELECT * FROM ai_tasks
WHERE status = 'PENDING'
AND created_at > NOW() - INTERVAL '30 days'
```

超过 30 天的任务：

- ✅ 不会被后台处理器处理
- ✅ 前端仍可查询状态（如果保存了 task_id）
- ✅ 可通过 `cleanup_old_tasks()` 定期清理

## API 接口

### 1. 提交任务

```http
POST /api/character/{character_id}/submit-task
Content-Type: application/json

{
  "image_prompt": "角色描述..."
}
```

**响应**：

```json
{
  "code": 0,
  "data": {
    "task_id": "123",
    "status": "PENDING"
  }
}
```

### 2. 查询状态

```http
GET /api/character/{character_id}/task-status/{task_id}
```

**响应**：

```json
{
  "code": 0,
  "data": {
    "status": "SUCCESS",
    "image_url": "https://cdn.example.com/..."
  }
}
```

## 后台处理器

### 启动

```bash
# 前台运行（调试）
python background/task_processor.py

# 后台运行
bash background/start_processor.sh

# 停止
bash background/stop_processor.sh
```

### 处理流程

每 3 秒循环：

1. **处理 PENDING 任务**（最多 5 个/次）

   - 调用 `jimeng.submit_task()`
   - 更新状态为 SUBMITTED

2. **轮询 ACTIVE 任务**（最多 50 个/次）

   - 查询 SUBMITTED/QUEUED/RUNNING 状态
   - 调用 `jimeng.check_task_status()`
   - SUCCESS: 下载图片 → 上传 R2 → 更新数据库
   - FAIL: 标记为 FAILED

3. **处理超时任务**（超过 30 分钟）

   - 标记为 TIMEOUT

4. **重试失败任务**
   - 重置状态为 PENDING
   - 增加 retry_count

### 配置参数

```python
# config.py
TASK_PROCESSOR_CONFIG = {
    "poll_interval": 10,        # 轮询间隔（秒）
    "task_timeout": 30,        # 任务超时时间（分钟）
    "max_pending_batch": 5,    # 每次最多处理的 PENDING 任务数
    "max_active_batch": 50,    # 每次最多查询的 ACTIVE 任务数
    "max_consecutive_errors": 10  # 连续错误阈值
}
```

## 模型层 API

### JimengT2IRH 类

```python
from models.jimeng_t2i_RH import JimengT2IRH

jimeng = JimengT2IRH()

# 【同步模式】脚本使用，直接等待完成
result = jimeng.generate_image(prompt="...", use_concurrency_control=True)
# 返回: {'code': 0, 'data': {'images': [{'imageUrl': '...'}]}}

# 【异步模式】API 使用，立即返回
task_info = jimeng.submit_task(prompt="...", use_concurrency_control=True)
# 返回: {'task_id': 'xxx', 'status': 'QUEUED'}

# 查询状态
status = jimeng.check_task_status(task_id="xxx")
# 返回: {'status': 'SUCCESS', 'result': {...}}
```

## 任务管理器

```python
from utils.ai_task_manager import AITaskManager, TaskType, EntityType

manager = AITaskManager(db)

# 创建任务
task_id = manager.create_task(
    task_type=TaskType.CHARACTER_IMAGE,
    entity_type=EntityType.CHARACTER,
    entity_id=123,
    prompt="...",
    drama_name="天归",
    episode_number=1,
    entity_name="李明"
)

# 查询任务
task = manager.get_task(task_id)

# 更新任务
manager.update_task(
    task_id,
    status=TaskStatus.SUCCESS,
    result_url="https://..."
)

# 清理旧任务
manager.cleanup_old_tasks(days=30)
```

## 初始化和部署

### 1. 创建数据库表

首次部署时，需要初始化数据库表：

```python
from utils.database import Database
from utils.config import DB_CONFIG

# 使用 auto_init=True 创建所有表（包括 ai_tasks）
db = Database(DB_CONFIG, auto_init=True)
```

或者直接运行：

```bash
python utils/database.py
```

### 2. 启动后台处理器

#### 本地手动启动（开发调试）

```bash
# 直接运行
python background/task_processor.py

# 或使用启动脚本（后台运行）
./background/start_processor.sh

# 停止
./background/stop_processor.sh

# 查看日志
tail -f logs/task_processor.log
```

#### Docker/K8s 部署（推荐）

**无需手动操作！** Task processor 已集成到 API 容器中，通过 supervisor 自动管理：

```bash
# Docker Compose
cd docker
docker-compose up -d  # API 和 task processor 自动启动

# Kubernetes
cd docker/k8s
./local-deploy.sh  # API 和 task processor 自动部署
```

**查看 supervisor 状态**：

```bash
# Docker
docker exec -it storyboard-api supervisorctl status

# K8s
kubectl exec -it deployment/storyboard-api -- supervisorctl status
```

**查看 task processor 日志**：

```bash
# Docker
docker exec -it storyboard-api tail -f /var/log/supervisor/task-processor.out.log

# K8s
kubectl exec -it deployment/storyboard-api -- tail -f /var/log/supervisor/task-processor.out.log
```

#### Supervisor 配置

位于 `docker/supervisor/supervisord.conf`：

- **API 进程**: `priority=1`, 先启动
- **Task Processor 进程**: `priority=2`, 后启动
- **自动重启**: 崩溃后自动恢复
- **独立日志**: API 和 task processor 分开记录
- **优雅关闭**: SIGTERM 信号正确传递

#### 健壮性保障

Task processor 内置多重保障：

1. **连续错误检测**: 连续 10 次错误后自动重新初始化连接
2. **指数退避**: 错误后等待时间递增（3s → 6s → 9s...最多 30s）
3. **数据库重连**: 连接失败时自动重建 Database/AITaskManager
4. **信号处理**: 正确响应 SIGINT/SIGTERM 优雅退出
5. **Supervisor 监控**: 进程崩溃时 supervisor 自动重启

### 3. 前端部署

前端无需改动，已实现轮询逻辑。

## 监控和维护

### 查看任务统计

```python
from utils.ai_task_manager import AITaskManager
from utils.database import Database
from utils.config import DB_CONFIG

db = Database(DB_CONFIG)
manager = AITaskManager(db)

stats = manager.get_task_stats()
print(stats)
# {'PENDING': 5, 'RUNNING': 3, 'SUCCESS': 120, 'FAILED': 2}
```

### 日志文件

```bash
# 后台处理器日志
tail -f logs/task_processor.log
```

### 定期清理

建议设置 cron 任务每周清理：

```bash
# crontab -e
0 2 * * 0 cd /path/to/project && python -c "from utils.ai_task_manager import AITaskManager; from utils.database import Database; from utils.config import DB_CONFIG; AITaskManager(Database(DB_CONFIG)).cleanup_old_tasks(30)"
```

## 故障排查

### 任务一直是 PENDING

**原因**：后台处理器未运行

**解决**：

```bash
bash background/start_processor.sh
```

### 任务一直是 RUNNING

**原因**：

1. 图片生成确实需要很长时间
2. 超过 10 分钟会自动标记为 TIMEOUT

**检查**：

```python
# 手动查询 RunningHub 状态
from models.jimeng_t2i_RH import JimengT2IRH
jimeng = JimengT2IRH()
status = jimeng.check_task_status("runninghub_task_id")
```

### 服务重启后任务丢失？

**不会丢失**！所有任务都存在数据库中，后台处理器重启后会继续处理。

### 前端刷新后找不到任务？

前端应该保存 `task_id`，可以使用 localStorage 或 URL 参数。

## 性能优化建议

### 1. 调整批处理大小

任务量大时，可增加批处理大小：

```python
# background/task_processor.py
max_pending_batch = 10  # 默认 5
max_active_batch = 50   # 默认 20
```

### 2. 调整轮询间隔

```python
poll_interval = 2  # 默认 3 秒，降低延迟
```

### 3. 多进程处理

如果单个处理器性能不够，可以启动多个：

```bash
# 启动 3 个处理器实例
for i in {1..3}; do
    python background/task_processor.py &
done
```

数据库锁会确保不重复处理。

## 总结

| 特性     | 同步模式           | 异步模式               |
| -------- | ------------------ | ---------------------- |
| 使用场景 | 脚本批量处理       | API 用户交互           |
| 调用方法 | `generate_image()` | `submit_task()` + 轮询 |
| 任务表   | ❌ 不使用          | ✅ 使用                |
| 并发控制 | 内存计数器         | 数据库 + 后台处理器    |
| 服务重启 | 任务失败           | 任务保留               |
| 前端体验 | 长连接超时         | 实时进度               |
| 适用场景 | 一次性生成大量图片 | 用户按需生成           |
