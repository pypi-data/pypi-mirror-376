# MCP Minder PyPI 发布指南

本文档说明如何将 MCP Minder 发布到 PyPI。

## 📦 发布准备

### 1. 安装发布工具

```bash
# 安装构建工具
pip install build twine

# 或者使用 uv
uv add build twine
```

### 2. 检查项目配置

确保以下文件存在且配置正确：

- `pyproject.toml` - 项目配置
- `setup.py` - 安装脚本
- `requirements.txt` - 依赖列表
- `MANIFEST.in` - 包含文件配置
- `README.md` - 项目说明
- `LICENSE` - 许可证文件

### 3. 更新版本号

在 `pyproject.toml` 中更新版本号：

```toml
[project]
version = "0.1.0"  # 更新版本号
```

## 🚀 发布步骤

### 方法一：使用发布脚本（推荐）

```bash
# 发布到测试PyPI
python scripts/publish.py --test

# 发布到正式PyPI
python scripts/publish.py --prod

# 仅构建包，不上传
python scripts/publish.py --build-only
```

### 方法二：手动发布

#### 1. 清理构建文件

```bash
rm -rf build dist *.egg-info
```

#### 2. 构建包

```bash
python -m build
```

#### 3. 检查包

```bash
python -m twine check dist/*
```

#### 4. 发布到测试PyPI

```bash
python -m twine upload --repository testpypi dist/*
```

#### 5. 发布到正式PyPI

```bash
python -m twine upload dist/*
```

## 🧪 测试发布

### 从测试PyPI安装

```bash
pip install --index-url https://test.pypi.org/simple/ mcp-minder
```

### 从正式PyPI安装

```bash
pip install mcp-minder
```

### 测试客户端库

```bash
# 运行测试脚本
python test_client.py
```

## 📝 发布检查清单

- [ ] 版本号已更新
- [ ] 所有依赖已正确配置
- [ ] README.md 已更新
- [ ] 示例代码已测试
- [ ] 客户端库功能正常
- [ ] 构建无错误
- [ ] 包检查通过
- [ ] 测试PyPI安装成功
- [ ] 正式PyPI发布成功

## 🔧 故障排除

### 常见问题

1. **构建失败**
   - 检查 `pyproject.toml` 语法
   - 确保所有依赖可用
   - 检查 `MANIFEST.in` 配置

2. **上传失败**
   - 检查 PyPI 凭据
   - 确保版本号唯一
   - 检查网络连接

3. **安装失败**
   - 检查依赖版本兼容性
   - 确保 Python 版本支持
   - 检查包完整性

### 获取帮助

- 查看 [PyPI 文档](https://packaging.python.org/)
- 检查 [twine 文档](https://twine.readthedocs.io/)
- 查看项目 Issues

## 📋 版本管理

### 语义化版本

使用语义化版本号 (Semantic Versioning)：

- `MAJOR.MINOR.PATCH`
- 例如：`1.0.0`, `1.1.0`, `1.1.1`

### 版本类型

- **MAJOR**: 不兼容的API更改
- **MINOR**: 向后兼容的功能添加
- **PATCH**: 向后兼容的错误修复

### 更新版本

```bash
# 更新版本号
sed -i 's/version = "0.1.0"/version = "0.1.1"/' pyproject.toml

# 提交更改
git add pyproject.toml
git commit -m "Bump version to 0.1.1"
git tag v0.1.1
git push origin v0.1.1
```

## 🎯 发布后任务

1. **更新文档**
   - 更新 README.md
   - 更新示例代码
   - 更新 API 文档

2. **通知用户**
   - 发布 Release Notes
   - 更新 Changelog
   - 发送通知邮件

3. **监控反馈**
   - 关注 Issues
   - 收集用户反馈
   - 修复报告的问题

## 📚 相关资源

- [PyPI 发布指南](https://packaging.python.org/tutorials/packaging-projects/)
- [Python 包开发指南](https://packaging.python.org/guides/distributing-packages-using-setuptools/)
- [语义化版本规范](https://semver.org/)
- [MCP Minder 项目](https://github.com/your-org/mcp-minder)
