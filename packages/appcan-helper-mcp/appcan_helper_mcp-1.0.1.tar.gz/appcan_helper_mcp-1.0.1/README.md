# AppCan Helper MCP Server

这是一个使用 FastMCP 构建的 AppCan 助手 MCP 服务器，提供基础工具和 AppCan 官方文档查询功能。

## 🤖 AI 使用指南

### 如何向 AI 说明 MCP 使用方法

本 MCP 服务通过以下方式向 AI 提供使用说明：

#### 1. **详细的工具描述（Docstring）**
每个工具都包含完整的类型注解和文档字符串，AI可以通过这些信息了解：
- 工具的功能和用途
- 参数类型和说明
- 返回值格式
- 使用示例

#### 2. **提示词系统（Prompt）**
使用 `@mcp.prompt` 装饰器提供的 `help_prompt` 包含：
- 所有工具的完整列表
- 详细的参数说明
- 实际使用示例
- 最佳实践建议
- 常见使用场景

#### 3. **智能返回格式**
所有工具返回结果都采用：
- 结构化的文本格式
- 清晰的状态标识（✅❌🔍📚等）
- 友好的错误提示
- 操作建议和下一步指导

### 📋 AI 调用示例

```python
# AI 可以通过以下方式获取帮助信息
result = await client.get_prompt("help_prompt")

# 然后根据信息调用具体工具
result = await client.call_tool("search_appcan_docs", {
    "query": "插件开发"
})
```

## 功能特性

### 🛠️ 基础工具
- `greet(name)` - 向用户问候
- `get_current_time()` - 获取当前时间

### 📚 AppCan 文档查询工具
- `search_appcan_docs(query, category)` - 搜索 AppCan 文档内容
  - 支持中文模糊搜索
  - 最多返回3个匹配度最高的结果
  - 支持按分类筛选
- `get_appcan_doc_categories()` - 获取所有文档分类列表
- `get_appcan_doc_content(doc_path, page, force_refresh)` - 获取指定文档内容
  - 返回 Markdown 格式内容
  - 支持分页显示（长内容自动分页）
  - 支持缓存和强制刷新
- `clear_appcan_docs_cache()` - 清空文档缓存

## 安装和运行

### 1. 安装依赖
```bash
# 安装所有依赖
uv pip install requests beautifulsoup4 fuzzywuzzy python-levenshtein markdown

# 或者从 requirements.txt 安装
uv pip install -r requirements.txt
```

### 2. 运行服务器

#### 方法一：使用模块运行（推荐）
```bash
# 先安装开发版本
uv pip install -e .

# 使用模块运行
python -m appcan_helper_mcp.server
```

#### 方法二：使用命令行工具
```bash
# 安装后可直接使用
appcan-helper-mcp
```

#### 方法三：使用 FastMCP CLI
```bash
fastmcp run appcan_helper_mcp.server:mcp
```

### 3. 测试服务器
在另一个终端运行：
```bash
python test/test_client.py
```

## 版本管理

### 统一版本号管理
项目采用统一的版本号管理策略，只需修改一个地方即可更新所有位置的版本号：

```bash
# 使用提供的脚本更新版本号
python scripts/update_version.py 1.2.0

# 或使用 Makefile 命令（需要安装 make）
make bump-patch  # 修订版本号升级 (1.0.0 -> 1.0.1)
make bump-minor  # 次版本号升级 (1.0.0 -> 1.1.0)
make bump-major  # 主版本号升级 (1.0.0 -> 2.0.0)
```

版本号遵循 [语义化版本控制规范](https://semver.org/lang/zh-CN/)：
- 主版本号(MAJOR)：当你做了不兼容的 API 修改
- 次版本号(MINOR)：当你做了向下兼容的功能性新增
- 修订号(PATCH)：当你做了向下兼容的问题修正

## AppCan 文档查询功能详解

### 🔍 搜索功能
- **模糊匹配**：支持关键词模糊搜索，自动匹配文档标题、分类和路径
- **中文支持**：完全支持中文关键词搜索
- **智能排序**：按匹配度排序，返回最相关的结果
- **结果限制**：最多返回3个结果，避免信息过载

### 💾 缓存机制
- **自动缓存**：文档内容自动缓存1天，提高访问速度
- **缓存目录**：`cache/` 目录存储缓存文件
- **强制刷新**：支持强制刷新获取最新内容
- **缓存管理**：提供缓存清理工具

### 📖 内容处理
- **Markdown 格式**：自动转换为 Markdown 格式，便于阅读
- **代码保护**：保留代码示例的格式和缩进
- **链接处理**：自动转换相对链接为绝对链接
- **图片支持**：图片以链接形式显示

### 📄 分页支持
- **自动分页**：长内容（>50KB）自动分页显示
- **页面大小**：每页15KB，适合阅读
- **导航提示**：提供下一页查看提示

## 使用示例

### 基础功能
```python
# 问候
result = await client.call_tool("greet", {"name": "张三"})

# 获取时间
result = await client.call_tool("get_current_time", {})
```

### AppCan 文档查询
```python
# 搜索文档
result = await client.call_tool("search_appcan_docs", {
    "query": "插件开发"
})

# 获取文档分类
result = await client.call_tool("get_appcan_doc_categories", {})

# 查看具体文档
result = await client.call_tool("get_appcan_doc_content", {
    "doc_path": "/IDE/summary",
    "page": 1,
    "force_refresh": False
})

# 强制刷新文档
result = await client.call_tool("get_appcan_doc_content", {
    "doc_path": "/plugin-API/manual",
    "force_refresh": True
})

# 清空缓存
result = await client.call_tool("clear_appcan_docs_cache", {})
```

## 文档分类

AppCan 文档中心包含以下主要分类：

- **入门篇**：平台概述、创建APP、术语解释
- **工具篇**：IDE相关功能和操作指南
- **指导篇**：开发流程、证书申请、配置说明
- **基础篇**：
  - 引擎API（uexWindow、uexWidget等）
  - JS SDK（本地存储、网络请求、UI组件等）
  - 插件API（系统功能、功能扩展、界面布局等）
  - UI框架（弹性盒子、基础样式等）
- **高级篇**：界面开发、MVVM、组件化开发
- **案例篇**：实际应用案例和解决方案
- **常见问题篇**：FAQ和故障排除

## 项目结构
```
appcan-helper-mcp/
├── pyproject.toml               # 包配置文件
├── README.md                   # 项目说明
├── LICENSE                     # 许可证
├── requirements.txt            # 依赖列表
├── MCP_PACKAGING_GUIDE.md      # 发布指南
├── src/                        # 源代码目录
│   └── appcan_helper_mcp/
│       ├── __init__.py       # 包初始化
│       ├── server.py         # MCP 服务器主文件
│       └── utility.py        # AppCan 文档工具类
└── test/                       # 测试目录
    ├── __init__.py             # 测试包初始化
    └── test_client.py          # 测试客户端
```

## 技术特性

### 🏗️ 架构设计
- **分层架构**：业务逻辑与工具类分离
- **工具类封装**：AppCanDocsUtility 封装所有文档处理逻辑
- **错误处理**：完善的异常处理和用户友好的错误信息
- **代码规范**：遵循 FastMCP 开发规范
- **模块化设计**：采用标准 src 包结构，支持相对导入

### 🚀 性能优化
- **智能缓存**：自动缓存减少网络请求
- **分页机制**：大内容分页提高响应速度
- **异步处理**：全异步设计，支持并发访问
- **连接复用**：HTTP 连接优化

### 🔒 安全特性
- **输入验证**：严格的参数验证
- **路径安全**：防止路径遍历攻击
- **请求限制**：合理的超时和重试机制
- **错误隔离**：错误不会影响其他功能

## 开发注意事项

### 基本规范
1. **类型注解必须完整** - FastMCP 依赖类型注解生成工具描述
2. **添加清晰的 docstring** - 帮助 AI 理解工具用途
3. **处理异常情况** - 提供有意义的错误信息
4. **使用异步客户端** - 所有客户端操作都是异步的
5. **上下文管理** - 必须在 `async with client:` 中使用客户端
6. **缓存管理** - 定期清理缓存避免磁盘空间占用
7. **网络超时** - 设置合理的网络请求超时时间

## 许可证

本项目仅供学习和研究使用。AppCan 相关商标和文档版权归正益移动互联科技股份有限公司所有。