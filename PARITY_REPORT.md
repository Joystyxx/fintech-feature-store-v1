# Parity-Test Report: Offline vs Online Store
**Generated At:** 2026-11-25 12:26:28
**Objective:** Verify that Point-in-Time offline retrieval matches low-latency online serving.

| Entity ID | Feature | As-Of Timestamp | Offline Value | Online Value | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| CUST01014 | `txn_count_1h` | 2024-10-13T11:11:25 | 3 | 3 | ✅ PASS |
| CUST01014 | `txn_count_24h` | 2024-10-13T11:11:25 | 13 | 13 | ✅ PASS |
| CUST01014 | `sum_amount_24h` | 2024-10-13T11:11:25 | 80.03 | 80.03 | ✅ PASS |
| CUST01014 | `avg_amount_7d` | 2024-10-13T11:11:25 | 38.93 | 38.93 | ✅ PASS |
| CUST01014 | `ip_risk_score` | 2024-10-13T11:11:25 | 0.1 | 0.1 | ✅ PASS |
| CUST00542 | `txn_count_1h` | 2024-12-17T02:05:42 | 0 | 0 | ✅ PASS |
| CUST00542 | `txn_count_24h` | 2024-12-17T02:05:42 | 4 | 4 | ✅ PASS |
| CUST00542 | `sum_amount_24h` | 2024-12-17T02:05:42 | 191.13 | 191.13 | ✅ PASS |
| CUST00542 | `avg_amount_7d` | 2024-12-17T02:05:42 | 15.17 | 15.17 | ✅ PASS |
| CUST00542 | `ip_risk_score` | 2024-12-17T02:05:42 | 0.1 | 0.1 | ✅ PASS |
| CUST01192 | `txn_count_1h` | 2024-08-14T09:36:44 | 1 | 1 | ✅ PASS |
| CUST01192 | `txn_count_24h` | 2024-08-14T09:36:44 | 9 | 9 | ✅ PASS |
| CUST01192 | `sum_amount_24h` | 2024-08-14T09:36:44 | 21.25 | 21.25 | ✅ PASS |
| CUST01192 | `avg_amount_7d` | 2024-08-14T09:36:44 | 55.53 | 55.53 | ✅ PASS |
| CUST01192 | `ip_risk_score` | 2024-08-14T09:36:44 | 0.5 | 0.5 | ✅ PASS |

## Summary
All sampled features across Velocity, Amount, and Device families passed the parity check with exact matches (or within ±1e-6 for floats). No train/serve skew detected.