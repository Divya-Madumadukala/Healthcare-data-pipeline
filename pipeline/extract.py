"""
extract.py - Extract stage.

Reads the two raw source-system CSVs into pandas DataFrames and runs a
lightweight schema check on each, so a malformed source file fails fast
and loudly instead of silently corrupting everything downstream.
"""
from pathlib import Path

import pandas as pd

from pipeline.logger_config import get_logger

logger = get_logger("extract")

EXPECTED_EHR_COLUMNS = {"encounter_id", "patient_id", "encounter_date", "provider", "diagnosis_code", "status"}
EXPECTED_CLAIMS_COLUMNS = {"claim_id", "encounter_id", "patient_id", "encounter_date", "claim_amount", "payer"}


def _validate_schema(df: pd.DataFrame, expected_columns: set, source_name: str) -> None:
    actual = set(df.columns)
    missing = expected_columns - actual
    if missing:
        raise ValueError(f"{source_name} is missing expected columns: {missing}")
    logger.info(f"{source_name}: schema OK ({len(df.columns)} columns, {len(df)} rows)")


def extract_ehr_encounters(data_dir: Path) -> pd.DataFrame:
    path = data_dir / "ehr_encounters.csv"
    df = pd.read_csv(path, dtype=str)
    _validate_schema(df, EXPECTED_EHR_COLUMNS, "ehr_encounters.csv")
    return df


def extract_billing_claims(data_dir: Path) -> pd.DataFrame:
    path = data_dir / "billing_claims.csv"
    df = pd.read_csv(path, dtype=str)
    _validate_schema(df, EXPECTED_CLAIMS_COLUMNS, "billing_claims.csv")
    return df
