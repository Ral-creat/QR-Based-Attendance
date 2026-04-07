import streamlit as st
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="📚 Scholar Attendance Dashboard", layout="wide")
st.title("📚 Scholar Attendance Monitoring System")

# =========================
# SESSION STATE
# =========================
if "attendance_df" not in st.session_state:
    st.session_state.attendance_df = None
if "student_db" not in st.session_state:
    st.session_state.student_db = None

# =========================
# STUDENT DATABASE (maps ID# → Name → Class)
# =========================
st.sidebar.header("Student Database (optional)")
uploaded_student_db = st.sidebar.file_uploader("Upload Student Database Excel", type=["xlsx", "csv"], key="db")

if uploaded_student_db:
    if uploaded_student_db.name.endswith(".csv"):
        student_db = pd.read_csv(uploaded_student_db)
    else:
        student_db = pd.read_excel(uploaded_student_db)
    if "ID" not in student_db.columns or "Name" not in student_db.columns or "Class" not in student_db.columns:
        st.sidebar.error("❌ Student DB must have columns: ID, Name, Class")
    else:
        st.session_state.student_db = student_db
        st.sidebar.success("✅ Student DB loaded")

# =========================
# UPLOAD AUTOMATED QR EXCEL
# =========================
st.sidebar.header("Upload QR Attendance")
uploaded_file = st.sidebar.file_uploader("Upload Excel/CSV (ID#, Name, Time In, Time Out)", type=["xlsx","csv"], key="qr")

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    # Check columns
    required_cols = ["ID", "Name", "Time In", "Time Out"]
    if not all(col in df.columns for col in required_cols):
        st.sidebar.error(f"❌ File must have columns: {required_cols}")
    else:
        df["Time In"] = pd.to_datetime(df["Time In"])
        df["Date"] = df["Time In"].dt.date
        df["Status"] = "Present"
        st.session_state.attendance_df = df
        st.sidebar.success("✅ Attendance file loaded")

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

if st.session_state.attendance_df is not None and st.session_state.student_db is not None:
    df = st.session_state.attendance_df.copy()
    student_db = st.session_state.student_db.copy()
    
    # Merge attendance with student db to get class
    df_full = df.merge(student_db, on=["ID","Name"], how="left")
    
    # All students in DB
    all_students = student_db.copy()
    
    # Fill absent for students not in QR file for that date
    all_dates = df_full["Date"].unique()
    records = []
    for date in all_dates:
        for _, student in student_db.iterrows():
            if not ((df_full["ID"]==student["ID"]) & (df_full["Date"]==date)).any():
                records.append({
                    "ID": student["ID"],
                    "Name": student["Name"],
                    "Class": student["Class"],
                    "Date": date,
                    "Status": "Absent"
                })
    if records:
        df_full = pd.concat([df_full, pd.DataFrame(records)], ignore_index=True)
    
    # =========================
    # DASHBOARD TAB
    # =========================
    with tabs[0]:
        st.subheader("📊 Overall Attendance Dashboard")
        
        total_records = len(df_full)
        present_count = len(df_full[df_full["Status"]=="Present"])
        absent_count = len(df_full[df_full["Status"]=="Absent"])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("👥 Total Students", student_db.shape[0])
        col2.metric("📚 Total Records", total_records)
        col3.metric("📈 Attendance Rate", f"{present_count/total_records*100:.2f}%")
        
        # Pie chart
        fig, ax = plt.subplots()
        ax.pie([present_count, absent_count], labels=["Present","Absent"], autopct="%1.1f%%", colors=["#4CAF50","#F44336"])
        ax.set_title("Overall Present vs Absent")
        st.pyplot(fig)
    
    # =========================
    # PER STUDENT TAB
    # =========================
    with tabs[1]:
        st.subheader("👤 Attendance per Student")
        student_summary = df_full.groupby("Name")["Status"].apply(lambda x: (x=="Present").sum()).reset_index(name="Days Present")
        student_summary["Total Classes"] = len(all_dates)
        student_summary["Attendance Rate (%)"] = student_summary["Days Present"]/student_summary["Total Classes"]*100
        st.dataframe(student_summary.sort_values("Attendance Rate (%)", ascending=False), use_container_width=True)
        
        st.bar_chart(student_summary.set_index("Name")["Attendance Rate (%)"])
    
    # =========================
    # PER CLASS TAB
    # =========================
    with tabs[2]:
        st.subheader("📚 Attendance per Class")
        class_summary = df_full.groupby(["Class","Date"])["Status"].apply(lambda x: (x=="Present").sum()).reset_index(name="Total Present")
        class_summary["Total Students"] = student_db.groupby("Class")["ID"].count().reindex(class_summary["Class"]).values
        class_summary["Attendance Rate (%)"] = class_summary["Total Present"]/class_summary["Total Students"]*100
        st.dataframe(class_summary, use_container_width=True)
        
        for class_name in class_summary["Class"].unique():
            st.write(f"**Class {class_name} Attendance Pie Chart**")
            sub = class_summary[class_summary["Class"]==class_name]
            fig, ax = plt.subplots()
            for _, row in sub.iterrows():
                ax.pie([row["Total Present"], row["Total Students"]-row["Total Present"]],
                       labels=["Present","Absent"], autopct="%1.1f%%", colors=["#4CAF50","#F44336"])
                ax.set_title(f"{class_name} - {row['Date']}")
            st.pyplot(fig)
    
    # =========================
    # MONTHLY TAB
    # =========================
    with tabs[3]:
        st.subheader("📅 Monthly Attendance Summary")
        df_full["Month"] = pd.to_datetime(df_full["Date"]).dt.to_period("M")
        selected_month = st.selectbox("Select Month", sorted(df_full["Month"].astype(str).unique()))
        month_data = df_full[df_full["Month"].astype(str)==selected_month]
        present_count = len(month_data[month_data["Status"]=="Present"])
        total_count = len(month_data)
        st.metric("📈 Monthly Attendance Rate", f"{present_count/total_count*100:.2f}%")
        
        # Pie chart
        absent_count = total_count - present_count
        fig, ax = plt.subplots()
        ax.pie([present_count, absent_count], labels=["Present","Absent"], autopct="%1.1f%%", colors=["#4CAF50","#F44336"])
        ax.set_title(f"{selected_month} Present vs Absent")
        st.pyplot(fig)
    
    # =========================
    # REPORTS TAB
    # =========================
    with tabs[4]:
        st.subheader("📥 Download Full Reports")
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_full.to_excel(writer, sheet_name="Full Attendance", index=False)
            student_summary.to_excel(writer, sheet_name="Student Summary", index=False)
            class_summary.to_excel(writer, sheet_name="Class Summary", index=False)
        st.download_button(
            "📥 Download Excel Report",
            data=output.getvalue(),
            file_name="attendance_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.warning("⚠️ Upload both Student DB and QR Attendance file to start")
