"""
etl.py: shared loading and cleaning module for the air-quality-usa project.

Used by the analysis notebook and by scripts/build_dataset.py
(which builds the final parquet files read by the dashboard).

Expects a `data/` folder containing the raw EPA downloads:
  - {pollutant}_{year}_{City}.csv   -> pm25 / o3 / pm10, 2020-2026, 6 cities
  - daily_aqi_by_cbsa_{year}.csv    -> national file, 2020-2026
  - daily_WIND_{year}.csv           -> national file (only years with events)
  - daily_TEMP_{year}.csv           -> national file (only years with events)

and two configuration files in the repo root: regions.csv, events.csv
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")
POLLUTANT_COLUMN = {
    "pm25": "Daily Mean PM2.5 Concentration",
    "pm10": "Daily Mean PM10 Concentration",
    "o3": "Daily Max 8-hour Ozone Concentration",
}
POLLUTANT_UNIT = {
    "pm25": "µg/m³",
    "pm10": "µg/m³",
    "o3": "ppm",
}

YEARS = range(2020, 2027)


def load_regions(path="regions.csv"):
    return pd.read_csv(path)


def load_events(path="events.csv"):
    return pd.read_csv(path)


def normalize_pollutant_file(df, pollutant, city):
    """Normalize a raw EPA CSV (Download Daily Data) to a common schema.

    Returns an empty DataFrame (not an error) if the expected column is
    missing, so the caller can warn instead of failing silently.
    """
    value_col = POLLUTANT_COLUMN[pollutant]
    if value_col not in df.columns:
        return pd.DataFrame(columns=["date", "city", "pollutant", "value", "unit", "county", "aqi", "site_name", "latitude", "longitude"])

    out = pd.DataFrame({
        "date": pd.to_datetime(df["Date"]),
        "city": city,
        "pollutant": pollutant,
        "value": pd.to_numeric(df[value_col], errors="coerce"),
        "unit": POLLUTANT_UNIT[pollutant],
        "county": df.get("County"),
        "aqi": pd.to_numeric(df.get("Daily AQI Value"), errors="coerce"),
        "site_name": df.get("Local Site Name"),
        "latitude": pd.to_numeric(df.get("Site Latitude"), errors="coerce"),
        "longitude": pd.to_numeric(df.get("Site Longitude"), errors="coerce"),
    })
    out = out.dropna(subset=["value"])
    out = out[out["value"] >= 0]  # drop negative values (sensor error)
    return out


def load_pollutant(pollutant, city, file_key, years=YEARS, data_dir=DATA_DIR):
    """Load and concatenate all years of one pollutant for one city,
    warning loudly if a year produces 0 rows (possible column rename in
    the source CSV, or a file that was not downloaded).

    `file_key` is the name as it appears in the file name (e.g. "NewYork",
    no space); `city` is the display name stored in the data
    (e.g. "New York")."""
    frames = []
    for year in years:
        fname = data_dir / f"{pollutant}_{year}_{file_key}.csv"
        if not fname.exists():
            print(f"  ⚠ WARNING: {fname} does not exist, skipping that year")
            continue
        raw = pd.read_csv(fname)
        norm = normalize_pollutant_file(raw, pollutant, city)
        if len(norm) == 0:
            print(f"  ⚠ WARNING: {fname.name} produced 0 normalized rows — "
                  f"check that the column '{POLLUTANT_COLUMN[pollutant]}' exists in that file")
        frames.append(norm)
    if not frames:
        return pd.DataFrame(columns=["date", "city", "pollutant", "value", "unit", "county", "aqi", "site_name", "latitude", "longitude"])
    return pd.concat(frames, ignore_index=True)


def load_all_pollutants(regions, pollutants=("pm25", "o3", "pm10"), years=YEARS, data_dir=DATA_DIR):
    """Load the 3 pollutants for the 6 cities listed in regions.csv."""
    frames = []
    for _, row in regions.iterrows():
        for pollutant in pollutants:
            frames.append(load_pollutant(pollutant, row["city"], row["file_key"], years, data_dir))
    return pd.concat(frames, ignore_index=True)


def load_aqi_by_cbsa(regions, years=YEARS, data_dir=DATA_DIR):
    """Load the daily composite AQI (national file) and keep the 6 CBSAs."""
    cbsa_to_city = dict(zip(regions["cbsa_name"], regions["city"]))
    frames = []
    for year in years:
        fname = data_dir / f"daily_aqi_by_cbsa_{year}.csv"
        if not fname.exists():
            print(f"  ⚠ WARNING: {fname} does not exist")
            continue
        raw = pd.read_csv(fname)
        raw = raw[raw["CBSA"].isin(cbsa_to_city.keys())].copy()
        raw["city"] = raw["CBSA"].map(cbsa_to_city)
        raw["date"] = pd.to_datetime(raw["Date"])
        frames.append(raw.rename(columns={
            "AQI": "aqi_composite",
            "Category": "aqi_category",
            "Defining Parameter": "aqi_defining_parameter",
        })[["date", "city", "aqi_composite", "aqi_category", "aqi_defining_parameter"]])
    if not frames:
        return pd.DataFrame(columns=["date", "city", "aqi_composite", "aqi_category", "aqi_defining_parameter"])
    result = pd.concat(frames, ignore_index=True)
    found_cities = set(result["city"].unique())
    missing = set(regions["city"]) - found_cities
    if missing:
        print(f"  ⚠ WARNING: no CBSA AQI data for: {missing}")
    return result


def load_meteo_for_events(regions, events, data_dir=DATA_DIR):
    """Load wind and temperature only for the event months listed in
    events.csv (the national weather files are large, so there is no
    point loading whole years that will not be used)."""
    cbsa_to_city = dict(zip(regions["cbsa_name"], regions["city"]))
    years_needed = sorted(events["event_year"].unique())

    wind_frames, temp_frames = [], []
    for year in years_needed:
        wind_fname = data_dir / f"daily_WIND_{year}.csv"
        temp_fname = data_dir / f"daily_TEMP_{year}.csv"

        if wind_fname.exists():
            w = pd.read_csv(wind_fname, dtype={"Event Type": "string"}, low_memory=False)
            w = w[w["CBSA Name"].isin(cbsa_to_city.keys())].copy()
            w["city"] = w["CBSA Name"].map(cbsa_to_city)
            w["date"] = pd.to_datetime(w["Date Local"])
            wind_frames.append(w[["date", "city", "Parameter Name", "Arithmetic Mean", "Units of Measure"]])
        else:
            print(f"  ⚠ WARNING: {wind_fname} does not exist")

        if temp_fname.exists():
            t = pd.read_csv(temp_fname, dtype={"Event Type": "string"}, low_memory=False)
            t = t[t["CBSA Name"].isin(cbsa_to_city.keys())].copy()
            t["city"] = t["CBSA Name"].map(cbsa_to_city)
            t["date"] = pd.to_datetime(t["Date Local"])
            temp_frames.append(t[["date", "city", "Parameter Name", "Arithmetic Mean", "Units of Measure"]])
        else:
            print(f"  ⚠ WARNING: {temp_fname} does not exist")

    wind = pd.concat(wind_frames, ignore_index=True) if wind_frames else pd.DataFrame()
    temp = pd.concat(temp_frames, ignore_index=True) if temp_frames else pd.DataFrame()
    meteo = pd.concat([wind, temp], ignore_index=True)

    # Keep only the rows that fall in each city's event month and year
    keep_masks = []
    for _, ev in events.iterrows():
        mask = (
            (meteo["city"] == ev["city"])
            & (meteo["date"].dt.year == ev["event_year"])
            & (meteo["date"].dt.month == ev["event_month"])
        )
        keep_masks.append(mask)
    if keep_masks:
        combined_mask = keep_masks[0]
        for m in keep_masks[1:]:
            combined_mask |= m
        meteo = meteo[combined_mask]

    return meteo.rename(columns={
        "Parameter Name": "parameter",
        "Arithmetic Mean": "value",
        "Units of Measure": "unit",
    })
