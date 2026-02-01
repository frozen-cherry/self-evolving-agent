def run(message, priority="normal", title="TinyBanana AI"):
    """通过 tg-notify 服务发送 Telegram 消息"""
    try:
        import requests
        
        # tg-notify 服务配置
        base_url = "http://81.92.219.140:8000"
        api_key = "bananaisgreat"
        
        # 设置请求头
        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        }
        
        # 请求体
        payload = {
            'title': title,
            'message': message,
            'priority': priority
        }
        
        # 发送请求
        response = requests.post(
            f"{base_url}/notify",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return f"✅ Telegram 消息已发送成功: {title} - {message}"
        else:
            return f"❌ 发送失败: HTTP {response.status_code}, {response.text}"
            
    except requests.exceptions.RequestException as e:
        return f"❌ 网络错误: {str(e)}"
    except Exception as e:
        return f"❌ 未知错误: {str(e)}"