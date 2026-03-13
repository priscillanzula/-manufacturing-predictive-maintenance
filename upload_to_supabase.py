# ============================================================
# upload_to_supabase.py — CORRECTED VERSION
#
# WHAT CHANGED AND WHY:
# The old script uploaded training data which ends at engine
# failure for every engine. So every engine's "latest reading"
# had RUL near 0 — making everything show as DANGER.
#
# This version uses test_FD001.txt + RUL_FD001.txt which is a
# realistic fleet snapshot with engines at different life stages:
#   55 HEALTHY  (80+ cycles remaining)
#   20 WARNING  (30-80 cycles remaining)
#   25 DANGER   (<30 cycles remaining)
#
# HOW TO RUN: python upload_to_supabase.py
# ============================================================

import pandas as pd
import numpy as np
from supabase import create_client

# ============================================================
# YOUR SUPABASE CREDENTIALS
# ============================================================
SUPABASE_URL = "https://tqspwjsofhkubzwddjqj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRxc3B3anNvZmhrdWJ6d2RkanFqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM0MDM5ODAsImV4cCI6MjA4ODk3OTk4MH0.5KMH4wIT_gOGAWPjiKjRU206NkY2Vu_7ly8ZlkYbdYE"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================
# STEP 1: LOAD TEST DATA + TRUE RUL LABELS
# ============================================================
print("Loading test data and RUL labels...")

column_names = [
    "engine_id", "cycle",
    "op_setting_1", "op_setting_2", "op_setting_3",
    "sensor_1","sensor_2","sensor_3","sensor_4","sensor_5",
    "sensor_6","sensor_7","sensor_8","sensor_9","sensor_10",
    "sensor_11","sensor_12","sensor_13","sensor_14","sensor_15",
    "sensor_16","sensor_17","sensor_18","sensor_19","sensor_20","sensor_21"
]

test = pd.read_csv(
    "data/test_FD001.txt",
    sep=r"\s+", header=None, names=column_names
)

rul_labels = pd.read_csv(
    "data/RUL_FD001.txt",
    header=None, names=["true_rul"]
)
rul_labels["engine_id"] = range(1, len(rul_labels) + 1)

print(f"  Loaded {len(test):,} readings for {test['engine_id'].nunique()} engines")

# ============================================================
# STEP 2: CALCULATE RUL FOR EVERY READING
# At the last test cycle: RUL = true_rul (from RUL_FD001.txt)
# At earlier cycles: RUL = true_rul + (max_cycle - current_cycle)
# ============================================================
print("Calculating RUL for all readings...")

last_cycles = test.groupby("engine_id")["cycle"].max().reset_index()
last_cycles.columns = ["engine_id", "max_cycle"]
last_cycles = last_cycles.merge(rul_labels, on="engine_id")

test = test.merge(last_cycles, on="engine_id")
test["RUL_capped"] = (test["true_rul"] + (test["max_cycle"] - test["cycle"])).clip(upper=125)

# ============================================================
# STEP 3: FEATURE ENGINEERING
# ============================================================
print("Engineering features...")

test = test.sort_values(["engine_id", "cycle"]).reset_index(drop=True)
test["cycle_ratio"] = test["cycle"] / test["max_cycle"]

for sensor in ["sensor_2", "sensor_7", "sensor_11", "sensor_12"]:
    test[f"{sensor}_rolling_avg"] = test.groupby("engine_id")[sensor].transform(
        lambda x: x.rolling(window=20, min_periods=1).mean()
    )

test["is_anomaly"] = test["cycle_ratio"] > 0.9

# ============================================================
# STEP 4: PREPARE FINAL COLUMNS
# ============================================================
test = test.rename(columns={"RUL_capped": "rul_capped"})
cols = ["engine_id","cycle","sensor_2","sensor_7","sensor_11","sensor_12",
        "rul_capped","is_anomaly","cycle_ratio"]
data = test[cols].copy()

latest = data.sort_values("cycle").groupby("engine_id").last()
danger  = int((latest["rul_capped"] < 30).sum())
warning = int(((latest["rul_capped"] >= 30) & (latest["rul_capped"] < 80)).sum())
healthy = int((latest["rul_capped"] >= 80).sum())

print(f"\nFleet health preview:")
print(f"  DANGER  (<30 cycles):   {danger} engines")
print(f"  WARNING (30-80 cycles): {warning} engines")
print(f"  HEALTHY (80+ cycles):   {healthy} engines")

# ============================================================
# STEP 5: CLEAR OLD DATA THEN UPLOAD NEW DATA
# ============================================================
print("\nClearing old data from Supabase...")
supabase.table("engine_readings").delete().neq("id", 0).execute()
print("  Old data cleared.")

print(f"\nUploading {len(data):,} rows...")
batch_size = 500
total_batches = (len(data) // batch_size) + 1

for i in range(0, len(data), batch_size):
    batch = data.iloc[i:i + batch_size]
    records = batch.to_dict(orient="records")

    for record in records:
        for key, value in record.items():
            if hasattr(value, "item"):
                record[key] = value.item()
            if not isinstance(value, bool):
                try:
                    if pd.isna(value):
                        record[key] = None
                except:
                    pass

    supabase.table("engine_readings").insert(records).execute()
    batch_num = i // batch_size + 1
    print(f"  Batch {batch_num}/{total_batches} uploaded")

print(f"\nDone! Dashboard will now show:")
print(f"  {danger} engines in DANGER")
print(f"  {warning} engines in WARNING")
print(f"  {healthy} engines HEALTHY")
print("\nRefresh your dashboard to see the correct fleet picture.")
