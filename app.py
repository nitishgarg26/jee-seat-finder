
import streamlit as st
import pandas as pd

st.set_page_config(page_title="College Seat Finder", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("jee_data.csv")
    df["Closing Rank"] = pd.to_numeric(df["Closing Rank"], errors="coerce")
    df["Opening Rank"] = pd.to_numeric(df["Opening Rank"], errors="coerce")
    return df

df = load_data()

st.title("🎓 JEE College Seat Finder (2024)")

# Sidebar filters

# Predefined categories
category_map = {
    "Computers": ["computer", "data", "ai", "artificial", "intelligence"],
    "Electronics": ["electronics"]
}

all_programs = sorted(df["Academic Program Name"].dropna().unique())
program_options = ["Computers", "Electronics"] + all_programs

selected_programs = st.sidebar.multiselect("Academic Programs", program_options)

gender = st.sidebar.selectbox("Gender", ["All", "Gender-Neutral", "Female-only (including Supernumerary)"])
quota = st.sidebar.selectbox("Quota", ["All"] + sorted(df["Quota"].dropna().unique()))
seat_type = st.sidebar.selectbox("Seat Type", ["All"] + sorted(df["Seat Type"].dropna().unique()))
rank_range = st.sidebar.slider("Rank Range", 1, 250000, (1, 75000))
min_rank, max_rank = rank_range

# Apply program filtering
if selected_programs:
    mask = pd.Series([False] * len(df))
    for selected in selected_programs:
        if selected in category_map:
            keywords = category_map[selected]
            for kw in keywords:
                mask |= df["Academic Program Name"].str.contains(kw, case=False, na=False)
        else:
            mask |= df["Academic Program Name"] == selected
    filtered_df = df[mask]
else:
    filtered_df = df.copy()

# Apply other filters
if gender != "All":
    filtered_df = filtered_df[filtered_df["Gender"] == gender]

if quota != "All":
    filtered_df = filtered_df[filtered_df["Quota"] == quota]

if seat_type != "All":
    filtered_df = filtered_df[filtered_df["Seat Type"] == seat_type]

filtered_df = filtered_df[
    (filtered_df["Opening Rank"] >= min_rank) &
    (filtered_df["Closing Rank"] <= max_rank)
]

# Sort by Closing Rank
filtered_df = filtered_df.sort_values("Closing Rank")

st.markdown(f"### 🔍 Showing {len(filtered_df)} Results")
st.dataframe(filtered_df.reset_index(drop=True))

# Download button
st.download_button("📥 Download Results as CSV", filtered_df.to_csv(index=False), "filtered_results.csv")
