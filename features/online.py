import fakeredis
import duckdb
from features.registry import REGISTRY

# Initialize our in-memory Redis (simulates a real Redis cluster)
r = fakeredis.FakeRedis(decode_responses=True)

def materialize(feature_names: list[str]) -> None:
    """
    Pulls the LATEST row per entity from Parquet and writes it to Redis.
    """
    # Group features by source file
    sources = {}
    for name in feature_names:
        source_file = REGISTRY[name].source
        sources.setdefault(source_file, []).append(name)

    for source_file, feats in sources.items():
        select_cols = ", ".join(feats)
        
        # Get the absolute latest row for every customer
        query = f"""
            SELECT customer_id, {select_cols}
            FROM read_parquet('{source_file}')
            QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY event_timestamp DESC) = 1
        """
        df = duckdb.sql(query).df()
        
        # Write to Redis
        for _, row in df.iterrows():
            entity_id = row['customer_id']
            values = {f: row[f] for f in feats}
            write_online("customer_id", entity_id, values)

def write_online(entity_type: str, entity_id: str, values: dict) -> None:
    """Writes feature values to the Redis hash."""
    # Convert numpy types to native Python types for fakeredis
    clean_values = {k: v.item() if hasattr(v, 'item') else v for k, v in values.items()}
    r.hset(f"{entity_type}:{entity_id}", mapping=clean_values)

def read_online(entity_type: str, entity_id: str, feature_names: list[str]) -> dict:
    """Reads feature values from Redis and casts them using the Registry."""
    raw = r.hmget(f"{entity_type}:{entity_id}", feature_names)
    result = {}
    for f, v in zip(feature_names, raw):
        if v is None:
            result[f] = None
        else:
            # Parse based on registry contract
            dtype = REGISTRY[f].dtype
            if dtype == "int":
                result[f] = int(v)
            elif dtype == "float":
                result[f] = float(v)
            else:
                result[f] = v
    return result