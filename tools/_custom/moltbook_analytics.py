#!/usr/bin/env python3
"""
Moltbook 内容分析和运营策略工具
分析真实平台内容，提供可执行的运营建议
"""

import requests
import json
import time
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import random
from pathlib import Path

def get_api_key():
    """获取Moltbook API Key"""
    import os
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

def parse_feed_output(feed_output: str) -> List[Dict]:
    """解析 moltbook_feed 的输出格式为字典列表"""
    posts = []
    
    # 使用正则表达式匹配每个帖子
    pattern = r'(\d+)\.\s*📝\s*(?:文字|链接)\s*\*\*(.*?)\*\*\s*❤️\s*(\d+)\s*\|\s*💬\s*(\d+)\s*📋\s*(.*?)\s*📝\s*(.*?)\s*🆔\s*ID:\s*(.*?)(?=\n|$)'
    matches = re.findall(pattern, feed_output, re.DOTALL)
    
    for match in matches:
        try:
            rank, author_name, likes, comments, title, content, post_id = match
            
            post = {
                'id': post_id.strip(),
                'author': {'name': author_name.strip()},
                'likes': int(likes),
                'comments': int(comments),
                'title': title.strip(),
                'content': content.strip(),
                'url': '',
                'type': 'text'
            }
            posts.append(post)
        except (ValueError, IndexError) as e:
            print(f"解析帖子失败: {e}")
            continue
    
    return posts

class MoltbookAnalyzer:
    def __init__(self):
        self.base_url = "https://www.moltbook.com/api/v1"
        self.api_key = get_api_key()
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
    def get_latest_feed(self, limit: int = 50) -> List[Dict]:
        """从真实API获取feed内容"""
        try:
            response = requests.get(
                f"{self.base_url}/posts",
                headers=self.headers,
                params={'sort': 'hot', 'limit': limit},
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API错误: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"获取feed失败: {e}")
            return []
    
    def analyze_hot_content(self, posts: List[Dict]) -> Dict[str, Any]:
        """分析热门内容"""
        if not posts:
            return {"top_posts": [], "rising_posts": [], "trending_topics": []}
        
        hot_posts = sorted(posts, key=lambda x: x.get('likes', 0), reverse=True)[:5]
        
        rising_posts = []
        for post in posts:
            likes = post.get('likes', 0)
            comments = post.get('comments', 0)
            if likes > 0 and comments > 0:
                engagement_rate = comments / likes
                if engagement_rate > 0.1:
                    rising_posts.append({
                        'post': post,
                        'engagement_rate': engagement_rate,
                        'score': likes * 0.7 + comments * 0.3
                    })
        
        rising_posts.sort(key=lambda x: x['score'], reverse=True)
        rising_posts = [item['post'] for item in rising_posts[:3]]
        
        trending_topics = self._extract_trending_topics(posts)
        
        return {
            "top_posts": hot_posts,
            "rising_posts": rising_posts,
            "trending_topics": trending_topics
        }
    
    def analyze_authors(self, posts: List[Dict]) -> Dict[str, Any]:
        """分析作者质量"""
        author_stats = {}
        
        for post in posts:
            author = post.get('author', {})
            author_name = author.get('name', 'unknown')
            
            if author_name not in author_stats:
                author_stats[author_name] = {
                    'author': author,
                    'posts_count': 0,
                    'total_likes': 0,
                    'total_comments': 0,
                    'avg_engagement': 0,
                    'quality_score': 0
                }
            
            stats = author_stats[author_name]
            stats['posts_count'] += 1
            stats['total_likes'] += post.get('likes', 0)
            stats['total_comments'] += post.get('comments', 0)
        
        for stats in author_stats.values():
            if stats['posts_count'] > 0:
                stats['avg_engagement'] = (stats['total_likes'] + stats['total_comments']) / stats['posts_count']
                stats['quality_score'] = stats['avg_engagement'] * stats['posts_count']
        
        top_authors = sorted(author_stats.values(), key=lambda x: x['quality_score'], reverse=True)[:5]
        
        return {
            "top_authors": top_authors,
            "active_authors_count": len(author_stats),
            "avg_posts_per_author": sum(s['posts_count'] for s in author_stats.values()) / len(author_stats) if author_stats else 0
        }
    
    def generate_engagement_suggestions(self, posts: List[Dict], analysis: Dict) -> Dict[str, Any]:
        """生成可执行的互动建议"""
        suggestions = {
            "like_targets": [],
            "follow_targets": [],
            "reply_opportunities": [],
            "posting_strategy": []
        }
        
        for post in posts:
            post_id = post.get('id')
            likes = post.get('likes', 0)
            comments = post.get('comments', 0)
            author = post.get('author', {})
            author_name = author.get('name', 'Unknown')
            content = post.get('content', '')
            
            if 5 < likes < 25 and len(content) > 30:
                suggestions["like_targets"].append({
                    'post_id': post_id,
                    'author_name': author_name,
                    'likes': likes,
                    'comments': comments,
                    'reason': '中等互动，内容有价值'
                })
        
        for author_data in analysis.get('authors', {}).get('top_authors', []):
            if author_data['posts_count'] >= 2 and author_data['quality_score'] > 15:
                author = author_data['author']
                suggestions["follow_targets"].append({
                    'username': author.get('name'),
                    'bio': author.get('bio', ''),
                    'quality_score': author_data['quality_score'],
                    'reason': '高质量作者(平均互动%.1f)' % author_data['avg_engagement']
                })
        
        for post in posts:
            post_id = post.get('id')
            comments = post.get('comments', 0)
            content = post.get('content', '')
            author = post.get('author', {})
            
            if comments >= 2 and len(content) > 50:
                suggestions["reply_opportunities"].append({
                    'post_id': post_id,
                    'author_name': author.get('name', 'Unknown'),
                    'comments': comments,
                    'reason': '有深度的讨论(%d条评论)' % comments
                })
        
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 11 or 19 <= current_hour <= 21:
            suggestions["posting_strategy"].append("当前是活跃时段，适合发帖")
        else:
            suggestions["posting_strategy"].append("当前互动较少，建议等待高峰时段")
        
        topics = analysis.get('hot_content', {}).get('trending_topics', [])
        if topics:
            suggestions["posting_strategy"].append("热门话题: %s" % ', '.join(topics[:3]))
        
        suggestions["posting_strategy"].append("保持'be very selective'原则，专注质量")
        
        return suggestions
    
    def _extract_trending_topics(self, posts: List[Dict]) -> List[str]:
        """提取趋势话题"""
        keywords = [
            "AI", "Agent", "Python", "machine learning", "data", 
            "blockchain", "crypto", "startup", "product", "design",
            "coding", "programming", "tech", "LLM", "GPT", "automation"
        ]
        
        topic_count = {}
        for post in posts:
            content = post.get('content', '').lower()
            title = post.get('title', '').lower()
            
            for keyword in keywords:
                if keyword.lower() in content or keyword.lower() in title:
                    topic_count[keyword] = topic_count.get(keyword, 0) + 1
        
        sorted_topics = sorted(topic_count.items(), key=lambda x: x[1], reverse=True)
        return [t[0] for t in sorted_topics[:5]]

def run(analysis_type: str = "feed", max_posts: int = 50, feed_input: str = None):
    """主执行函数"""
    analyzer = MoltbookAnalyzer()
    
    # 如果提供了feed输入，尝试解析它
    if feed_input:
        try:
            posts = parse_feed_output(feed_input)
            print(f"从feed输入解析到 {len(posts)} 个帖子")
        except Exception as e:
            print(f"解析feed输入失败: {e}")
            posts = []
    else:
        posts = analyzer.get_latest_feed(max_posts)
    
    if not posts:
        return "❌ 未能获取到Moltbook内容数据\n\n可能原因:\n- API Key未配置\n- 网络超时\n- API服务器不可用\n- feed输入格式无法解析"
    
    hot_analysis = analyzer.analyze_hot_content(posts)
    author_analysis = analyzer.analyze_authors(posts)
    engagement_suggestions = analyzer.generate_engagement_suggestions(posts, {
        'authors': author_analysis,
        'hot_content': hot_analysis
    })
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = """
🍌 Moltbook 运营报告 %s

📊 数据概览:
- 分析帖子: %d条
- 活跃作者: %d人
- 平均每作者帖子数: %.1f
""" % (current_time, len(posts), author_analysis['active_authors_count'], author_analysis['avg_posts_per_author'])
    
    # TOP 3 热门帖子
    report += "\n🔥 TOP 3 热门帖子:\n"
    for i, post in enumerate(hot_analysis["top_posts"][:3], 1):
        author = post.get('author', {})
        post_id = post.get('id', 'N/A')
        content = post.get('content', '')[:60]
        report += "%d. %s\n" % (i, author.get('name', 'Unknown'))
        report += "   ❤️ %d | 💬 %d\n" % (post.get('likes', 0), post.get('comments', 0))
        report += "   内容: %s...\n" % content
        report += "   🆔 ID: %s\n\n" % post_id
    
    # 上升期帖子
    if hot_analysis["rising_posts"]:
        report += "📈 上升期帖子 (高互动潜力):\n"
        for i, post in enumerate(hot_analysis["rising_posts"][:3], 1):
            author = post.get('author', {})
            post_id = post.get('id', 'N/A')
            report += "%d. %s (ID: %s)\n" % (i, author.get('name', 'Unknown'), post_id)
            report += "   ❤️ %d | 💬 %d\n\n" % (post.get('likes', 0), post.get('comments', 0))
    
    # 作者推荐
    report += "👥 值得关注的作者:\n"
    for i, author_data in enumerate(author_analysis["top_authors"][:3], 1):
        author = author_data['author']
        report += "%d. @%s\n" % (i, author.get('name', 'Unknown'))
        bio = author.get('bio', '')
        if bio:
            report += "   Bio: %s\n" % bio[:100]
        report += "   帖子数: %d | 平均互动: %.1f | 质量分: %.1f\n\n" % (author_data['posts_count'], author_data['avg_engagement'], author_data['quality_score'])
    
    # 趋势话题
    if hot_analysis['trending_topics']:
        report += "📈 热门话题:\n"
        for i, topic in enumerate(hot_analysis['trending_topics'][:5], 1):
            report += "%d. %s\n" % (i, topic)
        report += "\n"
    
    # 互动建议
    report += "💡 可执行的互动建议:\n"
    
    if engagement_suggestions["like_targets"]:
        report += "🎯 值得点赞的帖子:\n"
        for target in engagement_suggestions["like_targets"][:3]:
            report += "   • @%s 的帖子 (ID: %s)\n" % (target['author_name'], target['post_id'])
            report += "     理由: %s ❤️%d 💬%d\n\n" % (target['reason'], target['likes'], target['comments'])
    
    if engagement_suggestions["follow_targets"]:
        report += "👤 建议关注的作者:\n"
        for target in engagement_suggestions["follow_targets"][:2]:
            report += "   • @%s\n" % target['username']
            report += "     理由: %s\n\n" % target['reason']
    
    if engagement_suggestions["posting_strategy"]:
        report += "📝 发帖策略建议:\n"
        for strategy in engagement_suggestions["posting_strategy"]:
            report += "   • %s\n" % strategy
    
    report += "\n" + "="*50
    report += "\n🔄 分析完成 | 数据来源: moltbook_feed 解析"
    
    return report