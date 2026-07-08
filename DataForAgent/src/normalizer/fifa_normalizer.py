"""
FIFA 五大联赛数据归一化脚本
将 football-data.co.uk 的 CSV 数据统一标准化为结构化 JSON
使用规则匹配，无需 LLM
"""

import json
import re
import math
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
from loguru import logger

# ============================================================
# 工具函数
# ============================================================

def sanitize_for_json(obj: Any) -> Any:
    """全面清理对象使其符合 JSON 规范"""
    if obj is None:
        return None
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return round(obj, 10)
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items() if v is not None and v != ''}
    if isinstance(obj, list):
        result = []
        for item in obj:
            cleaned = sanitize_for_json(item)
            if cleaned is not None and cleaned != '':
                result.append(cleaned)
        return result
    if isinstance(obj, str):
        return obj.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    return obj


# ============================================================
# 联赛代码映射
# ============================================================

LEAGUE_CODES = {
    'E0': 'Premier League',
    'SP1': 'La Liga',
    'D1': 'Bundesliga',
    'I1': 'Serie A',
    'F1': 'Ligue 1'
}


# ============================================================
# 日期解析
# ============================================================

def parse_date(date_str: str) -> Optional[str]:
    """解析日期格式 DD/MM/YYYY -> YYYY-MM-DD"""
    if not date_str:
        return None
    try:
        parts = str(date_str).split('/')
        if len(parts) == 3:
            day, month, year = parts
            year = year.strip()
            if len(year) == 2:
                year = f"20{year}"
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    except Exception:
        pass
    return None


def parse_season_from_filename(filename: str) -> str:
    """从文件名解析赛季，如 2526 -> 2025/26"""
    match = re.search(r'(\d{2})(\d{2})', filename)
    if match:
        y1, y2 = match.groups()
        return f"20{y1}/20{y2}"
    return "2025/26"


# ============================================================
# 规则匹配归一化
# ============================================================

def safe_int(val):
    """安全转换为整数"""
    if val is None or val == '':
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def normalize_match_rule(record: dict, filename: str = "") -> dict:
    """归一化单条比赛记录"""
    home_team = record.get('HomeTeam')
    away_team = record.get('AwayTeam')
    league_code = record.get('Div', 'UNK')
    date_str = record.get('Date')
    time_str = record.get('Time')

    # 解析日期
    date = parse_date(date_str)

    # 解析赛季
    season = parse_season_from_filename(filename)

    # 解析比分
    home_score = safe_int(record.get('FTHG'))
    away_score = safe_int(record.get('FTAG'))

    # 半场比分
    half_home = safe_int(record.get('HTHG'))
    half_away = safe_int(record.get('HTAG'))

    # 生成唯一 ID
    match_id = f"{league_code}_{home_team}_{away_team}_{date}".replace(' ', '_')

    return {
        "match_id": match_id,
        "league": LEAGUE_CODES.get(league_code, league_code),
        "league_code": league_code,
        "season": season,
        "date": date,
        "time": time_str,
        "home_team": home_team,
        "away_team": away_team,
        "home_score": home_score,
        "away_score": away_score,
        "result": record.get('FTR'),  # H/D/A
        "half_home_score": half_home,
        "half_away_score": half_away,
        "half_result": record.get('HTR'),
        "referee": record.get('Referee'),
        "home_shots": safe_int(record.get('HS')),
        "away_shots": safe_int(record.get('AS')),
        "home_shots_on_target": safe_int(record.get('HST')),
        "away_shots_on_target": safe_int(record.get('AST')),
        "home_fouls": safe_int(record.get('HF')),
        "away_fouls": safe_int(record.get('AF')),
        "home_corners": safe_int(record.get('HC')),
        "away_corners": safe_int(record.get('AC')),
        "home_yellow_cards": safe_int(record.get('HY')),
        "away_yellow_cards": safe_int(record.get('AY')),
        "home_red_cards": safe_int(record.get('HR')),
        "away_red_cards": safe_int(record.get('AR')),
        "source": "football-data.co.uk",
        "raw_data": sanitize_for_json(record)
    }


def normalize_matches(matches: list, filename: str = "") -> list:
    """归一化比赛列表"""
    return [normalize_match_rule(record, filename) for record in matches]


# ============================================================
# 主程序
# ============================================================

def normalize_league_file(filepath: Path, output_dir: Path) -> list:
    """归一化单个联赛文件"""
    import pandas as pd

    try:
        # 先去掉 UTF-8 BOM，再交给 pandas 自动检测编码
        with open(filepath, 'rb') as f:
            raw = f.read()
        if raw.startswith(b'\xef\xbb\xbf'):
            raw = raw[3:]
        # 写成临时 .csv 供 pandas 读取
        tmp_path = filepath.with_suffix('.csv')
        with open(tmp_path, 'wb') as f:
            f.write(raw)
        try:
            df = pd.read_csv(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)
    except Exception as e:
        logger.error(f"无法读取文件: {filepath}: {e}")
        return []

    # 清理列名（去除首尾空白）
    df.columns = [col.strip() for col in df.columns]

    records = df.to_dict('records')
    logger.info(f"加载 {len(records)} 条记录: {filepath.name}")

    # 归一化
    normalized = normalize_matches(records, filepath.name)

    # 保存
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    league_name = filepath.stem.split('_')[0]
    output_path = output_dir / f"{league_name}_normalized_{ts}.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sanitize_for_json(normalized), f, ensure_ascii=False, indent=2)

    logger.success(f"保存: {output_path}")
    return normalized


def normalize_all_leagues(input_dir: str, output_dir: str):
    """归一化所有联赛数据"""
    input_path = Path(input_dir)
    output_path = Path(output_dir) / "league"
    output_path.mkdir(parents=True, exist_ok=True)

    csv_files = list(input_path.glob("*.csv"))

    if not csv_files:
        logger.warning(f"未找到 CSV 文件: {input_path}")
        return []

    all_normalized = []
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    for csv_file in csv_files:
        normalized = normalize_league_file(csv_file, output_path)
        all_normalized.extend(normalized)

    # 保存合并文件
    if all_normalized:
        unified_path = output_path / f"leagues_unified_{ts}.json"
        unified = {
            "metadata": {
                "source": "football-data.co.uk",
                "leagues": list(LEAGUE_CODES.values()),
                "season": "2025/26",
                "normalized_at": datetime.now().isoformat(),
                "total_matches": len(all_normalized)
            },
            "matches": sanitize_for_json(all_normalized)
        }

        with open(unified_path, 'w', encoding='utf-8') as f:
            json.dump(unified, f, ensure_ascii=False, indent=2)

        logger.success(f"\n=== 联赛数据归一化完成 ===")
        logger.success(f"总比赛数: {len(all_normalized)}")
        logger.success(f"输出目录: {output_path}")

    return all_normalized


def normalize_fifa(input_dir: str, output_dir: str):
    """FIFA 采集数据的统一入口"""
    return normalize_all_leagues(input_dir, output_dir)


if __name__ == '__main__':
    import sys
    logger.add(sys.stderr, level='INFO')

    input_dir = sys.argv[1] if len(sys.argv) > 1 else 'data/raw/fifa'
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'data/processed'

    normalize_all_leagues(input_dir, output_dir)
