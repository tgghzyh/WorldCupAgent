/**
 * Snapshot Loader
 * Responsible for loading latest.json
 * Does NOT transform, filter, or sort data
 */

import type { Snapshot } from "@/lib/tournament/types";

export class SnapshotLoadError extends Error {
  constructor(
    message: string,
    public code: "NOT_FOUND" | "PARSE_ERROR" | "NETWORK_ERROR" | "VALIDATION_ERROR"
  ) {
    super(message);
    this.name = "SnapshotLoadError";
  }
}

/**
 * Load snapshot from latest.json
 * Only reads and validates - no transformation
 */
export async function loadSnapshot(): Promise<Snapshot> {
  try {
    const response = await fetch("/data/snapshots/latest.json");

    if (!response.ok) {
      if (response.status === 404) {
        throw new SnapshotLoadError(
          "Snapshot file not found",
          "NOT_FOUND"
        );
      }
      throw new SnapshotLoadError(
        `Failed to load snapshot: ${response.status}`,
        "NETWORK_ERROR"
      );
    }

    const data = await response.json();

    if (!data || typeof data !== "object") {
      throw new SnapshotLoadError(
        "Invalid snapshot data: not an object",
        "PARSE_ERROR"
      );
    }

    return data as Snapshot;
  } catch (error) {
    if (error instanceof SnapshotLoadError) {
      throw error;
    }
    if (error instanceof SyntaxError) {
      throw new SnapshotLoadError(
        "Failed to parse snapshot JSON",
        "PARSE_ERROR"
      );
    }
    throw new SnapshotLoadError(
      `Unexpected error: ${error instanceof Error ? error.message : "Unknown"}`,
      "NETWORK_ERROR"
    );
  }
}

/**
 * Synchronous version for server components
 */
export function loadSnapshotSync(): Snapshot {
  // This is only for server-side usage
  // In production, use the async version
  if (typeof window !== "undefined") {
    throw new Error(
      "loadSnapshotSync should only be used in server components"
    );
  }

  try {
    // Dynamic require for server-side only
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const data = require("../../../public/data/snapshots/latest.json");
    return data as Snapshot;
  } catch (error) {
    throw new SnapshotLoadError(
      `Failed to load snapshot: ${error instanceof Error ? error.message : "Unknown"}`,
      "NOT_FOUND"
    );
  }
}
