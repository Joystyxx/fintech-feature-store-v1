\# Migration Plan: Integrating the Remaining 17 Models



\## Executive Summary

We have successfully migrated the Fraud Model (Model 1) to the feature store. This document outlines the phased migration for the remaining 17 models (Credit Underwriting, Pricing, and secondary Fraud models). 



We will not do a "big bang" migration. We will migrate in phases based on \*\*Blast Radius\*\* (business risk if the model fails). Legacy SQL pipelines will remain warm for 30 days post-migration to allow for instant atomic rollback.



\## Effort Estimation Key

\*   \*\*EW (Engineer-Week):\*\* The effort required by one Senior Data Engineer for one week (approx. 40 hours).

\*   \*\*DS (Data Scientist):\*\* The effort required by the model owner to validate parity and retrain.



\## Migration Phases



\### Phase 1: Shadow Mode (The Fraud Model) — \*Complete\*

\*   \*\*Models:\*\* 1 (Fraud)

\*   \*\*Status:\*\* Done. Running in production.

\*   \*\*Effort:\*\* 2 EW.

\*   \*\*Note:\*\* Serves as the reference implementation for the rest.



\### Phase 2: Low-Risk Batch Models (4 Models)

\*   \*\*Models:\*\* Batch-only credit limits, non-real-time batch risk scores.

\*   \*\*Risk Level:\*\* Low (No sub-second latency requirement).

\*   \*\*Strategy:\*\* Direct cutover with 1-week parallel run.

\*   \*\*Estimated Effort:\*\* 4 EW (1 EW per model).

\*   \*\*Key Challenge:\*\* Legacy SQL may have hardcoded date ranges that need to be refactored into our registry's `freshness` SLA.



\### Phase 3: Shared Feature Groups (8 Models)

\*   \*\*Models:\*\* Underwriting models (Income verification, KYC, Bureau scores).

\*   \*\*Risk Level:\*\* Medium.

\*   \*\*Strategy:\*\* Feature consolidation. Many of these models use the exact same features but defined them differently. We will define them once in the Registry, which will result in a \*\*30% reduction in total feature count\*\*.

\*   \*\*Estimated Effort:\*\* 12 EW (1.5 EW per model).

\*   \*\*Key Challenge:\*\* Requires data scientists to agree on a single definition of complex metrics (e.g., "What exactly is a 'bad' debt-to-income ratio?").



\### Phase 4: High-Traffic Real-Time Models (5 Models)

\*   \*\*Models:\*\* Dynamic Pricing, Checkout Fraud, Instant Credit limits.

\*   \*\*Risk Level:\*\* High (Sub-15ms latency required, directly impacts revenue).

\*   \*\*Strategy:\*\* Canary deployment. We will route 1% of live traffic to the new feature store, monitor the `missing\[]` array and latency in Grafana, then ramp to 10%, 50%, and 100% over 2 weeks.

\*   \*\*Estimated Effort:\*\* 20 EW (4 EW per model).

\*   \*\*Key Challenge:\*\* Extensive load testing required. We must provision a highly available Redis cluster to handle the QPS.



\## Total Effort Estimate

\*   \*\*Total Remaining Models:\*\* 17

\*   \*\*Total Engineering Time:\*\* \~36 EW (Engineer-Weeks)

\*   \*\*Total Data Science Validation Time:\*\* \~17 EW

\*   \*\*Calendar Timeline:\*\* Assuming a team of 2 Data Engineers and 2 Data Scientists, this migration will take \*\*4 to 5 months\*\*.



\## Rollback Strategy

1\. \*\*Dual Routing:\*\* The serving API will have a feature flag (`USE\_FEATURE\_STORE=true/false`). 

2\. \*\*Fallback:\*\* If the API returns a `503` or a parity mismatch is detected in production, the flag is toggled off, and the model instantly falls back to the legacy copy-pasted SQL.

3\. \*\*Data Retention:\*\* Legacy SQL jobs will continue to write to their old tables for 30 days after cutover, ensuring zero data loss.

