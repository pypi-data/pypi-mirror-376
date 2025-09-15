"""Git 信息获取工具"""

import subprocess
import os
from pathlib import Path
from typing import Dict, Optional


def get_user_info() -> Dict[str, str]:
    """获取用户信息"""
    try:
        # 获取Git用户信息
        git_name = ""
        git_email = ""
        
        try:
            result = subprocess.run(
                ["git", "config", "user.name"],
                capture_output=True, text=True, check=True
            )
            git_name = result.stdout.strip()
        except:
            pass
            
        try:
            result = subprocess.run(
                ["git", "config", "user.email"],
                capture_output=True, text=True, check=True
            )
            git_email = result.stdout.strip()
        except:
            pass
        
        # 获取系统用户名
        system_user = os.getenv("USER") or os.getenv("USERNAME") or "unknown"
        
        return {
            "git_name": git_name,
            "git_email": git_email,
            "system_user": system_user,
            "display_name": git_name or system_user,
            "primary_email": git_email
        }
    except Exception:
        return {
            "git_name": "",
            "git_email": "",
            "system_user": "unknown",
            "display_name": "unknown",
            "primary_email": ""
        }


def find_git_root(start_path: Optional[str] = None) -> Optional[Path]:
    """查找Git仓库根目录"""
    if start_path:
        current_dir = Path(start_path).resolve()
    else:
        current_dir = Path.cwd()
    
    # 如果是文件，从其父目录开始查找
    if current_dir.is_file():
        current_dir = current_dir.parent
    
    # 向上查找.git目录
    while current_dir != current_dir.parent:
        git_dir = current_dir / ".git"
        if git_dir.exists():
            return current_dir
        current_dir = current_dir.parent
    
    return None


def get_git_info(project_root: Optional[str] = None) -> Dict[str, str]:
    """获取Git仓库信息"""
    git_root = find_git_root(project_root)
    
    if not git_root:
        return {
            "error": "未找到Git仓库",
            "git_root": "",
            "remote_url": "",
            "current_branch": "",
            "current_commit": ""
        }
    
    repo_info = {"git_root": str(git_root)}
    
    try:
        # 获取远程URL
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=git_root, capture_output=True, text=True, check=True
        )
        repo_info["remote_url"] = result.stdout.strip()
    except Exception:
        repo_info["remote_url"] = ""
    
    try:
        # 获取当前分支
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=git_root, capture_output=True, text=True, check=True
        )
        repo_info["current_branch"] = result.stdout.strip()
    except Exception:
        repo_info["current_branch"] = ""
    
    try:
        # 获取当前commit
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=git_root, capture_output=True, text=True, check=True
        )
        repo_info["current_commit"] = result.stdout.strip()
    except Exception:
        repo_info["current_commit"] = ""
    
    return repo_info
