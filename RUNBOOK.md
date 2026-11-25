\# Feature Store Runbook: Adding a New Feature



This runbook outlines the standard operating procedure (SOP) for adding a new feature to the production feature store. Following these steps guarantees Point-in-Time correctness and zero Train/Serve Skew.



\## Phase 1: Definition (The Contract)

\*\*Goal:\*\* Define the feature as code without writing any SQL yet.



1\. Open `features/registry.py`.

2\. Add a new `Feature` object to the `REGISTRY` dictionary.

3\. Specify the `source` Parquet path, `dtype`, and `freshness` SLA.

4\. \*\*PR Check:\*\* Open a Pull Request. The CI pipeline will verify the registry compiles.



\## Phase 2: Offline Implementation (The Historian)

\*\*Goal:\*\* Ensure the feature can be calculated historically without data leakage.



1\. Write the transformation logic in your batch ETL tool (or DuckDB) to generate the new column in the source Parquet file.

2\. Add the new feature name to the `test\_offline\_online\_parity` test suite in `tests/test\_parity.py`.

3\. Run the offline test locally to verify the `ASOF JOIN` retrieves the correct historical values.

4\. \*\*PR Check:\*\* CI will run the offline tests to ensure no schema breaking changes occur.



\## Phase 3: Online Implementation (The Speed Demon)

\*\*Goal:\*\* Materialize the feature to Redis for low-latency serving.



1\. Update the `materialize` function call in your scheduler (or `serve.py` for local testing) to include the new feature name.

2\. Run the materialization job locally: `python -m scripts.generate\_report` (or your dedicated Airflow DAG).

3\. Verify the feature exists in Redis by querying the API:

&#x20;  `curl "http://127.0.0.1:8000/features?entity\_id=TEST\_USER\&features=new\_feature\_name"`



\## Phase 4: The Parity Gate (The Safety Net)

\*\*Goal:\*\* Prove that the offline and online stores match.



1\. Run the full test suite: `python -m pytest tests/`

2\. The Parity Gate will compare the Offline DuckDB result against the Online Redis result for a sample user.

3\. If the test fails (❌ FAIL), check:

&#x20;  - Did you use the exact same window function in both stores?

&#x20;  - Did the materialization job actually run?

4\. \*\*Merge:\*\* Once the Parity Gate is green, merge the PR. The feature is now live.



\## Phase 5: Monitoring (Post-Deployment)

1\. Monitor the `missing\[]` array in the serving API logs. 

2\. If the new feature appears in `missing\[]` more than 1% of the time, alert the data engineering team (indicates the materialization job is lagging).

