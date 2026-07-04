"""
Load synthetic CSV data into a local SQLite database.
"""

import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "economic_pulse.db")

def load_data():
    conn = sqlite3.connect(DB_PATH)

    footfall_df = pd.read_csv(os.path.join(os.path.dirname(__file__), "footfall_data.csv"))
    business_df = pd.read_csv(os.path.join(os.path.dirname(__file__), "business_activity.csv"))

    footfall_df.to_sql("footfall", conn, if_exists="replace", index=False)
    business_df.to_sql("business_activity", conn, if_exists="replace", index=False)

    conn.close()
    print(f"Loaded data into SQLite database at: {DB_PATH}")
    print(f"Tables created: footfall ({len(footfall_df)} rows), business_activity ({len(business_df)} rows)")


if __name__ == "__main__":
    load_data()