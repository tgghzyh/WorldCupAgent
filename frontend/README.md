# WorldCupAgent 前端说明

本目录是 2026 世界杯冠军预测 Agent 的前端展示层。当前前端把冠军预测总览、预测赛程树、比赛推理详情、真实官方赛程、球队入口和数据溯源拆成独立页面，避免单页信息过长，也便于后续接入真实 API。

## 功能概览

- **预测总览首页 `/`**
  - 冠军预测 Hero 卡片、夺冠概率环形进度图、三句核心推理摘要
  - Top 5 夺冠概率排行
  - 数据最后更新时间、手动刷新按钮和加载状态
  - 快捷入口：预测赛程树、球队搜索、数据溯源

- **预测赛程树 `/schedule`**
  - 12 个小组、48 支球队的小组积分展示
  - 32 强淘汰赛预测树，包含“小组前 2 名 + 8 个最佳第三名”的交叉晋级逻辑
  - 比赛节点展示国旗、队名、预测/实际比分、获胜概率
  - 已完赛置灰、进行中呼吸灯、未开赛正常显示
  - 支持滚轮缩放与拖拽平移

- **真实赛程 `/real-schedule`**
  - 基于联网核验后的 2026 世界杯真实赛程框架展示
  - 展示 48 队、104 场比赛、2026 年 6 月 11 日至 7 月 19 日、16 个承办城市等确认信息
  - 展示揭幕战、加拿大首战、美国首战、32 强开始、决赛等关键节点
  - 展示小组赛、32 强、16 强、四分之一决赛、半决赛、三四名决赛、决赛的阶段日期窗口
  - 保留 FIFA 官方页面等来源链接，并明确说明该页面不是 Agent 预测结果
  - 当前版本聚焦真实赛事日历、阶段窗口和承办城市；球队级实时对阵与赛果后续可接入官方 fixtures 数据源

- **比赛详情抽屉**
  - 双方球队、预测/实际比分、置信度
  - Agent 推理因素卡片与贡献权重条
  - Recharts 指标对比图
  - 数据来源链接与 Agent 推理时间戳

- **多语言**
  - 顶部导航提供 `EN / 中文` 切换
  - 主要页面和核心组件已接入中英文词典
  - 语言偏好保存到 `localStorage`

- **模块页**
  - `/teams`：球队搜索入口页，后续扩展球队画像
  - `/data`：数据溯源入口页，后续扩展快照与数据来源面板
  - `/tournament`、`/match`、`/compare`、`/demo`：保留已有展示页

## 技术栈

- **Framework**：Next.js App Router
- **Language**：TypeScript
- **Styling**：Tailwind CSS v4 + CSS Variables
- **UI 风格**：Shadcn/UI 风格的本地轻量组件
- **Chart**：Recharts
- **Icons**：Lucide React
- **Animation / Interaction**：CSS 动画 + 自定义缩放平移容器
- **i18n**：自定义 React Context，词典位于 `src/i18n`

> 注意：当前 package 版本为 Next.js 16 / React 19。用户需求中提到 Next.js 14，但本阶段没有强行降级依赖，以避免破坏现有 lockfile 和可运行状态。

## 核心目录与文件

```text
frontend/
  src/
    app/
      layout.tsx                 全局布局，挂载 Provider 与顶部导航
      page.tsx                   首页，渲染 PredictionDashboard
      schedule/page.tsx          预测赛程树页面
      real-schedule/page.tsx     真实官方赛程页面
      teams/page.tsx             球队搜索入口
      data/page.tsx              数据溯源入口

    components/
      SiteNavigation.tsx         全局导航栏与语言切换入口
      LanguageSwitcher.tsx       中英文切换组件
      dashboard/
        PredictionDashboard.tsx  首页预测总览组件

      world-cup-bracket/
        WorldCupBracketView.tsx  预测赛程树页面容器
        GroupStageGrid.tsx       12 个小组积分展示
        KnockoutBracket.tsx      32 强淘汰赛树
        MatchNode.tsx            单场比赛节点
        MatchDetailDrawer.tsx    比赛详情抽屉
        ZoomPanCanvas.tsx        缩放与拖拽平移画布

      ui/
        badge.tsx                Shadcn 风格 Badge
        button.tsx               Shadcn 风格 Button
        card.tsx                 Shadcn 风格 Card

    lib/
      real-schedule.ts           真实赛程结构化数据、承办城市、来源链接
      world-cup-bracket/
        types.ts                 前端预测赛程树数据结构定义
        mock-data.ts             Mock 数据示例，组件通过 props 消费
      utils.ts                   cn 等通用工具函数

    i18n/
      index.tsx                  I18nProvider、useI18n、t 函数
      en.json                    英文词典
      zh.json                    中文词典

    styles/
      globals.css                全局样式、主题变量、Tailwind theme 映射
```

## 数据设计原则

预测 Bracket 和 Dashboard 使用 `frontend/src/lib/world-cup-bracket/mock-data.ts` 提供的 Mock 数据。组件本身不发起 API 请求，所有预测数据均通过 props 传入。

真实赛程页面使用 `frontend/src/lib/real-schedule.ts` 中的结构化静态数据，数据来源来自联网核验后的公开赛程信息。该模块与预测 Mock 数据分离，避免把现实赛程和 Agent 推演结果混在一起。当前版本先覆盖赛事日历、阶段窗口、承办城市和关键节点；球队级 fixtures 与赛果适合在后续接入官方实时数据源。

这样做的原因：

- 展示层可以独立开发和测试
- 后续可以无缝替换为 `latest.json`、FastAPI 或实时模拟结果
- 避免 UI 组件与后端数据获取逻辑耦合
- 真实赛程与预测赛程拥有不同可信度语义，必须在产品上清晰分离

关键预测类型定义见 `src/lib/world-cup-bracket/types.ts`。

## 本地运行

```bash
cd frontend
npm install
npm run dev
```

访问：

```text
http://localhost:3000
```

生产构建验证：

```bash
npm run build
```

## 维护约定

以后修改前端模块时，请同步更新本 README，至少记录：

- 新增或删除的页面路由
- 新增的重要组件
- 数据结构变化
- i18n 词典新增范围
- 影响运行或构建的依赖变化

当前 README 最后更新：新增真实赛程页面、导航入口、真实赛程数据模块，并修复中英文词典结构。
