import os
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split


def run_ml_pipeline():
    print("Initializing Data Engineering & Machine Learning Pipeline...")
    
    # Paths configuration
    ledger_path = os.path.join("data", "structured", "processed_inventory_ledger.csv")
    if not os.path.exists(ledger_path):
        print("[ERROR] processed_inventory_ledger.csv not found! Run process_walmart_inventory.py first.")
        return
        
    # 1. Load the Engineered Ledger
    df = pd.read_csv(ledger_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # Select Top 5 SKUs (Departments) for high-velocity isolation
    top_5_skus = df['sku'].unique()[:5]
    print(f"Targeting Top 5 Operational SKUs: {list(top_5_skus)}")
    
    historical_sales_list = []
    future_forecasts_list = []
    inventory_anomalies_list = []
    
    for sku in top_5_skus:
        sku_data = df[df['sku'] == sku].sort_values('date').copy()
        
        # Feature Engineering for Time-Series Regression
        sku_data['day_of_year'] = sku_data['date'].dt.dayofyear
        sku_data['month'] = sku_data['date'].dt.month
        sku_data['year'] = sku_data['date'].dt.year
        sku_data['lag_1_week'] = sku_data['weekly_sales_units'].shift(1)
        sku_data['lag_2_weeks'] = sku_data['weekly_sales_units'].shift(2)
        
        # Fill NaN values created by lag shifts
        sku_data = sku_data.bfill()
        
        # Split features and targets
        features = ['day_of_year', 'month', 'year', 'lag_1_week', 'lag_2_weeks', 'temperature_f', 'fuel_price_usd', 'cpi']
        X = sku_data[features]
        y = sku_data['weekly_sales_units']
        
        # 2. Train XGBoost Forecast Model
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, shuffle=False)
        model = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
        model.fit(X_train, y_train)
        
        # Generate Historical Mapping Table
        sku_data['predicted_sales'] = model.predict(X)
        historical_sales_list.append(sku_data[['date', 'store_id', 'sku', 'weekly_sales_units', 'starting_stock', 'ending_stock', 'status']])
        
        # 3. Anomaly Detection Logic (Thresholds: Drop < 20% or Spike > 200% of baseline average)
        historical_mean = sku_data['weekly_sales_units'].mean()
        sku_data['anomaly_flag'] = np.where(
            (sku_data['weekly_sales_units'] < (historical_mean * 0.20)) | 
            (sku_data['weekly_sales_units'] > (historical_mean * 2.00)), 
            True, False
        )
        
        # Map out isolated anomalies for database ingestion
        anomalies = sku_data[sku_data['anomaly_flag'] == True].copy()
        anomalies['deviation_percentage'] = ((anomalies['weekly_sales_units'] - historical_mean) / historical_mean) * 100
        inventory_anomalies_list.append(anomalies[['date', 'store_id', 'sku', 'weekly_sales_units', 'status', 'deviation_percentage']])
        
        # 4. Generate Rolling 30-Day Future Demand Forecast
        last_row = sku_data.iloc[-1]
        future_dates = pd.date_range(start=last_row['date'] + pd.Timedelta(days=7), periods=4, freq='W') # 4 weeks = ~30 days
        
        future_records = []
        current_lag1 = last_row['weekly_sales_units']
        current_lag2 = last_row['lag_1_week']
        
        for f_date in future_dates:
            # Create placeholder inputs for future external factors using last known trends
            f_features = pd.DataFrame([{
                'day_of_year': f_date.dayofyear,
                'month': f_date.month,
                'year': f_date.year,
                'lag_1_week': current_lag1,
                'lag_2_weeks': current_lag2,
                'temperature_f': last_row['temperature_f'],
                'fuel_price_usd': last_row['fuel_price_usd'],
                'cpi': last_row['cpi']
            }])
            
            pred_demand = max(0, int(model.predict(f_features[features])[0]))
            
            future_records.append({
                'date': f_date.strftime('%Y-%m-%d'),
                'store_id': last_row['store_id'],
                'sku': sku,
                'forecasted_demand_units': pred_demand
            })
            
            # Slide lags forward for rolling prediction loop
            current_lag2 = current_lag1
            current_lag1 = pred_demand
            
        future_forecasts_list.append(pd.DataFrame(future_records))
        
    # 5. Compile and Export local CSV Database Staging Tables
    out_dir = os.path.join("data", "structured")
    
    historical_sales_table = pd.concat(historical_sales_list)
    future_forecasts_table = pd.concat(future_forecasts_list)
    inventory_anomalies_table = pd.concat(inventory_anomalies_list)
    
    historical_sales_table.to_csv(os.path.join(out_dir, "db_historical_sales.csv"), index=False)
    future_forecasts_table.to_csv(os.path.join(out_dir, "db_future_forecasts.csv"), index=False)
    inventory_anomalies_table.to_csv(os.path.join(out_dir, "db_inventory_anomalies.csv"), index=False)
    
    print("\n[SUCCESS] Traditional ML Engine execution complete!")
    print(f"Staged {len(historical_sales_table)} historical rows -> db_historical_sales.csv")
    print(f"Staged {len(future_forecasts_table)} rolling forecast rows -> db_future_forecasts.csv")
    print(f"Isolated {len(inventory_anomalies_table)} operational anomalies -> db_inventory_anomalies.csv")

if __name__ == "__main__":
    run_ml_pipeline()
