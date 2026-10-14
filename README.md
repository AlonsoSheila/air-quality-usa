# Air Quality USA — Comparative Analysis Across 6 Metro Areas

An interactive Streamlit dashboard and analytical notebook exploring PM2.5 and AQI trends across six major U.S. metro areas from 2020 to 2026, using EPA AQS data.

**Live dashboard:** [air-quality-usa.streamlit.app](https://air-quality-usa.streamlit.app)

![Dashboard screenshot](images/screenshot.png)

---

## Overview

This project analyses daily PM2.5, PM10 and Ozone measurements for Los Angeles, Seattle, New York, Chicago, Denver and Houston — covering roughly 2,200 days per city (2020 through mid-2026). It combines EPA monitoring records with meteorological event data to surface patterns, long-term trends, and risk-relevant insights for climate analytics, insurance and ESG portfolio screening.

Cities are identified by their EPA Core-Based Statistical Area (CBSA): for example, "California" in the internal data refers to the Los Angeles–Long Beach–Anaheim CBSA.

**Key questions explored:**
- Which cities exceed WHO and EPA air quality guidelines most often?
- Are PM2.5 levels improving, worsening, or flat over time?
- Do weekends consistently show lower pollution than weekdays?
- How do wildfire smoke and long-range transport events (e.g., Quebec 2023) affect local AQI?
- What is the order-of-magnitude health economic cost of observed exceedances?

---

## Key Findings

1. **Los Angeles is in a different tier entirely.** Mean AQI 88.8 vs 53.5–69.1 for the other five cities. 10.7% of days exceeded the "Unhealthy" threshold — roughly 4–13× the rate of every other city (Houston: 2.6%, the next highest). This chronic gap, not any single event, is the headline finding.

2. **"Worst day" and "worst pattern" are different things.** Seattle has the lowest mean AQI of all six cities (53.5) yet recorded the single highest AQI in the dataset (362, Hazardous, Oct 19 2022) — a city clean most of the year, punctuated by extreme, short-lived wildfire smoke events.

3. **The June 2023 Quebec wildfire smoke event reached both New York and Chicago**, confirmed independently in both cities' top-10 worst-AQI tables (NY: June 6–8, AQI up to 278; Chicago: June 27–28, AQI up to 246). Surface winds at ground level did not point toward Quebec — this event traveled at altitude and settled locally, a cross-border transported risk not captured by local emission monitoring.

4. **No city shows a statistically significant trend at the 95% level** over this 7-year period. California is the closest (Mann-Kendall τ=−0.619, p=0.069), driven by its 2020 wildfire peak and partial recovery. Houston is the only city with an upward direction (τ=+0.238). Limited statistical power with 7 annual data points is expected and does not rule out real underlying trends.

5. **The weekday–weekend AQI gap is real in four of six cities.** Houston (+4.50 AQI), Chicago (+4.27), Denver (+3.84) and New York (+3.38) all show positive gaps with 95% CIs entirely above zero. California and Seattle show no detectable gap — both are dominated by wildfire smoke, which has no weekly cycle.

6. **Screening-level health cost estimate: USD 58.1 billion (2020–2026)** across the six metro areas. California accounts for the largest single-year figure (USD 11.2B in 2020). The June 2023 Quebec event generated an estimated USD 7.2B in New York and USD 4.3B in Chicago — the costliest multi-city event in this dataset outside California's wildfire years.

> All health economic figures are screening-level estimates using the Pope et al. 2002 concentration-response function (6%/10 µg/m³) and HHS VSL USD 13.1M (2024). See methodology section below.

---

## Dashboard Tabs

| Tab | What it shows |
|-----|---------------|
| **Overview** | City-level risk scorecard: mean AQI, % unhealthy days, Mann-Kendall trend direction |
| **Per-City Detail** | Deep dive into one city: daily PM2.5 time series, seasonal heatmap, weekday vs. weekend gap with bootstrap 95% CI |
| **Trends** | Multi-city annual AQI trends with Theil-Sen slope and Mann-Kendall significance test |
| **Events** | Meteorological events (wildfire smoke, dust) linked to AQI spikes, with surface wind context |
| **Correlations** | Cross-city and cross-pollutant correlation heatmaps |

> **Note on 2026 data:** All charts show data through approximately June 2026. Because 2026 is incomplete, trend tests (Mann-Kendall) use only 2020–2025 to avoid seasonal bias from partial-year data. The 2026 line is shown as dashed to signal this.

---

## Methodology

### Trend detection
- **Mann-Kendall test** for monotonic trend detection (significance threshold p < 0.10), applied to annual mean AQI values
- **Theil-Sen slope** for robust trend magnitude estimation (median of pairwise slopes)
- Both tests use 2020–2025 only; 2026 is excluded as a partial year (data through ~July) to avoid downward seasonal bias for cities whose worst months are autumn (Seattle, California)

### Weekend effect
- **Bootstrap 95% CI** (10,000 resamples) for the weekday vs. weekend mean PM2.5 gap
- A gap whose CI crosses zero is reported as "no detectable gap", not as a reversal

### Population-weighted exposure
- **Person-days of PM2.5 exceedance:** county-level exceedance days × county population (Census ACS 2022)
- Population data sourced from Census ACS 2022 API (variable B01003\_001E) for all counties within each CBSA
- New York CBSA covers 22 counties across New York and New Jersey (full CBSA coverage)
- Metric captures both the intensity of an event and the population exposed to it

### Health economic screening model
- **Concentration-response function:** Pope et al. 2002 (ACS CPS-II cohort) — a 10 µg/m³ increase in long-term mean PM2.5 is associated with ~6% increase in all-cause mortality, applied here as 0.6%/µg/m³
- **Value of Statistical Life (VSL):** USD 13.1 million (2023 USD), U.S. Department of Health and Human Services standard regulatory value (HHS, January 2024)
- **Threshold:** EPA 24-hour NAAQS PM2.5 standard of 35 µg/m³

**Important caveats:** The Pope et al. 2002 coefficient was derived from chronic long-term exposure studies, not acute events. Its application to exceedance days is a known simplification — it likely overestimates risk for short acute episodes and underestimates it for cities with sustained elevated background levels. These figures are appropriate for order-of-magnitude risk communication and portfolio screening, not for regulatory analysis.

Note: EPA suspended monetization of PM2.5 health benefits in 2026 pending methodology review; HHS VSL is used here as an alternative federal reference value.

---

## Data Sources

| Source | Content | Access |
|--------|---------|--------|
| **EPA Air Quality System (AQS)** | Daily PM2.5, O3, PM10 and AQI by CBSA, 2020–2026 | [aqs.epa.gov/aqsweb/airdata](https://aqs.epa.gov/aqsweb/airdata/download_files.html) — public download |
| **EPA Meteorological Event Data** | Smoke and dust event flags | Included in AQS daily files |
| **Census ACS 2022** | County-level population for CBSA coverage | Census API — public |
| **NOAA surface wind** | Daily wind direction and speed (2023) | NOAA ISD — public |

Processed data is stored in `data/processed/` as Parquet files. The raw EPA CSV downloads are not committed to the repo (large files), but the processing notebook (`air_quality_usa.ipynb`) is fully reproducible from the public downloads.

---

## Project Structure

```
air-quality-usa/
├── app.py                        # Streamlit dashboard (main deliverable)
├── air_quality_usa.ipynb         # Full analysis notebook
├── requirements.txt
├── .gitignore                    # Excludes .env, raw CSVs, __pycache__
├── data/
│   ├── processed/
│   │   ├── air_quality_usa.parquet   # City-level daily AQI/PM2.5
│   │   ├── aqi_by_cbsa.parquet       # CBSA-level aggregated
│   │   └── meteo_events.parquet      # Smoke/dust event flags
│   └── county_population.csv         # Census ACS 2022 county populations
└── images/                       # Static chart exports
```

> **Note on `.env`:** A `.env` file with a `CENSUS_KEY` variable is used locally to access the Census API. It is listed in `.gitignore` and must never be committed to the repository.

---

## Running Locally

```bash
git clone https://github.com/AlonsoSheila/air-quality-usa.git
cd air-quality-usa
pip install -r requirements.txt
streamlit run app.py
```

To reproduce the full notebook from raw EPA data:
1. Download daily AQI by CBSA files for 2020–2026 from [EPA AQS](https://aqs.epa.gov/aqsweb/airdata/download_files.html)
2. Place them in `data/raw/`
3. Obtain a free Census API key at [api.census.gov/data/key\_signup.html](https://api.census.gov/data/key_signup.html) and add it to `.env` as `CENSUS_KEY=your_key_here`
4. Open `air_quality_usa.ipynb` and run all cells

---

## Analysis Sections

1. Setup and Data Loading
2. Data Quality Check
3. Headline Comparison: AQI Across Cities
4. Per-City Detail
5. County-Level Detail Within Each CBSA
   - 5.2 Population-Weighted Exposure: Person-Days of PM2.5 Exceedance
6. Documented Events: Wind Context
7. Cross-City Correlations
8. Year-Over-Year Trend
   - 8.2 Statistical Significance (Mann-Kendall Test)
9. Weekday vs. Weekend
10. Resolving Open Questions From Section 4
11. Health Economic Impact Estimate
    - Risk Implications for Business and Investment Decisions
12. Conclusions

---

## Technologies

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Pandas](https://img.shields.io/badge/Pandas-2.0-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red)
![Plotly](https://img.shields.io/badge/Plotly-5.20-blueviolet)
![Scipy](https://img.shields.io/badge/SciPy-1.13-blue)

Methodology: Exploratory Data Analysis, Statistical Trend Detection (Mann-Kendall / Theil-Sen), Bootstrap Inference, Population-Weighted Exposure Analysis, Health Economic Screening

---

## About this Project

This project is part of a data science portfolio focused on Climate Risk Analytics, combining environmental datasets, statistical methods, and risk assessment frameworks.

## Author

**Sheila Alonso** — Data Analyst | Climate Risk & ESG  
[GitHub](https://github.com/AlonsoSheila) · [LinkedIn](https://www.linkedin.com/in/sheila-alonso-rodriguez/)
