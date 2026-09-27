"""
load.py - Load stage.

Writes the reconciled dataset into a SQLite database (standing in for a real
data warehouse target) and writes the data-quality summary out as both a JSON
file (machine-readable, e.g. for an alerting job) and a CSV (human-readable).
"""
import json
import sqlite3
from pathlib import Path

import pandas as pd

from pipeline.logger_config import get_logger

logger = get_logger("load")


def load_to_sqlite(reconciled_df: pd.DataFrame, db_path: Path) -> None:
    db_path.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        reconciled_df.to_sql("encounter_reconciliation", conn, if_exists="replace", index=False)
        logger.info(f"Loaded {len(reconciled_df)} rows into {db_path} (table: encounter_reconciliation)")
    finally:
        conn.close()


def write_quality_report(metrics: dict, output_dir: Path) -> None:
    output_dir.mkdir(exist_ok=True)

    json_path = output_dir / "data_quality_report.json"
    with open(json_path, "w") as f:
        json.dump(metrics, f, indent=2)

    csv_path = output_dir / "data_quality_report.csv"
    pd.DataFrame([metrics]).to_csv(csv_path, index=False)

    logger.info(f"Wrote data quality report -> {json_path} and {csv_path}")
