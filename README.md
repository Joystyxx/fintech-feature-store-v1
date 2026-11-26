# Fintech Feature Store & Fraud Risk Engine (DuckDB + Redis + Streamlit)

This repository contains an end-to-end MLOps pipeline that ingests raw fintech data, builds a Dual-Store Feature Store (Offline Parquet + Online Redis), enforces a CI/CD parity gate to eliminate Train/Serve Skew, and deploys an interactive Streamlit dashboard for real-time fraud inference.

The goal of this project is not just to serve features, but to prove an understanding of the full ML lifecycle—from schema conforming and point-in-time temporal joins to low-latency caching, model serving, and operational runbooks.

**Live Demo:** [https://fintech-feature-store-v1.streamlit.app/](https://fintech-feature-store-v1.streamlit.app/)

## Architecture

1. **Define:** An immutable `registry.py` acts as the single source of truth for all 25 features, dictating types, freshness SLAs, and source paths.
2. **Ingest:** A script downloads real Kaggle fintech data, maps the messy schema to our data contract, and writes it to Parquet files.
3. **Offline Store:** DuckDB queries Parquet files using `ASOF JOIN` to guarantee point-in-time correctness for training (preventing data leakage).
4. **Materialize:** A batch job queries the latest state from DuckDB and writes it to Redis for low-latency serving.
5. **Parity Gate:** A Pytest suite compares the Offline (DuckDB) and Online (Redis) values at the exact same timestamp to detect skew.
6. **Serve:** A Streamlit UI queries Redis, verifies parity, and runs a heuristic rules engine to approve or block transactions.

## Tech Stack

- **Offline Store:** DuckDB 2.0, Parquet, Pandas
- **Online Store:** Redis (`fakeredis` for local testing)
- **Serving Layer:** Streamlit
- **Testing:** Pytest
- **Environment:** Python 3.14 (Windows/Linux), `uv` package installer (on Streamlit Cloud)

## Key Engineering Decisions

- **Point-in-Time Correctness (The `ASOF JOIN`):** Standard SQL joins in a training pipeline cause catastrophic data leakage (e.g., a transaction at 2:00 PM seeing feature values calculated at 3:00 PM). We use DuckDB's `ASOF JOIN` (`label_timestamp >= event_timestamp`) to ensure the model only sees data that existed exactly at the time of the transaction.
- **Idempotency in the Batch Pipeline:** During the initial build, looping through multiple feature families caused a `CatalogException: Table already exists`. We refactored the SQL to use `CREATE OR REPLACE TEMP TABLE` to ensure the materialization pipeline is fully idempotent. If an Airflow job fails and retries, it will not crash.
- **The Null-Safety Contract:** If a feature fails to materialize (e.g., the Redis sync lags), the FastAPI layer must not silently impute `0`, which would skew the model. The API explicitly returns a `missing[]` array. The ML model consumes this array to differentiate between "zero transactions" and "data unavailable."
- **Schema Conforming:** The Kaggle dataset is messy. We built an ingestion adapter that maps the raw schema (e.g., `transactions_last_1h`, `account_age_months`) into the exact data contract required by the Registry (e.g., `txn_count_1h`, `account_age_days`). 

## Parity Gate Results

The core defense against Train/Serve Skew is the CI Parity Gate (`tests/test_parity.py`). It runs on every deployment. It samples users, queries the Offline and Online stores at the same timestamp, and asserts they match.

| Entity ID | Feature | As-Of Timestamp | Offline Value | Online Value | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| CUST01014 | `txn_count_1h` | 2024-10-13T11:11:25 | 3 | 3 | ✅ PASS |
| CUST01014 | `sum_amount_24h` | 2024-10-13T11:11:25 | 80.03 | 80.03 | ✅ PASS |
| CUST00542 | `txn_count_1h` | 2024-12-17T02:05:42 | 0 | 0 | ✅ PASS |
| CUST01192 | `ip_risk_score` | 2024-08-14T09:36:44 | 0.5 | 0.5 | ✅ PASS |

If the pipeline detects a drift of even `1e-6` on a float, the build fails and the PR is blocked from merging.

## Limitations & Next Steps

- **Migration:** The Fraud model is fully migrated. A phased 5-month plan for the remaining 17 fintech models (Credit, Pricing) is documented in `MIGRATION_PLAN.md`.
- **Streaming:** The current v1 uses batch materialization (Parquet to Redis). A v2 architecture would transition to a Kappa architecture using Debezium (CDC), Kafka, and Flink for true sub-second streaming updates.
- **Infrastructure:** The prototype uses `fakeredis` for local portability. Production requires a highly available Redis cluster (e.g., AWS ElastiCache) with TTL policies enforcing freshness SLAs.

## How to Run

**1. Prerequisites**
- Python 3.11+ (Verified on 3.14.10)

**2. Setup**

    git clone https://github.com/Joystyxx/fintech-feature-store-v1.git
    cd fintech-feature-store-v1

    python -m venv .venv
    .venv\Scripts\activate     # Windows
    # source .venv/bin/activate  # macOS/Linux

    pip install -r requirements.txt

**3. Generate the Data**
Downloads the real Kaggle dataset and conforms it to our Parquet schema.

    python -m scripts.generate_data

**4. Run the Parity Gate (CI/CD Test)**
Proves that Offline and Online features match.

    python -m pytest tests/test_parity.py -s

**5. Launch the Dashboard**

    python -m streamlit run app.py

## Repository Structure

    .
    ├── features/
    │   ├── registry.py           # Immutable data contract (25 features)
    │   ├── offline.py            # DuckDB ASOF joins for training
    │   ├── online.py             # Redis read/write & materialization
    │   └── serve.py              # FastAPI null-safety contract
    ├── scripts/
    │   ├── generate_data.py      # Kaggle ingestion & schema conforming
    │   └── generate_report.py    # Automated parity report generation
    ├── tests/
    │   └── test_parity.py        # CI/CD gate comparing offline vs online
    ├── app.py                    # Streamlit interactive UI
    ├── DESIGN_DOC.md             # 5-page architecture specification
    ├── MIGRATION_PLAN.md         # Plan for migrating the remaining 17 models
    ├── RUNBOOK.md                # SOP for adding new features
    └── requirements.txt