import os
import pandas as pd
import numpy as np

def generate_inventory_ledger():
    print("Beginning professional data structuring pipeline...")
    
    structured_dir = os.path.join("data", "structured")
    train_path = os.path.join(structured_dir, "train.csv")
    features_path = os.path.join(structured_dir, "features.csv")
    
    # 1. Verification Check
    if not os.path.exists(train_path) or not os.path.exists(features_path):
        print("[ERROR] Please ensure 'train.csv' and 'features.csv' from the Walmart Kaggle dataset are in data/structured/")
        return

    # 2. Load Core Data Arrays
    sales_df = pd.read_csv(train_path)
    features_df = pd.read_csv(features_path)
    
    # Filter down to a manageable operational footprint for testing (Store 1, Top Depts)
    sales_df = sales_df[(sales_df['Store'] == 1) & (sales_df['Dept'].isin([1, 2, 3]))].copy()
    sales_df['Date'] = pd.to_datetime(sales_df['Date'])
    features_df['Date'] = pd.to_datetime(features_df['Date'])
    
    # Merge environmental data (Temperature, Fuel Price, CPI)
    merged_df = pd.merge(sales_df, features_df, on=['Store', 'Date'], how='left')
    merged_df = merged_df.sort_values(by=['Dept', 'Date']).reset_index(drop=True)
    
    print(f"Merged sales records with regional features. Core shape: {merged_df.shape}")
    
    # 3. Simulate Daily Inventory Balances (Engineering safety stock and on-hand supply)
    engineered_records = []
    
    for dept, group in merged_df.groupby('Dept'):
        # Establish initial capacity limits for the store department shelves
        current_inventory = 25000 
        reorder_point = 8000
        target_max_stock = 30000
        
        for idx, row in group.iterrows():
            weekly_sales = int(row['Weekly_Sales']) if row['Weekly_Sales'] > 0 else 0
            
            # Inventory calculation logic: Current On-Hand minus weekly consumer demand
            starting_inventory = current_inventory
            ending_inventory = max(0, starting_inventory - weekly_sales)
            
            # Rule Engine: Determine status indicators for the Retail Manager dashboard
            status = "OPTIMAL"
            if ending_inventory == 0:
                status = "STOCKOUT"
            elif ending_inventory < reorder_point:
                status = "REORDER_TRIGGERED"
            elif ending_inventory > (target_max_stock * 0.85):
                status = "OVERSTOCKED"
                
            # Simulate typical inbound supply shipment logic
            replenishment_received = 0
            if ending_inventory < reorder_point:
                replenishment_received = target_max_stock - ending_inventory
                current_inventory = target_max_stock
            else:
                current_inventory = ending_inventory
                
            # Append context-rich rows matching the platform's core retail objectives
            engineered_records.append({
                'date': row['Date'].strftime('%Y-%m-%d'),
                'store_id': f"STORE-{row['Store']}",
                'sku': f"DEPT-{row['Dept']}",
                'weekly_sales_units': weekly_sales,
                'starting_stock': starting_inventory,
                'ending_stock': ending_inventory,
                'status': status,
                'replenishment_order_units': replenishment_received,
                'temperature_f': row['Temperature'],
                'fuel_price_usd': row['Fuel_Price'],
                'cpi': row['CPI']
            })
            
    # 4. Save Final Refactored Dataset
    output_df = pd.DataFrame(engineered_records)
    output_path = os.path.join(structured_dir, "processed_inventory_ledger.csv")
    output_df.to_csv(output_path, index=False)
    
    print(f"\n[SUCCESS] Enterprise Data Engine Generated Successfully!")
    print(f"File Location: {output_path}")
    print("\nSample Generated Records for Retail Dashboard Matrix:")
    print(output_df[['date', 'sku', 'ending_stock', 'status', 'weekly_sales_units']].head(7))

if __name__ == "__main__":
    generate_inventory_ledger()
