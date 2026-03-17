#!/usr/bin/env python3
"""
配置管理模块
支持 YAML/JSON 配置文件加载
"""

import os
import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class BrowserConfig:
    """浏览器配置"""
    headless: bool = False
    viewport: Dict[str, int] = field(default_factory=lambda: {"width": 1280, "height": 720})
    user_data_dir: Optional[str] = None
    slow_mo: int = 0


@dataclass
class RequestConfig:
    """请求配置"""
    timeout: int = 30
    retry: Dict[str, int] = field(default_factory=lambda: {"max": 3, "delay": 1})
    interval: int = 1
    max_concurrency: int = 3


@dataclass
class AnticrawlerConfig:
    """反爬配置"""
    random_ua: bool = True
    ua_list: list = field(default_factory=list)
    proxies: list = field(default_factory=list)
    fingerprint: Dict = field(default_factory=dict)


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    file: Dict = field(default_factory=lambda: {"enabled": True, "path": "./logs/crawler.log"})


@dataclass
class OutputConfig:
    """输出配置"""
    default_format: str = "json"
    directory: str = "./data"
    json: Dict = field(default_factory=lambda: {"ensure_ascii": False, "indent": 2})
    csv: Dict = field(default_factory=lambda: {"encoding": "utf-8-sig", "delimiter": ","})
    sqlite: Dict = field(default_factory=lambda: {"database": "./data/crawler.db", "table": "crawled_data"})


@dataclass
class QueueConfig:
    """队列配置"""
    storage: str = "memory"
    redis: Dict = field(default_factory=dict)
    retry: Dict[str, int] = field(default_factory=lambda: {"max": 3, "delay": 5})


@dataclass
class CheckpointConfig:
    """断点配置"""
    enabled: bool = True
    file: str = "./data/checkpoint.json"
    dedup_fields: list = field(default_factory=lambda: ["url", "id"])


@dataclass
class Config:
    """全局配置"""
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    request: RequestConfig = field(default_factory=RequestConfig)
    anticrawler: AnticrawlerConfig = field(default_factory=AnticrawlerConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    queue: QueueConfig = field(default_factory=QueueConfig)
    checkpoint: CheckpointConfig = field(default_factory=CheckpointConfig)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Config":
        """从字典加载配置"""
        return cls(
            browser=BrowserConfig(**data.get("browser", {})),
            request=RequestConfig(**data.get("request", {})),
            anticrawler=AnticrawlerConfig(**data.get("anticrawler", {})),
            logging=LoggingConfig(**data.get("logging", {})),
            output=OutputConfig(**data.get("output", {})),
            queue=QueueConfig(**data.get("queue", {})),
            checkpoint=CheckpointConfig(**data.get("checkpoint", {}))
        )


class ConfigManager:
    """配置管理器"""
    
    _instance: Optional["ConfigManager"] = None
    _config: Optional[Config] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load(self, config_path: str = None) -> Config:
        """加载配置文件"""
        if config_path is None:
            # 默认查找当前目录的 config.yaml
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        
        if not os.path.exists(config_path):
            # 返回默认配置
            self._config = Config()
            return self._config
        
        # 根据扩展名选择加载方式
        ext = Path(config_path).suffix.lower()
        
        with open(config_path, "r", encoding="utf-8") as f:
            if ext in [".yaml", ".yml"]:
                data = yaml.safe_load(f)
            elif ext == ".json":
                data = json.load(f)
            else:
                raise ValueError(f"不支持的配置文件格式: {ext}")
        
        self._config = Config.from_dict(data)
        return self._config
    
    @property
    def config(self) -> Config:
        """获取当前配置"""
        if self._config is None:
            self._config = self.load()
        return self._config
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            elif isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value


# 全局配置管理器实例
config_manager = ConfigManager()


def get_config() -> Config:
    """获取全局配置"""
    return config_manager.config


def load_config(config_path: str = None) -> Config:
    """加载配置"""
    return config_manager.load(config_path)
