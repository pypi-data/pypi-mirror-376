# AI代码记录器客户端

AI代码记录器的客户端，运行在本地，获取Git信息并与远程服务器通信。

## 一、快速开始

### 1. 安装客户端

**从 PyPI 安装（推荐）：**

```bash
# 直接安装发布版本
pip install ai-code-recorder-client
```

**从源码安装（开发用）：**

```bash
# 克隆仓库并进入客户端目录
git clone <repository-url>
cd ai-code-recorder/client

# 安装开发版本
pip install -e .
```

### 2. 配置 Cursor

编辑 `~/.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "ai-code-recorder": {
      "command": "uvx",
      "args": ["ai-code-recorder-client"]
    }
  }
}
```

### 3. 使用

1. 重启 Cursor
2. 在 Cursor 中输入：`ai-code-recorder init`
3. 开始使用 AI 生成代码，会自动记录

## 二、开发和发布

### 1. 本地开发

如果要参与开发或使用最新功能：

```bash
# 克隆仓库并进入客户端目录
git clone <repository-url>
cd ai-code-recorder/client

# 安装开发依赖
pip install -e .
```

### 2. 发布到 PyPI

#### 发布前准备

1. **安装必要工具**
```bash
pip install build twine
```

2. **配置 PyPI API Token**
- 访问 [PyPI Token 管理页面](https://pypi.org/manage/account/token/)
- 创建新的 API token，作用域选择 "Entire account" 或特定项目
- 设置环境变量：
```bash
export PYPI_API_TOKEN="pypi-your-token-here"
```

#### 一键发布

```bash
# 在客户端目录中执行
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

#### 发布后验证

访问 PyPI 页面确认：https://pypi.org/project/ai-code-recorder-client/