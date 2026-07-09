# WorldCupAgent Frontend

这是世界杯冠军预测 Agent 的 Next.js 展示层。前端不直接调用 LLM，也不重新计算赛果，而是读取后端生成并同步过来的 prediction snapshot。

## 数据来源

前端读取：

```text
frontend/public/data/snapshots/latest.json
```

该文件由项目根目录脚本同步：

```powershell
python scripts\generate_and_sync.py --require-llm
```

或仅同步已有后端快照：

```powershell
python scripts\sync_snapshot_to_frontend.py
```

## 页面

- `/`: 冠军预测总览、Top 5 争冠队、更新时间、快捷入口
- `/schedule`: 小组积分、完整淘汰赛树、比赛详情弹窗
- `/teams`: 球队浏览和搜索入口
- `/data`: 数据来源、快照状态、比赛数量统计
- `/agent`: 最近一次 multi-agent 辅助运行结果和质量检查
- `/real-schedule`: 真实世界杯赛程信息说明
- `/compare`, `/match`, `/demo`, `/tournament`: 保留展示页面

## 核心文件

```text
src/app/page.tsx
src/app/schedule/page.tsx
src/app/data/page.tsx
src/app/agent/page.tsx

src/lib/tournament/loader/snapshot.loader.ts
src/lib/tournament/types/latest-json.types.ts
src/lib/world-cup-bracket/snapshot-to-bracket.ts
src/lib/world-cup-bracket/types.ts

src/components/dashboard/PredictionDashboard.tsx
src/components/world-cup-bracket/WorldCupBracketView.tsx
src/components/world-cup-bracket/GroupStageGrid.tsx
src/components/world-cup-bracket/KnockoutBracket.tsx
src/components/world-cup-bracket/MatchDetailDrawer.tsx
```

## 数据转换

后端 snapshot 与前端 UI 类型之间的转换集中在：

```text
src/lib/world-cup-bracket/snapshot-to-bracket.ts
```

该转换层负责：

- 将小组赛 match 转成可点击的 `BracketMatch`
- 将 `round_of_32`、16 强、8 强、半决赛、决赛转成赛程树
- 将 LLM 输出的 `llm_reasoning_factors` 映射到比赛详情弹窗
- 为中文球队名生成稳定 id，避免 React key 重复
- 将冠军概率转成首页 Top 5 展示数据

## 技术栈

- Next.js App Router
- React 19
- TypeScript
- Tailwind CSS
- lucide-react
- Recharts
- 自定义 i18n

## 本地运行

```powershell
cd frontend
npm run dev -- -p 3000
```

访问：

```text
http://localhost:3000
```

## 校验

```powershell
cd frontend
npm run lint
npm run build
```

## 维护约定

- 前端只展示 `latest.json` 中的预测结果，不在组件内重新预测或修正赛果。
- 新增 snapshot 字段时，同步更新 `latest-json.types.ts` 和 `snapshot-to-bracket.ts`。
- 新增可点击比赛信息时，确保 `MatchDetailDrawer` 可以展示对应 reasoning。
- 涉及时间格式时使用确定性格式，避免 SSR hydration mismatch。
