"""
generate_synthetic_data.py

Generates two SYNTHETIC source-system extracts that simulate a common healthcare
data-quality problem: reconciling patient encounter/claim records that originate
from two different systems (an EHR system and a billing/claims system) which
don't always agree.

No real patient data is used anywhere in this project - all names, IDs, dates,
and amounts are randomly generated for demonstration purposes only.
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)  # reproducible output

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

PROVIDERS = ["Dr. Chen", "Dr. Patel", "Dr. Nguyen", "Dr. Okafor", "Dr. Silva"]
DIAGNOSIS_CODES = ["E11.9", "I10", "J45.909", "M54.5", "K21.9", "F41.1", "N39.0"]
STATUSES = ["Completed", "Pending", "Cancelled"]

NUM_ENCOUNTERS = 5000


def random_date(start_year=2025):
    start = date(start_year, 1, 1)
    return start + timedelta(days=random.randint(0, 364))


def generate_ehr_encounters():
    """System 1: EHR encounter log (clinical source of truth)."""
    rows = []
    for i in range(1, NUM_ENCOUNTERS + 1):
        encounter_id = f"ENC{i:06d}"
        rows.append({
            "encounter_id": encounter_id,
            "patient_id": f"PT{random.randint(1, 1200):05d}",
            "encounter_date": random_date().isoformat(),
            "provider": random.choice(PROVIDERS),
            "diagnosis_code": random.choice(DIAGNOSIS_CODES),
            "status": random.choice(STATUSES),
        })
    path = DATA_DIR / "ehr_encounters.csv"
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return rows, path


def generate_billing_claims(ehr_rows):
    """
    System 2: Billing/claims extract. Intentionally introduces the kinds of
    discrepancies a real reconciliation pipeline has to catch:
      - ~4% of encounters are missing from billing (not yet submitted)
      - ~3% have a mismatched/corrupted encounter_date
      - ~2% have a null/blank claim_amount
      - ~1.5% are duplicated (submitted twice by mistake)
    """
    rows = []
    for row in ehr_rows:
        r = random.random()
        if r < 0.04:
            continue  # missing from billing entirely

        claim_amount = round(random.uniform(45.0, 2400.0), 2)
        encounter_date = row["encounter_date"]

        if r < 0.07:  # date mismatch/corruption
            encounter_date = "1900-01-01"

        if r < 0.09:  # null amount
            claim_amount = ""

        rows.append({
            "claim_id": f"CLM{row['encounter_id'][3:]}",
            "encounter_id": row["encounter_id"],
            "patient_id": row["patient_id"],
            "encounter_date": encounter_date,
            "claim_amount": claim_amount,
            "payer": random.choice(["Medi-Cal", "Medicare", "Commercial-BCBS", "Commercial-Aetna"]),
        })

        if r < 0.105:  # duplicate submission
            rows.append(dict(rows[-1]))

    path = DATA_DIR / "billing_claims.csv"
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return rows, path


if __name__ == "__main__":
    ehr_rows, ehr_path = generate_ehr_encounters()
    claims_rows, claims_path = generate_billing_claims(ehr_rows)
    print(f"Generated {len(ehr_rows)} synthetic EHR encounters -> {ehr_path}")
    print(f"Generated {len(claims_rows)} synthetic billing claims -> {claims_path}")
