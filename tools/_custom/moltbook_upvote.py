#!/usr/bin/env python3
"""
Moltbook 投票工具 - 点赞/踩帖子和评论
"""

import requests
import os
from pathlib import Path


def get_api_key():
    """获取Moltbook API Key"""
    api_key = os.environ.get('MOLTBOOK_API_KEY')
    if api_key:
        return api_key
    
    config_path = Path.home() / '.config' / 'moltbook' / 'credentials.json'
    if config_path.exists():
        try:
            import json
            with open(config_path) as f:
                config = json.load(f)
                return config.get('api_key', '')
        except:
            pass
    
    return ''


def run(post_id: str = None, comment_id: str = None, action: str = "upvote") -> str:
    """
    点赞/踩 Moltbook 帖子或评论
    
    Args:
        post_id: 帖子ID（点赞帖子时使用）
        comment_id: 评论ID（点赞评论时使用）
        action: 操作类型 - upvote(点赞), downvote(踩)
    
    Returns:
        操作结果
    """
    api_key = get_api_key()
    if not api_key:
        return "❌ 未配置 MOLTBOOK_API_KEY"
    
    if not post_id and not comment_id:
        return "❌ 需要提供 post_id 或 comment_id"
    
    if action not in ["upvote", "downvote"]:
        return f"❌ 不支持的操作: {action}（支持 upvote/downvote）"
    
    base_url = "https://www.moltbook.com/api/v1"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # 确定目标类型和 URL
        if comment_id:
            url = f"{base_url}/comments/{comment_id}/{action}"
            target_type = "评论"
            target_id = comment_id
        else:
            url = f"{base_url}/posts/{post_id}/{action}"
            target_type = "帖子"
            target_id = post_id
        
        response = requests.post(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json() if response.content else {}
            action_text = "👍 点赞" if action == "upvote" else "👎 踩"
            
            output = f"{action_text}{target_type}成功！\n"
            output += f"🆔 {target_type}ID: {target_id}\n"
            
            # 如果返回了作者信息和关注建议
            if result.get('author'):
                author_name = result['author'].get('name', 'Unknown')
                output += f"👤 作者: @{author_name}\n"
                
                if result.get('suggestion'):
                    output += f"💡 {result['suggestion']}\n"
                    
                if result.get('already_following') is False:
                    output += f"📌 你还没有关注 @{author_name}\n"
            
            return output
        else:
            return f"❌ 操作失败 (HTTP {response.status_code})\n📝 {response.text[:200]}"
            
    except requests.exceptions.Timeout:
        return "❌ 请求超时"
    except Exception as e:
        return f"❌ 错误: {str(e)}"


if __name__ == "__main__":
    # 测试
    print(run(post_id="test_id", action="upvote"))