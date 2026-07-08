#!/usr/bin/env python3
"""DataForAgent - 足球数据采集与归一化系统（规则化版）。

数据源：
- Kaggle (世界杯)
- FIFA 五大联赛 (football-data.co.uk)
- URL 抓取 (可选，规则化提取)

归一化策略：纯规则映射，无 LLM 依赖。
"""

import argparse
import sys
from pathlib import Path
from loguru import logger


def setup_logging(verbose: bool = False) -> None:
    """配置日志"""
    from loguru import logger as _logger
    _logger.remove()
    level = "DEBUG" if verbose else "INFO"
    _logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=level,
    )
    _logger.add(
        "logs/main_{time}.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
    )


def run_collect_fifa() -> int:
    """从 football-data.co.uk 重新拉取五大联赛 CSV"""
    from src.collectors.fifa_collector import FIFACollector
    logger.info("=== 采集五大联赛数据 ===")
    collector = FIFACollector()
    files = collector.download_all_leagues()
    logger.success(f"采集完成: {len(files)} 个联赛")
    return len(files)


def run_collect_kaggle(keyword: str = "worldcup football") -> int:
    """从 Kaggle 搜索并下载世界杯数据集"""
    from src.collectors.kaggle_collector import KaggleCollector
    logger.info(f"=== Kaggle 搜索: {keyword} ===")
    collector = KaggleCollector()
    datasets = collector.search_datasets(keyword)
    logger.info(f"找到 {len(datasets)} 个数据集")
    return len(datasets)


def run_scrape_urls(urls: list) -> int:
    """抓取指定 URL 的纯文本内容（无 LLM）"""
    from src.collectors.url_scraper import URLScraper
    logger.info(f"=== URL 抓取 ({len(urls)} 个) ===")
    scraper = URLScraper()
    results = scraper.batch_fetch(urls)
    logger.success(f"抓取完成: {len(results)} 条")
    return len(results)


def run_pipeline() -> None:
    """执行规则化数据管道"""
    from src.pipeline import run_pipeline as _run
    _run()


def run_collect_and_pipeline(keyword: str = "worldcup football") -> None:
    """采集 + 归一化一站式"""
    run_collect_kaggle(keyword)
    run_collect_fifa()
    run_pipeline()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DataForAgent - 足球数据采集与规则化归一化系统",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument(
        "--mode", "-m",
        choices=["pipeline", "collect-fifa", "collect-kaggle", "scrape", "all"],
        default="pipeline",
        help="运行模式",
    )
    parser.add_argument("--keyword", "-k", default="worldcup football", help="Kaggle 搜索关键词")
    parser.add_argument("--url", "-u", action="append", help="要抓取的 URL（可多次使用）")

    args = parser.parse_args()
    setup_logging(args.verbose)

    logger.info("DataForAgent - 规则化版")
    logger.info(f"运行模式: {args.mode}\n")

    if args.mode == "pipeline":
        run_pipeline()
    elif args.mode == "collect-fifa":
        run_collect_fifa()
    elif args.mode == "collect-kaggle":
        run_collect_kaggle(args.keyword)
    elif args.mode == "scrape":
        if not args.url:
            logger.error("scrape 模式需要 --url 参数")
            sys.exit(1)
        run_scrape_urls(args.url)
    elif args.mode == "all":
        run_collect_and_pipeline(args.keyword)


if __name__ == "__main__":
    main()