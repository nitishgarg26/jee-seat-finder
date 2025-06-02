import sqlite3
import pandas as pd
from hashlib import sha256

def get_connection():
    """Get database connection"""
    return sqlite3.connect("jee_data.db", check_same_thread=False)

def setup_user_tables():
    """Set up user and shortlist tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Shortlists table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shortlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            institute TEXT NOT NULL,
            program TEXT NOT NULL,
            closing_rank INTEGER,
            seat_type TEXT,
            quota TEXT,
            gender TEXT,
            notes TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ User tables created successfully!")

def get_jee_data():
    """Get JEE seats data"""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM jee_seats", conn)
    conn.close()
    return df

def hash_password(password):
    """Hash password using SHA256"""
    return sha256(password.encode()).hexdigest()
