# WorldCupAgent Frontend

Next.js 展示层。前端不调用 LLM、不重新计算赛果；它读取由后端 Agent 生成的规范快照，并把冠军预测、球队画像、赛程树、比分和推理依据展示给用户。

## 数据流

```text
data/snapshots/latest.json
  -> scripts/sync_snapshot_to_frontend.py
  -> public/data/snapshots/latest.json
  -> snapshot.loader.ts
  -> snapshot-to-bracket.ts
  -> Dashboard / Schedule / MatchDetailDrawer
```

完整后端流程会自动同步前端快照：

```powershell
python scripts\generate_and_sync.py --require-llm
```

只同步已有快照：

```powershell
python scripts\sync_snapshot_to_frontend.py
```

## 页面

| 路由 | 用途 |
| --- | --- |
| `/` | 冠军预测总览、争冠队、更新时间和快捷入口 |
| `/schedule` | 小组积分、32 强淘汰赛树，以及可点击的比赛节点 |
| `/teams` | 48 支球队的 LLM 实力画像、优势风险和关键球员 |
| `/data` | DataForAgent、预测快照和同步状态 |
| `/agent` | multi-agent 辅助运行记录、数据覆盖与质量检查 |
| `/real-schedule` | 与预测树分离的真实赛事日历说明 |
| `/match` | 单场预测展示页 |
| `/tournament` | 冠军晋级路径展示页 |
| `/demo` | 项目演示引导页 |

赛程页点击小组赛或淘汰赛比赛后，`MatchDetailDrawer` 展示：预测比分、双方胜率、LLM 推理摘要、结构化原因因素、概率模型基线、LLM 反思、数据对比和推理时间。

## 核心实现

```text
src/lib/tournament/loader/snapshot.loader.ts
  读取 public 快照

src/lib/tournament/types/latest-json.types.ts
  后端快照 TypeScript 类型

src/lib/world-cup-bracket/snapshot-to-bracket.ts
  将快照转换为前端赛程树 UI 模型

src/components/world-cup-bracket/
  WorldCupBracketView.tsx  赛程主视图
  GroupStageGrid.tsx       分组、积分与小组赛详情入口
  KnockoutBracket.tsx      淘汰赛树
  MatchNode.tsx            可点击比赛节点
  MatchDetailDrawer.tsx    推理详情弹窗
  CountryFlag.tsx          国家旗帜展示

src/components/dashboard/PredictionDashboard.tsx
  首页冠军与争冠队概览
```

## 快照字段

前端依赖以下后端字段：

- 基础赛果：`predicted_score`、`winner`、`home_win_prob`、`draw_prob`、`away_win_prob`、`confidence`
- 解释：`reasoning`、`llm_reasoning_factors`、`llm_reflection`
- 概率基线：`probability_model`
- 球队画像：`team_intelligence`
- 模拟结果：`simulation`、`monte_carlo_simulations`、`monte_carlo_modal_champion`

其中 `champion` 是确定性赛程树的决赛胜者；首页的“蒙特卡洛夺冠概率 Top 5”读取 `simulation.champion_probabilities`，用于表达不确定性分布，不能替代冠军路径页的单一路径结论。

新增后端字段时，应同步更新 `latest-json.types.ts` 与 `snapshot-to-bracket.ts`，并为缺失字段保留明确的降级显示。

## 国际化与视觉约定

- UI 使用自定义 i18n，翻译资源在 `src/i18n/zh.json` 与 `src/i18n/en.json`。
- 语言选择写入 `localStorage`，首屏以确定性默认语言渲染，避免 hydration mismatch。
- 中文模式会翻译静态界面、轮次、小组标签、晋级规则与比赛详情控件；LLM 原始推理文本按快照内容展示，不由前端改写。
- 球队以国旗替代英文三字母缩写；FlagCDN 已在 `next.config.ts` 配置为远程图片来源。

## 本地运行

```powershell
cd frontend
npm install
npm run dev -- -p 3000
```

访问 `http://localhost:3000`。

## 校验

```powershell
cd frontend
npm run lint
npm run build
```

## 展示边界

前端忠实展示后端快照，不在组件中修正预测。赛制、比分或胜者规则变更后，必须通过根目录的完整生成流程重新生成并同步快照；不要在前端掩盖数据问题。`/real-schedule` 也不应与 Agent 预测赛程混为一谈。
