# Scripts 目录说明

本目录包含项目开发和维护过程中使用的各种脚本工具。

## 脚本列表

### update_version.py
**功能**: 统一版本号更新工具

**用途**: 
- 一次性更新项目中所有位置的版本号
- 确保 pyproject.toml、__init__.py 和 manifest.json 中的版本号保持一致

**使用方法**:
```bash
# 激活虚拟环境后运行
python scripts/update_version.py <new_version>

# 示例
python scripts/update_version.py 1.2.0
```

**参数说明**:
- `<new_version>`: 新的版本号，需遵循语义化版本控制规范 (SemVer)

**工作原理**:
1. 验证版本号格式是否正确
2. 更新 pyproject.toml 文件中的版本号
3. 更新 src/appcan_helper_mcp/__init__.py 文件中的 __version__ 变量
4. 更新 manifest.json 文件中的 version 字段
5. 输出操作结果和下一步建议

### __init__.py
**功能**: Python 包标识文件

**用途**: 
- 使 scripts 目录成为一个 Python 包
- 允许其他模块导入 scripts 目录中的脚本

## 版本管理策略

### 静态版本号
项目采用静态版本号管理策略，直接在 pyproject.toml 中定义版本号，而不是使用 setuptools_scm 动态生成。这样做的好处是：

1. **PyPI 兼容性**: 避免因本地版本标识符导致的 PyPI 上传问题
2. **版本一致性**: 确保所有包文件使用相同的版本号格式
3. **可预测性**: 版本号完全由开发者控制，不会因 Git 状态而变化

### 统一版本号更新
通过 update_version.py 脚本统一管理所有位置的版本号更新，确保一致性：
- pyproject.toml: `version = "x.y.z"`
- src/appcan_helper_mcp/__init__.py: `__version__ = "x.y.z"`
- manifest.json: `"version": "x.y.z"`

## 使用建议

1. **版本号管理**: 
   - 推荐使用 `update_version.py` 脚本而不是手动修改各文件
   - 遵循语义化版本控制规范 (MAJOR.MINOR.PATCH)

2. **Makefile 集成**:
   - 项目根目录的 Makefile 提供了便捷的版本号升级命令:
     - `make bump-patch`: 修订版本号升级 (1.0.0 → 1.0.1)
     - `make bump-minor`: 次版本号升级 (1.0.0 → 1.1.0)
     - `make bump-major`: 主版本号升级 (1.0.0 → 2.0.0)

3. **Git 集成**:
   - 更新版本号后，建议按照脚本输出的提示进行 Git 操作:
     ```bash
     git add .
     git commit -m "Bump version to x.y.z"
     git tag vx.y.z
     git push && git push --tags
     ```

## 注意事项

1. 运行脚本前请确保已激活项目的虚拟环境
2. 确保有足够的文件写入权限
3. 建议在版本控制系统中提交更改前运行此脚本
4. 发布到 PyPI 前请确保使用静态版本号而非动态生成的版本号
5. 脚本会自动更新所有相关文件中的版本号，无需手动修改