import sqlite3

# Connect to the database
conn = sqlite3.connect("jee_data.db")
cursor = conn.cursor()

# Delete rows where Gender column is exactly "Gender"
cursor.execute("DELETE FROM jee_seats WHERE Gender = 'Gender'")
conn.commit()

# Optional: Check how many rows are left
cursor.execute("SELECT COUNT(*) FROM jee_seats")
row_count = cursor.fetchone()[0]
print(f"✅ Rows remaining in jee_seats: {row_count}")

conn.close()
