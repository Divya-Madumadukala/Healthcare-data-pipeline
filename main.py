"""
main.py - Pipeline entry point.

Orchestrates the full extract -> transform -> load run:
  1. Extract:   read the two raw source CSVs
  2. Transform: clean + reconcile them, compute data-quality metrics
  3. Load:      write the reconciled data to SQLite, write the QA report

Run with:  python main.py
"""
from pathlib import Path

from pipeline.extract import extract_ehr_encounters, extract_billing_claims
from pipeline.transform import clean_claims, reconcile, compute_quality_metrics
from pipeline.load import load_to_sqlite, write_quality_report
from pipeline.logger_config import get_logger

logger = get_logger("main")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"


def run_pipeline():
    logger.info("Pipeline run started")

    # 1. Extract
    ehr_df = extract_ehr_encounters(DATA_DIR)
    claims_df = extract_billing_claims(DATA_DIR)

    # 2. Transform
    claims_df = clean_claims(claims_df)
    reconciled_df = reconcile(ehr_df, claims_df)
    metrics = compute_quality_metrics(reconciled_df)

    # 3. Load
    load_to_sqlite(reconciled_df, OUTPUT_DIR / "healthcare_data.db")
    write_quality_report(metrics, OUTPUT_DIR)

    logger.info("Pipeline run completed successfully")
    return metrics


if __name__ == "__main__":
    result = run_pipeline()
    print("\nFinal data quality summary:")
    for k, v in result.items():
        print(f"  {k}: {v}")
