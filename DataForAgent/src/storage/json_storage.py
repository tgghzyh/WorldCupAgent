import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger

from src.config import DATA_RAW_PATH, DATA_PROCESSED_PATH


class JSONStorage:
    """JSON 格式存储管理器"""

    def __init__(self):
        self.raw_path = DATA_RAW_PATH
        self.processed_path = DATA_PROCESSED_PATH

    def save_raw(self, data: List[Dict], source: str) -> Path:
        """保存原始数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{source}_raw_{timestamp}.json"
        filepath = self.raw_path / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"原始数据已保存: {filepath}")
        return filepath

    def save_processed(self, data: List[Dict], source: str) -> Path:
        """保存处理后数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{source}_processed_{timestamp}.json"
        filepath = self.processed_path / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"处理后数据已保存: {filepath}")
        return filepath

    def load(self, filepath: Path) -> List[Dict]:
        """加载 JSON 文件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def merge_and_save(self, datasets: List[Dict], filename: str = None) -> Path:
        """合并多个数据集并保存"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"merged_{timestamp}.json"

        filepath = self.processed_path / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(datasets, f, ensure_ascii=False, indent=2)

        logger.info(f"合并数据已保存: {filepath}")
        return filepath

    def list_files(self, processed: bool = False) -> List[Path]:
        """列出存储的文件"""
        path = self.processed_path if processed else self.raw_path
        return list(path.glob("*.json"))

    def append_to_collection(self, data: List[Dict], collection_name: str) -> Path:
        """追加数据到集合文件（用于增量更新）"""
        filepath = self.processed_path / f"{collection_name}.json"

        existing = []
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                existing = json.load(f)

        existing.extend(data)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

        logger.info(f"已追加 {len(data)} 条数据到 {collection_name}")
        return filepath
