# ============================================================
# FILE 6: Streamlit Dashboard
# ============================================================
#
# WHAT IS STREAMLIT?
# Streamlit turns a Python script into a web app with buttons,
# charts, and tables — no HTML or web development needed.
# It is perfect for showing your data science results
# in a visual, interactive way.
#
# HOW TO RUN THIS DASHBOARD:
# 1. Open your terminal
# 2. Navigate to the project folder
# 3. Run: streamlit run 06_dashboard.py
# 4. Your browser will open automatically at localhost:8501
#
# INSTALL: pip install streamlit pandas numpy matplotlib plotly joblib
# ============================================================

import streamlit as st          # The web app framework
import pandas as pd
import numpy as np
import plotly.express as px     # Interactive charts
import plotly.graph_objects as go
import joblib
import os

# ============================================================
# PAGE CONFIGURATION — must be the FIRST streamlit command
# ============================================================

st.set_page_config(
    page_title="Engine Health Monitor",
    page_icon="✈️",
    layout="wide"           # Use the full width of the screen
)


# ============================================================
# SECTION 1: Load everything we need
# ============================================================

# We use @st.cache_data to load data only once (not every time you click something)
# This makes the app much faster

@st.cache_data
def load_data():
    """Load the processed sensor data."""
    if os.path.exists("data/train_FD001_processed.csv"):
        return pd.read_csv("data/train_FD001_processed.csv")
    else:
        # If processed data not found, create a small demo dataset
        st.warning("Processed data not found. Showing demo data.")
        # Create fake demo data so the dashboard still works visually
        np.random.seed(42)
        n = 5000
        demo = pd.DataFrame({
            "engine_id": np.repeat(range(1, 51), 100),
            "cycle": list(range(1, 101)) * 50,
            "sensor_2": 640 + np.random.normal(0, 5, n) + np.random.normal(0, 2, n),
            "sensor_7": 550 + np.random.normal(0, 10, n),
            "sensor_11": 47 + np.random.normal(0, 1, n),
            "sensor_12": 520 + np.random.normal(0, 5, n),
            "RUL_capped": np.clip(125 - np.repeat(range(1, 101), 50), 0, 125),
            "is_anomaly": np.random.choice([False, True], n, p=[0.95, 0.05]),
            "cycle_ratio": np.tile(np.linspace(0, 1, 100), 50),
            "max_cycle": 100,
        })
        return demo


@st.cache_resource
def load_model():
    """Load the trained prediction model."""
    if os.path.exists("data/random_forest_model.pkl"):
        return joblib.load("data/random_forest_model.pkl")
    return None


@st.cache_resource
def load_scaler():
    """Load the data scaler."""
    if os.path.exists("data/scaler.pkl"):
        return joblib.load("data/scaler.pkl")
    return None


# Actually load everything
data = load_data()
model = load_model()
scaler = load_scaler()


# ============================================================
# SECTION 2: HEADER
# ============================================================

st.title("✈️ Turbofan Engine Health Monitor")
st.markdown("""
**Business Problem:** Airlines and manufacturers lose millions when engines fail unexpectedly.
This dashboard uses sensor data and machine learning to predict engine failures
*before* they happen, enabling scheduled maintenance that saves cost and lives.

---
""")


# ============================================================
# SECTION 3: KEY METRICS (top row summary cards)
# ============================================================

# Calculate some summary stats
total_engines = data["engine_id"].nunique()
avg_life = data.groupby("engine_id")["max_cycle"].first().mean()

# Which engines are in the "danger zone" (low RUL)?
# Get the LATEST reading per engine (most current health status)
latest_readings = data.sort_values("cycle").groupby("engine_id").last().reset_index()

danger_engines  = (latest_readings["RUL_capped"] < 30).sum()
warning_engines = ((latest_readings["RUL_capped"] >= 30) & (latest_readings["RUL_capped"] < 80)).sum()
healthy_engines = (latest_readings["RUL_capped"] >= 80).sum()

# Display as 4 metric cards across the top
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Engines Monitored",
        value=total_engines,
        delta=None
    )

with col2:
    st.metric(
        label="🔴 DANGER (< 30 cycles left)",
        value=danger_engines,
        delta="Needs immediate maintenance"
    )

with col3:
    st.metric(
        label="🟡 WARNING (30-80 cycles left)",
        value=warning_engines,
        delta="Schedule maintenance soon"
    )

with col4:
    st.metric(
        label="🟢 HEALTHY (80+ cycles left)",
        value=healthy_engines,
        delta="Operating normally"
    )

st.markdown("---")


# ============================================================
# SECTION 4: Engine Fleet Health Overview
# ============================================================

st.subheader("🏥 Fleet Health Overview")

col_left, col_right = st.columns(2)

with col_left:
    # Bar chart showing how many engines are in each health category
    latest_readings["health_status"] = pd.cut(
        latest_readings["RUL_capped"],
        bins=[0, 30, 80, 200],
        labels=["🔴 DANGER", "🟡 WARNING", "🟢 HEALTHY"]
    )

    status_counts = latest_readings["health_status"].value_counts()

    fig_pie = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title="Fleet Health Distribution",
        color_discrete_sequence=["#e74c3c", "#f39c12", "#2ecc71"],
        hole=0.4    # Donut chart
    )
    fig_pie.update_traces(textinfo="percent+label")
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    # Histogram of RUL values across all engines
    fig_hist = px.histogram(
        latest_readings,
        x="RUL_capped",
        nbins=25,
        title="Distribution of Remaining Useful Life",
        labels={"RUL_capped": "Remaining Useful Life (cycles)"},
        color_discrete_sequence=["#3498db"]
    )
    fig_hist.add_vline(x=30, line_dash="dash", line_color="red",
                       annotation_text="Danger threshold")
    fig_hist.add_vline(x=80, line_dash="dash", line_color="orange",
                       annotation_text="Warning threshold")
    st.plotly_chart(fig_hist, use_container_width=True)


# ============================================================
# SECTION 5: Individual Engine Explorer
# ============================================================

st.markdown("---")
st.subheader("🔍 Individual Engine Deep Dive")

# Sidebar — let user select which engine to inspect
selected_engine = st.selectbox(
    "Select an Engine to Inspect:",
    options=sorted(data["engine_id"].unique()),
    index=0
)

# Filter data for selected engine
engine_data = data[data["engine_id"] == selected_engine].sort_values("cycle")

# Show engine summary
current_rul = engine_data["RUL_capped"].iloc[-1]
total_cycles_lived = engine_data["cycle"].max()

if current_rul < 30:
    health_emoji = "🔴"
    health_text = "DANGER — Immediate maintenance required!"
    health_color = "#e74c3c"
elif current_rul < 80:
    health_emoji = "🟡"
    health_text = "WARNING — Schedule maintenance soon"
    health_color = "#f39c12"
else:
    health_emoji = "🟢"
    health_text = "HEALTHY — Operating normally"
    health_color = "#2ecc71"

st.markdown(f"""
**Engine {selected_engine}** — {health_emoji} {health_text}
- Cycles completed: **{total_cycles_lived}**
- Estimated cycles remaining: **{int(current_rul)}**
""")

# Gauge chart for RUL
fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=int(current_rul),
    title={"text": f"Remaining Useful Life — Engine {selected_engine}"},
    gauge={
        "axis": {"range": [0, 125]},
        "bar": {"color": health_color},
        "steps": [
            {"range": [0, 30], "color": "#fadbd8"},    # Red zone
            {"range": [30, 80], "color": "#fef9e7"},   # Yellow zone
            {"range": [80, 125], "color": "#eafaf1"},  # Green zone
        ],
        "threshold": {
            "line": {"color": "red", "width": 4},
            "thickness": 0.75,
            "value": 30
        }
    }
))
fig_gauge.update_layout(height=300)
st.plotly_chart(fig_gauge, use_container_width=True)


# ============================================================
# SECTION 6: Sensor Trends for Selected Engine
# ============================================================

st.subheader(f"📊 Sensor Trends — Engine {selected_engine}")

# Let user pick which sensor to view
sensor_options = {
    "Sensor 2 (Temperature)": "sensor_2",
    "Sensor 7 (Pressure)": "sensor_7",
    "Sensor 11 (Static Pressure)": "sensor_11",
    "Sensor 12 (Fuel Flow)": "sensor_12",
}

selected_sensor_label = st.selectbox("Select a sensor to inspect:", options=list(sensor_options.keys()))
selected_sensor = sensor_options[selected_sensor_label]

# Line chart of sensor over time
fig_sensor = px.line(
    engine_data,
    x="cycle",
    y=selected_sensor,
    title=f"{selected_sensor_label} over {total_cycles_lived} Cycles",
    labels={"cycle": "Cycle Number", selected_sensor: "Sensor Reading"},
    color_discrete_sequence=["#3498db"]
)

# Highlight anomalies if detected
if "is_anomaly" in engine_data.columns:
    anomalies = engine_data[engine_data["is_anomaly"] == True]
    if len(anomalies) > 0:
        fig_sensor.add_scatter(
            x=anomalies["cycle"],
            y=anomalies[selected_sensor],
            mode="markers",
            marker=dict(color="red", size=10, symbol="x"),
            name="Anomaly Detected"
        )

st.plotly_chart(fig_sensor, use_container_width=True)

# Also show the rolling average on the same chart
if f"{selected_sensor}_rolling_avg" in engine_data.columns:
    st.caption(f"Red X marks = sensor readings flagged as unusual by our anomaly detector")


# ============================================================
# SECTION 7: Maintenance Alert Table
# ============================================================

st.markdown("---")
st.subheader("⚠️ Maintenance Alert Table")
st.markdown("Engines sorted by urgency — those with least cycles remaining shown first.")

# Create alert table
alert_table = latest_readings[["engine_id", "cycle", "RUL_capped"]].copy()
alert_table.columns = ["Engine ID", "Cycles Completed", "Estimated RUL"]
alert_table["Alert Level"] = pd.cut(
    alert_table["Estimated RUL"],
    bins=[0, 30, 80, 200],
    labels=["🔴 DANGER", "🟡 WARNING", "🟢 HEALTHY"]
)
alert_table = alert_table.sort_values("Estimated RUL")

# Colour the rows based on status (Streamlit dataframe styling)
def colour_row(val):
    if val == "🔴 DANGER":
        return "background-color: #fadbd8"
    elif val == "🟡 WARNING":
        return "background-color: #fef9e7"
    else:
        return "background-color: #eafaf1"

st.dataframe(
    alert_table.style.map(colour_row, subset=["Alert Level"]),
    use_container_width=True,
    height=400
)


# ============================================================
# SECTION 8: Project Summary (in the sidebar)
# ============================================================

with st.sidebar:
    st.markdown("## 📋 Project Info")
    st.markdown("""
    **Project:** Turbofan Engine Predictive Maintenance

    **Dataset:** NASA CMAPSS FD001

    **Skills demonstrated:**
    - 🕸️ Web scraping (requests, BeautifulSoup)
    - 🗄️ MySQL (schema design, SQL queries, CTEs, views, stored procedures)
    - 🐍 Python (pandas, numpy, sklearn)
    - 📊 Data science (EDA, feature engineering, ML, anomaly detection)

    ---
    **Model:** Random Forest Regressor

    **Goal:** Predict engine Remaining Useful Life (RUL)

    **Business Impact:**
    Prevent unplanned failures that cost $500,000+ each
    """)

    st.markdown("---")
    st.markdown("## ⚙️ Dataset Info")
    st.markdown(f"""
    - **Total readings:** {len(data):,}
    - **Engines monitored:** {total_engines}
    - **Features used:** 24
    """)

    if model:
        st.success("✅ ML Model loaded")
    else:
        st.warning("⚠️ No model found. Run 05_train_model.py")


# ============================================================
# SECTION 9: Footer
# ============================================================

st.markdown("---")
st.markdown("""
*Dashboard built with Python · Streamlit · Plotly*
*Data source: NASA PCOE Prognostic Data Repository*
*Model: Random Forest Regressor trained on CMAPSS FD001*
""")
