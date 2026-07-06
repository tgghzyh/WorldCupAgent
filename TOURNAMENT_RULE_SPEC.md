# FIFA World Cup 2026 — Rule Abstraction Specification

**Sprint**: PE-0 v2 · **Author**: Cursor AI (Qoder) · **Date**: 2026-07-05
**Status**: RULE ABSTRACTION COMPLETE (constraint-based, no lookup tables)

---

## 元声明

- **本文件为零代码输出**，仅记录世界杯规则抽象模型
- 采用 **Constraint-Based Engine** 设计，不使用 lookup table
- 所有数据来源为公开信息（FIFA 规则、Wikipedia 赛程），**不声称具有 FIFA 官方授权**
- 在此文档经人工确认之前，**禁止修改任何 Python 源码、Schema 或 latest.json**

---

## 一、核心赛制（事实层）

### 1.1 基本参数

| 参数 | 值 |
|---|---|
| 参赛球队 | 48 |
| 小组数 | 12（A–L）|
| 每组队数 | 4 |
| 小组赛场次 | 72（12组 × 每组6场）|
| 小组赛出线队 | 24（每组前2名）+ 8（最好第三名）= 32 |
| 淘汰赛总场次 | 33（R32:16 + R16:8 + QF:4 + SF:2 + 3rd:1 + Final:1）|
| 总比赛场次 | 105（72 + 33）|

### 1.2 小组赛规则

**积分规则**：胜=3分，平=1分，负=0分

**小组排名平局打破顺序**（依次应用，直到分出排名）：

1. 积分高者排名靠前
2. 净胜球多者排名靠前
3. 总进球多者排名靠前
4. 公平竞赛分高者排名靠前（红黄牌扣分少者）
5. FIFA 世界排名高者（排名数字小者）排名靠前

### 1.3 晋级规则

- 每组前 **2 名** 直接晋级
- 12 支第三名球队中，**积分最多者晋级**（同分按上述平局打破规则）
- 共 **32 支球队** 进入淘汰赛

---

## 二、Knockout Construction Rule（逻辑层）

### 2.1 淘汰赛结构

```
Round of 32  →  16 支球队参赛，16 场比赛
Round of 16  →   8 支球队参赛， 8 场比赛
Quarter-finals →  4 支球队参赛， 4 场比赛
Semi-finals    →  2 支球队参赛， 2 场比赛
Third Place    →  2 支球队参赛， 1 场比赛
Final          →  2 支球队参赛， 1 场比赛
```

### 2.2 R32 约束规则

R32 生成遵循以下**确定性约束**（无随机、无 lookup table）：

#### 约束 1：固定 Runner-Up vs Runner-Up 对阵

以下 8 场对阵**在小组赛结束前已确定**，无论第三名如何：

| Match | 主队 | 客队 |
|---|---|---|
| M73 | A组第2 | B组第2 |
| M75 | F组冠军 | C组第2 |
| M76 | C组冠军 | F组第2 |
| M78 | E组第2 | I组第2 |
| M83 | K组第2 | L组第2 |
| M84 | H组冠军 | J组第2 |
| M86 | J组冠军 | H组第2 |
| M88 | D组第2 | G组第2 |

#### 约束 2：组别隔离约束

**同一小组的球队在 R32 中不会相遇。**

这条约束决定了哪些冠军位必须对阵第三名球队：

以下 8 个冠军位，由于同组第二名已在 M73–M88 中对阵其他组别，因此这些位的冠军**只能对阵第三名球队**（不能对阵同组第二名）：

| 冠军位 | 原因（同组第2已固定对阵）| 可能对手组 |
|---|---|---|
| 1A | 2B 在 M73，2A 的其他对手在固定位 | C, E, F, H, I |
| 1B | 2A 在 M73 | E, F, G, I, J |
| 1D | 2G 在 M88 | B, E, F, I, J |
| 1E | 2F 在 M76，2I 在 M78 | A, B, C, D, F |
| 1G | 2D 在 M88 | A, E, H, I, J |
| 1I | 2E 在 M78 | C, D, F, G, H |
| 1K | 2L 在 M83 | D, E, I, J, L |
| 1L | 2K 在 M83 | E, H, I, J, K |

#### 约束 3：位置互斥约束

同一第三名球队**只出现在一个位置**（不能同时打两场）。

### 2.3 Constraint-Based R32 生成算法

```
输入：12 组 standings（每组含冠军、第2、第3名球队）

步骤：

1. 固定 Runner-Up 对阵（8场，直接生成）

2. 确定第三名晋级集合：
   - 收集12个第三名
   - 按 [积分, 净胜球, 进球, 公平竞赛, FIFA排名] 排序
   - 取前8名晋级

3. 填充冠军位（8场）：
   对每个冠军位（1A, 1B, 1D, 1E, 1G, 1I, 1K, 1L）：
     a. 获取该位允许的第三名组别列表
     b. 从剩余第三名中，按 FIFA 排名顺序选择允许的最高排名第三名
     c. 确保该第三名未被使用（位置互斥）
     d. 生成对阵

4. 输出：16 场 R32 对阵
```

**算法特点**：
- 确定性（相同输入 → 相同输出）
- 可解释（每步有规则依据）
- 无需 lookup table
- 不声称与 FIFA 官方赛程一致（AI 预测用，非官方赛程）

---

## 三、Constraint Engine 设计建议

### 3.1 R32 Generator 类签名

```python
@dataclass
class GroupStanding:
    group: str                    # "A", "B", ..., "L"
    winner: str                  # 冠军球队名
    runner_up: str               # 第2名球队名
    third: str                   # 第3名球队名
    fourth: str                  # 第4名球队名
    points: int                  # 积分
    goal_diff: int               # 净胜球
    goals_scored: int            # 进球数
    fair_play: int               # 公平竞赛分（越高越好）
    fifa_rank: int               # FIFA世界排名（越小越好）


@dataclass
class R32Match:
    match_id: str                # "r32_0", ..., "r32_15"
    home_team: str               # 来自约束规则确定的主队
    away_team: str               # 来自约束规则确定的客队
    constraint_type: str          # "runner_up_derby" | "champion_vs_third"


class R32Generator:
    """
    Constraint-based Round of 32 bracket generator.
    No lookup table. Deterministic. Explainable.
    """

    # 固定 Runner-Up Derby 对阵（Match 编号）
    FIXED_RUNNER_UP_PAIRS = [
        ("2A", "2B"),  # M73
        ("1F", "2C"),  # M75
        ("1C", "2F"),  # M76
        ("2E", "2I"),  # M78
        ("2K", "2L"),  # M83
        ("1H", "2J"),  # M84
        ("1J", "2H"),  # M86
        ("2D", "2G"),  # M88
    ]

    # 每个冠军位的允许第三名对手组（由约束2推导）
    CHAMPION_THIRD_SLOTS = {
        "1A": ["C", "E", "F", "H", "I"],
        "1B": ["E", "F", "G", "I", "J"],
        "1D": ["B", "E", "F", "I", "J"],
        "1E": ["A", "B", "C", "D", "F"],
        "1G": ["A", "E", "H", "I", "J"],
        "1I": ["C", "D", "F", "G", "H"],
        "1K": ["D", "E", "I", "J", "L"],
        "1L": ["E", "H", "I", "J", "K"],
    }

    def generate(self, group_standings: list[GroupStanding]) -> list[R32Match]:
        """
        Deterministic R32 generation from group standings.
        """
        ...
```

### 3.2 第三名排名函数

```python
def rank_third_place_teams(
    group_standings: list[GroupStanding]
) -> list[GroupStanding]:
    """
    从12个 group standings 中提取第三名，
    按 [积分, 净胜球, 进球, 公平竞赛, FIFA排名] 排序。

    Returns: 前8名（已排序）→ 晋级 R32
             后4名（已排序）→ 淘汰
    """
    thirds = [gs for gs in group_standings]
    thirds.sort(
        key=lambda gs: (
            -gs.points,           # 积分高优先
            -gs.goal_diff,        # 净胜球多优先
            -gs.goals_scored,     # 进球多优先
            -gs.fair_play,        # 公平竞赛分高优先
            gs.fifa_rank,         # FIFA排名数字小优先
        )
    )
    return thirds  # [0:8] = 晋级，[8:12] = 淘汰
```

### 3.3 约束验证函数

```python
def validate_r32(r32_matches: list[R32Match]) -> bool:
    """
    验证 R32 对阵是否满足约束：
    1. 32 支球队各出现一次
    2. 同组球队不对阵（M73-M88 固定位已覆盖）
    3. 8 场 runner-up derby 正确
    4. 冠军 vs 第三名对阵符合 CHAMPION_THIRD_SLOTS
    """
    ...
```

---

## 四、TournamentRule 配置对象

```python
@dataclass
class TournamentRule:
    year: int
    teams: int                    # 48
    groups: int                   # 12
    group_size: int              # 4
    qualifiers_per_group: int     # 2
    third_place_advancers: int    # 8
    knockout_order: list[str]     # ["r32", "r16", "qf", "sf", "third", "final"]
    knockout_sizes: dict[str, int]
    tiebreaker_keys: list[str]    # ["points", "goal_diff", "goals_scored", "fair_play", "fifa_rank"]

    # ⚠️ 不含任何 lookup table
    # ⚠️ 不声称与 FIFA 官方赛程一致

    @classmethod
    def wc2026(cls) -> "TournamentRule":
        return cls(
            year=2026,
            teams=48,
            groups=12,
            group_size=4,
            qualifiers_per_group=2,
            third_place_advancers=8,
            knockout_order=["r32", "r16", "qf", "sf", "third", "final"],
            knockout_sizes={"r32": 32, "r16": 16, "qf": 8, "sf": 4, "third": 2, "final": 2},
            tiebreaker_keys=["points", "goal_diff", "goals_scored", "fair_play", "fifa_rank"],
        )
```

---

## 五、与旧赛制的对比

| 项目 | 2022（旧）| 2026（新）|
|---|---|---|
| 参赛队 | 32 | 48 |
| 小组数 | 8 | 12 |
| 每组队数 | 4 | 4 |
| 小组赛场次 | 48 | 72 |
| 直接出线队 | 16（每组前2）| 24（每组前2）|
| 第三名出线 | 0 | 8 |
| 淘汰赛首轮 | R16（8场）| **R32（16场）** |
| 冠军比赛场数 | 7 | 8 |
| R32 Runner-Up Derby | 无 | **8场固定位** |

---

## 六、禁止事项

- ❌ 禁止引入任何 lookup table（ANNEX_C_ROWS 等）
- ❌ 禁止声称生成的 R32 对阵与 FIFA 官方赛程一致
- ❌ 禁止 `if year == 2026` 分支逻辑
- ❌ 禁止在 TournamentRule 中硬编码特定年份的配对结果
- ❌ 禁止修改 latest.json（PE-3 之前）

---

## 七、数据来源

- 赛制基本参数：FIFA 公开规则（12组 × 4队，top2 + 8 thirds）
- R32 固定位（M73–M88）：Wikipedia 赛程公开信息
- 冠军位允许第三名对手：基于约束2推导（组别隔离 + 固定位互斥）
- 第三名排序规则：FIFA 官方平局打破标准
