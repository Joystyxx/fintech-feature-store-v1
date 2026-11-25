from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class Feature:
    name: str
    entity: str
    dtype: Literal["int", "float", "str"]
    source: str
    freshness: str
    owner: str

# The Single Source of Truth for the Fraud Model's 25 Features
REGISTRY: dict[str, Feature] = {
    # --- Velocity Features (8) ---
    "txn_count_5m": Feature("txn_count_5m", "customer_id", "int", "data/velocity.parquet", "5m", "fraud-ml"),
    "txn_count_1h": Feature("txn_count_1h", "customer_id", "int", "data/velocity.parquet", "5m", "fraud-ml"),
    "txn_count_24h": Feature("txn_count_24h", "customer_id", "int", "data/velocity.parquet", "1h", "fraud-ml"),
    "distinct_devices_24h": Feature("distinct_devices_24h", "customer_id", "int", "data/velocity.parquet", "1h", "fraud-ml"),
    "failed_txn_count_1h": Feature("failed_txn_count_1h", "customer_id", "int", "data/velocity.parquet", "5m", "fraud-ml"),
    "txn_count_7d": Feature("txn_count_7d", "customer_id", "int", "data/velocity.parquet", "1d", "fraud-ml"),
    "declined_ratio_24h": Feature("declined_ratio_24h", "customer_id", "float", "data/velocity.parquet", "1h", "fraud-ml"),
    "distinct_countries_7d": Feature("distinct_countries_7d", "customer_id", "int", "data/velocity.parquet", "1d", "fraud-ml"),

    # --- Amount Aggregates (6) ---
    "sum_amount_24h": Feature("sum_amount_24h", "customer_id", "float", "data/amounts.parquet", "1h", "fraud-ml"),
    "avg_amount_7d": Feature("avg_amount_7d", "customer_id", "float", "data/amounts.parquet", "1d", "fraud-ml"),
    "max_amount_30d": Feature("max_amount_30d", "customer_id", "float", "data/amounts.parquet", "1d", "fraud-ml"),
    "amount_zscore_30d": Feature("amount_zscore_30d", "customer_id", "float", "data/amounts.parquet", "1d", "fraud-ml"),
    "std_amount_7d": Feature("std_amount_7d", "customer_id", "float", "data/amounts.parquet", "1d", "fraud-ml"),
    "avg_txn_amount_1h": Feature("avg_txn_amount_1h", "customer_id", "float", "data/amounts.parquet", "5m", "fraud-ml"),

    # --- Profile / KYC (6) ---
    "account_age_days": Feature("account_age_days", "customer_id", "int", "data/profile.parquet", "1d", "fraud-ml"),
    "kyc_tier": Feature("kyc_tier", "customer_id", "int", "data/profile.parquet", "1d", "fraud-ml"),
    "risk_segment": Feature("risk_segment", "customer_id", "str", "data/profile.parquet", "1d", "fraud-ml"),
    "country_risk_score": Feature("country_risk_score", "customer_id", "float", "data/profile.parquet", "1d", "fraud-ml"),
    "credit_limit": Feature("credit_limit", "customer_id", "float", "data/profile.parquet", "1d", "fraud-ml"),
    "is_pep": Feature("is_pep", "customer_id", "int", "data/profile.parquet", "1d", "fraud-ml"),

    # --- Device / Graph (5) ---
    "device_age_days": Feature("device_age_days", "customer_id", "int", "data/device.parquet", "1h", "fraud-ml"),
    "shared_device_count": Feature("shared_device_count", "customer_id", "int", "data/device.parquet", "1h", "fraud-ml"),
    "counterparty_risk_avg": Feature("counterparty_risk_avg", "customer_id", "float", "data/graph.parquet", "1d", "fraud-ml"),
    "device_change_count_7d": Feature("device_change_count_7d", "customer_id", "int", "data/device.parquet", "1d", "fraud-ml"),
    "ip_risk_score": Feature("ip_risk_score", "customer_id", "float", "data/device.parquet", "1h", "fraud-ml"),
}