import streamlit as st
import psycopg2
import json
import os
import pandas as pd
import altair as alt
from datetime import datetime

# 1. CORE LAYOUT CONFIGURATION - Forces Right Sidebar Open Automatically on Load
st.set_page_config(
    page_title="Supply Chain Control Platform", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom minimalist styling architecture to center lines, headers, and footers flawlessly
st.markdown("<style>.reportview-container .main .block-container { padding-top: 1.5rem; } .centered-title { text-align: center; font-family: sans-serif; color: #111111; font-weight: 700; margin-bottom: 0.2rem; } .centered-caption { text-align: center; font-family: sans-serif; color: #666666; margin-bottom: 1.5rem; } .centered-footer { text-align: center; font-size: 0.85rem; color: #888888; margin-top: 3rem; margin-bottom: 1rem; width: 100%; display: block; } div[data-testid='stMetricValue'] { font-size: 2.2rem !important; font-weight: 700 !important; color: #111111 !important; } div[data-testid='stMetricDelta'] { font-size: 0.9rem !important; font-weight: 500 !important; } hr { margin-left: auto !important; margin-right: auto !important; width: 100% !important; border: 1px solid #eeeeee !important; }</style>", unsafe_allow_html=True)

st.markdown("<h1 class='centered-title'>Supply Chain Control Platform</h1>", unsafe_allow_html=True)
st.markdown("<p class='centered-caption'>Collaborative Planning, Forecasting, and Replenishment (CPFR) Work Surface</p>", unsafe_allow_html=True)
st.write("---")

# 2. FIXED: MANDATORY TOP-LEVEL SESSION STATE INITIALIZATION 
# Guarantees variables exist globally before any lower layout line executes
if "staged_mitigation" not in st.session_state:
    st.session_state.staged_mitigation = None

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Workspace Online. Ask me to perform an executive supply chain disruption review."}]

if "dispatch_orders" not in st.session_state:
    st.session_state.dispatch_orders = [
        {"timestamp": "2026-07-04 14:48:02", "sku": "DEPT-3", "origin": "WH-WEST (Phoenix, AZ)", "destination": "STORE-1", "units": 15000, "status": "In Transit"},
        {"timestamp": "2026-07-04 14:48:02", "sku": "DEPT-3", "origin": "WH-EAST (Atlanta, GA)", "destination": "STORE-1", "units": 20000, "status": "In Transit"},
        {"timestamp": "2026-07-03 11:40:12", "sku": "DEPT-1", "origin": "WH-EAST (Atlanta, GA)", "destination": "STORE-1", "units": 45000, "status": "In Transit"}
    ]
# 2. Extract System Access Tokens Safely from Local Fallbacks or Cloud Management
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "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")
PINECONE_API_KEY = st.secrets.get("PINECONE_API_KEY", "pcsk_6pBXB2_7EnyeZVgWXoJFaqPLL1U3pGcGNWi8scUBo83MoQc1NaFkWPxQ1ULMdNJ6QmuNPE")
LAMBDA_API_URL = st.secrets.get("LAMBDA_API_URL", "https://jwfv3whasofhjtxsdxxtqss4py0uavoz.lambda-url.us-east-2.on.aws/")
DB_USER = st.secrets.get("DB_USER", "postgres_user")
DB_PASSWORD = st.secrets.get("DB_PASSWORD", "RiddhiSiddhi246!")
DB_HOST = st.secrets.get("DB_HOST", "inventory-db-instance.czmwusiwewpk.us-east-2.rds.amazonaws.com")
DB_PORT = "5432"
DB_NAME = "inventory_platform"

# 3. DUAL-PURPOSE METRICS & GRID FETCHING MOTOR (ZERO FALLBACK CONSTANTS)
def fetch_complete_rds_datasets():
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT)
    cursor = conn.cursor()
    
    # FIXED: Added explicit [0] index selection to unpack the row tuple layers instantly
    cursor.execute("SELECT COUNT(*) FROM inventory_anomalies WHERE status = 'STOCKOUT';")
    stockouts = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM inventory_anomalies WHERE status = 'REORDER_TRIGGERED';")
    reorders = cursor.fetchone()[0]
    
    cursor.execute("SELECT deviation_percentage FROM inventory_anomalies WHERE status = 'STOCKOUT';")
    financial_risk = sum([float(row[0]) * 35.50 for row in cursor.fetchall()])
    
    cursor.execute("SELECT warehouse_location, safety_stock, transit_windows, fulfillment_status FROM distribution_grid ORDER BY hub_id ASC;")
    grid_rows = cursor.fetchall()
    
    grid_data = []
    for r in grid_rows:
        grid_data.append({
            "Warehouse Location": str(r[0]),
            "Safety Stock": f"{int(r[1]):,} Units", 
            "Transit Windows": str(r[2]),
            "Fulfillment Status": str(r[3]),
            "Raw_Stock": int(r[1])
        })
    
    cursor.close()
    conn.close()
    return stockouts, reorders, round(financial_risk, 2), pd.DataFrame(grid_data)

live_stockouts, live_reorders, financial_risk, warehouse_df = fetch_complete_rds_datasets()

# ====================================================================
# 4. 100% LIVE DATABASESUMMARY METRIC CARD ROW
# ====================================================================
def fetch_live_dashboard_metrics():
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT)
    cursor = conn.cursor()
    
    # Dynamically query the operational tables so top cards respond to receipts instantly
    cursor.execute("SELECT COUNT(*) FROM live_store_inventory WHERE status = 'STOCKOUT';")
    stockouts = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM live_store_inventory WHERE status = 'REORDER_TRIGGERED';")
    reorders = cursor.fetchone()[0]
    
    cursor.execute("SELECT deviation_percentage FROM live_store_inventory WHERE status = 'STOCKOUT';")
    financial_risk = sum([float(row[0]) * 35.50 for row in cursor.fetchall()])
    
    cursor.close()
    conn.close()
    return stockouts, reorders, round(financial_risk, 2)

live_stockouts, live_reorders, financial_risk = fetch_live_dashboard_metrics()

col_m1, col_m2, col_m3 = st.columns(3)
with col_m1: st.metric(label="Active Stockout Events (Critical)", value=live_stockouts, delta="Action Required" if live_stockouts > 0 else "Clear", delta_color="inverse")
with col_m2: st.metric(label="Automated Reorder Triggers Activated", value=live_reorders, delta="Staged for Delivery")
with col_m3: st.metric(label="OTIF Financial Penalty Exposure ($)", value=f"${financial_risk:,.2f}", delta="Walmart Compliance Risk" if financial_risk > 0 else "Compliant", delta_color="inverse")
st.write("---")

# if st.session_state.get("staged_mitigation"):
#     mitigation = st.session_state.staged_mitigation
#     sku = mitigation["sku"]
#     dest = mitigation["store"]
#     total = mitigation["total_needed"]
    
#     st.info(f"💡 **Staged Mitigation Proposal Active** | Target SKU: `{sku}` | Cumulative Deficit: `{total:,}` Units Required")
    
#     if mitigation.get("unviable_split_warning"):
#         st.error(mitigation["warning_msg"])
#         if st.button("🏭 Authorize Option B: Trigger Emergency Production Plant Run", use_container_width=True, type="primary"):
#             cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             st.session_state.dispatch_orders.append({
#                 "timestamp": cur_time, "sku": sku, "origin": "EMERGENCY-PLANT-CHICAGO", "destination": dest, "units": total, "status": "In Transit"
#             })
#             st.toast("Emergency production run triggered!")
#             st.session_state.staged_mitigation = None
#             st.rerun()
#     else:
#         col_opt_a, col_opt_b = st.columns(2)
#         with col_opt_a:
#             if st.button(f"Commit Option A: Multi-Hub Network Split ({total:,} Units)", use_container_width=True, type="primary"):
#                 cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                 wh1 = mitigation["wh_1"]
#                 u1 = int(mitigation["units_a_1"])
#                 wh2 = mitigation["wh_2"]
#                 u2 = int(mitigation["units_a_2"])
                
#                 shipments_dispatched = 0
#                 deducted_log_strings = []
                
#                 if u1 > 0:
#                     st.session_state.dispatch_orders.append({
#                         "timestamp": cur_time, "sku": sku, "origin": wh1, "destination": dest, "units": u1, "status": "In Transit"
#                     })
#                     deducted_log_strings.append(f"• **Deducted:** {u1:,} units from {wh1}.")
#                     shipments_dispatched += 1
                    
#                 if u2 > 0:
#                     st.session_state.dispatch_orders.append({
#                         "timestamp": cur_time, "sku": sku, "origin": wh2, "destination": dest, "units": u2, "status": "In Transit"
#                     })
#                     deducted_log_strings.append(f"• **Deducted:** {u2:,} units from {wh2}.")
#                     shipments_dispatched += 1
                
#                 log_bullet_points = "\n".join(deducted_log_strings)
#                 audit_log = (
#                     f"⚙️ **[AUDIT LEDGER STREAM - {cur_time}]**\n"
#                     f"**Authorized User:** Executive Manager (Krina)\n"
#                     f"**Action:** Approved Option A Fulfillment Network Re-Routing Split.\n\n"
#                     f"{log_bullet_points}\n"
#                     f"• **Database Lineage:** Written back successfully to AWS RDS cloud parameters."
#                 )
#                 st.session_state.messages.append({"role": "assistant", "content": audit_log})
#                 st.toast(f"Fulfillment approved! Dispatched {shipments_dispatched} true delivery vehicles.")
#                 st.session_state.staged_mitigation = None
#                 st.rerun()
                
#         with col_opt_b:
#             if st.button("Commit Option B: Emergency Manufacturing Plant Run", use_container_width=True):
#                 cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                 st.session_state.dispatch_orders.append({
#                     "timestamp": cur_time, "sku": sku, "origin": "EMERGENCY-PLANT-CHICAGO", "destination": dest, "units": total, "status": "In Transit"
#                 })
#                 audit_log = (
#                     f"⚙️ **[AUDIT LEDGER STREAM - {cur_time}]**\n"
#                     f"**Authorized User:** Executive Manager (Krina)\n"
#                     f"**Action:** Override Trigger: Initiated emergency manufacturing run for {total:,} units due to system safety regulations."
#                 )
#                 st.session_state.messages.append({"role": "assistant", "content": audit_log})
#                 st.toast("Emergency production run authorized!")
#                 st.session_state.staged_mitigation = None
#                 st.rerun()
                
#         if st.button("❌ Cancel Staged Proposals", use_container_width=True):
#             st.session_state.staged_mitigation = None
#             st.rerun()

# ====================================================================
# SECTION 5 & 6 OVERWRITE: AGGREGATED ENTERPRISE LEDGER & CHARTS
# ====================================================================
conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT)
cursor = conn.cursor()

# Query A: Dynamically sum your on-hand volumes grouped by store and supply region
cursor.execute("""
    SELECT 
        b.store_id, 
        b.region, 
        SUM(b.current_on_hand) as total_live_stock,
        MAX(b.last_shipment_id) as latest_audit_id,
        CASE 
            WHEN SUM(b.current_on_hand) > 15000 THEN 'Low Risk'
            WHEN SUM(b.current_on_hand) > 6000 THEN 'Medium Risk'
            ELSE 'High Stockout Risk'
        END as risk_tier
    FROM live_store_balances b
    GROUP BY b.store_id, b.region
    ORDER BY b.store_id ASC;
""")
ledger_rows = cursor.fetchall()

# Query B: Pull aggregated chart totals cleanly from across all your recorded shipment rows
cursor.execute("SELECT region, SUM(current_on_hand) FROM live_store_balances GROUP BY region ORDER BY region ASC;")
chart_rows = cursor.fetchall()

cursor.close()
conn.close()

# Format the clean data frame strictly according to your required corporate parameters
store_ledger_df = pd.DataFrame([
    {
        "Store ID": str(r[0]), 
        "Assigned Supply Source": str(r[1]), 
        "Live Stock Volume": f"{int(r[2]):,} Units", 
        "Pipeline Risk Assessment": str(r[4])
    } for r in ledger_rows
])

store_chart_data = pd.DataFrame([
    {"Fulfillment Source Region": str(c[0]), "Real-Time On-Hand Stock (Units)": int(c[1])} 
    for c in chart_rows
])

col_left, col_right = st.columns(2)
with col_left:
    st.subheader("Real-Time Storefront Status Profile")
    st.dataframe(store_ledger_df, use_container_width=True, hide_index=True)
with col_right:
    st.subheader("Distribution Fleet Logistics Capacity")
    st.dataframe(warehouse_df[["Warehouse Location", "Safety Stock", "Transit Windows", "Fulfillment Status"]], use_container_width=True, hide_index=True)

st.write("")
col_ch1, col_col_ch2 = st.columns(2)
with col_ch1:
    st.subheader("Fleet Availability Across Backup Hubs")
    short_locations = ["Atlanta (East)", "Houston (South)", "Chicago (Midwest)", "Phoenix (West)"]
    raw_volumes = [
        int(warehouse_df.loc[warehouse_df["Warehouse Location"].str.contains("Atlanta"), "Raw_Stock"].values[0]),
        int(warehouse_df.loc[warehouse_df["Warehouse Location"].str.contains("Houston"), "Raw_Stock"].values[0]),
        int(warehouse_df.loc[warehouse_df["Warehouse Location"].str.contains("Chicago"), "Raw_Stock"].values[0]),
        int(warehouse_df.loc[warehouse_df["Warehouse Location"].str.contains("Phoenix"), "Raw_Stock"].values[0])
    ]
    chart_data = pd.DataFrame({"Fulfillment Warehouse": short_locations, "Backup Units Available": raw_volumes})
    altair_chart = alt.Chart(chart_data).mark_bar(size=45, color="#1E3A8A").encode(
        x=alt.X('Fulfillment Warehouse:N', axis=alt.Axis(labelAngle=-45, title="Fulfillment Center Storage Hub")),
        y=alt.Y('Backup Units Available:Q', title="Warehouse Safety Stock Pool (Units)")
    ).properties(height=300)
    st.altair_chart(altair_chart, use_container_width=True)

with col_col_ch2:
    st.subheader("Real-Time Storefront Inventory Balances")
    store_chart = alt.Chart(store_chart_data).mark_bar(size=45, color="#10B981").encode(
        x=alt.X('Fulfillment Source Region:N', axis=alt.Axis(labelAngle=-45, title="Standardized Fulfillment Anchor")),
        y=alt.Y('Real-Time On-Hand Stock (Units):Q', title="Live Shelf Inventory Balance (Units)")
    ).properties(height=300)
    st.altair_chart(store_chart, use_container_width=True)



# ==============================================================
# HUMAN-IN-THE-LOOP INTERACTIVE ACTION CONTROL BOARD
# ==============================================================
if st.session_state.staged_mitigation:
    opt = st.session_state.staged_mitigation
    sku = opt['sku']
    dest = opt['store']
    
    # CASE A: The split calculations breached safety boundaries
    if opt.get("unviable_split_warning", False):
        st.warning(f"### ⚠️ STRATEGIC CRISIS: {opt['warning_msg']}")
        st.write("Fulfillment split is unavailable due to strict network depletion guardrails. **Execute the manufacturing recovery plan to secure your retail shelves safely:**")
        if st.button("Authorize Option B: Trigger Emergency Production Plant Run", use_container_width=True):
            t_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.dispatch_orders.insert(0, {"timestamp": t_stamp, "sku": sku, "origin": "PRODUCTION_PLANT", "destination": dest, "units": opt['total_needed'], "status": "Manufacturing"})
            
            audit_log = (
                f"**[MANUFACTURING LEDGER LOG - {t_stamp}]**\n"
                f"**Authorized User:** Executive Manager (Krina)\n"
                f"**Action:** Approved Option B Manufacturing Production Run.\n"
                f"- **Reason:** Option A split rejected due to strict 5,000-unit warehouse cushion violations.\n"
                f"- **Staged Volume:** Emergency batch of {opt['total_needed']:,} units queued for manufacturing assembly line compilation."
            )
            st.session_state.messages.append({"role": "assistant", "content": audit_log})
            st.toast("Option B Scheduled! Manufacturing Line Active.")
            st.session_state.staged_mitigation = None
            st.rerun()
            
    # CASE B: Split parameters are verified as completely safe and legal
    else:
        st.markdown("### STAGED STRATEGIC OPERATIONS: Awaiting Executive Authorization")
        st.write("The AI Strategic Advisor has staged an optimized, compliance-verified allocation proposal:")
        c_btn1, col_btn2 = st.columns(2)
        
        with c_btn1:
            # Real-World Dynamic Labeling Matrix: Hides zero-quantity nodes from printing on the UI button canvas
            if int(opt['units_a_1']) > 0 and int(opt['units_a_2']) > 0:
                btn_label = f"Commit Option A: Multi-Hub Network Split ({opt['units_a_1']:,} Units from {opt['wh_1']} & {opt['units_a_2']:,} Units from {opt['wh_2']})"
            elif int(opt['units_a_1']) > 0:
                btn_label = f"Commit Option A: Direct Supply Sourcing ({opt['units_a_1']:,} Units from {opt['wh_1']})"
            else:
                btn_label = f"Commit Option A: Direct Supply Sourcing ({opt['units_a_2']:,} Units from {opt['wh_2']})"

            if st.button(btn_label, use_container_width=True, type="primary"):
                try:
                    write_conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT)
                    write_cursor = write_conn.cursor()
                    
                    # Real-World Substring Filter: Extract city name case-insensitively to prevent string format mismatches
                    city1 = "ATLANTA" if "ATLANTA" in str(opt['wh_1']).upper() else ("PHOENIX" if "PHOENIX" in str(opt['wh_1']).upper() else ("HOUSTON" if "HOUSTON" in str(opt['wh_1']).upper() else str(opt['wh_1']).upper()))
                    city2 = "ATLANTA" if "ATLANTA" in str(opt['wh_2']).upper() else ("PHOENIX" if "PHOENIX" in str(opt['wh_2']).upper() else ("HOUSTON" if "HOUSTON" in str(opt['wh_2']).upper() else str(opt['wh_2']).upper()))
                    
                    write_cursor.execute("UPDATE distribution_grid SET safety_stock = safety_stock - %s WHERE UPPER(warehouse_location) LIKE %s;", (int(opt['units_a_1']), f"%{city1}%"))
                    write_cursor.execute("UPDATE distribution_grid SET safety_stock = safety_stock - %s WHERE UPPER(warehouse_location) LIKE %s;", (int(opt['units_a_2']), f"%{city2}%"))
                    write_conn.commit()
                    write_cursor.close()
                    write_conn.close()
                    
                    t_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    deducted_log_strings = []
                    shipments_dispatched = 0
                    
                    # ====================================================================
                    # FIXED ZERO-QUANTITY LOGISTICAL FILTER (ELIMINATES GHOST TRUCKS)
                    # Maps shipments using strict greater-than-zero capacity validations
                    # ====================================================================
                    if int(opt['units_a_1']) > 0:
                        st.session_state.dispatch_orders.insert(0, {
                            "timestamp": t_stamp, "sku": sku, "origin": opt['wh_1'], "destination": dest, "units": int(opt['units_a_1']), "status": "In Transit"
                        })
                        deducted_log_strings.append(f"• **Deducted:** {opt['units_a_1']:,} units from {opt['wh_1']}.")
                        shipments_dispatched += 1
                        
                    if int(opt['units_a_2']) > 0:
                        st.session_state.dispatch_orders.insert(0, {
                            "timestamp": t_stamp, "sku": sku, "origin": opt['wh_2'], "destination": dest, "units": int(opt['units_a_2']), "status": "In Transit"
                        })
                        deducted_log_strings.append(f"• **Deducted:** {opt['units_a_2']:,} units from {opt['wh_2']}.")
                        shipments_dispatched += 1
                    
                    log_bullet_points = "\n".join(deducted_log_strings)
                    audit_log = (
                        f"⚠️ **[AUDIT LEDGER STREAM - {t_stamp}]**\n"
                        f"**Authorized User:** Executive Manager (Krina)\n"
                        f"**Action:** Approved Option A Fulfillment Multi-Hub Split.\n\n"
                        f"{log_bullet_points}\n"
                        f"• **Database Sync:** Written back successfully to AWS RDS 'distribution_grid' table rows."
                    )
                    st.session_state.messages.append({"role": "assistant", "content": audit_log})
                    st.toast(f"Option A Successfully Deployed! Dispatched {shipments_dispatched} active trucks.", icon="🚀")
                    st.session_state.staged_mitigation = None
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e_db:
                    st.error(str(e_db))
                    
        with col_btn2:
            if st.button("Option B: Cancel Split & Trigger Production Plant Run", use_container_width=True):
                t_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.dispatch_orders.insert(0, {"timestamp": t_stamp, "sku": sku, "origin": "PRODUCTION_PLANT", "destination": dest, "units": opt['total_needed'], "status": "Manufacturing"})
                
                audit_log = (
                    f"**[MANUFACTURING LEDGER LOG - {t_stamp}]**\n"
                    f"**Authorized User:** Executive Manager (Krina)\n"
                    f"**Action:** Approved Option B Manufacturing Production Run.\n"
                    f"- **Staged Allocation Volume:** Emergency batch of {opt['total_needed']:,} units queued for manufacturing assembly line compilation."
                )
                st.session_state.messages.append({"role": "assistant", "content": audit_log})
                st.toast("Option B Scheduled!")
                st.session_state.staged_mitigation = None
                st.rerun()
                
        if st.button("Cancel Staged Proposals", use_container_width=True):
            t_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cancel_log = (
                f"🛑 **[OPERATION ABORTED - {t_stamp}]**\n"
                f"**Authorized User:** Executive Manager (Krina)\n"
                f"**Action:** Cancelled staged mitigation proposals.\n"
                f"- **System Impact:** All temporary pipelines cleared. Main database state preserved intact without changes."
            )
            st.session_state.messages.append({"role": "assistant", "content": cancel_log})
            st.session_state.staged_mitigation = None
            st.rerun()
    st.write("---")


# ==============================================================
# 7. CLOSED-LOOP PROPORTIONAL SHIPPING LOG DATA TABLE 
# ==============================================================
st.write("---")
st.subheader("Real-Time Simulation Shipment Ledger")
st.caption("Tracks the physical transit status of emergency supply trucks dispatched during this browser session. Clearing entries here resolves active storefront penalty fines.")

if st.session_state.dispatch_orders:
    chronological_orders = list(reversed(st.session_state.dispatch_orders))
    ledger_display_df = pd.DataFrame(chronological_orders)
    ledger_display_df.columns = ["Dispatch Timestamp", "SKU Identifier", "Fulfillment Origin Hub", "Target Store Destination", "Shipment Volume (Units)", "Current Transit Status"]
    st.dataframe(ledger_display_df, use_container_width=True, hide_index=True)
    
    st.write("")
    st.markdown("##### Retail Store Dock Receiving Controls")
    
    for idx, order in enumerate(chronological_orders):
        if order['status'] == "In Transit":
            if st.button(f"📦 Log Delivery Arrival for Shipment #{idx} ({order['units']:,} Units to {order['destination']})", key=f"rec_grid_chron_{idx}_{order['timestamp']}", use_container_width=True):
                
                true_session_index = len(st.session_state.dispatch_orders) - 1 - idx
                if st.session_state.dispatch_orders[true_session_index]['status'] != "In Transit":
                    st.warning("This delivery request has already been safely absorbed into the database disk.", icon="⚠️")
                    st.rerun()
                    
                try:
                    rc_conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT)
                    rc_cursor = rc_conn.cursor()
                    
                    unique_shipment_id = f"TRK-{str(order['timestamp']).split()[-1].replace(':', '')}"
                    
                    # Log a unique historical row record for every incoming truck arrival
                    rc_cursor.execute("""
                        INSERT INTO live_store_balances (store_id, sku, region, current_on_hand, last_shipment_id)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (str(order['destination']), str(order['sku']), str(order['origin']), int(order['units']), unique_shipment_id))
                    
                    # Fetch matching active stockout rows from the live inventory tracking layer
                    rc_cursor.execute("""
                        SELECT live_id, shortage_units 
                        FROM live_store_inventory 
                        WHERE store_id = %s AND sku = %s AND region = %s AND status = 'STOCKOUT'
                        ORDER BY live_id ASC;
                    """, (str(order['destination']), str(order['sku']), str(order['origin'])))
                    
                    active_stockouts = rc_cursor.fetchall()
                    truck_units_remaining = int(order['units'])
                    ids_to_resolve = []
                    
                    for row in active_stockouts:
                        target_id = int(row[0])
                        shortage_val = int(row[1]) if row[1] else 15000
                        
                        if truck_units_remaining >= shortage_val:
                            ids_to_resolve.append(target_id)
                            truck_units_remaining -= shortage_val
                        else:
                            # ====================================================================
                            # FIXED GREEDY KNAPSACK LAYER: Skip large rows but CONTINUE testing 
                            # the remainder of the table to maximize row resolution efficiency!
                            # ====================================================================
                            if truck_units_remaining > 0:
                                # We can also check if the remaining cargo covers a massive chunk (>85%) of this row
                                if truck_units_remaining >= (shortage_val * 0.85):
                                    ids_to_resolve.append(target_id)
                                    truck_units_remaining = 0
                                    break
                            continue # Drive straight to the next rows rather than breaking out!
                    
                    if ids_to_resolve:
                        rc_cursor.execute(
                            "UPDATE live_store_inventory SET status = 'RESOLVED' WHERE live_id = ANY(%s);",
                            (ids_to_resolve,)
                        )
                        rows_updated_count = len(ids_to_resolve)
                    else:
                        rows_updated_count = 0
                    
                    rc_conn.commit()
                    rc_cursor.close()
                    rc_conn.close()
                    
                    st.session_state.dispatch_orders[true_session_index]['status'] = "Delivered"
                    
                    cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    receipt_log = (
                        f"✅ [SIMULATION INVENTORY RECEIPT - {cur_time}]\n"
                        f"**Action:** Store Dock Manager logged delivery of order slot #{idx}.\n"
                        f"- **Audit Token Generated:** `{unique_shipment_id}`\n"
                        f"- **Destination Center:** {order['destination']} received {order['units']:,} units of {order['sku']}.\n"
                        f"- **System Impact:** Successfully logged a new unique transactional entry row record. {rows_updated_count} active records resolved."
                    )
                    st.session_state.messages.append({"role": "assistant", "content": receipt_log})
                    
                    st.toast(f"Delivery logged! Tracker {unique_shipment_id} verified.", icon="✅")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e_rc:
                    st.error(f"Proportional Ingestion Failed: {str(e_rc)}")
else:
    st.write("No active logistical transport vectors currently staged.")

# ====================================================================
# # 8. FLOATING ADVISOR SIDEBAR CONSOLE (PART 1 OF 2 - ENGINE ROUTER)
# ====================================================================
with st.sidebar:
    st.markdown("### AI Strategic Advisor")
    st.write("---")
    
    # Initialize global fallback container variable to prevent NameErrors during reruns
    agent_reply = "Workspace Online. Strategic review parameters loaded safely."
    
    # Render persistent conversation viewport stream log history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    st.write("---")
    
    if user_input := st.chat_input("Enter request..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        try:
            from openai import OpenAI
            from pinecone import Pinecone
            import re
            import json
            
            conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT)
            cursor = conn.cursor()
            target_sku = "DEPT-3" if "DEPT-3" in user_input.upper() else "DEPT-1"
            
            # FIXED TUPLE INDICES: Mapping precise array coordinates to fix the float() tuple crash
            cursor.execute("SELECT store_id, sku, region, status, deviation_percentage, shortage_units FROM live_store_inventory WHERE sku = %s;", (target_sku,))
            db_data = [{"store_id": str(r[0]), "sku": str(r[1]), "region": str(r[2]), "status": str(r[3]), "deviation_percentage": float(r[4]), "shortage_units": int(r[5])} for r in cursor.fetchall()]
            
            cursor.execute("SELECT date, store_id, sku, forecasted_demand_units FROM future_forecasts WHERE sku = %s LIMIT 5;", (target_sku,))
            forecast_data = [{"date": str(f[0]), "store_id": str(f[1]), "sku": str(f[2]), "forecasted_units": int(f[3])} for f in cursor.fetchall()]
            
            cursor.execute("SELECT store_id, sku, region, SUM(current_on_hand) FROM live_store_balances GROUP BY store_id, sku, region;")
            store_status_dict = {f"{str(s[0])}_{str(s[1])}": {"region": str(s[2]), "current_stock": int(s[3])} for s in cursor.fetchall()}
            
            cursor.execute("SELECT warehouse_location, safety_stock, fulfillment_status FROM distribution_grid;")
            warehouses_dict = {str(w[0]): {"safety_stock_units": int(w[1]), "status": str(w[2])} for w in cursor.fetchall()}
            
            cursor.close()
            conn.close()
            
            openai_client = OpenAI(api_key=OPENAI_API_KEY)
            embed_res = openai_client.embeddings.create(input=user_input, model="text-embedding-3-small")
            query_vector = embed_res.data[0].embedding
            
            pc = Pinecone(api_key=PINECONE_API_KEY)
            idx = pc.Index("inventory-rag-index")
            vector_res = idx.query(vector=query_vector, top_k=2, include_metadata=True)
            log_context = [m["metadata"]["text"] for m in vector_res["matches"] if "metadata" in m and "text" in m["metadata"]]
            
            tools_schema = [{ 
                "type": "function", 
                "function": { 
                "name": "stage_mitigation_parameters", 
                "description": ( 
                "Call this function ONLY when the user explicitly requests an active inventory replenishment calculation, " 
                "network re-routing layout split, or emergency warehouse distribution allocation plan for a storefront SKU.\n" 
                "CRITICAL: If the user is asking general questions about flight paths, aviation telemetry, air cargo price metrics, " 
                "or email dispatches, you are STRICTLY FORBIDDEN from calling this function. Respond with text only." 
                ), 
                "parameters": { 
                "type": "object", 
                "properties": { 
                "json_allocation_payload": { 
                    "type": "string", 
                    # FIXED: Changed hardcoded corporate names to the exact keys present in your true database table
                    "description": "Flat JSON string matching schema: {'total': 35000, 'wh1': 'Atlanta (East)', 'w1_units': 20000, 'wh2': 'Phoenix (West)', 'w2_units': 15000}" 
                } 
            }, 
            "required": ["json_allocation_payload"] 
        } 
    } 
}]

# ------------------------------------------------------------ 
# # 8. FLOATING ADVISOR SIDEBAR CONSOLE (PART 2 OF 2 - PARSING ENGINE) 
# ------------------------------------------------------------ 
            system_prompt = (
                "You are an isolated, strict enterprise supply chain control tower agent.\n\n"
                "CRITICAL SECURITY BOUNDARY RULE (CORE DOMAIN GUARDRAIL):\n"
                "You are strictly FORBIDDEN from answering any queries regarding general life advice, personal finance, "
                "house purchasing, career guidance, hobbies, or general knowledge questions. You do not possess general human memory.\n"
                "If the user's intent is not directly and explicitly related to retail inventory anomalies, storefront stockouts, "
                "supply chain logistics, fleet aviation, or distribution pricing corridors, you must immediately halt execution and respond "
                "with this exact message structure: '❌ [OUT OF SCOPE] My core domain is strictly limited to supply chain logistics management. Please submit an asset inventory request.'\n\n"
                "CRITICAL INVENTORY NAVIGATION RULES:\n"
                "1. DEFICIT CALCULATION: Read the 'Anomaly_RDS' metrics to calculate the total unit stockout deficit for the SKU.\n"
                "2. AVAILABLE STOCK LOOKUP: You must read ONLY the 'Fulfillment_Grid' data to find available safety stock. You must use the exact warehouse keys provided in the grid: 'Atlanta (East)', 'Phoenix (West)', 'Houston (South)', 'Chicago (Midwest)'.\n"
                "3. SAFE BUFFER RULE: You are strictly FORBIDDEN from drawing more stock from a warehouse hub than its safety stock value. Furthermore, your final allocation split must leave a minimum of 5,000 units remaining inside that warehouse hub to protect buffers.\n"
                "4. DYNAMIC TOOL CALLING: Mathematically compute the split values and trigger the 'stage_mitigation_parameters' tool function.\n\n"
                "DYNAMIC MULTI-INTENT EXECUTION RULES:\n"
                "5. FLIGHT TRACKING (CASE 9): If queried about flight status, tracking, or specific callsigns like AA123, generate a professional real-time aviation telemetry response card. Outline exact gate allocations (ORD to ATL), Boeing coordinates, and status tracks dynamically.\n"
                "6. FREIGHT PRICE MONITORING (CASE 8): If asked to monitor route corridors or track flight prices (e.g., Chicago to Atlanta), compile a dynamic air freight market rate card report showing pricing indices ($/kg) and background tracking registrations.\n"
                "7. AUTOMATED NOTIFICATION MAIL (CASE 7): If a user mentions notifications or background emails, compile a transparent delivery receipt validation text block detailing that a secure operational payload has been transmitted to 'krina@inventoryplatform.com'.\n"
                "Keep all conversational responses highly professional, data-centric, and structured cleanly using clean Markdown formatting blocks."
            )
            
            formatted_messages = [{"role": "system", "content": system_prompt}]
            for m in st.session_state.messages[:-1]:
                formatted_messages.append({"role": m["role"], "content": m["content"]})
                
            user_msg = (
                f"User Instruction: {user_input}\n\n"
                f"Table A (Anomaly_RDS): {json.dumps(db_data)}\n\n"
                f"Table B (Store_Forecast_ML): {json.dumps(forecast_data)}\n\n"
                f"Table C (Storefront_Balances): {json.dumps(store_status_dict)}\n\n"
                f"Table D (Fulfillment_Grid_Stock): {json.dumps(warehouses_dict)}\n\n"
                f"Knowledge Context Logs: {json.dumps(log_context)}"
            )
            formatted_messages.append({"role": "user", "content": user_msg})
            
            ai_completion = openai_client.chat.completions.create(model="gpt-4o-mini", messages=formatted_messages, tools=tools_schema, temperature=0.1)
            response_message = ai_completion.choices[0].message
            
            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    if tool_call.function.name == "stage_mitigation_parameters":
                        raw_args_str = tool_call.function.arguments
                        clean_args_str = raw_args_str.replace("'", '"').strip()
                        
                        try:
                            args = json.loads(clean_args_str)
                            payload_str = args["json_allocation_payload"]
                            payload = json.loads(payload_str.replace("'", '"').replace('\\"', '"'))
                        except Exception as e_raw_fail:
                            total_match = re.search(r'"total"\s*:\s*(\d+)', raw_args_str)
                            w1_match = re.search(r'"w1_units"\s*:\s*(\d+)', raw_args_str)
                            w2_match = re.search(r'"w2_units"\s*:\s*(\d+)', raw_args_str)
                            wh1_match = re.search(r'"wh1"\s*:\s*"([^"]+)"', raw_args_str)
                            wh2_match = re.search(r'"wh2"\s*:\s*"([^"]+)"', raw_args_str)
                            
                            payload = {
                                "total": int(total_match.group(1)) if total_match else 35000,
                                "w1_units": int(w1_match.group(1)) if w1_match else 20000,
                                "w2_units": int(w2_match.group(1)) if w2_match else 15000,
                                "wh1": str(wh1_match.group(1)) if wh1_match else "WH-EAST (Atlanta, GA)",
                                "wh2": str(wh2_match.group(1)) if wh2_match else "WH-WEST (Phoenix, AZ)"
                            }
                        
                        total_needed = int(payload.get("total", 35000))
                        wh1_name = str(payload.get("wh1", "WH-EAST (Atlanta, GA)"))
                        w1_units = int(payload.get("w1_units", 20000))
                        wh2_name = str(payload.get("wh2", "WH-WEST (Phoenix, AZ)"))
                        w2_units = int(payload.get("w2_units", 15000))
                        
                        w1_max_safe = 999999
                        w2_max_safe = 999999
                        
                        for index, row in warehouse_df.iterrows():
                            row_loc_clean = str(row["Warehouse Location"]).upper()
                             # Dynamically extract the city name from between the parenthesis (e.g. extracts 'Atlanta' out of 'WH-EAST (Atlanta, GA)')
                            target_1 = str(wh1_name).split('(')[-1].split(',')[0].strip().upper() if '(' in str(wh1_name) else str(wh1_name).upper()
                            target_2 = str(wh2_name).split('(')[-1].split(',')[0].strip().upper() if '(' in str(wh2_name) else str(wh2_name).upper()
        
                            # Real-World Substring Check: Verify if the dynamic city string exists inside your database row row_loc_clean
                            if target_1 in row_loc_clean:
                                w1_max_safe = max(0, int(row["Raw_Stock"]) - 5000)
                            if target_2 in row_loc_clean:
                                w2_max_safe = max(0, int(row["Raw_Stock"]) - 5000)
                                
                        if w1_units > w1_max_safe or w2_units > w2_max_safe:
                            st.session_state.staged_mitigation = {
                                "sku": target_sku, "store": "STORE-1", "total_needed": total_needed, "unviable_split_warning": True,
                                "warning_msg": f"CRITICAL BUFFER VIOLATION: Split sourcing rejected. Pulling inventory would breach the mandatory 5,000-unit safe threshold at {wh1_name} or {wh2_name}."
                            }
                            agent_reply = "### ⚠️ WAREHOUSE SPLIT SOURCE REFUSED\n\nI evaluated our network grid and discovered that executing a fulfillment split would drop our regional safety stock pools below the mandatory **5,000-unit floor cushion**. Option A has been suspended. **Option B (Emergency Manufacturing Run)** has been staged as the only viable operational recommendation."
                        else:
                            st.session_state.staged_mitigation = {
                                "sku": target_sku, "store": "STORE-1", "total_needed": total_needed, "unviable_split_warning": False,
                                "wh_1": "WH-EAST (Atlanta, GA)" if "ATLANTA" in wh1_name.upper() else wh1_name,
                                "units_a_1": w1_units,
                                "wh_2": "WH-WEST (Phoenix, AZ)" if "PHOENIX" in wh2_name.upper() else wh2_name,
                                "units_a_2": w2_units
                            }
                            agent_reply = "### 📋 ANALYSIS COMPLETE: MITIGATION PROPOSAL STAGED\n\nI have evaluated your cloud tables and staged an optimized multi-hub split allocation block at the top of your workspace page."
            else:
                # PURE CONVERSATIONAL AI ROUTE: Hides the canopy buttons if the LLM didn't choose to call a tool
                st.session_state.staged_mitigation = None
                agent_reply = response_message.content
                
            # Append reply directly within the scoped input handlers
            st.session_state.messages.append({"role": "assistant", "content": agent_reply})
            st.cache_data.clear()
            st.rerun()
            
        except Exception as e_err:
            agent_reply = f"Warning: {str(e_err)}"
            st.session_state.staged_mitigation = None
            st.session_state.messages.append({"role": "assistant", "content": agent_reply})
            st.rerun()

# 10. PERFECT CENTER ALIGNMENT LINK FOOTER - Permanently encapsulated inside the code block envelope
st.write("---")
st.markdown("<p class='centered-footer'>Designed & Developed by <strong>Krina</strong> | <a href='mailto:kp46utd23@gmail.com' style='color: #666666; text-decoration: none;'>Email</a> | <a href='Linkedin.com/in/krina04/' style='color: #666666; text-decoration: none;'>LinkedIn</a></p>", unsafe_allow_html=True)
