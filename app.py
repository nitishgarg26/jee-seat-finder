import streamlit as st
import sqlite3
import pandas as pd

# Connect to the SQLite database
conn = sqlite3.connect("jee_data.db")
cursor = conn.cursor()

# Load unique values for filters
programs_df = pd.read_sql_query("SELECT DISTINCT [Academic Program Name] FROM jee_seats", conn)
programs = sorted(programs_df["Academic Program Name"].dropna().unique().tolist())

# Predefined categories
computer_keywords = ["Computer", "Data", "AI", "Artificial", "Intelligence"]
electronics_keywords = ["Electronics"]

def match_keywords(name, keywords):
    return any(kw.lower() in name.lower() for kw in keywords)

# Sidebar filters
st.sidebar.header("Filter Options")
rank_range = st.sidebar.slider("Rank Range (Opening to Closing)", 0, 100000, (0, 75000))

# Program multi-select with categories
custom_program_options = ["Computers", "Electronics"] + programs
selected_programs = st.sidebar.multiselect("Select Programs", custom_program_options)

# Seat Type and Quota
seat_types = pd.read_sql_query("SELECT DISTINCT [Seat Type] FROM jee_seats", conn)["Seat Type"].dropna().tolist()
selected_seat_types = st.sidebar.multiselect("Select Seat Types", seat_types)

# Construct SQL query
query = "SELECT * FROM jee_seats WHERE 1=1"
conditions = []

# Rank range filter
conditions.append(f'"Opening Rank" >= {rank_range[0]} AND "Closing Rank" <= {rank_range[1]}')

# Program filter logic
if selected_programs:
    program_conditions = []
    for program in selected_programs:
        if program == "Computers":
            program_conditions.append(" OR ".join([f"[Academic Program Name] LIKE '%{kw}%'" for kw in computer_keywords]))
        elif program == "Electronics":
            program_conditions.append(" OR ".join([f"[Academic Program Name] LIKE '%{kw}%'" for kw in electronics_keywords]))
        else:
            program_conditions.append(f"[Academic Program Name] = '{program}'")
    conditions.append("(" + " OR ".join(program_conditions) + ")")

# Seat Type filter
if selected_seat_types:
    seat_conditions = " OR ".join([f"[Seat Type] = '{st}'" for st in selected_seat_types])
    conditions.append("(" + seat_conditions + ")")

# Final query
if conditions:
    query += " AND " + " AND ".join(conditions)

query += " ORDER BY [Closing Rank] ASC"

# Execute and display
df_result = pd.read_sql_query(query, conn)
st.title("🎓 JEE Seat Finder (Database Powered)")
st.dataframe(df_result)

# Close connection
conn.close()
