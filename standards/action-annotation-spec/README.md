# Markdown Action Annotation 标准体系总纲

这是一套旨在将 Markdown 静态文档转化为**多智能体（Multi-Agent）自动化工作流流转画布**的注释标准。

通过在 Markdown 文件中植入符合标准语法的 HTML 隐性注释，不仅不会干扰最终读者的阅读体验，还能精准地将排版、配图、格式化等任务指派给下游的自动化脚本或智能体。

---

## 1. 核心语法规范 (Core Syntax)

本标准严格借用 **HTML 属性语法 (HTML Attribute Syntax)** 来传递指令和参数。

### 标准格式
```html
<!-- ACTION="[动作名称]" STATUS="[当前状态]" KEY="VALUE" ... -->
```

### 编写约束（大模型生成须知）
由于解析器直接对 HTML 属性进行解析，为避免正则表达式崩溃，必须严格遵守引号使用规范：
1. **外部属性包裹**：所有的值必须被双引号 `"` 包裹。
2. **内部属性转义**：属性值内部需要使用引号时，**优先使用单引号 `'`**。如果不可避免必须使用双引号，则**必须使用 HTML 实体转义符 `&quot;`**。绝不允许直接嵌套双引号。

**【正确示例】**：
```html
<!-- ACTION="GENERATE_IMAGE" STATUS="TODO" PROMPT="一个带着'墨镜'的帅哥" -->
<!-- ACTION="GENERATE_IMAGE" STATUS="TODO" PROMPT="牌子上写着&quot;你好&quot;的猫咪" -->
```

**【错误示例】**：
```html
<!-- 错误：双引号未转义导致解析截断 -->
<!-- ACTION="GENERATE_IMAGE" STATUS="TODO" PROMPT="牌子上写着"你好"的猫咪" -->
```

---

## 2. 并发与调度模型 (Dispatcher Pattern)

本标准不主张大模型直接抢占文件锁。我们推崇**派单模式 (Push Model)**：
1. **轻量扫描**：由轻量级脚本（Dispatcher）读取 Markdown，根据 `STATUS="TODO"` 提取任务块及其属性参数。
2. **免上下文分发**：调度器将属性参数作为极简的 Prompt 分发给对应的子智能体。子智能体无需阅读整篇文档。
3. **单点回写**：子智能体将结果（如生成的图片路径）返回给调度器，由调度器统一无冲突地回写 Markdown 状态。

通过该模式，可将大模型的 Token 消耗降至极低，并彻底避免文件读写竞态冲突。

---

## 3. 状态机与接力栈 (Lifecycle & Action Stacking)

`STATUS` 字段是一个严格的单向生命周期标识，绝不能用于承载 `COMMENT` 或 `FIXME` 等指令型语义（这些应作为 `ACTION` 存在）。

### 状态枚举值
*   **`TODO`**：待处理（调度器扫描目标）。
*   **`DONE`**：处理完成（调度器将包含 `RESULT` 等执行输出追加于此）。
*   **`PUBLISHED`**：已上云（如本地资产已被上传至 CDN）。
*   **`ERROR`**：执行失败（调度器可追加 `REASON` 字段）。

### 接力追加机制 (Action Stacking)
我们坚持**事件溯源（Event Sourcing）**理念：**不覆盖，只追加**。
当某个动作完成（`DONE`），并且需要将资产流转给下一个环节时，必须在其下方新开一行插入新的 `TODO` 注释，保留完整处理日志。

**【工作流示例】**：
1. 生成需求建立：
```html
<!-- ACTION="GENERATE_IMAGE" STATUS="TODO" ID="img-1" PROMPT="赛博朋克城市" -->
![未生成](placeholder.png)
```

2. 画图 Agent 生成完毕，并交出上云接力棒：
```html
<!-- ACTION="GENERATE_IMAGE" STATUS="DONE" ID="img-1" PROMPT="赛博朋克城市" RESULT="./assets/city.png" -->
<!-- ACTION="UPLOAD_ASSET" STATUS="TODO" ID="img-1-up" TARGET="./assets/city.png" -->
![本地图](./assets/city.png)
```

3. 发布 Agent 完成上云：
```html
<!-- ACTION="GENERATE_IMAGE" STATUS="DONE" ID="img-1" PROMPT="赛博朋克城市" RESULT="./assets/city.png" -->
<!-- ACTION="UPLOAD_ASSET" STATUS="DONE" ID="img-1-up" TARGET="./assets/city.png" RESULT="https://cdn.com/city.png" -->
![云端图](https://cdn.com/city.png)
```

---

## 4. 扩展规范导航

具体的 ACTION 动词字典与领域要求，请参阅以下子分类标准文档：
*   [配图与媒体检索规范](./image-action-spec.md) (`image-action-spec.md`)
*   [矢量与图表渲染规范](./diagram-action-spec.md) (`diagram-action-spec.md`)
