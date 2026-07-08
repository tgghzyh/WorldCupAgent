# DataForAgent

足球比赛数据采集与规则化归一化系统。用于为 2026 世界杯赛事预测建模提供高质量数据集。

## 项目目标

通过采集五大联赛（俱乐部球员表现）和往届世界杯（国家队历史战绩）数据，构建可关联的数据集：

```
俱乐部表现（五大联赛）
    ↓ 球员归属
国家队实力 ← 历史战绩（往届世界杯）
```

## 数据来源

| 来源 | 说明 | 网址 |
|---|---|---|
| football-data.co.uk | 五大联赛比赛数据 | https://www.football-data.co.uk |
| Kaggle FIFA World Cup | 往届世界杯数据集 | https://www.kaggle.com/datasets |

## 当前可用数据集（可直接用于建模）

当前 `data/processed/` 下已清理完毕，仅保留最新有效结果，共 3 个文件：

| 文件 | 说明 | 规模 |
|---|---|---|
| `data/processed/index.json` | 数据入口，记录最新结果路径 | - |
| `data/processed/league/leagues_unified_20260708_121431.json` | 五大联赛归一化统一文件 | 1752 场比赛 |
| `data/processed/worldcup/worldcup_normalized_20260708_121432.json` | 世界杯归一化结果 | 22 届、163 场、22 名射手 |

**下一步**：直接读取上述 JSON 文件，交给预测模型使用。无需再处理历史版本或单联赛文件。

---

## 历史说明

- **历史版本**：每次 pipeline 重跑会生成带不同时间戳的文件（如 `_115927`、`_120736`），内容与最新结果重复，已清理
- **单联赛文件**：各联赛单独归一化文件（如 `Bundesliga_normalized_*.json`）已汇总到统一文件 `leagues_unified_*.json`，属于冗余中间产物，已清理

---

## 目录结构

```
DataForAgent/
├── data/
│   ├── raw/                    # 原始数据（CSV / JSON）
│   │   ├── fifa/               # 五大联赛 CSV（from football-data.co.uk）
│   │   └── worldcup/           # 世界杯 CSV + JSON
│   └── processed/               # 归一化后的数据（已清理，仅保留最新有效文件）
│       ├── index.json          # 数据集索引（入口）
│       ├── league/             # 五大联赛归一化结果
│       │   └── leagues_unified_*.json    # 五大联赛合并文件（当前有效）
│       └── worldcup/           # 世界杯归一化结果
│           └── worldcup_normalized_*.json  # 当前有效
├── src/
│   ├── main.py                 # CLI 入口
│   ├── pipeline.py             # 数据管道编排
│   ├── config.py               # 配置（从 .env 读取）
│   ├── collectors/             # 数据采集器
│   │   ├── fifa_collector.py   # 五大联赛下载（football-data.co.uk）
│   │   ├── kaggle_collector.py # Kaggle 数据集下载
│   │   └── url_scraper.py      # URL 抓取（纯 HTTP，无 LLM）
│   ├── normalizer/             # 规则化归一化
│   │   ├── fifa_normalizer.py  # 五大联赛归一化
│   │   └── worldcup_normalizer.py  # 世界杯归一化
│   └── storage/
│       └── json_storage.py     # JSON 持久化工具
├── scripts/                    # 辅助脚本
├── logs/                      # 日志文件
├── .env                       # 环境变量（API 凭证）
└── requirements.txt
```

## 当前数据规模

### 五大联赛（2025/26 赛季）

| 联赛 | 代码 | 比赛数 |
|---|---|---|
| Premier League | E0 | 380 |
| La Liga | SP1 | 380 |
| Serie A | I1 | 380 |
| Bundesliga | D1 | 306 |
| Ligue 1 | F1 | 306 |
| **合计** | | **1752** |

来源：`data/processed/league/leagues_unified_*.json`

### 世界杯（1930 — 2022）

| 维度 | 数量 |
|---|---|
| 届（editions） | 22 |
| 比赛（matches） | 163 |
| 射手（scorers） | 22 |

来源：`data/processed/worldcup/worldcup_normalized_*.json`

### 2026 世界杯参赛名单（维基百科）

| 维度 | 数量 |
|---|---|
| 小组 | 12（A — L） |
| 球队 | 48 |
| 球员 | 1199（47队各25人，阿根廷24人） |

来源：`data/processed/worldcup/wc_2026_squad_normalized.json`

## 归一化数据格式

### 五大联赛比赛（league match）

```json
{
  "match_id": "D1_Bayern_Munich_RB_Leipzig_2025-08-22",
  "league": "Bundesliga",
  "league_code": "D1",
  "season": "2025/2026",
  "date": "2025-08-22",
  "time": "19:30",
  "home_team": "Bayern Munich",
  "away_team": "RB Leipzig",
  "home_score": 6,
  "away_score": 0,
  "result": "H",              // H=主队胜, D=平, A=客队胜
  "half_home_score": 3,
  "half_away_score": 0,
  "half_result": "H",
  "home_shots": 19,
  "away_shots": 12,
  "home_shots_on_target": 10,
  "away_shots_on_target": 1,
  "home_fouls": 13,
  "away_fouls": 13,
  "home_corners": 5,
  "away_corners": 5,
  "home_yellow_cards": 4,
  "away_yellow_cards": 1,
  "home_red_cards": 0,
  "away_red_cards": 0,
  "source": "football-data.co.uk",
  "raw_data": { ... }
}
```

### 世界杯比赛（worldcup match）

```json
{
  "year": 2022,
  "stage": "Final",
  "date": "2022-12-18",
  "home_team": "Argentina",
  "away_team": "France",
  "home_score": 3,
  "away_score": 3,
  "attendance": 88966,
  "stadium": "Lusail Stadium",
  "city": "Lusail",
  "referee": "S. Polling"
}
```

### 世界杯历届（worldcup edition）

```json
{
  "year": 2022,
  "host_country": "Qatar",
  "winner": "Argentina",
  "runner_up": "France",
  "third": "Croatia",
  "fourth": "Morocco",
  "goals_scored": 172,
  "matches_played": 64,
  "attendance": 3400000,
  "teams_count": 32
}
```

## 使用

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

编辑 `.env`：

```env
# Kaggle credentials（从 https://kaggle.com/account 下载）
KAGGLE_USERNAME=你的用户名
KAGGLE_KEY=你的key

# 数据路径（可选，默认如下）
DATA_RAW_PATH=data/raw
DATA_PROCESSED_PATH=data/processed
```

### 运行

```bash
# 完整 pipeline（采集 + 归一化）
python -m src.main --mode all

# 仅归一化（已有原始数据）
python -m src.main --mode pipeline

# 仅采集五大联赛
python -m src.main --mode collect-fifa

# 仅采集 Kaggle 数据
python -m src.main --mode collect-kaggle --keyword "worldcup football"

# URL 抓取（返回纯文本，不调用 LLM）
python -m src.main --mode scrape --url https://example.com
```

### 数据索引

每次 pipeline 运行后，`data/processed/index.json` 记录了最新数据集路径：

```json
{
  "generated_at": "2026-07-08T12:14:32",
  "datasets": {
    "leagues": {
      "file": "processed/league/leagues_unified_20260708_121431.json",
      "total_matches": 1752
    },
    "worldcup": {
      "file": "processed/worldcup/worldcup_normalized_20260708_121432.json",
      "editions": 22,
      "matches": 163,
      "scorers": 22
    },
    "wc2026_squad": {
      "file": "processed/worldcup/wc_2026_squad_normalized.json",
      "groups": 12,
      "teams": 48,
      "total_players": 1199
    }
  }
}
```

## 技术说明

- **归一化策略**：纯规则映射，无 LLM 依赖，速度快且结果可复现
- **编码处理**：自动处理 CSV 的 UTF-8 BOM 问题
- **SSL 容错**：下载时自动降级 SSL 验证，适配企业网络环境
- **去重**：世界杯数据按关键字段自动去重
- **持久化**：所有输出以时间戳命名，支持幂等重跑
