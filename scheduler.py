"""
定时任务调度器 - 负责管理和执行定时任务
"""

import json
import os
import logging
import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Callable
from croniter import croniter
import uuid

logger = logging.getLogger(__name__)

# 时区设置 (UTC+8)
TZ_OFFSET = timedelta(hours=8)
TZ = timezone(TZ_OFFSET)

# 任务存储路径
TASKS_FILE = os.path.join(os.path.dirname(__file__), "workspace", "scheduled_tasks.json")


class Scheduler:
    """定时任务调度器"""
    
    def __init__(self):
        self._tasks = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._on_task_execute: Optional[Callable] = None
        self._lock = threading.Lock()
        self._load_tasks()
    
    def _load_tasks(self):
        """从文件加载任务"""
        try:
            if os.path.exists(TASKS_FILE):
                with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._tasks = data.get("tasks", [])
                logger.info(f"已加载 {len(self._tasks)} 个定时任务")
            else:
                self._tasks = []
        except Exception as e:
            logger.error(f"加载定时任务失败: {e}")
            self._tasks = []
    
    def _save_tasks(self):
        """保存任务到文件"""
        try:
            os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
            with open(TASKS_FILE, 'w', encoding='utf-8') as f:
                json.dump({"tasks": self._tasks}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存定时任务失败: {e}")
    
    def _get_next_run(self, cron_expr: str) -> str:
        """根据 cron 表达式计算下次执行时间"""
        now = datetime.now(TZ)
        cron = croniter(cron_expr, now)
        next_run = cron.get_next(datetime)
        return next_run.isoformat()
    
    def create_task(self, cron: str, prompt: str, user_id: int, max_runs: int = 0) -> dict:
        """创建定时任务"""
        task = {
            "id": str(uuid.uuid4())[:8],
            "cron": cron,
            "prompt": prompt,
            "max_runs": max_runs,
            "run_count": 0,
            "user_id": user_id,
            "created_at": datetime.now(TZ).isoformat(),
            "last_run": None,
            "next_run": self._get_next_run(cron),
            "enabled": True
        }
        
        with self._lock:
            self._tasks.append(task)
            self._save_tasks()
        
        logger.info(f"创建定时任务: {task['id']} - {prompt[:30]}")
        return task
    
    def list_tasks(self, user_id: Optional[int] = None) -> list:
        """列出任务"""
        with self._lock:
            if user_id:
                return [t for t in self._tasks if t["user_id"] == user_id]
            return self._tasks.copy()
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        with self._lock:
            for i, task in enumerate(self._tasks):
                if task["id"] == task_id:
                    self._tasks.pop(i)
                    self._save_tasks()
                    logger.info(f"删除定时任务: {task_id}")
                    return True
        return False
    
    def get_task(self, task_id: str) -> Optional[dict]:
        """获取单个任务"""
        with self._lock:
            for task in self._tasks:
                if task["id"] == task_id:
                    return task.copy()
        return None
    
    def set_execute_callback(self, callback: Callable):
        """设置任务执行回调"""
        self._on_task_execute = callback
    
    def start(self):
        """启动调度器"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("定时任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("定时任务调度器已停止")
    
    def _run_loop(self):
        """调度循环"""
        while self._running:
            try:
                self._check_and_execute()
            except Exception as e:
                logger.error(f"调度循环错误: {e}")
            
            # 每 30 秒检查一次
            time.sleep(30)
    
    def _check_and_execute(self):
        """检查并执行到期任务"""
        now = datetime.now(TZ)
        
        with self._lock:
            tasks_to_run = []
            for task in self._tasks:
                if not task.get("enabled", True):
                    continue
                
                next_run = datetime.fromisoformat(task["next_run"])
                if next_run <= now:
                    tasks_to_run.append(task.copy())
        
        # 执行任务（在锁外执行，避免阻塞）
        for task in tasks_to_run:
            self._execute_task(task)
    
    def _execute_task(self, task: dict):
        """执行单个任务"""
        task_id = task["id"]
        logger.info(f"执行定时任务: {task_id}")
        
        try:
            # 调用回调执行任务
            if self._on_task_execute:
                self._on_task_execute(task)
            
            # 更新任务状态
            with self._lock:
                for t in self._tasks:
                    if t["id"] == task_id:
                        t["run_count"] += 1
                        t["last_run"] = datetime.now(TZ).isoformat()
                        
                        # 检查是否达到最大执行次数
                        max_runs = t.get("max_runs", 0)
                        if max_runs > 0 and t["run_count"] >= max_runs:
                            t["enabled"] = False
                            logger.info(f"任务 {task_id} 已达到最大执行次数 {max_runs}，已禁用")
                        else:
                            # 计算下次执行时间
                            t["next_run"] = self._get_next_run(t["cron"])
                        
                        break
                
                self._save_tasks()
                
        except Exception as e:
            logger.error(f"执行任务 {task_id} 失败: {e}")


# 全局调度器实例
scheduler = Scheduler()
