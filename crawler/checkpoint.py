#!/usr/bin/env python3
"""
断点续爬与去重模块
"""

import json
import os
import time
import hashlib
from typing import Any, Dict, List, Optional, Set
from pathlib import Path

from .config import get_config
from .logger import get_logger

logger = get_logger("checkpoint")


class Checkpoint:
    """断点管理器"""
    
    def __init__(self, checkpoint_file: str = None):
        config = get_config()
        checkpoint_config = config.checkpoint
        
        self.enabled = checkpoint_config.enabled
        self.checkpoint_file = checkpoint_file or checkpoint_config.file
        self.dedup_fields = checkpoint_config.dedup_fields
        
        # 内存缓存
        self._visited: Set[str] = set()
        self._data: Dict = {}
        
        if self.enabled:
            self._load()
    
    def _load(self):
        """加载断点文件"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                    self._visited = set(self._data.get("visited", []))
                logger.info(f"加载断点: {len(self._visited)} 条记录")
            except Exception as e:
                logger.warning(f"加载断点失败: {e}")
                self._data = {}
                self._visited = set()
    
    def _save(self):
        """保存断点文件"""
        if not self.enabled:
            return
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.checkpoint_file) or ".", exist_ok=True)
            
            self._data["visited"] = list(self._visited)
            self._data["updated_at"] = time.time()
            
            with open(self.checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            
            logger.debug("断点已保存")
        except Exception as e:
            logger.error(f"保存断点失败: {e}")
    
    def _generate_key(self, item: Dict) -> str:
        """生成去重 key"""
        # 根据配置的字段生成
        values = []
        for field in self.dedup_fields:
            value = item.get(field, "")
            values.append(str(value))
        
        key_str = "|".join(values)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def is_visited(self, item: Dict) -> bool:
        """检查是否已访问"""
        if not self.enabled:
            return False
        
        key = self._generate_key(item)
        return key in self._visited
    
    def mark_visited(self, item: Dict):
        """标记为已访问"""
        if not self.enabled:
            return
        
        key = self._generate_key(item)
        self._visited.add(key)
        
        # 定期保存
        if len(self._visited) % 10 == 0:
            self._save()
    
    def save(self):
        """手动保存断点"""
        self._save()
    
    def clear(self):
        """清空断点"""
        self._visited.clear()
        self._data = {}
        self._save()
        logger.info("断点已清空")
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            "enabled": self.enabled,
            "visited_count": len(self._visited),
            "checkpoint_file": self.checkpoint_file
        }


class RetryManager:
    """失败重试管理器"""
    
    def __init__(self, max_retries: int = None, delay: int = None):
        config = get_config()
        retry_config = config.request.retry
        
        self.max_retries = max_retries or retry_config.get("max", 3)
        self.delay = delay or retry_config.get("delay", 1)
        
        self._attempts: Dict[str, int] = {}
    
    def should_retry(self, key: str) -> bool:
        """是否应该重试"""
        attempts = self._attempts.get(key, 0)
        return attempts < self.max_retries
    
    def record_attempt(self, key: str):
        """记录尝试次数"""
        self._attempts[key] = self._attempts.get(key, 0) + 1
        logger.debug(f"尝试 {key}: {self._attempts[key]}/{self.max_retries}")
    
    def get_delay(self, key: str) -> float:
        """获取重试延迟（指数退避）"""
        attempts = self._attempts.get(key, 1)
        return self.delay * (2 ** (attempts - 1))
    
    def reset(self, key: str):
        """重置重试计数"""
        if key in self._attempts:
            del self._attempts[key]
    
    def clear(self):
        """清空所有计数"""
        self._attempts.clear()


# 全局实例
_checkpoint: Optional[Checkpoint] = None
_retry_manager: Optional[RetryManager] = None


def get_checkpoint(checkpoint_file: str = None) -> Checkpoint:
    """获取断点管理器"""
    global _checkpoint
    if _checkpoint is None:
        _checkpoint = Checkpoint(checkpoint_file)
    return _checkpoint


def get_retry_manager(max_retries: int = None, delay: int = None) -> RetryManager:
    """获取重试管理器"""
    global _retry_manager
    if _retry_manager is None:
        _retry_manager = RetryManager(max_retries, delay)
    return _retry_manager
