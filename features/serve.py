from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Union
from features.online import read_online, materialize
from features.registry import REGISTRY

app = FastAPI(title="Feature Store API", version="1.0")

# --- ADD THIS STARTUP EVENT ---
@app.on_event("startup")
def startup_event():
    print("🚀 Server starting: Materializing features to Redis...")
    # Materialize the features we need for this demo
    materialize(['txn_count_1h', 'sum_amount_24h'])
    print("✅ Materialization complete.")

class FeatureResponse(BaseModel):
    entity_id: str
    features: Dict[str, Optional[Union[float, int, str]]]
    missing: List[str]

@app.get("/features", response_model=FeatureResponse)
def get_features(
    entity_id: str = Query(..., description="Customer ID"),
    features: str = Query(..., description="Comma-separated list of features")
):
    feature_list = [f.strip() for f in features.split(",")]
    
    for f in feature_list:
        if f not in REGISTRY:
            raise HTTPException(status_code=400, detail=f"Feature '{f}' not found in registry.")
            
    values = read_online("customer_id", entity_id, feature_list)
    
    missing = [f for f, v in values.items() if v is None]
    present_values = {f: v for f, v in values.items() if v is not None}
    
    return FeatureResponse(
        entity_id=entity_id,
        features=present_values,
        missing=missing
    )