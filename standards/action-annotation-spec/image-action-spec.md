# 配图与媒体检索规范 (Image Action Spec)

本文档隶属于 [Markdown Action Annotation](./README.md) 标准体系，专门规范与**普通位图图像**（如插画、照片、表情包、外部检索图）处理相关的动作。

## 1. 强保留源图片 (RETAIN_ORIGINAL)

用于标识必须被完整保留的实证类资产（如带数据的图表、真实的截图等）。

### 参数规范
*   **`ACTION="RETAIN_ORIGINAL"`**
*   **`STATUS`**: `TODO` -> `DONE`
*   **`ID`**: 全局唯一标识符
*   **`SOURCE`**: 原始图像的 URL 或相对路径
*   **`REASON`**: （可选）为何必须保留该图片的简要说明

### 示例
```html
<!-- ACTION="RETAIN_ORIGINAL" STATUS="TODO" ID="img-retain-01" SOURCE="assets/real-data-chart.png" REASON="该图包含精密数值，不可丢弃" -->
![数据走势图](assets/real-data-chart.png)
```

---

## 2. 文生图请求 (GENERATE_IMAGE)

用于通知下游的图像生成类 Agent（或 `markdown-illustrator` 的生图管线）使用大模型绘制一张全新的视觉缓冲图或意境图。

### 参数规范
*   **`ACTION="GENERATE_IMAGE"`**
*   **`STATUS`**: `TODO` -> `DONE`
*   **`ID`**: 全局唯一标识符
*   **`PROMPT`**: 详细的生图英文或中文提示词。**注意：内部若包含引号，需使用单引号或 `&quot;`**。
*   **`STYLE`**: （可选）期待的视觉风格描述，如 `pop-science`, `cyberpunk`。

### 示例
```html
<!-- ACTION="GENERATE_IMAGE" STATUS="TODO" ID="img-gen-01" PROMPT="A cat wearing a 'cool' sunglasses, high resolution" STYLE="pop-science" -->
![酷炫的猫咪](placeholder.png "正在生成的插画")
```

---

## 3. 搜索引擎找图 (SEARCH_WEB)

用于指示下游检索系统在互联网或企业本地图库中搜索满足特定事实或新闻属性的截图素材。

### 参数规范
*   **`ACTION="SEARCH_WEB"`**
*   **`STATUS`**: `TODO` -> `DONE`
*   **`ID`**: 全局唯一标识符
*   **`QUERY`**: 用于提交给搜索引擎的关键词组合。
*   **`REQUIREMENT`**: （可选）对于搜索结果的具体要求说明，例如要求必须是带红头文件盖章的截图。

### 示例
```html
<!-- ACTION="SEARCH_WEB" STATUS="TODO" ID="img-search-01" QUERY="航天五院529厂 测试设备 实拍图" REQUIREMENT="必须是带有真实设备的工厂实拍照片" -->
![航天级测试场景](placeholder.png "新闻截图待搜索")
```
