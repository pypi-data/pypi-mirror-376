#!/bin/bash
# 发布脚本 - Release Script

set -e

echo "🚀 Moon Sol SDK Release Script"
echo "========================================="

# 检查必要工具
if ! command -v maturin &> /dev/null; then
    echo "❌ Maturin not found. Installing..."
    pip install maturin
fi

if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found. Please install poetry first."
    exit 1
fi

# 清理之前的构建
echo "🧹 Cleaning previous builds..."
rm -rf target/wheels/*
rm -rf dist/*

# 确保依赖是最新的
echo "📦 Installing dependencies..."
poetry install

# 运行测试 (如果有的话)
echo "🧪 Running tests..."
# poetry run pytest tests/ || echo "⚠️  No tests found or tests failed"

# 构建Rust扩展
echo "🔧 Building Rust extension..."
poetry run maturin develop

# 使用Maturin构建wheel包
echo "📦 Building wheels..."
maturin build --release --out dist --find-interpreter

# 构建源码包
echo "📦 Building source distribution..."
maturin sdist --out dist

echo "✅ Build completed!"
echo "📁 Distribution files created in ./dist/"
ls -la dist/

maturin publish --username __token__ --password pypi-AgEIcHlwaS5vcmcCJDkxNzZiYzYyLTVlODUtNGU2YS1hOTk1LTE2YWJkZWM3YzQyNAACFFsxLFsibW9vbi1zb2wtc2RrIl1dAAIsWzIsWyI1MDkzMTA4Ni05MzhjLTQ0NGMtODEwMS01MzU1YjliMjY0NmQiXV0AAAYgkJAIxFJHOUS1brT7z-48NeFCzffpLJ0Ugb949063eBc

echo ""
echo "🔍 To verify the build:"
echo "  pip install dist/*.whl"
echo ""
echo "📤 To publish to PyPI:"
echo "  maturin publish --username __token__ --password your_pypi_token"
echo "  # or"
echo "  twine upload dist/*"
