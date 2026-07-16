# local-search 计划评审报告

> 评审对象: `2026-07-16_145318-local-search-skill.md` (v1, 56.8 KB, 1542 行)
> 评审时间: 2026-07-16
> 落地目录: `C:\Users\jinnn\Documents\more-skills\skills\local-search\`
> AnyTxt wire-check: **已完成**, 5 个 method 全部实测

---

## TL;DR

计划总体方向正确、分层合理、文档丰富。但潜伏 **6 个代码级 Bug** + **4 处 AnyTxt API 假设完全错误** + **若干 CLI 语义不一致**。实测 AnyTxt 后, `anytxt.py` 需要重写大约 50%; `filters.py` / `formatters.py` / `cli.py` 需要局部修正。

---

## 🔴 AnyTxt Wire-Check 实测发现 (P0 — 计划完全错的部分)

### Finding 1: `GetResult` 返回的是**列的表格结构**, 不是字段字典

**计划假设:**
```python
files: [{fid, path, lastModify, size}]   # dict list
```

**实测响应:**
```json
{
  "count": 3,
  "field": ["fid", "lastModify", "size", "file"],   ← 列名声明
  "files": [
    ["2879675253150734652", "1761804532", "15674533", "C:\\Users\\jinnn\\Downloads\\..."],
    ...
  ]                                                    ← 每行都是 tuple, 按 field 顺序排列
}
```

关键差异:
1. **`files` 里每一项是 list, 不是 dict**——`_parse_file_entry` 的 dict 分支永远走不到, 只有 list/tuple fallback 生效;
2. **路径字段名是 `file`, 不是 `path` 也不是 `filePath`**——原计划两种 fallback 都没命中;
3. **数字字段用字符串序列化** (fid, lastModify, size 全是 str)——size 计算前得 `int(entry[2])`;
4. **列顺序: `[fid, lastModify, size, file]`**——原计划 `_parse_file_entry` 里 tuple 分支写的是 `[fid, path, mtime, size]`, **顺序完全对不上**, 会把 `path=lastModify的时间戳字符串`。

**修法**: 依赖响应里的 `field` 数组动态映射, 不要硬编码列顺序:
```python
def _parse_file_entry(entry, field_order):
    row = dict(zip(field_order, entry))
    return (
        str(row.get('fid')) if row.get('fid') is not None else None,
        row.get('file') or row.get('path') or '',
        int(row['lastModify']) if row.get('lastModify') else None,
        int(row['size']) if row.get('size') else None,
    )
```
调用侧从 `output['field']` 拿列顺序传进来。

### Finding 2: `GetFragment` 返回字段是 `text`, 不是 `fragment`

**计划假设:**
```python
frag = output.get("fragment") or output.get("text")
```

**实测响应:**
```json
{"text": "... OUT OF *<<*THE*>>* USE OF THIS SOFTWARE ..."}
```

- 字段名就是 `text`;
- 关键词高亮用 `*<<*keyword*>>*` 包裹, 不是 `<em>...</em>`;
- 结果里 `\n` 会被替换为 `... `。

**修法**: SKILL.md / formatters 里说清楚 snippet 的高亮标记, agent 消费时能识别。也可以在 `_fetch_snippet` 里把 `*<<*` / `*>>*` 转换为 markdown 的 `**`。

### Finding 3: `GetRawTextByFID` 字段也是 `text`, 且带页码标记

**实测响应**: `{"text": "📄 P 1 PostgreSQL 18.0 Documentation ..."}` (6.28 MB 纯文本)

- 字段名是 `text`, 不是 `rawText`;
- **PDF 会带页码标记 `📄 P N `**——用户消费前可能想 strip。给 `extract` 加 `--strip-page-marks` 选项。

### Finding 4: `filterDir` 是**前缀匹配, 空串会被服务端改写成 "C:"**

**实测:**
```
filterDir=''                       → server rewrites to 'C:'   count=231813
filterDir='C:\Users\jinnn'         → count=12811
filterDir='C:\Users\jinnn\'        → count=12811    (末尾反斜杠无影响)
filterDir='C:\Users\jinnn\Desktop' → count=1877
filterDir='c:\users\jinnn'         → count=12811    (大小写不敏感)
filterDir='D:\'                    → count=0        (无 D 盘, 干净返回)
```

**含义:**
- `filterDir=""` **不代表"全盘"**, 而是被强制改写成 `C:`, 只搜 C 盘。要搜多盘只能循环发多次请求, 或依赖 AnyTxt 的多盘索引配置;
- 前缀匹配, 大小写不敏感, 末尾反斜杠可有可无——参数标准化很简单。

**修法:**
- `filters.py` 里 `filterDir` 为空时**别传空串**, 明确记录"AnyTxt 只搜 C 盘"这一限制到 SKILL.md pitfalls;
- 或加一个 `count_matches_all_drives()` helper, 遍历 `["C:\\", "D:\\", "E:\\"]` 汇总。

### Finding 5: `filterExt` **自动容错 `.md` / `*.md` / `MD`**

**实测:**
```
filterExt='md'      count=6661
filterExt='.md'     count=6661     ← 有点也能识别
filterExt='*.md'    count=6661     ← 通配符也能识别
filterExt='MD'      count=6661     ← 大小写不敏感
filterExt='md;txt'  count=6785     ← 分号分隔正确
filterExt='*'       count=6815     ← 通配所有
```

**含义**: 原计划里"必须 strip dots, 不能有 glob"是**过度谨慎**——服务端做了容错。但为了确定性, 客户端做归一化仍然是好习惯 (`.md` 和 `*.md` 会得到相同结果, 归一化到 `md` 显然更规范)。

### Finding 6: 没有 `errno` 字段泄漏错误; error path 是 `resp["error"]`

**实测:**
- 所有成功调用: `result.data.errno` 为 `None` 或 `0` (不同 method 不一致——`GetFragment` 返回 `errno=0`, `Search` 干脆不返回 `errno` 字段);
- `Search` 传 `filterDir='Z:\bogus'`: `errno=None`, `count=0`——**bogus 路径不报错, 静默返回 0**;
- SyncIndex 传 bogus 路径: `errno` 不返回, `output={}`——**也不报错**;
- SyncIndex 传真实路径: `errno=0`, `output={}`——成功。

**含义**:
- **`SyncIndex` 没法通过响应区分成功/失败**, 只能靠"没抛异常 = 成功"这个较弱的信号;
- 用户传错路径不会得到反馈, sync 完 `text` 依然搜不到——需要在 CLI 层加一次真实 verification: sync 完立刻 `Search` 一次, count==0 就 warn;
- JSON-RPC `error` 顶层字段没在实测里出现过, `_call()` 里 `data.get("error")` 检查依然要保留, 但也要检查 `resp.get("error")` (顶层)——AnyTxt 疑似只在协议错误时才用它。

### Finding 7: `SyncIndex` **不返回耗时/文件数**

`SyncIndex` output 是空 dict `{}`——想给用户显示 "indexed N files in T seconds" **必须自己计时 + sync 前后 Search count 比较**。或者干脆只显示 "✅ Sync request completed"。

---

## 🔴 代码级 Bug (P0 — 与 wire-check 无关)

### Bug 1: `Row.humansize()` 破坏 `self.size` 状态
```python
self.size /= 1024   # type: ignore[assignment]
```
就地修改字段, 第二次调用 `humansize()` 或后续 `as_json()` 拿到的 size 就是错的。

**修**: 用局部变量 `size = self.size`, 循环内改的是 `size`。

### Bug 2: `recent` 命令静默丢弃 `--sort/--desc` 用户输入
```python
def recent(limit, path, ext, sort, desc, ...):
    f = _mk_filters(limit, path, ext, "modified", True)   # 硬编码, sort/desc 参数被吞
```
Click 注入了但没用。用户 `--sort size` 会被无声忽略。

**修**: 直接从 `recent` 的 `_shared_options` 里排除 `--sort` 和 `--desc` (它们对 recent 无意义)。

### Bug 3: `files` 命令三个开关声明了但没实现
```python
def files(query, ..., regex, match_path, case):
    rs = search_files(query, f)   # regex / match_path / case 全部丢失
```

**修法二选一:**
- (a) 在 `everything.py` 里实测 `everyfile.search()` 参数名 (先跑 `import everyfile; help(everyfile.search)` 拿真实签名), 把三个开关落地;
- (b) 从 CLI 中删除 (声明但不实现比不声明更糟)。

### Bug 4: `to_everything_query()` 的 `path:"..."` 引号语法可能错
```python
parts.append(f'path:"{normalized}"')
```
Everything 语法里 `path:` 后面**不应该带引号**; 含空格的路径需要**整个 token 用引号包起来** (`"path:C:\Program Files"`), 而不是引号包在路径外面。

**修**: 需要用 everyfile 实测确认。保守写法:
```python
if " " in normalized:
    parts.append(f'"path:{normalized}"')
else:
    parts.append(f'path:{normalized}')
```

### Bug 5: `recent` 的 `dm:>YYYY-MM-DD` 精度太粗
`--within 30m` / `--within 2h` 会退化成"今日全部"。

**修**: 用 Everything 的相对时间语法 `dm:lasthour`, `dm:today`, `dm:lastweek`——更准也更快。

### Bug 6: `EverythingError` 异常类名未验证
`from everyfile import search, EverythingError`——真实类名可能是 `EverythingIPCError` 或就是普通 `RuntimeError`。若 import 失败, `everything.py` 顶层 `try/except ImportError` 会误报"everyfile 未安装", 误导 doctor。

**修**: 装完 `everyfile` 先 `python -c "import everyfile; print([x for x in dir(everyfile) if 'rror' in x.lower()])"` 拿实际类名。

---

## 🟡 CLI 语义 & 一致性 (P1)

### 7.1 `--path` 双语义 (计划自己承认了)
Everything `path:` 是 substring, AnyTxt `filterDir` 是 prefix。用户传 `--path hermes`, `files` 返回上百条, `text` 返回 0。

**修**: MVP 就统一为 **prefix** 语义:
- CLI 收到 `--path C:\dev` 后, 为 Everything 生成 `path:"C:\dev\"` (加尾反斜杠强制前缀), AnyTxt 直传 `filterDir=C:\dev`;
- 别加 `--path-mode` 开关, 保持单一控制旋钮。

### 7.2 `--ext` 归一化不到位
`filters.py` 只做了 `lstrip(".")`, 没做 `.lower()` (Windows 文件系统大小写不敏感, `.PY` 和 `.py` 应等价)。虽然 AnyTxt 服务端做了 case-insensitive 处理, everyfile 侧未知。

**修**: `filters.py` 加 `e.lstrip(".").lower()`。

### 7.3 `sync` 的 `-p` 别名冲突
其他子命令的 `-p/--path` 是"过滤器", `sync` 里的 `-p/--path` 却是"要 sync 的根"——语义完全不同。

**修**: `sync` 只保留 positional `FOLDER`, 删掉 `-p` 别名。

### 7.4 `--within` 里 `m=分钟` 有歧义
和 `sleep`, `systemd`, `find -mtime` 家族的 `m=month` 冲突。

**修**: 只支持 `s/h/d/w`, 或改用 `min`/`mo` 显式后缀。

### 7.5 `extract --head 0` 反直觉
`--head 0` = "只输出字符数" 违反用户直觉 (直觉是"什么都不输出")。

**修**: 改成 `--count-only`, 与 `text --count-only` 对齐命名。

### 7.6 `doctor` 缺 `--format json`
Agent 想脚本化解析健康状态时, 只能解析 rich table (脆弱)。

**修**: `doctor` 加 `--format {text,json}`, JSON 输出结构化的 `{everything: {ok, elapsed_ms, hint}, anytxt: {...}}`。

---

## 🟠 架构/工程性 (P2)

### 8.1 `everyfile` alpha 依赖无兜底
计划说"若上游破了 fork"——这不算 mitigation。**加 `es.exe` fallback 路径**: `everyfile` 优先, ImportError/破坏时降级到 `es.exe` (Voidtools 官方 CLI, PATH 有的话直接跑)。~30 行代码。

### 8.2 `rich` 只给 doctor 用却进主 deps
所有 `local-search files/text` 调用都 import rich, 冷启动变慢。移到 optional dep:
```toml
[project.optional-dependencies]
doctor = ["rich>=13.7"]
```
`doctor.py` 里 lazy import + fallback 到纯 text。

### 8.3 缺 `--offset` 翻页开关
`UnifiedFilters` 里有 offset 字段但 CLI 没暴露。加一个即可。

### 8.4 JSON 输出缺 `truncated` 信号
markdown footer 有 `(showing 20)`, 但 JSON 里 agent 消费时没有明确的 "被截断" 布尔字段——只能算 `len(rows) < total`。加一个 `"truncated": bool` 更明确。

### 8.5 `_resolve_fid_from_path` 性能坑
用 `pattern=stem` + `filterDir=parent` 查同名文件, 会一次拿几十条。**优化**: `filterExt=ext` + `pattern=stem` + `limit=1` + 精确路径比对——大概率一次命中。

### 8.6 SyncIndex 无 verification
sync 完 output 是空 dict, 没法确认到底 index 成没成。**建议**: sync 完立刻用 `Search(pattern="*", filterDir=folder, filterExt="*")` 拿 count, 显示给用户 "Now indexed: N files under <folder>"。

---

## 🟢 测试与验证 (P2)

- `test_anytxt_parsers.py` 覆盖 `_parse_file_entry` 的 list-of-lists + field-order-driven 解析 (**这是 Finding 1 修复后新增的核心逻辑, 必测**);
- `test_cli_smoke.py` 用 `respx` mock AnyTxt + monkeypatch `everyfile.search`, 跑一次 `local-search files --format json`, 断言 JSON schema;
- Task 4 里的 "live smoke" 明确标注为**人工验证**, 不进 CI。

---

## 🟢 文档 (P2)

- SKILL.md `description` ~630 字符, 离 1024 上限还有 40%, 可挤更多关键词 (`grep local files`, `find file windows agent`, `fulltext PDF windows`, `AnyTxt CLI wrapper`);
- `related_skills` 顺序: 把 `ocr-and-documents` 放**第一位**, 加一行说明两者互补关系: `local-search extract` = 免费 (AnyTxt 已提取的), `ocr-and-documents` = 未索引/需 OCR 的;
- `doctor` 失败提示应引用 `ensure-everything-user-session.ps1` 的完整绝对路径, 而不是只打印 `Start-Process '<exe>'` 一行——目前是脱节的。

---

## 计划里我很赞的地方 (原样保留)

1. **两后端分工清晰**——Everything = 名字, AnyTxt = 全文, 不给 Everything 加 `content:` (你的记忆里已经踩过坑);
2. **`fields="meta"` 无 limit 会 timeout** 被明确写进注释;
3. **`extract` 复用 AnyTxt 已提取文本 → 免 marker-pdf** 是这个技能的核心增量价值;
4. **`sync` 命令**——agent 场景下写完文件立刻搜是常见需求, 很多类似工具忘做;
5. **markdown-first + `--format` 切换** 符合用户偏好;
6. **单一 CLI 入口 + 自解释子命令**, 避免 `--by files/text` 反模式。

---

## 修改优先级汇总

### P0 (必须, 进入 Task 1 前)
1. 路径全局替换 `~/.hermes/profiles/devops/skills/system-administration/local-search/` → `C:\Users\jinnn\Documents\more-skills\skills\local-search\`;
2. 修 6 个代码 Bug (Row.humansize / recent 忽略 sort / files 三个未实现 flag / path: 引号语法 / dm: 精度 / EverythingError 类名);
3. 应用 AnyTxt wire-check 的 7 项发现, **重写 anytxt.py 的 `_parse_file_entry` 和 `_fetch_snippet`, 引入 field-order 动态映射**;
4. 加装完 `everyfile` 后确认 `search()` 签名 (regex / match_path / case_sensitive 参数名 + 异常类名) 的一次 smoke 步骤。

### P1 (Task 5-6 落地前)
5. 统一 `--path` 语义为 prefix;
6. `--ext` 加 `.lower()`;
7. `sync` 去掉 `-p` 别名;
8. `--within` 去掉 `m` 或改 `min`/`mo`;
9. `extract --head 0` → `extract --count-only`;
10. `doctor` 加 `--format json`;
11. `everyfile` 加 `es.exe` fallback;
12. SyncIndex 加 post-sync verification (count files under folder);
13. `filterDir=""` 只搜 C 盘的限制写进 SKILL.md pitfalls (或提供多盘 helper)。

### P2 (可 v1.1 迭代)
14. `rich` 移到 optional dep, `doctor.py` 支持纯 text 输出;
15. CLI 加 `--offset`, JSON 加 `truncated` 字段;
16. `test_anytxt_parsers.py` + `test_cli_smoke.py`;
17. `_resolve_fid_from_path` 用 `filterExt+stem+limit=1` 优化;
18. SKILL.md description 挤更多关键词, `related_skills` 顺序调整;
19. `doctor` 失败提示引用 `ensure-everything-user-session.ps1` 完整路径;
20. `GetFragment` 高亮标记 `*<<*...*>>*` 转换为 markdown `**...**` (可选);
21. `extract` 加 `--strip-page-marks` 去掉 `📄 P N ` 页码标记。

---

## 决策项待用户确认

- [x] **技能落地目录**: `C:\Users\jinnn\Documents\more-skills\skills\local-search\` (已确认)
- [x] **AnyTxt wire-check**: 已完成, 发现固化在本文档 Finding 1-7
- [ ] **技能注册机制**: `more-skills` 不在 hermes agent 默认扫描路径。三选一:
    - (a) 建 junction `mklink /J ~/.hermes/profiles/devops/skills/system-administration/local-search  C:\Users\jinnn\Documents\more-skills\skills\local-search`
    - (b) 只依赖 `uv tool install` 让 CLI 全局可用, 不注册为 hermes skill (skill_view 用不了, agent 靠常识调用 CLI)
    - (c) 两个都做
- [ ] **修订版计划文档**: 是否让我基于本 REVIEW 生成一份 `2026-07-16_local-search-skill-v2.md` (P0/P1 全部应用完的)?

---

**Reviewer**: Hermes Agent (claude / ark-code-latest)
**评审耗时**: ~15 min (读全文 + wire-check + 分析)
