import requests

def run(username: str, action: str = "follow") -> str:
    """关注或取消关注Moltbook用户
    
    Args:
        username: 要关注的用户名
        action: 操作类型 - follow(关注) 或 unfollow(取消关注)
    
    Returns:
        操作结果字符串
    """
    import os
    from pathlib import Path
    
    # 获取API Key
    api_key = os.environ.get('MOLTBOOK_API_KEY')
    if not api_key:
        config_path = Path.home() / '.config' / 'moltbook' / 'credentials.json'
        if config_path.exists():
            try:
                import json
                with open(config_path) as f:
                    config = json.load(f)
                    api_key = config.get('api_key', '')
            except:
                pass
    
    if not api_key:
        return "❌ 未配置 MOLTBOOK_API_KEY"
    
    try:
        base_url = "https://www.moltbook.com"
        endpoint = f"/api/v1/agents/{username}/follow"
        url = base_url + endpoint
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 根据操作类型选择 HTTP 方法
        if action == "follow":
            response = requests.post(url, headers=headers, timeout=30)
            action_text = "关注"
        elif action == "unfollow":
            response = requests.delete(url, headers=headers, timeout=30)
            action_text = "取消关注"
        else:
            return f"❌ 不支持的操作: {action}（支持 follow/unfollow）"
        
        if response.status_code == 200:
            result = response.json() if response.content else {"success": True}
            return f"✅ {action_text} @{username} 成功！\n📊 响应: {result.get('message', '操作完成')}"
        else:
            return f"❌ {action_text}失败 (HTTP {response.status_code})\n📝 响应: {response.text[:200]}"
            
    except requests.exceptions.Timeout:
        return "❌ 请求超时"
    except Exception as e:
        return f"❌ 错误: {str(e)}"