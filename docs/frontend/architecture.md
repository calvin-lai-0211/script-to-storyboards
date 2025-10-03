# 前端架构文档

## 项目概述

基于 React + TypeScript + Vite 的分镜脚本管理系统前端应用。

## 技术栈

- **框架**: React 18
- **构建工具**: Vite 7
- **语言**: TypeScript
- **样式**: Tailwind CSS 4 + @tailwindcss/typography
- **路由**: React Router v7
- **状态管理**: Zustand
- **UI 组件**: Lucide React (图标)
- **Markdown**: React Markdown
- **测试**: Vitest + @testing-library/react
- **代码质量**: ESLint + Prettier + TypeScript

## 目录结构

```
frontend/src/
├── api/                    # API 层
│   ├── client.ts          # API 客户端配置 + 请求去重
│   ├── endpoints.ts       # API 端点定义
│   ├── requestDeduplicator.ts  # 请求去重管理器
│   ├── types/             # API 类型定义
│   │   ├── script.ts      # 剧本类型
│   │   ├── character.ts   # 角色类型
│   │   ├── scene.ts       # 场景类型
│   │   ├── prop.ts        # 道具类型
│   │   ├── storyboard.ts  # 分镜类型
│   │   ├── memory.ts      # Memory 类型
│   │   └── index.ts       # 统一导出
│   ├── services/          # API 服务层
│   │   ├── scriptService.ts
│   │   ├── characterService.ts
│   │   ├── sceneService.ts
│   │   ├── propService.ts
│   │   ├── storyboardService.ts
│   │   ├── memoryService.ts
│   │   └── index.ts
│   ├── __tests__/         # API 测试
│   │   ├── client.test.ts
│   │   ├── endpoints.test.ts
│   │   └── requestDeduplicator.test.ts
│   └── index.ts           # API 统一导出
│
├── store/                 # 状态管理
│   ├── useEpisodeStore.ts      # 剧集状态
│   ├── useCharacterStore.ts    # 角色缓存
│   ├── useSceneStore.ts        # 场景缓存
│   ├── usePropStore.ts         # 道具缓存
│   ├── useStoryboardStore.ts   # 分镜缓存
│   ├── useMemoryStore.ts       # 记忆缓存
│   ├── types.ts                # Store 类型定义
│   └── __tests__/              # Store 测试
│
├── layouts/               # 布局组件
│   └── MainLayout.tsx     # 主布局（侧边栏 + 内容区）
│
├── pages/                 # 页面组件
│   ├── ScriptsList.tsx    # 剧集列表（首页）
│   ├── Workspace.tsx      # 分镜工作台（带 Tab URL 参数）
│   ├── Characters.tsx     # 角色资产页
│   ├── Scenes.tsx         # 场景资产页
│   ├── Props.tsx          # 道具资产页
│   ├── CharacterViewer.tsx # 角色详情页
│   └── SceneViewer.tsx    # 场景详情页
│
├── components/            # 组件
│   └── tabs/              # Tab 组件
│       ├── ScriptTab.tsx      # 原文 Tab（带刷新按钮）
│       ├── StoryboardTab.tsx  # 分镜 Tab（带刷新按钮）
│       ├── MemoryTab.tsx      # Memory Tab（带刷新按钮）
│       └── WorkflowTab.tsx    # 流程控制 Tab
│
├── hooks/                 # 自定义 Hooks（预留）
│
├── assets/                # 静态资源
│
├── App.tsx                # 应用根组件（路由配置）
├── main.tsx               # 应用入口
└── index.css              # 全局样式（包含 prose 样式）
```

## 核心架构

### 1. API 层设计

采用分层架构，将 API 相关逻辑集中管理：

```
组件 → Service → Client → RequestDeduplicator → 后端 API
```

#### 层级说明：

- **RequestDeduplicator 层** (`api/requestDeduplicator.ts`):
  - **自动请求去重**: 防止并发的相同请求
  - **工作原理**:
    - 当一个请求正在进行时，后续相同请求会等待并共享第一个请求的结果
    - 请求完成后立即清理，不缓存响应数据
    - 基于 URL + HTTP方法 + 请求体生成唯一 key
  - **安全机制**: 自动清理超过5分钟的陈旧请求
  - **测试覆盖**: 7个测试用例，覆盖去重、错误处理、并发控制等场景

- **Client 层** (`api/client.ts`):
  - 封装 fetch 请求
  - 集成请求去重器
  - 统一错误处理
  - 响应数据提取

- **Types 层** (`api/types/`):
  - 所有 API 请求/响应类型定义
  - 按业务模块分类（script, character, scene, prop, storyboard, memory）
  - 避免类型重复定义

- **Service 层** (`api/services/`):
  - 封装具体的 API 调用
  - 提供语义化的方法名
  - 支持 AbortSignal 取消请求

- **Endpoints 层** (`api/endpoints.ts`):
  - 集中管理所有 API 端点
  - 支持动态参数
  - 自动 URL 编码

#### 使用示例：

```typescript
import { API_ENDPOINTS, apiCall } from '@api';

// 请求会自动去重
const data1 = apiCall(API_ENDPOINTS.getScript(key)); // 发起请求
const data2 = apiCall(API_ENDPOINTS.getScript(key)); // 复用上面的请求
// 实际只发起一个 HTTP 请求
```

### 2. 状态管理

使用 **Zustand** 进行全局状态管理，按模块分离：

#### Store 列表：

1. **useEpisodeStore**: 剧集上下文和缓存
2. **useCharacterStore**: 角色数据缓存
3. **useSceneStore**: 场景数据缓存
4. **usePropStore**: 道具数据缓存
5. **useStoryboardStore**: 分镜数据缓存
6. **useMemoryStore**: 记忆数据缓存

#### 核心概念：

**双重缓存策略**:
1. **RequestDeduplicator**: 防止并发重复请求（临时，请求完成即清除）
2. **Zustand Store**: 缓存响应数据（持久，直到用户刷新页面）

```typescript
useEffect(() => {
  // 1. 先检查 Store 缓存
  const cached = getStoryboard(scriptKey);
  if (cached) {
    setScenes(cached);
    return;
  }

  // 2. 无缓存时请求（自动去重）
  fetchStoryboards();
}, [scriptKey, getStoryboard]);
```

**优势**:
- 切换 Tab 时不重复请求
- 快速切换时请求自动合并
- 数据在客户端持久化

### 3. 路径别名配置

完成的路径别名配置：

**配置文件**:
- `vite.config.ts`: 使用 `path.resolve` 配置别名
- `tsconfig.json`: 配置 `paths` 映射

```typescript
// 使用别名（推荐）
import { API_ENDPOINTS, apiCall } from '@api';
import { useEpisodeStore } from '@store/useEpisodeStore';
```

### 4. URL 路由增强

#### Workspace Tab 参数

支持通过 URL 参数切换 Tab：

```
/episode/da4ef19d-5965-41c3-a971-f17d0ce06ef7?tab=storyboard
```

**特性**:
- Tab 切换时自动更新 URL
- 支持直接通过 URL 访问特定 Tab
- 刷新页面保持 Tab 状态

### 5. 样式系统

#### Tailwind Typography

在 `index.css` 中自定义了完整的 prose 样式：

```css
.prose p {
  margin-top: 1rem;
  margin-bottom: 1rem;
  line-height: 1.875;
}

.prose hr {
  margin-top: 1.25rem;
  margin-bottom: 1.25rem;
}
```

**原因**: Tailwind v4 不完全支持 `prose-hr:my-8` 这样的修饰符，需要在 CSS 中自定义。

### 6. 请求取消机制

所有 API 请求支持 **AbortController** 取消：

```typescript
useEffect(() => {
  const abortController = new AbortController();
  fetchData(abortController.signal);

  return () => {
    abortController.abort(); // 组件卸载时取消请求
  };
}, []);
```

## 测试覆盖

### 单元测试

使用 Vitest + @testing-library/react：

**API 测试**:
- `client.test.ts`: 6个测试
- `endpoints.test.ts`: 20个测试
- `requestDeduplicator.test.ts`: 7个测试

**Store 测试**:
- `useCharacterStore.test.ts`: 5个测试
- `useSceneStore.test.ts`: 4个测试
- `usePropStore.test.ts`: 4个测试
- `useEpisodeStore.test.ts`: 8个测试

**总计**: 54个测试，全部通过 ✅

### 运行测试

```bash
npm run test:run    # 运行所有测试
npm run test:ui     # 测试UI界面
npm run test:cov    # 测试覆盖率
```

## Git Hooks

### Pre-commit Hook

位于 `.githooks/pre-commit`，在每次提交前自动运行：

1. **Tests** - 运行所有单元测试
2. **Type-check** - TypeScript 类型检查
3. **Lint** - ESLint 代码规范检查

**启用方法**:
```bash
git config core.hooksPath .githooks
```

**跳过Hook** (不推荐):
```bash
git commit --no-verify
```

## 页面结构

### 1. 主布局 (MainLayout)

- **左侧导航**:
  - 深色背景 (slate-900)
  - 支持折叠/展开
  - 菜单项: 剧集、角色、场景、道具
  - 激活状态有渐变高亮

- **右侧内容区**: 渲染子路由

### 2. 路由配置

```typescript
<Routes>
  <Route path="/" element={<ScriptsList />} />
  <Route path="/episode/:key" element={<Workspace />} />
  <Route path="/characters" element={<Characters />} />
  <Route path="/scenes" element={<Scenes />} />
  <Route path="/props" element={<Props />} />
  <Route path="/character/:id" element={<CharacterViewer />} />
  <Route path="/scene/:id" element={<SceneViewer />} />
</Routes>
```

### 3. 页面说明

#### ScriptsList (首页)
- 展示所有剧集卡片
- 点击卡片 → 设置 currentEpisode → 跳转到 Workspace
- 支持复制剧集 key

#### Workspace (分镜工作台)
- 顶部显示剧集标题（从 currentEpisode）
- Tab 切换: 原文、分镜、Memory、流程控制
- **新增**: Tab 参数在 URL 中 (`?tab=xxx`)
- **新增**: 每个 Tab 都有刷新按钮

#### Characters / Scenes / Props (资产页)
- 独立页面，显示所有剧集的资产
- 按 ID 升序排序
- 显示资产所属剧集和集数

## 最佳实践

### 1. 类型安全

- 所有 API 响应都有明确的类型定义
- 使用 TypeScript 的类型推导
- 避免使用 `any`

### 2. 代码组织

- 按功能模块划分目录
- API 逻辑与组件逻辑分离
- 类型定义集中管理

### 3. 性能优化

- **请求去重**: 自动合并并发的相同请求
- **Zustand Store**: 缓存响应数据
- **AbortController**: 支持请求取消
- **URL 参数**: 保持 Tab 状态

### 4. 用户体验

- 缓存优先策略（先读缓存，再请求）
- 加载状态提示
- 错误处理和重试
- 刷新按钮手动更新数据
- Tab 状态持久化（URL 参数）

### 5. 代码质量

- **Pre-commit Hook**: 提交前自动检查
- **单元测试**: 54个测试覆盖核心功能
- **ESLint + Prettier**: 统一代码风格
- **TypeScript**: 严格类型检查

## useEffect 依赖最佳实践

### ❌ 错误示例

```typescript
// 错误：缺少 getStoryboard 依赖
useEffect(() => {
  const cached = getStoryboard(scriptKey);
  if (cached) return;
  fetchData();
}, [scriptKey]); // 缺少 getStoryboard
```

### ✅ 正确示例

```typescript
// 正确：包含所有使用的依赖
useEffect(() => {
  const cached = getStoryboard(scriptKey);
  if (cached) return;
  fetchData();
}, [scriptKey, getStoryboard]); // 完整依赖
```

**原因**: Zustand store 的 getter 函数会在 store 更新时变化，必须放在依赖数组中，否则会使用陈旧闭包导致缓存失效。

## 待开发功能

- [ ] 更多自定义 Hooks (@hooks/)
- [ ] 组件库集成优化
- [ ] 更多资产页面功能
- [ ] 实时数据更新
- [ ] API文档集成 (Swagger)
