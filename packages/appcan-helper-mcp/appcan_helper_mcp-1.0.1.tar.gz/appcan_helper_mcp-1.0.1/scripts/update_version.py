#!/usr/bin/env python3
"""
版本号更新脚本
使用方法: python scripts/update_version.py <new_version>
"""

import re
import sys
import json
from pathlib import Path

def update_pyproject_toml(version):
    """更新 pyproject.toml 中的版本号"""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text(encoding="utf-8")
    
    # 更新静态版本号
    content = re.sub(
        r'version = ".*"',
        f'version = "{version}"',
        content
    )
    
    pyproject_path.write_text(content, encoding="utf-8")
    print(f"✓ 更新 pyproject.toml 版本号为 {version}")

def update_init_py(version):
    """更新 __init__.py 中的版本号"""
    init_path = Path("src/appcan_helper_mcp/__init__.py")
    content = init_path.read_text(encoding="utf-8")
    
    # 更新版本号
    content = re.sub(
        r'__version__ = ".*"',
        f'__version__ = "{version}"',
        content
    )
    
    init_path.write_text(content, encoding="utf-8")
    print(f"✓ 更新 __init__.py 版本号为 {version}")

def update_manifest_json(version):
    """更新 manifest.json 中的版本号"""
    manifest_path = Path("manifest.json")
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    
    # 更新版本号
    manifest_data["version"] = version
    
    manifest_path.write_text(
        json.dumps(manifest_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✓ 更新 manifest.json 版本号为 {version}")

def main():
    if len(sys.argv) != 2:
        print("使用方法: python scripts/update_version.py <new_version>")
        sys.exit(1)
    
    new_version = sys.argv[1]
    
    # 验证版本号格式
    if not re.match(r'^\d+\.\d+\.\d+(?:[-+][\w.-]+)?$', new_version):
        print(f"错误: 版本号格式不正确 ({new_version})")
        sys.exit(1)
    
    print(f"正在更新版本号为: {new_version}")
    
    try:
        update_pyproject_toml(new_version)
        update_init_py(new_version)
        update_manifest_json(new_version)
        
        print(f"\n🎉 版本号已成功更新为 {new_version}")
        print("\n下一步建议:")
        print("1. 提交更改: git add . && git commit -m 'version: Bump version to {}'".format(new_version))
        print("2. 创建标签: git tag v{}".format(new_version))
        print("3. 推送更改: git push && git push --tags")
        
    except Exception as e:
        print(f"更新版本号时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()