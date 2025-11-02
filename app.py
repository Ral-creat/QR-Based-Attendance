import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Attendance Monitoring System", layout="wide")

# --- APP TITLE ---
st.markdown("<h2 style='text-align:center;'>📊 Automated Attendance Monitoring System</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray;'>Upload your dataset to view class summaries, ratings, and analytics.</p>", unsafe_allow_html=True)

# --- TABS ---
tab_upload, tab_class, tab_individual, tab_overall = st.tabs([
    "📂 Upload Dataset", 
    "🏫 Class Summary", 
    "👤 Individual Ratings", 
    "📈 Overall Analytics"
])

# --- SESSION DATA ---
if "attendance_data" not in st.session_state:
    st.session_state["attendance_data"] = None

# ==========================================================
# 📂 TAB 1: UPLOAD DATASET
# ==========================================================
with tab_upload:
    st.subheader("📤 Upload Attendance File")

    uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])

    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")
            st.stop()

        # Clean column names
        df.columns = [c.strip().lower() for c in df.columns]
        required_cols = ["employee_id", "name", "status", "date"]

        if not all(col in df.columns for col in required_cols):
            st.error(f"⚠️ Missing columns. Required: {required_cols}")
        else:
            st.success("✅ File uploaded successfully!")
            st.session_state["attendance_data"] = df
            st.dataframe(df, use_container_width=True, height=400)
            st.info("💡 Tip: Include a 'class' column for group-based analytics.")
    else:
        st.info("📎 Please upload your attendance dataset to get started.")

# ==========================================================
# 🏫 TAB 2: CLASS SUMMARY
# ==========================================================
with tab_class:
    st.subheader("🏫 Class Attendance Overview")

    df = st.session_state["attendance_data"]
    if df is not None:
        if "class" in df.columns:
            selected_class = st.selectbox("🎓 Select Class", sorted(df["class"].unique()))

            class_df = df[df["class"] == selected_class]

            st.markdown(f"### 📋 Attendance Summary for **{selected_class}**")
            st.dataframe(class_df, use_container_width=True, height=350)

            # --- Charts ---
            class_summary = class_df["status"].value_counts().reset_index()
            class_summary.columns = ["Status", "Count"]

            col1, col2 = st.columns(2)
            with col1:
                pie_chart = px.pie(class_summary, names="Status", values="Count", title="Status Distribution")
                st.plotly_chart(pie_chart, use_container_width=True)
            with col2:
                bar_chart = px.bar(class_summary, x="Status", y="Count", title="Attendance Count", color="Status")
                st.plotly_chart(bar_chart, use_container_width=True)
        else:
            st.warning("⚠️ The dataset doesn’t include a 'class' column.")
    else:
        st.info("Please upload data first in the 'Upload Dataset' tab.")

# ==========================================================
# 👤 TAB 3: INDIVIDUAL RATINGS
# ==========================================================
with tab_individual:
    st.subheader("👤 Employee Attendance Ratings")

    df = st.session_state["attendance_data"]

    if df is not None:
        # Rating logic
        rating_map = {"Absent": 1, "Late": 2, "On Time": 3}
        df["rating_score"] = df["status"].map(rating_map).fillna(0)

        # Average per employee
        rating_summary = (
            df.groupby(["employee_id", "name"])[["rating_score"]]
            .mean()
            .reset_index()
            .sort_values(by="rating_score", ascending=False)
        )

        # Rating labels
        def label_rating(score):
            if score >= 2.5:
                return "Excellent"
            elif score >= 1.8:
                return "Good"
            elif score >= 1:
                return "Needs Improvement"
            else:
                return "Poor"

        rating_summary["Rating"] = rating_summary["rating_score"].apply(label_rating)

        # Add class if available
        if "class" in df.columns:
            emp_class = df.groupby(["employee_id", "name"])["class"].first().reset_index()
            rating_summary = pd.merge(rating_summary, emp_class, on=["employee_id", "name"], how="left")

        st.dataframe(rating_summary, use_container_width=True, height=350)

        # Individual performance viewer
        st.markdown("### 🔎 View Individual Performance")
        selected_emp = st.selectbox("Select Employee:", rating_summary["name"].unique())

        emp_data = df[df["name"] == selected_emp]

        emp_chart = px.bar(
            emp_data,
            x="date",
            y="status",
            color="status",
            title=f"Attendance Record for {selected_emp}",
        )
        st.plotly_chart(emp_chart, use_container_width=True)

        # Download
        st.download_button(
            label="⬇️ Download Ratings (CSV)",
            data=rating_summary.to_csv(index=False).encode("utf-8"),
            file_name="employee_ratings.csv",
            mime="text/csv",
        )
    else:
        st.info("Upload your dataset first to calculate ratings.")

# ==========================================================
# 📈 TAB 4: OVERALL ANALYTICS
# ==========================================================
with tab_overall:
    st.subheader("📈 Attendance Analytics Overview")

    df = st.session_state["attendance_data"]

    if df is not None:
        overall_summary = df["status"].value_counts().reset_index()
        overall_summary.columns = ["Status", "Count"]

        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.pie(overall_summary, names="Status", values="Count", title="Overall Attendance Distribution")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.bar(overall_summary, x="Status", y="Count", title="Overall Status Count", color="Status")
            st.plotly_chart(fig2, use_container_width=True)

        if "class" in df.columns:
            st.markdown("### 🏫 Class Performance Overview")
            class_summary = df.groupby("class")["status"].value_counts().unstack().fillna(0)
            st.dataframe(class_summary, use_container_width=True, height=300)
            class_chart = px.bar(class_summary, barmode="group", title="Class-Wise Attendance Comparison")
            st.plotly_chart(class_chart, use_container_width=True)
    else:
        st.info("Upload your dataset first to view analytics.")
