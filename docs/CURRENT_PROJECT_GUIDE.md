# WorldCupAgent 当前项目指南

本文记录当前已经跑通的主链路，优先级高于仓库中较早的产品草稿和历史设计文档。

## 当前阶段

项目已经进入“LLM-first 逐场预测 + 完整赛事蒙特卡洛模拟 + 前端可视化展示”的阶段。

当前主链路是：

```text
DataForAgent 赛前数据
  -> worldcup_agent/llm_agent 重建赛事结构
  -> 球队画像 LLM 提炼赛前实力特征
  -> 概率模型提供胜平负基线，预测 LLM 逐场输出比分、胜负、概率和原因
  -> 反思 LLM 复核概率、比分、证据和晋级路径
  -> Monte Carlo 模拟完整小组赛和淘汰赛，统计晋级与冠军分布
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
team_intelligence.py 按小组调用 LLM，提炼球队实力分项、优势、风险和关键球员
probability_model.py 用球队画像、Elo、排名和主队调整计算可复算的胜平负基线
monte_carlo.py       基于球队画像概率与 LLM 赛果进行完整赛事抽样
predictor.py         约束 LLM 输出固定 JSON，并清洗为 MatchPrediction
reflection.py        复核每场预测的概率、比分、证据和晋级路径一致性
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
3. 调用球队画像 LLM、概率模型、逐场预测 LLM 和反思 LLM
4. 运行完整赛事 Monte Carlo，写入冠军与晋级概率分布
5. 默认运行 multi-agent 辅助层
6. 将 snapshot 同步到前端 public 目录

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

### 仅重跑 Monte Carlo

```powershell
python scripts\run_monte_carlo.py --runs 10000 --sync-frontend
```

该命令复用当前快照中的球队画像和逐场预测概率，不会重新请求 LLM。

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
MONTE_CARLO_RUNS=10000
MONTE_CARLO_SEED=20260710
```

## 当前实现亮点

- 从 DataForAgent 正确来源重建分组、赛程和参赛球队。
- 球队画像 LLM 先提炼赛前特征，再由概率模型和 LLM 逐场推演，而不是用写死规则直接给冠军。
- Simulation 已执行真实的多次完整赛事抽样，而不是读取快照或 softmax 伪造冠军概率。
- 小组赛结果会影响积分榜，积分榜会影响 32 强对阵。
- 淘汰赛逐轮推进，后续比赛由前一轮胜者动态生成。
- Teams 页面展示球队画像；比赛详情展示 LLM 原因、概率模型基线和反思结论。
- 已处理中文球队名导致前端 React key 重复的问题。

## 仍需完善

优先级从高到低：

1. 增加 LLM 输出 JSON Schema 校验、自动修复 prompt 和失败重试。
2. 增加断点续跑，避免完整 104 场预测中途失败后重复调用。
3. 为小组积分、32 强生成、中文球队 id、冠军概率写自动化测试。
4. 将 `prediction/` 旧入口和过期文档归档或标注为 legacy。
5. 扩展数据源：FIFA 排名、ELO、伤病、旅行距离、主客场/承办城市、近期国家队比赛。
6. 统一 snapshot schema，减少后端快照、前端类型和 multi-agent 输出之间的转换成本。
