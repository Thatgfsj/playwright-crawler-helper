#!/usr/bin/env python3
"""
任务队列模块
支持内存/Redis/SQLite 存储
"""

import time
import json
import uuid
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue, Empty
from threading import Thread, Lock
import sqlite3

from .config import get_config
from .logger import get_logger

logger = get_logger("queue")


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class Task:
    """任务"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    url: str = ""
    data: Dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    error: str = ""
    result: Any = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "data": self.data,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Task":
        task = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            url=data.get("url", ""),
            data=data.get("data", {}),
            retry_count=data.get("retry_count", 0),
            error=data.get("error", ""),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time())
        )
        if "status" in data:
            task.status = TaskStatus(data["status"])
        return task


class MemoryQueue:
    """内存队列"""
    
    def __init__(self):
        self.queue = Queue()
        self.tasks: Dict[str, Task] = {}
        self.lock = Lock()
    
    def put(self, task: Task):
        with self.lock:
            self.tasks[task.id] = task
        self.queue.put(task.id)
        logger.debug(f"任务入队: {task.id}")
    
    def get(self, timeout: int = 1) -> Optional[Task]:
        try:
            task_id = self.queue.get(timeout=timeout)
            with self.lock:
                task = self.tasks.get(task_id)
            if task:
                task.status = TaskStatus.RUNNING
                task.updated_at = time.time()
            return task
        except Empty:
            return None
    
    def get_task(self, task_id: str) -> Optional[Task]:
        with self.lock:
            return self.tasks.get(task_id)
    
    def update_task(self, task: Task):
        with self.lock:
            self.tasks[task.id] = task
    
    def get_pending(self) -> List[Task]:
        with self.lock:
            return [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
    
    def size(self) -> int:
        return self.queue.qsize()


class SQLiteQueue:
    """SQLite 队列"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                name TEXT,
                url TEXT,
                data TEXT,
                status TEXT,
                retry_count INTEGER,
                error TEXT,
                created_at REAL,
                updated_at REAL
            )
        """)
        conn.commit()
        conn.close()
    
    def put(self, task: Task):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (task.id, task.name, task.url, json.dumps(task.data), 
             task.status.value, task.retry_count, task.error,
             task.created_at, task.updated_at)
        )
        conn.commit()
        conn.close()
        logger.debug(f"任务入队: {task.id}")
    
    def get(self, timeout: int = 1) -> Optional[Task]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tasks WHERE status = ? ORDER BY created_at LIMIT 1",
            (TaskStatus.PENDING.value,)
        )
        row = cursor.fetchone()
        
        if row:
            cursor.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                (TaskStatus.RUNNING.value, time.time(), row[0])
            )
            conn.commit()
            conn.close()
            
            return Task(
                id=row[0], name=row[1], url=row[2],
                data=json.loads(row[3]), status=TaskStatus(row[4]),
                retry_count=row[5], error=row[6],
                created_at=row[7], updated_at=row[8]
            )
        
        conn.close()
        return None
    
    def get_task(self, task_id: str) -> Optional[Task]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Task(
                id=row[0], name=row[1], url=row[2],
                data=json.loads(row[3]), status=TaskStatus(row[4]),
                retry_count=row[5], error=row[6],
                created_at=row[7], updated_at=row[8]
            )
        return None
    
    def update_task(self, task: Task):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tasks SET status = ?, retry_count = ?, error = ?, updated_at = ? WHERE id = ?",
            (task.status.value, task.retry_count, task.error, time.time(), task.id)
        )
        conn.commit()
        conn.close()


class TaskQueue:
    """任务队列管理器"""
    
    def __init__(self, storage: str = None):
        config = get_config()
        storage = storage or config.queue.storage
        
        if storage == "sqlite":
            db_path = config.queue.redis.get("database", "./data/queue.db")
            self.queue = SQLiteQueue(db_path)
        else:
            self.queue = MemoryQueue()
        
        self.max_retries = config.queue.retry.get("max", 3)
        self.retry_delay = config.queue.retry.get("delay", 5)
        
        # 消费者线程
        self.workers: List[Thread] = []
        self.running = False
    
    def add_task(self, name: str, url: str = "", data: Dict = None) -> Task:
        """添加任务"""
        task = Task(name=name, url=url, data=data or {})
        self.queue.put(task)
        logger.info(f"添加任务: {task.id} - {name}")
        return task
    
    def get_task(self, timeout: int = 1) -> Optional[Task]:
        """获取任务"""
        return self.queue.get(timeout=timeout)
    
    def complete_task(self, task: Task, result: Any = None):
        """完成任务"""
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.updated_at = time.time()
        self.queue.update_task(task)
        logger.info(f"任务完成: {task.id}")
    
    def fail_task(self, task: Task, error: str):
        """任务失败"""
        task.error = error
        task.updated_at = time.time()
        
        if task.retry_count < self.max_retries:
            task.status = TaskStatus.RETRY
            task.retry_count += 1
            self.queue.update_task(task)
            logger.warning(f"任务重试: {task.id} ({task.retry_count}/{self.max_retries})")
        else:
            task.status = TaskStatus.FAILED
            self.queue.update_task(task)
            logger.error(f"任务失败: {task.id} - {error}")
    
    def start_workers(self, worker_func: Callable, num_workers: int = None):
        """启动工作线程"""
        config = get_config()
        num_workers = num_workers or config.request.max_concurrency
        
        self.running = True
        
        for i in range(num_workers):
            worker = Thread(target=self._worker, args=(worker_func, i), daemon=True)
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"启动了 {num_workers} 个工作线程")
    
    def _worker(self, worker_func: Callable, worker_id: int):
        """工作线程"""
        logger.debug(f"Worker {worker_id} 开始运行")
        
        while self.running:
            task = self.get_task()
            
            if task:
                try:
                    logger.info(f"Worker {worker_id} 处理任务: {task.id}")
                    result = worker_func(task)
                    self.complete_task(task, result)
                except Exception as e:
                    logger.exception(f"Worker {worker_id} 处理任务失败: {task.id}")
                    self.fail_task(task, str(e))
                    
                    # 重试延迟
                    if task.status == TaskStatus.RETRY:
                        time.sleep(self.retry_delay)
            else:
                time.sleep(0.5)
        
        logger.debug(f"Worker {worker_id} 停止")
    
    def stop(self):
        """停止队列"""
        self.running = False
        for worker in self.workers:
            worker.join(timeout=1)
        logger.info("任务队列已停止")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        tasks = self.queue.get_pending()
        return {
            "pending": self.queue.size(),
            "total": len(tasks) + self.queue.size()
        }


# 全局队列实例
_queue: Optional[TaskQueue] = None


def get_queue(storage: str = None) -> TaskQueue:
    """获取任务队列"""
    global _queue
    if _queue is None:
        _queue = TaskQueue(storage)
    return _queue
