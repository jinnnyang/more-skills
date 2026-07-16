# local-search

Windows 平台下的统一本地搜索工具，同时使用 [Voidtools Everything](https://voidtools.com)（文件名/路径检索）和 [AnyTxt](https://anytxt.net)（全文内容检索，含 PDF/docx/pptx）作为后端。

单一 CLI (`local-search`)，六个语义自解释的子命令。通过 `uv tool` 分发，可被 Hermes Agent 技能调用或直接在终端使用。

**English: see [README.md](./README.md).**

---

## ⚠️ 运行前置条件（必须完成才能使用）

**本技能只在下面两个后端都已安装、正在运行且按下述配置正确开启服务后才能工作**。它不是文件系统遍历器；缺少任一后端，所有子命令都会以 `BackendUnavailable` 错误退出。

### 操作系统支持

- ✅ **Windows 10 / Windows 11** — 已测试并支持
- ❌ **Windows 7 / 8 / 8.1** — Everything 可运行, AnyTxt 官方不支持, 未做兼容测试
- ❌ **macOS / Linux** — Everything 与 AnyTxt 均无官方版本, **不要在这些系统上使用本技能**

Everything 与 AnyTxt 都是原生 Windows 应用，即便在 WSL / Wine 下 IPC 通道（Everything IPC + AnyTxt 本地 HTTP 服务）也无法可靠工作。非 Windows 10+ 用户请改用 `search_files` / `rg` / `find`。

### 1. Voidtools Everything

**安装**: 从 <https://voidtools.com/downloads/> 下载（安装版或便携版均可）。

**配置——必须开启"服务模式"（Service Mode）:**

打开 Everything，进入 **Menu → Tools → Options → General**（**菜单 → 工具 → 选项 → 常规**），勾选:

- **[✓] Everything Service** — 让 Everything 以 Windows 服务方式运行，主实例在注销/登入间保持存活
- **[✓] Start Everything on system startup** — 开机自启（推荐）
- **[✓] Run as administrator** *（勾选 Service 后才会显示）* — 需要管理员权限, 索引 NTFS 卷时才不会遇到权限报错

**还必须启动一个用户会话内的 Everything 实例**。Everything 的 IPC（本技能通过 `everyfile` Python 包使用）只在同一 Windows Session 内工作。如果只开了 Service 但从未启动过前台程序, 服务运行在 Session 0, 而你的终端在 Session 1+, IPC 调用会静默失败。

我们提供了一个幂等修复脚本自动处理这种情况:

```powershell
powershell -ExecutionPolicy Bypass -File "scripts\ensure-everything-user-session.ps1"
```

或者手动从开始菜单启动一次 Everything 即可, 任务栏托盘会出现图标。

### 2. AnyTxt Searcher

**安装**: 从 <https://anytxt.net/download/> 下载（仅支持 Windows）。AnyTxt 免费但不开源。

**配置——必须在设置中打开 "HTTP 搜索 (Beta)":**

打开 AnyTxt, 进入 **菜单 → 选项 → 高级**（英文界面: **Menu → Options → General → Advanced**）, 勾选:

- **[✓] HTTP 搜索 (Beta)** *（英文界面显示为 "HTTP Search (Beta)" 或 "Remote Search Server"）*
- 确认监听端口为 **`9920`** — 这是默认端口, 也是 `local-search` 期望的端口
- 绑定地址保持 **`127.0.0.1`**（本地回环）以保证安全

点击 **应用**, 然后重启 AnyTxt。用下面的命令验证服务已就绪:

```bash
curl -s http://127.0.0.1:9920 -d '{}' | head -c 100
# 只要返回 HTTP 200（即便 body 是 JSON-RPC 错误）就说明服务已经在监听。
```

**还必须至少已经索引了一个目录**。AnyTxt 只搜索被明确加入索引的文件夹。进入 **菜单 → 选项 → 索引**, 把需要搜索的磁盘或目录（Documents / Desktop / 项目目录等）加进去, 等待初始索引完成——底部状态栏会显示索引进度。

### 3. 验证一切就绪

运行 `local-search doctor`:

```
─────────── local-search doctor ───────────
┌────────────────────┬────────┬─────────────────────────────────────┐
│ Check              │ Status │ Detail / Fix                        │
├────────────────────┼────────┼─────────────────────────────────────┤
│ Everything (files) │ ✅ OK  │ 26 ms — IPC OK, 4,102,043 files     │
│ AnyTxt (text)      │ ✅ OK  │ 1753 ms — HTTP OK, 231,824 files    │
└────────────────────┴────────┴─────────────────────────────────────┘
```

两行都必须是绿色的 ✅。红色状态行会附带精确的修复提示（该启动哪个服务、该打开哪个开关）。

---

## 软件要求

- **Windows 10 或 11**
- **Python 3.11+**
- **[uv](https://astral.sh/uv)** — 用于安装与工具管理
- **Voidtools Everything**（配置见上）
- **AnyTxt Searcher**（配置见上）

## 安装

```powershell
# 在本目录的 shell 中:
scripts\install.ps1
# 或 POSIX 等价命令 (git-bash / WSL 中运行 Windows Python):
bash scripts/install.sh
# 或直接:
uv tool install --editable . --force
```

然后:

```
local-search --version    # 0.1.1
local-search doctor       # 两个后端都 OK
```

## 命令速览

| 命令 | 后端 | 用途 |
|---|---|---|
| `files` | Everything | 按文件名 / 路径 / 扩展名搜索 |
| `text` | AnyTxt | 全文内容搜索（含 PDF/docx/pptx） |
| `recent` | Everything | 最近修改的文件，按 mtime 倒序 |
| `extract` | AnyTxt | 输出 AnyTxt 已提取好的纯文本 |
| `sync` | AnyTxt | 强制重建某个目录的索引并验证 |
| `doctor` | 两者 | 健康检查，附可执行修复提示 |

详细选项见 `SKILL.md`（面向 agent 的完整参考）或 `local-search <cmd> --help`。

## 开发

```bash
# 全部测试（离线；纯函数 + mock，不需要后端）
uv run pytest tests/ -v

# 联调 smoke（需要 Everything + AnyTxt 都已按上文配置并运行）
local-search doctor
local-search files "*.py" -n 5
local-search text "hermes" -e md --count-only
```

### 项目结构

```
local-search/
├── SKILL.md                         # agent-facing 技能声明
├── README.md                        # 英文说明
├── README_zh-CN.md                  # 本文件
├── REVIEW.md                        # v1 → v2 专家评审（保留）
├── 2026-07-16_145318-…-skill.md    # v1 计划（保留, 已被替代）
├── 2026-07-16_local-search-skill-v2.md   # v2 计划（source of truth）
├── pyproject.toml
├── src/local_search/
│   ├── __init__.py
│   ├── cli.py                       # Click 子命令树
│   ├── errors.py                    # BackendUnavailable / InvalidQuery
│   ├── filters.py                   # UnifiedFilters + 后端转换器
│   ├── formatters.py                # Row / ResultSet + md/json/csv
│   ├── everything.py                # Everything 后端 (everyfile IPC)
│   ├── anytxt.py                    # AnyTxt 后端 (HTTP JSON-RPC)
│   └── doctor.py                    # 健康检查
├── scripts/
│   ├── ensure-everything-user-session.ps1
│   ├── install.ps1
│   └── install.sh
└── tests/                           # 52 个测试，全部离线可跑
    ├── test_filters.py
    ├── test_formatters.py
    ├── test_anytxt_parsers.py
    └── test_cli.py                  # CLI 安全轨与路径规范化
```

### Wire-check 发现（v0.1.1 已锁定）

- AnyTxt `GetResult` 返回 `list[tuple]` 结构 — 列顺序由响应中的 `output.field` 数组声明
- AnyTxt `GetResult.count` 是**本页行数**, 不是总数; 总数要通过额外的 `Search` 调用获取
- AnyTxt 的路径字段名是 `file`, 不是 `path` 或 `filePath`
- AnyTxt 的数字字段 (`fid`, `lastModify`, `size`) 全都是字符串
- AnyTxt `filterDir=""` 会被服务端改写成 `"C:"`（只搜 C 盘）
- AnyTxt `SyncIndex` 返回 `{}` — 需要额外 `Search` 才能验证文件数
- everyfile `cursor.count` = 本页行数; `cursor.total` = 后端真实的总匹配数
- everyfile 异常类型为 `EverythingError(Exception)`
- everyfile 排序键是 `modified`（不是 `date_modified`）、`ext`（不是 `extension`）

完整 v1 → v2 diff 与专家评审见 `REVIEW.md`。

## 分发与多智能体注册

本技能存放在一个共享源目录（例如 `C:\Users\<你>\Documents\more-skills\skills\local-search\`）。通过目录联接把它注册到任意 Hermes Agent profile:

```powershell
mklink /J "C:\Users\<你>\.hermes\profiles\<profile>\skills\system-administration\local-search" ^
          "C:\Users\<你>\Documents\more-skills\skills\local-search"
```

源目录里的修改会瞬时反映到所有已注册的 profile。`uv tool install --editable` 已经把 `local-search` CLI 装到了全局 PATH——注册仅仅控制**智能体是否能发现**这个技能, 不影响 CLI 本身的可用性。

## 许可证

MIT
