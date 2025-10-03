# 代码质量

本文档详细说明项目的代码质量工具、配置和最佳实践。

## 工具链

- **ESLint**: 代码质量和风格检查
- **Prettier**: 代码格式化（待配置）
- **TypeScript**: 严格类型检查

---

## ESLint 配置

### eslint.config.js（Flat Config）

项目使用 ESLint 9+ 的 Flat Config 格式：

```javascript
import globals from "globals";
import pluginJs from "@eslint/js";
import tseslint from "typescript-eslint";
import pluginReact from "eslint-plugin-react";
import reactRefresh from "eslint-plugin-react-refresh";

export default tseslint.config(
  {
    ignores: [
      "dist",
      "node_modules",
      "server/",
      "**/*.config.js",
      "**/*.config.ts",
    ],
  },
  {
    files: ["**/*.{js,mjs,cjs,ts,tsx}"],
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
        ecmaVersion: "latest",
        sourceType: "module",
        project: ["./tsconfig.json", "./tsconfig.node.json"],
      },
      globals: globals.browser,
    },
  },
  pluginJs.configs.recommended,
  ...tseslint.configs.recommended,
  {
    settings: {
      react: {
        version: "detect",
      },
    },
    plugins: {
      react: pluginReact,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...pluginReact.configs.recommended.rules,
      ...pluginReact.configs["jsx-runtime"].rules,
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
      "react/jsx-no-target-blank": "off",
      "react/react-in-jsx-scope": "off",
      "react/prop-types": "off",
      "@typescript-eslint/no-explicit-any": "off",
    },
  }
);
```

### 核心规则

| 规则                                   | 配置   | 说明                           |
| -------------------------------------- | ------ | ------------------------------ |
| `@typescript-eslint/no-explicit-any`   | `off`  | 允许使用 `any` 类型            |
| `react/react-in-jsx-scope`             | `off`  | React 17+ 不需要导入 React     |
| `react/prop-types`                     | `off`  | 使用 TypeScript 代替 PropTypes |
| `react-refresh/only-export-components` | `warn` | 检查 Fast Refresh 兼容性       |

### 运行 ESLint

```bash
# 检查代码
npm run lint

# 自动修复
npm run lint:fix
```

---

## Prettier 配置

### .prettierrc

```json
{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

### 运行 Prettier

```bash
# 格式化代码
npm run pretty

# 检查格式
npm run pretty:check
```

### ESLint + Prettier 集成

```bash
npm install --save-dev eslint-config-prettier eslint-plugin-prettier
```

更新 `eslint.config.js`:

```javascript
import prettier from "eslint-plugin-prettier";
import prettierConfig from "eslint-config-prettier";

export default tseslint.config(
  // ...
  prettierConfig,
  {
    plugins: { prettier },
    rules: {
      "prettier/prettier": "error",
    },
  }
);
```

---

## TypeScript 配置

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",

    /* Path Aliases */
    "baseUrl": ".",
    "paths": {
      "@api": ["./src/api"],
      "@api/*": ["./src/api/*"],
      "@store/*": ["./src/store/*"],
      "@hooks/*": ["./src/hooks/*"]
    },

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [
    {
      "path": "./tsconfig.node.json"
    }
  ]
}
```

### 严格模式选项

| 选项                         | 启用 | 说明                         |
| ---------------------------- | ---- | ---------------------------- |
| `strict`                     | ✅   | 启用所有严格类型检查         |
| `noUnusedLocals`             | ✅   | 检查未使用的局部变量         |
| `noUnusedParameters`         | ✅   | 检查未使用的参数             |
| `noFallthroughCasesInSwitch` | ✅   | 检查 switch 语句 fallthrough |

### 类型检查

```bash
# 运行类型检查
npm run type-check
```

---

## 代码规范

### 1. 命名规范

**文件命名**:

```
✅ PascalCase:     ScriptsList.tsx, MainLayout.tsx
✅ camelCase:      client.ts, useEpisodeStore.ts
✅ kebab-case:     api-integration.md (仅文档)
```

**变量命名**:

```typescript
// ✅ 推荐
const userName = "Alice";
const API_BASE_URL = "http://localhost:8000";
const MAX_RETRIES = 3;

// ❌ 不推荐
const user_name = "Alice"; // 不使用 snake_case
const apibaseurl = "..."; // 常量应大写
```

**函数命名**:

```typescript
// ✅ 推荐：动词开头
function fetchData() {}
function handleClick() {}
function isValid() {}
function hasPermission() {}

// ❌ 不推荐
function data() {}
function click() {}
```

**组件命名**:

```typescript
// ✅ 推荐：PascalCase
const UserCard = () => {};
const ScriptsList = () => {};

// ❌ 不推荐
const userCard = () => {};
const scripts_list = () => {};
```

### 2. 导入顺序

```typescript
// 1. React 相关
import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

// 2. 第三方库
import { create } from "zustand";
import { Loader2, AlertCircle } from "lucide-react";

// 3. 内部模块（使用别名）
import { API_ENDPOINTS, apiCall } from "@api";
import { useEpisodeStore } from "@store/useEpisodeStore";

// 4. 相对导入
import "./index.css";
import MainLayout from "./layouts/MainLayout";
```

### 3. 组件结构

```typescript
import React, { useState, useEffect } from "react";

// 1. 类型定义
interface MyComponentProps {
  title: string;
  onSubmit: (data: string) => void;
}

// 2. 组件定义
const MyComponent: React.FC<MyComponentProps> = ({ title, onSubmit }) => {
  // 3. Hooks（顺序：useState, useEffect, 自定义 hooks）
  const [data, setData] = useState<string>("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  // 4. 事件处理函数
  const handleSubmit = () => {
    onSubmit(data);
  };

  // 5. 渲染辅助函数
  const renderContent = () => {
    if (loading) return <div>Loading...</div>;
    return <div>{data}</div>;
  };

  // 6. 返回 JSX
  return (
    <div>
      <h1>{title}</h1>
      {renderContent()}
      <button onClick={handleSubmit}>Submit</button>
    </div>
  );
};

// 7. 导出
export default MyComponent;
```

### 4. 注释规范

**JSDoc 注释**:

```typescript
/**
 * 获取剧集详情
 * @param key - 剧集唯一标识
 * @param signal - 取消请求信号
 * @returns 剧集详情数据
 * @throws 当 API 返回错误时抛出异常
 */
export const getScript = async (
  key: string,
  signal?: AbortSignal
): Promise<ScriptData> => {
  // ...
};
```

**TODO 注释**:

```typescript
// TODO: 添加缓存机制
// FIXME: 修复请求重复问题
// NOTE: 这里使用 encodeURIComponent 处理特殊字符
```

**调试日志**:

```typescript
// ✅ 使用 console.debug（方便后续删除）
console.debug("API call:", url);
console.debug("Storyboard: Using cached data");

// ❌ 避免使用 console.log（生产环境会保留）
console.log("Debug info");
```

### 5. 错误处理

```typescript
try {
  const data = await apiCall(url);
  setData(data);
  setError(null);
} catch (err) {
  // 区分不同类型的错误
  if ((err as Error).name === "AbortError") {
    console.debug("Request cancelled");
    return;
  }

  // 记录错误
  console.error("Error fetching data:", err);

  // 设置错误状态
  setError((err as Error).message || "数据加载失败");
}
```

---

## Git Hooks（待配置）

### Pre-commit Hook

**位置**: `.githooks/pre-commit`

```bash
#!/bin/sh

echo "Running pre-commit checks..."

# 1. 运行测试
echo "1. Running tests..."
npm run test:run
if [ $? -ne 0 ]; then
  echo "❌ Tests failed. Commit aborted."
  exit 1
fi

# 2. 类型检查
echo "2. Running type-check..."
npm run type-check
if [ $? -ne 0 ]; then
  echo "❌ Type-check failed. Commit aborted."
  exit 1
fi

# 3. ESLint 检查
echo "3. Running ESLint..."
npm run lint
if [ $? -ne 0 ]; then
  echo "❌ ESLint failed. Commit aborted."
  exit 1
fi

echo "✅ All checks passed. Proceeding with commit."
exit 0
```

**启用 Git Hooks**:

```bash
git config core.hooksPath .githooks
```

**跳过 Hook**（不推荐）:

```bash
git commit --no-verify
```

---

## VS Code 配置

### 推荐设置（.vscode/settings.json）

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true,
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### 推荐插件

- **ESLint** (dbaeumer.vscode-eslint)
- **Prettier** (esbenp.prettier-vscode)
- **Tailwind CSS IntelliSense** (bradlc.vscode-tailwindcss)
- **TypeScript Vue Plugin (Volar)** (Vue.vscode-typescript-vue-plugin)

---

## 代码审查清单

### 提交前检查

- [ ] 所有测试通过（`npm run test:run`）
- [ ] 类型检查通过（`npm run type-check`）
- [ ] ESLint 无警告（`npm run lint`）
- [ ] 代码已格式化（`npm run pretty`）
- [ ] 无 `console.log`（仅使用 `console.debug`）
- [ ] 无未使用的变量和导入
- [ ] 添加必要的注释和文档

### Code Review 要点

1. **类型安全**: 是否使用了 `any`？是否有类型断言？
2. **错误处理**: 是否处理了所有可能的错误情况？
3. **性能优化**: 是否有不必要的重新渲染？
4. **可读性**: 代码是否清晰易懂？
5. **测试覆盖**: 是否添加了单元测试？

---

## 总结

代码质量要点：

1. **ESLint**: Flat Config 格式，严格规则
2. **TypeScript**: 严格模式，完整类型定义
3. **Prettier**: 统一代码格式（待配置）
4. **Git Hooks**: 提交前自动检查（待配置）
5. **命名规范**: PascalCase 组件，camelCase 变量
6. **注释规范**: JSDoc 函数，console.debug 调试

---

**相关文档**:

- [测试指南](./testing.md)
- [项目结构](./project-structure.md)
- [API 集成](./api-integration.md)
