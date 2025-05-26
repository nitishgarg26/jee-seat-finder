import streamlit as st
import pandas as pd

st.set_page_config(page_title="College Seat Finder", layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv("jee_data.csv")

df = load_data()

st.title("🎓 JEE College Seat Finder (2024)")

# Sidebar filters
program = st.sidebar.text_input("Program (e.g., Computer Science)")
gender = st.sidebar.selectbox("Gender", ["All", "Gender-Neutral", "Female-only (including Supernumerary)"])
quota = st.sidebar.selectbox("Quota", ["All"] + sorted(df["Quota"].unique().tolist()))
max_rank = st.sidebar.slider("Maximum Closing Rank", 1, 250000, 75000)

# Filter
filtered_df = df.copy()

if program:
    filtered_df = filtered_df[filtered_df["Academic Program Name"].str.contains(program, case=False)]

if gender != "All":
    filtered_df = filtered_df[filtered_df["Gender"] == gender]

if quota != "All":
    filtered_df = filtered_df[filtered_df["Quota"] == quota]

filtered_df = filtered_df[filtered_df["Closing Rank"] <= max_rank]

st.markdown(f"### 🔍 Showing {len(filtered_df)} Results")
st.dataframe(filtered_df.reset_index(drop=True))

# Optional: Download option
st.download_button("📥 Download Results as CSV", filtered_df.to_csv(index=False), "filtered_results.csv")
