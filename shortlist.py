# Complete shortlist.py content with integrated table management

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


def update_priority_order(shortlist_id, new_priority, user_id):
    """Update priority order for a specific item"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get current priority
    cursor.execute("SELECT priority_order FROM shortlists WHERE id = ?", (shortlist_id,))
    current_priority = cursor.fetchone()
    
    if not current_priority:
        conn.close()
        return False
    
    current_priority = current_priority[0]
    
    # Update the target item's priority
    cursor.execute("UPDATE shortlists SET priority_order = ? WHERE id = ?", (new_priority, shortlist_id))
    
    # Reorder other items to maintain sequential order
    if new_priority != current_priority:
        # Get all items for this user ordered by new priority
        cursor.execute("""
            SELECT id FROM shortlists 
            WHERE user_id = ? 
            ORDER BY CASE WHEN id = ? THEN ? ELSE priority_order END
        """, (user_id, shortlist_id, new_priority))
        
        items = cursor.fetchall()
        
        # Update all priorities to be sequential
        for index, (item_id,) in enumerate(items, 1):
            cursor.execute("UPDATE shortlists SET priority_order = ? WHERE id = ?", (index, item_id))
    
    conn.commit()
    conn.close()
    return True


def process_shortlist_changes(user_id, original_df, edited_df):
    """Process changes made in the data editor"""
    changes_made = False
    
    # Check for removed items (marked for removal)
    if 'Remove' in edited_df.columns:
        items_to_remove = edited_df[edited_df['Remove'] == True]['id'].tolist()
        for item_id in items_to_remove:
            remove_from_shortlist(item_id)
            changes_made = True
        
        if items_to_remove:
            st.success(f"Removed {len(items_to_remove)} item(s) from shortlist!")
    
    # Check for notes changes
    if 'Notes' in edited_df.columns and 'Notes' in original_df.columns:
        for idx, row in edited_df.iterrows():
            if idx < len(original_df):
                original_notes = original_df.iloc[idx]['Notes'] or ''
                new_notes = row['Notes'] or ''
                if original_notes != new_notes:
                    update_shortlist_notes(row['id'], new_notes)
                    changes_made = True
    
    # Check for priority changes
    if 'Priority' in edited_df.columns and 'Priority' in original_df.columns:
        for idx, row in edited_df.iterrows():
            if idx < len(original_df):
                original_priority = original_df.iloc[idx]['Priority']
                new_priority = row['Priority']
                if original_priority != new_priority and pd.notnull(new_priority):
                    update_priority_order(row['id'], int(new_priority), user_id)
                    changes_made = True
    
    return changes_made


def shortlist_page():
    """Display shortlist management page with integrated table controls"""
    st.subheader("⭐ My Shortlist")
    
    shortlist_df = get_user_shortlist(st.session_state.user_id)
    
    if len(shortlist_df) == 0:
        st.info("Your shortlist is empty. Go to the search page to add some options!")
        return
    
    st.write(f"You have **{len(shortlist_df)}** items in your shortlist.")
    st.info("💡 Edit priority numbers, notes, or mark items for removal directly in the table below.")
    
    # Prepare dataframe for editing
    edit_df = shortlist_df.copy()
    
    # Format closing rank with commas
    if "closing_rank" in edit_df.columns:
        edit_df["closing_rank_display"] = edit_df["closing_rank"].apply(
            lambda x: f"{int(x):,}" if pd.notnull(x) else ""
        )
    
    # Rename and reorder columns for better display
    edit_df = edit_df.rename(columns={
        'priority_order': 'Priority',
        'institute': 'Institute',
        'program': 'Program',
        'closing_rank_display': 'Closing Rank',
        'seat_type': 'Seat Type',
        'quota': 'Quota',
        'gender': 'Gender',
        'notes': 'Notes'
    })
    
    # Add Remove column
    edit_df['Remove'] = False
    
    # Select and order columns for display
    display_columns = [
        'Priority', 'Institute', 'Program', 'Closing Rank', 
        'Seat Type', 'Quota', 'Gender', 'Notes', 'Remove'
    ]
    
    # Keep only required columns
    edit_df = edit_df[['id'] + display_columns]
    
    # Configure column settings
    column_config = {
        "Priority": st.column_config.NumberColumn(
            "Priority",
            help="Change the priority order (1 = highest priority)",
            min_value=1,
            max_value=len(edit_df),
            step=1,
            width="small"
        ),
        "Institute": st.column_config.TextColumn(
            "Institute",
            width="medium",
            disabled=True
        ),
        "Program": st.column_config.TextColumn(
            "Program",
            width="large",
            disabled=True
        ),
        "Closing Rank": st.column_config.TextColumn(
            "Closing Rank",
            width="small",
            disabled=True
        ),
        "Seat Type": st.column_config.TextColumn(
            "Seat Type",
            width="small",
            disabled=True
        ),
        "Quota": st.column_config.TextColumn(
            "Quota",
            width="small",
            disabled=True
        ),
        "Gender": st.column_config.TextColumn(
            "Gender",
            width="medium",
            disabled=True
        ),
        "Notes": st.column_config.TextColumn(
            "Notes",
            help="Add your personal notes about this option",
            width="medium"
        ),
        "Remove": st.column_config.CheckboxColumn(
            "Remove",
            help="Check to remove this item from shortlist",
            width="small"
        )
    }
    
    # Display the editable data table
    edited_df = st.data_editor(
        edit_df,
        column_config=column_config,
        disabled=["id", "Institute", "Program", "Closing Rank", "Seat Type", "Quota", "Gender"],
        hide_index=True,
        use_container_width=True,
        height=400,
        key="shortlist_editor"
    )
    
    # Process changes when Apply Changes button is clicked
    if st.button("💾 Apply Changes", type="primary", help="Save your changes to the database"):
        # Store original dataframe for comparison
        original_display_df = edit_df.copy()
        
        # Process the changes
        changes_made = process_shortlist_changes(
            st.session_state.user_id, 
            original_display_df, 
            edited_df
        )
        
        if changes_made:
            st.success("✅ Changes applied successfully!")
            # Small delay to show success message
            import time
            time.sleep(0.5)
            st.rerun()
        else:
            st.info("No changes detected.")
    
    # Export options
    st.markdown("---")
    st.subheader("📥 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Download current shortlist as CSV
        csv = shortlist_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"jee_shortlist_{st.session_state.username}.csv",
            mime="text/csv",
            help="Download your complete shortlist"
        )
    
    with col2:
        # Download formatted version
        formatted_df = edit_df.drop(columns=['id', 'Remove']).copy()
        formatted_csv = formatted_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📊 Download Formatted",
            data=formatted_csv,
            file_name=f"shortlist_formatted_{st.session_state.username}.csv",
            mime="text/csv",
            help="Download formatted shortlist"
        )
    
    with col3:
        # Clear all option
        if st.button("🗑️ Clear All", help="Remove all items from shortlist"):
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
            SELECT AVG(closing_rank) as avg_rank
            FROM shortlists
            WHERE user_id = ? AND closing_rank IS NOT NULL
        """, (user_id,))
        avg_rank = cursor.fetchone()[0]
        
        return {
            'total_items': total_items,
            'by_institute': by_institute,
            'by_seat_type': by_seat_type,
            'avg_rank': avg_rank
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
        
        if summary['by_institute']:
            st.sidebar.write("**Top Institutes:**")
            for institute, count in summary['by_institute'][:5]:
                st.sidebar.write(f"• {institute}: {count}")
        
        if summary['by_seat_type']:
            st.sidebar.write("**By Seat Type:**")
            for seat_type, count in summary['by_seat_type']:
                st.sidebar.write(f"• {seat_type}: {count}")
