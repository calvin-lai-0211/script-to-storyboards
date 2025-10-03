# 前端文档

欢迎来到 Script-to-Storyboards 前端项目文档。本文档旨在帮助开发者快速了解项目架构、技术栈和开发流程。

## 项目简介

Script-to-Storyboards 前端是一个基于 React + TypeScript + Vite 的现代化单页应用，用于管理和展示自动化生成的分镜脚本、角色、场景和道具资产。

### 核心功能

- **剧集管理**: 浏览和管理所有剧集的原文、分镜和 Memory 数据
- **资产管理**: 查看和管理角色、场景、道具的图像和提示词
- **分镜工作台**: 提供多 Tab 切换的工作环境，支持原文、分镜、Memory 和流程控制
- **详情查看**: 支持查看单个角色、场景、道具的详细信息和图像
- **请求优化**: 自动去重并发请求，提供高效的数据加载体验

## 技术栈

### 核心框架
- **React 18** - 现代化 UI 框架
- **TypeScript** - 类型安全的 JavaScript 超集
- **Vite 7** - 快速的构建工具和开发服务器

### 路由和状态
- **React Router v7** - 声明式路由管理
- **Zustand** - 轻量级状态管理库

### UI 和样式
- **Tailwind CSS 4** - 实用优先的 CSS 框架
- **@tailwindcss/typography** - 富文本样式插件
- **Lucide React** - 美观的图标库
- **React Markdown** - Markdown 渲染

### 开发工具
- **Vitest** - 快速的单元测试框架
- **@testing-library/react** - React 组件测试工具
- **ESLint** - 代码质量检查
- **Prettier** - 代码格式化（配置待添加）
- **TypeScript Compiler** - 类型检查

## 文档索引

### 快速开始
- [**开发快速开始**](./getting-started.md) - 环境搭建、安装依赖、启动项目
- [**项目结构说明**](./project-structure.md) - 完整的目录树和模块组织

### 核心概念
- [**架构设计**](./architecture.md) - 整体架构和设计理念
- [**组件开发**](./components.md) - 组件分类、使用和最佳实践
- [**状态管理**](./state-management.md) - Zustand store 设计和使用
- [**API 集成**](./api-integration.md) - API 客户端、Service 层和类型定义

### 样式和测试
- [**样式系统**](./styling.md) - Tailwind CSS 使用和主题配置
- [**测试指南**](./testing.md) - Vitest 测试框架和最佳实践

### 工程化
- [**代码质量**](./code-quality.md) - ESLint、Prettier、TypeScript 配置
- [**构建和部署**](./build-and-deployment.md) - Vite 构建、环境变量、Docker 部署

## 快速链接

### 常用命令
```bash
# 开发
npm run dev              # 启动开发服务器
npm run build            # 构建生产版本
npm run preview          # 预览生产构建

# 测试
npm run test             # 运行测试（监听模式）
npm run test:run         # 运行所有测试
npm run test:ui          # 测试 UI 界面
npm run test:cov         # 生成测试覆盖率报告

# 代码质量
npm run lint             # 运行 ESLint 检查
npm run lint:fix         # 自动修复 ESLint 错误
npm run type-check       # TypeScript 类型检查
npm run pretty           # 格式化代码（待添加）
npm run pretty:check     # 检查代码格式（待添加）
```

### 关键文件
- `/src/App.tsx` - 应用根组件和路由配置
- `/src/main.tsx` - 应用入口
- `/src/api/client.ts` - API 客户端和请求去重
- `/src/store/useEpisodeStore.ts` - 核心状态管理
- `/vite.config.ts` - Vite 构建配置
- `/tsconfig.json` - TypeScript 配置
- `/eslint.config.js` - ESLint 配置

### 目录结构速览
```
frontend/src/
├── api/                  # API 层（客户端、服务、类型、测试）
├── store/                # 状态管理（Zustand stores 和测试）
├── layouts/              # 布局组件
├── pages/                # 页面组件
├── components/           # 可复用组件
│   └── tabs/            # Tab 组件
├── hooks/                # 自定义 Hooks（预留）
├── config/               # 配置文件
├── test/                 # 测试设置
└── assets/               # 静态资源
```

## 核心特性

### 1. 请求去重机制
自动合并并发的相同请求，避免重复网络调用：
```typescript
// 多个组件同时请求相同数据时，只会发起一次 HTTP 请求
const data1 = await apiCall(API_ENDPOINTS.getScript(key));
const data2 = await apiCall(API_ENDPOINTS.getScript(key)); // 复用上面的请求
```

### 2. 双重缓存策略
- **RequestDeduplicator**: 临时缓存，防止并发重复请求
- **Zustand Store**: 持久缓存，跨组件共享数据

### 3. 认证错误处理
自动检测 4003 认证错误并重定向到登录页面：
```typescript
if (result.code === 4003) {
  const authUrl = result.data?.auth_url;
  if (authUrl) {
    window.location.href = authUrl;
  }
}
```

### 4. 路径别名
简化导入路径：
```typescript
import { API_ENDPOINTS, apiCall } from '@api';
import { useEpisodeStore } from '@store/useEpisodeStore';
```

### 5. URL 状态同步
Workspace Tab 状态通过 URL 参数持久化：
```
/episode/da4ef19d-5965-41c3-a971-f17d0ce06ef7?tab=storyboard
```

## 开发规范

### 类型安全
- 所有 API 响应都有明确的类型定义
- 严格的 TypeScript 配置（`strict: true`）
- 避免使用 `any` 类型

### 代码组织
- 按功能模块划分目录
- API 逻辑与组件逻辑分离
- 类型定义集中管理（`/src/api/types/`）

### 测试覆盖
- 所有核心功能都有单元测试
- 目标：API 层和 Store 层 100% 覆盖
- 使用 Vitest + @testing-library/react

### 性能优化
- 请求去重和缓存
- 支持请求取消（AbortController）
- 组件懒加载（未来优化）

## 贡献指南

### 提交前检查
运行以下命令确保代码质量：
```bash
npm run test:run         # 所有测试通过
npm run type-check       # 无类型错误
npm run lint             # 无 ESLint 警告
```

### Git Hooks（待配置）
项目计划配置 pre-commit hook，自动运行：
1. 单元测试
2. 类型检查
3. ESLint 检查

### 调试日志规范
根据项目规范，调试日志使用 `console.debug`：
```typescript
console.debug('API call:', url); // 方便后续识别并删除
```

## 相关资源

### 官方文档
- [React 官方文档](https://react.dev/)
- [TypeScript 官方文档](https://www.typescriptlang.org/)
- [Vite 官方文档](https://vitejs.dev/)
- [Zustand 文档](https://docs.pmnd.rs/zustand/getting-started/introduction)
- [React Router 文档](https://reactrouter.com/)
- [Tailwind CSS 文档](https://tailwindcss.com/)
- [Vitest 文档](https://vitest.dev/)

### 项目相关
- [后端 API 文档](../../CLAUDE.md) - 后端接口和数据模型
- [部署文档](../deployment/) - Kubernetes 和 Docker 部署

## 待完善功能

- [ ] Prettier 配置文件（`.prettierrc`）
- [ ] Git Hooks 配置（`.githooks/pre-commit`）
- [ ] 更多自定义 Hooks
- [ ] 组件库集成优化
- [ ] 更多资产页面功能
- [ ] 实时数据更新（WebSocket）
- [ ] API 文档集成（Swagger UI）

## 获取帮助

如有问题，请参考：
1. 本文档索引中的相关章节
2. 代码中的注释和类型定义
3. 单元测试中的示例用法
4. 提交 Issue 或联系项目维护者

---

**最后更新**: 2025-10-04
**文档版本**: 1.0.0
