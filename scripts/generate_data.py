import pandas as pd
import kagglehub
import os
from pathlib import Path

# 1. Download dataset via kagglehub
print("Downloading dataset...")
path = kagglehub.dataset_download("colabsss/financial-fraud-transaction-analytics")
csv_path = os.path.join(path, "financial_fraud_transaction_dataset.csv") 
# Note: If the filename is different, inspect the downloaded folder path printed above.

# 2. Load and prepare
df = pd.read_csv(csv_path)
print(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")

# Ensure data directory exists
Path("data").mkdir(exist_ok=True)

# 3. Schema Mapping & Conforming
# We map the real Kaggle columns to our registry's expected schema.
# The registry expects: customer_id, event_timestamp, and the feature names.

# Parse the timestamp
df['event_timestamp'] = pd.to_datetime(df['transaction_datetime'])

# --- Velocity Features ---
velocity_df = df[['customer_id', 'event_timestamp']].copy()
# Map real columns to our registry names
velocity_df['txn_count_1h'] = df.get('transactions_last_1h', 0)
velocity_df['txn_count_24h'] = df.get('transactions_last_24h', 0)
velocity_df['txn_count_7d'] = df.get('transactions_last_7d', 0)
# Derive approximations for missing features
velocity_df['txn_count_5m'] = (df.get('transactions_last_1h', 0) / 12).round().astype(int) # Approximation
velocity_df['distinct_devices_24h'] = 1 # Placeholder (dataset may not have this granularity)
velocity_df['failed_txn_count_1h'] = df.get('failed_login_attempts', 0) # Proxy
velocity_df['declined_ratio_24h'] = 0.0 # Placeholder
velocity_df['distinct_countries_7d'] = 1 # Placeholder

velocity_df.to_parquet("data/velocity.parquet", index=False)

# --- Amount Features ---
amounts_df = df[['customer_id', 'event_timestamp']].copy()
amounts_df['sum_amount_24h'] = df.get('transaction_amount', 0.0) # Simplified for snapshot
amounts_df['avg_amount_7d'] = df.get('average_transaction_amount_30d', 0.0)
amounts_df['max_amount_30d'] = df.get('transaction_amount', 0.0) # Simplified
amounts_df['amount_zscore_30d'] = 0.0 # Requires historical distribution
amounts_df['std_amount_7d'] = 0.0 # Placeholder
amounts_df['avg_txn_amount_1h'] = df.get('transaction_amount', 0.0)

amounts_df.to_parquet("data/amounts.parquet", index=False)

# --- Profile Features (Static / Per-customer) ---
profile_df = df[['customer_id']].copy().drop_duplicates()
profile_df['event_timestamp'] = df['event_timestamp'].min() # Static snapshot time
profile_df['account_age_days'] = (df.get('account_age_months', 0) * 30).astype(int)
profile_df['kyc_tier'] = 1 # Placeholder
profile_df['risk_segment'] = 'Low' # Placeholder
profile_df['country_risk_score'] = df.get('ip_risk_level', 'Low').map({'Low': 0.1, 'Medium': 0.5, 'High': 0.9}).fillna(0.1)
profile_df['credit_limit'] = df.get('account_balance', 0.0) # Proxy
profile_df['is_pep'] = 0 # Placeholder

profile_df.to_parquet("data/profile.parquet", index=False)

# --- Device / Graph Features ---
device_df = df[['customer_id', 'event_timestamp']].copy()
device_df['device_age_days'] = 1 # Placeholder
device_df['shared_device_count'] = 1 # Placeholder
device_df['counterparty_risk_avg'] = 0.1 # Placeholder
device_df['device_change_count_7d'] = 0 # Placeholder
device_df['ip_risk_score'] = df.get('ip_risk_level', 'Low').map({'Low': 0.1, 'Medium': 0.5, 'High': 0.9}).fillna(0.1)

device_df.to_parquet("data/device.parquet", index=False)

# Create an empty graph file as required by the registry
pd.DataFrame({"customer_id": [], "event_timestamp": [], "counterparty_risk_avg": []}).to_parquet("data/graph.parquet")

print("✅ Generated Parquet files in data/ from real Kaggle data.")