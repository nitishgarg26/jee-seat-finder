import streamlit as st
import pandas as pd
import sqlite3
from hashlib import sha256

# --- THEME AND PAGE CONFIG ---
st.set_page_config(
    page_title="JEE Seat Finder",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR STYLE ---
st.markdown("""
    <style>
    .main h1 { color: #2e7bcf; font-weight: 700; }
    .main h2 { color: #1b5e20; }
    section[data-testid="stSidebar"] {
        background-color: #f7f9fa;
        border-right: 2px solid #e0e0e0;
    }
    .css-1d391kg { font-size: 16px; }
    @media (max-width: 600px) {
        .main h1 { font-size: 2rem !important; }
        .main h2 { font-size: 1.5rem !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER & INFO ---
st.image(
    "https://cdn-icons-png.flaticon.com/512/3135/3135755.png",
    width=60,
)
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
st.info("Use the filters on the left to find your best-fit colleges and programs. The app works great on mobile too!")

# --- CONNECT TO DATABASE ---
conn = sqlite3.connect("jee_data.db", check_same_thread=False)
cursor = conn.cursor()
df = pd.read_sql_query("SELECT * FROM jee_seats", conn)

# --- SIDEBAR FILTERS ---
with st.sidebar:
    st.header("🔍 Filter Options")
    st.markdown("Customize your search:")

    # Admin mode toggle
    admin_mode = st.checkbox("🔑 Admin Login")

if not admin_mode:
    # 1. College Type
    college_types = sorted(df["Type"].dropna().unique())
    selected_types = st.sidebar.multiselect("🏫 College Type", college_types, default=college_types, help="Select one or more college types.")

    # 2. College Name (filtered by College Type), with "All" option
    filtered_df_for_colleges = df[df["Type"].isin(selected_types)]
    college_names = sorted(filtered_df_for_colleges["Institute"].dropna().unique())
    college_names_with_all = ["All"] + college_names
    selected_colleges = st.sidebar.multiselect("🏢 College Name", college_names_with_all, default=["All"], help="Choose colleges or select 'All'.")

    # Handle "All" logic
    if "All" in selected_colleges or not selected_colleges:
        filtered_df_for_programs = filtered_df_for_colleges
        selected_colleges = college_names
    else:
        filtered_df_for_programs = filtered_df_for_colleges[filtered_df_for_colleges["Institute"].isin(selected_colleges)]

    # 3. Program (filtered by College Name)
    all_programs = sorted(filtered_df_for_programs["Academic Program Name"].dropna().unique().tolist())
    program_group = st.sidebar.multiselect("🎓 Program(s)", ["Computers", "Electronics"] + all_programs, help="Select program groups or specific programs.")

    # Gender
    gender = st.sidebar.multiselect("⚧️ Gender", options=sorted(df["Gender"].dropna().unique()), help="Select gender-specific seats.")

    # Quota
    quota = st.sidebar.multiselect("🎟️ Quota", options=sorted(df["Quota"].dropna().unique()), help="Select quota types.")

    # Seat Type
    seat_type = st.sidebar.multiselect("💺 Seat Type", options=sorted(df["Seat Type"].dropna().unique()), help="Select seat types.")

    # Rank Range
    rank_range = st.sidebar.slider("🏅 Rank Range (Opening to Closing)", 0, 200000, (0, 200000), step=1000, help="Set your JEE rank range.")

    # --- FILTER LOGIC ---
    filtered_df = df[df["Type"].isin(selected_types)]
    filtered_df = filtered_df[(filtered_df["Opening Rank"] >= rank_range[0]) & (filtered_df["Closing Rank"] <= rank_range[1])]

    if gender:
        filtered_df = filtered_df[filtered_df["Gender"].isin(gender)]
    if seat_type:
        filtered_df = filtered_df[filtered_df["Seat Type"].isin(seat_type)]
    if quota:
        filtered_df = filtered_df[filtered_df["Quota"].isin(quota)]

    # Program group logic
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
    selected_programs += [pg for pg in program_group if pg not in ["Computers", "Electronics"]]
    if selected_programs:
        filtered_df = filtered_df[filtered_df["Academic Program Name"].isin(selected_programs)]

    filtered_df = filtered_df.sort_values(by="Closing Rank")

    # --- MAIN CONTENT: RESULTS TABLE ---
    st.subheader("🎯 Matching Programs")
    if len(filtered_df) == 0:
        st.warning("No results found. Try adjusting your filters.")
    else:
        st.dataframe(filtered_df, use_container_width=True, height=450)

        # Download button
        csv = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download results as CSV",
            data=csv,
            file_name="jee_filtered_results.csv",
            mime="text/csv",
            help="Download your filtered results."
        )

else:
    # --- ADMIN PANEL ---
    st.subheader("🔒 Admin Panel")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    # SHA-256 hash for password: "admin123"
    ADMIN_HASH = "c7282ea501f7b9491be0a7e2409293f4ee823d9f7247d986695a975f894259ce"

    if st.button("Login"):
        if username == "admin" and sha256(password.encode('utf-8')).hexdigest() == ADMIN_HASH:
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

# --- FOOTER ---
st.markdown(
    "<hr style='margin-top:2em;margin-bottom:1em;'>"
    "<div style='text-align:center; color: #999;'>"
    "Made with ❤️ using Streamlit &middot; Designed for mobile and desktop"
    "</div>",
    unsafe_allow_html=True
)
