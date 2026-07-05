/**
 * Snapshot Contract Test
 * Verifies latest.json has all required fields
 */

import { loadSnapshot, SnapshotLoadError } from "@/lib/tournament/loader/snapshot.loader";
import type { Snapshot } from "@/lib/tournament/types";

describe("Snapshot Contract", () => {
  let snapshot: Snapshot;

  beforeAll(async () => {
    snapshot = await loadSnapshot();
  });

  describe("Top-level fields", () => {
    it("must have knowledge_version", () => {
      expect(snapshot).toHaveProperty("knowledge_version");
      expect(typeof snapshot.knowledge_version).toBe("string");
    });

    it("must have prediction_version", () => {
      expect(snapshot).toHaveProperty("prediction_version");
      expect(typeof snapshot.prediction_version).toBe("string");
    });

    it("must have snapshot_time", () => {
      expect(snapshot).toHaveProperty("snapshot_time");
      expect(typeof snapshot.snapshot_time).toBe("string");
    });

    it("must have expires_at", () => {
      expect(snapshot).toHaveProperty("expires_at");
      expect(typeof snapshot.expires_at).toBe("string");
    });

    it("must have champion", () => {
      expect(snapshot).toHaveProperty("champion");
      expect(typeof snapshot.champion).toBe("string");
      expect(snapshot.champion.length).toBeGreaterThan(0);
    });

    it("must have champion_probability", () => {
      expect(snapshot).toHaveProperty("champion_probability");
      expect(typeof snapshot.champion_probability).toBe("number");
      expect(snapshot.champion_probability).toBeGreaterThanOrEqual(0);
      expect(snapshot.champion_probability).toBeLessThanOrEqual(1);
    });
  });

  describe("Group predictions", () => {
    it("must have group_predictions", () => {
      expect(snapshot).toHaveProperty("group_predictions");
      expect(typeof snapshot.group_predictions).toBe("object");
    });

    it("must have at least one group", () => {
      const groups = Object.keys(snapshot.group_predictions);
      expect(groups.length).toBeGreaterThan(0);
    });

    it("must have matches in each group", () => {
      for (const [groupLetter, group] of Object.entries(snapshot.group_predictions)) {
        expect(group).toHaveProperty("matches");
        expect(Array.isArray(group.matches)).toBe(true);
        expect(group.matches.length).toBeGreaterThan(0);

        // Each match must have required fields
        for (const match of group.matches) {
          expect(match).toHaveProperty("id");
          expect(match).toHaveProperty("home_team");
          expect(match).toHaveProperty("away_team");
          expect(match).toHaveProperty("reasoning");
          expect(typeof match.reasoning).toBe("string");
        }
      }
    });

    it("must have reasoning in each match", () => {
      for (const [groupLetter, group] of Object.entries(snapshot.group_predictions)) {
        for (const match of group.matches) {
          expect(match.reasoning).toBeDefined();
          expect(typeof match.reasoning).toBe("string");
          expect(match.reasoning.length).toBeGreaterThan(0);
        }
      }
    });
  });

  describe("Knockout predictions", () => {
    it("must have knockout_predictions", () => {
      expect(snapshot).toHaveProperty("knockout_predictions");
      expect(typeof snapshot.knockout_predictions).toBe("object");
    });

    it("must have predicted_champion", () => {
      expect(snapshot.knockout_predictions).toHaveProperty("predicted_champion");
      expect(typeof snapshot.knockout_predictions.predicted_champion).toBe("string");
    });

    it("must have champion_probability", () => {
      expect(snapshot.knockout_predictions).toHaveProperty("champion_probability");
      expect(typeof snapshot.knockout_predictions.champion_probability).toBe("string");
    });

    it("must have rounds", () => {
      expect(snapshot.knockout_predictions).toHaveProperty("rounds");
      const { rounds } = snapshot.knockout_predictions;

      expect(rounds).toHaveProperty("round_of_16");
      expect(rounds).toHaveProperty("quarter_finals");
      expect(rounds).toHaveProperty("semi_finals");
      expect(rounds).toHaveProperty("third_place");
      expect(rounds).toHaveProperty("final");
    });
  });

  describe("Monte Carlo", () => {
    it("must have monte_carlo_simulations", () => {
      expect(snapshot).toHaveProperty("monte_carlo_simulations");
      expect(typeof snapshot.monte_carlo_simulations).toBe("number");
      expect(snapshot.monte_carlo_simulations).toBeGreaterThanOrEqual(1000);
    });

    it("must have reasoning_chain", () => {
      expect(snapshot).toHaveProperty("reasoning_chain");
      expect(Array.isArray(snapshot.reasoning_chain)).toBe(true);
    });

    it("must have monte_carlo_tool in reasoning_chain", () => {
      const monteCarloEntry = snapshot.reasoning_chain.find(
        (entry) => entry.tool === "monte_carlo_tool"
      );
      expect(monteCarloEntry).toBeDefined();
      expect(monteCarloEntry).toHaveProperty("duration_ms");
      expect(typeof monteCarloEntry!.duration_ms).toBe("number");
    });
  });

  describe("LLM Analysis", () => {
    it("must have llm_analysis", () => {
      expect(snapshot).toHaveProperty("llm_analysis");
      expect(typeof snapshot.llm_analysis).toBe("string");
      expect(snapshot.llm_analysis.length).toBeGreaterThan(0);
    });
  });
});

describe("SnapshotLoadError", () => {
  it("should throw SnapshotLoadError for invalid data", async () => {
    // Mock fetch to return invalid data
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: false,
      status: 404,
    });

    await expect(loadSnapshot()).rejects.toThrow(SnapshotLoadError);
  });
});
