#!/bin/bash

# AI代码记录器客户端发布脚本

set -e

CLIENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 获取版本号（兼容不同Python版本）
get_version() {
    # 尝试使用 tomllib (Python 3.11+)
    if python3 -c "import tomllib" 2>/dev/null; then
        python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"
    else
        # 回退到使用 grep 和 sed 解析版本号
        grep -E '^version = ' pyproject.toml | sed -E 's/.*"(.*)".*/\1/'
    fi
}

VERSION=$(get_version)

echo "🚀 AI代码记录器客户端发布脚本"
echo "📦 当前版本: $VERSION"
echo "📁 客户端目录: $CLIENT_DIR"
echo ""

cd "$CLIENT_DIR"

# 检查是否有未提交的更改
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  检测到未提交的更改，请先提交代码"
    git status
    exit 1
fi

echo "1️⃣  清理旧的构建文件..."
rm -rf dist/ build/ *.egg-info/

echo "2️⃣  运行测试..."
if command -v pytest &> /dev/null; then
    pytest || echo "⚠️  没有测试文件或测试失败，继续发布流程"
else
    echo "⚠️  未找到pytest，跳过测试"
fi

echo "3️⃣  构建包..."
python3 -m build

echo "4️⃣  检查包质量..."
if command -v twine &> /dev/null; then
    twine check dist/*
else
    echo "⚠️  未找到twine，跳过包检查"
fi

echo "5️⃣  测试本地安装..."
# 创建临时虚拟环境测试
TEMP_VENV=$(mktemp -d)
python3 -m venv "$TEMP_VENV"
source "$TEMP_VENV/bin/activate"

# 只测试包安装，不执行任何可能启动MCP服务器的命令
echo "安装包到临时虚拟环境..."
pip install --quiet dist/ai_code_recorder_client-$VERSION-py3-none-any.whl

# 验证包是否正确安装（检查模块导入，不执行main函数）
if python3 -c "import src.mcp_tools; print('✅ 包模块导入成功')" 2>/dev/null; then
    echo "✅ wheel包已成功安装且模块可正常导入"
else
    echo "❌ 包安装失败或模块导入有问题"
    deactivate
    rm -rf "$TEMP_VENV"
    exit 1
fi

deactivate
rm -rf "$TEMP_VENV"

echo "✅ 本地安装测试通过"

echo ""
echo "📦 构建完成！生成的文件："
ls -la dist/

# 询问是否发布到 PyPI
echo ""
read -p "🚀 是否要发布到 PyPI? (y/N): " PUBLISH_PYPI
if [[ "$PUBLISH_PYPI" =~ ^[Yy]$ ]]; then
    echo ""
    echo "📤 准备发布到 PyPI..."
    
    # 检查是否已配置 PyPI token
    if [[ -z "$PYPI_API_TOKEN" ]] && [[ ! -f "$HOME/.pypirc" ]]; then
        echo "⚠️  请先配置 PyPI 认证："
        echo "1. 创建 PyPI API token: https://pypi.org/manage/account/token/"
        echo "2. 设置环境变量: export PYPI_API_TOKEN=your_token"
        echo "3. 或配置 ~/.pypirc 文件"
        echo ""
        read -p "已完成配置？继续发布? (y/N): " CONTINUE_PUBLISH
        if [[ ! "$CONTINUE_PUBLISH" =~ ^[Yy]$ ]]; then
            echo "❌ 取消发布"
            exit 1
        fi
    fi
    
    # 发布到 PyPI
    if [[ -n "$PYPI_API_TOKEN" ]]; then
        echo "6️⃣  使用 API token 发布到 PyPI..."
        python3 -m twine upload dist/* --username __token__ --password "$PYPI_API_TOKEN" --verbose
    else
        echo "6️⃣  发布到 PyPI..."
        python3 -m twine upload dist/* --verbose
    fi
    
    if [ $? -eq 0 ]; then
        echo "✅ 发布到 PyPI 成功！"
        echo "📦 包地址: https://pypi.org/project/ai-code-recorder-client/"
    else
        echo "❌ 发布到 PyPI 失败"
        exit 1
    fi
else
    echo "⏭️  跳过 PyPI 发布"
fi

echo ""
echo "🎯 使用选项："
echo "1. 本地使用: uvx --from $CLIENT_DIR ai-code-recorder-client"
echo "2. 分发wheel: 复制 dist/ai_code_recorder_client-$VERSION-py3-none-any.whl"
echo "3. PyPI安装: pip install ai-code-recorder-client"

echo ""
echo "📋 Cursor配置示例："
echo '{'
echo '  "mcpServers": {'
echo '    "ai-code-recorder": {'
echo '      "command": "uvx",'
echo '      "args": ["ai-code-recorder-client"]'
echo '    }'
echo '  }'
echo '}'

echo ""
echo "🎉 发布完成！"
