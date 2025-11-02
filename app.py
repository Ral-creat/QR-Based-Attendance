import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Attendance Monitoring System", layout="wide")

# --- SIDEBAR: UPLOAD DATASET ---
st.sidebar.header("📂 Upload Attendance Dataset")

uploaded_file = st.sidebar.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        df.columns = [c.strip().lower() for c in df.columns]
        st.sidebar.success("✅ File uploaded successfully!")
    except Exception as e:
        st.sidebar.error(f"❌ Error reading file: {e}")
        st.stop()
else:
    df = None
    st.sidebar.info("📎 Please upload your attendance dataset.")

# --- MAIN TITLE ---
st.markdown("<h2 style='text-align:center;'>📊 Automated Attendance Monitoring System</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray;'>Upload your attendance file from the sidebar to analyze class summaries, employee ratings, and visual analytics.</p>", unsafe_allow_html=True)

# --- TABS ---
tab_class, tab_individual, tab_overall = st.tabs([
    "🏫 Class Summary",
    "👤 Individual Ratings",
    "📈 Overall Analytics"
])

# ==========================================================
# 🏫 TAB 1: CLASS SUMMARY
# ==========================================================
with tab_class:
    st.subheader("🏫 Class Attendance Overview")

    if df is not None:
        required_cols = ["employee_id", "name", "status", "date"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"⚠️ Missing columns! Required: {required_cols}")
        else:
            if "class" in df.columns:
                selected_class = st.selectbox("🎓 Select Class", sorted(df["class"].unique()))
                class_df = df[df["class"] == selected_class]

                st.markdown(f"### 📋 Attendance Summary for **{selected_class}**")
                st.dataframe(class_df, use_container_width=True, height=350)

                # Summary stats
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
        st.info("⬅️ Upload a dataset in the sidebar to view this section.")

# ==========================================================
# 👤 TAB 2: INDIVIDUAL RATINGS
# ==========================================================
with tab_individual:
    st.subheader("👤 Employee Attendance Ratings")

    if df is not None:
        rating_map = {"Absent": 1, "Late": 2, "On Time": 3}
        df["rating_score"] = df["status"].map(rating_map).fillna(0)

        rating_summary = (
            df.groupby(["employee_id", "name"])[["rating_score"]]
            .mean()
            .reset_index()
            .sort_values(by="rating_score", ascending=False)
        )

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

        if "class" in df.columns:
            emp_class = df.groupby(["employee_id", "name"])["class"].first().reset_index()
            rating_summary = pd.merge(rating_summary, emp_class, on=["employee_id", "name"], how="left")

        st.markdown("### ⭐ Rating Summary Table")
        st.dataframe(rating_summary, use_container_width=True, height=350)

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

        st.download_button(
            label="⬇️ Download Ratings (CSV)",
            data=rating_summary.to_csv(index=False).encode("utf-8"),
            file_name="employee_ratings.csv",
            mime="text/csv",
        )
    else:
        st.info("⬅️ Upload a dataset in the sidebar to view ratings.")

# ==========================================================
# 📈 TAB 3: OVERALL ANALYTICS
# ==========================================================
with tab_overall:
    st.subheader("📈 Attendance Analytics Overview")

    if df is not None:
        overall_summary = df["status"].value_counts().reset_index()
        overall_summary.columns = ["Status", "Count"]

        col1, col2 = st.columns(2)
        with col1:
            pie_chart = px.pie(overall_summary, names="Status", values="Count", title="Overall Attendance Distribution")
            st.plotly_chart(pie_chart, use_container_width=True)
        with col2:
            bar_chart = px.bar(overall_summary, x="Status", y="Count", title="Overall Attendance Count", color="Status")
            st.plotly_chart(bar_chart, use_container_width=True)

        if "class" in df.columns:
            st.markdown("### 🏫 Class-Level Comparison")
            class_summary = df.groupby("class")["status"].value_counts().unstack().fillna(0)
            st.dataframe(class_summary, use_container_width=True, height=300)
            class_chart = px.bar(class_summary, barmode="group", title="Class-Wise Attendance Comparison")
            st.plotly_chart(class_chart, use_container_width=True)
    else:
        st.info("⬅️ Upload a dataset in the sidebar to see analytics.")
