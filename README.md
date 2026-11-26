\# Fintech Feature Store v1



A production-grade prototype of a Dual-Store Feature Store architecture, built to eliminate Train/Serve Skew for a fintech fraud model.



\*\*Live Demo:\*\* (https://fintech-feature-store-v1.streamlit.app/)

\*\*Architecture Design Doc:\*\* See `DESIGN\_DOC.md`

\*\*Migration Plan:\*\* See `MIGRATION\_PLAN.md`



\## The Problem

The fintech's data team was copy-pasting feature SQL across offline training notebooks and the online scoring service. This resulted in two production incidents this quarter caused by \*\*Train/Serve Skew\*\*—the model learned a data distribution in training that it never saw in production.



\## The Solution

We implemented a lightweight Feature Store that acts as the single source of truth. Instead of two pipelines (one for training, one for serving), we enforce a \*\*Dual-Store\*\* pattern with a hard CI parity gate.



\*   \*\*Feature Registry (`features/registry.py`):\*\* An immutable data contract. If a feature isn't defined here, it cannot be trained or served.

\*   \*\*Offline Store (DuckDB + Parquet):\*\* Historical data is queried using `ASOF JOIN` to guarantee Point-in-Time correctness. This prevents temporal data leakage during model training.

\*   \*\*Online Store (Redis):\*\* A batch materialization job writes the latest feature state to Redis for sub-10ms real-time serving.

\*   \*\*Parity Gate (`tests/test\_parity.py`):\*\* A Pytest suite that compares the Offline and Online values for the same entity at the same timestamp. If they drift by even `1e-6`, the CI pipeline blocks the deployment.

\*   \*\*Serving Layer (Streamlit):\*\* An interactive dashboard that demonstrates the pipeline in action, including a heuristic rules engine for risk scoring.



\## Stack \& Tooling

\*   \*\*Offline Store:\*\* DuckDB, Parquet, Pandas

\*   \*\*Online Store:\*\* Redis (`fakeredis` for local testing)

\*   \*\*Serving Layer:\*\* Streamlit

\*   \*\*Testing:\*\* Pytest



\## Local Setup



1\.  \*\*Clone the repo and navigate into it:\*\*

&#x20;   ```bash

&#x20;   git clone https://github.com/Joystyxx/fintech-feature-store-v1.git

&#x20;   cd fintech-feature-store-v1



2\. Create a virtual environment:

python -m venv .venv

\# Windows: .venv\\Scripts\\activate

\# Mac/Linux: source .venv/bin/activate



3\. Install dependencies:

pip install -r requirements.txt



4\. Generate the real Kaggle data:

python -m scripts.generate\_data



5\. Run the Parity Gate (CI/CD Test):

python -m pytest tests/test\_parity.py -s



6\. Launch the Dashboard:

python -m streamlit run app.py



Next Steps (v2)

Migration: Phased migration of the remaining 17 models over 5 months (See MIGRATION\_PLAN.md).



Streaming: Transition from batch Parquet to a Kappa architecture using Debezium (CDC), Kafka, and Flink for true real-time feature computation.



Infrastructure: Replace fakeredis with a production-grade Redis cluster (AWS ElastiCache / Upstash).



