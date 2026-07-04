"""
Synthetic Data Generator for Local Economic Pulse Dashboard
Generates footfall and business activity data across sectors/localities.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# ---------------------------
# CONFIG
# ---------------------------
NUM_DAYS = 180  # 6 months of data
START_DATE = datetime(2026, 1, 1)

SECTORS = [
    "Market Street", "Tech Park", "Old Town", "Riverside",
    "College Road", "Industrial Zone", "Central Mall", "Station Area"
]

BUSINESS_TYPES = [
    "Retail", "Food & Beverage", "Grocery", "Services",
    "Entertainment", "Healthcare"
]

random.seed(42)
np.random.seed(42)

# ---------------------------
# HELPER FUNCTIONS
# ---------------------------

def base_footfall(sector, day_of_week, day_index):
    """Generate base footfall with weekly seasonality + slow trend."""
    sector_base = {
        "Market Street": 1200, "Tech Park": 900, "Old Town": 700,
        "Riverside": 500, "College Road": 800, "Industrial Zone": 400,
        "Central Mall": 1500, "Station Area": 1100
    }[sector]

    # Weekend boost for market/mall/riverside, weekday boost for tech park/college
    weekend_sectors = ["Market Street", "Central Mall", "Riverside", "Old Town"]
    is_weekend = day_of_week in [5, 6]  # Sat, Sun

    if sector in weekend_sectors and is_weekend:
        multiplier = 1.4
    elif sector in ["Tech Park", "College Road"] and not is_weekend:
        multiplier = 1.3
    else:
        multiplier = 1.0

    # Slow upward trend over 6 months (economic growth simulation)
    trend = 1 + (day_index / NUM_DAYS) * 0.15

    # Random daily noise
    noise = np.random.normal(1.0, 0.08)

    return max(0, sector_base * multiplier * trend * noise)


def inject_anomaly(value, day_index, sector, anomaly_days):
    """Inject sudden drops/spikes on specific days for specific sectors."""
    if day_index in anomaly_days.get(sector, {}):
        anomaly_type = anomaly_days[sector][day_index]
        if anomaly_type == "drop":
            return value * random.uniform(0.3, 0.5)  # 50-70% drop
        elif anomaly_type == "spike":
            return value * random.uniform(1.6, 2.0)  # 60-100% spike
    return value


def generate_anomaly_schedule():
    """Predefine some anomaly events for realism (e.g. festival, construction, closure)."""
    schedule = {
        "Market Street": {45: "spike"},       # festival rush
        "Old Town": {70: "drop", 71: "drop", 72: "drop"},  # road closure/construction
        "Tech Park": {110: "drop"},           # holiday/long weekend
        "Central Mall": {130: "spike"},       # sale event
        "Riverside": {160: "drop", 161: "drop"},  # weather event
    }
    return schedule


# ---------------------------
# MAIN GENERATION
# ---------------------------

def generate_footfall_data():
    anomaly_schedule = generate_anomaly_schedule()
    records = []

    for day_index in range(NUM_DAYS):
        current_date = START_DATE + timedelta(days=day_index)
        day_of_week = current_date.weekday()

        for sector in SECTORS:
            footfall = base_footfall(sector, day_of_week, day_index)
            footfall = inject_anomaly(footfall, day_index, sector, anomaly_schedule)

            records.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "sector": sector,
                "footfall_count": int(footfall),
                "day_of_week": current_date.strftime("%A"),
            })

    return pd.DataFrame(records)


def generate_business_activity_data(footfall_df):
    """Derive business activity (revenue proxy, active businesses) from footfall."""
    records = []

    # Assign a mix of business types per sector
    sector_business_mix = {
        sector: random.sample(BUSINESS_TYPES, k=random.randint(3, len(BUSINESS_TYPES)))
        for sector in SECTORS
    }

    for _, row in footfall_df.iterrows():
        sector = row["sector"]
        footfall = row["footfall_count"]

        for business_type in sector_business_mix[sector]:
            # Different business types convert footfall differently
            conversion_rate = {
                "Retail": 0.15, "Food & Beverage": 0.25, "Grocery": 0.20,
                "Services": 0.08, "Entertainment": 0.12, "Healthcare": 0.05
            }[business_type]

            avg_transaction_value = {
                "Retail": 800, "Food & Beverage": 350, "Grocery": 600,
                "Services": 1200, "Entertainment": 500, "Healthcare": 1500
            }[business_type]

            transactions = int(footfall * conversion_rate * np.random.normal(1.0, 0.1))
            transactions = max(0, transactions)
            revenue_estimate = transactions * avg_transaction_value

            records.append({
                "date": row["date"],
                "sector": sector,
                "business_type": business_type,
                "estimated_transactions": transactions,
                "estimated_revenue": revenue_estimate,
            })

    return pd.DataFrame(records)


# ---------------------------
# RUN SCRIPT
# ---------------------------

if __name__ == "__main__":
    print("Generating footfall data...")
    footfall_df = generate_footfall_data()
    footfall_df.to_csv("data/footfall_data.csv", index=False)
    print(f"Saved {len(footfall_df)} footfall records to data/footfall_data.csv")

    print("Generating business activity data...")
    business_df = generate_business_activity_data(footfall_df)
    business_df.to_csv("data/business_activity.csv", index=False)
    print(f"Saved {len(business_df)} business activity records to data/business_activity.csv")

    print("\nSample footfall data:")
    print(footfall_df.head())
    print("\nSample business activity data:")
    print(business_df.head())