# 前端架构文档

## 项目概述

基于 React + TypeScript + Vite 的分镜脚本管理系统前端应用。

## 技术栈

- **框架**: React 18
- **构建工具**: Vite 7
- **语言**: TypeScript
- **样式**: Tailwind CSS 4
- **路由**: React Router v6
- **状态管理**: Zustand
- **UI 组件**: Lucide React (图标)
- **数据缓存**: LocalForage

## 目录结构

```
frontend/src/
├── api/                    # API 层
│   ├── client.ts          # API 客户端配置
│   ├── endpoints.ts       # API 端点定义
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
│   └── index.ts           # API 统一导出
│
├── store/                 # 状态管理
│   └── useScriptStore.ts  # 全局 store
│
├── layouts/               # 布局组件
│   └── MainLayout.tsx     # 主布局（侧边栏 + 内容区）
│
├── pages/                 # 页面组件
│   ├── ScriptsList.tsx    # 剧集列表（首页）
│   ├── Workspace.tsx      # 分镜工作台
│   ├── Characters.tsx     # 角色资产页
│   ├── Scenes.tsx         # 场景资产页
│   ├── Props.tsx          # 道具资产页
│   └── CharacterViewer.tsx # 角色详情页
│
├── components/            # 组件
│   └── tabs/              # Tab 组件
│       ├── ScriptTab.tsx      # 原文 Tab
│       ├── StoryboardTab.tsx  # 分镜 Tab
│       ├── MemoryTab.tsx      # Memory Tab
│       └── WorkflowTab.tsx    # 流程控制 Tab
│
├── config/                # 配置文件（已废弃，迁移到 api/）
│
├── hooks/                 # 自定义 Hooks（预留）
│
├── assets/                # 静态资源
│
├── App.tsx                # 应用根组件（路由配置）
├── main.tsx               # 应用入口
└── index.css              # 全局样式
```

## 核心架构

### 1. API 层设计

采用分层架构，将 API 相关逻辑集中管理：

```
组件 → Service → Client → 后端 API
```

#### 层级说明：

- **Client 层** (`api/client.ts`):
  - 封装 fetch 请求
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

#### 使用示例：

```typescript
// 旧方式（已废弃）
import { API_ENDPOINTS, apiCall } from '../config/api';
const data = await apiCall<{ props: Prop[] }>(
  API_ENDPOINTS.getAllProps(),
  { signal }
);

// 新方式
import { propService, type Prop } from '@api';
const data = await propService.getAllProps(signal);
```

### 2. 状态管理

使用 **Zustand** 进行全局状态管理：

#### Store 设计：

```typescript
interface ScriptStore {
  // 当前剧集上下文
  currentEpisode: CurrentEpisode | null;
  setCurrentEpisode: (episode: CurrentEpisode) => void;

  // 数据缓存（按 key 索引）
  scripts: Record<string, ScriptData>;
  storyboards: Record<string, StoryboardData>;
  characters: Record<string, CharactersData>;
  scenes: Record<string, ScenesData>;
  memories: Record<string, MemoryData>;

  // Getter/Setter 方法
  getScript: (key: string) => ScriptData | undefined;
  setScript: (key: string, data: ScriptData) => void;
  // ...
}
```

#### 核心概念：

1. **currentEpisode**: 当前选中的剧集信息
   - 点击剧集卡片时设置
   - Workspace 标题显示剧集名
   - 用于跨 Tab 共享上下文

2. **数据缓存**: 按 `key` 索引缓存 API 数据
   - 避免重复请求
   - 跨 Tab 数据共享
   - 提升用户体验

### 3. 路径别名配置

已完成路径别名配置，简化导入语句：

**配置文件**:
- `vite.config.ts`: 使用 `path.resolve` 配置别名（需安装 `@types/node`）
- `tsconfig.json`: 配置 `paths` 映射

```typescript
// vite.config.ts
import path from 'path';

export default defineConfig({
  resolve: {
    alias: {
      '@api': path.resolve(__dirname, './src/api'),
      '@store': path.resolve(__dirname, './src/store'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
    }
  }
});

// tsconfig.json
{
  "baseUrl": ".",
  "paths": {
    "@api": ["./src/api"],      // 直接导入整个模块
    "@api/*": ["./src/api/*"],  // 导入子路径
    "@store/*": ["./src/store/*"],
    "@hooks/*": ["./src/hooks/*"]
  }
}
```

使用示例：
```typescript
// ✅ 使用别名（推荐）
import { API_ENDPOINTS, apiCall } from '@api';
import { useScriptStore } from '@store/useScriptStore';

// ❌ 旧方式（相对路径）
import { API_ENDPOINTS, apiCall } from '../../config/api';
import { useScriptStore } from '../../../store/useScriptStore';
```

**注意**: 项目中所有导入已更新为使用路径别名。

### 4. 数据缓存策略

#### LocalForage 缓存（剧集列表）

采用 **Stale-While-Revalidate** 策略：

```typescript
// 1. 立即从缓存加载
const cachedData = await localforage.getItem('scripts_list_cache');
if (cachedData) {
  setScripts(cachedData);
  setLoading(false);
}

// 2. 后台异步请求最新数据
const freshData = await apiCall(...);

// 3. 更新 UI 和缓存
setScripts(freshData);
await localforage.setItem('scripts_list_cache', freshData);
```

#### Zustand Store 缓存（详情数据）

```typescript
// 检查 store 缓存
const cachedScript = getScript(key);
if (cachedScript) {
  // 直接使用缓存
  return;
}

// 无缓存时请求
const data = await scriptService.getScript(key);
setScript(key, data);
```

### 5. 请求取消机制

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
  <Route path="/workspace" element={<Workspace />} />
  <Route path="/characters" element={<Characters />} />
  <Route path="/scenes" element={<Scenes />} />
  <Route path="/props" element={<Props />} />
  <Route path="/character/:id" element={<CharacterViewer />} />
</Routes>
```

### 3. 页面说明

#### ScriptsList (首页)
- 展示所有剧集卡片
- 点击卡片 → 设置 currentEpisode → 跳转到 Workspace
- 支持复制剧集 key
- LocalForage 缓存 + 后台刷新

#### Workspace (分镜工作台)
- 顶部显示剧集标题（从 currentEpisode）
- Tab 切换: 原文、分镜、Memory、流程控制
- 通过 URL 参数 `?key=xxx` 传递剧集标识

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

- 使用 Zustand store 缓存数据
- 使用 LocalForage 持久化缓存
- 支持请求取消（AbortController）
- 避免重复请求

### 4. 用户体验

- Stale-While-Revalidate 缓存策略
- 加载状态提示
- 错误处理和重试
- 路由参数传递状态

## 待开发功能

- [ ] 更多自定义 Hooks (@hooks/)
- [ ] 组件库集成优化
- [ ] 更多资产页面功能
- [ ] 实时数据更新
