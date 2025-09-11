# Makefile for appcan-helper-mcp

# 默认目标
.PHONY: help
help:
	@echo "AppCan Helper MCP 开发辅助命令"
	@echo ""
	@echo "可用命令:"
	@echo "  install     - 安装开发版本"
	@echo "  build       - 构建包"
	@echo "  test        - 运行测试"
	@echo "  version     - 显示当前版本"
	@echo "  bump-major  - 主版本号升级 (x.y.z -> (x+1).0.0)"
	@echo "  bump-minor  - 次版本号升级 (x.y.z -> x.(y+1).0)"
	@echo "  bump-patch  - 修订版本号升级 (x.y.z -> x.y.(z+1))"
	@echo "  clean       - 清理构建文件"

# 安装开发版本
.PHONY: install
install:
	uv pip install -e .

# 构建包
.PHONY: build
build:
	uv build

# 运行测试
.PHONY: test
test:
	python test/test_client.py

# 显示当前版本
.PHONY: version
version:
	@python -c "import src.appcan_helper_mcp; print(src.appcan_helper_mcp.__version__)"

# 主版本号升级
.PHONY: bump-major
bump-major:
	@python -c "import src.appcan_helper_mcp; v=src.appcan_helper_mcp.__version__; x,y,z=v.split('.'); nv=f'{int(x)+1}.0.0'; __import__('subprocess').run(['python', 'scripts/update_version.py', nv])"

# 次版本号升级
.PHONY: bump-minor
bump-minor:
	@python -c "import src.appcan_helper_mcp; v=src.appcan_helper_mcp.__version__; x,y,z=v.split('.'); nv=f'{x}.{int(y)+1}.0'; __import__('subprocess').run(['python', 'scripts/update_version.py', nv])"

# 修订版本号升级
.PHONY: bump-patch
bump-patch:
	@python -c "import src.appcan_helper_mcp; v=src.appcan_helper_mcp.__version__; x,y,z=v.split('.'); nv=f'{x}.{y}.{int(z)+1}'; __import__('subprocess').run(['python', 'scripts/update_version.py', nv])"

# 清理构建文件
.PHONY: clean
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete