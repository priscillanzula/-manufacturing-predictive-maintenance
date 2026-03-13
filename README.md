# ✈️ Turbofan Engine Predictive Maintenance
### A Full-Stack Data Science Portfolio Project

---

## 🎯 What This Project Does

This project builds a system that **predicts when an aircraft engine will need maintenance**, before it breaks down.

It uses real NASA sensor data from turbofan engines, recorded from when the engine was new until it failed.

---

## 💼 The Business Problem

Airlines and manufacturers lose **$500,000+ per unplanned engine failure**.  
Traditional maintenance is scheduled by calendar time — not by actual engine health.  
This project replaces guesswork with data-driven predictions.

---

## 🛠️ Skills Demonstrated

| Skill | What You Will See |
|-------|-------------------|
| **Web Scraping** | Python downloads data from NASA's website using `requests` and `BeautifulSoup` |
| **MySQL** | Normalised schema, GROUP BY, CASE, RANK(), LAG(), CTEs, JOINs, VIEW, Stored Procedure |
| **Python** | pandas, numpy, matplotlib, seaborn for EDA and feature engineering |
| **Data Science** | Random Forest (RUL prediction), Isolation Forest (anomaly detection), Streamlit dashboard |

---

## 📁 Project Files

```
turbofan_project/
│
├── 01_download_data.py      ← Web scraping: downloads NASA data files
├── 02_load_to_mysql.py      ← Loads all data into MySQL database
├── sql/
│   └── 03_sql_analysis.sql  ← All SQL queries: CTEs, window functions, stored procedure
├── 04_eda_features.py       ← Exploratory analysis + feature engineering
├── 05_train_model.py        ← Trains Random Forest + anomaly detector
├── 06_dashboard.py          ← Streamlit web app dashboard
├── data/                    ← Downloaded data files go here
└── project_report.docx      ← Full written report with findings & recommendations
```

---

## 🚀 How to Run (Step by Step)

### Step 0 — Install required packages
```
pip install requests beautifulsoup4 pandas numpy matplotlib seaborn scikit-learn joblib streamlit plotly mysql-connector-python
```

### Step 1 — Download the data
```
python 01_download_data.py
```
This visits NASA's website and downloads 12 data files into a `data/` folder.

### Step 2 — Load into MySQL
```
python 02_load_to_mysql.py
```
⚠️ **Edit DB_PASSWORD in the file first** to match your MySQL password.  
This creates a database called `turbofan_db` with 3 tables.

### Step 3 — Run SQL analysis
Open `sql/03_sql_analysis.sql` in MySQL Workbench and run it.  
Contains 8 different SQL techniques including CTEs, window functions, and a stored procedure.

### Step 4 — Explore the data
```
python 04_eda_features.py
```
Generates 3 charts and creates a processed data file with engineered features.

### Step 5 — Train the model
```
python 05_train_model.py
```
Trains a Random Forest model to predict Remaining Useful Life.  
Saves the model to `data/random_forest_model.pkl`.

### Step 6 — Open the dashboard
```
streamlit run 06_dashboard.py
```
Opens an interactive web app in your browser at `http://localhost:8501`.

---

## 📊 What the Dashboard Shows

- **Fleet health overview** — how many engines are in DANGER / WARNING / HEALTHY status
- **Individual engine inspector** — pick any engine and see its RUL gauge and sensor trends
- **Maintenance alert table** — all engines sorted by urgency
- **Anomaly markers** — unusual sensor readings highlighted in red on charts

---

## 📈 Model Results

| Metric | Value | Meaning |
|--------|-------|---------|
| RMSE | ~18 cycles | Average prediction error |
| MAE | ~12 cycles | Typical prediction error |
| R² | ~0.87 | Model explains 87% of variation |

---

## 💡 Key Findings

1. Engine lifespans vary from 128 to 362 cycles — predictions are genuinely valuable
2. Sensor 2 (temperature) and Sensor 11 (pressure) are the strongest failure indicators
3. 6 sensors are constant and useless — removing them improves the model
4. ~5% of all readings contain anomalies that deserve engineer attention

---

## 📖 Full Report

See `project_report.docx` for the full business report with findings, analysis, and recommendations.

---

*Data source: NASA PCOE Prognostic Data Repository — CMAPSS Dataset*
