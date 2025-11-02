import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="✨ Smart Attendance System", layout="wide", page_icon="🗓️")

# --- LOAD EXTERNAL CSS ---
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
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

# Center buttons with hover effect
st.markdown("""
<div style='text-align:center;'>
    <style>
    .nav-btn {display:inline-block; margin:5px; padding:10px 20px; background-color:#4B0082; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:bold;}
    .nav-btn:hover {background-color:#6A0DAD;}
    </style>
</div>
""", unsafe_allow_html=True)

cols = st.columns(5)
buttons = ["🏫 Class Overview", "👤 Individual Ratings", "📊 Overall Stats", "📈 Trends & Alerts", "🔥 Attendance Heatmap"]
pages = ["class_overview", "individual_ratings", "overall_stats", "trends_alerts", "heatmap"]

for col, btn, page_name in zip(cols, buttons, pages):
    if col.button(btn):
        st.session_state.page = page_name

# --- PAGE LOGIC ---

# ---------- CLASS OVERVIEW ----------
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

# ---------- INDIVIDUAL RATINGS ----------
elif st.session_state.page == "individual_ratings":
    st.subheader("👤 Employee Attendance Rating & Streaks")
    if df is not None:
        rating_map = {"Absent": 1, "Late": 2, "On Time": 3}
        df["rating_score"] = df["status"].map(rating_map).fillna(0)

        rating_summary = df.groupby(["employee_id", "name"])["rating_score"].mean().reset_index()
        rating_summary = rating_summary.sort_values(by="rating_score", ascending=False)

        def label_rating(score):
            if score >= 2.5: return "🌟 Excellent"
            elif score >= 1.8: return "👍 Good"
            elif score >= 1: return "⚠️ Needs Improvement"
            else: return "❌ Poor"

        rating_summary["Rating"] = rating_summary["rating_score"].apply(label_rating)
        st.dataframe(rating_summary, use_container_width=True, height=350)

        selected_emp = st.selectbox("Select Employee", rating_summary["name"].unique())
        emp_data = df[df["name"] == selected_emp].sort_values("date")
        emp_data["date"] = pd.to_datetime(emp_data["date"])

        # Streak calculation
        emp_data['on_time_flag'] = emp_data['status'] == 'On Time'
        streak = max_streak = 0
        for flag in emp_data['on_time_flag']:
            streak = streak + 1 if flag else 0
            max_streak = max(max_streak, streak)
        st.markdown(f"**Longest On-Time Streak:** {max_streak} days")

        st.plotly_chart(px.bar(emp_data, x="date", y="rating_score", color="status", title=f"{selected_emp}'s Attendance Trend"), use_container_width=True)

        # Smart alerts
        recent_status = emp_data.iloc[-1]["status"]
        if recent_status == "Absent":
            st.warning(f"⚠️ {selected_emp} was absent on {emp_data.iloc[-1]['date'].date()}")
        elif recent_status == "Late":
            st.info(f"⏰ {selected_emp} was late on {emp_data.iloc[-1]['date'].date()}")
    else:
        st.info("⬅️ Upload a dataset to view ratings and streaks.")

# ---------- OVERALL STATS ----------
elif st.session_state.page == "overall_stats":
    st.subheader("📊 Overall Attendance Stats")
    if df is not None:
        overall_summary = df["status"].value_counts().reset_index()
        overall_summary.columns = ["Status", "Count"]

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.pie(overall_summary, names="Status", values="Count", title="Overall Status Distribution"), use_container_width=True)
        with col2:
            st.plotly_chart(px.bar(overall_summary, x="Status", y="Count", color="Status", title="Overall Attendance Count"), use_container_width=True)

        if "class" in df.columns:
            class_summary = df.groupby("class")["status"].value_counts().unstack().fillna(0)
            st.dataframe(class_summary, use_container_width=True, height=300)
            st.plotly_chart(px.bar(class_summary, barmode="group", title="Class-Wise Attendance Comparison"), use_container_width=True)
    else:
        st.info("⬅️ Upload a dataset to see overall analytics.")

# ---------- TRENDS & ALERTS ----------
elif st.session_state.page == "trends_alerts":
    st.subheader("📈 Attendance Trends & Alerts")
    if df is not None:
        df["date"] = pd.to_datetime(df["date"])
        trend_summary = df.groupby(["date", "status"]).size().reset_index(name="Count")
        st.plotly_chart(px.line(trend_summary, x="date", y="Count", color="status", markers=True, title="Daily Attendance Trend"), use_container_width=True)

        # Auto-alert top absentees
        absences = df[df["status"] == "Absent"].groupby("name").size().sort_values(ascending=False).head(5)
        st.markdown("### ⚠️ Top 5 Absentees")
        st.table(absences)
    else:
        st.info("⬅️ Upload a dataset to see trends and alerts.")

# ---------- HEATMAP ----------
elif st.session_state.page == "heatmap":
    st.subheader("🔥 Attendance Heatmap (Employee vs Date)")
    if df is not None:
        df["date"] = pd.to_datetime(df["date"])
        df['on_time_flag'] = df['status'] == 'On Time'
        heatmap_data = df.pivot_table(index='name', columns='date', values='on_time_flag', fill_value=0)
        fig = px.imshow(heatmap_data, color_continuous_scale="YlGnBu",
                        labels=dict(x="Date", y="Employee", color="On-Time Attendance"),
                        title="🔥 Attendance Heatmap")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("⬅️ Upload a dataset to see the heatmap.")
