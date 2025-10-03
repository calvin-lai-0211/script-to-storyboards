# 构建和部署

本文档详细说明项目的构建配置、环境变量、Docker 部署和生产优化。

## Vite 构建配置

### vite.config.ts

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

export default defineConfig({
  plugins: [
    react({
      jsxRuntime: 'automatic'
    }),
    tailwindcss()
  ],
  resolve: {
    dedupe: ['react', 'react-dom'],
    alias: {
      '@api': path.resolve(__dirname, './src/api'),
      '@store': path.resolve(__dirname, './src/store'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
    }
  }
});
```

### 核心配置

| 配置项 | 说明 |
|--------|------|
| `plugins.react` | React 插件，自动 JSX 转换 |
| `plugins.tailwindcss` | Tailwind CSS 4 插件 |
| `resolve.dedupe` | 去重 React 包，避免多实例 |
| `resolve.alias` | 路径别名，简化导入 |

---

## 环境变量

### 环境变量文件

项目支持多种环境配置：

| 文件 | 用途 |
|------|------|
| `.env` | 本地开发环境（不提交） |
| `.env.example` | 环境变量示例 |
| `.env.docker` | Docker 环境 |
| `.env.k8s.local` | Kubernetes 本地环境 |
| `.env.k8s.remote` | Kubernetes 远程环境 |

### .env.example

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
```

### 环境变量规则

**重要**: Vite 只会暴露以 `VITE_` 开头的环境变量到客户端代码。

```typescript
// ✅ 可以访问
const apiUrl = import.meta.env.VITE_API_BASE_URL;

// ❌ 无法访问（不以 VITE_ 开头）
const secret = import.meta.env.SECRET_KEY; // undefined
```

### 使用环境变量

```typescript
// src/api/client.ts
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
```

**类型定义** (`src/vite-env.d.ts`):
```typescript
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

---

## 构建命令

### 开发模式

```bash
# 启动开发服务器（默认端口 5173）
npm run dev

# 指定 API 地址
VITE_API_BASE_URL=http://localhost:8001 npm run dev

# 使用其他端口
npm run dev -- --port 3000

# 暴露到网络
npm run dev -- --host
```

### 生产构建

```bash
# 构建生产版本
npm run build

# 输出目录: dist/
```

**构建输出**:
```
dist/
├── index.html
├── assets/
│   ├── index-[hash].js      # 主 JS bundle
│   ├── index-[hash].css     # 主 CSS bundle
│   └── vendor-[hash].js     # 第三方库 bundle
└── favicon.ico
```

### 预览构建

```bash
# 预览生产构建
npm run preview

# 访问 http://localhost:4173
```

---

## 构建优化

### 1. Code Splitting

Vite 自动进行代码分割：

```typescript
// 懒加载组件
const LazyComponent = React.lazy(() => import('./LazyComponent'));

<Suspense fallback={<div>Loading...</div>}>
  <LazyComponent />
</Suspense>
```

### 2. Tree Shaking

Vite 自动移除未使用的代码：

```typescript
// ✅ 只导入需要的图标
import { Loader2, AlertCircle } from 'lucide-react';

// ❌ 导入整个库
import * as Icons from 'lucide-react';
```

### 3. Bundle 分析

```bash
# 分析 bundle 大小
npm run build

# 查看 dist/ 目录中的文件大小
ls -lh dist/assets/
```

**推荐插件** (可选):
```bash
npm install --save-dev rollup-plugin-visualizer
```

```typescript
// vite.config.ts
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    // ...
    visualizer({ open: true }),
  ],
});
```

### 4. 压缩优化

Vite 默认使用 esbuild 压缩，速度极快。

**配置**:
```typescript
export default defineConfig({
  build: {
    minify: 'esbuild', // 或 'terser'
    target: 'es2015',
    cssMinify: true,
  },
});
```

---

## Docker 部署

### Dockerfile（待创建）

**推荐配置**:
```dockerfile
# 多阶段构建
FROM node:18-alpine AS builder

WORKDIR /app

# 复制依赖文件
COPY package.json package-lock.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产环境
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### nginx.conf

```nginx
server {
  listen 80;
  server_name localhost;

  root /usr/share/nginx/html;
  index index.html;

  # 支持 SPA 路由
  location / {
    try_files $uri $uri/ /index.html;
  }

  # 静态资源缓存
  location /assets/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
  }

  # Gzip 压缩
  gzip on;
  gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

### 构建 Docker 镜像

```bash
# 构建镜像
docker build -t drama-creator-frontend:latest .

# 运行容器
docker run -p 8080:80 -e VITE_API_BASE_URL=http://api.example.com drama-creator-frontend:latest

# 访问 http://localhost:8080
```

### Docker Compose（待创建）

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:80"
    environment:
      - VITE_API_BASE_URL=http://api:8000
    depends_on:
      - api

  api:
    image: drama-creator-api:latest
    ports:
      - "8000:8000"
```

---

## Kubernetes 部署

### 环境配置

**K8s 本地环境** (`.env.k8s.local`):
```bash
VITE_API_BASE_URL=http://localhost:8001
```

**K8s 远程环境** (`.env.k8s.remote`):
```bash
VITE_API_BASE_URL=https://api.production.com
```

### Deployment YAML（示例）

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: drama-creator-frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: drama-creator-frontend
  template:
    metadata:
      labels:
        app: drama-creator-frontend
    spec:
      containers:
      - name: frontend
        image: drama-creator-frontend:latest
        ports:
        - containerPort: 80
        env:
        - name: VITE_API_BASE_URL
          valueFrom:
            configMapKeyRef:
              name: frontend-config
              key: api-base-url
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: drama-creator-frontend
spec:
  selector:
    app: drama-creator-frontend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: LoadBalancer
```

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: frontend-config
data:
  api-base-url: "https://api.production.com"
```

---

## 生产环境检查清单

### 构建前检查

- [ ] 所有测试通过（`npm run test:run`）
- [ ] 类型检查通过（`npm run type-check`）
- [ ] ESLint 无警告（`npm run lint`）
- [ ] 移除所有 `console.debug` 和 `console.log`
- [ ] 更新版本号（`package.json`）

### 环境变量检查

- [ ] 正确配置 `VITE_API_BASE_URL`
- [ ] 验证 API 地址可访问
- [ ] 检查 CORS 配置

### 性能检查

- [ ] Bundle 大小合理（< 500KB）
- [ ] 首次加载时间 < 3s
- [ ] Lighthouse 评分 > 90

### 安全检查

- [ ] 无敏感信息泄露（API keys、密码等）
- [ ] 启用 HTTPS
- [ ] 配置 CSP（Content Security Policy）
- [ ] 启用 Gzip 压缩

---

## 常见问题

### 1. 构建失败

**问题**: `npm run build` 失败

**解决方法**:
```bash
# 清理缓存
rm -rf node_modules dist
npm cache clean --force

# 重新安装依赖
npm install

# 重新构建
npm run build
```

### 2. 环境变量不生效

**问题**: `import.meta.env.VITE_API_BASE_URL` 返回 `undefined`

**解决方法**:
1. 确保环境变量以 `VITE_` 开头
2. 重启开发服务器
3. 检查 `.env` 文件是否在项目根目录

### 3. 路由 404 错误

**问题**: 刷新页面时出现 404

**解决方法**: 配置 nginx 支持 SPA 路由：
```nginx
location / {
  try_files $uri $uri/ /index.html;
}
```

### 4. Docker 镜像过大

**问题**: Docker 镜像超过 1GB

**解决方法**:
1. 使用多阶段构建
2. 使用 Alpine 基础镜像
3. 清理 npm 缓存：`RUN npm cache clean --force`
4. 使用 `.dockerignore`:
```
node_modules
dist
.git
.env
*.log
```

---

## 性能优化

### 1. 预加载关键资源

```html
<!-- index.html -->
<link rel="preload" href="/assets/index.js" as="script">
<link rel="preconnect" href="https://api.example.com">
```

### 2. 启用 HTTP/2

Nginx 配置：
```nginx
listen 443 ssl http2;
```

### 3. CDN 加速

将静态资源部署到 CDN：
```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui': ['lucide-react'],
        },
      },
    },
  },
});
```

### 4. 懒加载图片

```typescript
<img
  src={imageUrl}
  loading="lazy"
  alt="Description"
/>
```

---

## 监控和日志

### 1. 错误追踪（待集成）

推荐工具：
- **Sentry**: 错误追踪和性能监控
- **LogRocket**: 会话回放

### 2. 性能监控（待集成）

推荐工具：
- **Google Analytics**: 用户行为分析
- **Vercel Analytics**: 性能监控

### 3. 日志管理

```typescript
// 生产环境移除调试日志
if (import.meta.env.PROD) {
  console.debug = () => {};
}
```

---

## 总结

构建和部署要点：
1. **Vite 构建**: 快速、现代、开箱即用
2. **环境变量**: 使用 `VITE_` 前缀
3. **Docker 部署**: 多阶段构建，Alpine 镜像
4. **Nginx 配置**: SPA 路由支持，Gzip 压缩
5. **性能优化**: Code splitting、Tree shaking、CDN
6. **生产检查**: 测试、类型检查、安全审查

---

**相关文档**:
- [快速开始](./getting-started.md)
- [项目结构](./project-structure.md)
- [代码质量](./code-quality.md)
- [测试指南](./testing.md)
