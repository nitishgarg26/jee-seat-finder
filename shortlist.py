import pandas as pd
import streamlit as st
from database import get_connection

def add_to_shortlist(user_id, institute, program, closing_rank, seat_type, quota, gender, notes=""):
    """Add item to user's shortlist"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if already in shortlist
    cursor.execute("""
        SELECT id FROM shortlists 
        WHERE user_id = ? AND institute = ? AND program = ? AND seat_type = ? AND quota = ? AND gender = ?
    """, (user_id, institute, program, seat_type, quota, gender))
    
    if cursor.fetchone():
        conn.close()
        return False, "This option is already in your shortlist!"
    
    cursor.execute("""
        INSERT INTO shortlists (user_id, institute, program, closing_rank, seat_type, quota, gender, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, institute, program, closing_rank, seat_type, quota, gender, notes))
    conn.commit()
    conn.close()
    return True, "Added to shortlist successfully!"

def get_user_shortlist(user_id):
    """Get user's shortlist"""
    conn = get_connection()
    query = """
        SELECT id, institute, program, closing_rank, seat_type, quota, gender, notes, added_at
        FROM shortlists WHERE user_id = ? ORDER BY added_at DESC
    """
    df = pd.read_sql_query(query, conn, params=(user_id,))
    conn.close()
    return df

def remove_from_shortlist(shortlist_id):
    """Remove item from shortlist"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shortlists WHERE id = ?", (shortlist_id,))
    conn.commit()
    conn.close()

def update_shortlist_notes(shortlist_id, notes):
    """Update notes for a shortlist item"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE shortlists SET notes = ? WHERE id = ?", (notes, shortlist_id))
    conn.commit()
    conn.close()

def shortlist_page():
    """Display shortlist management page"""
    st.subheader("⭐ My Shortlist")
    
    shortlist_df = get_user_shortlist(st.session_state.user_id)
    
    if len(shortlist_df) == 0:
        st.info("Your shortlist is empty. Go to the search page to add some options!")
        return
    
    st.write(f"You have **{len(shortlist_df)}** items in your shortlist.")
    
    for idx, row in shortlist_df.iterrows():
        with st.expander(f"{row['institute']} - {row['program']}", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Institute:** {row['institute']}")
                st.markdown(f"**Program:** {row['program']}")
                st.markdown(f"**Closing Rank:** {row['closing_rank']:,}")
                st.markdown(f"**Seat Type:** {row['seat_type']}")
                st.markdown(f"**Quota:** {row['quota']}")
                st.markdown(f"**Gender:** {row['gender']}")
                st.markdown(f"**Added:** {row['added_at']}")
                
                # Notes section
                new_notes = st.text_area(f"Notes", value=row['notes'] or '', key=f"notes_{row['id']}")
                if st.button(f"💾 Update Notes", key=f"update_{row['id']}"):
                    update_shortlist_notes(row['id'], new_notes)
                    st.success("Notes updated!")
                    st.rerun()
            
            with col2:
                if st.button(f"🗑️ Remove", key=f"remove_{row['id']}"):
                    remove_from_shortlist(row['id'])
                    st.success("Removed from shortlist!")
                    st.rerun()
    
    # Download shortlist as CSV
    if st.button("📥 Download Shortlist as CSV"):
        csv = shortlist_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"jee_shortlist_{st.session_state.username}.csv",
            mime="text/csv"
        )
