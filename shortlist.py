# Complete shortlist.py content for JEE Seat Finder app

import pandas as pd
import streamlit as st
from database import get_connection


def add_to_shortlist(user_id, institute, program, closing_rank, seat_type, quota, gender, notes=""):
    """Add item to user's shortlist with automatic priority assignment"""
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
    
    # Get the next priority number (highest priority + 1)
    cursor.execute("SELECT MAX(priority_order) FROM shortlists WHERE user_id = ?", (user_id,))
    max_priority = cursor.fetchone()[0]
    next_priority = (max_priority or 0) + 1
    
    cursor.execute("""
        INSERT INTO shortlists (user_id, institute, program, closing_rank, seat_type, quota, gender, notes, priority_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, institute, program, closing_rank, seat_type, quota, gender, notes, next_priority))
    conn.commit()
    conn.close()
    return True, "Added to shortlist successfully!"


def get_user_shortlist(user_id):
    """Get user's shortlist ordered by priority"""
    conn = get_connection()
    query = """
        SELECT id, institute, program, closing_rank, seat_type, quota, gender, notes, added_at, 
               COALESCE(priority_order, id) as priority_order
        FROM shortlists 
        WHERE user_id = ? 
        ORDER BY COALESCE(priority_order, id) ASC
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


def update_priority_order(user_id, item_id, new_priority):
    """Update priority order for a specific item"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get current priority
    cursor.execute("SELECT priority_order FROM shortlists WHERE id = ? AND user_id = ?", (item_id, user_id))
    current_priority = cursor.fetchone()
    
    if not current_priority:
        conn.close()
        return False, "Item not found!"
    
    current_priority = current_priority[0]
    
    # Update the target item's priority
    cursor.execute("UPDATE shortlists SET priority_order = ? WHERE id = ? AND user_id = ?", 
                   (new_priority, item_id, user_id))
    
    # Shift other items if necessary
    if new_priority < current_priority:
        # Moving up - shift items down
        cursor.execute("""
            UPDATE shortlists 
            SET priority_order = priority_order + 1 
            WHERE user_id = ? AND priority_order >= ? AND priority_order < ? AND id != ?
        """, (user_id, new_priority, current_priority, item_id))
    elif new_priority > current_priority:
        # Moving down - shift items up
        cursor.execute("""
            UPDATE shortlists 
            SET priority_order = priority_order - 1 
            WHERE user_id = ? AND priority_order > ? AND priority_order <= ? AND id != ?
        """, (user_id, current_priority, new_priority, item_id))
    
    conn.commit()
    conn.close()
    return True, "Priority updated successfully!"


def move_item_up(user_id, item_id):
    """Move item up in priority (decrease priority number)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get current item priority
    cursor.execute("SELECT priority_order FROM shortlists WHERE id = ? AND user_id = ?", (item_id, user_id))
    current_priority = cursor.fetchone()
    
    if not current_priority or current_priority[0] <= 1:
        conn.close()
        return False, "Item is already at the top!"
    
    current_priority = current_priority[0]
    
    # Find the item immediately above (lower priority number)
    cursor.execute("""
        SELECT id, priority_order FROM shortlists 
        WHERE user_id = ? AND priority_order < ? 
        ORDER BY priority_order DESC LIMIT 1
    """, (user_id, current_priority))
    
    above_item = cursor.fetchone()
    if not above_item:
        conn.close()
        return False, "No item above to swap with!"
    
    above_id, above_priority = above_item
    
    # Swap priorities
    cursor.execute("UPDATE shortlists SET priority_order = ? WHERE id = ?", (above_priority, item_id))
    cursor.execute("UPDATE shortlists SET priority_order = ? WHERE id = ?", (current_priority, above_id))
    
    conn.commit()
    conn.close()
    return True, "Item moved up!"


def move_item_down(user_id, item_id):
    """Move item down in priority (increase priority number)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get current item priority
    cursor.execute("SELECT priority_order FROM shortlists WHERE id = ? AND user_id = ?", (item_id, user_id))
    current_priority = cursor.fetchone()
    
    if not current_priority:
        conn.close()
        return False, "Item not found!"
    
    current_priority = current_priority[0]
    
    # Find the item immediately below (higher priority number)
    cursor.execute("""
        SELECT id, priority_order FROM shortlists 
        WHERE user_id = ? AND priority_order > ? 
        ORDER BY priority_order ASC LIMIT 1
    """, (user_id, current_priority))
    
    below_item = cursor.fetchone()
    if not below_item:
        conn.close()
        return False, "Item is already at the bottom!"
    
    below_id, below_priority = below_item
    
    # Swap priorities
    cursor.execute("UPDATE shortlists SET priority_order = ? WHERE id = ?", (below_priority, item_id))
    cursor.execute("UPDATE shortlists SET priority_order = ? WHERE id = ?", (current_priority, below_id))
    
    conn.commit()
    conn.close()
    return True, "Item moved down!"


def reorder_all_priorities(user_id):
    """Reorder all priorities to be sequential (1, 2, 3, ...)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all items ordered by current priority
    cursor.execute("""
        SELECT id FROM shortlists 
        WHERE user_id = ? 
        ORDER BY COALESCE(priority_order, id) ASC
    """, (user_id,))
    
    items = cursor.fetchall()
    
    # Update priorities to be sequential
    for index, (item_id,) in enumerate(items, 1):
        cursor.execute("UPDATE shortlists SET priority_order = ? WHERE id = ?", (index, item_id))
    
    conn.commit()
    conn.close()


def shortlist_page():
    """Display shortlist management page with tabular format and priority controls"""
    st.subheader("⭐ My Shortlist")
    
    shortlist_df = get_user_shortlist(st.session_state.user_id)
    
    if len(shortlist_df) == 0:
        st.info("Your shortlist is empty. Go to the search page to add some options!")
        return
    
    st.write(f"You have **{len(shortlist_df)}** items in your shortlist.")
    
    # Reorder priorities button
    if st.button("🔄 Reorder Priorities", help="Reset priority numbers to be sequential"):
        reorder_all_priorities(st.session_state.user_id)
        st.success("Priorities reordered!")
        st.rerun()
    
    # Format dataframe for display
    display_df = shortlist_df.copy()
    if "closing_rank" in display_df.columns:
        display_df["closing_rank"] = display_df["closing_rank"].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "")
    
    # Rename columns for better display
    display_df = display_df.rename(columns={
        'priority_order': 'Priority',
        'institute': 'Institute',
        'program': 'Program',
        'closing_rank': 'Closing Rank',
        'seat_type': 'Seat Type',
        'quota': 'Quota',
        'gender': 'Gender',
        'notes': 'Notes'
    })
    
    # Select columns for main table display
    table_columns = ['Priority', 'Institute', 'Program', 'Closing Rank', 'Seat Type', 'Quota', 'Gender', 'Notes']
    
    # Display main table
    st.subheader("📊 Shortlist Table")
    st.dataframe(
        display_df[table_columns], 
        use_container_width=True, 
        height=300,
        hide_index=True
    )
    
    # Individual item controls
    st.subheader("🎛️ Priority Controls & Actions")
    
    for idx, row in shortlist_df.iterrows():
        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([0.5, 3, 1, 0.8, 0.8, 0.8])
            
            with col1:
                st.markdown(f"**#{int(row['priority_order'])}**")
            
            with col2:
                st.markdown(f"**{row['institute']}** - {row['program']}")
                st.caption(f"Rank: {row['closing_rank']:,} | {row['seat_type']} | {row['quota']} | {row['gender']}")
            
            with col3:
                # Notes editing
                new_notes = st.text_input(
                    "Notes", 
                    value=row['notes'] or '', 
                    key=f"notes_{row['id']}",
                    label_visibility="collapsed"
                )
                if new_notes != (row['notes'] or ''):
                    if st.button("💾", key=f"save_notes_{row['id']}", help="Save notes"):
                        update_shortlist_notes(row['id'], new_notes)
                        st.success("Notes saved!")
                        st.rerun()
            
            with col4:
                # Move up button
                if st.button("⬆️", key=f"up_{row['id']}", help="Move up in priority"):
                    success, message = move_item_up(st.session_state.user_id, row['id'])
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.warning(message)
            
            with col5:
                # Move down button
                if st.button("⬇️", key=f"down_{row['id']}", help="Move down in priority"):
                    success, message = move_item_down(st.session_state.user_id, row['id'])
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.warning(message)
            
            with col6:
                # Remove button
                if st.button("🗑️", key=f"remove_{row['id']}", help="Remove from shortlist"):
                    remove_from_shortlist(row['id'])
                    st.success("Removed from shortlist!")
                    st.rerun()
            
            st.markdown("---")
    
    # Bulk actions
    st.subheader("📥 Export & Download")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Download shortlist as CSV
        csv = shortlist_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Shortlist as CSV",
            data=csv,
            file_name=f"jee_shortlist_{st.session_state.username}.csv",
            mime="text/csv",
            help="Download your complete shortlist"
        )
    
    with col2:
        # Download formatted shortlist
        formatted_df = display_df.copy()
        formatted_csv = formatted_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📊 Download Formatted Shortlist",
            data=formatted_csv,
            file_name=f"jee_shortlist_formatted_{st.session_state.username}.csv",
            mime="text/csv",
            help="Download formatted shortlist with proper column names"
        )
    
    # Clear all shortlist option
    st.markdown("---")
    if st.button("🗑️ Clear All Shortlist", help="Remove all items from shortlist"):
        if st.button("⚠️ Confirm Clear All", key="confirm_clear"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM shortlists WHERE user_id = ?", (st.session_state.user_id,))
            conn.commit()
            conn.close()
            st.success("All items cleared from shortlist!")
            st.rerun()


def get_shortlist_summary(user_id):
    """Get summary statistics of user's shortlist"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Total items
        cursor.execute("SELECT COUNT(*) FROM shortlists WHERE user_id = ?", (user_id,))
        total_items = cursor.fetchone()[0]
        
        # Items by college type
        cursor.execute("""
            SELECT s.institute, COUNT(*) as count
            FROM shortlists s
            WHERE s.user_id = ?
            GROUP BY s.institute
            ORDER BY count DESC
        """, (user_id,))
        by_institute = cursor.fetchall()
        
        # Items by seat type
        cursor.execute("""
            SELECT seat_type, COUNT(*) as count
            FROM shortlists
            WHERE user_id = ?
            GROUP BY seat_type
            ORDER BY count DESC
        """, (user_id,))
        by_seat_type = cursor.fetchall()
        
        return {
            'total_items': total_items,
            'by_institute': by_institute,
            'by_seat_type': by_seat_type
        }
        
    except Exception as e:
        print(f"Error getting shortlist summary: {e}")
        return None
    finally:
        conn.close()


def display_shortlist_summary():
    """Display shortlist summary statistics"""
    summary = get_shortlist_summary(st.session_state.user_id)
    
    if summary and summary['total_items'] > 0:
        st.sidebar.subheader("📊 Shortlist Summary")
        st.sidebar.metric("Total Items", summary['total_items'])
        
        if summary['by_institute']:
            st.sidebar.write("**Top Institutes:**")
            for institute, count in summary['by_institute'][:3]:
                st.sidebar.write(f"• {institute}: {count}")
        
        if summary['by_seat_type']:
            st.sidebar.write("**By Seat Type:**")
            for seat_type, count in summary['by_seat_type']:
                st.sidebar.write(f"• {seat_type}: {count}")
