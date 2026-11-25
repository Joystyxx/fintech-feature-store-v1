import streamlit as st
import pandas as pd
import time
from features.offline import get_historical_features
from features.online import materialize, read_online

# --- PAGE CONFIG ---
st.set_page_config(page_title="Fintech Risk Engine", page_icon="💳", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    /* Title styling */
    .main-title { font-size: 32px !important; font-weight: 700; margin-bottom: 0px; }
    .sub-title { font-size: 16px; opacity: 0.7; margin-bottom: 20px; }
    
    /* Custom Metric Cards */
    .metric-card {
        background-color: rgba(128, 128, 128, 0.1);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        text-align: center;
    }
    .metric-value { font-size: 28px; font-weight: 700; }
    .metric-label { font-size: 14px; opacity: 0.7; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        font-weight: 600;
        border-radius: 8px;
        height: 48px;
        border: none;
        transition: all 0.2s;
    }
    .stButton>button:hover { 
        background-color: #1D4ED8 !important; 
    }
    </style>
""", unsafe_allow_html=True)

# --- DATA INITIALIZATION ---
@st.cache_resource
def init_redis():
    features = ['txn_count_1h', 'sum_amount_24h', 'avg_amount_7d', 'ip_risk_score']
    materialize(features)
    return True

init_redis()

@st.cache_data
def load_customer_ids():
    df = pd.read_parquet('data/velocity.parquet')
    return sorted(df['customer_id'].unique())

customer_ids = load_customer_ids()

# --- HEADER ---
st.markdown('<p class="main-title">Fintech Fraud Risk Engine</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Real-time inference powered by the Dual-Store Feature Store Architecture.</p>', unsafe_allow_html=True)
st.divider()

# --- SIDEBAR ---
with st.sidebar:
    st.header("Transaction Input")
    selected_customer = st.selectbox("Select Customer ID", customer_ids)
    transaction_amount = st.number_input("Incoming Amount ($)", min_value=1.0, value=250.0, step=10.0)
    
    st.markdown("---")
    run_btn = st.button("Run Live Inference")

# --- MAIN DASHBOARD ---
if run_btn:
    with st.spinner("Executing Temporal Joins and Cache Lookups..."):
        time.sleep(1)
        
        features_to_fetch = ['txn_count_1h', 'sum_amount_24h', 'avg_amount_7d', 'ip_risk_score']
        
        # 1. Fetch Online
        online_features = read_online("customer_id", selected_customer, features_to_fetch)
        
        # 2. Fetch Offline
        df_raw = pd.read_parquet('data/velocity.parquet')
        user_data = df_raw[df_raw['customer_id'] == selected_customer]
        latest_ts = user_data['event_timestamp'].max()
        
        entity_df = pd.DataFrame({'customer_id': [selected_customer], 'label_timestamp': [latest_ts]})
        offline_df = get_historical_features(entity_df, features_to_fetch)
        offline_features = offline_df.iloc[0].to_dict()

        # 3. PARITY GATE
        parity_passed = True
        for f in features_to_fetch:
            off = offline_features.get(f)
            on = online_features.get(f)
            if isinstance(off, float):
                if abs(off - on) > 1e-6: parity_passed = False
            elif off != on:
                parity_passed = False

        # --- UI RENDER ---
        st.markdown("### Feature Store Lookup")
        c1, c2 = st.columns(2)
        
        with c1:
            st.info("⚡ **Online Store (Redis)**")
            st.json(online_features)
        with c2:
            st.warning("📦 **Offline Store (DuckDB)**")
            clean_off = {k: round(v, 2) if isinstance(v, float) else v for k, v in offline_features.items() if k not in ['customer_id', 'label_timestamp']}
            st.json(clean_off)

        if parity_passed:
            st.success(f"✅ **Parity Verified.** Offline and Online values match exactly for `{selected_customer}`.")
        else:
            st.error("❌ **Parity Failed.** Train/Serve Skew detected! Pipeline halted.")

        st.divider()

        # --- MODEL INFERENCE (Heuristic Rules Engine) ---
        st.markdown("### Model Inference")
        
        # Business Rules
        risk_score = 0
        triggers = []
        
        # Rule 1: High Velocity
        if online_features.get('txn_count_1h', 0) > 3: 
            risk_score += 30
            triggers.append("High 1H Velocity")
            
        # Rule 2: Incoming Amount vs Historical Average
        avg_amt = online_features.get('avg_amount_7d', 100)
        if transaction_amount > avg_amt * 3:
            risk_score += 40
            triggers.append("Amount > 3x 7-day Avg")
            
        # Rule 3: High IP Risk
        if online_features.get('ip_risk_score', 0) > 0.5: 
            risk_score += 30
            triggers.append("High IP Risk Score")

        # Metric Cards
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Incoming Amount</div><div class="metric-value">${transaction_amount:,.2f}</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">7d Avg Amount</div><div class="metric-value">${avg_amt:,.2f}</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Fraud Risk Score</div><div class="metric-value">{risk_score}/100</div></div>', unsafe_allow_html=True)

        st.write("") 

        # Final Decision
        if risk_score >= 50:
            st.error(f"🚨 **TRANSACTION BLOCKED** — High probability of fraud ({risk_score}% Risk).")
            st.caption(f"Triggered Rules: {', '.join(triggers)}")
        else:
            st.success(f"✅ **TRANSACTION APPROVED** — Low probability of fraud ({risk_score}% Risk).")

else:
    st.info("👈 Select a Customer ID in the sidebar and click **Run Live Inference** to begin.")