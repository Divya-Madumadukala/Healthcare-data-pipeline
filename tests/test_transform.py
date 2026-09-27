"""
Unit tests for the transform/reconciliation logic - the part of the pipeline
most worth testing, since a bug here would silently mis-flag real records.

Run with:  pytest
"""
import pandas as pd

from pipeline.transform import clean_claims, reconcile, compute_quality_metrics


def _sample_ehr():
    return pd.DataFrame([
        {"encounter_id": "ENC1", "patient_id": "PT1", "encounter_date": "2026-01-05",
         "provider": "Dr. Chen", "diagnosis_code": "I10", "status": "Completed"},
        {"encounter_id": "ENC2", "patient_id": "PT2", "encounter_date": "2026-02-10",
         "provider": "Dr. Patel", "diagnosis_code": "E11.9", "status": "Completed"},
        {"encounter_id": "ENC3", "patient_id": "PT3", "encounter_date": "2026-03-01",
         "provider": "Dr. Nguyen", "diagnosis_code": "J45.909", "status": "Pending"},
    ])


def test_clean_claims_removes_exact_duplicates():
    claims = pd.DataFrame([
        {"claim_id": "CLM1", "encounter_id": "ENC1", "patient_id": "PT1",
         "encounter_date": "2026-01-05", "claim_amount": "100.00", "payer": "Medi-Cal"},
        {"claim_id": "CLM1", "encounter_id": "ENC1", "patient_id": "PT1",
         "encounter_date": "2026-01-05", "claim_amount": "100.00", "payer": "Medi-Cal"},
    ])
    cleaned = clean_claims(claims)
    assert len(cleaned) == 1


def test_reconcile_flags_missing_in_billing():
    ehr = _sample_ehr()
    claims = pd.DataFrame([
        {"claim_id": "CLM1", "encounter_id": "ENC1", "patient_id": "PT1",
         "encounter_date": "2026-01-05", "claim_amount": "100.00", "payer": "Medi-Cal"},
    ])
    claims = clean_claims(claims)
    result = reconcile(ehr, claims)

    status_by_encounter = dict(zip(result["encounter_id"], result["reconciliation_status"]))
    assert status_by_encounter["ENC1"] == "MATCHED"
    assert status_by_encounter["ENC2"] == "MISSING_IN_BILLING"
    assert status_by_encounter["ENC3"] == "MISSING_IN_BILLING"


def test_reconcile_flags_invalid_date():
    ehr = _sample_ehr()
    claims = pd.DataFrame([
        {"claim_id": "CLM1", "encounter_id": "ENC1", "patient_id": "PT1",
         "encounter_date": "1900-01-01", "claim_amount": "100.00", "payer": "Medi-Cal"},
    ])
    claims = clean_claims(claims)
    result = reconcile(ehr, claims)
    row = result[result["encounter_id"] == "ENC1"].iloc[0]
    assert row["reconciliation_status"] == "INVALID_DATE"


def test_reconcile_flags_null_amount():
    ehr = _sample_ehr()
    claims = pd.DataFrame([
        {"claim_id": "CLM1", "encounter_id": "ENC1", "patient_id": "PT1",
         "encounter_date": "2026-01-05", "claim_amount": "", "payer": "Medi-Cal"},
    ])
    claims = clean_claims(claims)
    result = reconcile(ehr, claims)
    row = result[result["encounter_id"] == "ENC1"].iloc[0]
    assert row["reconciliation_status"] == "NULL_AMOUNT"


def test_compute_quality_metrics_match_rate():
    ehr = _sample_ehr()
    claims = pd.DataFrame([
        {"claim_id": "CLM1", "encounter_id": "ENC1", "patient_id": "PT1",
         "encounter_date": "2026-01-05", "claim_amount": "100.00", "payer": "Medi-Cal"},
    ])
    claims = clean_claims(claims)
    reconciled = reconcile(ehr, claims)
    metrics = compute_quality_metrics(reconciled)

    assert metrics["total_ehr_encounters"] == 3
    assert metrics["matched"] == 1
    assert metrics["match_rate_pct"] == round(1 / 3 * 100, 2)
