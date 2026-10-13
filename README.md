# Air Quality USA Dashboard

An interactive Streamlit dashboard exploring air quality trends across major U.S. cities from 2020 to 2026, using EPA AQS data.

**Live app:** [air-quality-usa.streamlit.app](https://air-quality-usa.streamlit.app)

![Dashboard screenshot](images/screenshot.png)

---

## Overview

This project analyzes PM2.5 and AQI data for 6 U.S. cities, combining EPA monitoring records with meteorological event data to surface patterns, long-term trends, and policy-relevant insights.

Key questions explored:
- Which cities exceed WHO and EPA air quality guidelines most often?
- Are PM2.5 levels improving, worsening, or flat over time?
- Do weekends consistently show lower pollution than weekdays?
- How do wildfire smoke and dust events affect local AQI?

---

## Dashboard Tabs

| Tab | What it shows |
|-----|---------------|
| **Overview** | City-level risk scorecard with mean AQI, % unhealthy days, and key findings |
| **Per-City Detail** | Deep dive into one city: daily PM2.5 time series, seasonal patterns, weekday vs. weekend gap with bootstrap 95% CI |
| **Trends** | Multi-city AQI trends with Theil-Sen slope and Mann-Kendall significance test |
| **Events** | Meteorological events (wildfire smoke, dust) linked to AQI spikes |
| **Correlations** | Cross-city and cross-pollutant correlation heatmaps |

---

## Data Sources

- **EPA Air Quality System (AQS):** PM2.5, O3 and PM10 daily measurements and AQI by CBSA, downloaded via the EPA AQS API
- **Meteorological events:** Smoke and dust event flags from EPA records
- Processed data stored in `data/processed/` as Parquet files

---

## Methods

- **Mann-Kendall test** for monotonic trend detection (significance threshold p < 0.10)
- **Theil-Sen slope** for robust trend magnitude estimation
- **Bootstrap 95% CI** (10,000 resamples) for weekday vs. weekend PM2.5 gap
- WHO PM2.5 daily guideline: 15 µg/m³
- EPA NAAQS PM2.5 24-hour standard: 35 µg/m³

---

## Project Structure

```
air-quality-usa/
├── app.py                  # Streamlit dashboard
├── requirements.txt        # Python dependencies
├── data/
│   └── processed/
│       ├── air_quality_usa.parquet
│       ├── aqi_by_cbsa.parquet
│       └── meteo_events.parquet
└── images/                 # Static assets
```

---

## Running Locally

```bash
git clone https://github.com/AlonsoSheila/air-quality-usa.git
cd air-quality-usa
pip install -r requirements.txt
streamlit run app.py
```

---

## Author

**Sheila Alonso** — Data Science Portfolio  
[GitHub](https://github.com/AlonsoSheila)
