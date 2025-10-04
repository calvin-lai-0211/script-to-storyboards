# API 文档

## 概述

Script-to-Storyboards API 提供了完整的 RESTful API 接口，用于管理剧本、分镜、角色、场景等数据。

**✨ 新功能**: 所有 API 端点现在都包含完整的 TypeScript 类型定义，Swagger/ReDoc 文档中可以查看详细的响应数据结构。

## 在线 API 文档和工具

- [Swagger UI](/api/docs) - 交互式 API 测试工具 (可直接调用接口)
- [ReDoc](/api/redoc) - 美观的 API 文档阅读界面 (类型定义展示更清晰)

## 本地 API 文档访问

### Swagger UI (推荐)

启动 API 服务器后，访问：

```
http://localhost:8001/docs
```

这是 FastAPI 自动生成的交互式 API 文档，提供：

- ✅ 完整的 API 端点列表
- ✅ **详细的 TypeScript 类型定义**（不再显示 "any"）
- ✅ 请求/响应示例
- ✅ 在线测试功能
- ✅ Schema 定义（包含所有字段类型）

### ReDoc (更清晰的类型展示)

访问：

```
http://localhost:8001/redoc
```

更美观的文档界面，适合阅读。**推荐用于查看完整的类型定义**。

## 基础信息

### Base URL

```
开发环境: http://localhost:8001
生产环境: https://your-domain.com
```

### 响应格式

**所有 API 响应都遵循统一的包装格式**：
前端对统一返回结构的定义如下：

```typescript
interface ApiResponse<T> {
  code: number; // 0 表示成功，非 0 表示错误
  message: string; // 消息描述（默认 "success"）
  data: T | null; // 实际数据，类型为 T（泛型）
}
```

**示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "characters": [...],
    "count": 10
  }
}
```

**注意**: `data` 字段的类型因端点而异，详见各端点的具体类型定义。

### 错误码

| 错误码 | 说明           |
| ------ | -------------- |
| 0      | 成功           |
| 1      | 通用错误       |
| 404    | 资源不存在     |
| 500    | 服务器内部错误 |

## 主要 API 端点

### 1. 剧本 (Scripts)

#### 获取所有剧本

```http
GET /api/scripts
```

**响应类型**: `ScriptListResponse`

```typescript
interface ScriptListResponse {
  code: number;
  message: string;
  data: {
    scripts: ScriptMetadata[];
    count: number;
  };
}

interface ScriptMetadata {
  script_id: number | null;
  key: string;
  title: string;
  episode_num: number;
  author: string | null;
  creation_year: number | null;
  score: number | null;
}
```

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "scripts": [
      {
        "script_id": 1,
        "key": "da4ef19d-5965-41c3-a971-f17d0ce06ef7",
        "title": "天归（「西语版」） - Episode 1",
        "episode_num": 1,
        "author": "张馨月(moon)",
        "creation_year": 2025,
        "score": null
      }
    ],
    "count": 1
  }
}
```

#### 获取单个剧本详情

```http
GET /api/scripts/{key}
```

**参数**:

- `key` (path): 剧本唯一标识符

**响应类型**: `ScriptDetailResponse`

```typescript
interface ScriptDetail {
  script_id: number | null;
  key: string;
  title: string;
  episode_num: number;
  content: string; // 剧本完整内容
  roles: string[] | null; // 角色列表
  sceneries: string[] | null; // 场景列表
  author: string | null;
  creation_year: number | null;
  score: number | null;
}
```

### 2. 分镜 (Storyboards)

#### 获取剧集分镜

```http
GET /api/storyboards/{key}
```

**参数**:

- `key` (path): 剧本唯一标识符

**响应类型**: `StoryboardResponse`

```typescript
interface StoryboardResponse {
  code: number;
  message: string;
  data: {
    key: string;
    drama_name: string;
    episode_number: number;
    storyboards: FlatStoryboard[]; // 扁平化的分镜数据
    count: number;
  };
}

interface FlatStoryboard {
  id: number;
  scene_number: string; // 场景编号
  scene_description: string; // 场景描述
  shot_number: string; // 镜头编号
  shot_description: string; // 镜头描述
  sub_shot_number: string; // 子镜头编号
  camera_angle: string; // 镜头角度/景别
  characters: string[]; // 涉及角色列表
  scene_context: string[]; // 场景上下文列表
  key_props: string[]; // 关键道具列表
  image_prompt: string; // 图像生成提示词
  video_prompt: string | null; // 视频生成提示词
  dialogue_sound: string; // 对白/音效
  duration_seconds: number; // 时长（秒）
  notes: string; // 导演备注
}
```

**注意**: 前端会将扁平的 `storyboards` 数组转换为层级结构（Scene → Shot → SubShot）。

### 3. 角色 (Characters)

#### 获取所有角色

```http
GET /api/characters/all
```

**响应类型**: `CharacterListResponse`

```typescript
interface CharacterListResponse {
  code: number;
  message: string;
  data: {
    characters: CharacterPortrait[];
    count: number;
  };
}

interface CharacterPortrait {
  id: number;
  drama_name: string;
  episode_number: number;
  character_name: string;
  image_prompt: string | null;
  reflection: string | null;
  image_url: string | null;
  is_key_character: boolean;
  character_brief: string | null;
}
```

#### 获取指定剧集的角色

```http
GET /api/characters/{key}
```

**响应类型**: `CharactersByKeyResponse`

```typescript
interface CharactersByKeyResponse {
  code: number;
  message: string;
  data: {
    key: string;
    drama_name: string;
    episode_number: number;
    characters: CharacterPortrait[];
    count: number;
  };
}
```

#### 获取单个角色详情

```http
GET /api/character/{id}
```

**响应类型**: `CharacterDetailResponse` （数据结构与 `CharacterPortrait` 相同）

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

### 6. 图片上传 (Upload)

#### 上传图片

```http
POST /api/upload-image
Content-Type: multipart/form-data

file: <图片文件>
```

**响应类型**: `UploadImageResponse`

```typescript
interface UploadImageResponse {
  code: number;
  message: string;
  data: {
    url: string; // 上传后的图片 URL
  };
}
```

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "url": "http://example.com/images/uploaded-image.jpg"
  }
}
```

### 7. 剧集记忆 (Memory)

#### 获取剧集摘要

```http
GET /api/memory/{key}
```

**响应类型**: `MemoryResponse`

```typescript
interface MemoryResponse {
  code: number;
  message: string;
  data: EpisodeMemory;
}

interface EpisodeMemory {
  id: number;
  script_name: string;
  episode_number: number;
  plot_summary: string; // 剧情摘要文本
  options: string | null;
  created_at: string | null; // ISO 8601 格式
}
```

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "script_name": "天归（「西语版」）",
    "episode_number": 1,
    "plot_summary": "剧情摘要文本...",
    "options": null,
    "created_at": "2025-01-01T00:00:00"
  }
}
```

## 前端集成

### API Client

前端使用统一的 `apiCall` 函数调用 API：

```typescript
import { API_ENDPOINTS, apiCall } from "@api";

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
