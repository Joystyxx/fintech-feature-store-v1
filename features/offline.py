import duckdb
import pandas as pd
from features.registry import REGISTRY

def get_historical_features(
    entity_df: pd.DataFrame, 
    feature_names: list[str]
) -> pd.DataFrame:
    """Retrieves point-in-time correct features for training."""
    
    # Group features by their source Parquet file
    sources = {}
    for name in feature_names:
        if name not in REGISTRY:
            raise ValueError(f"Feature {name} not found in registry.")
        source_file = REGISTRY[name].source
        if source_file not in sources:
            sources[source_file] = []
        sources[source_file].append(name)

    # Start with the entity dataframe
    base_df = entity_df.copy()
    base_df['label_timestamp'] = pd.to_datetime(base_df['label_timestamp'])

    # Register the base entity dataframe with DuckDB
    duckdb.register('base_entity', base_df)

    # Current table we are building up
    current_table = 'base_entity'

    # For each Parquet file, perform a chained ASOF JOIN
    for i, (source_file, feats) in enumerate(sources.items()):
        select_cols = ", ".join(feats)
        table_name = f"feat_{i}"
        
        # The ASOF JOIN: base entity LEFT JOIN parquet source
        query = f"""
            CREATE OR REPLACE TEMP TABLE {table_name} AS
            SELECT 
                e.*, 
                u.{select_cols.replace(', ', f', u.')}
            FROM {current_table} e
            ASOF LEFT JOIN (
                SELECT * FROM read_parquet('{source_file}')
            ) u
              ON e.customer_id = u.customer_id
             AND e.label_timestamp >= u.event_timestamp
        """
        duckdb.sql(query)
        current_table = table_name

    # The final table only contains entity columns + requested features
    final_query = f"SELECT * FROM {current_table}"
    return duckdb.sql(final_query).df()