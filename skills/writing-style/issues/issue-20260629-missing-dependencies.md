# Issue: 缺少 md2ast 依赖包，脚本目录未与 pretty-markdown 同步

## 问题描述

在 `writing-style` 技能中，`scripts/` 目录需要依赖 `pretty-markdown` 中已有的 `md2ast` 包和完整的 `llm.ts`/`processor.ts` 实现，但初始状态下：

1. ❌ `llm.ts` 不完整，存在语法错误（apiKey 行不完整）
2. ❌ `processor.ts` 不完整，不是完整版本
3. ❌ `node_modules/md2ast` 缺失（`md2ast` 是 `pretty-markdown` 内部包，不在 npm 公共 registry）
4. ❌ `.env` 位置错误，应该放在技能根目录 `writing-style/.env` 而不是 `scripts/.env`（`llm.ts` 从那里加载）

## 修复步骤已完成

- [x] 从 `pretty-markdown/scripts` 完整复制了 `llm.ts`（字节完全一致）
- [x] 从 `pretty-markdown/scripts` 完整复制了 `processor.ts`（字节完全一致）
- [x] 从 `pretty-markdown/scripts/node_modules/` 复制了 `md2ast` 包
- [x] 移动 `.env` 到技能根目录（符合 llm.ts 加载逻辑）
- [x] 安装了 `tsx` 运行时依赖
- [x] 所有依赖节点模块安装完成

## 当前状态

所有代码已经同步完成，与 `pretty-markdown` 保持一致，等待用户配置 API 密钥后即可运行标准化预处理。

## 备注

`package.json` 和 `tsconfig.json` 存在合理差异（`writing-style` 是独立运行，需要额外依赖），不需要强制对齐。
