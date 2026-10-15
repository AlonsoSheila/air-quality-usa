"""
scripts/build_dataset.py

Reads every raw CSV in data/, normalizes it with etl.py, and writes:
  - data/processed/air_quality_usa.parquet   (daily PM2.5, O3, PM10, 6 cities)
  - data/processed/aqi_by_cbsa.parquet       (daily composite AQI, 6 cities)
  - data/processed/meteo_events.parquet      (wind + temperature, event months only)

Run from the repo root:
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

    print("Loading PM2.5 / O3 / PM10 for the 6 cities...")
    pollutants_df = etl.load_all_pollutants(regions)
    print(f"  -> {len(pollutants_df):,} rows")

    print("\nLoading composite AQI by CBSA...")
    aqi_df = etl.load_aqi_by_cbsa(regions)
    print(f"  -> {len(aqi_df):,} rows")

    print("\nLoading wind/temperature for the event months...")
    meteo_df = etl.load_meteo_for_events(regions, events)
    print(f"  -> {len(meteo_df):,} rows")

    pollutants_df.to_parquet(out_dir / "air_quality_usa.parquet", index=False)
    aqi_df.to_parquet(out_dir / "aqi_by_cbsa.parquet", index=False)
    meteo_df.to_parquet(out_dir / "meteo_events.parquet", index=False)

    print(f"\nDone. Files saved to {out_dir}/")


if __name__ == "__main__":
    main()
