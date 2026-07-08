"""世界杯数据归一化器（纯规则）。

数据来源：Kaggle FIFA World Cup 数据集，已经按
- editions（届）
- matches（比赛）
- top_scorers（射手榜）
三个维度预处理为 JSON。

本模块做：
- 字段重命名（驼峰 → snake_case）
- 类型规范化（字符串数字 → int）
- 去重
- 输出统一的归一化结构
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from loguru import logger

RAW_DIR = Path("data/raw/worldcup")
PROCESSED_DIR = Path("data/processed/worldcup")


def safe_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def sanitize(value: Any) -> Any:
    """递归清理 NaN/Inf，确保可 JSON 序列化"""
    if value is None:
        return None
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            return None
        return round(value, 10)
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items() if v is not None and v != ""}
    if isinstance(value, list):
        return [sanitize(v) for v in value if v is not None and v != ""]
    return value


def load_json(path: Path) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("matches", "editions", "scorers", "data"):
            if key in data and isinstance(data[key], list):
                return data[key]
    return []


def normalize_edition(record: Dict[str, Any]) -> Dict[str, Any]:
    """统一一届世界杯为一个记录"""
    return sanitize({
        "year": safe_int(record.get("Year") or record.get("year")),
        "host_country": record.get("Host") or record.get("host"),
        "winner": record.get("Winner") or record.get("winner"),
        "runner_up": record.get("Runners-Up") or record.get("runner_up") or record.get("Runner-Up"),
        "third": record.get("Third") or record.get("third"),
        "fourth": record.get("Fourth") or record.get("fourth"),
        "goals_scored": safe_int(record.get("GoalsScored") or record.get("goals_scored")),
        "matches_played": safe_int(record.get("MatchesPlayed") or record.get("matches_played")),
        "attendance": safe_int(record.get("Attendance") or record.get("attendance")),
        "teams_count": safe_int(record.get("QualifiedTeams") or record.get("teams")),
    })


def normalize_match(record: Dict[str, Any]) -> Dict[str, Any]:
    """统一一场世界杯比赛为一个记录"""
    return sanitize({
        "year": safe_int(record.get("Year") or record.get("year")),
        "stage": record.get("Stage") or record.get("stage") or record.get("Round"),
        "date": record.get("Date") or record.get("date"),
        "home_team": record.get("Home Team Name") or record.get("home_team") or record.get("HomeTeam"),
        "away_team": record.get("Away Team Name") or record.get("away_team") or record.get("AwayTeam"),
        "home_score": safe_int(record.get("Home Team Goals") or record.get("home_score")),
        "away_score": safe_int(record.get("Away Team Goals") or record.get("away_score")),
        "attendance": safe_int(record.get("Attendance") or record.get("attendance")),
        "stadium": record.get("Stadium") or record.get("stadium"),
        "city": record.get("City") or record.get("city"),
        "referee": record.get("Referee") or record.get("referee"),
    })


def normalize_scorer(record: Dict[str, Any]) -> Dict[str, Any]:
    """统一一名射手为一个记录"""
    return sanitize({
        "year": safe_int(record.get("Year") or record.get("year") or record.get("tournament_year")),
        "rank": safe_int(record.get("Rank") or record.get("rank")),
        "player": record.get("Player") or record.get("player") or record.get("name"),
        "team": record.get("Team") or record.get("team"),
        "goals": safe_int(record.get("Goals") or record.get("goals")),
    })


def dedupe(records: List[Dict[str, Any]], key_fields: List[str]) -> List[Dict[str, Any]]:
    """按关键字段去重（保留首条）"""
    seen = set()
    result = []
    for r in records:
        key = tuple(r.get(k) for k in key_fields)
        if key in seen:
            continue
        seen.add(key)
        result.append(r)
    return result


def normalize_all(raw_dir: Path = RAW_DIR, processed_dir: Path = PROCESSED_DIR) -> Dict[str, Any]:
    """归一化全部世界杯数据"""
    processed_dir.mkdir(parents=True, exist_ok=True)

    filtered = raw_dir / "filtered"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output: Dict[str, Any] = {
        "metadata": {
            "source": "Kaggle FIFA World Cup",
            "normalized_at": datetime.now().isoformat(),
        }
    }

    # Editions
    editions_path = filtered / "wc_editions_pre2026.json"
    if editions_path.exists():
        editions = [normalize_edition(r) for r in load_json(editions_path)]
        editions = dedupe(editions, ["year"])
        output["editions"] = editions
        logger.info(f"editions: {len(editions)} 条")

    # Matches
    matches_path = filtered / "wc_matches_pre2026.json"
    if matches_path.exists():
        matches = [normalize_match(r) for r in load_json(matches_path)]
        matches = dedupe(matches, ["year", "stage", "date", "home_team", "away_team"])
        output["matches"] = matches
        logger.info(f"matches: {len(matches)} 条")

    # Scorers
    scorers_path = filtered / "wc_scorers_pre2026.json"
    if scorers_path.exists():
        scorers = [normalize_scorer(r) for r in load_json(scorers_path)]
        scorers = dedupe(scorers, ["year", "player", "team"])
        output["scorers"] = scorers
        logger.info(f"scorers: {len(scorers)} 条")

    output["metadata"]["totals"] = {
        "editions": len(output.get("editions", [])),
        "matches": len(output.get("matches", [])),
        "scorers": len(output.get("scorers", [])),
    }

    out_path = processed_dir / f"worldcup_normalized_{timestamp}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(sanitize(output), f, ensure_ascii=False, indent=2)

    logger.success(f"世界杯数据归一化完成: {out_path}")
    logger.success(f"editions={output['metadata']['totals']['editions']}, "
                   f"matches={output['metadata']['totals']['matches']}, "
                   f"scorers={output['metadata']['totals']['scorers']}")

    return output


if __name__ == "__main__":
    normalize_all()