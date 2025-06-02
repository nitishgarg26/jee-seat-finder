# Complete auth.py content for JEE Seat Finder app

import sqlite3
import streamlit as st
import time
import pandas as pd
from database import get_connection, hash_password


def initialize_session():
    """Initialize session state variables properly"""
    # Core login states
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    # Additional states for UI
    if 'show_login' not in st.session_state:
        st.session_state.show_login = False
    if 'selected_items' not in st.session_state:
        st.session_state.selected_items = set()
    
    # Login attempt tracking
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0
    
    # Form states
    if 'signup_success' not in st.session_state:
        st.session_state.signup_success = False


def create_user(username, email, password):
    """Create a new user account with proper error handling"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Validate inputs
        username = username.strip()
        email = email.strip().lower()
        
        if not username or not email or not password:
            return False, "All fields are required!"
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters long!"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters long!"
        
        if "@" not in email or "." not in email:
            return False, "Please enter a valid email address!"
        
        # Hash the password
        password_hash = hash_password(password)
        
        # Check if username or email already exists
        cursor.execute(
            "SELECT username, email FROM users WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)",
            (username, email)
        )
        existing_user = cursor.fetchone()
        
        if existing_user:
            if existing_user[0].lower() == username.lower():
                return False, "Username already exists! Please choose a different username."
            else:
                return False, "Email already exists! Please use a different email."
        
        # Insert user with explicit commit
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        
        # Commit the transaction
        conn.commit()
        
        # Verify the user was actually created
        cursor.execute(
            "SELECT id, username FROM users WHERE LOWER(username) = LOWER(?) AND LOWER(email) = LOWER(?)",
            (username, email)
        )
        created_user = cursor.fetchone()
        
        if created_user:
            return True, f"Account created successfully for {username}!"
        else:
            return False, "Account creation failed - user not found after insert"
            
    except sqlite3.IntegrityError as e:
        if "username" in str(e).lower():
            return False, "Username already exists! Please choose a different username."
        elif "email" in str(e).lower():
            return False, "Email already exists! Please use a different email."
        else:
            return False, f"Account creation failed: {str(e)}"
    except Exception as e:
        return False, f"Database error: {str(e)}"
    finally:
        if conn:
            conn.close()


def authenticate_user(username, password):
    """Authenticate user login with proper error handling"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        password_hash = hash_password(password)
        
        # Search case-insensitive
        cursor.execute(
            "SELECT id, username, email FROM users WHERE LOWER(username) = LOWER(?) AND password_hash = ?",
            (username.strip(), password_hash)
        )
        user = cursor.fetchone()
        
        if user:
            # Update last login
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user[0],)
            )
            conn.commit()
            return True, user
        else:
            return False, None
            
    except Exception as e:
        print(f"Authentication error: {e}")
        return False, None
    finally:
        if conn:
            conn.close()


def login_page():
    """Display login/signup page with proper state management"""
    st.title("🔐 Login to JEE Seat Finder")
    
    # Show success message if just signed up
    if st.session_state.signup_success:
        st.success("🎉 Account created successfully! Please login below.")
        st.session_state.signup_success = False
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login to Your Account")
        
        # Show login attempts if any failures
        if st.session_state.login_attempts > 0:
            st.warning(f"Login attempts: {st.session_state.login_attempts}")
            if st.session_state.login_attempts >= 3:
                st.error("Too many failed attempts. Please check your credentials or create a new account.")
        
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if submitted:
                if username and password:
                    success, user = authenticate_user(username, password)
                    if success:
                        # Set session state
                        st.session_state.logged_in = True
                        st.session_state.user_id = user[0]
                        st.session_state.username = user[1]
                        st.session_state.login_attempts = 0
                        st.session_state.show_login = False
                        
                        st.success("✅ Logged in successfully!")
                        st.balloons()
                        # Brief pause to show success message
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.session_state.login_attempts += 1
                        st.error("❌ Invalid username or password!")
                        st.info("💡 If you're a new user, please sign up in the 'Sign Up' tab.")
                else:
                    st.warning("Please enter both username and password.")
        
        # Help section
        with st.expander("🆘 Need Help?"):
            st.markdown("""
            **Having trouble logging in?**
            - Make sure you're using the correct username and password
            - Username is case-insensitive
            - If you forgot your password, you'll need to create a new account
            - If you're a new user, use the 'Sign Up' tab above
            """)
    
    with tab2:
        st.subheader("Create New Account")
        
        with st.form("signup_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input(
                    "Username", 
                    placeholder="Choose a unique username",
                    help="Username must be at least 3 characters long"
                )
                new_password = st.text_input(
                    "Password", 
                    type="password", 
                    placeholder="Minimum 6 characters",
                    help="Password must be at least 6 characters long"
                )
            
            with col2:
                new_email = st.text_input(
                    "Email", 
                    placeholder="your.email@example.com",
                    help="Enter a valid email address"
                )
                confirm_password = st.text_input(
                    "Confirm Password", 
                    type="password", 
                    placeholder="Re-enter your password"
                )
            
            # Terms and conditions
            agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
            
            submitted = st.form_submit_button("🎉 Create Account", use_container_width=True)
            
            if submitted:
                # Validation
                if not all([new_username, new_email, new_password, confirm_password]):
                    st.error("❌ Please fill in all fields.")
                elif not agree_terms:
                    st.error("❌ Please agree to the Terms of Service.")
                elif new_password != confirm_password:
                    st.error("❌ Passwords don't match!")
                else:
                    success, message = create_user(new_username, new_email, new_password)
                    if success:
                        st.session_state.signup_success = True
                        st.success(f"✅ {message}")
                        st.info("🎉 Account created! Please switch to the 'Login' tab to sign in.")
                        # Auto-switch to login tab after a delay
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        # Additional info
        with st.expander("ℹ️ Why Create an Account?"):
            st.markdown("""
            **With an account, you can:**
            - 📌 Save your favorite colleges to a personal shortlist
            - 📝 Add notes to your shortlisted options
            - 📥 Download your shortlist for easy reference
            - 🔄 Access your data from any device
            - 🔒 Keep your preferences secure and private
            """)


def logout():
    """Handle user logout with proper cleanup"""
    # Clear all user-related session state
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.show_login = False
    st.session_state.selected_items = set()
    st.session_state.login_attempts = 0
    st.session_state.signup_success = False
    
    # Show logout message
    st.success("👋 You have been logged out successfully!")
    time.sleep(0.5)
    st.rerun()


def check_login_status():
    """Check and display current login status for debugging"""
    if st.sidebar.checkbox("🔍 Debug Login Status", help="Check current login state"):
        st.sidebar.write("**Current Session State:**")
        st.sidebar.write(f"- Logged in: {st.session_state.logged_in}")
        st.sidebar.write(f"- User ID: {st.session_state.user_id}")
        st.sidebar.write(f"- Username: {st.session_state.username}")
        st.sidebar.write(f"- Login attempts: {st.session_state.login_attempts}")
        st.sidebar.write(f"- Show login: {st.session_state.show_login}")
        
        if st.sidebar.button("🔄 Reset Session"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()


def get_user_info(user_id):
    """Get user information by user ID"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, username, email, created_at, last_login FROM users WHERE id = ?",
            (user_id,)
        )
        user = cursor.fetchone()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'created_at': user[3],
                'last_login': user[4]
            }
        return None
        
    except Exception as e:
        print(f"Error getting user info: {e}")
        return None
    finally:
        if conn:
            conn.close()


def update_user_profile(user_id, email=None, new_password=None):
    """Update user profile information"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if email:
            # Check if email already exists for another user
            cursor.execute(
                "SELECT id FROM users WHERE LOWER(email) = LOWER(?) AND id != ?",
                (email, user_id)
            )
            if cursor.fetchone():
                return False, "Email already exists for another user!"
            
            cursor.execute(
                "UPDATE users SET email = ? WHERE id = ?",
                (email.lower().strip(), user_id)
            )
        
        if new_password:
            password_hash = hash_password(new_password)
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (password_hash, user_id)
            )
        
        conn.commit()
        return True, "Profile updated successfully!"
        
    except Exception as e:
        return False, f"Error updating profile: {e}"
    finally:
        if conn:
            conn.close()


def delete_user_account(user_id, password):
    """Delete user account after password verification"""
    conn = None
    try:
        # First verify password
        user_info = get_user_info(user_id)
        if not user_info:
            return False, "User not found!"
        
        # Authenticate with password
        success, _ = authenticate_user(user_info['username'], password)
        if not success:
            return False, "Incorrect password!"
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Delete user (shortlists will be deleted automatically due to CASCADE)
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        
        return True, "Account deleted successfully!"
        
    except Exception as e:
        return False, f"Error deleting account: {e}"
    finally:
        if conn:
            conn.close()


def validate_session():
    """Validate current session and user existence"""
    if not st.session_state.logged_in or not st.session_state.user_id:
        return False
    
    # Check if user still exists in database
    user_info = get_user_info(st.session_state.user_id)
    if not user_info:
        # User was deleted, clear session
        logout()
        return False
    
    return True


# Debug function for testing
def debug_auth_functions():
    """Debug function to test authentication functions"""
    st.subheader("🔧 Auth Debug Functions")
    
    # Test user creation
    if st.button("Test User Creation"):
        success, message = create_user("debuguser", "debug@example.com", "debug123")
        st.write(f"Create user result: {success} - {message}")
    
    # Test authentication
    test_username = st.text_input("Test Username", value="debuguser")
    test_password = st.text_input("Test Password", value="debug123", type="password")
    
    if st.button("Test Authentication"):
        success, user = authenticate_user(test_username, test_password)
        st.write(f"Auth result: {success}")
        if user:
            st.write(f"User info: ID={user[0]}, Username={user[1]}, Email={user[2]}")
    
    # Show all users
    if st.button("Show All Users"):
        try:
            conn = get_connection()
            df = pd.read_sql_query("SELECT id, username, email, created_at, last_login FROM users", conn)
            conn.close()
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error: {e}")
