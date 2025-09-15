"""MCP 工具定义"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import Field
from typing import Annotated

from fastmcp import FastMCP, Context
from .git_utils import get_git_info, get_user_info
from .api_client import APIClient


# 创建FastMCP应用实例
mcp = FastMCP("AI代码记录器客户端")

# API客户端
api_client = APIClient()


@mcp.tool()
async def get_repository_info(
    ctx: Context,
    project_root: Annotated[str, Field(description="客户端项目的根目录绝对路径")],
    file_path: Annotated[str | None, Field(description="文件的相对或绝对路径")] = None,
) -> str:
    """获取Git仓库信息（客户端版本）"""
    try:
        await ctx.info(f"正在获取项目Git信息: {project_root}")
        
        # 直接从客户端本地获取Git信息
        git_info = get_git_info(project_root)
        user_info = get_user_info()
        
        if git_info.get("error"):
            await ctx.info(f"⚠️ {git_info['error']}")
            return json.dumps({
                "success": False,
                "error": git_info["error"],
                "suggestion": "请确保在Git仓库目录中执行"
            }, ensure_ascii=False)
        
        await ctx.info("✅ Git信息获取成功")
        
        return json.dumps({
            "success": True,
            "data": {
                "repository_info": {
                    "match_source": "client_local",
                    "git_root": git_info["git_root"],
                    "remote_url": git_info["remote_url"],
                    "current_branch": git_info["current_branch"],
                    "current_commit": git_info["current_commit"],
                    "project_root": project_root,
                    "file_path": file_path or ""
                },
                "user_info": user_info
            }
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        await ctx.info(f"❌ 获取Git信息失败: {str(e)}")
        return json.dumps({
            "success": False, 
            "error": f"获取Git仓库信息时发生错误: {str(e)}"
        }, ensure_ascii=False)


@mcp.tool()
async def create_agents_guide(
    ctx: Context,
    project_root: Annotated[str | None, Field(description="项目根目录绝对路径")] = None
) -> str:
    """创建AGENTS.md使用指南文件"""
    try:
        base_dir = Path(project_root) if project_root else Path.cwd()
        target = base_dir / "AGENTS.md"

        guide_section = """# ai-code-recorder 规则

## 基本原则
当 AI 生成/修改代码时，自动调用 ai-code-recorder 记录到数据库，用于后续采纳率分析。

## 两步执行流程
1. 获取 Git 信息：调用 `get_repository_info`
2. 记录代码：调用 `record_code_snippet`

## 触发场景（示例）
- 生成/重构/修复代码
- 新增配置或脚本
- 用户明确提出"生成代码/优化代码"等

## 注意
- 必填：filename/language/source/code
- source: cursor/copilot/chatgpt/claude/gemini/other
- 建议在生成后立即记录
"""

        if not target.exists():
            target.write_text(guide_section, encoding="utf-8")
            await ctx.info(f"✅ 创建 AGENTS.md: {target}")
            return json.dumps({"success": True, "action": "created", "file_path": str(target)}, ensure_ascii=False)

        # 已有文件则检查内容
        content = target.read_text(encoding="utf-8")
        heading = "# ai-code-recorder 规则"
        if heading in content:
            return json.dumps({"success": True, "action": "exists", "file_path": str(target)}, ensure_ascii=False)

        # 追加到文件末尾
        new_content = content.rstrip() + "\n\n" + guide_section
        target.write_text(new_content, encoding="utf-8")
        await ctx.info(f"✅ 更新 AGENTS.md: {target}")
        return json.dumps({"success": True, "action": "appended", "file_path": str(target)}, ensure_ascii=False)
        
    except Exception as e:
        await ctx.info(f"❌ 创建AGENTS.md失败: {e}")
        return json.dumps({"success": False, "error": f"创建失败: {e}"}, ensure_ascii=False)


@mcp.tool()
async def record_code_snippet(
    ctx: Context,
    filename: Annotated[str | None, Field(description="文件名，例如: main.py, index.html")] = None,
    language: Annotated[str | None, Field(description="编程语言，例如: python, javascript, html, css, go, java")] = None,
    source: Annotated[str | None, Field(description="AI代码来源: cursor/copilot/chatgpt/claude/gemini/other")] = None,
    code: Annotated[str | None, Field(description="AI生成的完整代码内容")] = None,
    file_path: Annotated[str | None, Field(description="文件在项目中的相对路径")] = None,
    project_context: Annotated[str | None, Field(description="项目上下文描述")] = None,
    repository_url: Annotated[str | None, Field(description="Git仓库URL")] = None,
    git_branch: Annotated[str | None, Field(description="Git分支名")] = None,
    commit_hash: Annotated[str | None, Field(description="Git Commit Hash")] = None,
    meta: Annotated[Dict[str, Any] | None, Field(description="额外的元数据信息")] = None,
) -> str:
    """记录AI生成的代码片段"""
    
    try:
        # 校验必填字段
        missing = []
        if not filename:
            missing.append("filename")
        if not language:
            missing.append("language")
        if not source:
            missing.append("source")
        if not code or not str(code).strip():
            missing.append("code")
        
        if missing:
            error_msg = f"缺少必填参数: {', '.join(missing)}"
            await ctx.info(f"❌ {error_msg}")
            return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)

        # 规范source值
        source_allowed = {"cursor", "copilot", "chatgpt", "claude", "gemini", "other"}
        if source not in source_allowed:
            source = "other"
        
        await ctx.info(f"开始记录代码片段: {filename}")
        
        # 获取用户信息和Git信息
        user_info = get_user_info()
        
        # 如果没有提供Git信息，尝试自动获取
        git_info = None
        if not repository_url:
            git_info = get_git_info()
            if not git_info.get("error"):
                repository_url = git_info.get("remote_url", "")
                git_branch = git_info.get("current_branch", "")
                commit_hash = git_info.get("current_commit", "")
        
        # 准备数据
        code_data = api_client.prepare_code_data(
            filename=filename,
            language=language,
            source=source,
            code=code,
            file_path=file_path,
            project_context=project_context,
            git_info={
                "remote_url": repository_url or "",
                "current_branch": git_branch or "",
                "current_commit": commit_hash or ""
            },
            user_info=user_info,
            meta=meta
        )
        
        # 上传到远程服务器
        await ctx.info("正在上传到远程服务器...")
        result = api_client.record_code_snippet(code_data)
        
        if not result["success"]:
            await ctx.info(f"❌ 上传失败: {result['error']}")
            return json.dumps({"success": False, "error": f"上传失败: {result['error']}"}, ensure_ascii=False)
        
        await ctx.info("✅ 代码片段记录成功")
        
        return json.dumps({
            "success": True,
            "message": f"代码片段已成功记录: {filename}",
            "data": result["data"]
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"记录代码片段失败: {str(e)}"
        await ctx.info(f"❌ {error_msg}")
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)
