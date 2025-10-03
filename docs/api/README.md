# API 文档

## 概述

Script-to-Storyboards API 提供了完整的 RESTful API 接口，用于管理剧本、分镜、角色、场景等数据。

## API 文档访问

### Swagger UI (推荐)

启动 API 服务器后，访问：

```
http://localhost:8001/docs
```

这是 FastAPI 自动生成的交互式 API 文档，提供：
- 完整的 API 端点列表
- 请求/响应示例
- 在线测试功能
- Schema 定义

### ReDoc

访问：

```
http://localhost:8001/redoc
```

更美观的文档界面，适合阅读。

## 基础信息

### Base URL

```
开发环境: http://localhost:8001
生产环境: https://your-domain.com
```

### 响应格式

所有 API 响应都遵循统一格式：

```json
{
  "code": 0,           // 0 表示成功，非 0 表示错误
  "message": "success", // 消息描述
  "data": {}           // 实际数据
}
```

### 错误码

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1 | 通用错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 主要 API 端点

### 1. 剧本 (Scripts)

#### 获取所有剧本

```http
GET /api/scripts
```

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "scripts": [
      {
        "key": "uuid-string",
        "title": "剧本名",
        "episode_num": 1,
        "author": "作者",
        "creation_year": 2024
      }
    ]
  }
}
```

#### 获取单个剧本详情

```http
GET /api/scripts/{key}
```

**参数**:
- `key` (path): 剧本唯一标识符

**响应**: 包含剧本完整内容（content）、角色列表（roles）、场景列表（sceneries）

### 2. 分镜 (Storyboards)

#### 获取剧集分镜

```http
GET /api/storyboards/{key}
```

**参数**:
- `key` (path): 剧本唯一标识符

**响应**: 分镜脚本的扁平化数据，包含场景、镜头、子镜头等层级信息

**数据结构**:
- `scene_number`: 场景编号
- `scene_description`: 场景描述
- `shot_number`: 镜头编号
- `shot_description`: 镜头描述
- `sub_shot_number`: 子镜头编号
- `camera_angle`: 镜头角度/景别
- `characters`: 涉及角色列表
- `scene_context`: 场景上下文列表
- `key_props`: 关键道具列表
- `image_prompt`: 图像生成提示词
- `dialogue_sound`: 对白/音效
- `duration_seconds`: 时长（秒）
- `notes`: 导演备注

### 3. 角色 (Characters)

#### 获取所有角色

```http
GET /api/characters/all
```

#### 获取指定剧集的角色

```http
GET /api/characters/{key}
```

#### 获取单个角色详情

```http
GET /api/character/{id}
```

#### 更新角色提示词

```http
POST /api/character/{id}/prompt
Content-Type: application/json

{
  "image_prompt": "新的图像生成提示词"
}
```

#### 生成角色图片

```http
POST /api/character/{id}/generate-image
Content-Type: application/json

{
  "model": "jimeng"  // 可选: "jimeng" 或 "qwen"
}
```

### 4. 场景 (Scenes)

#### 获取所有场景

```http
GET /api/scenes/all
```

#### 获取指定剧集的场景

```http
GET /api/scenes/{key}
```

#### 获取单个场景详情

```http
GET /api/scene/{id}
```

### 5. 道具 (Props)

#### 获取所有道具

```http
GET /api/props/all
```

### 6. 剧集记忆 (Memory)

#### 获取剧集摘要

```http
GET /api/memory/{key}
```

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "script_name": "剧本名",
    "episode_number": 1,
    "plot_summary": "剧情摘要文本...",
    "options": {},
    "created_at": "2024-01-01T00:00:00"
  }
}
```

## 前端集成

### API Client

前端使用统一的 `apiCall` 函数调用 API：

```typescript
import { API_ENDPOINTS, apiCall } from '@api';

// 获取剧本
const script = await apiCall(API_ENDPOINTS.getScript(key));

// 获取分镜
const storyboards = await apiCall(API_ENDPOINTS.getStoryboards(key));
```

### 请求去重

所有 API 请求会自动去重，并发的相同请求会合并为一个实际的 HTTP 请求。

### 缓存策略

前端使用 Zustand Store 缓存 API 响应数据：

1. 首次请求：从 API 获取数据并缓存
2. 后续访问：直接使用缓存
3. 手动刷新：点击刷新按钮重新请求

## 开发环境设置

### 启动 API 服务器

```bash
# 进入 api 目录
cd api

# 安装依赖
pip install -r requirements.txt

# 启动服务器
uvicorn main:app --reload --port 8001
```

### 环境变量

在 `api/.env` 文件中配置：

```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
API_BASE_URL=http://localhost:8001
```

## 生产部署

参考 [Kubernetes 部署文档](../k8s/README.md)

## 常见问题

### 1. CORS 错误

API 服务器已配置允许前端跨域访问：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 前端开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. 请求超时

默认超时时间为 30 秒，可以在前端 `apiCall` 中通过 `AbortController` 控制。

### 3. 数据格式

所有日期时间字段使用 ISO 8601 格式：`2024-01-01T00:00:00`

## 未来计划

- [ ] 添加用户认证（JWT）
- [ ] 添加请求限流
- [ ] 添加 API 版本控制
- [ ] 添加 WebSocket 支持（实时更新）
- [ ] 添加文件上传接口
