# AI代码记录器客户端

AI代码记录器的客户端，运行在本地，获取Git信息并与远程服务器通信。

## 快速开始

### 1. 安装客户端

```bash
# 进入客户端目录
cd /Users/liuhe/workspace/learning/ai-code-recorder/client

# 安装
pip install -e .
```

### 2. 配置 Cursor

编辑 `~/.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "ai-code-recorder": {
      "command": "uvx",
      "args": ["--from", "/Users/liuhe/workspace/learning/ai-code-recorder/client", "ai-code-recorder-client"]
    }
  }
}
```

### 3. 使用

1. 重启 Cursor
2. 在 Cursor 中输入：`ai-code-recorder init`
3. 开始使用 AI 生成代码，会自动记录

## 故障排除

- **uvx 未找到**：运行 `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **连接失败**：检查服务器是否在 `http://10.111.200.14:9000` 运行
- **Git 错误**：确保在 Git 仓库目录中使用

就这么简单！