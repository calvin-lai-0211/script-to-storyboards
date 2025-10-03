# 项目结构

本文档详细说明 Script-to-Storyboards 前端项目的目录结构、文件组织和模块职责。

## 完整目录树

```
frontend/
├── src/                          # 源代码目录
│   ├── api/                      # API 层（网络请求和类型）
│   │   ├── __tests__/            # API 单元测试
│   │   │   ├── client.test.ts    # 客户端测试（6 个测试）
│   │   │   ├── endpoints.test.ts # 端点测试（20 个测试）
│   │   │   └── requestDeduplicator.test.ts  # 去重器测试（7 个测试）
│   │   ├── services/             # API 服务层
│   │   │   ├── characterService.ts   # 角色服务
│   │   │   ├── sceneService.ts       # 场景服务
│   │   │   ├── propService.ts        # 道具服务
│   │   │   ├── scriptService.ts      # 剧本服务
│   │   │   ├── storyboardService.ts  # 分镜服务
│   │   │   ├── memoryService.ts      # Memory 服务
│   │   │   └── index.ts              # 服务统一导出
│   │   ├── types/                # API 类型定义
│   │   │   ├── character.ts      # 角色相关类型
│   │   │   ├── scene.ts          # 场景相关类型
│   │   │   ├── prop.ts           # 道具相关类型
│   │   │   ├── script.ts         # 剧本相关类型
│   │   │   ├── storyboard.ts     # 分镜相关类型
│   │   │   ├── memory.ts         # Memory 相关类型
│   │   │   └── index.ts          # 类型统一导出
│   │   ├── client.ts             # API 客户端（请求封装）
│   │   ├── endpoints.ts          # API 端点定义
│   │   ├── requestDeduplicator.ts  # 请求去重管理器
│   │   └── index.ts              # API 统一导出
│   │
│   ├── store/                    # 状态管理（Zustand）
│   │   ├── __tests__/            # Store 单元测试
│   │   │   ├── useCharacterStore.test.ts  # 角色 Store 测试（5 个）
│   │   │   ├── useSceneStore.test.ts      # 场景 Store 测试（4 个）
│   │   │   ├── usePropStore.test.ts       # 道具 Store 测试（4 个）
│   │   │   └── useEpisodeStore.test.ts    # 剧集 Store 测试（8 个）
│   │   ├── useEpisodeStore.ts    # 剧集上下文和缓存
│   │   ├── useCharacterStore.ts  # 角色数据缓存
│   │   ├── useSceneStore.ts      # 场景数据缓存
│   │   ├── usePropStore.ts       # 道具数据缓存
│   │   ├── useStoryboardStore.ts # 分镜数据缓存
│   │   ├── useMemoryStore.ts     # Memory 数据缓存
│   │   └── types.ts              # Store 通用类型
│   │
│   ├── pages/                    # 页面组件
│   │   ├── ScriptsList.tsx       # 剧集列表（首页）
│   │   ├── Workspace.tsx         # 分镜工作台（带 Tab）
│   │   ├── Characters.tsx        # 角色资产列表页
│   │   ├── Scenes.tsx            # 场景资产列表页
│   │   ├── Props.tsx             # 道具资产列表页
│   │   ├── CharacterViewer.tsx   # 角色详情页
│   │   ├── SceneViewer.tsx       # 场景详情页
│   │   └── PropViewer.tsx        # 道具详情页
│   │
│   ├── components/               # 可复用组件
│   │   ├── tabs/                 # Tab 组件（Workspace 使用）
│   │   │   ├── ScriptTab.tsx     # 原文 Tab
│   │   │   ├── StoryboardTab.tsx # 分镜 Tab
│   │   │   ├── MemoryTab.tsx     # Memory Tab
│   │   │   └── WorkflowTab.tsx   # 流程控制 Tab
│   │   ├── Header.tsx            # 顶部标题组件
│   │   ├── Sidebar.tsx           # 侧边栏导航组件
│   │   ├── BackButton.tsx        # 返回按钮组件
│   │   ├── ImageDisplay.tsx      # 图像显示组件
│   │   ├── ImagePreviewModal.tsx # 图像预览弹窗
│   │   └── PromptInput.tsx       # 提示词输入组件
│   │
│   ├── layouts/                  # 布局组件
│   │   └── MainLayout.tsx        # 主布局（侧边栏 + 内容区）
│   │
│   ├── hooks/                    # 自定义 Hooks（预留目录）
│   │
│   ├── config/                   # 配置文件
│   │   └── api.ts                # API 配置（Base URL 等）
│   │
│   ├── test/                     # 测试配置
│   │   └── setup.ts              # Vitest 测试环境设置
│   │
│   ├── assets/                   # 静态资源（图片、字体等）
│   │
│   ├── App.tsx                   # 应用根组件（路由配置）
│   ├── main.tsx                  # 应用入口（ReactDOM.render）
│   ├── index.css                 # 全局样式（Tailwind + prose）
│   ├── vite-env.d.ts             # Vite 环境类型声明
│   ├── tsconfig.app.json         # 应用 TypeScript 配置
│   ├── tsconfig.json             # 根 TypeScript 配置
│   ├── tsconfig.node.json        # Node 环境 TypeScript 配置
│   └── vite.config.ts            # Vite 构建配置（src/ 内）
│
├── public/                       # 公共静态资源（直接复制到 dist/）
│
├── dist/                         # 构建输出目录（生成）
│
├── node_modules/                 # NPM 依赖包（自动生成）
│
├── coverage/                     # 测试覆盖率报告（生成）
│
├── .env                          # 环境变量（不提交到 Git）
├── .env.example                  # 环境变量示例
├── .env.docker                   # Docker 环境变量
├── .env.k8s.local                # K8s 本地环境变量
├── .env.k8s.remote               # K8s 远程环境变量
├── .dockerignore                 # Docker 忽略文件
├── .gitignore                    # Git 忽略文件
│
├── package.json                  # NPM 项目配置
├── package-lock.json             # NPM 依赖锁定文件
│
├── vite.config.ts                # Vite 配置（根目录）
├── vitest.config.ts              # Vitest 测试配置
├── tsconfig.json                 # TypeScript 配置（根目录）
├── tsconfig.node.json            # Node 环境 TypeScript 配置
├── tailwind.config.ts            # Tailwind CSS 配置
│
├── eslint.config.js              # ESLint 配置（Flat Config）
│
└── README.md                     # 项目说明（待创建）
```

## 目录职责说明

### `/src/api/` - API 层

**职责**: 封装所有与后端 API 交互的逻辑。

**核心文件**:
- **`client.ts`**: 封装 `fetch` 请求，集成请求去重、错误处理、认证跳转
- **`endpoints.ts`**: 定义所有 API 端点，支持动态参数
- **`requestDeduplicator.ts`**: 请求去重管理器，防止并发重复请求

**子目录**:
- **`services/`**: 按业务模块封装 API 调用，提供语义化方法
  - 每个 Service 对应一个业务模块（角色、场景、道具等）
  - 提供高级封装，隐藏底层 HTTP 细节
- **`types/`**: 所有 API 请求和响应的 TypeScript 类型定义
  - 按业务模块分类，避免类型重复
  - 统一从 `index.ts` 导出
- **`__tests__/`**: API 层单元测试
  - 测试覆盖率目标：100%
  - 使用 Vitest + MSW（Mock Service Worker）

**设计原则**:
- 分层清晰：Client → Service → Component
- 类型安全：所有请求和响应都有明确类型
- 可测试性：依赖注入，易于 Mock

### `/src/store/` - 状态管理

**职责**: 使用 Zustand 管理全局状态和数据缓存。

**核心 Stores**:
- **`useEpisodeStore`**: 剧集上下文、剧本、分镜、Memory 缓存
- **`useCharacterStore`**: 角色数据缓存
- **`useSceneStore`**: 场景数据缓存
- **`usePropStore`**: 道具数据缓存
- **`useStoryboardStore`**: 分镜数据缓存（独立）
- **`useMemoryStore`**: Memory 数据缓存（独立）

**文件说明**:
- **`types.ts`**: Store 通用类型定义
- **`__tests__/`**: Store 单元测试

**设计原则**:
- 按业务模块分离 Store
- 提供 Getter 和 Setter 方法
- 支持缓存清理和重置

### `/src/pages/` - 页面组件

**职责**: 定义应用的各个页面（对应路由）。

**页面列表**:
- **`ScriptsList.tsx`**: 剧集列表（首页，路径 `/`）
- **`Workspace.tsx`**: 分镜工作台（路径 `/episode/:key`）
- **`Characters.tsx`**: 角色列表页（路径 `/characters`）
- **`Scenes.tsx`**: 场景列表页（路径 `/scenes`）
- **`Props.tsx`**: 道具列表页（路径 `/props`）
- **`CharacterViewer.tsx`**: 角色详情页（路径 `/character/:id`）
- **`SceneViewer.tsx`**: 场景详情页（路径 `/scene/:id`）
- **`PropViewer.tsx`**: 道具详情页（路径 `/prop/:id`）

**设计原则**:
- 页面组件只负责布局和数据流
- 业务逻辑封装在 Service 和 Store
- 使用 `useParams`、`useSearchParams` 等 React Router hooks

### `/src/components/` - 可复用组件

**职责**: 存放可在多个页面中复用的 UI 组件。

**组件分类**:

1. **Tab 组件** (`components/tabs/`)
   - `ScriptTab.tsx`: 显示原文内容
   - `StoryboardTab.tsx`: 显示分镜场景列表
   - `MemoryTab.tsx`: 显示 Memory 数据
   - `WorkflowTab.tsx`: 流程控制面板

2. **UI 组件** (`components/`)
   - `Header.tsx`: 顶部标题栏
   - `Sidebar.tsx`: 侧边栏导航
   - `BackButton.tsx`: 返回按钮
   - `ImageDisplay.tsx`: 图像展示
   - `ImagePreviewModal.tsx`: 图像预览弹窗
   - `PromptInput.tsx`: 提示词输入框

**设计原则**:
- 组件应尽可能通用和可复用
- 使用 Props 传递数据和回调
- 避免在组件内直接调用 API

### `/src/layouts/` - 布局组件

**职责**: 定义页面的整体布局结构。

**布局文件**:
- **`MainLayout.tsx`**: 主布局（包含侧边栏和内容区）
  - 左侧：深色导航栏，支持折叠
  - 右侧：内容区，渲染子路由

**设计原则**:
- Layout 组件包裹所有页面
- 提供一致的导航和布局体验

### `/src/hooks/` - 自定义 Hooks

**职责**: 存放可复用的自定义 React Hooks（目前为预留目录）。

**潜在用途**:
- `useDebounce`: 防抖 Hook
- `useFetch`: 通用数据获取 Hook
- `useLocalStorage`: 本地存储 Hook

### `/src/config/` - 配置文件

**职责**: 存放应用配置常量。

**文件**:
- **`api.ts`**: API 相关配置（Base URL、超时等）

### `/src/test/` - 测试配置

**职责**: 存放测试框架的全局配置。

**文件**:
- **`setup.ts`**: Vitest 测试环境设置（如配置 jsdom、全局 Mock 等）

### `/src/assets/` - 静态资源

**职责**: 存放需要通过 Vite 处理的静态资源（如图片、字体）。

**特点**:
- 支持 URL 引用（如 `import logo from '@assets/logo.png'`）
- Vite 会自动优化和打包

### 根目录配置文件

**Vite 相关**:
- **`vite.config.ts`**: Vite 构建配置（插件、别名、服务器配置）
- **`vitest.config.ts`**: Vitest 测试配置

**TypeScript 相关**:
- **`tsconfig.json`**: 根 TypeScript 配置
- **`tsconfig.node.json`**: Node 环境配置（用于 Vite 配置文件）
- **`tsconfig.app.json`**: 应用代码配置

**样式相关**:
- **`tailwind.config.ts`**: Tailwind CSS 配置

**代码质量**:
- **`eslint.config.js`**: ESLint 配置（Flat Config 格式）

**环境变量**:
- **`.env`**: 本地开发环境变量（不提交）
- **`.env.example`**: 环境变量示例
- **`.env.docker`**: Docker 环境变量
- **`.env.k8s.local`**: Kubernetes 本地环境
- **`.env.k8s.remote`**: Kubernetes 远程环境

## 文件命名规范

### 组件文件
- **React 组件**: 使用 PascalCase，扩展名 `.tsx`
  - 示例：`ScriptsList.tsx`, `MainLayout.tsx`
- **非组件 TypeScript 文件**: 使用 camelCase，扩展名 `.ts`
  - 示例：`client.ts`, `useEpisodeStore.ts`

### 测试文件
- 测试文件命名：`{原文件名}.test.ts` 或 `{原文件名}.test.tsx`
  - 示例：`client.test.ts`, `ScriptsList.test.tsx`

### 类型文件
- 类型定义文件：使用 camelCase，扩展名 `.ts`
  - 示例：`types.ts`, `character.ts`

### 配置文件
- 配置文件：使用原生工具的命名约定
  - 示例：`vite.config.ts`, `tsconfig.json`, `eslint.config.js`

## 模块组织原则

### 1. 按功能分层

```
用户界面（Pages）
     ↓
可复用组件（Components）
     ↓
状态管理（Store）
     ↓
服务层（Services）
     ↓
客户端（Client）
     ↓
后端 API
```

### 2. 关注点分离

- **API 层**: 只负责网络请求和数据获取
- **Store 层**: 只负责状态管理和缓存
- **组件层**: 只负责 UI 渲染和用户交互
- **页面层**: 组合组件和协调数据流

### 3. 单一职责原则

每个模块、文件、函数都应该只做一件事：
- 一个 Service 只负责一个业务模块的 API 调用
- 一个 Store 只管理一类数据
- 一个组件只负责一个 UI 功能

### 4. 依赖倒置

- 上层依赖下层（Pages 依赖 Components，Components 依赖 Hooks）
- 通过接口和类型约束（TypeScript）
- 避免循环依赖

### 5. 可测试性

- 每个模块都应该可以独立测试
- 使用依赖注入和 Mock
- 测试文件与源文件放在同一目录（`__tests__/`）

## 路径别名配置

为了简化导入路径，项目配置了以下别名：

```typescript
// vite.config.ts
{
  resolve: {
    alias: {
      '@api': path.resolve(__dirname, './src/api'),
      '@store': path.resolve(__dirname, './src/store'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
    }
  }
}

// tsconfig.json
{
  "paths": {
    "@api": ["./src/api"],
    "@api/*": ["./src/api/*"],
    "@store/*": ["./src/store/*"],
    "@hooks/*": ["./src/hooks/*"]
  }
}
```

**使用示例**:
```typescript
// 不推荐：相对路径
import { apiCall } from '../../../api/client';

// 推荐：路径别名
import { apiCall } from '@api';
import { useEpisodeStore } from '@store/useEpisodeStore';
```

## 代码组织最佳实践

### 1. 统一导出

每个目录都应该有 `index.ts` 文件统一导出：

```typescript
// src/api/index.ts
export * from './client';
export * from './endpoints';
export * from './types';
export * from './services';
```

### 2. 类型定义优先

在编写代码前先定义类型：

```typescript
// 1. 先定义类型
interface Script {
  id: string;
  title: string;
  content: string;
}

// 2. 再实现功能
const getScript = async (id: string): Promise<Script> => {
  // ...
};
```

### 3. 避免默认导出

优先使用命名导出（Named Export）：

```typescript
// 推荐：命名导出
export const useEpisodeStore = create(...);

// 不推荐：默认导出（除非是 React 组件）
export default useEpisodeStore;
```

### 4. 文件大小控制

单个文件不应超过 300 行代码，超过时应拆分：
- 提取可复用逻辑到 Hooks
- 拆分大组件为小组件
- 分离类型定义到独立文件

### 5. 注释规范

使用 JSDoc 风格注释：

```typescript
/**
 * 获取剧集详情
 * @param key - 剧集唯一标识
 * @param signal - 取消请求信号
 * @returns 剧集详情数据
 */
export const getScript = async (key: string, signal?: AbortSignal): Promise<ScriptData> => {
  // ...
};
```

## 总结

项目结构遵循以下原则：
1. **分层清晰**: API → Store → Components → Pages
2. **模块化**: 按功能划分目录和文件
3. **类型安全**: TypeScript 严格模式
4. **可测试性**: 单元测试覆盖核心功能
5. **可维护性**: 统一的命名和组织规范

---

**相关文档**:
- [快速开始](./getting-started.md)
- [架构设计](./architecture.md)
- [组件开发](./components.md)
- [API 集成](./api-integration.md)
