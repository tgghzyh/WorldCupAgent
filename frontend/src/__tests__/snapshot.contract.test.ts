/**
 * Snapshot Contract Test
 * Verifies latest.json has all required fields
 * Based on ENGINEERING_GUIDELINES.md v2.0
 */

import { loadSnapshot, SnapshotLoadError } from "@/lib/tournament/loader/snapshot.loader";
import type { Snapshot } from "@/lib/tournament/types";

describe("Snapshot Contract", () => {
  let snapshot: Snapshot;

  beforeAll(async () => {
    snapshot = await loadSnapshot();
  });

  describe("ISO8601 时间格式验证", () => {
    it("snapshot_time 必须是有效的 ISO8601", () => {
      const isoRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/;
      expect(snapshot.snapshot_time).toMatch(isoRegex);
    });

    it("expires_at 必须是有效的 ISO8601", () => {
      const isoRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/;
      expect(snapshot.expires_at).toMatch(isoRegex);
    });
  });

  describe("Confidence Level 枚举验证", () => {
    it("confidence 必须是 High/Medium/Low", () => {
      const allMatches = Object.values(snapshot.group_predictions)
        .flatMap((g) => g.matches);

      for (const match of allMatches) {
        expect(["High", "Medium", "Low"]).toContain(match.confidence);
      }
    });

    it("confidence 不能是 undefined/null/空字符串", () => {
      const allMatches = Object.values(snapshot.group_predictions)
        .flatMap((g) => g.matches);

      for (const match of allMatches) {
        expect(match.confidence).toBeDefined();
        expect(typeof match.confidence).toBe("string");
        expect(match.confidence.length).toBeGreaterThan(0);
      }
    });
  });

  describe("Probability 范围验证", () => {
    it("champion_probability 必须在 0~1 之间", () => {
      expect(snapshot.champion_probability).toBeGreaterThanOrEqual(0);
      expect(snapshot.champion_probability).toBeLessThanOrEqual(1);
    });

    it("所有概率字段必须是百分比字符串", () => {
      const allMatches = Object.values(snapshot.group_predictions)
        .flatMap((g) => g.matches);

      for (const match of allMatches) {
        expect(match.home_win_prob).toMatch(/^\d+(\.\d+)?%$/);
        expect(match.draw_prob).toMatch(/^\d+(\.\d+)?%$/);
        expect(match.away_win_prob).toMatch(/^\d+(\.\d+)?%$/);
      }
    });
  });

  describe("Reasoning 验证", () => {
    it("每场比赛必须有非空 reasoning（至少10字符）", () => {
      const allMatches = Object.values(snapshot.group_predictions)
        .flatMap((g) => g.matches);

      for (const match of allMatches) {
        expect(match.reasoning).toBeDefined();
        expect(typeof match.reasoning).toBe("string");
        expect(match.reasoning.length).toBeGreaterThan(10);
      }
    });

    it("reasoning 不能只是占位符", () => {
      const allMatches = Object.values(snapshot.group_predictions)
        .flatMap((g) => g.matches);

      for (const match of allMatches) {
        const invalidReasonings = ["N/A", "TBD", "pending", "-", ""];
        expect(invalidReasonings).not.toContain(match.reasoning.toLowerCase());
      }
    });
  });

  describe("比赛数量验证", () => {
    it("必须有 72 场小组赛", () => {
      const totalMatches = Object.values(snapshot.group_predictions)
        .flatMap((g) => g.matches).length;
      expect(totalMatches).toBe(72);
    });
  });

  describe("Monte Carlo 验证", () => {
    it("monte_carlo_simulations 必须 >= 10000", () => {
      expect(snapshot.monte_carlo_simulations).toBeGreaterThanOrEqual(10000);
    });

    it("reasoning_chain 必须包含 monte_carlo_tool", () => {
      const hasMonteCarlo = snapshot.reasoning_chain.some(
        (entry) => entry.tool === "monte_carlo_tool"
      );
      expect(hasMonteCarlo).toBe(true);
    });
  });

  describe("Champion 数据验证", () => {
    it("champion 不能为空", () => {
      expect(snapshot.champion).toBeDefined();
      expect(snapshot.champion.length).toBeGreaterThan(0);
    });

    it("champion_probability 必须是数字", () => {
      expect(typeof snapshot.champion_probability).toBe("number");
    });
  });

  describe("Top-level fields", () => {
    it("必须有 knowledge_version", () => {
      expect(snapshot).toHaveProperty("knowledge_version");
      expect(typeof snapshot.knowledge_version).toBe("string");
    });

    it("必须有 prediction_version", () => {
      expect(snapshot).toHaveProperty("prediction_version");
      expect(typeof snapshot.prediction_version).toBe("string");
    });

    it("必须有 champion", () => {
      expect(snapshot).toHaveProperty("champion");
      expect(typeof snapshot.champion).toBe("string");
    });

    it("必须有 runner_up 和 third_place", () => {
      expect(snapshot).toHaveProperty("runner_up");
      expect(snapshot).toHaveProperty("third_place");
    });
  });

  describe("Group predictions", () => {
    it("必须有 group_predictions", () => {
      expect(snapshot).toHaveProperty("group_predictions");
      expect(typeof snapshot.group_predictions).toBe("object");
    });

    it("必须有 reasoning_chain", () => {
      expect(snapshot).toHaveProperty("reasoning_chain");
      expect(Array.isArray(snapshot.reasoning_chain)).toBe(true);
    });

    it("必须有 llm_analysis", () => {
      expect(snapshot).toHaveProperty("llm_analysis");
      expect(typeof snapshot.llm_analysis).toBe("string");
      expect(snapshot.llm_analysis.length).toBeGreaterThan(0);
    });
  });

  describe("Knockout predictions", () => {
    it("必须有 knockout_predictions", () => {
      expect(snapshot).toHaveProperty("knockout_predictions");
    });

    it("必须有 predicted_champion", () => {
      expect(snapshot.knockout_predictions).toHaveProperty("predicted_champion");
    });

    it("必须有 champion_probability", () => {
      expect(snapshot.knockout_predictions).toHaveProperty("champion_probability");
    });

    it("必须有所有淘汰赛轮次", () => {
      const { rounds } = snapshot.knockout_predictions;
      expect(rounds).toHaveProperty("round_of_16");
      expect(rounds).toHaveProperty("quarter_finals");
      expect(rounds).toHaveProperty("semi_finals");
      expect(rounds).toHaveProperty("third_place");
      expect(rounds).toHaveProperty("final");
    });
  });
});

describe("SnapshotLoadError", () => {
  it("should throw SnapshotLoadError for invalid data", async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: false,
      status: 404,
    });

    await expect(loadSnapshot()).rejects.toThrow(SnapshotLoadError);
  });
});
