#!/usr/bin/env python3
"""
Moltbook 真实API调用工具 - Feed获取
"""

import requests
import json
from datetime import datetime
from typing import List, Optional

# 从环境变量或文件获取API Key
def get_api_key():
    """获取Moltbook API Key"""
    import os
    from pathlib import Path
    
    # 检查环境变量
    api_key = os.environ.get('MOLTBOOK_API_KEY')
    if api_key:
        return api_key
    
    # 检查配置文件
    config_path = Path.home() / '.config' / 'moltbook' / 'credentials.json'
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
                return config.get('api_key', '')
        except:
            pass
    
    # 默认使用已知的工作API Key
    return 'moltbook_sk_eizKbYzmnyaSYRzsIG2ashWEE8WcuulM'

class MoltbookFeed:
    def __init__(self):
        self.base_url = "https://www.moltbook.com/api/v1"
        self.api_key = get_api_key()
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_feed(self, sort: str = "hot", limit: int = 25, submolt: str = None):
        """
        获取Feed内容
        """
        try:
            params = {'sort': sort, 'limit': limit}
            if submolt:
                params['submolt'] = submolt
            
            response = requests.get(
                f"{self.base_url}/posts",
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # 正确提取posts
                if isinstance(data, dict):
                    if data.get('success') and 'posts' in data:
                        posts = data['posts']
                    else:
                        posts = data.get('posts', [])
                else:
                    posts = data if isinstance(data, list) else []
                
                return {
                    "success": True,
                    "posts": posts,
                    "count": len(posts),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "message": response.text[:200]
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "timeout",
                "message": "API请求超时"
            }
        except Exception as e:
            return {
                "success": False,
                "error": "exception",
                "message": str(e)[:200]
            }
    
    def get_personalized_feed(self, limit: int = 25):
        """
        获取个性化Feed
        """
        try:
            response = requests.get(
                f"{self.base_url}/feed",
                headers=self.headers,
                params={'sort': 'hot', 'limit': limit},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # 正确提取posts
                if isinstance(data, dict):
                    if data.get('success') and 'posts' in data:
                        posts = data['posts']
                    else:
                        posts = data.get('posts', [])
                else:
                    posts = data if isinstance(data, list) else []
                
                return {
                    "success": True,
                    "posts": posts,
                    "count": len(posts),
                    "timestamp": datetime.now().isoformat()
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

def run(sort: str = "hot", limit: int = 25, personalized: bool = False):
    """
    获取Moltbook Feed
    
    Args:
        sort: 排序方式 - hot(热门), new(最新), top(最赞), rising(上升)
        limit: 返回数量 - 默认25条
        personalized: 是否获取个性化订阅流
    
    Returns:
        格式化的Feed数据
    """
    feed = MoltbookFeed()
    
    if personalized:
        result = feed.get_personalized_feed(limit)
    else:
        result = feed.get_feed(sort, limit)
    
    if not result['success']:
        return f"❌ 获取Feed失败: {result.get('message', '未知错误')}"
    
    posts = result.get('posts', [])
    
    if not posts:
        return "📭 Feed为空或没有内容"
    
    # 格式化输出
    output = f"🍌 Moltbook Feed ({result['timestamp'][:19]})\n"
    output += f"📊 获取到 {len(posts)} 条帖子\n"
    output += f"🔽 排序: {sort}\n"
    output += "="*50 + "\n\n"
    
    for i, post in enumerate(posts, 1):
        # 安全处理author字段 - 可能是字符串或字典
        author = post.get('author', {})
        if isinstance(author, str):
            author_name = author
        elif isinstance(author, dict):
            author_name = author.get('name', author.get('username', 'Unknown'))
        else:
            author_name = 'Unknown'
        
        # 获取帖子内容
        title = post.get('title', '')
        content = post.get('content', '')
        url = post.get('url', '')
        
        # 确定帖子类型
        post_type = "🔗 链接" if url else "📝 文字"
        
        output += f"{i}. {post_type} **{author_name}**\n"
        output += f"   ❤️ {post.get('upvotes', 0)} | 💬 {post.get('comment_count', 0)}\n"
        
        # 添加标题（如果有）
        if title:
            title_preview = title[:60] + "..." if len(title) > 60 else title
            output += f"   📋 {title_preview}\n"
        
        # 添加内容预览
        if content:
            content_preview = content[:100] + "..." if len(content) > 100 else content
            output += f"   📝 {content_preview}\n"
        elif url:
            output += f"   🔗 {url}\n"
        
        output += f"   🆔 ID: {post.get('id', 'N/A')}\n\n"
    
    return output

if __name__ == "__main__":
    result = run(sort="hot", limit=10)
    print(result)