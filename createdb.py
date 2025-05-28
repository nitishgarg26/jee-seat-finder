import pandas as pd
import sqlite3

# Load CSV
df = pd.read_csv("College Counselling - JAC.csv")

# Ensure ranks are numeric
df["Closing Rank"] = pd.to_numeric(df["Closing Rank"], errors="coerce")
df["Opening Rank"] = pd.to_numeric(df["Opening Rank"], errors="coerce")

# Create SQLite DB and write to table
conn = sqlite3.connect("jee_data.db")
df.to_sql("jee_seats", conn, if_exists="append", index=False)
conn.close()

print("✅ Data successfully loaded into jee_data.db")
