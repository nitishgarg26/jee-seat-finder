import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="JEE Seat Finder", layout="wide")
st.title("🎓 JEE Seat Finder")

# Connect to the SQLite database
conn = sqlite3.connect("jee_data.db")
cursor = conn.cursor()
df = pd.read_sql_query("SELECT * FROM jee_seats", conn)

# Sidebar filters
st.sidebar.header("🔍 Filter Options")

# Admin mode toggle
admin_mode = st.sidebar.checkbox("🔑 Admin Login")

if not admin_mode:
    # User view
    gender = st.sidebar.multiselect("Gender", options=sorted(df["Gender"].unique()))
    seat_type = st.sidebar.multiselect("Seat Type", options=sorted(df["Seat Type"].unique()))
    rank_range = st.sidebar.slider("Rank Range (Opening to Closing)", 0, 200000, (0, 200000), step=1000)

    # Program filter with custom groups
    program_group = st.sidebar.multiselect(
        "Program Group",
        ["Computers", "Electronics", "Custom"]
    )
    custom_programs = []
    if "Computers" in program_group:
        custom_programs += df[df["Academic Program Name"].str.contains("Computer|Data|AI|Artificial|Intelligence", case=False, na=False)]["Academic Program Name"].unique().tolist()
    if "Electronics" in program_group:
        custom_programs += df[df["Academic Program Name"].str.contains("Electronics", case=False, na=False)]["Academic Program Name"].unique().tolist()
    if "Custom" in program_group:
        custom_programs += st.sidebar.multiselect("Select Programs", options=sorted(df["Academic Program Name"].unique()))

    # Apply filters
    filtered_df = df.copy()
    filtered_df = filtered_df[(filtered_df["Opening Rank"] >= rank_range[0]) & (filtered_df["Closing Rank"] <= rank_range[1])]
    if gender:
        filtered_df = filtered_df[filtered_df["Gender"].isin(gender)]
    if seat_type:
        filtered_df = filtered_df[filtered_df["Seat Type"].isin(seat_type)]
    if program_group:
        filtered_df = filtered_df[filtered_df["Academic Program Name"].isin(custom_programs)]

    # Sort and display
    filtered_df = filtered_df.sort_values(by="Closing Rank")
    st.dataframe(filtered_df, use_container_width=True)

    # CSV download
    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download results as CSV",
        data=csv,
        file_name="jee_filtered_results.csv",
        mime="text/csv"
    )
else:
    # Admin login
    st.subheader("🔒 Admin Panel")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "admin123":
            st.success("Logged in successfully!")
            st.markdown("---")
            st.subheader("➕ Add New Seat Record")

            # Form to add new data
            with st.form("data_entry_form"):
                inst_type = st.selectbox("Type", ["IIT", "NIT", "IIIT", "GFTI"])
                existing_institutes = sorted(df["Institute"].dropna().unique())
                existing_locations = sorted(df["Location"].dropna().unique())
                existing_programs = sorted(df["Academic Program Name"].dropna().unique())

                institute = st.selectbox("Institute", options=[""] + existing_institutes)
                location = st.selectbox("Location", options=[""] + existing_locations)
                program = st.selectbox("Academic Program Name", options=[""] + existing_programs)

                quota = st.selectbox("Quota", ["AI", "HS", "OS"])
                seat_type = st.text_input("Seat Type")
                gender = st.selectbox("Gender", ["Gender-Neutral", "Female-only (including Supernumerary)"])
                opening = st.number_input("Opening Rank", min_value=0, step=1)
                closing = st.number_input("Closing Rank", min_value=0, step=1)
                year = st.selectbox("Year", [2021, 2022, 2023, 2024])

                submitted = st.form_submit_button("Add Record")
                if submitted:
                    cursor.execute("""
                        INSERT INTO jee_seats (Institute, Location, Type, `Academic Program Name`, Quota, `Seat Type`, Gender, `Opening Rank`, `Closing Rank`, Year)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (institute, location, inst_type, program, quota, seat_type, gender, opening, closing, year))
                    conn.commit()
                    st.success("✅ Record added successfully!")
        else:
            st.error("Invalid credentials.")
