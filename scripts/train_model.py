import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
import joblib
import os

print("Loading data for training...")
df_vel = pd.read_parquet('data/velocity.parquet')
df_amt = pd.read_parquet('data/amounts.parquet')
df_dev = pd.read_parquet('data/device.parquet')

df = pd.merge(df_vel, df_amt[['customer_id', 'event_timestamp', 'sum_amount_24h', 'avg_amount_7d']], 
              on=['customer_id', 'event_timestamp'], how='inner')
df = pd.merge(df, df_dev[['customer_id', 'event_timestamp', 'ip_risk_score']], 
              on=['customer_id', 'event_timestamp'], how='inner')

# We will use sum_amount_24h as a proxy for the "incoming amount" for training
features = ['txn_count_1h', 'sum_amount_24h', 'avg_amount_7d', 'ip_risk_score']

# Create a target that actually includes the amount this time
df['is_fraud'] = (
    (df['txn_count_1h'] > 4) | 
    (df['ip_risk_score'] > 0.7) | 
    (df['sum_amount_24h'] > 1000)
).astype(int)

X = df[features]
y = df['is_fraud']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"Training XGBoost on {len(X_train)} rows...")

model = xgb.XGBClassifier(
    n_estimators=50,
    max_depth=3,
    learning_rate=0.1,
    objective='binary:logistic',
    random_state=42
)
model.fit(X_train, y_train)

preds = model.predict(X_test)
probs = model.predict_proba(X_test)[:, 1]
print(f"✅ Model Accuracy: {accuracy_score(y_test, preds):.2f}")
print(f"✅ Model ROC-AUC: {roc_auc_score(y_test, probs):.2f}")

os.makedirs('models', exist_ok=True)
joblib.dump(model, 'models/fraud_model.pkl')
print("✅ Model saved to models/fraud_model.pkl")