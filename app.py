import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="PHX47 Attendance Management System", layout="wide")
st.title("PHX47 Attendance Management System")

# =========================
# SESSION STATE
# =========================
if "attendance_df" not in st.session_state:
    st.session_state.attendance_df = None

# =========================
# UPLOAD SECTION
# =========================
st.sidebar.header("📂 Upload Attendance File")
st.sidebar.write("⚠️ Please upload an Excel file with headers: Name, Date, Status (Present/Absent)")

uploaded_file = st.sidebar.file_uploader("Upload Excel", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Check required columns
    required_cols = ["Name", "Date", "Status"]
    if not all(col in df.columns for col in required_cols):
        st.error(f"❌ File must contain columns: {', '.join(required_cols)}")
    else:
        df["Date"] = pd.to_datetime(df["Date"])
        df["Month"] = df["Date"].dt.to_period("M")
        st.session_state.attendance_df = df
        st.sidebar.success("✅ File uploaded successfully!")

# =========================
# MAIN TABS
# =========================
tabs = st.tabs([
    "📊 Dashboard",
    "👤 Per Student",
    "📚 Per Class",
    "📥 Database Report"
])

# =========================
# PROCESS DATA
# =========================
if st.session_state.attendance_df is not None:
    df = st.session_state.attendance_df.copy()

    selected_month = st.selectbox(
        "📅 Select Month",
        sorted(df["Month"].astype(str).unique())
    )

    df_month = df[df["Month"].astype(str) == selected_month]

    total_students = df["Name"].nunique()
    total_classes = df_month["Date"].nunique()

    # Overall present/absent counts
    overall_counts = df_month["Status"].value_counts()
    present_count = overall_counts.get("Present", 0)
    absent_count = overall_counts.get("Absent", 0)
    present_pct = present_count / (present_count + absent_count) * 100 if (present_count + absent_count) > 0 else 0
    absent_pct = absent_count / (present_count + absent_count) * 100 if (present_count + absent_count) > 0 else 0

    # Per Student Summary
    student_summary = df_month.groupby("Name").agg(
        Days_Present=("Status", lambda x: (x == "Present").sum()),
        Days_Absent=("Status", lambda x: (x == "Absent").sum())
    ).reset_index()
    student_summary["Attendance Rate (%)"] = student_summary["Days_Present"] / total_classes * 100
    low_attendance = student_summary["Attendance Rate (%)"].min()
    high_attendance = student_summary["Attendance Rate (%)"].max()

    # Per Class Summary
    class_summary = df_month.groupby("Date").agg(
        Total_Present=("Status", lambda x: (x == "Present").sum()),
        Total_Absent=("Status", lambda x: (x == "Absent").sum())
    ).reset_index()
    class_summary["Attendance Rate (%)"] = class_summary["Total_Present"] / total_students * 100

    # =========================
    # DASHBOARD TAB
    # =========================
    with tabs[0]:
        st.subheader("📊 Overall Attendance Dashboard")
        col1, col2, col3 = st.columns(3)
        col1.metric("👥 Total Students", total_students)
        col2.metric("📅 Total Classes (Month)", total_classes)
        col3.metric("📈 Overall Attendance", f"{present_pct:.2f}%")

        st.subheader("📊 Present vs Absent")
        fig = px.pie(
            names=["Present", "Absent"],
            values=[present_count, absent_count],
            color_discrete_sequence=px.colors.qualitative.Set2,
            title=f"Attendance Distribution ({selected_month})"
        )
        st.plotly_chart(fig, use_container_width=True)

    # =========================
    # PER STUDENT TAB
    # =========================
    with tabs[1]:
        st.subheader("👤 Per Student Attendance")
        st.dataframe(student_summary.sort_values("Attendance Rate (%)", ascending=False), use_container_width=True)
        st.markdown(f"✅ Highest Attendance: {high_attendance:.2f}%")
        st.markdown(f"⚠️ Lowest Attendance: {low_attendance:.2f}%")

    # =========================
    # PER CLASS TAB
    # =========================
    with tabs[2]:
        st.subheader("📚 Per Class Attendance")
        st.dataframe(class_summary.sort_values("Date"), use_container_width=True)

    # =========================
    # DATABASE REPORT TAB
    # =========================
    with tabs[3]:
        st.subheader("📥 Download Full Reports")
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name="Raw Attendance", index=False)
            student_summary.to_excel(writer, sheet_name="Per Student", index=False)
            class_summary.to_excel(writer, sheet_name="Per Class", index=False)

        st.download_button(
            "📥 Download Excel Report",
            data=output.getvalue(),
            file_name=f"attendance_report_{selected_month}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.warning("⚠️ Upload an Excel attendance file from the sidebar to start")
