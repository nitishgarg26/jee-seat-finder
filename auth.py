import sqlite3
import streamlit as st
from database import get_connection, hash_password

def create_user(username, email, password):
    """Create a new user account"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Username or email already exists!"
    finally:
        conn.close()

def authenticate_user(username, password):
    """Authenticate user login"""
    conn = get_connection()
    cursor = conn.cursor()
    password_hash = hash_password(password)
    cursor.execute(
        "SELECT id, username FROM users WHERE username = ? AND password_hash = ?",
        (username, password_hash)
    )
    user = cursor.fetchone()
    conn.close()
    return user

def initialize_session():
    """Initialize session state variables"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None

def login_page():
    """Display login/signup page"""
    st.title("🔐 Login to JEE Seat Finder")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            user = authenticate_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_id = user[0]
                st.session_state.username = user[1]
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password!")
    
    with tab2:
        st.subheader("Create Account")
        new_username = st.text_input("Username", key="signup_username")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        
        if st.button("Sign Up"):
            if new_password != confirm_password:
                st.error("Passwords don't match!")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters!")
            else:
                success, message = create_user(new_username, new_email, new_password)
                if success:
                    st.success(message)
                else:
                    st.error(message)

def logout():
    """Handle user logout"""
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.rerun()
