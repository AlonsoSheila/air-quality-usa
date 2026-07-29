"""
etl.py — módulo compartido de carga y limpieza para el proyecto air-quality-usa.

Usado tanto por los notebooks de análisis como por scripts/build_dataset.py
(que genera el parquet final que consume el dashboard).

Espera que exista una carpeta `data/` con:
  - {pollutant}_{year}_{City}.csv   -> pm25 / o3 / pm10, 2020-2026, 6 ciudades
  - daily_aqi_by_cbsa_{year}.csv    -> archivo nacional, 2020-2026
  - daily_WIND_{year}.csv           -> archivo nacional (solo años con eventos)
  - daily_TEMP_{year}.csv           -> archivo nacional (solo años con eventos)

y dos archivos de configuración en la raíz del repo: regions.csv, events.csv
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
    """Normaliza un CSV crudo de EPA (Download Daily Data) a un esquema común.

    Devuelve un DataFrame vacío (no un error) si la columna esperada no
    existe, para que el llamador pueda avisar en vez de fallar en silencio.
    """
    value_col = POLLUTANT_COLUMN[pollutant]
    if value_col not in df.columns:
        return pd.DataFrame(columns=["date", "city", "pollutant", "value", "unit", "county", "aqi"])

    out = pd.DataFrame({
        "date": pd.to_datetime(df["Date"]),
        "city": city,
        "pollutant": pollutant,
        "value": pd.to_numeric(df[value_col], errors="coerce"),
        "unit": POLLUTANT_UNIT[pollutant],
        "county": df.get("County"),
        "aqi": pd.to_numeric(df.get("Daily AQI Value"), errors="coerce"),
    })
    out = out.dropna(subset=["value"])
    out = out[out["value"] >= 0]  # descarta negativos (error de sensor)
    return out


def load_pollutant(pollutant, city, file_key, years=YEARS, data_dir=DATA_DIR):
    """Carga y concatena todos los años de un contaminante para una ciudad,
    avisando en voz alta si algún año produce 0 filas (posible cambio de
    nombre de columna en el CSV de origen, o archivo no descargado).

    `file_key` es el nombre tal cual aparece en el archivo (ej. "NewYork",
    sin espacio); `city` es el nombre bonito que se guarda en los datos
    para mostrar (ej. "New York")."""
    frames = []
    for year in years:
        fname = data_dir / f"{pollutant}_{year}_{file_key}.csv"
        if not fname.exists():
            print(f"  ⚠ WARNING: no existe {fname}, se omite ese año")
            continue
        raw = pd.read_csv(fname)
        norm = normalize_pollutant_file(raw, pollutant, city)
        if len(norm) == 0:
            print(f"  ⚠ WARNING: {fname.name} produjo 0 filas normalizadas — "
                  f"revisa si la columna '{POLLUTANT_COLUMN[pollutant]}' existe en ese archivo")
        frames.append(norm)
    if not frames:
        return pd.DataFrame(columns=["date", "city", "pollutant", "value", "unit", "county", "aqi"])
    return pd.concat(frames, ignore_index=True)


def load_all_pollutants(regions, pollutants=("pm25", "o3", "pm10"), years=YEARS, data_dir=DATA_DIR):
    """Carga los 3 contaminantes para las 6 ciudades de regions.csv."""
    frames = []
    for _, row in regions.iterrows():
        for pollutant in pollutants:
            frames.append(load_pollutant(pollutant, row["city"], row["file_key"], years, data_dir))
    return pd.concat(frames, ignore_index=True)


def load_aqi_by_cbsa(regions, years=YEARS, data_dir=DATA_DIR):
    """Carga el AQI compuesto diario (archivo nacional) y filtra a las 6 CBSA."""
    cbsa_to_city = dict(zip(regions["cbsa_name"], regions["city"]))
    frames = []
    for year in years:
        fname = data_dir / f"daily_aqi_by_cbsa_{year}.csv"
        if not fname.exists():
            print(f"  ⚠ WARNING: no existe {fname}")
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
        print(f"  ⚠ WARNING: sin datos de AQI por CBSA para: {missing}")
    return result


def load_meteo_for_events(regions, events, data_dir=DATA_DIR):
    """Carga viento y temperatura solo para los meses de evento listados en
    events.csv (los archivos nacionales de meteorología son grandes, no
    tiene sentido cargar años enteros que no se van a usar)."""
    cbsa_to_city = dict(zip(regions["cbsa_name"], regions["city"]))
    years_needed = sorted(events["event_year"].unique())

    wind_frames, temp_frames = [], []
    for year in years_needed:
        wind_fname = data_dir / f"daily_WIND_{year}.csv"
        temp_fname = data_dir / f"daily_TEMP_{year}.csv"

        if wind_fname.exists():
            w = pd.read_csv(wind_fname)
            w = w[w["CBSA Name"].isin(cbsa_to_city.keys())].copy()
            w["city"] = w["CBSA Name"].map(cbsa_to_city)
            w["date"] = pd.to_datetime(w["Date Local"])
            wind_frames.append(w[["date", "city", "Parameter Name", "Arithmetic Mean", "Units of Measure"]])
        else:
            print(f"  ⚠ WARNING: no existe {wind_fname}")

        if temp_fname.exists():
            t = pd.read_csv(temp_fname)
            t = t[t["CBSA Name"].isin(cbsa_to_city.keys())].copy()
            t["city"] = t["CBSA Name"].map(cbsa_to_city)
            t["date"] = pd.to_datetime(t["Date Local"])
            temp_frames.append(t[["date", "city", "Parameter Name", "Arithmetic Mean", "Units of Measure"]])
        else:
            print(f"  ⚠ WARNING: no existe {temp_fname}")

    wind = pd.concat(wind_frames, ignore_index=True) if wind_frames else pd.DataFrame()
    temp = pd.concat(temp_frames, ignore_index=True) if temp_frames else pd.DataFrame()
    meteo = pd.concat([wind, temp], ignore_index=True)

    # Filtra cada fila al mes de evento correspondiente a su ciudad+año
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
