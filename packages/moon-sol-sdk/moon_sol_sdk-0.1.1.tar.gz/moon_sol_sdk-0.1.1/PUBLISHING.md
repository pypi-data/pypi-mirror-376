# 发布指南 - Publishing Guide

这是Moon Sol SDK的完整发布指南，包含本地测试、构建和发布到PyPI的所有步骤。

## 🚀 快速发布流程

### 1. 准备工作

确保你有以下工具：
```bash
# 安装Poetry (如果尚未安装)
curl -sSL https://install.python-poetry.org | python3 -

# 安装Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 安装发布工具
pip install maturin twine
```

### 2. 本地构建和测试

```bash
# 克隆项目
git clone <your-repo-url>
cd moon_sol_sdk

# 安装依赖
poetry install

# 构建开发版本
poetry run maturin develop

# 测试包导入
poetry run python -c "import moon_sol_sdk; print('✅ Import successful!')"

# 运行示例
poetry run python examples/complete_example.py
```

### 3. 构建发布包

```bash
# 使用发布脚本（推荐）
./release.sh

# 或手动构建
maturin build --release --out dist --find-interpreter
maturin sdist --out dist
```

### 4. 验证构建

```bash
# 检查构建的文件
ls -la dist/

# 在新环境中测试安装
python -m venv test_env
source test_env/bin/activate
pip install dist/*.whl
python -c "import moon_sol_sdk; print('✅ Wheel installation successful!')"
deactivate
rm -rf test_env
```

## 📤 发布到PyPI

### 方法1: 使用Maturin (推荐)

```bash
# 发布到测试PyPI
maturin publish --repository testpypi --username __token__ --password YOUR_TEST_PYPI_TOKEN

# 发布到正式PyPI
maturin publish --username __token__ --password YOUR_PYPI_TOKEN
```

### 方法2: 使用Twine

```bash
# 发布到测试PyPI
twine upload --repository testpypi dist/* --username __token__ --password YOUR_TEST_PYPI_TOKEN

# 发布到正式PyPI
twine upload dist/* --username __token__ --password YOUR_PYPI_TOKEN
```

## 🔧 环境变量配置

创建 `.env` 文件（不要提交到git）：
```bash
# PyPI tokens
PYPI_TOKEN=pypi-your-actual-token-here
TEST_PYPI_TOKEN=pypi-your-test-token-here

# 或设置环境变量
export MATURIN_PYPI_TOKEN=your-pypi-token
export MATURIN_REPOSITORY=https://upload.pypi.org/legacy/
```

## 📋 发布前检查清单

- [ ] 更新版本号 (`pyproject.toml` 和 `Cargo.toml`)
- [ ] 更新 `CHANGELOG.md`
- [ ] 运行所有测试
- [ ] 检查文档是否最新
- [ ] 构建并测试wheel包
- [ ] 在测试PyPI上发布并验证
- [ ] 创建Git标签
- [ ] 发布到正式PyPI

## 🏷️ 版本管理

### 更新版本号

1. **更新 pyproject.toml**:
```toml
[tool.poetry]
version = "0.2.0"
```

2. **更新 Cargo.toml**:
```toml
[package]
version = "0.2.0"
```

3. **创建Git标签**:
```bash
git add .
git commit -m "Release v0.2.0"
git tag v0.2.0
git push origin v0.2.0
```

## 🤖 自动化发布 (GitHub Actions)

项目已配置GitHub Actions工作流：

1. **推送到main分支** - 自动测试和构建
2. **创建Release** - 自动发布到PyPI

设置GitHub Secrets：
- `PYPI_TOKEN`: 你的PyPI API token

## 🐛 常见问题解决

### 构建错误

1. **Missing patchelf**:
```bash
pip install maturin[patchelf]
```

2. **Rust编译错误**:
```bash
rustup update
cargo clean
```

3. **Python版本问题**:
```bash
# 确保使用正确的Python版本
pyenv install 3.11.5
pyenv local 3.11.5
```

### 发布错误

1. **权限错误**:
   - 检查PyPI token是否正确
   - 确保包名没有被占用

2. **文件已存在**:
   - 更新版本号
   - 删除已上传的版本（如果在测试环境）

## 📚 其他资源

- [Maturin用户指南](https://maturin.rs/)
- [PyPI发布指南](https://packaging.python.org/tutorials/packaging-projects/)
- [Poetry文档](https://python-poetry.org/docs/)
- [Rust Cargo文档](https://doc.rust-lang.org/cargo/)

## 📞 获取帮助

如果遇到问题：
1. 查看GitHub Issues
2. 查阅相关工具文档
3. 在项目仓库创建Issue
