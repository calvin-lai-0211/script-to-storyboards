# Git Hooks

这个目录包含项目的 Git hooks，用于在提交前自动运行代码质量检查。

## 安装

运行以下命令来启用 Git hooks：

```bash
git config core.hooksPath .githooks
```

## Hooks

### pre-commit

在每次提交前自动运行以下检查：

1. **Tests** - 运行所有单元测试
2. **Type-check** - TypeScript 类型检查
3. **Lint** - ESLint 代码规范检查

如果任何检查失败，提交将被阻止。

## 跳过 Hooks（不推荐）

如果在紧急情况下需要跳过 hooks，可以使用：

```bash
git commit --no-verify
```

**注意：** 只在特殊情况下使用此选项，正常情况下应该修复所有错误后再提交。
