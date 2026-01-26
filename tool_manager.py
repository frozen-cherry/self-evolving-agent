"""
工具管理器 - 动态加载、创建、删除工具
支持 AI 自我扩展能力
"""

import os
import json
import importlib.util
import traceback
from pathlib import Path
from datetime import datetime

# 路径配置
BASE_DIR = Path(__file__).parent
BUILTIN_TOOLS_DIR = BASE_DIR / "tools" / "_builtin"
CUSTOM_TOOLS_DIR = BASE_DIR / "tools" / "_custom"
MANIFEST_FILE = CUSTOM_TOOLS_DIR / "manifest.json"


class ToolManager:
    def __init__(self):
        self.tools = {}  # name -> {schema, function, is_builtin}
        self._ensure_dirs()
        self._load_builtin_tools()
        self._load_custom_tools()
    
    def _ensure_dirs(self):
        """确保目录存在"""
        CUSTOM_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
        if not MANIFEST_FILE.exists():
            MANIFEST_FILE.write_text("{}")
    
    def _load_builtin_tools(self):
        """加载内置工具"""
        
        # 1. 联网搜索
        self.tools["web_search"] = {
            "schema": {
                "name": "web_search",
                "description": "搜索互联网获取实时信息。用于查询新闻、价格、事件等实时数据。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词"
                        }
                    },
                    "required": ["query"]
                }
            },
            "function": self._web_search,
            "is_builtin": True
        }
        
        # 2. 代码执行
        self.tools["run_python"] = {
            "schema": {
                "name": "run_python",
                "description": "执行 Python 代码。用于计算、数据处理、调用 API、测试逻辑等。代码在隔离环境中执行。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "要执行的 Python 代码"
                        }
                    },
                    "required": ["code"]
                }
            },
            "function": self._run_python,
            "is_builtin": True
        }
        
        # 3. 创建新工具（元工具）
        self.tools["create_tool"] = {
            "schema": {
                "name": "create_tool",
                "description": """创建一个新的工具来扩展自己的能力。
当用户需要一个你目前没有的功能时使用。
创建的工具会被持久化保存，下次可以直接使用。

注意：
- 工具代码必须包含一个 run() 函数作为入口
- run() 函数的参数要和 parameters 定义匹配
- 代码要处理好异常，返回字符串结果
- 不要创建一次性工具，只创建可复用的""",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "工具名称，英文小写+下划线格式，如 get_btc_price"
                        },
                        "description": {
                            "type": "string",
                            "description": "工具功能的详细描述"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "工具参数的 JSON Schema 定义",
                            "properties": {
                                "type": {"type": "string"},
                                "properties": {"type": "object"},
                                "required": {"type": "array"}
                            }
                        },
                        "code": {
                            "type": "string",
                            "description": "Python 代码，必须包含 def run(...) 函数"
                        }
                    },
                    "required": ["name", "description", "parameters", "code"]
                }
            },
            "function": self._create_tool,
            "is_builtin": True
        }
        
        # 4. 列出所有工具
        self.tools["list_tools"] = {
            "schema": {
                "name": "list_tools",
                "description": "列出当前所有可用的工具，包括内置工具和自定义工具",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            "function": self._list_tools,
            "is_builtin": True
        }
        
        # 5. 删除工具
        self.tools["delete_tool"] = {
            "schema": {
                "name": "delete_tool",
                "description": "删除一个自定义工具（内置工具不可删除）",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "要删除的工具名称"
                        }
                    },
                    "required": ["name"]
                }
            },
            "function": self._delete_tool,
            "is_builtin": True
        }
        
        # 6. 查看工具代码
        self.tools["view_tool_code"] = {
            "schema": {
                "name": "view_tool_code",
                "description": "查看自定义工具的源代码，用于了解或修改工具",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "工具名称"
                        }
                    },
                    "required": ["name"]
                }
            },
            "function": self._view_tool_code,
            "is_builtin": True
        }
        
        # 7. 更新工具
        self.tools["update_tool"] = {
            "schema": {
                "name": "update_tool",
                "description": "更新一个已存在的自定义工具的代码或描述",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "要更新的工具名称"
                        },
                        "description": {
                            "type": "string",
                            "description": "新的描述（可选）"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "新的参数定义（可选）"
                        },
                        "code": {
                            "type": "string",
                            "description": "新的代码（可选）"
                        }
                    },
                    "required": ["name"]
                }
            },
            "function": self._update_tool,
            "is_builtin": True
        }
        
        # 8. 记忆 - 记住重要信息
        self.tools["remember"] = {
            "schema": {
                "name": "remember",
                "description": """记住重要信息，持久化保存。

应该记住的信息类型：
- wallet: 钱包地址、私钥位置
- api: API Key 位置、调用方法
- secret: 密码、密钥存放位置
- knowledge: 学到的知识（比如某API要收费了）
- preference: 用户的偏好和习惯""",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "分类：wallet/api/secret/knowledge/preference"
                        },
                        "key": {
                            "type": "string",
                            "description": "唯一标识，如 solana_main_wallet"
                        },
                        "content": {
                            "type": "string",
                            "description": "记忆内容"
                        }
                    },
                    "required": ["category", "key", "content"]
                }
            },
            "function": self._remember,
            "is_builtin": True
        }
        
        # 9. 回忆 - 搜索记忆
        self.tools["recall"] = {
            "schema": {
                "name": "recall",
                "description": "回忆/搜索之前记住的信息",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词（可选）"
                        },
                        "category": {
                            "type": "string",
                            "description": "指定分类（可选）"
                        }
                    }
                }
            },
            "function": self._recall,
            "is_builtin": True
        }
        
        # 10. 列出所有记忆
        self.tools["list_memories"] = {
            "schema": {
                "name": "list_memories",
                "description": "列出所有已保存的记忆",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            "function": self._list_memories,
            "is_builtin": True
        }
        
        # 11. 删除记忆
        self.tools["forget"] = {
            "schema": {
                "name": "forget",
                "description": "删除一条记忆",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "分类"
                        },
                        "key": {
                            "type": "string",
                            "description": "记忆的 key"
                        }
                    },
                    "required": ["category", "key"]
                }
            },
            "function": self._forget,
            "is_builtin": True
        }
    
    def _load_custom_tools(self):
        """从 manifest 加载所有自定义工具"""
        if not MANIFEST_FILE.exists():
            return
        
        try:
            manifest = json.loads(MANIFEST_FILE.read_text())
        except json.JSONDecodeError:
            manifest = {}
        
        for name, meta in manifest.items():
            try:
                self._load_single_tool(name, meta)
            except Exception as e:
                print(f"⚠️ 加载工具 {name} 失败: {e}")
    
    def _load_single_tool(self, name: str, meta: dict):
        """动态加载单个自定义工具"""
        code_file = CUSTOM_TOOLS_DIR / f"{name}.py"
        if not code_file.exists():
            return
        
        # 动态导入模块
        spec = importlib.util.spec_from_file_location(name, code_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if not hasattr(module, "run"):
            raise ValueError(f"工具 {name} 缺少 run() 函数")
        
        self.tools[name] = {
            "schema": {
                "name": name,
                "description": meta["description"],
                "input_schema": meta["parameters"]
            },
            "function": module.run,
            "is_builtin": False
        }
        print(f"✅ 已加载自定义工具: {name}")
    
    # ========== 内置工具实现 ==========
    
    def _web_search(self, query: str) -> str:
        """联网搜索"""
        try:
            from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
            
            if not results:
                return "没有找到相关结果"
            
            output = []
            for r in results:
                output.append(f"**{r['title']}**\n{r['body']}\n链接: {r['href']}")
            
            return "\n\n---\n\n".join(output)
        
        except ImportError:
            return "❌ 搜索功能需要安装: pip install duckduckgo-search"
        except Exception as e:
            return f"❌ 搜索失败: {str(e)}"
    
    def _run_python(self, code: str) -> str:
        """执行 Python 代码"""
        import subprocess
        import tempfile
        from config import CODE_TIMEOUT
        
        # 安全检查（只限制最危险的操作）
        dangerous_patterns = [
            "rm -rf /",
            "rm -rf /*",
            "open('/etc/shadow",
            "open('/etc/passwd",
            "> /dev/sda",
            "mkfs.",
            "dd if=",
        ]
        
        for pattern in dangerous_patterns:
            if pattern in code:
                return f"❌ 安全限制：代码包含禁止的操作 ({pattern})"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_file = f.name
        
        try:
            result = subprocess.run(
                ['python3', temp_file],
                capture_output=True,
                text=True,
                timeout=CODE_TIMEOUT,
                cwd=tempfile.gettempdir()
            )
            
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += f"\n[STDERR]\n{result.stderr}"
            
            return output.strip() if output.strip() else "✅ 代码执行完成，无输出"
        
        except subprocess.TimeoutExpired:
            return f"❌ 执行超时（{CODE_TIMEOUT}秒）"
        except Exception as e:
            return f"❌ 执行错误: {str(e)}"
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass
    
    def _create_tool(self, name: str, description: str, parameters: dict, code: str) -> str:
        """创建新的自定义工具"""
        # 验证工具名
        if name in self.tools:
            return f"❌ 工具 {name} 已存在。如需更新请使用 update_tool"
        
        if not name.replace("_", "").isalnum():
            return "❌ 工具名只能包含字母、数字、下划线"
        
        if name.startswith("_"):
            return "❌ 工具名不能以下划线开头"
        
        # 验证代码
        if "def run(" not in code and "def run (" not in code:
            return "❌ 代码必须包含 def run(...) 函数作为入口"
        
        # 安全检查（只限制最危险的操作）
        dangerous_patterns = ["rm -rf /", "rm -rf /*", "open('/etc/shadow"]
        for pattern in dangerous_patterns:
            if pattern in code:
                return f"❌ 安全限制：代码包含禁止的操作 ({pattern})"
        
        # 保存代码文件
        code_file = CUSTOM_TOOLS_DIR / f"{name}.py"
        code_file.write_text(code)
        
        # 更新 manifest
        try:
            manifest = json.loads(MANIFEST_FILE.read_text())
        except:
            manifest = {}
        
        manifest[name] = {
            "description": description,
            "parameters": parameters,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        MANIFEST_FILE.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        
        # 尝试热加载
        try:
            self._load_single_tool(name, manifest[name])
            return f"✅ 工具 「{name}」 创建成功！现在可以直接使用了。"
        except Exception as e:
            # 回滚
            code_file.unlink()
            del manifest[name]
            MANIFEST_FILE.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
            return f"❌ 工具创建失败，代码有错误: {str(e)}\n\n请检查代码后重试。"
    
    def _list_tools(self) -> str:
        """列出所有工具"""
        builtin_tools = []
        custom_tools = []
        
        for name, tool in self.tools.items():
            desc = tool["schema"]["description"].split("\n")[0]  # 只取第一行
            if tool.get("is_builtin", False):
                builtin_tools.append(f"  • {name}: {desc[:50]}...")
            else:
                custom_tools.append(f"  • {name}: {desc[:50]}...")
        
        output = "📦 **内置工具：**\n" + "\n".join(sorted(builtin_tools))
        
        if custom_tools:
            output += "\n\n🔧 **自定义工具：**\n" + "\n".join(sorted(custom_tools))
        else:
            output += "\n\n🔧 **自定义工具：** 暂无"
        
        return output
    
    def _delete_tool(self, name: str) -> str:
        """删除自定义工具"""
        if name not in self.tools:
            return f"❌ 工具 {name} 不存在"
        
        if self.tools[name].get("is_builtin", False):
            return f"❌ {name} 是内置工具，无法删除"
        
        # 删除代码文件
        code_file = CUSTOM_TOOLS_DIR / f"{name}.py"
        if code_file.exists():
            code_file.unlink()
        
        # 更新 manifest
        try:
            manifest = json.loads(MANIFEST_FILE.read_text())
            if name in manifest:
                del manifest[name]
                MANIFEST_FILE.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        except:
            pass
        
        # 从内存移除
        del self.tools[name]
        
        return f"✅ 工具 「{name}」 已删除"
    
    def _view_tool_code(self, name: str) -> str:
        """查看工具代码"""
        if name not in self.tools:
            return f"❌ 工具 {name} 不存在"
        
        if self.tools[name].get("is_builtin", False):
            return f"❌ {name} 是内置工具，代码不可查看"
        
        code_file = CUSTOM_TOOLS_DIR / f"{name}.py"
        if not code_file.exists():
            return f"❌ 找不到工具 {name} 的代码文件"
        
        code = code_file.read_text()
        
        # 获取 manifest 信息
        try:
            manifest = json.loads(MANIFEST_FILE.read_text())
            meta = manifest.get(name, {})
            info = f"创建时间: {meta.get('created_at', '未知')}\n更新时间: {meta.get('updated_at', '未知')}"
        except:
            info = ""
        
        return f"📄 **工具 {name} 的代码：**\n\n{info}\n\n```python\n{code}\n```"
    
    def _update_tool(self, name: str, description: str = None, parameters: dict = None, code: str = None) -> str:
        """更新自定义工具"""
        if name not in self.tools:
            return f"❌ 工具 {name} 不存在"
        
        if self.tools[name].get("is_builtin", False):
            return f"❌ {name} 是内置工具，无法更新"
        
        if not any([description, parameters, code]):
            return "❌ 请至少提供一个要更新的字段（description, parameters, code）"
        
        # 读取现有 manifest
        try:
            manifest = json.loads(MANIFEST_FILE.read_text())
            meta = manifest.get(name, {})
        except:
            return "❌ 读取工具信息失败"
        
        # 更新代码
        if code:
            if "def run(" not in code and "def run (" not in code:
                return "❌ 代码必须包含 def run(...) 函数"
            
            # 安全检查（只限制最危险的操作）
            dangerous_patterns = ["rm -rf /", "rm -rf /*", "open('/etc/shadow"]
            for pattern in dangerous_patterns:
                if pattern in code:
                    return f"❌ 安全限制：代码包含禁止的操作 ({pattern})"
            
            code_file = CUSTOM_TOOLS_DIR / f"{name}.py"
            code_file.write_text(code)
        
        # 更新 manifest
        if description:
            meta["description"] = description
        if parameters:
            meta["parameters"] = parameters
        meta["updated_at"] = datetime.now().isoformat()
        
        manifest[name] = meta
        MANIFEST_FILE.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        
        # 重新加载
        try:
            # 先移除旧的
            if name in self.tools:
                del self.tools[name]
            self._load_single_tool(name, meta)
            return f"✅ 工具 「{name}」 更新成功！"
        except Exception as e:
            return f"❌ 更新失败: {str(e)}"
    
    # ========== 记忆工具实现 ==========
    
    def _remember(self, category: str, key: str, content: str) -> str:
        """记住重要信息"""
        from memory_manager import memory_manager
        return memory_manager.remember(category, key, content)
    
    def _recall(self, query: str = None, category: str = None) -> str:
        """回忆信息"""
        from memory_manager import memory_manager
        return memory_manager.recall(query, category)
    
    def _list_memories(self) -> str:
        """列出所有记忆"""
        from memory_manager import memory_manager
        return memory_manager.list_memories()
    
    def _forget(self, category: str, key: str) -> str:
        """删除记忆"""
        from memory_manager import memory_manager
        return memory_manager.forget(category, key)
    
    # ========== 对外接口 ==========
    
    def get_schemas(self) -> list:
        """获取所有工具的 schema（供 Claude API 使用）"""
        return [tool["schema"] for tool in self.tools.values()]
    
    def execute(self, name: str, params: dict) -> str:
        """执行指定工具"""
        if name not in self.tools:
            return f"❌ 未知工具: {name}"
        
        try:
            result = self.tools[name]["function"](**params)
            return str(result) if result else "✅ 执行完成"
        except Exception as e:
            error_detail = traceback.format_exc()
            return f"❌ 工具执行失败: {str(e)}\n\n详细错误:\n{error_detail}"
    
    def reload_tools(self):
        """重新加载所有自定义工具"""
        # 保留内置工具
        builtin = {k: v for k, v in self.tools.items() if v.get("is_builtin", False)}
        self.tools = builtin
        self._load_custom_tools()
        return f"✅ 已重新加载 {len(self.tools) - len(builtin)} 个自定义工具"


# 全局单例
tool_manager = ToolManager()
