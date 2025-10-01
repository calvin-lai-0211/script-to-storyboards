# API 路由说明

## 问题说明

在 K8s 部署时，所有流量都通过 80 端口的 Ingress 统一入口。前端和 API 需要使用相同的域名和端口。

## 解决方案

### 1. Ingress 配置

```yaml
spec:
  rules:
  - http:
      paths:
      - path: /api      # API 路径
        backend:
          service:
            name: storyboard-api
            port:
              number: 8000   # Service 端口（内部）
      - path: /         # 其他所有路径
        backend:
          service:
            name: storyboard-frontend
```

**说明**：
- `number: 8000` 是 **Service 的端口**，不是外部访问端口
- 外部访问都是 80 端口
- Ingress 负责将 80 端口的请求转发到内部 Service 的 8000 端口

### 2. 流量路径

```
浏览器请求                    Ingress                  Service              Pod
────────────────────────────────────────────────────────────────────────────
http://<ip>/                → 80端口                 → frontend:80      → Pod:80
  └─ 返回 HTML/JS/CSS

http://<ip>/api/character/1 → 80端口                 → api:8000         → Pod:8000
                               /api 路径匹配            内部Service端口     容器监听端口
```

### 3. 前端配置

**开发环境**（`.env` 或 `.env.local`）：
```bash
VITE_API_BASE_URL=http://localhost:8000
```

**K8s 部署**（`.env.k8s`）：
```bash
VITE_API_BASE_URL=""
```

**效果**：
- 开发环境：`http://localhost:8000/api/character/1`
- K8s 环境：`/api/character/1`（相对路径，自动使用当前域名）

### 4. 代码修改

`frontend/src/config/api.ts`：
```typescript
// 使用 ?? 而不是 ||，允许空字符串
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

// API 路径已经包含 /api 前缀
export const API_ENDPOINTS = {
  getCharacter: (id) => `${API_BASE_URL}/api/character/${id}`,
  // 开发环境：http://localhost:8000/api/character/1
  // K8s环境：/api/character/1
};
```

## 部署流程

部署脚本（`deploy.sh`）会自动：

1. 复制 `.env.k8s` → `.env`
2. 构建前端（使用空 API_BASE_URL）
3. 构建 Docker 镜像
4. 部署到 K8s

## 验证

### 从服务器上测试

```bash
# Frontend
curl http://localhost/

# API
curl http://localhost/api/health
curl http://localhost/api/docs
```

### 从浏览器访问

```
http://<server-ip>/              # Frontend
http://<server-ip>/api/health    # API health check
http://<server-ip>/api/docs      # API documentation
```

## 常见问题

### Q: 为什么 Ingress 配置是 8000 端口？

A: 这是 Service 的端口，不是外部端口。流程是：
```
外部:80 → Ingress:80 → Service:8000 → Pod:8000
```

### Q: 前端如何知道访问哪个端口？

A: 前端使用相对路径 `/api/...`，浏览器会自动使用当前页面的域名和端口（80）。

### Q: 如果我只部署 API，不部署 Ingress？

A: API 使用 ClusterIP，只能在集群内部访问。必须部署 Ingress 才能从外部访问。

### Q: 能否使用 NodePort 而不是 Ingress？

A: 可以，但需要：
1. 修改 Service 类型为 NodePort
2. 为 API 和 Frontend 分配不同的 NodePort
3. 前端配置正确的 API URL（包含端口号）

**不推荐**，因为：
- 需要开放多个端口
- 管理复杂
- 无法使用统一的 80 端口入口

## 相关文件

- `k8s/ingress.yaml` - Ingress 配置
- `frontend/.env.k8s` - K8s 环境变量
- `frontend/src/config/api.ts` - API 配置
- `k8s/deploy.sh` - 部署脚本
