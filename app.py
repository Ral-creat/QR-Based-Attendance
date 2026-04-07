import streamlit as st
import pandas as pd
from io import BytesIO

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="📚 Attendance Monitoring System", layout="wide")

st.title("📚 Scholar Attendance Monitoring System")
st.markdown("Upload your attendance Excel file to generate reports 📊")

# =========================
# SESSION STATE
# =========================
if "attendance_df" not in st.session_state:
    st.session_state.attendance_df = None

# =========================
# TABS
# =========================
tab1, tab2 = st.tabs(["📊 Upload & Process", "📈 Dashboard"])

# =========================
# TAB 1: UPLOAD
# =========================
with tab1:
    st.subheader("📁 Upload Attendance File")

    uploaded_file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"])

    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.write("### Preview Data")
            st.dataframe(df)

            # REQUIRED COLUMNS CHECK
            required_cols = ["Name", "Date"]
            if not all(col in df.columns for col in required_cols):
                st.error("❌ File must contain 'Name' and 'Date' columns")
            else:
                df["Date"] = pd.to_datetime(df["Date"])
                df["Month"] = df["Date"].dt.to_period("M")

                st.session_state.attendance_df = df
                st.success("✅ File uploaded and processed!")

        except Exception as e:
            st.error(f"❌ Error: {e}")

# =========================
# TAB 2: DASHBOARD
# =========================
with tab2:
    st.subheader("📊 Attendance Dashboard")

    if st.session_state.attendance_df is None:
        st.warning("⚠️ Please upload a file first")
    else:
        df = st.session_state.attendance_df.copy()

        # =========================
        # MONTH FILTER
        # =========================
        selected_month = st.selectbox(
            "📅 Select Month",
            sorted(df["Month"].astype(str).unique())
        )

        df_month = df[df["Month"].astype(str) == selected_month]

        total_classes = df_month["Date"].nunique()
        total_students = df["Name"].nunique()

        # =========================
        # STUDENT SUMMARY
        # =========================
        st.subheader("👤 Attendance per Student")

        student_summary = df_month.groupby("Name").size().reset_index(name="Days Present")

        student_summary["Attendance Rate (%)"] = (
            student_summary["Days Present"] / total_classes * 100
        )

        def get_rating(rate):
            if rate == 100:
                return "Excellent ⭐"
            elif rate >= 75:
                return "Good 👍"
            elif rate >= 50:
                return "Fair ⚠️"
            else:
                return "Poor ❌"

        student_summary["Rating"] = student_summary["Attendance Rate (%)"].apply(get_rating)

        st.dataframe(student_summary.sort_values(by="Attendance Rate (%)", ascending=False), use_container_width=True)

        st.bar_chart(student_summary.set_index("Name")["Attendance Rate (%)"])

        # =========================
        # CLASS SUMMARY
        # =========================
        st.subheader("📚 Attendance per Class")

        class_summary = df_month.groupby("Date")["Name"].count().reset_index()
        class_summary.columns = ["Class Date", "Total Present"]

        # Attendance rate per class
        class_summary["Attendance Rate (%)"] = (
            class_summary["Total Present"] / total_students * 100
        )

        st.dataframe(class_summary, use_container_width=True)
        st.line_chart(class_summary.set_index("Class Date")["Total Present"])

        # =========================
        # METRICS
        # =========================
        st.subheader("📊 Monthly Overview")

        avg_attendance = student_summary["Attendance Rate (%)"].mean()

        col1, col2, col3 = st.columns(3)
        col1.metric("👥 Total Students", total_students)
        col2.metric("📚 Total Classes", total_classes)
        col3.metric("📈 Avg Attendance", f"{avg_attendance:.2f}%")

        # =========================
        # DOWNLOAD REPORT
        # =========================
        st.subheader("⬇️ Download Report")

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            student_summary.to_excel(writer, sheet_name='Student Summary', index=False)
            class_summary.to_excel(writer, sheet_name='Class Summary', index=False)

        st.download_button(
            label="📥 Download Monthly Report",
            data=output.getvalue(),
            file_name=f"attendance_report_{selected_month}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
