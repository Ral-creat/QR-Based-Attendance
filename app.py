import streamlit as st
import pandas as pd
import plotly.express as px
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
        tabs = st.tabs(["Dashboard","Per Student Rate","Per Class","Database Report"])

        # ------------------- Dashboard Tab -------------------
        with tabs[0]:
            st.header("📊 Overall Attendance Dashboard")

            overall_counts = df['Status'].value_counts()
            fig = px.pie(
                names=overall_counts.index,
                values=overall_counts.values,
                title="Overall Attendance Percentage (All Months)",
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown(f"**Total Students:** {df['ID'].nunique()}")
            st.markdown(f"**Total Records:** {len(df)}")

        # ------------------- Per Student Rate Tab -------------------
        with tabs[1]:
            st.header("👤 Attendance Rate per Student")
            student_summary = df.groupby(['ID','Name']).agg(
                Days_Present=('Status', lambda x: (x=='Present').sum()),
                Days_Absent=('Status', lambda x: (x=='Absent').sum())
            ).reset_index()
            student_summary['Total_Days'] = student_summary['Days_Present'] + student_summary['Days_Absent']
            student_summary['Attendance (%)'] = round((student_summary['Days_Present']/student_summary['Total_Days'])*100,2)

            # Sort descending
            st.dataframe(student_summary.sort_values('Attendance (%)', ascending=False), use_container_width=True)

        # ------------------- Per Class Tab -------------------
        with tabs[2]:
            st.header("📚 Attendance per Class")
            class_summary = df.groupby(['Class','ID','Name']).agg(
                Days_Present=('Status', lambda x: (x=='Present').sum()),
                Days_Absent=('Status', lambda x: (x=='Absent').sum())
            ).reset_index()

            # Class level %
            class_percent = class_summary.groupby('Class').agg(
                Total_Present=('Days_Present', 'sum'),
                Total_Records=('Days_Present', 'count')
            ).reset_index()
            class_percent['Attendance (%)'] = round((class_percent['Total_Present']/class_percent['Total_Records'])*100,2)

            st.dataframe(class_percent.merge(class_summary, on='Class'), use_container_width=True)

        # ------------------- Database Report Tab -------------------
        with tabs[3]:
            st.header("📥 Database / Monthly Report")
            st.dataframe(df.sort_values(['Month','Class','Name']), use_container_width=True)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name="All Attendance", index=False)
                student_summary.to_excel(writer, sheet_name="Student Summary", index=False)
                class_summary.to_excel(writer, sheet_name="Class Summary", index=False)

            st.download_button(
                "📥 Download Full Attendance Report",
                data=output.getvalue(),
                file_name="attendance_full_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

else:
    st.warning("⚠️ Please upload the Excel file to start monitoring attendance.")
