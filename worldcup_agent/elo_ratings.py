"""S9 — Elo Ratings scraper (eloratings.net).

Data source: https://www.eloratings.net/World.tsv
Format: headerless TSV, 244 rows, 2-letter ISO codes

TTL cache (7 days default, configurable via ELO_CACHE_TTL_HOURS env var).

Usage:
  python -m worldcup_agent.elo_ratings        # uses cache if fresh
  python -m worldcup_agent.elo_ratings --force   # bypass TTL, force refresh
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import httpx
import pandas as pd

# ── Config (inline to avoid dependency on data_layer/config.py) ─────────────────

ROOT = Path(__file__).resolve().parents[1]          # WorldCupAgent/worldcup_agent → WorldCupAgent
DATA = ROOT / "worldcup_agent" / "data_layer"
CLEANED_DIR = DATA / "cleaned"
FEATURES_DIR = DATA / "features"
CLEANED_DIR.mkdir(parents=True, exist_ok=True)
FEATURES_DIR.mkdir(parents=True, exist_ok=True)

HEADERS_JSON = {
    "User-Agent": "WorldCupAgent-research/1.0 (https://github.com/worldcup-agent)"
}
REQUEST_TIMEOUT = 30.0
ELO_TSV_URL = "https://www.eloratings.net/World.tsv"
ELO_CACHE = CLEANED_DIR / "elo_live_ratings.json"
ELO_CSV = FEATURES_DIR / "team_elo_rankings.csv"
ELO_TTL_HOURS = int(os.getenv("ELO_CACHE_TTL_HOURS", "168"))   # 7 days

# 2-letter ISO code → 2026 WC roster team name
ELO_CODE_TO_NAME: dict[str, str] = {
    "AR": "Argentina",      "MX": "Mexico",          "EC": "Ecuador",
    "JM": "Jamaica",       "ES": "Spain",           "NL": "Netherlands",
    "CM": "Cameroon",      "QA": "Qatar",          "EN": "England",
    "US": "USA",           "IR": "Iran",            "WA": "Wales",
    "BR": "Brazil",        "PT": "Portugal",        "RS": "Serbia",
    "GH": "Ghana",         "DE": "Germany",         "JP": "Japan",
    "CR": "Costa Rica",    "NZ": "New Zealand",    "BE": "Belgium",
    "HR": "Croatia",       "MA": "Morocco",         "CA": "Canada",
    "FR": "France",        "DK": "Denmark",         "TN": "Tunisia",
    "PE": "Peru",          "UY": "Uruguay",         "IT": "Italy",
    "KR": "South Korea",   "AU": "Australia",       "CO": "Colombia",
    "PY": "Paraguay",      "PA": "Panama",          "BO": "Bolivia",
    "SN": "Senegal",       "DZ": "Algeria",         "ZA": "South Africa",
    "BF": "Burkina Faso",  "PL": "Poland",          "SE": "Sweden",
    "AT": "Austria",       "EG": "Egypt",           "NG": "Nigeria",
    "CI": "Ivory Coast",   "GR": "Greece",          "ZM": "Zambia",
}


# ── TTL helpers ────────────────────────────────────────────────────────────────

def _cache_age_hours() -> float | None:
    if not ELO_CACHE.exists():
        return None
    mtime = datetime.fromtimestamp(ELO_CACHE.stat().st_mtime, tz=timezone.utc)
    return (datetime.now(timezone.utc) - mtime).total_seconds() / 3600


def _is_cache_fresh() -> bool:
    age = _cache_age_hours()
    return age is not None and age < ELO_TTL_HOURS


# ── Fetch ─────────────────────────────────────────────────────────────────────

def fetch_elo_tsv() -> str:
    r = httpx.get(ELO_TSV_URL, headers=HEADERS_JSON, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.text


# ── Parse ─────────────────────────────────────────────────────────────────────

def parse_elo_tsv(raw: str) -> pd.DataFrame:
    rows = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        code = parts[2].strip()
        if not re.match(r"^[A-Z]{2}$", code):
            continue
        try:
            rows.append({"world_rank": int(parts[0]), "fifa_code": code,
                         "elo": int(parts[3])})
        except (ValueError, IndexError):
            continue
    return pd.DataFrame(rows)


# ── Map ───────────────────────────────────────────────────────────────────────

def build_enriched_mapping(elo_df: pd.DataFrame) -> dict:
    elo_df = elo_df.copy()
    elo_df["team_name"] = elo_df["fifa_code"].map(ELO_CODE_TO_NAME)
    out = {}
    for _, row in elo_df.iterrows():
        name = row["team_name"]
        if pd.isna(name) or name in out:
            continue
        out[name] = {
            "team_2026_name": name,
            "fifa_code": row["fifa_code"],
            "world_rank": int(row["world_rank"]),
            "elo_rating": int(row["elo"]),
            "source": "eloratings.net live",
        }
    return out


# ── Patch enriched.json ────────────────────────────────────────────────────────

def _patch_enriched_from_csv() -> None:
    enriched_path = CLEANED_DIR / "teams_2026_enriched.json"
    if not enriched_path.exists() or not ELO_CSV.exists():
        return
    elo_df = pd.read_csv(ELO_CSV)
    teams = json.loads(enriched_path.read_text(encoding="utf-8"))["teams"]
    elo_lkp = dict(zip(elo_df["team_2026_name"], elo_df["world_rank"]))
    elo_vlkp = dict(zip(elo_df["team_2026_name"], elo_df["elo_rating"]))
    code_lkp = dict(zip(elo_df["team_2026_name"], elo_df["fifa_code"]))
    patched = []
    for t in teams:
        name = t["team_2026_name"]
        patched.append({
            **t,
            "world_rank_live": elo_lkp.get(name),
            "elo_rating_live": elo_vlkp.get(name),
            "fifa_code": code_lkp.get(name, t.get("fifa_code")),
            "ranking_source": "eloratings.net",
        })
    out = {"generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
           "total": len(patched), "teams": patched}
    enriched_path.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                             encoding="utf-8")


# ── Main ───────────────────────────────────────────────────────────────────────

def run(force_refresh: bool = False) -> dict:
    if not force_refresh and _is_cache_fresh():
        age = _cache_age_hours()
        if ELO_CSV.exists():
            try:
                _patch_enriched_from_csv()
                return {"ok": True, "cached": True,
                        "age_hours": round(age, 1),
                        "teams_matched": int(pd.read_csv(ELO_CSV).shape[0])}
            except Exception:
                pass
        return {"ok": True, "cached": True}

    try:
        raw = fetch_elo_tsv()
    except Exception as e:
        if ELO_CACHE.exists():
            raw = ELO_CACHE.read_text(encoding="utf-8")
        else:
            return {"ok": False, "error": str(e)[:120]}

    ELO_CACHE.write_text(raw, encoding="utf-8")
    elo_df = parse_elo_tsv(raw)
    elo_map = build_enriched_mapping(elo_df)
    pd.DataFrame(list(elo_map.values())).to_csv(ELO_CSV, index=False)
    _patch_enriched_from_csv()

    return {"ok": True, "cached": False, "teams_matched": len(elo_map)}


if __name__ == "__main__":
    result = run(force_refresh=("--force" in sys.argv or "--refresh" in sys.argv))
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
