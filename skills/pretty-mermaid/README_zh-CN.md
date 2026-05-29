# `pretty-mermaid` 技能

> [!WARNING]
> 当前技能将会迁移到 `more-skills` 下面，后续不再单独维护。请移步使用 [more-skills](https://github.com/jinnnyang/more-skills) 仓库中的版本。

绘制美观的 Mermaid 图表（类图、时序图、状态图、ER图、XY图表等），包含语法检查和导出为 SVG/PNG 的功能。

## 功能特性

- **统一的 CLI 入口**：通过根目录下的 `cli.js` 统一执行所有的语法验证与图片导出任务。
- **自动初始化**：在首次运行时自动检测并在后台静默安装所需的 Node.js 依赖包，实现“零门槛”使用。
- **直接字符串处理**：支持通过 `--code` 参数直接传递 Mermaid 代码，避免了在工作区生成并清理临时 `.mmd` 文件的麻烦。
- **丰富的绘图指南**：新增了状态图和 ER 图，配合已有的流程图、时序图、类图和 XY 图表，构成完整的绘图参考库。

## 环境要求

- **Node.js**：系统必须已安装 Node.js。

## 命令行接口 (CLI) 使用说明

核心入口为技能根目录下的 `cli.js`：

```bash
node cli.js [options]
```

### 参数说明：
- `-c, --code <code>`      直接传入 Mermaid 代码字符串。
- `-i, --input <file>`     传入已保存的 `.mmd` 文件路径。
- `-o, --output <file>`    导出的图片路径。自动根据后缀名（`.svg` 或 `.png`）决定导出格式。
- `-t, --theme <theme>`    选择渲染主题（可选 `zinc-light` (默认), `zinc-dark`, `tokyo-night`, `dracula`, `github-light`, `github-dark` 等）。
- `-v, --validate-only`    仅做语法验证，不进行图片渲染与导出。

### 使用示例：

1. **仅验证语法**：
   ```bash
   node cli.js --validate-only -c "graph TD; A[\"开始\"] --> B[\"结束\"]"
   ```

2. **直接将代码渲染为 PNG**：
   ```bash
   node cli.js -c "graph TD; A[\"开始\"] --> B[\"结束\"]" -o output.png -t tokyo-night
   ```

3. **从 `.mmd` 文件中渲染为 SVG**：
   ```bash
   node cli.js -i diagram.mmd -o output.svg
   ```

## 参考指南
- [流程图指南](references/flowchart.md)
- [时序图指南](references/sequence.md)
- [类图指南](references/class.md)
- [状态图指南](references/state.md)
- [ER图指南](references/er.md)
- [XY图表指南](references/xychart.md)
