import pandas as pd
import pytest
from features.offline import get_historical_features
from features.online import materialize, read_online

def test_offline_online_parity():
    """
    G3 (Verified Parity): Proves offline and online stores return the exact same values
    for the same entity at the same timestamp.
    """
    feature_names = ['txn_count_1h', 'sum_amount_24h']
    test_customer = 'CUST00989'
    
    # 1. Get the latest timestamp for this customer from the raw data
    df_raw = pd.read_parquet('data/velocity.parquet')
    customer_data = df_raw[df_raw['customer_id'] == test_customer]
    latest_ts = customer_data['event_timestamp'].max()
    
    # 2. Offline Store: Get features AS OF that exact timestamp
    entity_df = pd.DataFrame({
        'customer_id': [test_customer],
        'label_timestamp': [latest_ts]
    })
    offline_df = get_historical_features(entity_df, feature_names)
    offline_values = offline_df.iloc[0].to_dict()

    # 3. Online Store: Materialize and Read
    # (We materialize to ensure Redis has the absolute latest state)
    materialize(feature_names)
    online_values = read_online('customer_id', test_customer, feature_names)

    # 4. Assert Parity
    print(f"\n--- Parity Test for {test_customer} at {latest_ts} ---")
    for f in feature_names:
        off_val = offline_values[f]
        on_val = online_values[f]
        
        print(f"Feature: {f:<15} | Offline: {off_val:<10} | Online: {on_val:<10}")
        
        # Use pytest.approx for floats to handle tiny float precision differences, exact match for ints
        if isinstance(off_val, float):
            assert off_val == pytest.approx(on_val, abs=1e-6), f"Mismatch on {f}"
        else:
            assert off_val == on_val, f"Mismatch on {f}"
            
    print("✅ Parity Passed: Offline and Online values match exactly.")