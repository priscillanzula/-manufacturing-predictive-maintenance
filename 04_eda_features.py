# ============================================================
# FILE 4: Exploratory Data Analysis (EDA) + Feature Engineering
# ============================================================
#
# WHAT IS EDA?
# EDA means "exploring" your data before building any model.
# Think of it like reading a book's table of contents before
# diving into the chapters. It helps you understand:
# - What does the data look like?
# - Are there any problems (missing values, weird numbers)?
# - Which columns are most useful for prediction?
#
# WHAT IS FEATURE ENGINEERING?
# The raw data has sensor readings, but sensors alone may not
# be the best way to predict failure. We create NEW columns
# (features) that capture patterns better.
# Example: Instead of "sensor_2 = 645.5", we calculate
# "rolling_avg_sensor_2_last_20_cycles = 643.8"
# The rolling average is smoother and shows the trend.
#
# HOW TO RUN:
# Option 1 (Jupyter): jupyter notebook 04_eda_features.py
# Option 2 (Terminal): python 04_eda_features.py
#
# INSTALL: pip install pandas numpy matplotlib seaborn scikit-learn
# ============================================================


# ============================================================
# CELL 1 — Import tools
# ============================================================

import pandas as pd           # For reading and working with tables
import numpy as np            # For maths operations on numbers
import matplotlib.pyplot as plt  # For drawing charts
import seaborn as sns          # For prettier charts
import os
import warnings
warnings.filterwarnings("ignore")   # Hide unimportant warnings

# Make charts look nicer
plt.style.use("seaborn-v0_8-whitegrid")  # Clean background with grid lines
sns.set_palette("husl")                  # Nice colour palette

print("All libraries imported successfully!")


# ============================================================
# CELL 2 — Load the data
# ============================================================

# Column names (same as in File 2)
column_names = [
    "engine_id", "cycle",
    "op_setting_1", "op_setting_2", "op_setting_3",
    "sensor_1", "sensor_2", "sensor_3", "sensor_4", "sensor_5",
    "sensor_6", "sensor_7", "sensor_8", "sensor_9", "sensor_10",
    "sensor_11", "sensor_12", "sensor_13", "sensor_14", "sensor_15",
    "sensor_16", "sensor_17", "sensor_18", "sensor_19", "sensor_20",
    "sensor_21"
]

# Load FD001 training data
# We focus on FD001 because it has ONE operating condition = easier to understand
train_data = pd.read_csv(
    "data/train_FD001.txt",
    sep=r"\s+",
    header=None,
    names=column_names
)

# Load FD001 test data
test_data = pd.read_csv(
    "data/test_FD001.txt",
    sep=r"\s+",
    header=None,
    names=column_names
)

# Load the RUL labels for test data
rul_test = pd.read_csv(
    "data/RUL_FD001.txt",
    header=None,
    names=["true_rul"]
)

print(f"Training data shape: {train_data.shape}")
print(f"  → {train_data.shape[0]} rows (sensor readings)")
print(f"  → {train_data.shape[1]} columns (engine_id, cycle, 3 settings, 21 sensors)")
print(f"\nTest data shape: {test_data.shape}")
print(f"RUL labels shape: {rul_test.shape}")


# ============================================================
# CELL 3 — First look at the data
# ============================================================

print("=" * 60)
print("FIRST 5 ROWS OF TRAINING DATA:")
print("=" * 60)
print(train_data.head())

print("\n" + "=" * 60)
print("DATA TYPES AND NON-NULL COUNTS:")
print("=" * 60)
print(train_data.info())

print("\n" + "=" * 60)
print("BASIC STATISTICS FOR EACH COLUMN:")
print("=" * 60)
# round to 2 decimal places so it's readable
print(train_data.describe().round(2))


# ============================================================
# CELL 4 — Check for missing values
# ============================================================

print("=" * 60)
print("MISSING VALUES CHECK:")
print("=" * 60)

missing_count = train_data.isnull().sum()
missing_percent = (missing_count / len(train_data) * 100).round(2)

missing_report = pd.DataFrame({
    "Missing Count": missing_count,
    "Missing %": missing_percent
})

print(missing_report[missing_report["Missing Count"] > 0])

if missing_count.sum() == 0:
    print("GREAT NEWS: No missing values found! Data is complete.")
else:
    print(f"WARNING: Found missing values in some columns.")


# ============================================================
# CELL 5 — Find constant sensors (useless for prediction)
# ============================================================
# If a sensor never changes, it tells us nothing.
# We should drop these columns to simplify our model.

print("\n" + "=" * 60)
print("CONSTANT SENSOR DETECTION:")
print("=" * 60)

sensor_columns = [f"sensor_{i}" for i in range(1, 22)]

constant_sensors = []
useful_sensors = []

for col in sensor_columns:
    # Standard deviation = how much a column varies
    # If std = 0, the column never changes = useless
    std_val = train_data[col].std()
    if std_val < 0.001:  # Essentially zero variation
        constant_sensors.append(col)
        print(f"  CONSTANT (will drop): {col}  std={std_val:.6f}")
    else:
        useful_sensors.append(col)

print(f"\nConstant sensors (to drop): {len(constant_sensors)}")
print(f"Useful sensors (to keep):   {len(useful_sensors)}")
print(f"Useful sensors: {useful_sensors}")


# ============================================================
# CELL 6 — Add the RUL column to training data
# ============================================================
# For training, we calculate how many cycles are LEFT for each reading.
# This is what we want our model to PREDICT.

print("\n" + "=" * 60)
print("ADDING REMAINING USEFUL LIFE (RUL) COLUMN:")
print("=" * 60)

# Step 1: Find the last cycle for each engine (= when it failed)
max_cycles = train_data.groupby("engine_id")["cycle"].max()
max_cycles.name = "max_cycle"

# Step 2: Merge this info back into the main dataframe
train_data = train_data.merge(max_cycles, on="engine_id")

# Step 3: Calculate RUL = max_cycle - current_cycle
train_data["RUL"] = train_data["max_cycle"] - train_data["cycle"]

print("RUL calculation: max_cycle - current_cycle")
print("\nExample — Engine 1, first 5 rows:")
print(train_data[train_data["engine_id"] == 1][["engine_id", "cycle", "max_cycle", "RUL"]].head())

print(f"\nRUL statistics:")
print(f"  Min RUL (just before failure): {train_data['RUL'].min()}")
print(f"  Max RUL (at start of life):    {train_data['RUL'].max()}")
print(f"  Average RUL:                   {train_data['RUL'].mean():.1f}")


# ============================================================
# CELL 7 — Chart: Distribution of Engine Lifespans
# ============================================================

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Chart 1: Histogram of how long engines last
engine_lives = train_data.groupby("engine_id")["max_cycle"].first()

axes[0].hist(engine_lives, bins=20, color="#3498db", edgecolor="white", linewidth=0.8)
axes[0].set_title("How Long Do Engines Last?\n(Distribution of Engine Lifespans)", fontsize=13)
axes[0].set_xlabel("Total Cycles Before Failure")
axes[0].set_ylabel("Number of Engines")
axes[0].axvline(engine_lives.mean(), color="red", linestyle="--", linewidth=1.5, label=f"Average = {engine_lives.mean():.0f}")
axes[0].legend()

# Chart 2: RUL distribution across all readings
axes[1].hist(train_data["RUL"], bins=40, color="#2ecc71", edgecolor="white", linewidth=0.8)
axes[1].set_title("Distribution of RUL Across All Readings\n(What we want to predict)", fontsize=13)
axes[1].set_xlabel("Remaining Useful Life (cycles)")
axes[1].set_ylabel("Number of Readings")

plt.tight_layout()
plt.savefig("data/chart_01_engine_lifespans.png", dpi=150, bbox_inches="tight")
plt.show()
print("Chart saved: data/chart_01_engine_lifespans.png")

# ============================================================
# FINDING:
# Most engines last between 150 and 350 cycles.
# The distribution is fairly spread out, which means
# different engines degrade at different rates.
# ============================================================


# ============================================================
# CELL 8 — Chart: How sensors change as engines degrade
# ============================================================

# Plot sensor trends for a few engines
fig, axes = plt.subplots(2, 3, figsize=(16, 10))
axes = axes.flatten()

# Pick the sensors that vary the most (most useful for prediction)
sensors_to_plot = ["sensor_2", "sensor_7", "sensor_11", "sensor_12", "sensor_15", "sensor_20"]

# Pick 5 random engines to plot (so the chart is not too crowded)
sample_engines = [1, 10, 20, 50, 80]

for idx, sensor in enumerate(sensors_to_plot):
    ax = axes[idx]
    for eng in sample_engines:
        engine_data = train_data[train_data["engine_id"] == eng].sort_values("cycle")
        ax.plot(engine_data["cycle"], engine_data[sensor], alpha=0.7, linewidth=1)

    ax.set_title(f"{sensor} over time", fontsize=11)
    ax.set_xlabel("Cycle")
    ax.set_ylabel("Sensor Reading")

plt.suptitle("Sensor Readings Over Time for 5 Sample Engines\n(Each line = one engine)", fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig("data/chart_02_sensor_trends.png", dpi=150, bbox_inches="tight")
plt.show()
print("Chart saved: data/chart_02_sensor_trends.png")

# ============================================================
# FINDING:
# Sensor 2 (temperature) slowly increases over time — this is
# a sign of heat buildup from wear. Sensor 11 (pressure) shows
# a slight decrease over time. These trends are exactly what
# a predictive model needs to detect.
# ============================================================


# ============================================================
# CELL 9 — Chart: Sensor correlation heatmap
# ============================================================
# A correlation tells us: when sensor A goes up, does sensor B also go up?
# If yes, they are correlated. Highly correlated sensors carry the same info
# — we might only need one of them.

# Calculate correlation between all useful sensors
correlation_matrix = train_data[useful_sensors].corr().round(2)

fig, ax = plt.subplots(figsize=(14, 12))
sns.heatmap(
    correlation_matrix,
    annot=True,         # Show numbers inside each square
    fmt=".2f",          # Format to 2 decimal places
    cmap="RdYlGn",      # Red = negative, Green = positive correlation
    center=0,
    linewidths=0.5,
    ax=ax
)
ax.set_title("Correlation Between Sensors\n(Green = Positive, Red = Negative correlation)", fontsize=13)
plt.tight_layout()
plt.savefig("data/chart_03_sensor_correlation.png", dpi=150, bbox_inches="tight")
plt.show()
print("Chart saved: data/chart_03_sensor_correlation.png")

# ============================================================
# FINDING:
# Sensors 3 and 4 (temperatures) are strongly correlated.
# Sensors 9 and 14 (core speeds) are also very similar.
# In a production model, we might drop one from each pair.
# ============================================================


# ============================================================
# CELL 10 — Feature Engineering
# "Create better inputs for our prediction model"
# ============================================================

print("=" * 60)
print("FEATURE ENGINEERING")
print("=" * 60)
print("We are creating NEW columns from the existing data.")
print("These new columns capture trends and patterns better.")

# We will work on FD001 only
data = train_data.copy()

# Sort data so each engine's readings are in time order
data = data.sort_values(["engine_id", "cycle"]).reset_index(drop=True)

# FEATURE 1: Rolling average of key sensors (window of 20 cycles)
# This smooths out noise — instead of one noisy reading,
# we take the average of the last 20 readings.
print("\nCreating rolling average features (window = 20 cycles)...")

rolling_window = 20
key_sensors = ["sensor_2", "sensor_7", "sensor_11", "sensor_12"]

for sensor in key_sensors:
    new_col_name = f"{sensor}_rolling_avg"
    data[new_col_name] = (
        data.groupby("engine_id")[sensor]
        .transform(lambda x: x.rolling(window=rolling_window, min_periods=1).mean())
    )
    print(f"  Created: {new_col_name}")


# FEATURE 2: Rolling standard deviation (how noisy/unstable a sensor is)
# High variability can indicate a problem even before the average changes
print("\nCreating rolling standard deviation features...")

for sensor in key_sensors:
    new_col_name = f"{sensor}_rolling_std"
    data[new_col_name] = (
        data.groupby("engine_id")[sensor]
        .transform(lambda x: x.rolling(window=rolling_window, min_periods=2).std().fillna(0))
    )
    print(f"  Created: {new_col_name}")


# FEATURE 3: How far into the engine's life are we? (relative cycle)
# Cycle 50 means different things for an engine that lives 100 vs 300 cycles
# "Cycle ratio" = current_cycle / max_cycle (a number between 0 and 1)
# 0.0 = just started, 1.0 = about to fail
print("\nCreating cycle ratio feature...")
data["cycle_ratio"] = data["cycle"] / data["max_cycle"]
print("  Created: cycle_ratio (0 = just started, 1 = about to fail)")


# FEATURE 4: Cap the RUL at 125 cycles (piece-wise linear target)
# Early in engine life, the exact RUL doesn't matter much.
# What matters is: is it in the last 125 cycles or not?
# This is a standard technique in predictive maintenance research.
print("\nCapping RUL at 125 cycles (standard predictive maintenance technique)...")
data["RUL_capped"] = data["RUL"].clip(upper=125)
print("  Created: RUL_capped")
print("  Reasoning: We only care about PREDICTING near-term failures.")
print("  An engine with 400 cycles left vs 300 cycles left is not actionable.")
print("  But 50 cycles vs 125 cycles IS actionable.")


# ============================================================
# CELL 11 — Save the processed data
# ============================================================

# Save to CSV so we don't have to redo this every time
data.to_csv("data/train_FD001_processed.csv", index=False)
print(f"\nProcessed data saved to: data/train_FD001_processed.csv")
print(f"Shape: {data.shape}")
print(f"New feature columns: {[c for c in data.columns if 'rolling' in c or 'ratio' in c or 'capped' in c]}")


# ============================================================
# CELL 12 — Summary and Recommendations
# ============================================================

print("\n" + "=" * 60)
print("EDA SUMMARY & FINDINGS")
print("=" * 60)

print("""
WHAT WE FOUND:
--------------
1. ENGINE LIFESPAN VARIES A LOT:
   Engines last anywhere from ~128 to ~362 cycles (FD001).
   Average life = ~206 cycles. High variation means some engines
   wear out much faster than others — predicting this early is valuable.

2. SOME SENSORS ARE USELESS:
   Several sensors (sensor_1, sensor_5, sensor_6, sensor_10, 
   sensor_16, sensor_18, sensor_19) are CONSTANT — they never change.
   We should drop these from our model to keep it simple.

3. SENSORS SHOW CLEAR DEGRADATION TRENDS:
   Sensor 2 (temperature) increases over time.
   Sensor 11 (pressure) decreases over time.
   These trends are detectable BEFORE failure — perfect for prediction.

4. SOME SENSORS ARE HIGHLY CORRELATED:
   Sensors 3 & 4 carry similar information.
   Sensors 9 & 14 carry similar information.
   Including both in a model adds complexity without adding value.

RECOMMENDATIONS FOR THE MODEL:
------------------------------
- Use rolling averages instead of raw sensor values
- Drop constant sensors
- Use RUL capped at 125 cycles as the prediction target
- Focus on sensors: 2, 7, 8, 9, 11, 12, 13, 14, 15, 17
""")

print("NEXT STEP: Run file 05_train_model.py")
print("           That file builds and trains the prediction model.")
