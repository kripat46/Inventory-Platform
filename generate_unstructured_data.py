import os

# Define the production anomalies to feed the GenAI agent
unstructured_docs = {
    "logistics_update_2026_01.txt": (
        "LOGISTICS REPORT - JAN 2026\n"
        "Due to an intense winter storm system across the Midwest on January 12, 2026, "
        "interstate closures severely disrupted fleet operations. Shipments from our primary "
        "Ohio distribution hub traveling to Texas regional storefronts faced extended transit holds, "
        "resulting in a 5-business-day delivery delay for key inventory categories."
    ),
    "promo_calendar_q2.txt": (
        "MARKETING & CAMPAIGN BRIEF - Q2\n"
        "Promotional Event Notice: SKU-102 was actively featured in a regional BOGO (Buy One Get One) "
        "coupon campaign distributed via mobile application channels. The campaign ran from April 1 "
        "through April 7, triggering an instantaneous 300% demand spike across local retail nodes."
    ),
    "supplier_disruption_electronics.txt": (
        "SUPPLY CHAIN ALERT - MARCH 2026\n"
        "A critical microchip fabrication component short-circuit at our major semiconductor vendor "
        "in Taiwan caused a complete production line shutdown from March 5 to March 14. Factory output "
        "allocations for SKU-405 and SKU-408 dropped by 45%, impacting inbound ocean freight timelines."
    ),
    "warehouse_audit_fl.txt": (
        "FACILITY AUDIT REPORT - FLORIDA REGION\n"
        "An internal physical inventory reconciliation audit conducted at the Miami fulfillment hub "
        "on May 18 identified a major software mismatch. Over 1,200 units of SKU-882 were misallocated "
        "to a legacy bin location, creating an artificial 'Out of Stock' condition on the live system."
    ),
    "competitor_price_war.txt": (
        "COMPETITIVE INTELLIGENCE DAILY\n"
        "Effective June 1, a primary competitor launched an aggressive 40% liquidation discount on equivalent "
        "home electronics lines. This pricing shift dramatically reduced consumer conversion velocity for "
        "our regional SKU-511 items across midwest brick-and-mortar storefronts."
    )
}

# Expand the list programmatically to match your 15-20 document requirement
for i in range(1, 16):
    doc_name = f"incident_report_batch_{i}.txt"
    unstructured_docs[doc_name] = (
        f"SUPPLY CHAIN INCIDENT TICKET #{2930 + i}\n"
        f"Timestamp: 2026-04-12\n"
        f"Impacted Scope: SKU-{100 + i} through SKU-{105 + i}.\n"
        f"Description: Routine regional maintenance overhead operations delayed order picking "
        f"efficiencies at fulfillment node #{i % 4 + 1} by approximately 36 hours. Minor downstream stock variations expected."
    )

def deploy_mock_data():
    target_dir = os.path.join("data", "unstructured")
    os.makedirs(target_dir, exist_ok=True)
    
    print(f"Generating {len(unstructured_docs)} operational intelligence documents...")
    for filename, content in unstructured_docs.items():
        file_path = os.path.join(target_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
    print(f"Success! All unstructured context files successfully deployed to: {target_dir}")

if __name__ == "__main__":
    deploy_mock_data()
