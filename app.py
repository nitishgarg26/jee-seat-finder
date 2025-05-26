import streamlit as st
import pandas as pd
import sqlite3

# Set page layout to wide
st.set_page_config(layout="wide", page_title="JEE Seat Finder")

# Connect to SQLite database
conn = sqlite3.connect("jee_data.db")
cursor = conn.cursor()

# Sidebar filters
st.sidebar.header("Filter Options")
rank_range = st.sidebar.slider("Rank Range (Opening to Closing)", 0, 100000, (0, 75000))

# Load distinct values for dynamic filters
df = pd.read_sql_query("SELECT DISTINCT Gender, `Seat Type`, `Academic Program Name` FROM jee_seats", conn)

# Gender filter
genders = df["Gender"].dropna().unique().tolist()
selected_genders = st.sidebar.multiselect("Select Gender", genders)

# Seat Type filter
seat_types = df["Seat Type"].dropna().unique().tolist()
selected_seat_types = st.sidebar.multiselect("Select Seat Type", seat_types)

# Academic Program filter with categorized options
programs_df = df["Academic Program Name"].dropna().unique().tolist()
categorized_programs = [
    "Computers",
    "Electronics"
] + sorted(programs_df)

selected_programs = st.sidebar.multiselect(
    "Select Academic Programs",
    categorized_programs,
    default=[]
)

# Build SQL query conditions
conditions = [
    f"`Opening Rank` >= {rank_range[0]} AND `Closing Rank` <= {rank_range[1]}"
]

# Gender filter
if selected_genders:
    gender_cond = " OR ".join([f"Gender = '{g}'" for g in selected_genders])
    conditions.append(f"({gender_cond})")

# Seat type filter
if selected_seat_types:
    seat_cond = " OR ".join([f"`Seat Type` = '{s}'" for s in selected_seat_types])
    conditions.append(f"({seat_cond})")

# Academic program filter
if selected_programs:
    program_keywords = {
        "Computers": ["Computer", "Data", "AI", "Artificial", "Intelligence"],
        "Electronics": ["Electronics"]
    }
    keywords = []
    for prog in selected_programs:
        if prog in program_keywords:
            keywords.extend(program_keywords[prog])
        else:
            keywords.append(prog)
    program_cond = " OR ".join([f"`Academic Program Name` LIKE '%{k}%'" for k in keywords])
    conditions.append(f"({program_cond})")

# Final SQL query
query = "SELECT * FROM jee_seats"
if conditions:
    query += " WHERE " + " AND ".join(conditions)
query += " ORDER BY `Closing Rank` ASC"

# Fetch data
try:
    df_result = pd.read_sql_query(query, conn)
except Exception as e:
    st.error(f"Error retrieving data: {e}")
    df_result = pd.DataFrame()

# Display results
st.title("\U0001F393 JEE Seat Finder (Database Powered)")

if not df_result.empty:
    st.markdown(f"### Showing {len(df_result)} results")

    st.dataframe(
        df_result,
        use_container_width=True,
        hide_index=True,
    )

    # CSV download option
    csv = df_result.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="\u2B07\uFE0F Download Results as CSV",
        data=csv,
        file_name='jee_seat_results.csv',
        mime='text/csv',
    )
else:
    st.warning("No results found. Try adjusting your filters.")
