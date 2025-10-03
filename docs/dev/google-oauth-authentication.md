# Google OAuth 登录配置指南

本文档说明如何配置和使用 Google OAuth 2.0 登录功能。

## 快速开始

### 1. 获取 Google OAuth 凭证

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 Google+ API
4. 创建 OAuth 2.0 客户端 ID（应用类型：Web 应用）
5. 配置授权重定向 URI：
   - 开发环境: `http://localhost:8001/api/user/google/callback`
   - 生产环境: `https://yourdomain.com/api/user/google/callback`

### 2. 配置项目

编辑 `utils/config.py`，填入你的 Google OAuth 凭证：

```python
GOOGLE_OAUTH_CONFIG = {
    "client_id": "YOUR_GOOGLE_CLIENT_ID",
    "client_secret": "YOUR_GOOGLE_CLIENT_SECRET",
    "redirect_path": "/api/user/google/callback",
    ...
}

# 配置 API 域名（生产环境需修改）
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
```

### 3. 启动 Redis

```bash
# Docker Compose
cd docker/compose
docker-compose up -d redis

# 或本地启动（端口 6379）
redis-server
```

### 4. 初始化数据库

```bash
PYTHONPATH=. python utils/database.py
```

### 5. 启动 API 服务

```bash
cd api
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## 环境配置

### 开发环境

默认配置即可使用，无需额外设置：

```bash
# 使用默认配置
python -m uvicorn api.main:app --port 8001
```

### 生产环境（Kubernetes）

在 `docker/k8s/api-deployment.yaml` 中配置环境变量：

```yaml
env:
  - name: API_BASE_URL
    value: "https://yourdomain.com"
  - name: REDIS_HOST
    value: "storyboard-redis"
  - name: REDIS_PORT
    value: "6379"
```

部署：

```bash
kubectl apply -f docker/k8s/redis-deployment.yaml
kubectl apply -f docker/k8s/api-deployment.yaml
```

### Docker Compose

修改 `docker/compose/docker-compose.yml` 中的环境变量：

```yaml
api:
  environment:
    - API_BASE_URL=https://yourdomain.com
```

启动：

```bash
docker-compose up -d
```

## API 使用

### 认证流程

```
1. 用户访问受保护的 API
   ↓
2. 检查登录状态 (GET /api/user/check-login)
   ↓
3. 未登录 → 返回 Google 授权 URL → 跳转登录
   ↓
4. 用户授权 → Google 回调 (GET /api/user/google/callback)
   ↓
5. 后端获取用户信息 → 创建 Session → 设置 Cookie
   ↓
6. 重定向回原页面 → 登录成功 ✅
```

### API 端点

| 端点 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/user/check-login` | GET | 检查登录状态 | 否 |
| `/api/user/logout` | POST | 退出登录 | 否 |
| `/api/user/google/callback` | GET | Google OAuth 回调 | 否 |
| `/api/storyboards/*` | GET/POST | 故事板相关 | 是 |
| `/api/characters/*` | GET/POST | 角色相关 | 是 |
| `/api/scenes/*` | GET/POST | 场景相关 | 是 |

### 前端集成示例

#### 检查登录状态

```javascript
async function checkLogin() {
  const response = await fetch('/api/user/check-login', {
    credentials: 'include'  // 重要：发送 cookies
  });

  const data = await response.json();

  if (data.code === 401) {
    // 未登录，跳转到 Google 登录
    window.location.href = data.data.auth_url;
  } else {
    // 已登录
    console.log('当前用户:', data.data.user);
  }
}
```

#### 调用受保护的 API

```javascript
async function fetchStoryboards(key) {
  const response = await fetch(`/api/storyboards/${key}`, {
    credentials: 'include'  // 自动发送 session cookie
  });

  if (response.status === 401) {
    // Session 过期，重新登录
    await checkLogin();
  } else {
    return await response.json();
  }
}
```

#### 退出登录

```javascript
async function logout() {
  await fetch('/api/user/logout', {
    method: 'POST',
    credentials: 'include'
  });

  window.location.href = '/';
}
```

## 后端开发

### 添加受保护的路由

```python
from fastapi import APIRouter, Depends
from api.middleware.auth import require_auth, UserPrincipal

router = APIRouter(prefix="/api")

@router.get("/my-protected-route")
async def my_route(user: UserPrincipal = Depends(require_auth)):
    """需要登录才能访问"""
    user_id = user.get("user_id")
    email = user.get("email")

    return {
        "message": f"Hello {user.get('name')}",
        "user_id": user_id
    }
```

### 可选认证（登录和未登录都可访问）

```python
from api.middleware.auth import get_current_user, UserPrincipal

@router.get("/optional-auth-route")
async def optional_route(user: UserPrincipal = Depends(get_current_user)):
    """登录用户可获得额外功能"""
    if user.is_authenticated:
        return {"message": f"Welcome back, {user.get('name')}!"}
    else:
        return {"message": "Welcome, guest!"}
```

## 技术细节

### Session 存储

- **存储引擎**: Redis (支持内存 fallback)
- **Key 格式**: `st_session:{session_id}`
- **过期时间**: 2592000 秒（30 天）
- **自动续期**: 每次访问时重置 TTL

### Session 数据结构

```json
{
  "data": {
    "user": {
      "user_id": 1,
      "open_id": "google_user_id",
      "platform": "google",
      "status": 1,
      "email": "user@example.com",
      "name": "User Name",
      "picture": "https://..."
    },
    "token_info": {
      "access_token": "...",
      "expires_in": 3600,
      "refresh_token": "..."
    }
  },
  "created_at": 1234567890.123,
  "last_accessed": 1234567890.123
}
```

### Cookie 安全设置

```python
response.set_cookie(
    key="st_sess_id",
    value=session_id,
    max_age=2592000,      # 30 天
    path="/",
    httponly=True,         # 防止 XSS 攻击
    samesite="lax",        # 防止 CSRF 攻击
    secure=False           # 生产环境设为 True（需 HTTPS）
)
```

### 数据库表结构

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    open_id VARCHAR(200) DEFAULT '' UNIQUE,
    avatar VARCHAR(300) DEFAULT '',
    email VARCHAR(100) DEFAULT '',
    name VARCHAR(50) DEFAULT '',
    platform VARCHAR(50) DEFAULT '',
    status SMALLINT DEFAULT 1,
    is_deleted SMALLINT DEFAULT 0,
    create_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_open_id_platform ON users(open_id, platform) WHERE is_deleted = 0;
```

## 故障排查

### redirect_uri_mismatch 错误

**原因**: Google 回调的 redirect_uri 与 Google Cloud Console 配置不匹配

**解决方法**:
1. 检查当前 `API_BASE_URL` 环境变量值
2. 确认完整 redirect_uri: `{API_BASE_URL}/api/user/google/callback`
3. 在 Google Cloud Console 中添加对应的 redirect_uri

```bash
# 查看当前配置
echo $API_BASE_URL
# 例如: https://gaudi.gaudivideo.com

# 完整 redirect_uri:
# https://gaudi.gaudivideo.com/api/user/google/callback
```

### Redis 连接失败

系统会自动降级到内存存储（fallback），但重启后 session 会丢失。

**检查 Redis 连接**:
```bash
redis-cli ping
# 返回 PONG 表示正常
```

**查看日志**:
```
WARNING: Failed to connect to Redis: ... Using in-memory fallback.
```

### Session 验证失败

**常见原因**:
1. Cookie 未发送 → 前端请求添加 `credentials: 'include'`
2. Session 已过期 → 重新登录
3. Redis 数据丢失 → 检查 Redis 持久化配置

**调试方法**:
```bash
# 查看 Redis 中的 session
redis-cli
KEYS st_session:*
GET st_session:{session_id}
TTL st_session:{session_id}
```

## 环境变量参考

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `API_BASE_URL` | API 服务域名 | `http://localhost:8001` | `https://yourdomain.com` |
| `REDIS_HOST` | Redis 主机地址 | `localhost` | `redis-service` |
| `REDIS_PORT` | Redis 端口 | `6379` | `6379` |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | - | `123456.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | - | `GOCSPX-xxx` |

## 安全建议

1. ✅ 生产环境使用 HTTPS
2. ✅ 设置 Cookie `Secure` 标志（HTTPS 环境）
3. ✅ 定期更新 Google OAuth 凭证
4. ✅ 监控异常登录行为
5. ✅ Redis 配置密码保护
6. ✅ 定期备份用户数据

## 相关资源

- [Google OAuth 2.0 文档](https://developers.google.com/identity/protocols/oauth2)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Redis 文档](https://redis.io/documentation)
