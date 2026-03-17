# ✈️ Turbofan Engine Predictive Maintenance

A full-stack data science project that predicts when aircraft engines will need maintenance, using real NASA sensor data and a live cloud-connected dashboard.

**[Live Demo →]([https://turbofan-predictive-maintenance-system.streamlit.app/](https://turbofan-predictive-maintenance-system.streamlit.app/))**


---

## The Problem

Unplanned engine failures cost airlines $500,000+ per incident. Traditional maintenance runs on fixed schedules rather than actual engine condition. This project builds a system that monitors live sensor data and flags engines before they reach a critical state.

---

## Pipeline Overview

```
NASA CMAPSS data  →  MySQL  →  EDA & feature engineering  →  Random Forest model  →  Supabase  →  Streamlit dashboard
                                                                                                         ↓
                                                                                              Automated email alerts
```

| File | What it does |
|------|-------------|
| `download_data.py` | Scrapes NASA's PCOE site and downloads the 12 CMAPSS data files |
| `load_to_mysql.py` | Loads all data into a normalised MySQL schema (3 tables, ~80k rows) |
| `sql_analysis.sql` | SQL analysis — CTEs, window functions (LAG, RANK), stored procedure, VIEW |
| `eda_features.ipynb` | Exploratory analysis, drops constant sensors, engineers rolling features |
| `train_model.ipynb` | Trains Random Forest (RUL prediction) + Isolation Forest (anomaly detection) |
| `dashboard.py` | Streamlit dashboard connected to live Supabase data |
| `upload_to_supabase.py` | Pushes processed test fleet data to Supabase |
| `send_alerts.py` | Reads Supabase, emails alerts for engines in the danger zone |

---

## Model Performance (FD001)

| Metric | Value |
|--------|-------|
| RMSE | 7.2 cycles |
| MAE | 4.4 cycles |
| R² | 0.969 |

Trained on 16,504 samples, validated on 4,127. The model predicts engine failure within ~7 cycles on average, enabling maintenance to be scheduled with high confidence.

Key finding: `cycle_ratio`, `sensor_7_rolling_avg`, and `sensor_2_rolling_avg` are the strongest predictive features. Seven sensors are entirely constant (sensor_1, sensor_5, sensor_6, sensor_10, sensor_16, sensor_18, sensor_19) and were dropped before modelling. The anomaly detector (Isolation Forest) flagged 37.9% of all readings as unusual.

---

## Running It Locally

```bash
pip install -r requirements.txt
```

```bash
python download_data.py          # Download data
python load_to_mysql.py          # Load to MySQL (set DB_PASSWORD first)
# Run sql_analysis.sql in MySQL Workbench
# Run eda_features.ipynb         # EDA + feature engineering
# Run train_model.ipynb          # Train model
streamlit run dashboard.py       # Launch dashboard
```

Requires MySQL running locally. Set `DB_PASSWORD` in `load_to_mysql.py` before running step 2.

For the live Supabase-connected dashboard, set `SUPABASE_URL` and `SUPABASE_KEY` as environment variables (or in `.streamlit/secrets.toml` for local Streamlit use).

---

## Stack

Python · pandas · scikit-learn · MySQL · Supabase · Streamlit · Plotly

*Data: NASA PCOE CMAPSS Dataset*

---

## Contributors

| | |
|---|---|
| **Priscilla Nzula** | [@priscillanzula](https://github.com/priscillanzula) |

Built and maintained solely by Priscilla Nzula.
