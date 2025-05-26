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
program = st.sidebar.text_input("Program (e.g., Computer Science)")
gender = st.sidebar.selectbox("Gender", ["All", "Gender-Neutral", "Female-only (including Supernumerary)"])
quota = st.sidebar.selectbox("Quota", ["All"] + sorted(df["Quota"].dropna().unique()))
seat_type = st.sidebar.selectbox("Seat Type", ["All"] + sorted(df["Seat Type"].dropna().unique()))
max_rank = st.sidebar.slider("Maximum Closing Rank", 1, 250000, 75000)

# Filter logic
filtered_df = df.copy()

if program:
    filtered_df = filtered_df[filtered_df["Academic Program Name"].str.contains(program, case=False)]

if gender != "All":
    filtered_df = filtered_df[filtered_df["Gender"] == gender]

if quota != "All":
    filtered_df = filtered_df[filtered_df["Quota"] == quota]

if seat_type != "All":
    filtered_df = filtered_df[filtered_df["Seat Type"] == seat_type]

filtered_df = filtered_df[filtered_df["Closing Rank"] <= max_rank]

# Sort by Closing Rank (ascending)
filtered_df = filtered_df.sort_values(by="Closing Rank")

st.markdown(f"### 🔍 Showing {len(filtered_df)} Results")
st.dataframe(filtered_df.reset_index(drop=True))

# Download button
st.download_button("📥 Download Results as CSV", filtered_df.to_csv(index=False), "filtered_results.csv")
