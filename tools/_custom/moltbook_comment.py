
#!/usr/bin/env python3
"""
Moltbook 评论工具
"""

import requests
import json
from datetime import datetime

def get_api_key():
    """获取Moltbook API Key"""
    import os
    from pathlib import Path
    
    api_key = os.environ.get('MOLTBOOK_API_KEY')
    if api_key:
        return api_key
    
    config_path = Path.home() / '.config' / 'moltbook' / 'credentials.json'
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
                return config.get('api_key', '')
        except:
            pass
    
    return ''

class MoltbookCommenter:
    def __init__(self):
        self.base_url = "https://www.moltbook.com/api/v1"
        self.api_key = get_api_key()
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def add_comment(self, post_id: str, content: str, parent_id: str = None):
        """
        添加评论
        
        Args:
            post_id: 帖子ID
            content: 评论内容
            parent_id: 父评论ID（用于回复评论）
        """
        try:
            data = {'content': content}
            if parent_id:
                data['parent_id'] = parent_id
            
            response = requests.post(
                f"{self.base_url}/posts/{post_id}/comments",
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "success": True,
                    "comment": result,
                    "message": "✅ 评论成功"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "message": response.text[:200]
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": "exception",
                "message": str(e)[:200]
            }
    
    def get_comments(self, post_id: str, sort: str = "top"):
        """获取帖子评论"""
        try:
            response = requests.get(
                f"{self.base_url}/posts/{post_id}/comments",
                headers=self.headers,
                params={'sort': sort},
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "comments": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "message": response.text[:200]
                }
        except Exception as e:
            return {
                "success": False,
                "error": "exception",
                "message": str(e)[:200]
            }

def run(post_id: str, content: str, parent_id: str = None):
    """
    评论/回复 Moltbook 帖子
    
    Args:
        post_id: 帖子ID
        content: 评论内容
        parent_id: 父评论ID（回复评论时使用）
    
    Returns:
        评论结果
    """
    commenter = MoltbookCommenter()
    result = commenter.add_comment(post_id, content, parent_id)
    
    if result['success']:
        comment = result.get('comment', {})
        output = f"💬 评论成功！\n"
        output += f"📝 内容: {content}\n"
        output += f"🆔 帖子ID: {post_id}\n"
        if parent_id:
            output += f"↩️ 回复评论ID: {parent_id}\n"
        output += f"🆔 评论ID: {comment.get('id', 'N/A')}\n"
        return output
    else:
        return f"❌ 评论失败: {result['message']}"

if __name__ == "__main__":
    # 测试评论
    result = run(
        post_id="test_post_id",
        content="这是一个测试评论"
    )
    print(result)
