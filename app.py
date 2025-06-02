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

# Enhanced CSS for dark theme compatibility and better styling
st.markdown("""
    <style>
    /* Dark and Light mode compatibility */
    .block-container {
        max-width: 100vw !important;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    
    /* Dark mode styles */
    @media (prefers-color-scheme: dark) {
        .block-container {
            background-color: #0e1117 !important;
            color: #fafafa !important;
        }
        
        section[data-testid="stSidebar"] {
            background-color: #1e1e1e !important;
            color: #fafafa !important;
            border-right: 1px solid #333 !important;
        }
        
        .main h1, .main h2 {
            color: #ff6b6b !important;
        }
        
        .stAlert > div {
            background-color: #262730 !important;
            color: #fafafa !important;
            border-left: 4px solid #ff6b6b !important;
        }
        
        .stDataFrame {
            background-color: #1e1e1e !important;
        }
        
        .login-prompt {
            background-color: #262730 !important;
            color: #fafafa !important;
            border-left: 4px solid #ff6b6b !important;
        }
    }
    
    /* Light mode styles */
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
    
    /* Responsive design */
    @media (max-width: 600px) {
        .main h1 { font-size: 2rem !important; }
        .main h2 { font-size: 1.5rem !important; }
    }
    
    /* Shortlist button styling */
    .shortlist-btn {
        background-color: #4caf50 !important;
        color: white !important;
        border: none !important;
        padding: 0.25rem 0.5rem !important;
        border-radius: 4px !important;
        font-size: 0.8rem !important;
    }
    
    .shortlist-btn:hover {
        background-color: #45a049 !important;
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
    
    gender = st.multiselect("⚧️ Gender", options=sorted(df["Gender"].dropna().unique()), default="Gender-Neutral")
    quota = st.multiselect("🎟️ Quota", options=sorted(df["Quota"].dropna().unique()),default="AI")
    seat_type = st.multiselect("💺 Seat Type", options=sorted(df["Seat Type"].dropna().unique()), default=["OPEN"])
    
    rank_range = (min_rank, max_rank)
    return selected_types, selected_colleges, program_group, rank_range, gender, quota, seat_type, filtered_df_for_programs

def apply_filters(df, selected_types, selected_colleges, program_group, rank_range, gender, quota, seat_type, filtered_df_for_programs):
    """Apply all filters to the dataframe"""
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
    
    return filtered_df.sort_values(by="Closing Rank")

def format_dataframe_for_display(df):
    """Format dataframe with commas in ranks"""
    display_df = df.copy()
    if "Closing Rank" in display_df.columns:
        display_df["Closing Rank"] = display_df["Closing Rank"].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "")
    if "Opening Rank" in display_df.columns:
        display_df["Opening Rank"] = display_df["Opening Rank"].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "")
    return display_df

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
    
    # Get data and apply filters
    df = get_jee_data()
    
    # Responsive filter placement
    if is_mobile:
        st.markdown("### 🔍 Filters")
        selected_types, selected_colleges, program_group, rank_range, gender, quota, seat_type, filtered_df_for_programs = filter_widgets()
    else:
        with st.sidebar:
            st.header("🔍 Filters")
            selected_types, selected_colleges, program_group, rank_range, gender, quota, seat_type, filtered_df_for_programs = filter_widgets()
    
    # Apply filters and format
    filtered_df = apply_filters(df, selected_types, selected_colleges, program_group, rank_range, gender, quota, seat_type, filtered_df_for_programs)
    display_df = format_dataframe_for_display(filtered_df)
    
    # Display results
    st.subheader("🎯 Matching Programs")
    if len(filtered_df) == 0:
        st.warning("No results found. Try adjusting your filters.")
        return
    
    # Add login prompt column to display dataframe
    display_with_action = display_df.copy()
    display_with_action['🔐 Save Option'] = ['Login to Save' for _ in range(len(display_with_action))]
    
    st.write(f"Found **{len(filtered_df)}** matching programs:")
    st.info("💡 **Login to save your favorite options to a personal shortlist!**")
    st.dataframe(display_with_action, use_container_width=True, height=400)
    
    # Download and feedback sections
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
    """Search functionality for logged-in users with table display and checkbox shortlisting"""
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
    
    # Get data and apply filters
    df = get_jee_data()
    
    # Responsive filter placement
    if is_mobile:
        st.markdown("### 🔍 Filters")
        selected_types, selected_colleges, program_group, rank_range, gender, quota, seat_type, filtered_df_for_programs = filter_widgets()
    else:
        with st.sidebar:
            st.header("🔍 Filters")
            selected_types, selected_colleges, program_group, rank_range, gender, quota, seat_type, filtered_df_for_programs = filter_widgets()
    
    # Apply filters and format
    filtered_df = apply_filters(df, selected_types, selected_colleges, program_group, rank_range, gender, quota, seat_type, filtered_df_for_programs)
    
    # Reset index to ensure proper indexing for selection
    filtered_df = filtered_df.reset_index(drop=True)
    display_df = format_dataframe_for_display(filtered_df)
    
    # Display results
    st.subheader("🎯 Matching Programs")
    if len(filtered_df) == 0:
        st.warning("No results found. Try adjusting your filters.")
        return
    
    st.write(f"Found **{len(filtered_df)}** matching programs:")
    
    # Initialize session state for selected items - only if not exists
    if 'selected_items' not in st.session_state:
        st.session_state.selected_items = set()
    
    # Shortlist controls
    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        select_all = st.checkbox("Select All")
        if select_all:
            st.session_state.selected_items = set(range(len(filtered_df)))
        elif not select_all and len(st.session_state.selected_items) == len(filtered_df):
            st.session_state.selected_items = set()
    
    with col2:
        st.write(f"Selected: {len(st.session_state.selected_items)}")
    
    with col3:
        if st.button("⭐ Add Selected to Shortlist", disabled=len(st.session_state.selected_items) == 0):
            success_count = 0
            error_count = 0
            
            # Process selected items safely
            for idx in st.session_state.selected_items:
                try:
                    # Ensure index is within bounds
                    if 0 <= idx < len(filtered_df):
                        row = filtered_df.iloc[idx]
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
                            success_count += 1
                        else:
                            error_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    st.error(f"Error adding item: {e}")
                    error_count += 1
            
            if success_count > 0:
                st.success(f"✅ Added {success_count} items to shortlist!")
            if error_count > 0:
                st.warning(f"⚠️ {error_count} items could not be added.")
            
            # Clear selections after adding
            st.session_state.selected_items = set()
            st.rerun()
    
    # Create the enhanced dataframe with selection checkboxes
    enhanced_df = display_df.copy()
    enhanced_df.insert(0, 'Select', False)
    
    # Set previously selected items to True
    for idx in st.session_state.selected_items:
        if idx < len(enhanced_df):
            enhanced_df.loc[idx, 'Select'] = True
    
    # Display the main results table with checkboxes
    edited_df = st.data_editor(
        enhanced_df,
        column_config={
            "Select": st.column_config.CheckboxColumn(
                "Select",
                help="Select rows to add to shortlist",
                default=False,
            ),
            "Institute": st.column_config.TextColumn(
                "Institute",
                width="medium",
            ),
            "Academic Program Name": st.column_config.TextColumn(
                "Program",
                width="large",
            ),
            "Closing Rank": st.column_config.TextColumn(
                "Closing Rank",
                width="small",
            ),
            "Opening Rank": st.column_config.TextColumn(
                "Opening Rank",
                width="small",
            ),
            "Seat Type": st.column_config.TextColumn(
                "Seat Type",
                width="small",
            ),
            "Quota": st.column_config.TextColumn(
                "Quota",
                width="small",
            ),
            "Gender": st.column_config.TextColumn(
                "Gender",
                width="medium",
            ),
        },
        disabled=["Institute", "Academic Program Name", "Type", "Closing Rank", "Opening Rank", "Seat Type", "Quota", "Gender", "Year"],
        hide_index=True,
        use_container_width=True,
        height=400,
        key="results_table"
    )
    
    # Update selected items based on table selections
    if edited_df is not None:
        selected_indices = edited_df.index[edited_df['Select'] == True].tolist()
        st.session_state.selected_items = set(selected_indices)
    
    # Add selected items to shortlist button (alternative placement)
    if len(st.session_state.selected_items) > 0:
        st.info(f"💡 {len(st.session_state.selected_items)} items selected. Click 'Add Selected to Shortlist' above to save them.")
    
    # Download search results as CSV
    st.markdown("---")
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

# Initialize session state for login modal and selections
if 'show_login' not in st.session_state:
    st.session_state.show_login = False
if 'selected_items' not in st.session_state:
    st.session_state.selected_items = []

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
