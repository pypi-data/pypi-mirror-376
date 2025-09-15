"""AI代码记录器客户端主入口"""

import sys
from .mcp_tools import mcp


def main():
    """主函数 - uvx 入口点"""
    # 强制使用stdio模式
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
