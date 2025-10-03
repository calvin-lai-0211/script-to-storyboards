# Git Hooks 和 CI/CD

本文档介绍 Script-to-Storyboards 项目的代码提交规范、Git Hooks 和 CI/CD 自动化流程。

## 目录

- [Git Hooks](#git-hooks)
- [GitHub Actions CI/CD](#github-actions-cicd)
- [代码质量检查](#代码质量检查)
- [提交规范](#提交规范)
- [故障排查](#故障排查)

---

## Git Hooks

Git Hooks 是在特定 Git 事件（如 commit、push）时自动执行的脚本，用于确保代码质量。

### Pre-commit Hook

**位置**: `.git/hooks/pre-commit`

**功能**: 在每次 `git commit` 前自动运行前端代码质量检查。

**检查项**:
1. ✅ **单元测试** (`pnpm test:run`)
2. ✅ **TypeScript 类型检查** (`tsc --noEmit`)
3. ✅ **ESLint 代码规范** (`pnpm lint`)

**工作流程**:
```
git commit
    ↓
进入 frontend/ 目录
    ↓
运行测试 (pnpm test:run)
    ↓ 通过
类型检查 (tsc --noEmit)
    ↓ 通过
代码规范检查 (pnpm lint)
    ↓ 通过
允许提交 ✅
```

如果任何检查失败，提交将被阻止。

### 安装 Pre-commit Hook

项目已自带 pre-commit hook，位于 `.git/hooks/pre-commit`。如果你克隆了新的仓库，hook 应该已经存在。

**手动安装**（如果缺失）:

```bash
# 检查是否存在
ls -la .git/hooks/pre-commit

# 如果不存在，创建它
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
# Pre-commit hook for frontend code quality checks

echo "🔍 Running pre-commit checks..."
cd frontend || exit 1

# Run tests
echo "ℹ️  Running tests..."
if ! npm run test:run; then
    echo "❌ Tests failed!"
    exit 1
fi

# Run type-check
echo "ℹ️  Running type-check..."
if ! npx tsc --noEmit; then
    echo "❌ Type-check failed!"
    exit 1
fi

# Run lint
echo "ℹ️  Running lint..."
if ! npm run lint; then
    echo "❌ Linting failed!"
    exit 1
fi

echo "✅ All pre-commit checks passed!"
exit 0
EOF

# 添加执行权限
chmod +x .git/hooks/pre-commit
```

### 跳过 Pre-commit Hook（不推荐）

在紧急情况下，可以使用 `--no-verify` 跳过 hook：

```bash
git commit --no-verify -m "Emergency fix"
```

**⚠️ 注意**: 跳过 hook 可能导致代码质量问题进入代码库，CI 可能会失败。仅在紧急修复时使用。

### Pre-commit Hook 故障排查

**问题：Hook 无法执行**
```bash
# 检查文件权限
ls -la .git/hooks/pre-commit

# 添加执行权限
chmod +x .git/hooks/pre-commit
```

**问题：找不到 npm 或 pnpm**
```bash
# 确保 Node.js 和 pnpm 已安装
node --version
pnpm --version

# 如果使用 nvm，确保 shell 配置正确
echo $PATH
```

**问题：检查失败**
```bash
# 手动运行检查查看详细错误
cd frontend
pnpm test:run
pnpm exec tsc --noEmit
pnpm lint

# 自动修复 lint 错误
pnpm lint:fix
```

---

## GitHub Actions CI/CD

项目使用 GitHub Actions 自动化 CI/CD 流程。

### CI 工作流

**配置文件**: `.github/workflows/ci.yml`

**触发条件**:
- Push 到 `main` 分支
- 针对 `main` 分支的 Pull Request

**并发控制**:
- 同一 PR 的多次 push 会取消之前未完成的运行
- 节省 CI 资源，加快反馈速度

### CI 流程

```
触发 (Push/PR)
    ↓
[Job: frontend-checks]
    ├─ 📥 Checkout 代码
    ├─ 📦 安装 pnpm
    ├─ 🟢 配置 Node.js 20
    ├─ 📚 安装依赖 (--frozen-lockfile)
    ├─ 🧪 运行测试
    ├─ 🔍 TypeScript 类型检查
    ├─ ✨ ESLint 代码规范
    ├─ 🏗️ 构建检查
    └─ 📊 上传测试覆盖率
    ↓
[Job: status-check]
    └─ ✅ 检查所有任务是否通过
```

### 详细步骤

#### 1. Frontend 检查

```yaml
name: Frontend Tests & Checks
runs-on: ubuntu-latest
working-directory: ./frontend

steps:
  - Checkout 代码
  - 安装 pnpm 10
  - 安装 Node.js 20（使用 pnpm 缓存）
  - 安装依赖（pnpm install --frozen-lockfile）
  - 运行单元测试
  - TypeScript 类型检查
  - ESLint 代码规范检查
  - 构建前端项目
  - 上传测试覆盖率（可选，保留 7 天）
```

#### 2. 状态检查

```yaml
name: All Checks Passed
needs: [frontend-checks]
if: always()

steps:
  - 检查所有依赖任务是否成功
  - 失败则退出并标记 CI 失败
```

### 查看 CI 状态

**在 GitHub 上查看**:
1. 进入仓库页面
2. 点击 "Actions" 标签
3. 选择相应的 workflow run
4. 查看详细日志

**通过 PR 查看**:
- PR 页面底部会显示 CI 状态
- ✅ 绿色勾：所有检查通过
- ❌ 红叉：检查失败
- 🟡 黄点：检查进行中

**命令行查看**（需要 GitHub CLI）:
```bash
# 安装 GitHub CLI
brew install gh

# 查看 workflow 运行状态
gh run list

# 查看特定 run 的详细信息
gh run view <run-id>

# 查看 run 的日志
gh run view <run-id> --log
```

### 本地模拟 CI

在提交前，可以本地运行与 CI 相同的检查：

```bash
cd frontend

# 清理缓存（可选）
rm -rf node_modules pnpm-lock.yaml

# 重新安装依赖（与 CI 一致）
pnpm install --frozen-lockfile

# 运行所有 CI 检查
pnpm test:run          # 测试
pnpm exec tsc --noEmit # 类型检查
pnpm lint              # 代码规范
pnpm build             # 构建检查
```

**一键运行所有检查**（创建快捷脚本）:

```bash
# 在 frontend/package.json 中添加
{
  "scripts": {
    "ci": "pnpm test:run && tsc --noEmit && pnpm lint && pnpm build"
  }
}

# 运行
pnpm ci
```

---

## 代码质量检查

### 前端检查项

| 检查项 | 命令 | 说明 |
|--------|------|------|
| **单元测试** | `pnpm test:run` | Vitest 单元测试，覆盖率要求 80%+ |
| **类型检查** | `pnpm exec tsc --noEmit` | TypeScript 严格模式类型检查 |
| **代码规范** | `pnpm lint` | ESLint + Prettier 规范检查 |
| **自动修复** | `pnpm lint:fix` | 自动修复可修复的规范问题 |
| **构建检查** | `pnpm build` | 确保生产构建成功 |

### 测试覆盖率

项目要求核心模块测试覆盖率达到 **80%+**。

**查看覆盖率报告**:
```bash
cd frontend
pnpm test:run

# 在浏览器中打开覆盖率报告
open coverage/index.html
```

**覆盖率不足时**:
1. 识别未覆盖的代码
2. 添加测试用例
3. 重新运行测试确认覆盖率提升

### 代码规范

项目使用 ESLint + Prettier 统一代码风格。

**常见规范**:
- 使用 2 空格缩进
- 使用单引号 (JavaScript/TypeScript)
- 末尾不加分号
- 每行最大长度 100 字符
- 使用 `const` 优于 `let`，避免 `var`
- 禁止 `console.log`（开发时使用 `console.debug`）

**自动修复规范问题**:
```bash
cd frontend
pnpm lint:fix
```

**手动检查**:
```bash
pnpm lint
```

---

## 提交规范

### Commit Message 格式

推荐使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型 (type)**:
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构（既非新功能也非修复）
- `test`: 添加或修改测试
- `chore`: 构建或辅助工具变动
- `perf`: 性能优化

**示例**:
```bash
# 添加新功能
git commit -m "feat(api): add Google OAuth login"

# 修复 bug
git commit -m "fix(frontend): resolve API request timeout issue"

# 更新文档
git commit -m "docs(k8s): add deployment guide"

# 重构代码
git commit -m "refactor(storyboard): extract scene generation logic"

# 添加测试
git commit -m "test(character): add unit tests for portrait generation"
```

**完整示例**:
```
feat(api): add Google OAuth login

- Implement Google OAuth 2.0 authentication flow
- Add session management with Redis
- Create authentication middleware for protected routes

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 提交最佳实践

1. **原子性提交**: 每个 commit 只做一件事
2. **有意义的信息**: 清晰描述"做了什么"和"为什么"
3. **保持简洁**: Subject 不超过 50 字符
4. **测试后提交**: 确保代码通过所有检查
5. **避免大 commit**: 将大改动拆分为多个小 commit

**推荐工作流**:
```bash
# 1. 开发新功能
# ... 编写代码 ...

# 2. 运行检查
cd frontend
pnpm test:run
pnpm lint:fix
pnpm exec tsc --noEmit

# 3. 暂存更改
git add src/components/NewFeature.tsx
git add src/api/newFeatureService.ts

# 4. 提交（会触发 pre-commit hook）
git commit -m "feat(frontend): add new feature component"

# 5. 推送
git push origin your-branch
```

---

## Pull Request 流程

### 创建 PR

```bash
# 1. 创建功能分支
git checkout -b feat/your-feature

# 2. 开发并提交
git add .
git commit -m "feat: your feature"

# 3. 推送到远程
git push origin feat/your-feature

# 4. 在 GitHub 创建 PR
# - 填写 PR 标题和描述
# - 关联相关 Issue
# - 等待 CI 检查通过
```

### PR 检查清单

创建 PR 前确保：

- [ ] 所有本地测试通过
- [ ] 代码已格式化（`pnpm lint:fix`）
- [ ] 类型检查通过（`tsc --noEmit`）
- [ ] 添加了相关测试
- [ ] 更新了文档（如果需要）
- [ ] Pre-commit hook 检查通过
- [ ] GitHub Actions CI 通过
- [ ] PR 描述清晰，说明了改动内容

### PR Review

**等待 Review**:
- CI 必须通过才能合并
- 至少需要 1 名 reviewer 批准（可选，根据团队规则）
- 解决所有 review comments

**合并 PR**:
```bash
# 方式1: GitHub UI 合并（推荐）
# 选择 "Squash and merge" 或 "Rebase and merge"

# 方式2: 本地合并
git checkout main
git pull origin main
git merge feat/your-feature
git push origin main
```

---

## 故障排查

### CI 失败常见原因

#### 1. 测试失败

**错误信息**:
```
❌ Tests failed! Please fix the failing tests before committing.
```

**解决方法**:
```bash
cd frontend
pnpm test:run

# 查看失败的测试
# 修复代码或更新测试
# 重新运行确认
```

#### 2. 类型检查失败

**错误信息**:
```
❌ Type-check failed! Please fix type errors before committing.
```

**解决方法**:
```bash
cd frontend
pnpm exec tsc --noEmit

# 查看具体的类型错误
# 修复类型定义
# 重新检查
```

#### 3. Lint 失败

**错误信息**:
```
❌ Linting failed! Please fix lint errors before committing.
```

**解决方法**:
```bash
cd frontend
pnpm lint:fix   # 自动修复大部分问题
pnpm lint       # 检查剩余问题

# 手动修复无法自动修复的问题
```

#### 4. 构建失败

**错误信息**:
```
❌ Build failed!
```

**解决方法**:
```bash
cd frontend
pnpm build

# 查看构建错误
# 通常是类型错误或未处理的 import
# 修复后重新构建
```

#### 5. 依赖安装失败

**错误信息**:
```
❌ pnpm install failed
```

**解决方法**:
```bash
# 删除缓存重试
rm -rf node_modules pnpm-lock.yaml
pnpm install

# 更新 pnpm
npm install -g pnpm@latest

# 检查 Node.js 版本
node --version  # 应为 20.x
```

### Pre-commit Hook 故障排查

**Hook 不执行**:
```bash
# 检查 hook 是否存在且可执行
ls -la .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**Hook 卡住不动**:
```bash
# 可能是测试运行时间过长
# 按 Ctrl+C 中断
# 检查是否有死循环或无限等待的测试
```

**想临时禁用 Hook**:
```bash
# 使用 --no-verify（不推荐）
git commit --no-verify -m "message"

# 或重命名 hook（临时禁用）
mv .git/hooks/pre-commit .git/hooks/pre-commit.bak
# ... 进行操作 ...
mv .git/hooks/pre-commit.bak .git/hooks/pre-commit
```

---

## 相关文档

- [开发入门指南](getting-started.md) - 本地开发环境搭建
- [Kubernetes 部署](../k8s/deployment.md) - K8s 部署流程
- [Google OAuth 配置](google-oauth-authentication.md) - 认证集成

---

## 最佳实践总结

1. **提交前运行检查**: 确保本地检查通过后再提交
2. **小步快跑**: 频繁提交小改动，而非一次大改动
3. **描述清晰**: Commit message 清晰描述改动
4. **测试覆盖**: 新功能必须有对应测试
5. **代码审查**: 认真对待 PR review 的建议
6. **持续集成**: 依赖 CI 作为质量保障的最后一道防线
7. **文档同步**: 代码改动后及时更新文档

遵循这些规范，可以确保代码库的质量和一致性。
