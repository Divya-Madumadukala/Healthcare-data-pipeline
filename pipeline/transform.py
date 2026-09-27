"""
transform.py - Transform / reconciliation / data-quality stage.

This is the heart of the pipeline: it reconciles the EHR encounter log against
the billing claims extract (the same "does system A agree with system B"
problem behind most healthcare data-quality work), flags specific anomaly
types, and computes summary data-quality metrics.
"""
from datetime import date

import pandas as pd

from pipeline.logger_config import get_logger

logger = get_logger("transform")

SENTINEL_BAD_DATE = "1900-01-01"


def clean_claims(claims_df: pd.DataFrame) -> pd.DataFrame:
    """De-duplicate exact-duplicate claim rows and standardize types."""
    before = len(claims_df)
    claims_df = claims_df.drop_duplicates(subset=["claim_id", "encounter_id"], keep="first").copy()
    removed = before - len(claims_df)
    if removed:
        logger.info(f"Removed {removed} duplicate claim rows ({removed / before:.1%} of raw claims)")

    claims_df["claim_amount"] = pd.to_numeric(claims_df["claim_amount"], errors="coerce")
    return claims_df


def reconcile(ehr_df: pd.DataFrame, claims_df: pd.DataFrame) -> pd.DataFrame:
    """
    Left-join EHR encounters to billing claims on encounter_id and classify
    each encounter into one of: MATCHED, MISSING_IN_BILLING,
    INVALID_DATE, NULL_AMOUNT.
    """
    merged = ehr_df.merge(
        claims_df, on="encounter_id", how="left", suffixes=("_ehr", "_claim")
    )

    def classify(row):
        if pd.isna(row.get("claim_id")):
            return "MISSING_IN_BILLING"
        if row.get("encounter_date_claim") == SENTINEL_BAD_DATE:
            return "INVALID_DATE"
        if pd.isna(row.get("claim_amount")):
            return "NULL_AMOUNT"
        return "MATCHED"

    merged["reconciliation_status"] = merged.apply(classify, axis=1)
    logger.info("Reconciliation complete: " + merged["reconciliation_status"].value_counts().to_dict().__repr__())
    return merged


def compute_quality_metrics(reconciled_df: pd.DataFrame) -> dict:
    total = len(reconciled_df)
    counts = reconciled_df["reconciliation_status"].value_counts().to_dict()
    matched = counts.get("MATCHED", 0)

    metrics = {
        "run_date": date.today().isoformat(),
        "total_ehr_encounters": total,
        "matched": matched,
        "match_rate_pct": round(matched / total * 100, 2) if total else 0.0,
        "missing_in_billing": counts.get("MISSING_IN_BILLING", 0),
        "invalid_date": counts.get("INVALID_DATE", 0),
        "null_amount": counts.get("NULL_AMOUNT", 0),
    }
    logger.info(f"Data quality summary: {metrics}")
    return metrics
