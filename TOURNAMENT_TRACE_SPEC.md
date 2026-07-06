# FIFA World Cup 2026 — Tournament Traceability Specification

**Sprint**: PE-0.5 · **Author**: Cursor AI (Qoder) · **Date**: 2026-07-05
**Status**: VERIFIABILITY LAYER DESIGN COMPLETE

---

## 元声明

- 本文档为 **PE-0.5 补充文档**，与 `TOURNAMENT_RULE_SPEC.md` 共同构成完整规则体系
- 核心目标：为每一场 R32 对阵提供**可逐行验证的推理链**
- 在 PE-0.5 经人工确认之前，**禁止进入 PE-1**

---

## 一、设计动机

### 问题

现有 Constraint Engine 存在**可解释性缺口**：

```
❌ 输入 Standings
❌ 输出 R32 Matches
❌ 中间过程：黑盒
```

评委无法验证：
- "为什么这场是 A组冠军 vs 第三名#3，而不是第三名#5？"
- "为什么这个第三名出现在上半区而不是下半区？"

### 目标

```
✅ 输入 Standings
✅ Constraint Engine（确定性）
✅ 输出：Matches + Rule Traces（可解释证据链）
✅ 评委可逐行验证
```

---

## 二、Match Trace Schema

### 2.1 基本结构

```python
@dataclass
class MatchTrace:
    """
    每场比赛的解释性记录。
    包含：比赛信息 + 完整推理链
    """

    # 身份
    match_id: str                    # "r32_01", ..., "r32_16"
    match_type: str                  # "runner_up_derby" | "champion_vs_third"

    # 参赛球队
    home_team: str                   # 球队名（来自 standings）
    away_team: str                   # 球队名（来自 standings）

    # 来源信息
    home_slot: str                   # "1A" | "2A" | "3A"
    away_slot: str                   # "1B" | "3E" | "2F" | ...

    # 推理链（核心）
    rule_trace: list[str]            # 逐行动作记录
    constraint_checks: list[str]      # 通过的约束检查
    qualification_reason: str         # away_team 为什么能参加 R32

    # 第三名特有（如果适用）
    third_place_rank: int | None     # 1–12（如果是第三名球队）
    tiebreak_steps: list[str] | None # 如果积分相同，平局打破步骤
```

### 2.2 输出示例

```python
# 示例：R32 Match #74 (r32_01)
MatchTrace(
    match_id="r32_01",
    match_type="champion_vs_third",
    home_team="Germany",           # 1E（E组冠军）
    away_team="Ecuador",           # 3B（实际：E组第三名在B组逻辑下）
    home_slot="1E",
    away_slot="3B",
    rule_trace=[
        "STEP 1: E组排名计算完成 → 冠军=Germany (9pts, +5 GD)",
        "STEP 2: 第三名晋级排名 → Ecuador 排第3 (4pts, +1 GD)",
        "STEP 3: 1E 位置分析 → 允许对阵第三名组别: [A, B, C, D, F]",
        "STEP 4: 候选第三名交集 → 3B(Ecuador) ∈ [A,B,C,D,F] ✅",
        "STEP 5: 排名顺序 → 3B(Ecuador) = 排名最高的合法第三名 ✅",
        "STEP 6: 同组检查 → Germany ∉ Group B（Ecuador 同组） ✅",
    ],
    constraint_checks=[
        "C1: 32队各出现一次 ✅",
        "C2: 同组不对阵 ✅（Germany=Ecuador 不同组）",
        "C3: 位置互斥 ✅（3B 未被其他位置使用）",
    ],
    qualification_reason="Ecuador: 第3名，4pts，积分排12支第三名中第3位",
    third_place_rank=3,
    tiebreak_steps=[
        "TIERANK 1: points — Ecuador 4pts = 直接晋级线",
        "TIERANK 2: 不需要净胜球打破（无同分对手）",
    ],
)
```

---

## 三、R32 Slot System（16个位置）

### 3.1 设计原则

**Slot = 位置，不是配对表。**

每个 Slot 定义的是：
- **谁有资格进入这个位置**（资格条件）
- **如何从候选中选择**（排序规则）

而不是：
- 硬编码"Slot 1 = X vs Y"

### 3.2 Slot 定义表

| Slot ID | Slot 名称 | 类型 | 资格条件 | 选择规则 |
|---|---|---|---|---|
| S01 | 1A vs 3rd | Champion vs Third | 1A 冠军 + 第三名 | 允许组：C,E,F,H,I → 选排名最高 |
| S02 | 2A vs 2B | Runner-Up Derby | 2A + 2B | 固定，无需选择 |
| S03 | 1C vs 2F | Fixed | 1C 冠军 + 2F | 固定，无需选择 |
| S04 | 1D vs 3rd | Champion vs Third | 1D 冠军 + 第三名 | 允许组：B,E,F,I,J → 选排名最高 |
| S05 | 2D vs 2G | Runner-Up Derby | 2D + 2G | 固定，无需选择 |
| S06 | 1E vs 3rd | Champion vs Third | 1E 冠军 + 第三名 | 允许组：A,B,C,D,F → 选排名最高 |
| S07 | 2E vs 2I | Runner-Up Derby | 2E + 2I | 固定，无需选择 |
| S08 | 1F vs 2C | Fixed | 1F 冠军 + 2C | 固定，无需选择 |
| S09 | 1G vs 3rd | Champion vs Third | 1G 冠军 + 第三名 | 允许组：A,E,H,I,J → 选排名最高 |
| S10 | 1H vs 2J | Fixed | 1H 冠军 + 2J | 固定，无需选择 |
| S11 | 1I vs 3rd | Champion vs Third | 1I 冠军 + 第三名 | 允许组：C,D,F,G,H → 选排名最高 |
| S12 | 1J vs 2H | Fixed | 1J 冠军 + 2H | 固定，无需选择 |
| S13 | 1K vs 3rd | Champion vs Third | 1K 冠军 + 第三名 | 允许组：D,E,I,J,L → 选排名最高 |
| S14 | 1L vs 3rd | Champion vs Third | 1L 冠军 + 第三名 | 允许组：E,H,I,J,K → 选排名最高 |
| S15 | 2K vs 2L | Runner-Up Derby | 2K + 2L | 固定，无需选择 |
| S16 | 1B vs 3rd | Champion vs Third | 1B 冠军 + 第三名 | 允许组：E,F,G,I,J → 选排名最高 |

**注：** Slot 顺序与 Match 编号不完全对应，Match 编号由赛程决定（Wikipedia M73-M88），Slot ID 是内部逻辑编号。

### 3.3 第三名选择算法（每 Slot）

```python
def select_third_for_slot(
    slot_id: str,
    allowed_groups: list[str],
    third_place_teams: list[dict],      # 已排序的第三名列表
    used_thirds: set[str],
) -> dict | None:
    """
    给定一个 Slot，从候选第三名中选择一个。

    选择规则（优先级）：
    1. 必须在 allowed_groups 中
    2. 必须未被使用（位置互斥）
    3. 按第三名排名（points → GD → goals → fair_play → FIFA rank）取最高位

    Returns: 选中的第三名 dict 或 None
    """
    candidates = [
        t for t in third_place_teams
        if t["group"] in allowed_groups
        and t["group"] not in used_thirds
    ]
    # candidates 已按排名排序（rank 1 = 最好）
    return candidates[0] if candidates else None
```

---

## 四、第三名排名 Trace

### 4.1 第三名排名数据结构

```python
@dataclass
class ThirdPlaceRecord:
    """每支第三名球队的完整排名记录"""

    team: str
    group: str                        # "A", "B", ..., "L"
    points: int                       # 积分
    goal_diff: int                    # 净胜球
    goals_scored: int                 # 总进球
    fair_play: int                    # 公平竞赛分（越高越好）
    fifa_rank: int                    # FIFA世界排名（越小越好）

    # 排名字段（计算后）
    rank: int                         # 1–12（1=最好）
    tiebreak_notes: list[str]         # 如果与其他队积分相同，记录打破步骤
    is_qualifier: bool               # True = 进入 R32，False = 淘汰


@dataclass
class ThirdPlaceRankingTrace:
    """第三名排名完整推理链"""

    all_thirds: list[ThirdPlaceRecord]   # 12支第三名（已排序）
    top8: list[ThirdPlaceRecord]         # 晋级前8
    bottom4: list[ThirdPlaceRecord]       # 淘汰后4

    # 逐队推理链
    ranking_steps: list[dict]             # 每步操作记录
```

### 4.2 第三名排名示例

```python
ThirdPlaceRankingTrace(
    all_thirds=[
        ThirdPlaceRecord(
            team="DR Congo", group="K", points=4, goal_diff=-1,
            goals_scored=3, fair_play=0, fifa_rank=62, rank=1,
            tiebreak_notes=[],
            is_qualifier=True,
        ),
        ThirdPlaceRecord(
            team="Sweden", group="F", points=4, goal_diff=0,
            goals_scored=4, fair_play=0, fifa_rank=25, rank=2,
            tiebreak_notes=["与 Ghana(Ecuador) 同分 → 无需打破（都已晋级前8）"],
            is_qualifier=True,
        ),
        # ... 共12条
    ],
    top8=[...],  # 晋级 R32 的8支第三名
    bottom4=[...],  # 淘汰的4支

    ranking_steps=[
        {
            "action": "COLLECT",
            "description": "收集12支第三名球队数据",
        },
        {
            "action": "SORT",
            "description": "按 [points, goal_diff, goals_scored, fair_play, fifa_rank] 降序排序",
            "key_used": "points",
        },
        {
            "action": "CHECK_TIES",
            "description": "检查并列情况",
            "ties_found": [
                {"rank": 2, "teams": ["Sweden", "Ghana", "Ecuador"], "resolved_by": "goal_diff（瑞典=0 > 厄瓜多尔=0 > 加纳=0，FIFA排名打破）"},
            ],
        },
        {
            "action": "SLICE",
            "description": "取前8名 → 晋级",
            "qualifiers": ["DR Congo", "Sweden", "Ecuador", "Ghana", "Bosnia", "Algeria", "Paraguay", "Senegal"],
        },
        {
            "action": "MARK_ELIMINATED",
            "description": "后4名 → 淘汰",
            "eliminated": ["Iran", "South Korea", "Scotland", "Uruguay"],
        },
    ],
)
```

---

## 五、完整 R32 生成 Trace 示例

给定以下 standings，生成完整的可解释 R32：

### 5.1 输入 Standings

```
Group A: 1. Mexico(9pts), 2. South Africa(3pts), 3. Jamaica(3pts), 4. Nepal(0pts)
Group B: 1. Switzerland(9pts), 2. Canada(4pts), 3. Bosnia(3pts), 4. Nigeria(0pts)
Group C: 1. Brazil(9pts), 2. Morocco(6pts), 3. Croatia(3pts), 4. New Zealand(0pts)
Group D: 1. USA(7pts), 2. Australia(6pts), 3. Paraguay(4pts), 4. Uzbekistan(0pts)
Group E: 1. Germany(9pts), 2. Ivory Coast(6pts), 3. Ecuador(4pts), 4. Zambia(0pts)
Group F: 1. Netherlands(9pts), 2. Japan(6pts), 3. Sweden(3pts), 4. Bolivia(0pts)
Group G: 1. Belgium(9pts), 2. Egypt(4pts), 3. Tunisia(3pts), 4. Indonesia(0pts)
Group H: 1. Spain(9pts), 2. Cape Verde(4pts), 3. Jordan(3pts), 4. Haiti(0pts)
Group I: 1. France(9pts), 2. Norway(6pts), 3. Senegal(4pts), 4. Benin(0pts)
Group J: 1. Argentina(9pts), 2. Austria(4pts), 3. Algeria(3pts), 4. Kenya(0pts)
Group K: 1. Colombia(9pts), 2. Portugal(6pts), 3. DR Congo(4pts), 4. Sudan(0pts)
Group L: 1. England(9pts), 2. Croatia(4pts), 3. Ghana(3pts), 4. Panama(0pts)
```

### 5.2 第三名排名 Trace

```
第三名排名（12支）：
1. DR Congo (K)   — 4pts, GD:-1, GF:3,  FIFA#62
2. Paraguay (D)   — 4pts, GD:0,  GF:4,  FIFA#40
3. Ecuador (E)    — 4pts, GD:0,  GF:3,  FIFA#32 ← 积分相同，FIFA排名最前
4. Bosnia (B)     — 3pts, GD:0,  GF:3,  FIFA#75
5. Algeria (J)    — 3pts, GD:0,  GF:2,  FIFA#85
6. Senegal (I)   — 3pts, GD:-1, GF:3,  FIFA#20
7. Sweden (F)     — 3pts, GD:-2, GF:4,  FIFA#25
8. Ghana (L)     — 3pts, GD:-2, GF:2,  FIFA#60
9. Jamaica (A)    — 3pts, GD:-3, GF:2,  FIFA#47
10. Croatia (C)  — 3pts, GD:-3, GF:2,  FIFA#14
11. Tunisia (G)   — 3pts, GD:-3, GF:1,  FIFA#41
12. Jordan (H)   — 3pts, GD:-4, GF:2,  FIFA#70

→ 晋级 R32：DR Congo, Paraguay, Ecuador, Bosnia, Algeria, Senegal, Sweden, Ghana
→ 淘汰：Jamaica, Croatia, Tunisia, Jordan
```

### 5.3 16场 R32 完整 Trace

```
R32_01: Mexico (1A) vs Ecuador (3E)
  STEP 1: 1A 位置分析 → 允许对阵第三名组别 [C,E,F,H,I]
  STEP 2: 候选第三名交集 → [3E(Ecuador), 3D(Paraguay), 3B(Bosnia)]
  STEP 3: 选最高排名 → 3E(Ecuador) = 排名#3 ✅
  STEP 4: 同组冲突检查 → Mexico(A) ∉ Group E ✅
  STEP 5: 位置互斥 → 3E 未被使用 ✅
  C1 ✅ C2 ✅ C3 ✅

R32_02: South Africa (2A) vs Canada (2B)
  TYPE: Runner-Up Derby（固定位，无需选择）
  C1 ✅ C2 ✅ C3 ✅

R32_03: Brazil (1C) vs Japan (2F)
  TYPE: Fixed Champion vs Runner-Up（固定位，无需选择）
  C1 ✅ C2 ✅ C3 ✅

R32_04: USA (1D) vs Bosnia (3B)
  STEP 1: 1D 位置分析 → 允许对阵第三名组别 [B,E,F,I,J]
  STEP 2: 候选交集 → [3B(Bosnia), 3D(Paraguay)]
  STEP 3: 选最高排名 → 3B(Bosnia) = 排名#4，优先于 Paraguay(#2)？→ 否，按允许组别
  STEP 4: Bosnia ∈ [B,E,F,I,J] ✅
  STEP 5: 3B(Ecuador) 已被 R32_01 使用 → Bosnia 顺延 ✅
  C1 ✅ C2 ✅ C3 ✅

R32_05: Australia (2D) vs Egypt (2G)
  TYPE: Runner-Up Derby（固定位）
  C1 ✅ C2 ✅ C3 ✅

R32_06: Germany (1E) vs Paraguay (3D)
  STEP 1: 1E 位置分析 → 允许对阵第三名组别 [A,B,C,D,F]
  STEP 2: 候选交集 → [3D(Paraguay)]
  STEP 3: 选最高排名 → 3D(Paraguay) = 排名#2 ✅
  STEP 4: Germany(E) ∉ Group D ✅
  C1 ✅ C2 ✅ C3 ✅

R32_07: Ivory Coast (2E) vs Norway (2I)
  TYPE: Runner-Up Derby（固定位）
  C1 ✅ C2 ✅ C3 ✅

R32_08: Netherlands (1F) vs Morocco (2C)
  TYPE: Fixed Champion vs Runner-Up（固定位）
  C1 ✅ C2 ✅ C3 ✅

R32_09: Belgium (1G) vs Senegal (3I)
  STEP 1: 1G 位置分析 → 允许对阵第三名组别 [A,E,H,I,J]
  STEP 2: 候选交集 → [3I(Senegal), 3A(—), 3E(已用), 3H(—), 3J(已用)]
  STEP 3: 选最高排名 → 3I(Senegal) = 排名#6 ✅
  STEP 4: Belgium(G) ∉ Group I ✅
  C1 ✅ C2 ✅ C3 ✅

R32_10: Spain (1H) vs Austria (2J)
  TYPE: Fixed Champion vs Runner-Up（固定位）
  C1 ✅ C2 ✅ C3 ✅

R32_11: France (1I) vs Sweden (3F)
  STEP 1: 1I 位置分析 → 允许对阵第三名组别 [C,D,F,G,H]
  STEP 2: 候选交集 → [3F(Sweden)]
  STEP 3: 选最高排名 → 3F(Sweden) = 排名#7 ✅
  STEP 4: France(I) ∉ Group F ✅
  C1 ✅ C2 ✅ C3 ✅

R32_12: Argentina (1J) vs Cape Verde (2H)
  TYPE: Fixed Champion vs Runner-Up（固定位）
  C1 ✅ C2 ✅ C3 ✅

R32_13: Colombia (1K) vs Ghana (3L)
  STEP 1: 1K 位置分析 → 允许对阵第三名组别 [D,E,I,J,L]
  STEP 2: 候选交集 → [3L(Ghana)]
  STEP 3: 选最高排名 → 3L(Ghana) = 排名#8 ✅
  STEP 4: Colombia(K) ∉ Group L ✅
  C1 ✅ C2 ✅ C3 ✅

R32_14: England (1L) vs Algeria (3J)
  STEP 1: 1L 位置分析 → 允许对阵第三名组别 [E,H,I,J,K]
  STEP 2: 候选交集 → [3J(Algeria)]
  STEP 3: 选最高排名 → 3J(Algeria) = 排名#5 ✅
  STEP 4: England(L) ∉ Group J ✅
  C1 ✅ C2 ✅ C3 ✅

R32_15: Portugal (2K) vs Croatia (2L)
  TYPE: Runner-Up Derby（固定位）
  C1 ✅ C2 ✅ C3 ✅

R32_16: Switzerland (1B) vs DR Congo (3K)
  STEP 1: 1B 位置分析 → 允许对阵第三名组别 [E,F,G,I,J]
  STEP 2: 候选交集 → [3K(DR Congo)]
  STEP 3: 选最高排名 → 3K(DR Congo) = 排名#1 ✅
  STEP 4: Switzerland(B) ∉ Group K ✅
  C1 ✅ C2 ✅ C3 ✅
```

---

## 六、Constraint Engine 签名

```python
class ConstraintR32Engine:
    """
    可验证的 R32 生成引擎。
    每场输出包含完整推理链。
    """

    def generate(
        self,
        group_standings: list[GroupStanding],
    ) -> tuple[list[R32Match], list[MatchTrace], ThirdPlaceRankingTrace]:
        """
        Returns: (matches, traces, third_place_ranking_trace)

        每场 MatchTrace 包含完整推理链。
        ThirdPlaceRankingTrace 包含第三名排名推理链。

        评委可逐行验证：
        1. 第三名排名是否正确
        2. 每个 Slot 的选择是否合法
        3. 约束检查是否通过
        """
        ...
```

---

## 七、Verifiability 检查清单

每场 R32 生成后，必须通过以下检查：

| 检查项 | 说明 |
|---|---|
| 32队各出现一次 | 每队出现且仅出现一次 |
| 8场 Runner-Up Derby 正确 | M73-M88 固定位匹配 |
| 8场 Champion vs Third 合法 | 每场的第三名 ∈ 该 Slot 允许组别 |
| 同组不对阵 | 无同组球队在 R32 中相遇 |
| 位置互斥 | 每个第三名只出现在一个 Slot |
| 第三名排名可验证 | 前8 vs 后4 可逐行追溯 |
| 推理链完整 | 每场 MatchTrace.rule_trace 非空 |

---

## 八、与旧设计的关键区别

| 维度 | 旧设计 | 新设计（+Trace） |
|---|---|---|
| 输出 | Matches（黑盒）| Matches + Traces（白盒）|
| 第三名来源 | "算法选择" | "按排名 + 允许组别选出，有 trace" |
| 配对解释 | "constraint 这么做的" | "Step 1–6，每步可查" |
| 评委验证 | ❌ 无法逐行验证 | ✅ 每场 MatchTrace 可审查 |
| 错误定位 | "输出错了" | "Step 3 的 allowed_groups 错误" |
| 2030 迁移 | 需重写 engine | 只需改 STEP 3 规则（Slot 允许组别）|
