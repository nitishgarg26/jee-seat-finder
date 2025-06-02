# Complete database.py content for JEE Seat Finder app

import sqlite3
import pandas as pd
from hashlib import sha256
import os


def get_connection():
    """Get database connection with proper settings"""
    # Ensure database directory exists
    os.makedirs(os.path.dirname("jee_data.db") if os.path.dirname("jee_data.db") else ".", exist_ok=True)
    
    conn = sqlite3.connect("jee_data.db", check_same_thread=False)
    # Enable foreign keys and WAL mode for better concurrency
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def setup_user_tables():
    """Set up user and shortlist tables with proper constraints"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Users table with better constraints
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
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
                priority_order INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shortlists_user_id ON shortlists(user_id)")
        
        conn.commit()
        print("✅ User tables created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def hash_password(password):
    """Hash password using SHA256"""
    return sha256(password.encode('utf-8')).hexdigest()


def get_jee_data():
    """Get JEE seats data"""
    try:
        conn = get_connection()
        df = pd.read_sql_query("SELECT * FROM jee_seats", conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Error getting JEE data: {e}")
        # Return empty dataframe with expected columns if table doesn't exist
        return pd.DataFrame(columns=[
            'Institute', 'Academic Program Name', 'Type', 'Opening Rank', 
            'Closing Rank', 'Seat Type', 'Quota', 'Gender', 'Year'
        ])


def debug_database():
    """Debug function to check database state"""
    import streamlit as st
    
    # Check if database file exists
    db_exists = os.path.exists("jee_data.db")
    st.write(f"Database file exists: {db_exists}")
    
    if db_exists:
        # Check file size
        file_size = os.path.getsize("jee_data.db")
        st.write(f"Database file size: {file_size} bytes")
        
        # Check if users table exists and has data
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Check if users table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
            table_exists = cursor.fetchone()
            st.write(f"Users table exists: {table_exists is not None}")
            
            if table_exists:
                # Count users
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                st.write(f"Number of users in database: {user_count}")
                
                # Show all users (remove passwords for security)
                cursor.execute("SELECT id, username, email, created_at FROM users")
                users = cursor.fetchall()
                if users:
                    st.write("Users in database:")
                    for user in users:
                        st.write(f"- ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Created: {user[3]}")
                else:
                    st.write("No users found in database")
            
            # Check if jee_seats table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jee_seats';")
            jee_table_exists = cursor.fetchone()
            st.write(f"JEE seats table exists: {jee_table_exists is not None}")
            
            if jee_table_exists:
                cursor.execute("SELECT COUNT(*) FROM jee_seats")
                jee_count = cursor.fetchone()[0]
                st.write(f"Number of JEE seat records: {jee_count}")
            
            # Check if shortlists table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shortlists';")
            shortlist_table_exists = cursor.fetchone()
            st.write(f"Shortlists table exists: {shortlist_table_exists is not None}")
            
            if shortlist_table_exists:
                cursor.execute("SELECT COUNT(*) FROM shortlists")
                shortlist_count = cursor.fetchone()[0]
                st.write(f"Number of shortlist items: {shortlist_count}")
            
            conn.close()
            
        except Exception as e:
            st.error(f"Error checking database: {e}")
    else:
        st.warning("Database file does not exist. It will be created when you first use the app.")


def check_write_permissions():
    """Check if we can write to the database directory"""
    try:
        test_file = "test_write.tmp"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        return True, "Write permissions OK"
    except Exception as e:
        return False, f"Write permission error: {e}"


def create_sample_jee_data():
    """Create sample JEE data if table is empty (for testing)"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if jee_seats table exists and is empty
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jee_seats';")
        if not cursor.fetchone():
            # Create jee_seats table
            cursor.execute("""
                CREATE TABLE jee_seats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Institute TEXT,
                    Location TEXT,
                    Type TEXT,
                    "Academic Program Name" TEXT,
                    Quota TEXT,
                    "Seat Type" TEXT,
                    Gender TEXT,
                    "Opening Rank" INTEGER,
                    "Closing Rank" INTEGER,
                    Year INTEGER
                )
            """)
            
            # Insert sample data
            sample_data = [
                ("IIT Delhi", "Delhi", "IIT", "Computer Science and Engineering", "AI", "OPEN", "Gender-Neutral", 1, 100, 2024),
                ("IIT Bombay", "Mumbai", "IIT", "Electrical Engineering", "AI", "OPEN", "Gender-Neutral", 101, 500, 2024),
                ("NIT Trichy", "Trichy", "NIT", "Mechanical Engineering", "HS", "OPEN", "Gender-Neutral", 501, 1000, 2024),
                ("IIIT Hyderabad", "Hyderabad", "IIIT", "Computer Science and Engineering", "AI", "OPEN", "Gender-Neutral", 1001, 2000, 2024),
            ]
            
            cursor.executemany("""
                INSERT INTO jee_seats (Institute, Location, Type, "Academic Program Name", Quota, "Seat Type", 
                                     Gender, "Opening Rank", "Closing Rank", Year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_data)
            
            conn.commit()
            print("✅ Sample JEE data created!")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return False


def verify_database_integrity():
    """Verify database integrity and fix common issues"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check database integrity
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()[0]
        
        if integrity_result != "ok":
            print(f"⚠️ Database integrity issue: {integrity_result}")
            return False
        
        # Check foreign key constraints
        cursor.execute("PRAGMA foreign_key_check")
        fk_violations = cursor.fetchall()
        
        if fk_violations:
            print(f"⚠️ Foreign key violations found: {fk_violations}")
            return False
        
        conn.close()
        print("✅ Database integrity verified!")
        return True
        
    except Exception as e:
        print(f"❌ Error verifying database: {e}")
        return False


# Initialize database when module is imported
def initialize_database():
    """Initialize database with all required tables"""
    try:
        # Setup user tables
        if not setup_user_tables():
            return False
        
        # Create sample JEE data if needed
        create_sample_jee_data()
        
        # Verify database integrity
        verify_database_integrity()
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False


# Auto-initialize when imported
if __name__ != "__main__":
    initialize_database()
