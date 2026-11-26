import pandas as pd
import numpy as np
import urllib.request
import zipfile
import io
from datetime import datetime, timedelta
from pathlib import Path

Path("data").mkdir(exist_ok=True)

print("Downloading dataset from Kaggle...")
url = "https://www.kaggle.com/api/v1/datasets/download/colabsss/financial-fraud-transaction-analytics"

try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        zip_data = io.BytesIO(response.read())
    
    print("Extracting CSV...")
    with zipfile.ZipFile(zip_data) as z:
        csv_filename = [f for f in z.namelist() if f.endswith('.csv')][0]
        with z.open(csv_filename) as f:
            df = pd.read_csv(f)
except Exception as e:
    print(f"Failed to download real data: {e}")
    raise e

print(f"Loaded {len(df)} rows.")

# --- SCHEMA MAPPING ---
df['event_timestamp'] = pd.to_datetime(df['transaction_datetime'])

# Velocity
velocity_df = df[['customer_id', 'event_timestamp']].copy()
velocity_df['txn_count_1h'] = df.get('transactions_last_1h', 0)
velocity_df['txn_count_24h'] = df.get('transactions_last_24h', 0)
velocity_df['txn_count_7d'] = df.get('transactions_last_7d', 0)
velocity_df['txn_count_5m'] = (df.get('transactions_last_1h', 0) / 12).round().astype(int)
velocity_df['distinct_devices_24h'] = 1
velocity_df['failed_txn_count_1h'] = df.get('failed_login_attempts', 0)
velocity_df['declined_ratio_24h'] = 0.0
velocity_df['distinct_countries_7d'] = 1
velocity_df.to_parquet("data/velocity.parquet", index=False)

# Amounts
amounts_df = df[['customer_id', 'event_timestamp']].copy()
amounts_df['sum_amount_24h'] = df.get('transaction_amount', 0.0)
amounts_df['avg_amount_7d'] = df.get('average_transaction_amount_30d', 0.0)
amounts_df['max_amount_30d'] = df.get('transaction_amount', 0.0)
amounts_df['amount_zscore_30d'] = 0.0
amounts_df['std_amount_7d'] = 0.0
amounts_df['avg_txn_amount_1h'] = df.get('transaction_amount', 0.0)
amounts_df.to_parquet("data/amounts.parquet", index=False)

# Profile
profile_df = df[['customer_id']].copy().drop_duplicates()
profile_df['event_timestamp'] = df['event_timestamp'].min()
profile_df['account_age_days'] = (df.get('account_age_months', 0) * 30).astype(int)
profile_df['kyc_tier'] = 1
profile_df['risk_segment'] = 'Low'
profile_df['country_risk_score'] = df.get('ip_risk_level', 'Low').map({'Low': 0.1, 'Medium': 0.5, 'High': 0.9}).fillna(0.1)
profile_df['credit_limit'] = df.get('account_balance', 0.0)
profile_df['is_pep'] = 0
profile_df.to_parquet("data/profile.parquet", index=False)

# Device
device_df = df[['customer_id', 'event_timestamp']].copy()
device_df['device_age_days'] = 1
device_df['shared_device_count'] = 1
device_df['counterparty_risk_avg'] = 0.1
device_df['device_change_count_7d'] = 0
device_df['ip_risk_score'] = df.get('ip_risk_level', 'Low').map({'Low': 0.1, 'Medium': 0.5, 'High': 0.9}).fillna(0.1)
device_df.to_parquet("data/device.parquet", index=False)

pd.DataFrame({"customer_id": [], "event_timestamp": [], "counterparty_risk_avg": []}).to_parquet("data/graph.parquet")
print("✅ Generated Parquet files in data/ from real Kaggle data.")