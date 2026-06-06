"""
fetch_data.py
API 1 → { "total": N, "registered": N, "not_registered": N }
API 2 → { "count": { "completed": N, "inprogress": N, "not_started": N } }
Only updates data/history.json — index.html reads it at runtime.
"""

import json, os, sys
from datetime import datetime, timezone
from pathlib import Path
import requests

# ── Config ─────────────────────────────────────────────────────────────────────
API_URL_1   = os.environ.get("API_URL_1",   "").strip()
API_URL_2   = os.environ.get("API_URL_2",   "").strip()

DATA_FILE = Path("data/history.json")
MAX_ROWS  = 200   # ← change: 200 snapshots = ~50 hrs at 15-min interval

# ── Validate ────────────────────────────────────────────────────────────────────
missing = [n for n, v in [("API_URL_1", API_URL_1), ("API_URL_2", API_URL_2)] if not v]
if missing:
    print(f"ERROR: Missing GitHub secrets: {', '.join(missing)}")
    sys.exit(1)

# ── Fetch ────────────────────────────────────────────────────────────────────────
def fetch(url, label):
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        print(f"✅ Fetched {label}: {data}")
        return {"data": data, "error": None}
    except Exception as e:
        print(f"⚠️  ERROR fetching {label}: {e}")
        return {"data": None, "error": str(e)}

fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
r1 = fetch(API_URL_1, "Registration API")
r2 = fetch(API_URL_2, "Test Status API")

# ── Save history ──────────────────────────────────────────────────────────────
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
history = []
if DATA_FILE.exists():
    try:
        history = json.loads(DATA_FILE.read_text())
        if not isinstance(history, list): history = []
    except: history = []

history.append({
    "fetched_at":   fetched_at,
    "registration": r1,   # { data: { total, registered, not_registered } }
    "test_status":  r2,   # { data: { count: { completed, inprogress, not_started } } }
})
history = history[-MAX_ROWS:]
DATA_FILE.write_text(json.dumps(history, indent=2))
print(f"📦 Snapshot #{len(history)} saved at {fetched_at}")
