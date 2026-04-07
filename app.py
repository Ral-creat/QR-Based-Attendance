import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="PHX47 Attendance Management System", layout="wide")
st.title("📊 PHX47 Attendance Management System")
st.markdown("**Note:** Upload your Excel file. Make sure it has headers: `ID`, `Name`, `Class`, `Time In`, `Time Out`.")

# -------------------
# Upload Excel
# -------------------
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    required_cols = ['ID','Name','Class','Time In','Time Out']
    if not all(col in df.columns for col in required_cols):
        st.error("❌ File must contain columns: ID, Name, Class, Time In, Time Out")
    else:
        # Add Status column
        df['Status'] = df.apply(lambda x: 'Present' if pd.notna(x['Time In']) else 'Absent', axis=1)
        df['Date'] = pd.to_datetime(df['Time In'].fillna(pd.Timestamp.today()))
        df['Month'] = df['Date'].dt.to_period('M')

        # Tabs
        tabs = st.tabs(["Dashboard","Per Student","Per Class","Database Report"])

        # ------------------- Dashboard Tab -------------------
        with tabs[0]:
            st.header("📊 Overall Attendance Dashboard")

            overall_counts = df['Status'].value_counts()
            # Pie chart using matplotlib
            fig, ax = plt.subplots()
            ax.pie(overall_counts.values, labels=overall_counts.index, autopct='%1.1f%%', colors=['#1f77b4','#ff7f0e'])
            ax.set_title("Overall Attendance Percentage")
            st.pyplot(fig)

            st.markdown(f"**Total Students:** {df['ID'].nunique()}")
            st.markdown(f"**Total Attendance Records:** {len(df)}")
            st.dataframe(df[['ID','Name','Class','Date','Status']], use_container_width=True)

        # ------------------- Per Student Tab -------------------
        with tabs[1]:
            st.header("👤 Attendance Per Student")
            student_summary = df.groupby(['ID','Name']).agg(
                Days_Present=('Status', lambda x: (x=='Present').sum()),
                Days_Absent=('Status', lambda x: (x=='Absent').sum())
            ).reset_index()
            student_summary['Total_Days'] = student_summary['Days_Present'] + student_summary['Days_Absent']
            student_summary['Attendance (%)'] = round((student_summary['Days_Present']/student_summary['Total_Days'])*100,2)

            st.dataframe(student_summary.sort_values('Attendance (%)', ascending=False), use_container_width=True)

        # ------------------- Per Class Tab -------------------
        with tabs[2]:
            st.header("📚 Attendance Per Class")
            class_summary = df.groupby(['Class','ID','Name']).agg(
                Days_Present=('Status', lambda x: (x=='Present').sum()),
                Days_Absent=('Status', lambda x: (x=='Absent').sum())
            ).reset_index()
            st.dataframe(class_summary, use_container_width=True)

        # ------------------- Database Report Tab -------------------
        with tabs[3]:
            st.header("📥 Download Monthly Report")
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                student_summary.to_excel(writer, sheet_name="Student Summary", index=False)
                class_summary.to_excel(writer, sheet_name="Class Summary", index=False)
            st.download_button(
                "📥 Download Excel Report",
                data=output.getvalue(),
                file_name="attendance_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

else:
    st.warning("⚠️ Please upload the Excel file to start monitoring attendance.")
