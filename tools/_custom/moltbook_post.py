#!/usr/bin/env python3
"""
Moltbook 发帖工具
"""

import requests
import json
from datetime import datetime
from typing import Optional

def get_api_key():
    """获取Moltbook API Key"""
    import os
    from pathlib import Path
    
    # 首先检查环境变量
    api_key = os.environ.get('MOLTBOOK_API_KEY')
    if api_key:
        return api_key
    
    # 检查本地配置文件
    config_path = Path.home() / '.config' / 'moltbook' / 'credentials.json'
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
                return config.get('api_key', '')
        except:
            pass
    
    # 返回默认值（临时方案）
    return "moltbook_sk_eizKbYzmnyaSYRzsIG2ashWEE8WcuulM"

class MoltbookPoster:
    def __init__(self):
        self.base_url = "https://www.moltbook.com/api/v1"
        self.api_key = get_api_key()
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def create_post(self, title: str, content: str = "", url: str = "", submolt: str = "general"):
        """
        创建帖子
        
        Args:
            title: 帖子标题
            content: 帖子内容（文字帖子时使用）
            url: 链接（链接帖子时使用）
            submolt: 社区名称，默认general
        """
        try:
            print(f"🔍 尝试发帖: {title}")
            print(f"🔑 使用API Key: {self.api_key[:20]}...")
            print(f"📡 请求URL: {self.base_url}/posts")
            
            data = {
                'submolt': submolt,
                'title': title
            }
            
            if url:
                data['url'] = url
            elif content:
                data['content'] = content
            
            print(f"📊 发送数据: {json.dumps(data, indent=2)}")
            
            response = requests.post(
                f"{self.base_url}/posts",
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            print(f"📊 响应状态码: {response.status_code}")
            print(f"📄 响应内容: {response.text[:500]}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "success": True,
                    "post": result,
                    "message": f"✅ 发帖成功！"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "message": response.text[:200]
                }
                
        except Exception as e:
            print(f"❌ 异常: {str(e)}")
            return {
                "success": False,
                "error": "exception",
                "message": str(e)[:200]
            }
    
    def delete_post(self, post_id: str):
        """删除自己的帖子"""
        try:
            response = requests.delete(
                f"{self.base_url}/posts/{post_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                return {
                    "success": True,
                    "message": "✅ 删除成功"
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

def run(title: str, content: str = "", url: str = "", submolt: str = "general"):
    """
    在Moltbook发帖
    
    Args:
        title: 帖子标题（必填）
        content: 帖子内容（文字帖子）
        url: 链接（链接帖子）
        submolt: 社区名称（默认general）
    
    Returns:
        发帖结果
    """
    poster = MoltbookPoster()
    result = poster.create_post(title, content, url, submolt)
    
    if result['success']:
        post = result['post']
        output = f"🍌 发帖成功！\n"
        output += f"📝 标题: {title}\n"
        if content:
            content_preview = content[:100] + "..." if len(content) > 100 else content
            output += f"📄 内容: {content_preview}\n"
        if url:
            output += f"🔗 链接: {url}\n"
        output += f"🏷️ 社区: {submolt}\n"
        output += f"🆔 帖子ID: {post.get('id', 'N/A')}\n"
        return output
    else:
        return f"❌ 发帖失败: {result['message']}"

if __name__ == "__main__":
    # 测试发帖
    result = run(
        title="Hello Moltbook!",
        content="我的第一个Moltbook帖子！",
        submolt="general"
    )
    print(result)