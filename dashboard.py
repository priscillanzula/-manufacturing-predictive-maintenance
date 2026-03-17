

# import necessary libraries
from streamlit_autorefresh import st_autorefresh
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
import os
from supabase import create_client

st.set_page_config(
    page_title="Engine Health Monitor",
    page_icon="",
    layout="wide"
)


SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]


@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# Load latest reading for each engine, Used for: fleet overview, metrics, alert table, dropdown
# This will return one row per engine — max 100 rows for FD001

@st.cache_data(ttl=300)
def load_latest_per_engine():
    """Loads only the latest reading per engine by fetching all data in pages."""
    try:
        supabase = get_supabase_client()
        all_rows = []
        page_size = 1000
        start = 0

        with st.spinner("Loading fleet data from Supabase..."):
            while True:
                response = (
                    supabase.table("engine_readings")
                    .select("engine_id, cycle, sensor_2, sensor_7, sensor_11, sensor_12, rul_capped, is_anomaly, cycle_ratio")
                    .range(start, start + page_size - 1)
                    .execute()
                )
                batch = response.data
                if not batch:
                    break
                all_rows.extend(batch)
                if len(batch) < page_size:
                    break
                start += page_size

        if not all_rows:
            return pd.DataFrame()

        df = pd.DataFrame(all_rows)
        df = df.rename(columns={"rul_capped": "RUL_capped"})
        df["RUL_capped"] = pd.to_numeric(df["RUL_capped"], errors="coerce")
        df["cycle"] = pd.to_numeric(df["cycle"], errors="coerce")
        df["engine_id"] = pd.to_numeric(df["engine_id"], errors="coerce")
        if "is_anomaly" in df.columns:
            df["is_anomaly"] = df["is_anomaly"].astype(bool)

        # Keep only the latest cycle per engine
        latest = df.sort_values("cycle").groupby(
            "engine_id", as_index=False).last()
        return latest

    except Exception as e:
        st.error(f"Could not connect to Supabase: {e}")
        return pd.DataFrame()


# load full history for one enegine (on demand in deep dive)


@st.cache_data(ttl=300)
def load_engine_history(engine_id: int):
    """Loads all readings for a single engine — used in deep dive."""
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("engine_readings")
            .select("*")
            .eq("engine_id", engine_id)
            .order("cycle")
            .execute()
        )
        if not response.data:
            return pd.DataFrame()
        df = pd.DataFrame(response.data)
        df = df.rename(columns={"rul_capped": "RUL_capped"})
        df["RUL_capped"] = pd.to_numeric(df["RUL_capped"], errors="coerce")
        df["cycle"] = pd.to_numeric(df["cycle"], errors="coerce")
        if "is_anomaly" in df.columns:
            df["is_anomaly"] = df["is_anomaly"].astype(bool)
        return df.sort_values("cycle").reset_index(drop=True)
    except Exception as e:
        st.error(f"Could not load engine {engine_id} history: {e}")
        return pd.DataFrame()


@st.cache_resource
def load_model():
    if os.path.exists("data/random_forest_model.pkl"):
        return joblib.load("data/random_forest_model.pkl")
    return None


# auto-refresh every 5 minutes (300000ms)
st_autorefresh(interval=300_000, limit=None, key="auto_refresh")
# LOAD DATA
latest_readings = load_latest_per_engine()
model = load_model()


# Header
st.markdown("## ✈️ Turbofan Engine Health Monitoring System")
st.caption("Real-time predictive maintenance dashboard powered by machine learning")
st.markdown("""

Unexpected engine failures cost airlines millions.  
This dashboard uses live sensor data and machine learning to predict failures *before* they happen,  
enabling proactive maintenance that saves money and prevents catastrophic downtime.
""")
col_refresh, col_time = st.columns([1, 4])
with col_refresh:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
with col_time:
    st.caption(
        f"Auto-refreshes every 5 minutes. Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

st.markdown("---")

if latest_readings.empty:
    st.error("No data available. Please run upload_to_supabase.py to load your data.")
    st.stop()


# Compute health status for all engines

if "health_status" not in latest_readings.columns:
    conditions = [
        latest_readings["RUL_capped"] < 30,
        (latest_readings["RUL_capped"] >= 30) & (
            latest_readings["RUL_capped"] < 80),
        latest_readings["RUL_capped"] >= 80
    ]
    choices = ["🔴 DANGER", "🟡 WARNING", "🟢 HEALTHY"]
    latest_readings["health_status"] = np.select(
        conditions, choices, default="🟢 HEALTHY")
latest_readings["health_status"] = latest_readings["health_status"].fillna(
    "🟢 HEALTHY")

total_engines = latest_readings["engine_id"].nunique()
danger_count = (latest_readings["health_status"] == "🔴 DANGER").sum()
warning_count = (latest_readings["health_status"] == "🟡 WARNING").sum()
healthy_count = (latest_readings["health_status"] == "🟢 HEALTHY").sum()


# Key metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Fleet Size", total_engines)

with col2:
    st.metric(
        "🔴 Critical",
        int(danger_count),
        delta=f"{int((danger_count/total_engines)*100)}% of fleet",
        delta_color="inverse"
    )

with col3:
    st.metric(
        "🟡 At Risk",
        int(warning_count),
        delta=f"{int((warning_count/total_engines)*100)}% of fleet"
    )

with col4:
    st.metric(
        "🟢 Healthy",
        int(healthy_count),
        delta=f"{int((healthy_count/total_engines)*100)}% of fleet"
    )
# Fleet health overview

st.subheader("Fleet Health Overview")
col_left, col_right = st.columns(2)

with col_left:
    status_counts = latest_readings["health_status"].value_counts(
    ).reset_index()
    status_counts.columns = ["Status", "Count"]

    color_map = {
        "🔴 DANGER":  "#e74c3c",
        "🟡 WARNING": "#f39c12",
        "🟢 HEALTHY": "#2ecc71"
    }
    fig_pie = px.pie(
        status_counts,
        values="Count",
        names="Status",
        title=f"Fleet Health Distribution ({total_engines} engines)",
        color="Status",
        color_discrete_map=color_map,
        hole=0.4
    )
    fig_pie.update_traces(textinfo="percent+label", textfont_size=13)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    fig_hist = px.histogram(
        latest_readings,
        x="RUL_capped",
        nbins=25,
        title="Distribution of Remaining Useful Life Across Fleet",
        labels={"RUL_capped": "Remaining Useful Life (cycles)"},
        color_discrete_sequence=["#3498db"]
    )
    fig_hist.add_vline(x=30, line_dash="dash", line_color="red",
                       annotation_text="🔴 Danger (30)")
    fig_hist.add_vline(x=80, line_dash="dash", line_color="orange",
                       annotation_text="🟡 Warning (80)")
    st.plotly_chart(fig_hist, use_container_width=True)

if danger_count > 0:
    st.error(
        f"🚨 CRITICAL ALERT: {danger_count} engines require immediate maintenance")
elif warning_count > 0:
    st.warning(
        f"⚠️ WARNING: {warning_count} engines approaching failure window")
else:
    st.success("✅ All engines operating within safe limits")

# Fleet summary
st.markdown("---")
st.subheader("Full Fleet Summary ")
st.markdown(
    "Every engine in the fleet sorted by urgency. Use this as your daily work order.")

summary = latest_readings[["engine_id", "cycle",
                           "RUL_capped", "health_status"]].copy()
summary.columns = ["Engine ID", "Last Cycle", "Estimated RUL", "Status"]
summary = summary.sort_values("Estimated RUL")
summary["Estimated RUL"] = summary["Estimated RUL"].round(1)
summary["Action"] = summary["Status"].map({
    "🔴 DANGER":  "Ground engine. Schedule immediate inspection.",
    "🟡 WARNING": "Plan maintenance within 2 weeks.",
    "🟢 HEALTHY": "Continue monitoring. No action needed."
})


def style_status(val):
    # noqa: F401
    # pylint: disable=unused-argument
    if "DANGER" in str(val):
        return "background-color:#fadbd8; color:#922b21; font-weight:bold"
    elif "WARNING" in str(val):
        return "background-color:#fef9e7; color:#7d6608; font-weight:bold"
    return "background-color:#eafaf1; color:#1e8449"


st.dataframe(
    summary.style.map(style_status, subset=["Status"]),
    use_container_width=True,
    hide_index=True,
    height=400
)

csv = summary.to_csv(index=False)
st.download_button(
    label="📥 Download Full Maintenance Report (CSV)",
    data=csv,
    file_name=f"maintenance_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv"
)


# Indivindual engine deep dive
# All 100 engines are in the dropdown, health status shown and full sensor history loaded only when engine is selected

st.markdown("---")
st.subheader("Individual Engine Deep Dive")
st.markdown(
    "Select any engine to see its full sensor history, RUL degradation and anomaly detections.")

# Build dropdown labels showing health status for all 100 engines
engine_status_map = dict(zip(
    latest_readings["engine_id"].astype(int),
    latest_readings["health_status"]
))
all_engine_ids = sorted(latest_readings["engine_id"].astype(int).unique())
engine_labels = [
    f"Engine {e}  —  {engine_status_map.get(e, '')}" for e in all_engine_ids]
label_to_id = dict(zip(engine_labels, all_engine_ids))

st.info(f"All **{total_engines} engines** are available below. "
        f"🔴 {int(danger_count)} DANGER · 🟡 {int(warning_count)} WARNING · 🟢 {int(healthy_count)} HEALTHY")

selected_label = st.selectbox(
    "Select an Engine to Inspect:", options=engine_labels)
selected_engine = label_to_id[selected_label]

# Load full history for selected engine
engine_data = load_engine_history(selected_engine)

if engine_data.empty:
    st.warning(f"No history data found for Engine {selected_engine}.")
    st.stop()

current_rul = engine_data["RUL_capped"].iloc[-1]
total_cycles_lived = int(engine_data["cycle"].max())
anomaly_count_eng = int(engine_data["is_anomaly"].sum(
)) if "is_anomaly" in engine_data.columns else 0

if current_rul < 30:
    health_emoji, health_text, health_color = "🔴", "DANGER — Immediate maintenance required!", "#e74c3c"
elif current_rul < 80:
    health_emoji, health_text, health_color = "🟡", "WARNING — Schedule maintenance soon", "#f39c12"
else:
    health_emoji, health_text, health_color = "🟢", "HEALTHY — Operating normally", "#2ecc71"

st.markdown(f"""
<div style="background-color:{health_color}22; border-left:5px solid {health_color};
     padding:12px 16px; border-radius:6px; margin-bottom:12px;">
  <strong>Engine {selected_engine}</strong> &nbsp;|&nbsp; {health_emoji} {health_text}<br>
  Cycles completed: <strong>{total_cycles_lived}</strong> &nbsp;|&nbsp;
  Estimated cycles remaining: <strong>{int(current_rul)}</strong> &nbsp;|&nbsp;
  Anomalies detected: <strong>{anomaly_count_eng}</strong>
</div>
""", unsafe_allow_html=True)

# Gauge
fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=int(current_rul),
    delta={"reference": 80, "decreasing": {"color": "#e74c3c"},
           "increasing": {"color": "#2ecc71"}},
    title={"text": f"Remaining Useful Life — Engine {selected_engine}",
           "font": {"size": 16}},
    gauge={
        "axis": {"range": [0, 125]},
        "bar":  {"color": health_color, "thickness": 0.3},
        "steps": [
            {"range": [0, 30],   "color": "#fadbd8"},
            {"range": [30, 80],  "color": "#fef9e7"},
            {"range": [80, 125], "color": "#eafaf1"},
        ],
        "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 30}
    }
))
fig_gauge.update_layout(height=300, margin=dict(t=60, b=20))
st.plotly_chart(fig_gauge, use_container_width=True)

# RUL Degradation chart
st.subheader(f"RUL Degradation {selected_engine}")
fig_rul = px.line(
    engine_data, x="cycle", y="RUL_capped",
    title=f"How Engine {selected_engine}'s Remaining Life Decreased Over {total_cycles_lived} Cycles",
    labels={"cycle": "Cycle Number",
            "RUL_capped": "Remaining Useful Life (cycles)"},
    color_discrete_sequence=["#8e44ad"]
)
fig_rul.add_hline(y=30, line_dash="dash", line_color="red",
                  annotation_text="🔴 Danger threshold")
fig_rul.add_hline(y=80, line_dash="dash", line_color="orange",
                  annotation_text="🟡 Warning threshold")
fig_rul.update_layout(hovermode="x unified")
st.plotly_chart(fig_rul, use_container_width=True)
st.caption(
    "A steeper slope means faster degradation. Sudden drops may indicate a developing fault.")

# Sensor trend chart
st.subheader(f"Sensor Trends {selected_engine}")
sensor_options = {
    "Sensor 2 (Temperature)":       "sensor_2",
    "Sensor 7 (Pressure)":          "sensor_7",
    "Sensor 11 (Static Pressure)":  "sensor_11",
    "Sensor 12 (Fuel Flow)":        "sensor_12",
}
available_sensors = {k: v for k,
                     v in sensor_options.items() if v in engine_data.columns}

if available_sensors:
    selected_sensor_label = st.selectbox(
        "Select sensor:", options=list(available_sensors.keys()))
    selected_sensor = available_sensors[selected_sensor_label]

    fig_sensor = px.line(
        engine_data, x="cycle", y=selected_sensor,
        title=f"{selected_sensor_label} — Engine {selected_engine}",
        labels={"cycle": "Cycle Number", selected_sensor: "Sensor Reading"},
        color_discrete_sequence=["#3498db"]
    )
    if "is_anomaly" in engine_data.columns:
        anomalies = engine_data[engine_data["is_anomaly"] == True]
        if len(anomalies) > 0:
            fig_sensor.add_scatter(
                x=anomalies["cycle"], y=anomalies[selected_sensor],
                mode="markers",
                marker=dict(color="red", size=10, symbol="x"),
                name="🔴 Anomaly Detected"
            )
    fig_sensor.update_layout(hovermode="x unified")
    st.plotly_chart(fig_sensor, use_container_width=True)
    st.caption(f"Red X = anomalous reading. Engine {selected_engine} has "
               f"{anomaly_count_eng} anomalous readings out of {len(engine_data)} total.")


# Sidebar

with st.sidebar:
    # --- Project Info (Collapsible) ---
    with st.expander("Project Info", expanded=True):
        st.markdown("""
        **Project:** Turbofan Engine Predictive Maintenance  
        **Dataset:** NASA CMAPSS FD001  
        **Goal:** Predict engine Remaining Useful Life (RUL)

        **Technologies used:**  
        - 🗄️ Supabase (live cloud database). 
        - 🐍 Python (pandas, numpy, sklearn).  
        - 📊 Data science (EDA, feature engineering, ML).  
        - 🚨 Automated email alerts via Gmail.  
        - ☁️ Streamlit Community Cloud deployment.

        **Model:** Random Forest Regressor.
        """)

    st.markdown("---")

    # --- Live Stats (Collapsible) ---
    with st.expander("⚙️ Live Stats", expanded=True):
        st.metric("Engines monitored", total_engines)
        st.metric("🔴 Danger", int(danger_count))
        st.metric("🟡 Warning", int(warning_count))
        st.metric("🟢 Healthy", int(healthy_count))
        st.markdown("**Data source:** Supabase (live)")

        # Conditional alerts
        if danger_count > 0:
            st.error(
                f"🔴 {int(danger_count)} engine(s) need immediate attention!")
        elif warning_count > 0:
            st.warning(
                f"🟡 {int(warning_count)} engine(s) need maintenance soon.")
        else:
            st.success("✅ All engines healthy.")

        # Model status
        if model:
            st.success("✅ ML Model loaded")
        else:
            st.warning("⚠️ No model found.")


# Footer

st.markdown("---")

st.caption("""
✈️ **Turbofan Predictive Maintenance System**

Built with **Python · Streamlit · Plotly · Supabase**  
Model: Random Forest Regressor · Anomaly Detection: Isolation Logic  

📊 Real-time monitoring · 🚨 Alerting · 🔧 Maintenance optimization  
""")
