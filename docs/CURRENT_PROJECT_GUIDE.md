# WorldCupAgent 当前项目指南

本文记录当前已经跑通的主链路，优先级高于仓库中较早的产品草稿和历史设计文档。

## 当前阶段

项目已经进入“LLM-first 逐场预测 + 前端可视化展示”的阶段。

当前主链路是：

```text
DataForAgent 赛前数据
  -> worldcup_agent/llm_agent 重建赛事结构
  -> LLM 逐场预测比分、胜负、概率和原因
  -> data/snapshots/latest.json
  -> scripts 同步到 frontend/public
  -> Next.js 前端展示
```

`worldcup_agent/multi_agent` 仍保留，但现在定位为辅助校验和摘要层，不再是核心赛果生成入口。

## 目录职责

### DataForAgent/

`DataForAgent` 是世界杯开打前的数据区，负责提供可被 Agent 使用的原始/归一化数据。

当前关键索引：

```text
DataForAgent/data/processed/index.json
```

当前使用的数据集：

- `wc2026_squad`: 2026 参赛球队、小组、教练、球员名单
- `worldcup`: 历史世界杯比赛数据
- `leagues`: 联赛比赛归一化数据

其中 `DataForAgent/data/processed/worldcup/wc_2026_squad_normalized.json` 是当前分组、球队和名单信息的权威来源。

### worldcup_agent/llm_agent/

这是当前核心 Agent 实现。

```text
context_builder.py   把 DataForAgent、球队资料、教练/球员知识组装成单场比赛上下文
llm_client.py        读取 .env.local 并调用兼容 OpenAI 协议的 LLM 服务
predictor.py         约束 LLM 输出固定 JSON，并清洗为 MatchPrediction
snapshot_builder.py  从球队名单重建小组赛、32 强、后续淘汰赛结构
snapshot_writer.py   按赛事顺序逐场预测、重算积分、推进淘汰赛、写入快照
main.py              独立运行 LLM 预测层的 CLI 入口
```

LLM 每场比赛需要输出：

- `winner`: `home | away | draw`
- `predicted_score`: 如 `2-1`
- `home_win_prob / draw_prob / away_win_prob`
- `confidence`
- `reasoning`
- `reasoning_factors`
- `llm_model / llm_provider / llm_prompt_version`

这些字段会被写入 `latest.json`，并在前端比赛弹窗中展示。

### worldcup_agent/multi_agent/

这是辅助 Agent 层。

当前包含：

- `DataAgent`: 加载 DataForAgent 和 canonical snapshot
- `AnalysisAgent`: 基于积分、净胜球、冠军概率生成队伍强度分
- `SimulationAgent`: 生成赛事级冠军摘要
- `ReflectionAgent`: 检查数据与预测完整性
- `ExplainerAgent`: 生成冠军预测说明
- `QualityAgent`: 输出质量检查分数

该层输出到：

```text
data/multi_agent/multi_agent_output_*.json
```

前端 `/agent` 页面会读取最近一次 multi-agent 输出，用于展示 Agent trace 和质量检查。

### data/

`data` 是运行输出目录，不是赛前原始数据源。

关键文件：

```text
data/snapshots/latest.json
data/multi_agent/multi_agent_output_*.json
```

`data/snapshots/latest.json` 是后端 canonical prediction snapshot。

### frontend/

`frontend` 是 Next.js 前端展示层。

主要页面：

- `/`: 冠军预测总览、Top 5 争冠队、更新时间
- `/schedule`: 小组积分、完整淘汰赛树、比赛详情弹窗
- `/teams`: 球队浏览入口
- `/data`: 数据来源与快照状态
- `/agent`: 最近一次 multi-agent 运行结果
- `/real-schedule`: 真实赛程信息说明页

前端静态读取：

```text
frontend/public/data/snapshots/latest.json
```

该文件由脚本从 `data/snapshots/latest.json` 同步而来。

## 常用命令

### 完整生成并同步

```powershell
python scripts\generate_and_sync.py --require-llm
```

该命令会：

1. 校验 DataForAgent 数据集
2. 校验当前 snapshot
3. 调用 LLM-first 逐场预测层
4. 默认运行 multi-agent 辅助层
5. 将 snapshot 同步到前端 public 目录

### 小批量测试 LLM

```powershell
python scripts\generate_and_sync.py --require-llm --llm-match-limit 10 --skip-agent
```

适合先验证 API 连通性和输出格式。

### 只重建快照，不调用真实 LLM

```powershell
$env:LLM_DISABLE="1"
python scripts\generate_and_sync.py --skip-agent
Remove-Item Env:\LLM_DISABLE
```

此模式会使用本地 fallback，用于快速验证数据结构和前端页面。

### 启动前端

```powershell
cd frontend
npm run dev -- -p 3000
```

### 前端校验

```powershell
cd frontend
npm run lint
npm run build
```

## 配置约定

LLM 配置放在项目根目录 `.env.local`。该文件已被 `.gitignore` 忽略，不应提交真实密钥。仓库提供了 `.env.example` 作为占位模板。

示例：

```text
LLM_PROVIDER=xfyun-maas
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://maas-api.cn-huabei-1.xf-yun.com/v2
LLM_MODEL=xop35qwen2b
LLM_MAX_RETRIES=5
LLM_RETRY_BASE_SECONDS=3
LLM_REQUEST_DELAY_SECONDS=1.2
LLM_TIMEOUT_SECONDS=120
```

## 当前实现亮点

- 从 DataForAgent 正确来源重建分组、赛程和参赛球队。
- LLM 逐场推演，而不是用写死规则直接给冠军。
- 小组赛结果会影响积分榜，积分榜会影响 32 强对阵。
- 淘汰赛逐轮推进，后续比赛由前一轮胜者动态生成。
- 前端可展示小组赛和淘汰赛的 LLM 原因。
- 已处理中文球队名导致前端 React key 重复的问题。

## 仍需完善

优先级从高到低：

1. 增加 LLM 输出 JSON Schema 校验、自动修复 prompt 和失败重试。
2. 增加断点续跑，避免完整 104 场预测中途失败后重复调用。
3. 为小组积分、32 强生成、中文球队 id、冠军概率写自动化测试。
4. 将 `prediction/` 旧入口和过期文档归档或标注为 legacy。
5. 提升冠军概率模型。目前最终冠军来自单一路径推演，概率分布仍偏薄，后续可结合多次 LLM/Monte Carlo 采样。
6. 扩展数据源：FIFA 排名、ELO、伤病、旅行距离、主客场/承办城市、近期国家队比赛。
7. 统一 snapshot schema，减少后端快照、前端类型和 multi-agent 输出之间的转换成本。
