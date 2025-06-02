import streamlit as st
import pandas as pd
import sqlite3
from hashlib import sha256
from streamlit_javascript import st_javascript
from streamlit_super_slider import st_slider

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="JEE Seat Finder",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Detect screen width
width = st_javascript("window.innerWidth")

# Set a threshold for mobile (e.g., 768px)
is_mobile = width is not None and width < 480

# --- HEADER ---
st.title("🎓 JEE Seat Finder")
st.markdown(
    """
    <div style='font-size:16px; color:#444; margin-bottom:10px;'>
    <b>Opening/Closing Ranks for Open Seats</b> represent <b>CRL</b>.<br>
    <b>Opening/Closing Ranks for EWS, OBC-NCL, SC and ST Seats</b> represent respective <b>Category Ranks</b>.<br>
    <b>Opening/Closing Ranks for PwD Seats</b> represent <b>PwD Ranks</b> within Respective Categories.<br>
    <b>Opening/Closing Ranks for JAC Delhi Seats</b> represent <b>CRL</b> within Respective Categories.<br>
    </div>
    """,
    unsafe_allow_html=True
)
st.info("Filter below to find your best-fit colleges and programs.")

# --- CONNECT TO DATABASE ---
conn = sqlite3.connect("jee_data.db", check_same_thread=False)
cursor = conn.cursor()
df = pd.read_sql_query("SELECT * FROM jee_seats", conn)

def filter_widgets():
    college_types = sorted(df["Type"].dropna().unique())
    selected_types = st.multiselect("🏫 College Type", college_types, default=college_types)

    filtered_df_for_colleges = df[df["Type"].isin(selected_types)]
    college_names = sorted(filtered_df_for_colleges["Institute"].dropna().unique())
    college_names_with_all = ["All"] + college_names
    selected_colleges = st.multiselect("🏢 College Name", college_names_with_all, default=["All"])

    if "All" in selected_colleges or not selected_colleges:
        filtered_df_for_programs = filtered_df_for_colleges
        selected_colleges = college_names
    else:
        filtered_df_for_programs = filtered_df_for_colleges[filtered_df_for_colleges["Institute"].isin(selected_colleges)]

    all_programs = sorted(filtered_df_for_programs["Academic Program Name"].dropna().unique().tolist())
    program_group = st.multiselect("🎯 Program(s)", ["Computers", "Electronics"] + all_programs)

    min_rank = st.number_input(
        "Minimum Closing Rank",
        min_value=0,
        max_value=1000000,
        value=0,
        step=1000,
        format="%d"
    )
    max_rank = st.number_input(
        "Maximum Closing Rank",
        min_value=0,
        max_value=1000000,
        value=1000000,
        step=50000,
        format="%d"
    )
    rank_range = (min_rank, max_rank)
    
    gender = st.multiselect("⚧️ Gender", options=sorted(df["Gender"].dropna().unique()), default= "Gender-Neutral")
    quota = st.multiselect("🎟️ Quota", options=sorted(df["Quota"].dropna().unique()),default= "AI")
    seat_type = st.multiselect("💺 Seat Type", options=sorted(df["Seat Type"].dropna().unique()), default=["OPEN"])

    return selected_types, selected_colleges, program_group, rank_range, gender, quota, seat_type, filtered_df_for_programs

# --- FILTERS: Conditional Placement ---
admin_mode = False
if is_mobile:
    st.markdown("### 🔍 Filters")
    admin_mode = st.checkbox("🔑 Admin Login")
    if not admin_mode:
        selected_types, selected_colleges, program_group, rank_range, gender, quota, seat_type, filtered_df_for_programs = filter_widgets()
else:
    with st.sidebar:
        st.header("🔍 Filters")
        admin_mode = st.checkbox("🔑 Admin Login")
        if not admin_mode:
            selected_types, selected_colleges, program_group, rank_range, gender, quota, seat_type, filtered_df_for_programs = filter_widgets()

# --- FILTER LOGIC (same as before, using selected_* variables) ---
if not admin_mode:
    filtered_df = df[df["Type"].isin(selected_types)]
    if selected_colleges and "All" not in selected_colleges:
        filtered_df = filtered_df[filtered_df["Institute"].isin(selected_colleges)]
    filtered_df = filtered_df[(filtered_df["Closing Rank"] >= rank_range[0]) & (filtered_df["Closing Rank"] <= rank_range[1])]


    if gender:
        filtered_df = filtered_df[filtered_df["Gender"].isin(gender)]
    if seat_type:
        filtered_df = filtered_df[filtered_df["Seat Type"].isin(seat_type)]
    if quota:
        filtered_df = filtered_df[filtered_df["Quota"].isin(quota)]

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

    # Format ranks with commas for display
    # Keep data numeric for proper sorting, format only for display
    st.subheader("🎯 Matching Programs")
    st.dataframe(
        filtered_df,
        use_container_width=True,
        column_config={
            "Opening Rank": st.column_config.NumberColumn(
                "Opening Rank",
                format="{:,}",  # This should show commas
                help="Opening rank for admission"
            ),
            "Closing Rank": st.column_config.NumberColumn(
                "Closing Rank",
                format="{:,}",  # This should show commas
                help="Closing rank for admission"
            )
        }
    )

    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download results as CSV",
        data=csv,
        file_name="jee_filtered_results.csv",
        mime="text/csv",
        help="Download your filtered results."
    )
# --- Feedback Section ---
st.subheader("📝 Submit Your Feedback")
feedback = st.text_area("Please provide your feedback or suggestions:")
if st.button("Submit Feedback"):
    if feedback.strip():
        # Save feedback to a file, database, or email here if desired
        st.success("Thank you for your feedback!")
        with open("feedback.txt", "a") as f:
            f.write(feedback + "\n---\n")
        # Optionally, clear the feedback box after submission:
        # st.experimental_rerun()
    else:
        st.warning("Please enter some feedback before submitting.")



# --- ADMIN PANEL (unchanged) ---
if admin_mode:
    st.subheader("🔒 Admin Panel")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    ADMIN_HASH = "c7282ea501f7b9491be0a7e2409293f4ee823d9f7247d986695a975f894259ce"
    if st.button("Login"):
        if username == "admin" and sha256(password.encode('utf-8')).hexdigest() == ADMIN_HASH:
            st.success("Logged in successfully!")
            st.markdown("---")
            st.subheader("➕ Add New Seat Record")
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

st.markdown(
    "<hr style='margin-top:2em;margin-bottom:1em;'>"
    "<div style='text-align:center; color: #999;'>"
    "</div>",
    unsafe_allow_html=True
)
