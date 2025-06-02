# Complete shortlist.py content with requested removals

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
    return True, "Moved up!"


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
    return True, "Moved down!"


def move_item_to_top(user_id, item_id):
    """Move item to top of the list"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get current priority
    cursor.execute("SELECT priority_order FROM shortlists WHERE id = ? AND user_id = ?", (item_id, user_id))
    current_priority = cursor.fetchone()
    
    if not current_priority or current_priority[0] <= 1:
        conn.close()
        return False, "Item is already at the top!"
    
    # Update all items with priority < current to priority + 1
    cursor.execute("""
        UPDATE shortlists 
        SET priority_order = priority_order + 1 
        WHERE user_id = ? AND priority_order < ?
    """, (user_id, current_priority[0]))
    
    # Set current item to priority 1
    cursor.execute("UPDATE shortlists SET priority_order = 1 WHERE id = ?", (item_id,))
    
    conn.commit()
    conn.close()
    return True, "Moved to top!"


def move_item_to_bottom(user_id, item_id):
    """Move item to bottom of the list"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get total items and current priority
    cursor.execute("SELECT COUNT(*) FROM shortlists WHERE user_id = ?", (user_id,))
    total_items = cursor.fetchone()[0]
    
    cursor.execute("SELECT priority_order FROM shortlists WHERE id = ? AND user_id = ?", (item_id, user_id))
    current_priority = cursor.fetchone()
    
    if not current_priority or current_priority[0] >= total_items:
        conn.close()
        return False, "Item is already at the bottom!"
    
    # Update all items with priority > current to priority - 1
    cursor.execute("""
        UPDATE shortlists 
        SET priority_order = priority_order - 1 
        WHERE user_id = ? AND priority_order > ?
    """, (user_id, current_priority[0]))
    
    # Set current item to last position
    cursor.execute("UPDATE shortlists SET priority_order = ? WHERE id = ?", (total_items, item_id))
    
    conn.commit()
    conn.close()
    return True, "Moved to bottom!"


def shortlist_page():
    """Display shortlist management page with streamlined controls"""
    st.subheader("⭐ My Shortlist")
    
    shortlist_df = get_user_shortlist(st.session_state.user_id)
    
    if len(shortlist_df) == 0:
        st.info("Your shortlist is empty. Go to the search page to add some options!")
        return
    
    st.write(f"You have **{len(shortlist_df)}** items in your shortlist.")
    st.info("💡 Use the control buttons to reorder items, edit notes, or remove items from your shortlist.")
    
    # Display shortlist in a clean table format with controls
    for idx, row in shortlist_df.iterrows():
        with st.container():
            # Create columns for layout
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.5, 2.5, 1.5, 0.6, 0.6, 0.6, 0.6, 0.8])
            
            with col1:
                # Show current position
                current_position = idx + 1
                st.markdown(f"**#{current_position}**")
            
            with col2:
                # Institute and program info
                st.markdown(f"**{row['institute']}**")
                st.caption(f"{row['program']}")
            
            with col3:
                # Details
                st.caption(f"**Rank:** {row['closing_rank']:,}")
                st.caption(f"**Type:** {row['seat_type']} | {row['quota']}")
                st.caption(f"**Gender:** {row['gender']}")
            
            with col4:
                # Move up button
                if st.button("⬆️", key=f"up_{row['id']}", help="Move up one position", disabled=(current_position == 1)):
                    success, message = move_item_up(st.session_state.user_id, row['id'])
                    if success:
                        st.rerun()
                    else:
                        st.warning(message)
            
            with col5:
                # Move down button
                if st.button("⬇️", key=f"down_{row['id']}", help="Move down one position", disabled=(current_position == len(shortlist_df))):
                    success, message = move_item_down(st.session_state.user_id, row['id'])
                    if success:
                        st.rerun()
                    else:
                        st.warning(message)
            
            with col6:
                # Move to top button
                if st.button("⏫", key=f"top_{row['id']}", help="Move to top", disabled=(current_position == 1)):
                    success, message = move_item_to_top(st.session_state.user_id, row['id'])
                    if success:
                        st.rerun()
                    else:
                        st.warning(message)
            
            with col7:
                # Move to bottom button
                if st.button("⏬", key=f"bottom_{row['id']}", help="Move to bottom", disabled=(current_position == len(shortlist_df))):
                    success, message = move_item_to_bottom(st.session_state.user_id, row['id'])
                    if success:
                        st.rerun()
                    else:
                        st.warning(message)
            
            with col8:
                # Remove button
                if st.button("🗑️", key=f"remove_{row['id']}", help="Remove from shortlist"):
                    remove_from_shortlist(row['id'])
                    st.success("Removed from shortlist!")
                    st.rerun()
            
            # Notes section (full width)
            notes_value = row['notes'] or ''
            new_notes = st.text_input(
                f"Notes for {row['institute']}", 
                value=notes_value,
                key=f"notes_{row['id']}",
                placeholder="Add your personal notes about this option...",
                label_visibility="collapsed"
            )
            
            # Auto-save notes when changed
            if new_notes != notes_value:
                update_shortlist_notes(row['id'], new_notes)
                st.success("Notes saved!")
                st.rerun()
            
            st.markdown("---")
    
    # Export options only
    st.markdown("---")
    st.subheader("📥 Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Download shortlist as CSV
        csv = shortlist_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"jee_shortlist_{st.session_state.username}.csv",
            mime="text/csv",
            help="Download your complete shortlist"
        )
    
    with col2:
        # Clear all option
        if st.button("🗑️ Clear All Shortlist"):
            if st.button("⚠️ Confirm Clear All", key="confirm_clear_all"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM shortlists WHERE user_id = ?", (st.session_state.user_id,))
                conn.commit()
                conn.close()
                st.success("All items cleared from shortlist!")
                st.rerun()
    
    # Display shortlist summary in sidebar
    display_shortlist_summary()


def get_shortlist_summary(user_id):
    """Get summary statistics of user's shortlist"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Total items
        cursor.execute("SELECT COUNT(*) FROM shortlists WHERE user_id = ?", (user_id,))
        total_items = cursor.fetchone()[0]
        
        # Items by institute
        cursor.execute("""
            SELECT institute, COUNT(*) as count
            FROM shortlists
            WHERE user_id = ?
            GROUP BY institute
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
        
        # Average rank
        cursor.execute("""
            SELECT AVG(closing_rank) as avg_rank, MIN(closing_rank) as min_rank, MAX(closing_rank) as max_rank
            FROM shortlists
            WHERE user_id = ? AND closing_rank IS NOT NULL
        """, (user_id,))
        rank_stats = cursor.fetchone()
        
        return {
            'total_items': total_items,
            'by_institute': by_institute,
            'by_seat_type': by_seat_type,
            'avg_rank': rank_stats[0] if rank_stats[0] else None,
            'min_rank': rank_stats[1] if rank_stats[1] else None,
            'max_rank': rank_stats[2] if rank_stats[2] else None
        }
        
    except Exception as e:
        print(f"Error getting shortlist summary: {e}")
        return None
    finally:
        conn.close()


def display_shortlist_summary():
    """Display shortlist summary statistics in sidebar"""
    summary = get_shortlist_summary(st.session_state.user_id)
    
    if summary and summary['total_items'] > 0:
        st.sidebar.subheader("📊 Shortlist Summary")
        st.sidebar.metric("Total Items", summary['total_items'])
        
        if summary['avg_rank']:
            st.sidebar.metric("Avg. Closing Rank", f"{int(summary['avg_rank']):,}")
        
        if summary['min_rank'] and summary['max_rank']:
            st.sidebar.write(f"**Rank Range:** {summary['min_rank']:,} - {summary['max_rank']:,}")
        
        if summary['by_institute']:
            st.sidebar.write("**Top Institutes:**")
            for institute, count in summary['by_institute'][:5]:
                st.sidebar.write(f"• {institute}: {count}")
        
        if summary['by_seat_type']:
            st.sidebar.write("**By Seat Type:**")
            for seat_type, count in summary['by_seat_type']:
                st.sidebar.write(f"• {seat_type}: {count}")
