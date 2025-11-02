import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="✨ Smart Attendance System", layout="wide", page_icon="🗓️")

# --- SIDEBAR: UPLOAD DATASET ---
st.sidebar.header("📂 Upload Attendance File")
uploaded_file = st.sidebar.file_uploader("CSV or Excel", type=["csv", "xlsx"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        df.columns = [c.strip().lower() for c in df.columns]
        st.sidebar.success("✅ File uploaded successfully!")
    except Exception as e:
        st.sidebar.error(f"❌ Could not read file: {e}")
        st.stop()
else:
    df = None
    st.sidebar.info("📎 Upload a CSV or Excel file to start.")

# --- MAIN TITLE ---
st.markdown("<h1 style='text-align:center; color:#4B0082;'>🗓️ Smart Attendance Monitoring</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray;'>Track attendance trends, streaks, and get alerts for absences or lateness.</p>", unsafe_allow_html=True)

# --- NAVIGATION BUTTONS ---
if "page" not in st.session_state:
    st.session_state.page = "class_overview"

# Center buttons
st.markdown("""
<div style='text-align:center;'>
    <style>
    .nav-btn {display:inline-block; margin:5px; padding:10px 20px; background-color:#4B0082; color:white; border:none; border-radius:8px; cursor:pointer;}
    .nav-btn:hover {background-color:#6A0DAD;}
    </style>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("🏫 Class Overview"):
        st.session_state.page = "class_overview"
with col2:
    if st.button("👤 Individual Ratings"):
        st.session_state.page = "individual_ratings"
with col3:
    if st.button("📊 Overall Stats"):
        st.session_state.page = "overall_stats"
with col4:
    if st.button("📈 Trends & Alerts"):
        st.session_state.page = "trends_alerts"
with col5:
    if st.button("🔥 Attendance Heatmap"):
        st.session_state.page = "heatmap"

# --- PAGE CONTENT ---
if st.session_state.page == "class_overview":
    st.subheader("🏫 Class-Level Attendance")
    if df is not None:
        required_cols = ["employee_id", "name", "status", "date"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"⚠️ Missing columns! Required: {required_cols}")
        else:
            if "class" in df.columns:
                selected_class = st.selectbox("🎓 Select Class", sorted(df["class"].unique()))
                class_df = df[df["class"] == selected_class]
                st.dataframe(class_df, use_container_width=True, height=350)

                class_summary = class_df["status"].value_counts().reset_index()
                class_summary.columns = ["Status", "Count"]

                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(px.pie(class_summary, names="Status", values="Count", title="Status Distribution"), use_container_width=True)
                with col2:
                    st.plotly_chart(px.bar(class_summary, x="Status", y="Count", color="Status", title="Attendance Count"), use_container_width=True)
            else:
                st.warning("⚠️ Dataset has no 'class' column.")
    else:
        st.info("⬅️ Upload a dataset to visualize class attendance.")

# Continue the same logic for other pages, e.g., "individual_ratings", "overall_stats", etc.
