import os
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

def upload_data_to_aws():
    print("Initiating direct data pipeline migration to AWS RDS Cloud...")
    
    # 1. AWS RDS Connection Setup Configuration
    DB_USER = "postgres_user"
    DB_PASSWORD = "RiddhiSiddhi246!" 
    DB_HOST = "inventory-db-instance.czmwusiwewpk.us-east-2.rds.amazonaws.com" 
    DB_PORT = "5432"
    DB_NAME = "inventory_platform"
    
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    # 2. Map Local CSV Files to Staged Arrays
    data_dir = os.path.join("data", "structured")
    ledger_file_path = os.path.join(data_dir, "processed_inventory_ledger.csv")
    
    tables_to_upload = {
        "historical_sales": os.path.join(data_dir, "db_historical_sales.csv"),
        "future_forecasts": os.path.join(data_dir, "db_future_forecasts.csv"),
        "inventory_anomalies": os.path.join(data_dir, "db_inventory_anomalies.csv"),
        "processed_inventory_ledger": ledger_file_path
    }
    
    # 3. Stream Rows up to AWS Database
    for table_name, file_path in tables_to_upload.items():
        if not os.path.exists(file_path):
            print(f"[ERROR] Staging file missing: {file_path}. Run forecasting pipeline first.")
            return
            
        print(f"Reading {file_path} into memory...")
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.lower().str.strip()
        
        if table_name in ["inventory_anomalies", "processed_inventory_ledger"]:
            print(f"Executing standardized regional mapping for table: '{table_name}'...")
            
            def resolve_hash_matrix_region(row_data):
                st_id = str(row_data.get("store_id", "STORE-1")).strip().upper()
                sku_id = str(row_data.get("sku", "DEPT-3")).strip().upper()
                composite_key = st_id + sku_id
                char_sum = sum(ord(char) for char in composite_key)
                
                if char_sum % 3 == 0: return "WH-EAST (Atlanta, GA)"
                elif char_sum % 3 == 1: return "WH-SOUTH (Houston, TX)"
                else: return "WH-WEST (Phoenix, AZ)"
            
            df['region'] = df.apply(resolve_hash_matrix_region, axis=1)
            
            if table_name == "inventory_anomalies":
                def calculate_explicit_shortage(row):
                    dev = float(row.get("deviation_percentage", 0.25))
                    decimal_percentage = dev / 100.0 if dev > 5.0 else dev
                    return int(decimal_percentage * 6000)
                
                df['shortage_units'] = df.apply(calculate_explicit_shortage, axis=1)
                df = df[["date", "store_id", "sku", "region", "status", "deviation_percentage", "shortage_units"]]
                
            elif table_name == "processed_inventory_ledger":
                base_cols = [col for col in df.columns if col != 'region']
                df = df[["region"] + base_cols]
                
        print(f"Uploading {len(df)} rows to AWS RDS table: '{table_name}'...")
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"[SUCCESS] Table '{table_name}' is now live in the cloud.\n")
        
    # ====================================================================
    # COMPLIANT OPERATIONAL COUPLING SCHEMA INITIALIZATION
    # ====================================================================
    print("Generating clean, decoupled operational tables for real-time tracking...")
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT)
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS live_store_inventory CASCADE;")
        cursor.execute("""
            CREATE TABLE live_store_inventory (
                live_id SERIAL PRIMARY KEY,
                store_id VARCHAR(50) NOT NULL,
                sku VARCHAR(50) NOT NULL,
                region VARCHAR(100) NOT NULL,
                status VARCHAR(50) NOT NULL,
                shortage_units INT NOT NULL,
                deviation_percentage DECIMAL(10,2) NOT NULL
            );
        """)
        cursor.execute("""
            INSERT INTO live_store_inventory (store_id, sku, region, status, shortage_units, deviation_percentage)
            SELECT store_id, sku, region, status, shortage_units, deviation_percentage FROM inventory_anomalies;
        """)
        
        print("Rebuilding decoupled operational tables for multi-row transaction tracking...")
        cursor.execute("DROP TABLE IF EXISTS live_store_balances CASCADE;")
        cursor.execute("""
            CREATE TABLE live_store_balances (
                balance_transaction_id SERIAL PRIMARY KEY, -- Auto-incrementing unique key allows endless rows
                store_id VARCHAR(50) NOT NULL,
                sku VARCHAR(50) NOT NULL,
                region VARCHAR(100) NOT NULL,
                current_on_hand INT NOT NULL,
                last_shipment_id VARCHAR(100) NOT NULL
            );
        """)
        cursor.execute("""
            INSERT INTO live_store_balances (store_id, sku, region, current_on_hand, last_shipment_id)
            SELECT store_id, sku, region, 5000, 'SYS-INITIAL-SEED' FROM inventory_anomalies GROUP BY store_id, sku, region;
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("[SUCCESS] Decoupled current-state operational datastore successfully generated!")
    except Exception as e_seed:
        print(f"[ERROR] Live schema initialization failure: {str(e_seed)}")

if __name__ == "__main__":
    upload_data_to_aws()