import sqlite3

conn = sqlite3.connect('jee_data.db')
cursor = conn.cursor()

cursor.execute("UPDATE jee_seats SET Gender = 'Female-only (including Supernumerary)' WHERE Gender = 'Female Only'")
conn.commit()

rows_affected = cursor.rowcount

conn.close()

print(f"Rows updated: {rows_affected}")
