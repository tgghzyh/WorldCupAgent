import json, sys
paths = [
    r"C:\Users\43021\Desktop\ART\data\snapshots\latest.json",
    r"C:\Users\43021\Desktop\ART\WorldCupAgent\data\snapshots\latest.json",
    r"C:\Users\43021\Desktop\ART\WorldCupAgent\latest.json",
]
found = False
for p in paths:
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        found = True
        print(f"OK: {p}")
        matches = d.get("matches", [])
        print(f"  matches: {len(matches)}")
        print(f"  snapshot_id: {d.get('snapshot_id')}")
        print(f"  headline: {d.get('headline', 'MISSING')[:80]}")
        print(f"  generated_at: {d.get('generated_at')}")
        print(f"  expires_at: {d.get('expires_at')}")
        print(f"  changes: {len(d.get('changes', []))}")
        print(f"  versions: {d.get('versions')}")
        if matches:
            m = matches[0]
            print(f"  sample match match_id: {m.get('match_id')}")
            print(f"  prediction.outcome: {m.get('prediction',{}).get('outcome')}")
            print(f"  prediction.confidence: {m.get('prediction',{}).get('confidence')}")
            factors = m.get("factors", [])
            print(f"  factors count: {len(factors)}")
            if factors:
                print(f"  factors[0]: {factors[0]}")
            print(f"  metadata: {m.get('metadata')}")
    except FileNotFoundError:
        print(f"NOT FOUND: {p}")
    except Exception as e:
        print(f"ERROR {p}: {e}")

if not found:
    print("No valid snapshot found!")
    sys.exit(1)
