# DataForAgent

`DataForAgent` 是 WorldCupAgent 的数据采集和归一化子项目。它负责把公开足球数据整理为可被预测 Agent 稳定读取的 JSON 数据集；它本身不调用 LLM，也不直接给出比赛预测。

## 在整体架构中的位置

```text
公开数据源 -> collectors -> raw/ -> normalizer -> processed/ -> index.json
                                                        |
                                                        v
                         worldcup_agent.data_layer / LLM 预测上下文
```

主预测链通过 `worldcup_agent.data_layer.load_dataset()` 读取 `processed/index.json`。因此新增或替换数据集时，应先更新索引，而不是在 Agent 内硬编码文件名。

## 当前数据集

| 索引键 | 文件 | 当前索引规模 | 在预测中的作用 |
| --- | --- | --- | --- |
| `leagues` | `processed/league/leagues_unified_*.json` | 1,752 场 | 俱乐部表现的可扩展数据资产 |
| `worldcup` | `processed/worldcup/worldcup_normalized_*.json` | 22 届、163 场 | 历史世界杯覆盖度与赛前上下文 |
| `wc2026_squad` | `processed/worldcup/wc_2026_squad_normalized.json` | 12 组、48 队、1,199 名球员 | 当前预测赛事结构、名单、教练与球员信息的直接来源 |

`wc2026_squad` 当前有 47 支 25 人名单和阿根廷 24 人名单，共 1,199 名球员。这是源数据现状，不能自动视为 FIFA 最终报名名单。

## 数据来源与采集能力

| 来源 | 采集模块 | 内容 |
| --- | --- | --- |
| football-data.co.uk | `collectors/fifa_collector.py` | 五大联赛比赛结果与基础技术统计 |
| Kaggle FIFA World Cup 数据集 | `collectors/kaggle_collector.py` | 往届世界杯赛事、届次与射手信息 |
| URL / Wikipedia 资料 | `collectors/url_scraper.py` 与现有原始资料 | 2026 分组、球队、教练和名单补充信息 |

数据采集能力满足预测项目对历史战绩、球队分组与球员资料的输入需求，但当前并非实时数据服务。排名、伤病、最终名单和官方赛程仍需要独立的刷新策略与来源审计。

## 目录

```text
DataForAgent/
  data/
    raw/                 下载或抓取的原始文件
    processed/
      index.json         规范数据入口
      league/            五大联赛归一化结果
      worldcup/          历史世界杯与 2026 名单/分组
  src/
    collectors/          采集器
    normalizer/          规则化归一化器
    storage/             JSON 持久化工具
    pipeline.py          数据管道编排
    main.py              CLI 入口
```

## 使用

在 `DataForAgent` 目录运行：

```powershell
pip install -r requirements.txt
python -m src.main --mode all
```

`--mode all` 会重新拉取五大联赛数据、搜索 Kaggle 数据集并执行归一化。当前 Kaggle 步骤只负责发现候选数据集，不会自动将任意搜索结果映射成项目所需的三份世界杯历史原始文件；`wc2026_squad` 也由专用 HTML 解析器维护。因此，若要刷新 2026 分组与名单，请先更新 `data/raw/worldcup/wc_2026_squad_full.html`，再运行：

```powershell
python scripts/wc_2026_squad_normalizer.py
python -m src.main --mode pipeline
```

每次 `pipeline` 重建索引时会保留并重新登记 `wc2026_squad`，确保下游 Agent 仍能读取该数据集。

已有原始文件时，仅执行归一化：

```powershell
python -m src.main --mode pipeline
```

其他常用模式：

```powershell
python -m src.main --mode collect-fifa
python -m src.main --mode collect-kaggle --keyword "worldcup football"
python -m src.main --mode scrape --url https://example.com
```

Kaggle 凭证配置在 `DataForAgent/.env`，不要提交真实凭证：

```text
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_key
DATA_RAW_PATH=data/raw
DATA_PROCESSED_PATH=data/processed
```

## 数据契约

`processed/index.json` 必须包含 `datasets` 对象，每个数据集至少提供相对于 `DataForAgent/data/` 的 `file`。例如：

```json
{
  "datasets": {
    "wc2026_squad": {
      "file": "processed/worldcup/wc_2026_squad_normalized.json",
      "groups": 12,
      "teams": 48,
      "total_players": 1199
    }
  }
}
```

修改 schema、球队名称或分组字段时，必须同步验证 `worldcup_agent/llm_agent/context_builder.py` 和 `snapshot_builder.py` 的读取逻辑。当前 Agent 使用中文队名作为规范展示名，并将其映射到英文 enrichment；对于 enrichment 中没有的最新参赛队，`context_builder.py` 会回退到本地缓存的 `elo_live_ratings.json`，保证 48 支球队都有排名/Elo 证据。

## 质量与边界

- 归一化是确定性的规则处理，适合复现和审计。
- `raw/` 保留来源资料，`processed/` 才是下游读取入口。
- 数据规模不等同于数据实时性或预测准确率。
- 每次更新后应检查 JSON 可解析、索引路径存在、12 组 48 队和名单数量是否符合预期。
