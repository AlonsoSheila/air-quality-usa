"""
scripts/build_dataset.py

Lee todos los CSV crudos de data/, los normaliza con etl.py, y genera:
  - data/processed/air_quality_usa.parquet   (PM2.5, O3, PM10 diario, 6 ciudades)
  - data/processed/aqi_by_cbsa.parquet       (AQI compuesto diario, 6 ciudades)
  - data/processed/meteo_events.parquet      (viento+temp, solo meses de evento)

Ejecutar desde la raíz del repo:
    python scripts/build_dataset.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import etl  # noqa: E402


def main():
    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)

    regions = etl.load_regions("regions.csv")
    events = etl.load_events("events.csv")

    print("Cargando PM2.5 / O3 / PM10 para las 6 ciudades...")
    pollutants_df = etl.load_all_pollutants(regions)
    print(f"  -> {len(pollutants_df):,} filas")

    print("\nCargando AQI compuesto por CBSA...")
    aqi_df = etl.load_aqi_by_cbsa(regions)
    print(f"  -> {len(aqi_df):,} filas")

    print("\nCargando viento/temperatura para los meses de evento...")
    meteo_df = etl.load_meteo_for_events(regions, events)
    print(f"  -> {len(meteo_df):,} filas")

    pollutants_df.to_parquet(out_dir / "air_quality_usa.parquet", index=False)
    aqi_df.to_parquet(out_dir / "aqi_by_cbsa.parquet", index=False)
    meteo_df.to_parquet(out_dir / "meteo_events.parquet", index=False)

    print(f"\nListo. Archivos guardados en {out_dir}/")


if __name__ == "__main__":
    main()
