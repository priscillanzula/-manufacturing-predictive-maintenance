# generate_dashboard.py
# Pulls latest data from Supabase and rewrites docs/index.html with updated numbers.
# Run manually or via GitHub Actions (see .github/workflows/refresh_dashboard.yml).

import os
import json
from datetime import datetime, timezone
from supabase import create_client

# ── CONFIG ──────────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Set SUPABASE_URL and SUPABASE_KEY environment variables.")

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "docs", "index.html")
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# ── FETCH DATA ───────────────────────────────────────────────────────────────
print("Connecting to Supabase...")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Fetching engine readings...")
all_rows = []
page_size = 1000
start = 0
while True:
    resp = supabase.table("engine_readings") \
        .select("engine_id, cycle, rul_capped, is_anomaly") \
        .range(start, start + page_size - 1) \
        .execute()
    batch = resp.data
    if not batch:
        break
    all_rows.extend(batch)
    if len(batch) < page_size:
        break
    start += page_size

print(f"  Fetched {len(all_rows):,} rows")

# ── COMPUTE LATEST PER ENGINE ────────────────────────────────────────────────
latest = {}
for row in all_rows:
    eid = row["engine_id"]
    if eid not in latest or row["cycle"] > latest[eid]["cycle"]:
        latest[eid] = row

readings = list(latest.values())
total    = len(readings)
danger   = sum(1 for r in readings if r["rul_capped"] is not None and r["rul_capped"] < 30)
warning  = sum(1 for r in readings if r["rul_capped"] is not None and 30 <= r["rul_capped"] < 80)
healthy  = sum(1 for r in readings if r["rul_capped"] is not None and r["rul_capped"] >= 80)
ruls     = [r["rul_capped"] for r in readings if r["rul_capped"] is not None]
avg_rul  = round(sum(ruls) / len(ruls), 1) if ruls else 0
min_rul  = min(ruls) if ruls else 0

sorted_readings = sorted(readings, key=lambda x: x["rul_capped"] or 9999)
critical_rows   = sorted_readings[:7]

# Build RUL histogram bins: 0-15, 15-30, 30-45, 45-60, 60-80, 80-100, 100-120, 120+
bins = [0, 15, 30, 45, 60, 80, 100, 120, 999]
rul_hist = [0] * (len(bins) - 1)
for v in ruls:
    for i in range(len(bins) - 1):
        if bins[i] <= v < bins[i+1]:
            rul_hist[i] += 1
            break

now_str = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")

print(f"  Total: {total}  Danger: {danger}  Warning: {warning}  Healthy: {healthy}")
print(f"  Avg RUL: {avg_rul}  Min RUL: {min_rul}")

# ── BUILD TABLE ROWS ─────────────────────────────────────────────────────────
table_rows_html = ""
for r in critical_rows:
    rul_val = int(r["rul_capped"]) if r["rul_capped"] is not None else "—"
    status  = "DANGER" if r["rul_capped"] < 30 else "WARNING" if r["rul_capped"] < 80 else "OK"
    css     = "badge-d" if status == "DANGER" else "badge-w" if status == "WARNING" else "badge-s"
    table_rows_html += (
        f'<tr><td>#{r["engine_id"]}</td>'
        f'<td style="font-family:var(--font-mono);color:var(--danger);">{rul_val}</td>'
        f'<td><span class="badge {css}">{status}</span></td></tr>\n'
    )

# ── READ TEMPLATE AND INJECT DATA ────────────────────────────────────────────
template_path = os.path.join(os.path.dirname(__file__), "index.html")
with open(template_path, "r", encoding="utf-8") as f:
    html = f.read()

# Patch KPI values via simple string replacement markers
replacements = {
    "<!--TOTAL-->":   str(total),
    "<!--DANGER-->":  str(danger),
    "<!--WARNING-->": str(warning),
    "<!--HEALTHY-->": str(healthy),
    "<!--AVG_RUL-->": str(avg_rul),
    "<!--MIN_RUL-->": str(int(min_rul)),
    "<!--UPDATED-->": now_str,
    "<!--TABLE_ROWS-->": table_rows_html,
    "<!--RUL_HIST_DATA-->": json.dumps(rul_hist),
}

for marker, value in replacements.items():
    html = html.replace(marker, value)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nDashboard written to: {OUTPUT_PATH}")
print("Done.")
