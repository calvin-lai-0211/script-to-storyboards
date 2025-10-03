# 快速开始

本文档将帮助你快速搭建开发环境并启动 Script-to-Storyboards 前端项目。

## 环境要求

### 必需软件

- **Node.js**: >= 18.0.0（推荐使用 LTS 版本）
- **npm**: >= 9.0.0（随 Node.js 安装）
- **Git**: 用于版本控制

### 推荐工具

- **VS Code**: 推荐的代码编辑器
  - 推荐插件：
    - ESLint
    - Prettier - Code formatter
    - Tailwind CSS IntelliSense
    - TypeScript Vue Plugin (Volar)
- **Chrome/Firefox**: 用于调试和开发

### 系统要求

- **操作系统**: macOS, Linux, Windows (WSL2)
- **内存**: >= 4GB RAM
- **磁盘空间**: >= 500MB（包含 node_modules）

## 安装步骤

### 1. 克隆仓库

```bash
# 克隆项目
git clone https://github.com/your-org/script-to-storyboards.git

# 进入前端目录
cd script-to-storyboards/frontend
```

### 2. 安装依赖

```bash
npm install
```

这将安装所有必需的依赖包，包括：

- React, React Router, Zustand（运行时依赖）
- Vite, TypeScript, Vitest（开发依赖）
- Tailwind CSS, ESLint（工具链）

### 3. 配置环境变量

创建环境变量文件（可选，但推荐）：

```bash
# 复制示例文件
cp .env.example .env

# 编辑环境变量
vim .env
```

**环境变量说明**:

```bash
# .env 文件内容
VITE_API_BASE_URL=http://localhost:8001  # API 服务器地址
```

**注意**:

- 环境变量必须以 `VITE_` 开头才能在客户端代码中访问
- 如果不设置，默认使用 `http://localhost:8000`

### 4. 启动开发服务器

```bash
npm run dev
```

**预期输出**:

```
VITE v7.1.5  ready in 1234 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
➜  press h to show help
```

打开浏览器访问 `http://localhost:5173/`，你应该能看到应用首页。

## 常用命令

### 开发相关

| 命令              | 说明                            |
| ----------------- | ------------------------------- |
| `npm run dev`     | 启动开发服务器（默认端口 5173） |
| `npm run build`   | 构建生产版本                    |
| `npm run preview` | 预览生产构建                    |

**开发服务器特性**:

- 热模块替换（HMR）- 代码修改后自动刷新
- 快速冷启动（~1-2 秒）
- TypeScript 类型检查

### 测试相关

| 命令               | 说明                 |
| ------------------ | -------------------- |
| `npm run test`     | 运行测试（监听模式） |
| `npm run test:run` | 运行所有测试（单次） |
| `npm run test:ui`  | 启动测试 UI 界面     |
| `npm run test:cov` | 生成测试覆盖率报告   |

**测试覆盖率报告**:
运行 `npm run test:cov` 后，打开 `coverage/index.html` 查看详细覆盖率。

### 代码质量

| 命令                   | 说明                   |
| ---------------------- | ---------------------- |
| `npm run lint`         | 运行 ESLint 检查       |
| `npm run lint:fix`     | 自动修复 ESLint 错误   |
| `npm run type-check`   | TypeScript 类型检查    |
| `npm run pretty`       | 格式化代码（待配置）   |
| `npm run pretty:check` | 检查代码格式（待配置） |

## 开发工作流

### 典型的开发流程

1. **启动开发服务器**

   ```bash
   npm run dev
   ```

2. **编辑代码**

   - 在 VS Code 中修改代码
   - 浏览器自动刷新（HMR）

3. **运行测试**（推荐在另一个终端）

   ```bash
   npm run test
   ```

4. **提交前检查**

   ```bash
   # 运行所有检查
   npm run test:run && npm run type-check && npm run lint
   ```

5. **提交代码**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push
   ```

## 项目结构速览

启动项目后，你会看到以下关键目录：

```
frontend/
├── src/
│   ├── api/              # API 层（重要：请求逻辑）
│   ├── store/            # 状态管理（Zustand stores）
│   ├── pages/            # 页面组件
│   ├── components/       # 可复用组件
│   ├── layouts/          # 布局组件
│   ├── App.tsx           # 应用根组件
│   └── main.tsx          # 应用入口
├── public/               # 静态资源（直接复制）
├── dist/                 # 构建输出（生成）
├── node_modules/         # 依赖包
├── package.json          # 项目配置
├── vite.config.ts        # Vite 配置
└── tsconfig.json         # TypeScript 配置
```

详细说明请参考 [项目结构文档](./project-structure.md)。

## 首次运行检查

### 1. 检查 API 服务器

前端需要连接到后端 API 服务器。确保后端已启动：

```bash
# 在项目根目录启动后端（假设使用 uvicorn）
cd ../api
python -m api.main
```

如果后端未启动，前端会显示网络错误。

### 2. 检查浏览器控制台

打开浏览器开发者工具（F12），查看：

- **Console**: 应该看到 `API call:` 的调试日志
- **Network**: 查看 API 请求是否成功
- **React DevTools**: 查看组件树和 props

### 3. 测试基本功能

- 访问首页：`http://localhost:5173/`
- 点击剧集卡片进入工作台
- 切换不同 Tab（原文、分镜、Memory）
- 检查网络请求是否去重

## 常见问题

### 1. 端口冲突

**问题**: `Error: Port 5173 is already in use`

**解决方法**:

```bash
# 杀死占用端口的进程
lsof -ti:5173 | xargs kill -9

# 或者使用其他端口
npm run dev -- --port 3000
```

### 2. 依赖安装失败

**问题**: `npm install` 失败或超时

**解决方法**:

```bash
# 清理缓存
npm cache clean --force

# 删除 node_modules 和 lock 文件
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

### 3. TypeScript 错误

**问题**: VS Code 显示大量 TypeScript 错误

**解决方法**:

1. 重启 TypeScript 服务器（VS Code 命令面板：`TypeScript: Restart TS Server`）
2. 检查 `tsconfig.json` 配置
3. 运行 `npm run type-check` 查看详细错误

### 4. API 请求失败

**问题**: 网络请求失败，控制台显示 CORS 错误

**解决方法**:

1. 确保后端服务器已启动
2. 检查 `.env` 中的 `VITE_API_BASE_URL`
3. 检查后端 CORS 配置是否允许前端域名

### 5. HMR 不工作

**问题**: 修改代码后浏览器不自动刷新

**解决方法**:

```bash
# 重启 Vite 开发服务器
# Ctrl+C 停止服务器
npm run dev
```

## 下一步

现在你已经成功启动了开发环境，接下来可以：

1. **了解项目结构**: 阅读 [项目结构文档](./project-structure.md)
2. **学习架构设计**: 阅读 [架构文档](./architecture.md)
3. **开始开发组件**: 阅读 [组件开发指南](./components.md)
4. **编写测试**: 阅读 [测试指南](./testing.md)
5. **配置代码质量工具**: 阅读 [代码质量文档](./code-quality.md)

## 快速参考

### 开发服务器快捷键

在开发服务器运行时，按下以下快捷键：

| 快捷键 | 功能           |
| ------ | -------------- |
| `r`    | 重启服务器     |
| `u`    | 显示服务器 URL |
| `o`    | 在浏览器中打开 |
| `c`    | 清空控制台     |
| `q`    | 退出服务器     |
| `h`    | 显示帮助       |

### 调试技巧

1. **使用 React DevTools**

   - 安装 Chrome 扩展：[React Developer Tools](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi)
   - 查看组件树、props、state

2. **使用 Zustand DevTools**

   ```typescript
   // 在 store 中添加 devtools 中间件
   import { devtools } from "zustand/middleware";

   export const useEpisodeStore = create(
     devtools(
       (set, get) => ({
         /* ... */
       }),
       { name: "EpisodeStore" }
     )
   );
   ```

3. **调试 API 请求**
   - 查看 Network 面板
   - 检查 `console.debug` 日志
   - 使用 `debugger` 断点

### 性能优化技巧

1. **减少不必要的重新渲染**

   ```typescript
   // 使用 React.memo
   export default React.memo(MyComponent);

   // 使用 useMemo 缓存计算结果
   const expensiveValue = useMemo(() => computeExpensiveValue(a, b), [a, b]);
   ```

2. **代码分割**

   ```typescript
   // 使用 React.lazy 懒加载组件
   const LazyComponent = React.lazy(() => import("./LazyComponent"));
   ```

3. **监控 bundle 大小**
   ```bash
   # 构建并分析 bundle
   npm run build
   # 查看 dist/ 目录中的文件大小
   ```

## 总结

你现在应该能够：

- 启动开发服务器
- 运行测试和代码检查
- 理解基本的开发工作流
- 解决常见的开发问题

如有更多问题，请参考其他文档或提交 Issue。

---

**相关文档**:

- [项目结构](./project-structure.md)
- [架构设计](./architecture.md)
- [测试指南](./testing.md)
- [代码质量](./code-quality.md)
