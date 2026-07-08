import requests
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from loguru import logger

from src.config import DATA_RAW_PATH


class FIFACollector:
    """FIFA 五大联赛数据采集器（基于 football-data.co.uk）"""

    BASE_URL = "https://www.football-data.co.uk"
    LEAGUES = {
        "Premier League": "E0",
        "La Liga": "SP1",
        "Bundesliga": "D1",
        "Serie A": "I1",
        "Ligue 1": "F1"
    }

    def __init__(self):
        self.raw_path = DATA_RAW_PATH / "fifa"
        self.raw_path.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })

    def _download_with_retry(
        self, url: str, max_retries: int = 4, timeout: int = 30
    ) -> Optional[requests.Response]:
        """带重试的下载，支持 SSL 降级"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.SSLError:
                if attempt == max_retries - 1:
                    raise
                import urllib3
                urllib3.disable_warnings()
                try:
                    response = self.session.get(url, timeout=timeout, verify=False)
                    response.raise_for_status()
                    return response
                except Exception:
                    pass
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
        return None

    def get_available_seasons(self, league_code: str) -> List[str]:
        """获取可用赛季列表"""
        try:
            url = f"{self.BASE_URL}/mmz4281/{league_code}.csv"
            response = self.session.head(url, timeout=10)

            seasons = []
            for year in range(2026, 2019, -1):
                next_year = str(year + 1)[-2:]
                season = f"{year}{next_year}"
                test_url = f"{self.BASE_URL}/mmz4281/{season[:4]}{season[4:]}/{league_code}.csv"

                try:
                    r = self.session.head(test_url, timeout=5)
                    if r.status_code == 200:
                        seasons.append(season)
                except:
                    continue

            return seasons[:5]
        except Exception as e:
            logger.error(f"获取赛季列表失败: {e}")
            return []

    def download_league(self, league_name: str, season: str = None) -> Optional[Path]:
        """下载单个联赛数据"""
        if league_name not in self.LEAGUES:
            logger.error(f"未知联赛: {league_name}")
            return None

        league_code = self.LEAGUES[league_name]
        year = season[:4] if season else "2526"

        url = f"{self.BASE_URL}/mmz4281/{year}/{league_code}.csv"

        try:
            response = self._download_with_retry(url)
            if response is None:
                return None

            filename = f"{league_name.replace(' ', '_')}_{year}.csv"
            filepath = self.raw_path / filename

            with open(filepath, 'wb') as f:
                f.write(response.content)

            logger.info(f"已下载: {league_name} {year} -> {filepath}")
            return filepath

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                url_fallback = f"{self.BASE_URL}/mmz4281/{league_code}.csv"
                return self._download_latest(url_fallback, league_name)
            logger.error(f"下载失败: {e}")
            return None
        except Exception as e:
            logger.error(f"下载失败: {e}")
            return None

    def _download_latest(self, url: str, league_name: str) -> Optional[Path]:
        """备用：下载最新可用数据"""
        try:
            response = self._download_with_retry(url)
            if response is None:
                return None

            filename = f"{league_name.replace(' ', '_')}_latest.csv"
            filepath = self.raw_path / filename

            with open(filepath, 'wb') as f:
                f.write(response.content)

            logger.info(f"已下载（最新）: {league_name} -> {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"备用下载失败: {e}")
            return None

    def download_all_leagues(self, seasons: List[str] = None) -> List[Path]:
        """下载所有五大联赛数据"""
        downloaded = []

        for league_name in self.LEAGUES.keys():
            logger.info(f"正在下载: {league_name}")

            if seasons:
                for season in seasons[:2]:
                    path = self.download_league(league_name, season)
                    if path:
                        downloaded.append(path)
            else:
                path = self.download_league(league_name)
                if path:
                    downloaded.append(path)

        logger.info(f"共下载 {len(downloaded)} 个文件")
        return downloaded

    def load_csv_as_dict(self, filepath: Path) -> List[Dict]:
        """加载 CSV 为字典列表"""
        try:
            df = pd.read_csv(filepath)
            df['source_file'] = filepath.name
            df['source_league'] = filepath.stem.split('_')[0]
            records = df.to_dict('records')
            logger.info(f"已加载 {len(records)} 条记录: {filepath.name}")
            return records
        except Exception as e:
            logger.error(f"加载 CSV 失败: {e}")
            return []

    def get_match_preview(self, filepath: Path) -> Dict:
        """获取比赛数据预览"""
        df = pd.read_csv(filepath)
        return {
            'columns': list(df.columns),
            'rows': len(df),
            'sample': df.head(3).to_dict('records')
        }


def main():
    collector = FIFACollector()

    print("=== FIFA 五大联赛数据采集器 ===\n")

    for league in collector.LEAGUES.keys():
        path = collector.download_league(league)
        if path:
            preview = collector.get_match_preview(path)
            print(f"\n{league}:")
            print(f"  列名: {preview['columns']}")
            print(f"  记录数: {preview['rows']}")


if __name__ == "__main__":
    main()
