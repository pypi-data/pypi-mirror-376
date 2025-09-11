# MCP 包发布原理详解

## 🔍 核心概念

### 1. 入口点（Entry Points）原理

**入口点是 Python 包系统的核心机制**，它告诉系统：
- 当用户运行某个命令时，应该调用哪个函数
- 包的哪个模块和函数是"主入口"

### 2. 两种入口点配置方式

#### 方式一：`project.scripts`（推荐）
```toml
[project.scripts]
appcan-helper-mcp = "appcan_helper_mcp.server:main"
```

**解释**：
- `appcan-helper-mcp`：命令名称（用户在终端输入的）
- `appcan_helper_mcp.server`：Python 模块路径（注意：现在使用正式的 server.py）
- `main`：模块中的函数名

#### 方式二：`project.entry-points`（项目中未使用）
```toml
[project.entry-points."fastmcp.servers"]
appcan-helper = "appcan_helper_mcp.server:mcp"
```

**解释**：
- `fastmcp.servers`：入口点组（MCP 框架可能会扫描这个组）
- `appcan-helper`：服务标识符
- `mcp`：指向 server.py 中的 mcp 对象

> ⚠️ 注意：当前项目实际只使用了 `project.scripts` 方式，这种方式已足够满足需求。

## 🏠 标准 src 包结构

```
appcan-helper-mcp/
├── pyproject.toml              # 包配置文件（关键！）
├── README.md                   # 项目说明
├── LICENSE                     # 许可证
├── requirements.txt            # 依赖列表（可选）
├── MCP_PACKAGING_GUIDE.md      # 发布指南
├── src/                        # 📦 源代码目录
│   └── appcan_helper_mcp/
│       ├── __init__.py       # 包初始化
│       ├── server.py         # MCP 服务器主文件
│       └── utility.py        # AppCan 文档工具类
└── test/                       # 🧪 测试目录
    ├── __init__.py             # 测试包初始化
    └── test_client.py          # 测试客户端
```

### 标准 src 布局的优势

1. **符合 Python 最佳实践**：现代 Python 项目的标准做法
2. **清晰的分离**：源代码、测试、文档各就各位
3. **易于维护**：结构明确，新手可快速理解
4. **支持复杂功能**：为未来扩展预留空间
5. **打包友好**：setuptools 可以正确识别包结构

## 🔧 构建和发布流程

### 1. 本地测试
```bash
# 安装构建工具
uv pip install build twine

# 构建包
uv build

# 本地安装测试
uv pip install -e .

# 测试命令
appcan-helper-mcp
```

### 2. 发布到 PyPI
```bash
# 构建发布包
uv build

# 上传到 PyPI（需要账号）
uvx twine upload dist/*
```

### 3. 用户使用
```bash
# 用户安装
uv pip install appcan-helper-mcp

# 或者直接运行（uvx 方式）
uvx appcan-helper-mcp@latest
```

## 🎯 `uvx` 的工作原理

当用户运行 `uvx appcan-helper-mcp@latest` 时：

1. **下载包**：从 PyPI 下载最新版本的包
2. **创建虚拟环境**：临时创建一个独立的 Python 环境
3. **安装依赖**：自动安装包的所有依赖
4. **查找入口点**：读取 `pyproject.toml` 中的 `[project.scripts]`
5. **执行函数**：调用 `appcan_helper_mcp.server:main` 函数
6. **运行服务**：执行 `main()` 函数，启动 MCP 服务器

## 📋 与您的示例对比

### 您看到的配置：
```json
{
  "mcpServers": {
    "mcp-feedback-enhanced": {
      "command": "uvx",
      "args": ["mcp-feedback-enhanced@latest"]
    }
  }
}
```

### 对应您的包：
```json
{
  "mcpServers": {
    "appcan-helper": {
      "command": "uvx", 
      "args": ["appcan-helper-mcp@latest"]
    }
  }
}
```

## 🔍 关键文件解析

### pyproject.toml 关键部分：
```toml
# 包元数据
[project]
name = "appcan-helper-mcp"              # PyPI 包名
version = "0.1.0"                       # 版本号
dependencies = ["fastmcp", "requests", ...] # 依赖

# 🔑 入口点定义（最关键）
[project.scripts]
appcan-helper-mcp = "appcan_helper_mcp.server:main"
#     ↑命令名          ↑正式模块路径      ↑函数名

# 包查找配置
[tool.setuptools.packages.find]
where = ["src"]                         # 在 src 目录下查找包
include = ["appcan_helper_mcp*"]        # 包含哪些包
```

### src/appcan_helper_mcp/server.py 中的入口函数：
```python
def main():
    """主入口函数 - 这就是 pyproject.toml 中指定的函数"""
    print("启动 AppCan Helper MCP 服务器...")
    mcp.run()  # 启动 FastMCP 服务器

if __name__ == "__main__":
    main()
```

## 📝 重要更新说明

### 🚀 推荐的运行方式
```bash
# 1. 安装开发版本
uv pip install -e .

# 2. 使用模块运行（推荐）
uv run python -m appcan_helper_mcp.server

# 3. 使用命令行工具
appcan-helper-mcp

# 4. 使用 FastMCP CLI
fastmcp run appcan_helper_mcp.server:mcp
```

### ⚠️ 注意事项
1. **相对导入问题**: `server.py` 使用相对导入，必须作为包运行
2. **版本一致性**: 确保运行的是最新的 `server.py` 版本

## 💫 总结

**整个流程的核心逻辑**：
1. **pyproject.toml** 告诉 Python："当用户运行 `appcan-helper-mcp` 命令时，调用 `appcan_helper_mcp.server.main()` 函数"
2. **main() 函数** 是实际的入口点，负责启动 MCP 服务器
3. **uvx** 工具负责处理包的下载、安装和命令执行
4. **标准化结构** 确保了代码的可维护性和扩展性

这样，用户就可以通过简单的命令使用您的 MCP 服务，而不需要手动下载代码和安装依赖！