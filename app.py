import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Attendance Monitoring System", layout="wide")

# --- TITLE ---
st.title("📊 Employee Attendance Monitoring and Evaluation System")
st.write("I-upload ang attendance dataset aron makita ang summary, rating, ug visual analysis.")

# --- FILE UPLOAD ---
uploaded_file = st.file_uploader("📂 Upload Attendance CSV or Excel File", type=["csv", "xlsx"])

if uploaded_file:
    # --- READ FILE ---
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        st.stop()

    st.success("✅ File successfully uploaded!")

    # --- DISPLAY DATA ---
    st.subheader("📋 Attendance Dataset")
    st.dataframe(df, use_container_width=True)

    # --- CLEANING ---
    df.columns = [c.strip().lower() for c in df.columns]  # normalize column names

    # --- REQUIRED COLUMNS CHECK ---
    required_cols = ["employee_id", "name", "status", "date"]
    if not all(col in df.columns for col in required_cols):
        st.error(f"⚠️ Missing columns. Required: {required_cols}")
        st.stop()

    # --- ANALYSIS ---
    st.divider()
    st.subheader("📈 Attendance Summary")

    # Count by status (On Time, Late, Absent, etc.)
    status_summary = df["status"].value_counts().reset_index()
    status_summary.columns = ["Status", "Count"]

    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.pie(status_summary, names="Status", values="Count", title="Attendance Distribution")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = px.bar(status_summary, x="Status", y="Count", title="Total per Attendance Status")
        st.plotly_chart(fig2, use_container_width=True)

    # --- EMPLOYEE PERFORMANCE / RATING ---
    st.divider()
    st.subheader("⭐ Employee Attendance Rating")

    # Rating formula (example: 1 = absent, 2 = late, 3 = on time)
    rating_map = {"Absent": 1, "Late": 2, "On Time": 3}
    df["rating_score"] = df["status"].map(rating_map).fillna(0)

    rating_summary = (
        df.groupby(["employee_id", "name"])["rating_score"]
        .mean()
        .reset_index()
        .sort_values(by="rating_score", ascending=False)
    )

    # Convert numeric scores to text-based ratings
    def rating_label(score):
        if score >= 2.5:
            return "Excellent"
        elif score >= 1.8:
            return "Good"
        elif score >= 1:
            return "Needs Improvement"
        else:
            return "Poor"

    rating_summary["Rating"] = rating_summary["rating_score"].apply(rating_label)

    st.dataframe(rating_summary, use_container_width=True)

    # --- VISUALIZATION PER EMPLOYEE ---
    st.divider()
    st.subheader("📊 Attendance Over Time")

    selected_employee = st.selectbox("Pili ug empleyado:", df["name"].unique())
    emp_data = df[df["name"] == selected_employee]

    fig3 = px.bar(
        emp_data,
        x="date",
        y="status",
        color="status",
        title=f"Attendance History: {selected_employee}",
    )
    st.plotly_chart(fig3, use_container_width=True)

    # --- DOWNLOADABLE REPORT ---
    st.divider()
    st.subheader("📥 Export Report")

    csv = rating_summary.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Employee Ratings (CSV)",
        data=csv,
        file_name="employee_ratings.csv",
        mime="text/csv",
    )

else:
    st.info("⬆️ Upload an attendance dataset to start analysis.")
