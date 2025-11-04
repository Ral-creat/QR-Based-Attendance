import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="FloodAlert", page_icon="🌊", layout="wide")

# --- INIT DATA STORAGE ---
if "reports.csv" not in os.listdir():
    pd.DataFrame(columns=["Reporter", "Barangay", "Flood_Level", "Description", "Date", "Latitude", "Longitude"]).to_csv("reports.csv", index=False)

# --- LOAD DATA ---
data = pd.read_csv("reports.csv")

# --- SIDEBAR NAV ---
st.sidebar.title("🌊 FloodAlert Navigation")
page = st.sidebar.radio("Go to", ["🏠 Home", "🗺️ Flood Map", "📋 Report Flood", "📊 Analytics"])

# --- PAGE 1: HOME ---
if page == "🏠 Home":
    st.title("🌊 FloodAlert: Community Flood Reporting & Visualization System")
    st.markdown("""
    Welcome to **FloodAlert**, a community-driven platform to report, visualize, and analyze flood events in your area.

    **Main Features**
    - 🧭 Real-time flood reporting  
    - 🗺️ Interactive flood map visualization  
    - 📈 Analytics for risk assessment  
    - 🏘️ Community-based monitoring  

    Developed using **Streamlit + Plotly + Pandas**.
    """)

# --- PAGE 2: MAP VIEW ---
elif page == "🗺️ Flood Map":
    st.title("🗺️ Flood Map Overview")
    if data.empty:
        st.warning("No flood reports yet. Be the first to submit one!")
    else:
        fig = px.scatter_mapbox(
            data,
            lat="Latitude",
            lon="Longitude",
            color="Flood_Level",
            hover_name="Barangay",
            hover_data=["Description", "Date"],
            color_continuous_scale="reds",
            zoom=10,
            height=600
        )
        fig.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig, use_container_width=True)

# --- PAGE 3: REPORT FORM ---
elif page == "📋 Report Flood":
    st.title("📋 Submit a Flood Report")
    with st.form("report_form", clear_on_submit=True):
        name = st.text_input("Reporter Name")
        brgy = st.text_input("Barangay / Location")
        level = st.selectbox("Flood Level", ["Low", "Moderate", "High", "Severe"])
        desc = st.text_area("Short Description")
        lat = st.number_input("Latitude", format="%.6f")
        lon = st.number_input("Longitude", format="%.6f")
        submitted = st.form_submit_button("🚨 Submit Report")

        if submitted:
            new_report = pd.DataFrame([{
                "Reporter": name,
                "Barangay": brgy,
                "Flood_Level": level,
                "Description": desc,
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Latitude": lat,
                "Longitude": lon
            }])
            new_report.to_csv("reports.csv", mode="a", header=False, index=False)
            st.success("✅ Flood report submitted successfully!")

# --- PAGE 4: ANALYTICS ---
elif page == "📊 Analytics":
    st.title("📊 Flood Analytics Dashboard")
    if data.empty:
        st.info("No data yet to analyze.")
    else:
        st.subheader("Flood Reports by Barangay")
        count = data["Barangay"].value_counts().reset_index()
        count.columns = ["Barangay", "Reports"]
        st.bar_chart(count.set_index("Barangay"))

        st.subheader("Flood Level Distribution")
        level_count = data["Flood_Level"].value_counts()
        st.write(level_count)

        fig = px.pie(names=level_count.index, values=level_count.values, title="Flood Severity Distribution", color_discrete_sequence=px.colors.sequential.Reds)
        st.plotly_chart(fig, use_container_width=True)
