# 提交前检查清单

> 每次提交代码前必须执行以下检查，确保代码质量。

## 1. TypeScript 编译检查

```bash
cd frontend && npx tsc --noEmit
```

零错误才能提交。

## 2. Python 语法检查

```bash
cd backend && python3 -c "import py_compile; py_compile.compile('main.py', doraise=True)"
```

## 3. i18n 翻译 key 完整性检查

```bash
node frontend/src/scripts/check-i18n.cjs
```

输出 `✅ 翻译 key 检查通过` 才能提交。如果有缺失 key：
- 在 `frontend/src/locales/zh/translation.json` 和 `frontend/src/locales/en/translation.json` 中补齐
- 如果是中英文站各自独有的 key（如 `input.*` vs `home.input.*`），在脚本的 `KNOWN_ZH_ONLY` / `KNOWN_EN_ONLY` 中添加排除规则

## 4. 提交范围确认

```bash
git status && git diff --stat
```

确认只包含预期改动的文件，排除：
- `.env` / `.env.auth` 等含密钥的文件
- 未完成的功能代码
- 调试用的临时文件
