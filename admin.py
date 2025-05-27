import streamlit as st
import sqlite3
import pandas as pd

# Set up page
st.set_page_config(page_title="Admin - Add JEE Data", layout="centered")
st.title("🔒 Admin Panel: Add New Seat Data")

# --- Hardcoded login credentials (you can replace this with a secure method) ---
USERNAME = "admin"
PASSWORD = "admin123"

# --- Login Form ---
with st.sidebar:
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

# --- Authentication ---
if login_button:
    if username == USERNAME and password == PASSWORD:
        st.success("Logged in successfully!")

        # Connect to database
        conn = sqlite3.connect("jee_data.db")
        cursor = conn.cursor()

        st.subheader("📝 Add New Entry")

        # Input fields
        institute = st.text_input("Institute")
        location = st.text_input("Location")
        inst_type = st.selectbox("Type", ["IIT", "NIT", "IIIT", "GFTI"])
        program = st.text_input("Academic Program Name")
        quota = st.selectbox("Quota", ["AI", "HS", "OS"])
        seat_type = st.text_input("Seat Type")
        gender = st.selectbox("Gender", ["Gender-Neutral", "Female-only (including Supernumerary)"])
        opening = st.number_input("Opening Rank", min_value=0, step=1)
        closing = st.number_input("Closing Rank", min_value=0, step=1)
        year = st.selectbox("Year", [2021,2022, 2023, 2024])

        if st.button("➕ Add to Database"):
            cursor.execute("""
                INSERT INTO jee_seats (Institute, Location, Type, `Academic Program Name`, Quota, `Seat Type`, Gender, `Opening Rank`, `Closing Rank`, Year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (institute, location, inst_type, program, quota, seat_type, gender, opening, closing, year))
            conn.commit()
            st.success("✅ Record added successfully!")

    else:
        st.error("Invalid username or password")
