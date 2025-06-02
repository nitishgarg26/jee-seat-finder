import streamlit as st
import pandas as pd
from streamlit_javascript import st_javascript
from hashlib import sha256
from auth import initialize_session, login_page, logout
from shortlist import add_to_shortlist, shortlist_page
from database import setup_user_tables, get_jee_data, get_connection

# Initialize database and session
setup_user_tables()
initialize_session()

st.set_page_config(
    page_title="JEE Seat Finder",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .block-container {
        max-width: 100vw !important;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    .main h1 { color: #2e7bcf; font-weight: 700; }
    .main h2 { color: #1b5e20; }
    section[data-testid="stSidebar"] {
        background-color: #f7f9fa;
        border-right: 2px solid #e0e0e0;
    }
    .login-prompt {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
    @media (max-width: 600px) {
        .main h1 { font-size: 2rem !important; }
        .main h2 { font-size: 1.5rem !important; }
    }
    </style>
""", unsafe_allow_html=True)

def filter_widgets():
    """Reusable filter widgets function"""
    df = get_jee_data()
    
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
    
    min_rank = st.number_input("Minimum Closing Rank", min_value=0, max_value=1000000, value=0, step=1000, format="%d")
    max_rank = st.number_input("Maximum Closing Rank", min_value=0, max_value=1000000, value=1000000, step=1000, format="%d")
    
    gender = st.multiselect("⚧️ Gender", options=sorted(df["Gender"].dropna().unique()))
    quota = st.multiselect("🎟️ Quota", options=sorted(df["Quota"].dropna().unique()))
    seat_type = st.multiselect("💺 Seat Type", options=sorted(df["Seat Type"].dropna().unique()), default=["OPEN"])
    
    rank_range = (min_rank, max_rank)
    return selected_types, selected_colleges, program_group, rank_range, gender, quota, seat_type, filtered_df_for_programs

def guest_search_page():
    """Search functionality for guest users (without shortlisting)"""
    # Header for guest users
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🎓 JEE Seat Finder")
    with col2:
        if st.button("🔐 Login / Sign Up"):
            st.session_state.show_login = True
            st.rerun()
    
    st.markdown("""
    <div style='font-size:15px; color:#444; margin-bottom:10px;'>
    <b>Opening/Closing Ranks for Open Seats</b> represent <b>CRL</b>.<br>
    <b>Opening/Closing Ranks for EWS, OBC-NCL, SC and ST Seats</b> represent respective <b>Category Ranks</b>.<br>
    <b>Opening/Closing Ranks for PwD Seats</b> represent <b>PwD Ranks</b> within Respective Categories.<br>
    <b>Opening/Closing Ranks for JAC Delhi Seats</b> represent <b>CRL</b> within Respective Categories.<br>
    </div>
    """, unsafe_allow_html=True)
    
    # Login prompt box
    st.markdown("""
    <div class='login-prompt'>
    <h4>💡 Create an account to unlock advanced features:</h4>
    <ul>
    <li>📌 Save your favorite colleges to a personal shortlist</li>
    <li>📝 Add notes to your shortlisted options</li>
    <li>📥 Download your shortlist for easy reference</li>
    <li>🔄 Access your data from any device</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Device detection for responsive layout
    width = st_javascript("window.innerWidth")
    is_mobile = width is not None and width < 768
    
    # Get data
    df = get_jee_data()
    
    # Responsive filter placement
    if is_mobile:
        st.markdown("### 🔍 Filters")
        selected_types, selected_colleges, program_group, rank_range, gender, quota, seat_type, filtered_df_for_programs = filter_widgets()
    else:
        with st.sidebar:
            st.header("🔍 Filters")
            selected_types, selected_colleges, program_group, rank_range, gender, quota, seat_type, filtered_df_for_programs = filter_widgets()
    
    # Apply filters (same logic as before)
    filtered_df = df[df["Type"].isin(selected_types)]
    if selected_colleges and "All" not in selected_colleges:
        filtered_df = filtered_df[filtered_df["Institute"].isin(selected_colleges)]
    filtered_df = filtered_df[
        (filtered_df["Closing Rank"] >= rank_range[0]) &
        (filtered_df["Closing Rank"] <= rank_range[1])
    ]
    
    if gender:
        filtered_df = filtered_df[filtered_df["Gender"].isin(gender)]
    if seat_type:
        filtered_df = filtered_df[filtered_df["Seat Type"].isin(seat_type)]
    if quota:
        filtered_df = filtered_df[filtered_df["Quota"].isin(quota)]
    
    # Program filtering logic
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
    display_df = filtered_df.copy()
    if "Closing Rank" in display_df.columns:
        display_df["Closing Rank"] = display_df["Closing Rank"].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "")
    if "Opening Rank" in display_df.columns:
        display_df["Opening Rank"] = display_df["Opening Rank"].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "")
    
    # Display results
    st.subheader("🎯 Matching Programs")
    if len(filtered_df) == 0:
        st.warning("No results found. Try adjusting your filters.")
        return
    
    # Full table display
    st.write(f"Found **{len(filtered_df)}** matching programs:")
    st.dataframe(display_df, use_container_width=True, height=400)
    
    # Show individual results with login prompt for shortlist
    st.markdown("### Want to save these results?")
    st.info("💡 **Create an account** to save your favorite options to a personal shortlist!")
    
    for idx, row in filtered_df.iterrows():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{row['Institute']}** - {row['Academic Program Name']}")
            st.markdown(f"Closing Rank: {row['Closing Rank']:,} | Seat Type: {row['Seat Type']} | Quota: {row['Quota']} | Gender: {row['Gender']}")
        with col2:
            if st.button(f"🔐 Login to Save", key=f"login_prompt_{idx}"):
                st.session_state.show_login = True
                st.rerun()
        st.markdown("---")
    
    # Download search results as CSV (available to all users)
    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Search Results as CSV",
        data=csv,
        file_name="jee_search_results.csv",
        mime="text/csv",
        help="Download your filtered search results."
    )
    
    # Feedback Section (available to all users)
    st.markdown("---")
    st.subheader("📝 Submit Your Feedback")
    feedback = st.text_area("Please provide your feedback or suggestions about the app:")
    
    if st.button("Submit Feedback"):
        if feedback.strip():
            try:
                with open("feedback.txt", "a") as f:
                    f.write(f"User: Guest\n")
                    f.write(f"Feedback: {feedback}\n")
                    f.write(f"Timestamp: {pd.Timestamp.now()}\n")
                    f.write("---\n")
                st.success("Thank you for your feedback!")
            except Exception as e:
                st.success("Thank you for your feedback!")
        else:
            st.warning("Please enter some feedback before submitting.")

def logged_in_search_page():
    """Search functionality for logged-in users (with shortlisting)"""
    st.markdown("""
    <div style='font-size:15px; color:#444; margin-bottom:10px;'>
    <b>Opening/Closing Ranks for Open Seats</b> represent <b>CRL</b>.<br>
    <b>Opening/Closing Ranks for EWS, OBC-NCL, SC and ST Seats</b> represent respective <b>Category Ranks</b>.<br>
    <b>Opening/Closing Ranks for PwD Seats</b> represent <b>PwD Ranks</b> within Respective Categories.<br>
    <b>Opening/Closing Ranks for JAC Delhi Seats</b> represent <b>CRL</b> within Respective Categories.<br>
    </div>
    """, unsafe_allow_html=True)
    
    # Device detection for responsive layout
    width = st_javascript("window.innerWidth")
    is_mobile = width is not None and width < 768
    
    # Get data
    df = get_jee_data()
    
    # Responsive filter placement
    if is_mobile:
        st.markdown("### 🔍 Filters")
        selected_types, selected_colleges, program_group, rank_range, gender, quota, seat_type, filtered_df_for_programs = filter_widgets()
    else:
        with st.sidebar:
            st.header("🔍 Filters")
            selected_types, selected_colleges, program_group, rank_range, gender, quota, seat_type, filtered_df_for_programs = filter_widgets()
    
    # Apply filters (same logic as before)
    filtered_df = df[df["Type"].isin(selected_types)]
    if selected_colleges and "All" not in selected_colleges:
        filtered_df = filtered_df[filtered_df["Institute"].isin(selected_colleges)]
    filtered_df = filtered_df[
        (filtered_df["Closing Rank"] >= rank_range[0]) &
        (filtered_df["Closing Rank"] <= rank_range[1])
    ]
    
    if gender:
        filtered_df = filtered_df[filtered_df["Gender"].isin(gender)]
    if seat_type:
        filtered_df = filtered_df[filtered_df["Seat Type"].isin(seat_type)]
    if quota:
        filtered_df = filtered_df[filtered_df["Quota"].isin(quota)]
    
    # Program filtering logic
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
    display_df = filtered_df.copy()
    if "Closing Rank" in display_df.columns:
        display_df["Closing Rank"] = display_df["Closing Rank"].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "")
    if "Opening Rank" in display_df.columns:
        display_df["Opening Rank"] = display_df["Opening Rank"].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "")
    
    # Display results
    st.subheader("🎯 Matching Programs")
    if len(filtered_df) == 0:
        st.warning("No results found. Try adjusting your filters.")
        return
    
    # Full table display
    st.write(f"Found **{len(filtered_df)}** matching programs:")
    st.dataframe(display_df, use_container_width=True, height=400)
    
    # Individual rows with shortlist buttons
    st.markdown("### Add to Shortlist")
    for idx, row in filtered_df.iterrows():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{row['Institute']}** - {row['Academic Program Name']}")
            st.markdown(f"Closing Rank: {row['Closing Rank']:,} | Seat Type: {row['Seat Type']} | Quota: {row['Quota']} | Gender: {row['Gender']}")
        with col2:
            if st.button(f"⭐ Add to Shortlist", key=f"shortlist_{idx}"):
                success, message = add_to_shortlist(
                    st.session_state.user_id,
                    row['Institute'],
                    row['Academic Program Name'],
                    row['Closing Rank'],
                    row['Seat Type'],
                    row['Quota'],
                    row['Gender']
                )
                if success:
                    st.success(message)
                else:
                    st.warning(message)
                st.rerun()
        st.markdown("---")
    
    # Download search results as CSV
    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Search Results as CSV",
        data=csv,
        file_name="jee_search_results.csv",
        mime="text/csv",
        help="Download your filtered search results."
    )
    
    # Feedback Section
    st.markdown("---")
    st.subheader("📝 Submit Your Feedback")
    feedback = st.text_area("Please provide your feedback or suggestions about the app:")
    
    if st.button("Submit Feedback"):
        if feedback.strip():
            try:
                with open("feedback.txt", "a") as f:
                    f.write(f"User: {st.session_state.username}\n")
                    f.write(f"Feedback: {feedback}\n")
                    f.write(f"Timestamp: {pd.Timestamp.now()}\n")
                    f.write("---\n")
                st.success("Thank you for your feedback!")
            except Exception as e:
                st.success("Thank you for your feedback!")
        else:
            st.warning("Please enter some feedback before submitting.")

def admin_page():
    """Admin panel for adding new seat records"""
    st.subheader("🔒 Admin Panel")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    # SHA-256 hash for password
    ADMIN_HASH = "c7282ea501f7b9491be0a7e2409293f4ee823d9f7247d986695a975f894259ce"
    
    if st.button("Login"):
        if username == "admin" and sha256(password.encode('utf-8')).hexdigest() == ADMIN_HASH:
            st.success("Logged in successfully!")
            st.markdown("---")
            st.subheader("➕ Add New Seat Record")
            
            df = get_jee_data()
            existing_institutes = sorted(df["Institute"].dropna().unique())
            existing_locations = sorted(df["Location"].dropna().unique()) if "Location" in df.columns else []
            existing_programs = sorted(df["Academic Program Name"].dropna().unique())
            
            with st.form("data_entry_form"):
                institute = st.selectbox("Institute", options=[""] + existing_institutes)
                location = st.selectbox("Location", options=[""] + existing_locations) if existing_locations else st.text_input("Location")
                inst_type = st.selectbox("Type", ["IIT", "NIT", "IIIT", "GFTI"])
                program = st.selectbox("Academic Program Name", options=[""] + existing_programs)
                quota = st.selectbox("Quota", ["AI", "HS", "OS"])
                seat_type = st.text_input("Seat Type")
                gender = st.selectbox("Gender", ["Gender-Neutral", "Female-only (including Supernumerary)"])
                opening = st.number_input("Opening Rank", min_value=0, step=1)
                closing = st.number_input("Closing Rank", min_value=0, step=1)
                year = st.selectbox("Year", [2021, 2022, 2023, 2024, 2025])
                
                submitted = st.form_submit_button("Add Record")
                if submitted:
                    conn = get_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute("""
                            INSERT INTO jee_seats (Institute, Location, Type, `Academic Program Name`, Quota, `Seat Type`, Gender, `Opening Rank`, `Closing Rank`, Year)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (institute, location, inst_type, program, quota, seat_type, gender, opening, closing, year))
                        conn.commit()
                        st.success("✅ Record added successfully!")
                    except Exception as e:
                        st.error(f"Error adding record: {e}")
                    finally:
                        conn.close()
        else:
            st.error("Invalid credentials.")

def main_app():
    """Main application after login"""
    # Header with user info and logout
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(f"🎓 JEE Seat Finder - Welcome, {st.session_state.username}!")
    with col2:
        if st.button("🚪 Logout"):
            logout()
    
    # Navigation
    if st.session_state.username == "admin":
        page = st.sidebar.selectbox("Navigate", ["🔍 Search Seats", "⭐ My Shortlist", "🔑 Admin Panel"])
    else:
        page = st.sidebar.selectbox("Navigate", ["🔍 Search Seats", "⭐ My Shortlist"])
    
    if page == "🔍 Search Seats":
        logged_in_search_page()
    elif page == "⭐ My Shortlist":
        shortlist_page()
    elif page == "🔑 Admin Panel":
        admin_page()

# Footer
def show_footer():
    st.markdown(
        "<hr style='margin-top:2em;margin-bottom:1em;'>"
        "<div style='text-align:center; color: #999;'>"
        "Made with ❤️ using Streamlit · Designed for mobile and desktop"
        "</div>",
        unsafe_allow_html=True
    )

# Initialize session state for login modal
if 'show_login' not in st.session_state:
    st.session_state.show_login = False

# --- MAIN APP LOGIC ---
if st.session_state.show_login and not st.session_state.logged_in:
    login_page()
    if st.button("🔙 Back to Search"):
        st.session_state.show_login = False
        st.rerun()
elif st.session_state.logged_in:
    main_app()
else:
    guest_search_page()

show_footer()
