import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="✨ Smart Attendance System", layout="wide", page_icon="🗓️")

# --- LOAD EXTERNAL CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Example: create 'style.css' in your project folder
local_css("style.css")

# --- SIDEBAR: UPLOAD DATASET ---
st.sidebar.header("📂 Upload Attendance File")
uploaded_file = st.sidebar.file_uploader("CSV or Excel", type=["csv", "xlsx"])
if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
    df.columns = [c.strip().lower() for c in df.columns]
    st.sidebar.success("✅ File uploaded successfully!")
else:
    df = None
    st.sidebar.info("📎 Upload a CSV or Excel file to start.")

# --- MAIN TITLE ---
st.markdown("<h1 style='text-align:center; color:#4B0082;'>🗓️ Smart Attendance Monitoring</h1>", unsafe_allow_html=True)

# --- NAVIGATION BUTTONS ---
tabs = ["Class Overview", "Individual Ratings", "Overall Stats", "Trends & Alerts", "Attendance Heatmap"]
st.markdown(
    "<div class='tab-container'>" +
    "".join([f"<button class='tab-button' onclick='window.location.href=\"#{tab}\"'>{tab}</button>" for tab in tabs]) +
    "</div>", unsafe_allow_html=True
)

# --- SESSION STATE FOR TAB SELECTION ---
if "current_tab" not in st.session_state:
    st.session_state.current_tab = tabs[0]

# Tab selection buttons (click sets session_state)
for tab in tabs:
    if st.button(tab, key=tab):
        st.session_state.current_tab = tab

# --- RENDER TABS BASED ON SELECTION ---
selected_tab = st.session_state.current_tab

# --- TAB CONTENT ---
if selected_tab == "Class Overview":
    st.subheader("🏫 Class-Level Attendance")
    if df is not None:
        if "class" in df.columns:
            selected_class = st.selectbox("Select Class", sorted(df["class"].unique()))
            class_df = df[df["class"] == selected_class]
            st.dataframe(class_df)
            summary = class_df["status"].value_counts().reset_index()
            summary.columns = ["Status", "Count"]
            st.plotly_chart(px.bar(summary, x="Status", y="Count", color="Status", title="Class Attendance Count"))
        else:
            st.warning("No 'class' column in dataset")
    else:
        st.info("Upload dataset to view Class Overview.")

elif selected_tab == "Individual Ratings":
    st.subheader("👤 Individual Attendance Ratings")
    if df is not None:
        rating_map = {"Absent": 1, "Late": 2, "On Time": 3}
        df["rating_score"] = df["status"].map(rating_map).fillna(0)
        rating_summary = df.groupby(["employee_id", "name"])["rating_score"].mean().reset_index()
        st.dataframe(rating_summary)
    else:
        st.info("Upload dataset to view Individual Ratings.")

elif selected_tab == "Overall Stats":
    st.subheader("📊 Overall Stats")
    if df is not None:
        overall_summary = df["status"].value_counts().reset_index()
        overall_summary.columns = ["Status", "Count"]
        st.plotly_chart(px.pie(overall_summary, names="Status", values="Count", title="Overall Attendance Distribution"))
    else:
        st.info("Upload dataset to view Overall Stats.")

elif selected_tab == "Trends & Alerts":
    st.subheader("📈 Trends & Alerts")
    if df is not None:
        df["date"] = pd.to_datetime(df["date"])
        trend_summary = df.groupby(["date", "status"]).size().reset_index(name="Count")
        st.plotly_chart(px.line(trend_summary, x="date", y="Count", color="status", markers=True, title="Attendance Trends"))
    else:
        st.info("Upload dataset to view Trends & Alerts.")

elif selected_tab == "Attendance Heatmap":
    st.subheader("🔥 Attendance Heatmap")
    if df is not None:
        df["date"] = pd.to_datetime(df["date"])
        df["on_time_flag"] = df["status"] == "On Time"
        heatmap_data = df.pivot_table(index="name", columns="date", values="on_time_flag", fill_value=0)
        fig = px.imshow(heatmap_data, color_continuous_scale="YlGnBu",
                        labels=dict(x="Date", y="Employee", color="On-Time Attendance"),
                        title="Attendance Heatmap")
        st.plotly_chart(fig)
    else:
        st.info("Upload dataset to view Attendance Heatmap.")
