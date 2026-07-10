"""干净的规则化数据管道（无 LLM 依赖）。

Pipeline 步骤：
1. 读取 data/raw/ 下的原始 CSV / JSON
2. 调用相应的规则化归一器（fifa_normalizer / worldcup_normalizer）
3. 持久化到 data/processed/，按来源分目录
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from src.config import DATA_RAW_PATH, DATA_PROCESSED_PATH
from src.normalizer.fifa_normalizer import normalize_all_leagues
from src.normalizer.worldcup_normalizer import normalize_all as normalize_worldcup


def ensure_dirs() -> None:
    DATA_PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
    (DATA_PROCESSED_PATH / "league").mkdir(parents=True, exist_ok=True)
    (DATA_PROCESSED_PATH / "worldcup").mkdir(parents=True, exist_ok=True)


def stage_leagues() -> List[Dict[str, Any]]:
    """阶段1：归一化五大联赛数据"""
    fifa_raw = DATA_RAW_PATH / "fifa"
    if not fifa_raw.exists():
        logger.warning(f"未找到五大联赛原始数据: {fifa_raw}")
        return []

    out_dir = DATA_PROCESSED_PATH / "league"
    records = normalize_all_leagues(str(fifa_raw), str(DATA_PROCESSED_PATH))
    logger.info(f"[league] 归一化完成: {len(records)} 条比赛")
    return records


def stage_worldcup() -> Dict[str, Any]:
    """阶段2：归一化世界杯数据"""
    wc_raw = DATA_RAW_PATH / "worldcup"
    if not wc_raw.exists():
        logger.warning(f"未找到世界杯原始数据: {wc_raw}")
        return {}

    output = normalize_worldcup(raw_dir=wc_raw, processed_dir=DATA_PROCESSED_PATH / "worldcup")
    totals = output.get("metadata", {}).get("totals", {})
    logger.info(f"[worldcup] 归一化完成: {totals}")
    return output


def write_index() -> None:
    """写入 processed/index.json 作为元数据索引"""
    index = {
        "generated_at": datetime.now().isoformat(),
        "datasets": {},
    }

    league_dir = DATA_PROCESSED_PATH / "league"
    if league_dir.exists():
        unified_files = sorted(league_dir.glob("leagues_unified_*.json"))
        if unified_files:
            latest = unified_files[-1]
            with open(latest, "r", encoding="utf-8") as f:
                data = json.load(f)
            index["datasets"]["leagues"] = {
                "file": str(latest.relative_to(DATA_PROCESSED_PATH.parent)),
                "total_matches": data.get("metadata", {}).get("total_matches", 0),
            }

    wc_dir = DATA_PROCESSED_PATH / "worldcup"
    if wc_dir.exists():
        wc_files = sorted(wc_dir.glob("worldcup_normalized_*.json"))
        if wc_files:
            latest = wc_files[-1]
            with open(latest, "r", encoding="utf-8") as f:
                data = json.load(f)
            index["datasets"]["worldcup"] = {
                "file": str(latest.relative_to(DATA_PROCESSED_PATH.parent)),
                **data.get("metadata", {}).get("totals", {}),
            }

        # The 2026 roster is produced by its dedicated normalizer rather than
        # ``worldcup_normalizer``. Keep it in the public data contract whenever
        # the general pipeline refreshes the index.
        squad_path = wc_dir / "wc_2026_squad_normalized.json"
        if squad_path.exists():
            with open(squad_path, "r", encoding="utf-8") as f:
                squad_data = json.load(f)
            stats = squad_data.get("stats", {})
            squads = squad_data.get("squads", {})
            index["datasets"]["wc2026_squad"] = {
                "file": str(squad_path.relative_to(DATA_PROCESSED_PATH.parent)),
                "groups": stats.get("groups", len(squads)),
                "teams": stats.get(
                    "teams", sum(len(teams) for teams in squads.values())
                ),
                "total_players": stats.get(
                    "total_players",
                    sum(
                        len(team.get("players", []))
                        for teams in squads.values()
                        for team in teams.values()
                    ),
                ),
            }

    index_path = DATA_PROCESSED_PATH / "index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    logger.success(f"索引已写入: {index_path}")


def run_pipeline() -> Dict[str, Any]:
    """执行完整 pipeline"""
    logger.info("=== DataForAgent Pipeline 启动 ===")
    ensure_dirs()

    summary = {}

    try:
        leagues = stage_leagues()
        summary["leagues"] = len(leagues)
    except Exception as e:
        logger.error(f"联赛归一化失败: {e}")
        summary["leagues"] = 0

    try:
        worldcup = stage_worldcup()
        summary["worldcup"] = worldcup.get("metadata", {}).get("totals", {})
    except Exception as e:
        logger.error(f"世界杯归一化失败: {e}")
        summary["worldcup"] = {}

    write_index()

    logger.success("=== Pipeline 完成 ===")
    logger.success(f"汇总: {summary}")
    return summary


if __name__ == "__main__":
    run_pipeline()
