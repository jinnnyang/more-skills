---
name: pretty-mermaid
description: 绘制美观的 Mermaid 图表（类图、时序图、状态图、ER图、XY图表等），包含语法检查和导出为 SVG/PNG 的功能。当用户需要绘制图表或你的回答中包含 Mermaid 代码时，优先使用此技能。
---

# When to use
- 当用户明确要求绘制图表（如流程图、时序图、类图、状态图、ER图、XY图表等）时。
- 当你需要使用图表来辅助说明复杂的逻辑、架构或流程时。
- 当你需要将 Mermaid 代码导出为美观的图片（SVG 或 PNG）时。

# When NOT to use
- 当用户只需要简单的文本列表或表格时。
- 当用户明确要求使用其他绘图工具（如 PlantUML, Graphviz）时。

# Prerequisites
- **Node.js**: 用户系统上必须安装有 Node.js。
- **自动初始化**: 技能根目录下的 `cli.js` 在首次运行时会自动检测并安装所需的 Node.js 依赖，你不需要手动执行 `npm install`。

# Workflow

1. **选择图表类型并加载参考**
   - 根据用户需求或你要表达的内容，选择合适的图表类型。
   - **必须**阅读对应的参考文件以获取语法规范和美观示例：
     - 流程图: `references/flowchart.md`
     - 时序图: `references/sequence.md`
     - 类图: `references/class.md`
     - 状态图: `references/state.md`
     - ER图: `references/er.md`
     - XY图表: `references/xychart.md`
   - *注意：任何需要显示的文本都需要被双引号包围，节点/参与者的内部命名应该具有自解释性。*

2. **验证 Mermaid 代码**
   - 你可以直接通过代码字符串进行语法验证，无需在用户工作区创建临时文件：
     ```bash
     node <pretty-mermaid-path>/cli.js --validate-only --code "YOUR_MERMAID_CODE"
     ```
   - 若代码内容过长，可以将其保存至绝对路径下的临时文件（如 `/absolute/path/to/temp.mmd`）再进行验证：
     ```bash
     node <pretty-mermaid-path>/cli.js --validate-only --input /absolute/path/to/temp.mmd
     ```
   - 如果验证失败，根据输出的诊断信息和修复指南修改代码，重新验证直到通过。

3. **预览与确认**
   - 将验证通过的 Mermaid 代码以 markdown 代码块的形式输出给用户预览。
   - 主动询问用户是否需要修改，并配合用户进行调整，直到用户确认无误。

4. **导出图片 (可选)**
   - 用户确认后，询问是否需要导出图片，以及需要的格式（SVG 或 PNG）和主题（如 `zinc-light`, `zinc-dark`, `tokyo-night`, `dracula`, `github-light`, `github-dark` 等）。
   - 直接通过代码字符串导出：
     ```bash
     node <pretty-mermaid-path>/cli.js --code "YOUR_MERMAID_CODE" -o /absolute/path/to/output.png -t tokyo-night
     ```
   - 或通过已保存的临时文件导出：
     ```bash
     node <pretty-mermaid-path>/cli.js --input /absolute/path/to/temp.mmd -o /absolute/path/to/output.png -t tokyo-night
     ```
   - 告知用户文件已保存的绝对路径。

5. **完成任务**
   - 如果你在步骤 2/4 中创建了临时的 `.mmd` 文件，**必须主动删除它们**以保持工作区整洁。如果你直接使用了 `--code` 字符串参数，则无需进行清理！
   - 确认无误后完成任务。

# Examples

**场景：用户要求画一个简单的登录流程图**

1. 读取 `references/flowchart.md` 了解规范。
2. 编写代码：
   ```mermaid
   graph TD
       start["开始"] --> input["输入账号密码"]
       input --> validate{"验证信息"}
       validate -->|"成功"| home["进入主页"]
       validate -->|"失败"| error["提示错误"]
       error --> input
   ```
3. 运行语法检查：
   ```bash
   node c:/Users/jinnn/Documents/more-skills/skills/pretty-mermaid/cli.js --validate-only --code "graph TD; start[\"开始\"] --> input[\"输入账号密码\"]; input --> validate{\"验证信息\"}; validate -->|\"成功\"| home[\"进入主页\"]; validate -->|\"失败\"| error[\"提示错误\"]; error --> input"
   ```
4. 输出代码给用户预览并确认。
5. 用户确认并要求导出暗色主题的 PNG。
6. 运行导出：
   ```bash
   node c:/Users/jinnn/Documents/more-skills/skills/pretty-mermaid/cli.js --code "graph TD; start[\"开始\"] --> input[\"输入账号密码\"]; input --> validate{\"验证信息\"}; validate -->|\"成功\"| home[\"进入主页\"]; validate -->|\"失败\"| error[\"提示错误\"]; error --> input" -o c:/Users/jinnn/Documents/more-skills/login.png -t tokyo-night
   ```
7. 告知用户图片保存位置，完成任务。（由于没有创建临时文件，不需要进行清理工作！）

# Troubleshooting
- **`npm: command not found`**: 确保系统已安装 Node.js。
- **依赖安装失败**: 若 `cli.js` 自动安装依赖失败，可手动进入 `scripts` 目录执行 `npm install`。
- **语法检查失败**: 仔细查看 `cli.js` 打印出的错误日志和诊断指南，确认特殊字符均已被双引号包裹，以及图表声明正确。
