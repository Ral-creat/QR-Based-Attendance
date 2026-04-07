import streamlit as st
import pandas as pd
from io import BytesIO

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="📚 Attendance Monitoring", layout="wide")

st.title("📚 Scholar Attendance Monitoring System")

# =========================
# SESSION STATE
# =========================
if "attendance_df" not in st.session_state:
    st.session_state.attendance_df = None

# =========================
# UPLOAD SECTION
# =========================
st.sidebar.header("📂 Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Required columns
    if "Name" not in df.columns or "Date" not in df.columns:
        st.error("❌ File must contain 'Name' and 'Date'")
    else:
        df["Date"] = pd.to_datetime(df["Date"])
        df["Month"] = df["Date"].dt.to_period("M")
        st.session_state.attendance_df = df
        st.sidebar.success("✅ Uploaded!")

# =========================
# MAIN TABS
# =========================
tabs = st.tabs([
    "📊 Dashboard",
    "👤 Per Student",
    "📚 Per Class",
    "📅 Monthly",
    "📥 Reports"
])

# =========================
# LOAD DATA
# =========================
if st.session_state.attendance_df is not None:
    df = st.session_state.attendance_df.copy()

    selected_month = st.selectbox(
        "📅 Select Month",
        sorted(df["Month"].astype(str).unique())
    )

    df_month = df[df["Month"].astype(str) == selected_month]

    total_students = df["Name"].nunique()
    total_classes = df_month["Date"].nunique()  # should be 2

    # =========================
    # 👤 PER STUDENT
    # =========================
    student_summary = df_month.groupby("Name").size().reset_index(name="Days Present")
    student_summary["Attendance Rate (%)"] = (
        student_summary["Days Present"] / total_classes * 100
    )

    # =========================
    # 📚 PER CLASS
    # =========================
    class_summary = df_month.groupby("Date")["Name"].count().reset_index()
    class_summary.columns = ["Class Date", "Total Present"]

    class_summary["Attendance Rate (%)"] = (
        class_summary["Total Present"] / total_students * 100
    )

    # =========================
    # 📊 DASHBOARD TAB
    # =========================
    with tabs[0]:
        st.subheader("📊 Overall Dashboard")

        avg_rate = student_summary["Attendance Rate (%)"].mean()

        col1, col2, col3 = st.columns(3)
        col1.metric("👥 Students", total_students)
        col2.metric("📚 Classes (Month)", total_classes)
        col3.metric("📈 Overall Attendance", f"{avg_rate:.2f}%")

        st.subheader("📈 Overall Attendance Graph")
        st.bar_chart(student_summary.set_index("Name")["Attendance Rate (%)"])

    # =========================
    # 👤 PER STUDENT TAB
    # =========================
    with tabs[1]:
        st.subheader("👤 Attendance per Student")

        sorted_df = student_summary.sort_values("Attendance Rate (%)", ascending=False)
        st.dataframe(sorted_df, use_container_width=True)

        st.bar_chart(sorted_df.set_index("Name")["Attendance Rate (%)"])

    # =========================
    # 📚 PER CLASS TAB
    # =========================
    with tabs[2]:
        st.subheader("📚 Attendance per Class")

        st.dataframe(class_summary, use_container_width=True)

        st.line_chart(class_summary.set_index("Class Date")["Total Present"])

    # =========================
    # 📅 MONTHLY TAB
    # =========================
    with tabs[3]:
        st.subheader("📅 Monthly Attendance Summary")

        st.write(f"Total Classes this Month: **{total_classes}** (Expected: 2 Saturdays)")

        avg_rate = student_summary["Attendance Rate (%)"].mean()

        st.metric("📊 Monthly Average Attendance", f"{avg_rate:.2f}%")

        st.bar_chart(class_summary.set_index("Class Date")["Attendance Rate (%)"])

    # =========================
    # 📥 REPORTS TAB
    # =========================
    with tabs[4]:
        st.subheader("📥 Download Reports")

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            student_summary.to_excel(writer, sheet_name="Student Summary", index=False)
            class_summary.to_excel(writer, sheet_name="Class Summary", index=False)

        st.download_button(
            "📥 Download Excel Report",
            data=output.getvalue(),
            file_name=f"attendance_{selected_month}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.warning("⚠️ Upload attendance file from sidebar to start")
