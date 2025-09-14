# PyPI 发布指南

## 📋 发布前准备

### 1. 安装必要工具

```bash
pip install build twine
```

### 2. 配置 PyPI API Token

1. 访问 [PyPI Token 管理页面](https://pypi.org/manage/account/token/)
2. 创建新的 API token，作用域选择 "Entire account" 或特定项目
3. 设置环境变量：

```bash
export PYPI_API_TOKEN="pypi-your-token-here"
```

## 🚀 一键发布（推荐）

```bash
cd /Users/liuhe/workspace/learning/ai-code-recorder/client
./release.sh
```

脚本会自动执行所有发布步骤：
- ✅ 清理旧构建文件
- ✅ 运行测试
- ✅ 构建包文件
- ✅ 检查包质量
- ✅ 测试本地安装
- ✅ 询问是否发布到 PyPI
- ✅ 自动发布（如果选择是）

## 🔍 发布后验证

访问 PyPI 页面确认：https://pypi.org/project/ai-code-recorder-client/

## 📦 包信息

- **包名**: `ai-code-recorder-client`
- **当前版本**: 1.0.0
- **Python 支持**: >= 3.8
- **依赖**: fastmcp, requests

就这么简单！🎉
