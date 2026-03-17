#!/usr/bin/env python3
"""
数据输出模块
支持 JSON/CSV/SQLite 导出
"""

import os
import json
import csv
import sqlite3
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

from .config import get_config
from .logger import get_logger

logger = get_logger("output")


class DataExporter:
    """数据导出器"""
    
    def __init__(self, format: str = None, directory: str = None):
        config = get_config()
        self.format = format or config.output.default_format
        self.directory = directory or config.output.directory
        
        # 确保目录存在
        os.makedirs(self.directory, exist_ok=True)
    
    def export(self, data: List[Dict], filename: str = None, **kwargs) -> str:
        """导出数据"""
        if not data:
            logger.warning("没有数据需要导出")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_{timestamp}"
        
        if self.format == "json":
            return self.export_json(data, filename, **kwargs)
        elif self.format == "csv":
            return self.export_csv(data, filename, **kwargs)
        elif self.format == "sqlite":
            return self.export_sqlite(data, filename, **kwargs)
        else:
            raise ValueError(f"不支持的格式: {self.format}")
    
    def export_json(self, data: List[Dict], filename: str, **kwargs) -> str:
        """导出为 JSON"""
        config = get_config()
        json_config = config.output.json
        
        filepath = os.path.join(self.directory, f"{filename}.json")
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                data, f,
                ensure_ascii=json_config.get("ensure_ascii", False),
                indent=json_config.get("indent", 2),
                **kwargs
            )
        
        logger.info(f"已导出 JSON: {filepath} ({len(data)} 条)")
        return filepath
    
    def export_csv(self, data: List[Dict], filename: str, **kwargs) -> str:
        """导出为 CSV"""
        if not data:
            return ""
        
        config = get_config()
        csv_config = config.output.csv
        
        filepath = os.path.join(self.directory, f"{filename}.csv")
        
        # 获取所有字段
        fieldnames = set()
        for item in data:
            fieldnames.update(item.keys())
        fieldnames = sorted(fieldnames)
        
        with open(filepath, "w", encoding=csv_config.get("encoding", "utf-8-sig"), 
                  newline="", delimiter=csv_config.get("delimiter", ",")) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, **kwargs)
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"已导出 CSV: {filepath} ({len(data)} 条)")
        return filepath
    
    def export_sqlite(self, data: List[Dict], filename: str, table: str = None, **kwargs) -> str:
        """导出为 SQLite"""
        if not data:
            return ""
        
        config = get_config()
        sqlite_config = config.output.sqlite
        
        filepath = os.path.join(self.directory, sqlite_config.get("database", "crawler.db"))
        table_name = table or sqlite_config.get("table", "crawled_data")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        
        # 获取字段
        fieldnames = set()
        for item in data:
            fieldnames.update(item.keys())
        fieldnames = sorted(fieldnames)
        
        # 创建表
        columns = ", ".join([f'"{k}" TEXT' for k in fieldnames])
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})")
        
        # 插入数据
        placeholders = ", ".join(["?"] * len(fieldnames))
        for item in data:
            values = [str(item.get(k, "")) for k in fieldnames]
            cursor.execute(f"INSERT INTO {table_name} VALUES ({placeholders})", values)
        
        conn.commit()
        conn.close()
        
        logger.info(f"已导出 SQLite: {filepath} ({len(data)} 条)")
        return filepath
    
    def append_json(self, data: List[Dict], filename: str = "data") -> str:
        """追加到 JSON 文件"""
        filepath = os.path.join(self.directory, f"{filename}.json")
        
        # 读取现有数据
        existing = []
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    existing = json.load(f)
                    if not isinstance(existing, list):
                        existing = [existing]
                except:
                    existing = []
        
        # 追加新数据
        existing.extend(data)
        
        # 写入
        config = get_config()
        json_config = config.output.json
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                existing, f,
                ensure_ascii=json_config.get("ensure_ascii", False),
                indent=json_config.get("indent", 2)
            )
        
        logger.info(f"已追加 JSON: {filepath} (共 {len(existing)} 条)")
        return filepath


class DataCollector:
    """数据收集器（更高级的封装）"""
    
    def __init__(self, exporter: DataExporter = None):
        self.exporter = exporter or DataExporter()
        self.data: List[Dict] = []
        self._fields: set = set()
    
    def add(self, item: Dict):
        """添加数据项"""
        self.data.append(item)
        self._fields.update(item.keys())
    
    def add_many(self, items: List[Dict]):
        """批量添加"""
        for item in items:
            self.add(item)
    
    def get(self, index: int = None) -> Any:
        """获取数据"""
        if index is None:
            return self.data
        return self.data[index]
    
    def filter(self, **kwargs) -> List[Dict]:
        """过滤数据"""
        result = []
        for item in self.data:
            match = True
            for key, value in kwargs.items():
                if item.get(key) != value:
                    match = False
                    break
            if match:
                result.append(item)
        return result
    
    def export(self, filename: str = None, **kwargs) -> str:
        """导出数据"""
        return self.exporter.export(self.data, filename, **kwargs)
    
    def clear(self):
        """清空数据"""
        self.data.clear()
        self._fields.clear()
    
    def __len__(self):
        return len(self.data)
    
    def __iter__(self):
        return iter(self.data)


# 便捷函数
def create_exporter(format: str = None, directory: str = None) -> DataExporter:
    """创建导出器"""
    return DataExporter(format, directory)


def collect_and_export(
    data: List[Dict], 
    format: str = None, 
    filename: str = None,
    directory: str = None
) -> str:
    """收集并导出数据（单步完成）"""
    exporter = DataExporter(format, directory)
    return exporter.export(data, filename)
