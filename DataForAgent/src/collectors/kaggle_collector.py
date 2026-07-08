import os
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from kaggle.api.kaggle_api_extended import KaggleApi
from loguru import logger

from src.config import KAGGLE_USERNAME, KAGGLE_KEY, DATA_RAW_PATH


class KaggleCollector:
    """Kaggle 数据采集器"""

    def __init__(self):
        self.api = None
        self.raw_path = DATA_RAW_PATH
        if KAGGLE_USERNAME and KAGGLE_KEY:
            self._init_api()

    def _init_api(self):
        """初始化 Kaggle API"""
        try:
            os.environ['KAGGLE_USERNAME'] = KAGGLE_USERNAME
            os.environ['KAGGLE_KEY'] = KAGGLE_KEY
            self.api = KaggleApi()
            self.api.authenticate()
            logger.info("Kaggle API 初始化成功")
        except Exception as e:
            logger.warning(f"Kaggle API 初始化失败: {e}，将使用备用方案")

    def search_datasets(self, query: str = "worldcup", exclude_2026: bool = True) -> List[Dict]:
        """搜索 Kaggle 数据集"""
        if not self.api:
            logger.error("Kaggle API 未初始化，请配置 KAGGLE_USERNAME 和 KAGGLE_KEY")
            return []

        try:
            datasets = self.api.dataset_list(search=query, sort_by='hottest')
            results = []

            for ds in datasets:
                title = ds.title or ""
                if exclude_2026 and '2026' in title.upper():
                    logger.debug(f"跳过 2026 数据集: {title}")
                    continue

                results.append({
                    'ref': ds.ref,
                    'title': title,
                    'size': ds.size,
                    'download_count': getattr(ds, 'download_count', 0),
                    'last_updated': str(ds.last_updated) if hasattr(ds, 'last_updated') else None
                })

            logger.info(f"找到 {len(results)} 个相关数据集")
            return results

        except Exception as e:
            logger.error(f"搜索数据集失败: {e}")
            return []

    def download_dataset(self, dataset_ref: str, filename_pattern: str = None) -> Optional[Path]:
        """下载数据集"""
        if not self.api:
            logger.error("Kaggle API 未初始化")
            return None

        try:
            download_path = self.raw_path / dataset_ref.replace('/', '_')
            download_path.mkdir(parents=True, exist_ok=True)

            self.api.dataset_download_files(
                dataset_ref,
                path=str(download_path),
                unzip=True
            )

            logger.info(f"数据集已下载: {dataset_ref} -> {download_path}")

            csv_files = list(download_path.glob("*.csv"))
            if csv_files:
                return csv_files[0]
            return download_path

        except Exception as e:
            logger.error(f"下载数据集失败: {e}")
            return None

    def load_csv_as_dict(self, filepath: Path) -> List[Dict]:
        """加载 CSV 文件为字典列表"""
        try:
            df = pd.read_csv(filepath)
            records = df.to_dict('records')
            logger.info(f"已加载 {len(records)} 条记录: {filepath.name}")
            return records
        except Exception as e:
            logger.error(f"加载 CSV 失败: {e}")
            return []

    def quick_search_and_download(self, query: str = "worldcup football") -> List[Path]:
        """快速搜索并下载世界杯相关数据集"""
        datasets = self.search_datasets(query)

        downloaded = []
        for ds in datasets[:5]:
            path = self.download_dataset(ds['ref'])
            if path:
                downloaded.append(path)

        return downloaded


def main():
    collector = KaggleCollector()

    logger.info("开始搜索 Kaggle 数据集...")
    datasets = collector.search_datasets("worldcup football")

    print("\n找到的数据集:")
    for i, ds in enumerate(datasets[:10], 1):
        print(f"{i}. {ds['title']}")
        print(f"   Ref: {ds['ref']}")
        print(f"   Size: {ds['size']}, Downloads: {ds['download_count']}")
        print()


if __name__ == "__main__":
    main()
