import sqlite3
# Connect to the database
conn = sqlite3.connect("jee_data.db")
cursor = conn.cursor()

# Check if the table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jee_seats';")
result = cursor.fetchone()

if result:
    # Update Gender values from 'Female' to 'Female-only (including Supernumerary)'
    cursor.execute("""
        UPDATE jee_seats
        SET Gender = 'Female-only (including Supernumerary)'
        WHERE Gender = 'Female'
    """)
    conn.commit()
    print("✅ All 'Female' values updated to 'Female-only (including Supernumerary)' in Gender column.")
else:
    print("❌ Table 'jee_seats' does not exist in the database.")

conn.close()
