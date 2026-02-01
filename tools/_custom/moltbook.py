
import requests
import json

API_BASE = "https://www.moltbook.com/api/v1"
API_KEY = "moltbook_sk_eizKbYzmnyaSYRzsIG2ashWEE8WcuulM"

def run(action, submolt=None, sort="hot", limit=10, title=None, content=None, 
        post_id=None, comment_id=None, query=None, search_type="all",
        recipient=None, message_id=None, username=None):
    """Moltbook AI Agent 社交网络工具"""
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        if action == "browse":
            params = {"sort": sort, "limit": limit}
            if submolt:
                params["submolt"] = submolt
            resp = requests.get(f"{API_BASE}/feed", headers=headers, params=params, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            posts = data.get("posts", [])
            
            result = []
            for p in posts[:limit]:
                result.append({
                    "id": p.get("id"),
                    "title": p.get("title"),
                    "author": p.get("author", {}).get("name"),
                    "submolt": p.get("submolt", {}).get("name"),
                    "karma": p.get("karma", 0),
                    "comments": p.get("comment_count", 0),
                    "url": f"https://moltbook.com/post/{p.get('id')}"
                })
            return json.dumps(result, indent=2, ensure_ascii=False)
        
        elif action == "post":
            if not title or not content:
                return "错误: 发帖需要 title 和 content"
            payload = {"title": title, "content": content}
            if submolt:
                payload["submolt"] = submolt
            resp = requests.post(f"{API_BASE}/posts", headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            post = data.get("post", data)
            return f"发帖成功!\nID: {post.get('id')}\nURL: https://moltbook.com/post/{post.get('id')}"
        
        elif action == "reply":
            if not post_id or not content:
                return "错误: 回复需要 post_id 和 content"
            payload = {"content": content}
            resp = requests.post(f"{API_BASE}/posts/{post_id}/comments", headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return f"回复成功!\n评论 ID: {data.get('comment', {}).get('id')}"
        
        elif action == "view":
            if not post_id:
                return "错误: 需要 post_id"
            resp = requests.get(f"{API_BASE}/posts/{post_id}", headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            post = data.get("post", data)
            
            result = {
                "title": post.get("title"),
                "author": post.get("author", {}).get("name"),
                "content": post.get("content"),
                "karma": post.get("karma", 0),
                "comments": post.get("comment_count", 0),
                "url": f"https://moltbook.com/post/{post.get('id')}"
            }
            
            comments = post.get("comments", [])
            if comments:
                result["comment_list"] = []
                for c in comments[:10]:
                    result["comment_list"].append({
                        "author": c.get("author", {}).get("name"),
                        "content": c.get("content"),
                        "karma": c.get("karma", 0)
                    })
            return json.dumps(result, indent=2, ensure_ascii=False)
        
        elif action == "notifications":
            resp = requests.get(f"{API_BASE}/notifications", headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            notifs = data.get("notifications", [])
            
            result = []
            for n in notifs[:10]:
                result.append({
                    "type": n.get("type"),
                    "read": n.get("read"),
                    "post_id": n.get("post_id"),
                    "comment_id": n.get("comment_id"),
                    "from": n.get("from_agent", {}).get("name")
                })
            return json.dumps(result, indent=2, ensure_ascii=False)
        
        elif action == "profile":
            resp = requests.get(f"{API_BASE}/agents/me", headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            agent = data.get("agent", data)
            return json.dumps({
                "name": agent.get("name"),
                "bio": agent.get("bio"),
                "karma": agent.get("karma"),
                "claimed": agent.get("claimed"),
                "claimed_by": agent.get("claimed_by"),
                "post_count": agent.get("post_count"),
                "comment_count": agent.get("comment_count"),
                "url": f"https://moltbook.com/u/{agent.get('name')}"
            }, indent=2, ensure_ascii=False)
        
        elif action == "search":
            if not query:
                return "错误: 搜索需要 query"
            params = {"q": query, "type": search_type, "limit": limit}
            resp = requests.get(f"{API_BASE}/search", headers=headers, params=params, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            
            results = []
            for item in data.get("results", [])[:limit]:
                results.append({
                    "type": item.get("type"),
                    "title": item.get("title"),
                    "content": item.get("content", "")[:200],
                    "author": item.get("author", {}).get("name"),
                    "similarity": item.get("similarity"),
                    "post_id": item.get("post_id"),
                    "url": f"https://moltbook.com/post/{item.get('post_id')}"
                })
            return json.dumps(results, indent=2, ensure_ascii=False)
        
        elif action == "upvote":
            if comment_id:
                resp = requests.post(f"{API_BASE}/comments/{comment_id}/upvote", headers=headers, timeout=60)
                resp.raise_for_status()
                return f"已点赞评论 {comment_id}"
            elif post_id:
                resp = requests.post(f"{API_BASE}/posts/{post_id}/upvote", headers=headers, timeout=60)
                resp.raise_for_status()
                return f"已点赞帖子 {post_id}"
            else:
                return "错误: upvote 需要 post_id 或 comment_id"
        
        elif action == "downvote":
            if comment_id:
                resp = requests.post(f"{API_BASE}/comments/{comment_id}/downvote", headers=headers, timeout=60)
                resp.raise_for_status()
                return f"已踩评论 {comment_id}"
            elif post_id:
                resp = requests.post(f"{API_BASE}/posts/{post_id}/downvote", headers=headers, timeout=60)
                resp.raise_for_status()
                return f"已踩帖子 {post_id}"
            else:
                return "错误: downvote 需要 post_id 或 comment_id"
        
        elif action == "messages":
            # 检查私信活动 (dm/check)
            resp = requests.get(f"{API_BASE}/agents/dm/check", headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            
            result = {
                "has_activity": data.get("has_activity"),
                "summary": data.get("summary"),
                "pending_requests": data.get("requests", {}).get("count", 0),
                "unread_messages": data.get("messages", {}).get("total_unread", 0)
            }
            
            # 如果有待处理的请求，显示它们
            requests_items = data.get("requests", {}).get("items", [])
            if requests_items:
                result["requests"] = []
                for r in requests_items:
                    result["requests"].append({
                        "conversation_id": r.get("conversation_id"),
                        "from": r.get("from", {}).get("name"),
                        "preview": r.get("message_preview")
                    })
            
            # 如果有未读消息，显示最新的
            latest = data.get("messages", {}).get("latest", [])
            if latest:
                result["latest_messages"] = latest
            
            return json.dumps(result, indent=2, ensure_ascii=False)
        
        elif action == "send_message":
            if not recipient or not content:
                return "错误: 发送私信需要 recipient 和 content"
            
            # 先检查是否已有对话
            conv_resp = requests.get(f"{API_BASE}/agents/dm/conversations", headers=headers, timeout=60)
            conv_resp.raise_for_status()
            conversations = conv_resp.json().get("conversations", {}).get("items", [])
            
            # 查找已有对话
            existing_conv = None
            for conv in conversations:
                if conv.get("with_agent", {}).get("name", "").lower() == recipient.lower():
                    existing_conv = conv.get("conversation_id")
                    break
            
            if existing_conv:
                # 在已有对话中发送消息
                payload = {"message": content}
                resp = requests.post(f"{API_BASE}/agents/dm/conversations/{existing_conv}/send", 
                                    headers=headers, json=payload, timeout=60)
                resp.raise_for_status()
                return f"私信发送成功!\n收件人: {recipient}\n(已有对话)"
            else:
                # 发送新的聊天请求
                payload = {"to": recipient, "message": content}
                resp = requests.post(f"{API_BASE}/agents/dm/request", headers=headers, json=payload, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                return f"聊天请求已发送!\n收件人: {recipient}\n状态: 等待对方批准"
        
        elif action == "read_message":
            if not message_id:
                return "错误: 需要 message_id (conversation_id)"
            
            resp = requests.get(f"{API_BASE}/agents/dm/conversations/{message_id}", headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            
            conv = data.get("conversation", {})
            messages = conv.get("messages", [])
            
            result = {
                "with_agent": conv.get("with_agent", {}).get("name"),
                "status": conv.get("status"),
                "messages": []
            }
            
            for m in messages[-20:]:  # 最近20条
                result["messages"].append({
                    "from": m.get("from", {}).get("name"),
                    "content": m.get("content"),
                    "sent_at": m.get("sent_at")
                })
            
            return json.dumps(result, indent=2, ensure_ascii=False)
        
        elif action == "follow":
            if not username:
                return "错误: 关注需要 username"
            resp = requests.post(f"{API_BASE}/agents/{username}/follow", headers=headers, timeout=60)
            resp.raise_for_status()
            return f"已关注 {username}"
        
        elif action == "unfollow":
            if not username:
                return "错误: 取消关注需要 username"
            resp = requests.delete(f"{API_BASE}/agents/{username}/follow", headers=headers, timeout=60)
            resp.raise_for_status()
            return f"已取消关注 {username}"
        
        else:
            return f"未知操作: {action}"
    
    except requests.exceptions.Timeout:
        return "错误: 请求超时，Moltbook API 响应较慢，请稍后再试"
    except requests.exceptions.HTTPError as e:
        error_msg = str(e)
        try:
            error_detail = e.response.json()
            error_msg = error_detail.get("error", error_msg)
        except:
            pass
        return f"HTTP 错误: {error_msg}"
    except Exception as e:
        return f"错误: {str(e)}"
