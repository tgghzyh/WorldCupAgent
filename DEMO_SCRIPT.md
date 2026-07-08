# WC2026 Explainable Prediction Page — Demo Script
# Sprint: Agent Explainability & Demo Experience
# Duration: 2–3 minutes

## 启动命令

```bash
cd C:\Users\43021\Desktop\ART\WorldCupAgent
streamlit run explainable_page.py
# 或一键启动 + 公开链接:
streamlit run explainable_page.py --server.headless true
```

## 公开访问（ngrok）

```bash
# 终端1: 启动服务
cd C:\Users\43021\Desktop\ART\WorldCupAgent
streamlit run explainable_page.py --server.port 8501

# 终端2: 转发
ngrok http 8501
# 复制 https://xxx.ngrok.io 分享给评委
```

---

## 演示顺序（2-3 分钟）

### 第 1 分钟：整体感知

1. **打开页面** → 顶部 Agent Identity Banner
   - 展示：LangGraph · Qwen LLM · ELO System · Monte Carlo
   - 话术："这是一个基于 LangGraph 的多步推理 Agent，不是简单的 API 调用"

2. **Agent 工作流 Timeline**（侧边栏）
   - 展示 6 个真实步骤：Plan → Search → Load Data → Reason → Predict → Save
   - 话术："每个步骤对应 agent.py 中真实的方法，不是伪造的流程图"

3. **Hero 每日简报**
   - 展示 headline + snapshot metadata
   - 话术："每天自动生成，包含生成时间、版本号、过期时间"

---

### 第 2 分钟：核心功能

4. **72 场比赛卡片**
   - 选择一场比赛（如 Argentina vs Mexico）
   - 展示三段胜率条（深蓝=主胜，灰=平局，橙=客胜）
   - 展示 confidence badge
   - 话术："胜率来自 ELO expected_score 模型，confidence 由概率离散度计算"

5. **展开推理因子**（🔍 查看推理因子）
   - 展示 ELO Rating Advantage（42%）+ FIFA Ranking Advantage（26%）
   - 话术："每场比赛有 2 个因子，按贡献度排序，附带原始证据数值"

6. **Factor Attribution 总览**（Tab 2）
   - 展示所有比赛的因子聚合统计
   - 话术："ELO 是最主导的因素（42%），FIFA 排名其次（26%）"

---

### 第 3 分钟：细节与公信力

7. **今日变化**（Tab 3）
   - 展示与上一快照的概率差异
   - 话术："系统每天对比，变化超过 0.5pp 才记录，确保只展示有意义的变化"

8. **预测元数据**（展开卡片内）
   - 展示 snapshot_id / expires_at / prediction_version / knowledge_version
   - 话术："每个预测都有版本号，可追溯、可复现"

9. **筛选功能**（侧边栏）
   - 按可信度筛选（高/中/低）
   - 按球队搜索（如搜索 Brazil）
   - 话术："72 场比赛均可筛选，方便深入研究特定球队"

---

## 评分项对照

| 评分项 | 演示内容 |
|--------|---------|
| **可视化呈现** | 深色主题卡片、胜率条、因子条、Timeline、Badge |
| **系统架构可解释性** | Agent Identity Banner、6步工作流Timeline、Metadata |
| **创新展示** | Factor Attribution 图表、Graceful Degradation Optional 组件 |
| **技术文档质量** | Feature Freeze 声明、代码注释、Step-by-step 注释 |
| **预测逻辑严谨性** | ELO 差值证据、数值精确到4位小数、版本号追踪 |

---

## 禁止演示的内容

- ~~修改 ELO 算法~~
- ~~调整 Monte Carlo 模拟次数~~
- ~~改动 Snapshot Schema~~
- ~~新增 champion_probabilities~~（展示 placeholder 即可）

---

## 快速验证（启动前）

```bash
# 确认快照存在
python validate_snapshot.py

# 确认语法无误
python -m py_compile explainable_page.py
```
