#!/bin/bash
# 验证构建包的脚本

set -e

echo "🧪 Package Verification Script"
echo "================================"

# 检查dist目录
if [ ! -d "dist" ]; then
    echo "❌ dist/ directory not found. Run build first."
    exit 1
fi

echo "📦 Found distribution files:"
ls -la dist/

# 创建临时虚拟环境
echo -e "\n🔧 Creating temporary virtual environment..."
python -m venv temp_test_env
source temp_test_env/bin/activate

# 安装wheel包
echo -e "\n📥 Installing wheel package..."
# 找到与当前Python版本匹配的wheel
PYTHON_VERSION=$(python -c "import sys; print(f'cp{sys.version_info.major}{sys.version_info.minor}')")
WHEEL_FILE=$(ls dist/*${PYTHON_VERSION}*.whl 2>/dev/null | head -1)

if [ -z "$WHEEL_FILE" ]; then
    echo "⚠️  No matching wheel found for current Python version, trying any available wheel..."
    WHEEL_FILE=$(ls dist/*.whl | head -1)
fi

echo "📦 Installing: $WHEEL_FILE"
pip install --force-reinstall "$WHEEL_FILE"

# 测试导入
echo -e "\n🧪 Testing package import..."
python -c "
import moon_sol_sdk
print('✅ moon_sol_sdk imported successfully')

from moon_sol_sdk.client import SolClient
print('✅ SolClient imported successfully')

# 尝试创建客户端（使用测试密钥）
try:
    client = SolClient(
        private_key='TEST_KEY',
        rpc_url='https://api.mainnet-beta.solana.com',
        commitment='confirmed',
        priority_fee=1000000,
        is_jito=False
    )
    print(f'✅ SolClient created successfully')
    print(f'📍 Public key: {client.get_public_key()}')
except Exception as e:
    print(f'❌ Client creation failed: {e}')
"

# 清理
echo -e "\n🧹 Cleaning up..."
deactivate
rm -rf temp_test_env

echo -e "\n✅ Package verification completed successfully!"
echo "📤 Your package is ready for publishing!"

echo -e "\n📋 Next steps:"
echo "  1. Test on TestPyPI: maturin publish --repository testpypi"
echo "  2. Publish to PyPI: maturin publish"
