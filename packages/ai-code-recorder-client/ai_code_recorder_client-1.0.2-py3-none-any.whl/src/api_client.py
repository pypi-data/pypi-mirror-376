"""API 客户端"""

import requests
import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime


class APIClient:
    """远程API客户端"""
    
    def __init__(self, base_url: str = "http://10.111.200.14:9000"):
        self.base_url = base_url.rstrip('/')
    
    def record_code_snippet(self, code_data: Dict[str, Any]) -> Dict[str, Any]:
        """记录代码片段到远程服务器"""
        try:
            response = requests.post(
                f"{self.base_url}/api/code/record",
                json=code_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def prepare_code_data(
        self,
        filename: str,
        language: str,
        source: str,
        code: str,
        file_path: Optional[str] = None,
        project_context: Optional[str] = None,
        git_info: Optional[Dict[str, str]] = None,
        user_info: Optional[Dict[str, str]] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """准备要发送的代码数据"""
        
        # 计算统计信息
        lines_count = len(str(code).splitlines())
        characters_count = len(str(code))
        code_hash = hashlib.md5(str(code).encode()).hexdigest()[:16]
        
        # 构建元数据
        meta_data = {
            "git_info_provided": git_info or {},
            "user_info": user_info or {},
            "analysis_ready": True,
            "record_version": "7.0",
            "client_type": "uvx_client",
            "timestamp": datetime.now().isoformat(),
            **(meta or {})
        }
        
        return {
            "filename": str(filename),
            "language": str(language),
            "source": str(source),
            "code_content": str(code),
            "file_path": file_path or "",
            "project_context": project_context or "",
            "repository_url": git_info.get("remote_url", "") if git_info else "",
            "git_branch": git_info.get("current_branch", "") if git_info else "",
            "commit_hash": git_info.get("current_commit", "") if git_info else "",
            "user_name": user_info.get("git_name", "") if user_info else "",
            "user_email": user_info.get("git_email", "") if user_info else "",
            "code_lines": lines_count,
            "code_characters": characters_count,
            "code_hash": code_hash,
            "meta": meta_data
        }
