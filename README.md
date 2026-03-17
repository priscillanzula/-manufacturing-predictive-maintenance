# ✈️ Turbofan Engine Predictive Maintenance

A full-stack data science project that predicts when aircraft engines will need maintenance, using real NASA sensor data and a live cloud-connected dashboard.

**[Live Demo →](https://turbofan-health-monitor.streamlit.app/)**

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
| `01_download_data.py` | Scrapes NASA's PCOE site and downloads the 12 CMAPSS data files |
| `02_load_to_mysql.py` | Loads all data into a normalised MySQL schema (3 tables, ~80k rows) |
| `03_sql_analysis.sql` | SQL analysis — CTEs, window functions (LAG, RANK), stored procedure, VIEW |
| `04_eda_features.py` | Exploratory analysis, drops constant sensors, engineers rolling features |
| `05_train_model.py` | Trains Random Forest (RUL prediction) + Isolation Forest (anomaly detection) |
| `06_dashboard.py` | Streamlit dashboard connected to live Supabase data |
| `upload_to_supabase.py` | Pushes processed test fleet data to Supabase |
| `send_alerts.py` | Reads Supabase, emails alerts for engines in the danger zone |

---

## Model Performance (FD001)

| Metric | Value |
|--------|-------|
| RMSE | ~18 cycles |
| MAE | ~12 cycles |
| R² | ~0.87 |

Key finding: sensor_2 (temperature) and sensor_11 (static pressure) are the strongest degradation signals. Seven sensors are entirely constant and were dropped before modelling.

---

## Running It Locally

```bash
pip install -r requirements.txt
```

```bash
python 01_download_data.py       # Download data
python 02_load_to_mysql.py       # Load to MySQL (set DB_PASSWORD first)
# Run 03_sql_analysis.sql in MySQL Workbench
python 04_eda_features.py        # EDA + feature engineering
python 05_train_model.py         # Train model
streamlit run 06_dashboard.py    # Launch dashboard
```

Requires MySQL running locally. Set credentials in `02_load_to_mysql.py` before running step 2.

For the live Supabase-connected dashboard, set `SUPABASE_URL` and `SUPABASE_KEY` as environment variables (or in `.streamlit/secrets.toml` for local Streamlit use).

---

## Stack

Python · pandas · scikit-learn · MySQL · Supabase · Streamlit · Plotly · GitHub Actions

*Data: NASA PCOE CMAPSS Dataset*
