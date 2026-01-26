"""
记忆管理模块 - 持久化存储 AI 的重要记忆
"""

import os
import json
from datetime import datetime
from pathlib import Path

# 记忆存储目录
MEMORY_DIR = Path(os.path.expanduser("~/self-evolving-agent/workspace/memory"))
MEMORY_FILE = MEMORY_DIR / "memories.json"


class MemoryManager:
    def __init__(self):
        self._ensure_dirs()
        self.memories = self._load_memories()
    
    def _ensure_dirs(self):
        """确保目录存在"""
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        if not MEMORY_FILE.exists():
            MEMORY_FILE.write_text("{}")
    
    def _load_memories(self) -> dict:
        """加载记忆"""
        try:
            return json.loads(MEMORY_FILE.read_text())
        except:
            return {}
    
    def _save_memories(self):
        """保存记忆"""
        MEMORY_FILE.write_text(json.dumps(self.memories, indent=2, ensure_ascii=False))
    
    def remember(self, category: str, key: str, content: str) -> str:
        """
        记住重要信息
        
        Args:
            category: 分类（wallet/api/knowledge/preference）
            key: 唯一标识
            content: 记忆内容
        """
        if category not in self.memories:
            self.memories[category] = {}
        
        self.memories[category][key] = {
            "content": content,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self._save_memories()
        return f"✅ 已记住 [{category}] {key}"
    
    def recall(self, query: str = None, category: str = None) -> str:
        """
        回忆信息
        
        Args:
            query: 搜索关键词（可选）
            category: 指定分类（可选）
        """
        if not self.memories:
            return "记忆为空"
        
        results = []
        
        for cat, items in self.memories.items():
            # 如果指定了分类，只看这个分类
            if category and cat != category:
                continue
            
            for key, data in items.items():
                content = data["content"]
                
                # 如果有搜索词，过滤匹配的
                if query:
                    if query.lower() not in key.lower() and query.lower() not in content.lower():
                        continue
                
                results.append(f"[{cat}] **{key}**\n{content}")
        
        if not results:
            return f"没有找到相关记忆" + (f"（搜索词: {query}）" if query else "")
        
        return "\n\n---\n\n".join(results)
    
    def forget(self, category: str, key: str) -> str:
        """
        删除记忆
        """
        if category not in self.memories:
            return f"❌ 分类 {category} 不存在"
        
        if key not in self.memories[category]:
            return f"❌ 记忆 {key} 不存在"
        
        del self.memories[category][key]
        
        # 如果分类空了，删除分类
        if not self.memories[category]:
            del self.memories[category]
        
        self._save_memories()
        return f"✅ 已删除 [{category}] {key}"
    
    def list_memories(self) -> str:
        """
        列出所有记忆
        """
        if not self.memories:
            return "📭 记忆为空"
        
        output = ["📝 **所有记忆：**\n"]
        
        for category, items in self.memories.items():
            output.append(f"\n**[{category}]**")
            for key, data in items.items():
                # 截取内容前 50 字符
                preview = data["content"][:50] + "..." if len(data["content"]) > 50 else data["content"]
                output.append(f"  • {key}: {preview}")
        
        return "\n".join(output)
    
    def get_core_memories(self) -> str:
        """
        获取核心记忆（用于注入 system prompt）
        """
        if not self.memories:
            return ""
        
        output = []
        
        # 优先级分类
        priority_categories = ["wallet", "api", "secret", "preference"]
        
        for cat in priority_categories:
            if cat in self.memories:
                for key, data in self.memories[cat].items():
                    output.append(f"- [{cat}] {key}: {data['content']}")
        
        # 其他分类
        for cat, items in self.memories.items():
            if cat not in priority_categories:
                for key, data in items.items():
                    output.append(f"- [{cat}] {key}: {data['content']}")
        
        return "\n".join(output) if output else ""


# 全局单例
memory_manager = MemoryManager()
