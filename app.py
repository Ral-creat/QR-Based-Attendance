import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- PAGE CONFIG (must be first) ---
st.set_page_config(
    page_title="Attendance Monitoring Dashboard",
    layout="wide",
    page_icon="📊"
)

# --- SIDEBAR ---
st.sidebar.title("📁 Upload Section")
uploaded_file = st.sidebar.file_uploader("Upload Attendance File (Excel)", type=["xlsx"])

st.sidebar.markdown("---")
st.sidebar.info("👈 Upload your attendance dataset here to get started.")

# --- MAIN DASHBOARD ---
st.title("📊 Employee Attendance Monitoring System")
st.write("Monitor attendance by class, track individual ratings, and visualize trends easily.")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        st.stop()

    st.success("✅ File uploaded successfully!")

    # Clean data
    df.columns = df.columns.str.strip().str.lower()
    st.write("### 📋 Preview of Uploaded Data")
    st.dataframe(df.head())

    if "class" not in df.columns or "employee name" not in df.columns or "attendance" not in df.columns:
        st.warning("⚠️ Your dataset must have columns: 'Class', 'Employee Name', and 'Attendance'.")
    else:
        # Tabs for organization
        tab1, tab2, tab3 = st.tabs(["🏫 Class Overview", "👥 Individual Ratings", "📈 Attendance Analytics"])

        # --- TAB 1: CLASS OVERVIEW ---
        with tab1:
            st.subheader("🏫 Attendance Summary by Class")
            class_summary = df.groupby("class")["attendance"].mean().reset_index()
            class_summary["attendance"] = class_summary["attendance"].round(2)

            st.dataframe(class_summary)

            fig, ax = plt.subplots()
            ax.bar(class_summary["class"], class_summary["attendance"])
            ax.set_title("Average Attendance Rate per Class")
            ax.set_ylabel("Attendance (%)")
            ax.set_xlabel("Class")
            st.pyplot(fig)

        # --- TAB 2: INDIVIDUAL RATINGS ---
        with tab2:
            st.subheader("👥 Employee Ratings")

            df["rating"] = df["attendance"].apply(
                lambda x: "🌟 Excellent" if x >= 95 else
                          "👍 Good" if x >= 85 else
                          "🟡 Fair" if x >= 70 else
                          "🔴 Needs Improvement"
            )

            st.dataframe(df[["employee name", "class", "attendance", "rating"]])

            class_filter = st.selectbox("🔎 Select Class to View Individual Ratings", df["class"].unique())
            filtered_df = df[df["class"] == class_filter]
            st.write(f"### 📚 Ratings for {class_filter}")
            st.dataframe(filtered_df[["employee name", "attendance", "rating"]])

        # --- TAB 3: ATTENDANCE ANALYTICS ---
        with tab3:
            st.subheader("📈 Attendance Analytics & Graphs")

            avg_attendance = df["attendance"].mean().round(2)
            st.metric("📊 Overall Average Attendance", f"{avg_attendance}%")

            # Line chart for trend (if dataset has date)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"], errors='coerce')
                st.write("### 📅 Attendance Trend Over Time")
                fig, ax = plt.subplots()
                for c in df["class"].unique():
                    class_data = df[df["class"] == c]
                    ax.plot(class_data["date"], class_data["attendance"], label=c)
                ax.legend()
                ax.set_title("Attendance Trend by Class")
                ax.set_ylabel("Attendance (%)")
                ax.set_xlabel("Date")
                st.pyplot(fig)
            else:
                st.info("📆 No date column found. Add one to view trends over time.")

else:
    st.info("👈 Please upload an attendance file in the sidebar to start.")
