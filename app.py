# Main Tabs (UPDATED)
tab1, tab2 = st.tabs(["📊 Upload & Process", "📈 Dashboard"])

# ==============================
# 📊 TAB 1: UPLOAD + PROCESS
# ==============================
with tab1:
    st.subheader("📁 Upload Attendance File")

    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "csv"])

    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.write("### Preview Data")
        st.dataframe(df)

        # Standardize columns
        df["Date"] = pd.to_datetime(df["Date"])
        df["Month"] = df["Date"].dt.to_period("M")

        # Save to session
        st.session_state.attendance_df = df

        st.success("✅ File uploaded successfully!")

# ==============================
# 📈 TAB 2: DASHBOARD
# ==============================
with tab2:
    st.subheader("📊 Attendance Dashboard")

    if "attendance_df" not in st.session_state:
        st.warning("⚠️ Upload attendance file first")
    else:
        df = st.session_state.attendance_df.copy()

        # SELECT MONTH
        selected_month = st.selectbox(
            "📅 Select Month",
            sorted(df["Month"].astype(str).unique())
        )

        df_month = df[df["Month"].astype(str) == selected_month]

        # =========================
        # 👤 STUDENT ATTENDANCE
        # =========================
        st.subheader("👤 Attendance per Student")

        total_classes = df_month["Date"].nunique()

        student_summary = df_month.groupby("Name").size().reset_index(name="Days Present")

        student_summary["Attendance Rate (%)"] = (
            student_summary["Days Present"] / total_classes * 100
        )

        def rate_label(x):
            if x == 100:
                return "Excellent ⭐"
            elif x >= 75:
                return "Good 👍"
            elif x >= 50:
                return "Fair ⚠️"
            else:
                return "Poor ❌"

        student_summary["Rating"] = student_summary["Attendance Rate (%)"].apply(rate_label)

        st.dataframe(student_summary, use_container_width=True)
        st.bar_chart(student_summary.set_index("Name")["Attendance Rate (%)"])

        # =========================
        # 📚 CLASS ATTENDANCE
        # =========================
        st.subheader("📚 Attendance per Class")

        class_summary = df_month.groupby("Date")["Name"].count().reset_index()
        class_summary.columns = ["Class Date", "Total Present"]

        st.dataframe(class_summary, use_container_width=True)
        st.line_chart(class_summary.set_index("Class Date"))

        # =========================
        # 📅 MONTHLY SUMMARY
        # =========================
        st.subheader("📅 Monthly Summary")

        avg_attendance = student_summary["Attendance Rate (%)"].mean()

        col1, col2 = st.columns(2)
        col1.metric("📊 Avg Student Attendance", f"{avg_attendance:.2f}%")
        col2.metric("📚 Total Classes", total_classes)

        # =========================
        # 🏫 OVERALL CLASS RATE
        # =========================
        st.subheader("🏫 Overall Attendance per Class (%)")

        total_students = df["Name"].nunique()

        class_summary["Attendance Rate (%)"] = (
            class_summary["Total Present"] / total_students * 100
        )

        st.dataframe(class_summary, use_container_width=True)
        st.bar_chart(class_summary.set_index("Class Date")["Attendance Rate (%)"])

        # =========================
        # ⬇️ DOWNLOAD REPORT
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
