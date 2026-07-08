# WorldCupAgent 当前项目指南

本文档记录当前已经跑通的项目主链路，优先级高于仓库中较早的架构草稿和历史说明。

## 当前阶段

项目已经进入“主链路闭环 + 前端展示接入”阶段。

已经跑通的链路是：

```text
DataForAgent 初始数据
  -> worldcup_agent 数据读取与 multi-agent 管线
  -> data/snapshots/latest.json 和 data/multi_agent/*.json
  -> scripts 同步到 frontend/public
  -> Next.js 前端页面展示
```

## 目录职责

### DataForAgent/

`DataForAgent` 是世界杯开赛前的初始数据区，负责采集、清洗和归一化上游数据。

当前主索引：

```text
DataForAgent/data/processed/index.json
```

当前索引中的数据集：

- `leagues`: 联赛比赛归一化数据
- `worldcup`: 历史世界杯归一化数据
- `wc2026_squad`: 2026 参赛队伍和球员名单归一化数据

### worldcup_agent/

`worldcup_agent` 是预测和 Agent 推理系统。

当前关键入口：

```text
worldcup_agent/data_layer/dataforagent_loader.py
worldcup_agent/multi_agent/main.py
worldcup_agent/multi_agent/agents.py
```

其中 `dataforagent_loader.py` 提供统一读取入口：

```python
from worldcup_agent.data_layer import load_dataset

worldcup = load_dataset("worldcup")
squad = load_dataset("wc2026_squad")
```

`multi_agent` 当前包含 6 个可运行 agent：

- `DataAgent`: 读取 DataForAgent 和当前预测快照
- `AnalysisAgent`: 生成球队强度分数
- `SimulationAgent`: 生成赛事级预测摘要
- `ReflectionAgent`: 做一致性检查
- `ExplainerAgent`: 生成解释文本
- `QualityAgent`: 做最终质量检查

### data/

`data` 是预测系统的运行输出区，不是原始数据源。

关键文件：

```text
data/snapshots/latest.json
data/multi_agent/multi_agent_output_*.json
```

`data/snapshots/latest.json` 是当前前端使用的主预测快照。

`data/multi_agent/*.json` 是 multi-agent 每次运行的可解释执行记录，包含运行时间、质量分数、48 支球队状态、Agent trace、数据来源摘要、冠军预测摘要和质量检查结果。

### frontend/

`frontend` 是 Next.js 前端。

当前主要页面：

- `/`: 预测总览
- `/schedule`: 预测赛程树
- `/real-schedule`: 真实官方赛程信息
- `/tournament`: 冠军路径
- `/teams`: 球队入口
- `/data`: 数据链路状态
- `/agent`: 最近一次 multi-agent 运行结果
- `/compare`: 快照变化对比
- `/match`: 比赛详情示例

前端静态读取：

```text
frontend/public/data/snapshots/latest.json
```

该文件由脚本从 `data/snapshots/latest.json` 同步而来。

## 常用命令

### 校验数据、运行 Agent、同步前端

在项目根目录运行：

```bash
python scripts\generate_and_sync.py
```

该命令会：

1. 校验 `DataForAgent/data/processed/index.json`
2. 校验所有 indexed dataset 可读取
3. 校验 `data/snapshots/latest.json`
4. 运行 multi-agent 管线
5. 写入 `data/multi_agent/multi_agent_output_*.json`
6. 同步 `data/snapshots/latest.json` 到前端 public 目录

### 只同步已有预测快照

```bash
python scripts\generate_and_sync.py --skip-agent
```

### 同步后同时构建前端

```bash
python scripts\generate_and_sync.py --build
```

### 启动前端开发服务

```bash
cd frontend
npm run dev -- -p 3000
```

然后打开：

```text
http://localhost:3000
http://localhost:3000/agent
http://localhost:3000/data
```

### 前端校验

```bash
cd frontend
npm run lint
npm run build
```

当前状态：`lint` 和 `build` 均通过。

## 当前数据事实

最近一次完整运行结果：

```text
data/multi_agent/multi_agent_output_20260708_094647.json
```

该次运行摘要：

- Quality Score: 100%
- Teams Loaded: 48
- Simulation Runs: 10,000
- Champion Pick: Argentina
- DataForAgent datasets: `leagues`, `wc2026_squad`, `worldcup`

## 重要约定

### DataForAgent 和 data 不合并

二者职责不同：

- `DataForAgent`: 初始数据、采集数据、归一化数据
- `data`: 预测系统运行后的快照、缓存、Agent 输出

当前不建议合并。

### 前端只展示，不重新预测

前端可以做格式化、排序、筛选、布局和可视化，但不应该重新计算预测结果。

预测结果应来自：

```text
data/snapshots/latest.json
data/multi_agent/*.json
```

### 当前 canonical snapshot

当前前端主展示仍以 `data/snapshots/latest.json` 为 canonical prediction snapshot。

`data/multi_agent/*.json` 用来展示 Agent 运行过程和质量检查，不替代主预测快照。

## 下一步建议

优先级从高到低：

1. 完善 `/teams` 页面，把 48 支球队、分组、强度分数和球员覆盖数据接入。
2. 统一 snapshot schema，减少旧 `prediction/agent.py` schema 和当前 `latest.json` schema 的差异。
3. 修复或隔离 `multi_agent` 中仍未接入主入口的实验模块，例如 cognitive model、goal agent、debate mechanism。
4. 清理历史乱码文档，保留当前指南作为主入口。
5. 将 `scripts/generate_and_sync.py` 扩展成更完整的 release/check 命令。
