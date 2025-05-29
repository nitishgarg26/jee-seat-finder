import streamlit as st
import pandas as pd
import sqlite3
from hashlib import sha256

st.set_page_config(page_title="JEE Seat Finder", layout="wide")
st.title("🎓 JEE Seat Finder")
st.markdown(
    """
    <div style='font-size:16px; color:#444; margin-bottom:16px;'>
    <b>Opening/Closing Ranks for Open Seats</b> represent <b>CRL</b>.<br>
    <b>Opening/Closing Ranks for EWS, OBC-NCL, SC and ST Seats</b> represent respective <b>Category Ranks</b>.<br>
    <b>Opening/Closing Ranks for PwD Seats</b> represent <b>PwD Ranks</b> within Respective Categories.<br>
    <b>Opening/Closing Ranks for JAC Delhi Seats</b> represent <b>CRL</b> within Respective Categories.<br>
    </div>
    """,
    unsafe_allow_html=True
)

# Connect to the SQLite database
conn = sqlite3.connect("jee_data.db")
cursor = conn.cursor()
df = pd.read_sql_query("SELECT * FROM jee_seats", conn)

# Sidebar filters
st.sidebar.header("🔍 Filter Options")

# Admin mode toggle
admin_mode = st.sidebar.checkbox("🔑 Admin Login")

if not admin_mode:
    # User filters
    
    # 1. College Type
    college_types = sorted(df["Type"].dropna().unique())
    selected_types = st.sidebar.multiselect("College Type", college_types, default=college_types)
    
    # 2. College Name (filtered by College Type), with "All" option
    filtered_df_for_colleges = df[df["Type"].isin(selected_types)]
    college_names = sorted(filtered_df_for_colleges["Institute"].dropna().unique())
    college_names_with_all = ["All"] + college_names

    selected_colleges = st.sidebar.multiselect(
    "College Name",
    college_names_with_all,
    default=["All"]
    )   

    # Handle "All" selection logic
    if "All" in selected_colleges or not selected_colleges:
        filtered_df_for_programs = filtered_df_for_colleges
        selected_colleges = college_names  # for further filtering
    else:
        filtered_df_for_programs = filtered_df_for_colleges[filtered_df_for_colleges["Institute"].isin(selected_colleges)]
    
    # 3. Program (filtered by College Name)
    filtered_df_for_programs = filtered_df_for_colleges[filtered_df_for_colleges["Institute"].isin(selected_colleges)]
    all_programs = sorted(filtered_df_for_programs["Academic Program Name"].dropna().unique().tolist())
    program_group = st.sidebar.multiselect(
    "Select Program(s)",
    ["Computers", "Electronics"] + all_programs
    )

    # Gender filter
    gender = st.sidebar.multiselect("Gender", options=sorted(df["Gender"].dropna().unique()))

    # Quota filter (new)
    quota = st.sidebar.multiselect("Quota", options=sorted(df["Quota"].dropna().unique()))

    # Seat type filter
    seat_type = st.sidebar.multiselect("Seat Type", options=sorted(df["Seat Type"].dropna().unique()))

    # Rank range slider (opening and closing)
    rank_range = st.sidebar.slider("Rank Range (Closing)", 0, 200000, (0, 1000000), step=1000)

    # Apply filters step by step
    filtered_df = df[df["Type"].isin(selected_types)]
    filtered_df = filtered_df[(filtered_df["Closing Rank"] >= rank_range[0]) & (filtered_df["Closing Rank"] <= rank_range[1])]

    if gender:
        filtered_df = filtered_df[filtered_df["Gender"].isin(gender)]
    if seat_type:
        filtered_df = filtered_df[filtered_df["Seat Type"].isin(seat_type)]
    if quota:
        filtered_df = filtered_df[filtered_df["Quota"].isin(quota)]

    # Program filtering logic with groups
    selected_programs = []
    if "Computers" in program_group:
        selected_programs += filtered_df_for_programs[
            filtered_df_for_programs["Academic Program Name"].str.contains(
                "Computer|Data|AI|Artificial|Intelligence", case=False, na=False
            )
        ]["Academic Program Name"].unique().tolist()

    if "Electronics" in program_group:
        selected_programs += filtered_df_for_programs[
            filtered_df_for_programs["Academic Program Name"].str.contains(
                "Electronics", case=False, na=False
            )
        ]["Academic Program Name"].unique().tolist()

    # Add any explicitly selected programs (not groups)
    selected_programs += [pg for pg in program_group if pg not in ["Computers", "Electronics"]]

    if selected_programs:
        filtered_df = filtered_df[filtered_df["Academic Program Name"].isin(selected_programs)]

    # Sort by Closing Rank
    filtered_df = filtered_df.sort_values(by="Closing Rank")

    # Display the filtered dataframe
    st.dataframe(filtered_df, use_container_width=True)

    # CSV download option
    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download results as CSV",
        data=csv,
        file_name="jee_filtered_results.csv",
        mime="text/csv"
    )

else:
    # Admin login and add data panel
    st.subheader("🔒 Admin Panel")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and sha256(password.encode('utf-8')).hexdigest() == "0xc7282ea501f7b9491be0a7e2409293f4ee823d9f7247d986695a975f894259ce":
            st.success("Logged in successfully!")
            st.markdown("---")
            st.subheader("➕ Add New Seat Record")

            # Suggestions for admin entry
            existing_institutes = sorted(df["Institute"].dropna().unique())
            existing_locations = sorted(df["Location"].dropna().unique())
            existing_programs = sorted(df["Academic Program Name"].dropna().unique())

            with st.form("data_entry_form"):
                institute = st.selectbox("Institute", options=[""] + existing_institutes)
                location = st.selectbox("Location", options=[""] + existing_locations)
                inst_type = st.selectbox("Type", ["IIT", "NIT", "IIIT", "GFTI"])
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
