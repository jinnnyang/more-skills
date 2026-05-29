# 流程图 (Flowchart) 绘图指南

## 适用场景
流程图非常适合展示：
- 算法或程序的逻辑流程
- 业务审批或操作流程
- 系统架构图（通过节点和连接线展示组件关系）
- 决策树

## 语法要点
- 支持的方向：`TD` (从上到下), `LR` (从左到右), `BT` (从下到上), `RL` (从右到左)
- 节点形状：`[矩形]`, `(圆角矩形)`, `{菱形/判断}`, `((圆形))` 等
- 连接线：`-->` (实线箭头), `---` (实线), `-.->` (虚线箭头), `==>` (粗线箭头)
- 标签：`-->|"标签文本"|`
- **重要规范**：任何需要显示的文本都需要被双引号包围，并且节点的内部命名应该具有自解释性，而不是使用ABCD这种抽象名称。

## 美观示例

### 1. 基础业务流程
```mermaid
graph TD
    start["开始"] --> isLogged{"是否已登录?"}
    isLogged -->|"是"| home["进入主页"]
    isLogged -->|"否"| login["跳转登录页"]
    login --> success{"登录成功?"}
    success -->|"是"| home
    success -->|"否"| login
    home --> endNode["结束"]
```

### 2. 系统架构图 (带子图)
```mermaid
graph LR
    subgraph client["客户端"]
        app["移动端 App"]
        web["Web 浏览器"]
    end

    subgraph gateway["API 网关"]
        kong["Kong Gateway"]
    end

    subgraph services["微服务"]
        auth["认证服务"]
        user["用户服务"]
        order["订单服务"]
    end

    subgraph database["数据库"]
        db[("PostgreSQL")]
        cache[("Redis")]
    end

    app --> kong
    web --> kong
    kong --> auth
    kong --> user
    kong --> order
    
    auth --> cache
    user --> db
    order --> db
```
