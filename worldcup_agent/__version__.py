"""WorldCupAgent pipeline version.

Semantic versioning: MAJOR.MINOR.PATCH
  MAJOR — Breaking changes to prediction schema (incompatible snapshot format)
  MINOR — New features (new data sources, new models)
  PATCH — Bug fixes, tests, documentation

When a new prediction snapshot is generated, it records this version so that
future snapshots can be compared correctly even after schema changes.
"""
__version__ = "0.2.0"

CHANGELOG = {
    "0.2.0": "Elo ratings (S9) integrated; FactorAttribution schema; versioned snapshots",
    "0.1.0": "Initial release: sequential pipeline, Monte Carlo simulation",
}
