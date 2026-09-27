# Healthcare Encounter Reconciliation Pipeline

A small, self-contained Python ETL pipeline that reconciles patient encounter
records from two different source systems — an EHR (clinical) system and a
billing/claims system — the same "does system A agree with system B" problem
that comes up constantly in real healthcare data quality work.

**All data in this project is synthetic** (randomly generated), created only
to demonstrate the pipeline. No real patient information is used anywhere.

## Why this project

This started as a hands-on project to build real, practical experience with
Python-based data pipelines, Git version control, and automated testing —
skills that complement my SQL/BI-heavy professional background as a data
analyst working with large-scale enterprise healthcare data.

## Architecture

```
generate_synthetic_data.py    Creates two synthetic source-system CSVs
        |
        v
pipeline/extract.py           Reads + schema-validates both CSVs
        |
        v
pipeline/transform.py         Cleans, de-duplicates, and reconciles the two
                               sources on encounter_id; classifies each
                               encounter as MATCHED / MISSING_IN_BILLING /
                               INVALID_DATE / NULL_AMOUNT; computes summary
                               data-quality metrics (match rate, etc.)
        |
        v
pipeline/load.py              Loads the reconciled dataset into SQLite and
                               writes a JSON + CSV data-quality report
        |
        v
main.py                       Orchestrates the full run, with logging at
                               every stage (console + logs/pipeline_run.log)
```

## What it catches

The synthetic billing data intentionally includes the kinds of real-world
discrepancies a reconciliation pipeline has to handle:

- Encounters missing from billing entirely (not yet submitted)
- Corrupted/mismatched encounter dates
- Null claim amounts
- Duplicate claim submissions

## Running it

```bash
pip install -r requirements.txt
python generate_synthetic_data.py   # writes data/ehr_encounters.csv, data/billing_claims.csv
python main.py                      # runs the full pipeline
pytest                              # runs the unit tests
```

Output lands in `output/` (SQLite DB + data quality report) and `logs/`
(pipeline run log) — both are git-ignored since they're generated artifacts,
not source.

## Testing

`tests/test_transform.py` covers the core reconciliation logic: duplicate
removal, and each of the anomaly classifications (missing, invalid date,
null amount), plus the summary metric calculation.

## Possible next steps

- Swap the SQLite target for a real warehouse connection (e.g., a cloud SQL
  instance) to more closely mirror a production setup
- Add a scheduler (e.g., cron, Airflow, or Microsoft Fabric pipelines) to run
  this on a recurring cadence
- Add CI (GitHub Actions) to run `pytest` automatically on every push
