import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="🎓 Student Org Management", layout="wide", page_icon="🧑‍🎓")

# --- SIDEBAR: NAVIGATION ---
st.sidebar.title("Navigation")
nav = st.sidebar.radio("Go to:", ["Dashboard", "Members", "Attendance", "Organizations", "Analytics"])

# --- LOAD DATA (CSV/Excel) ---
uploaded_file = st.sidebar.file_uploader("Upload Members Dataset", type=["csv", "xlsx"])
if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
    df.columns = [c.strip().lower() for c in df.columns]
else:
    df = None

# ========================
# DASHBOARD
# ========================
if nav == "Dashboard":
    st.title("🎓 Organization Management Dashboard")
    if df is not None:
        st.metric("Total Members", df.shape[0])
        if "organization" in df.columns:
            org_count = df["organization"].nunique()
            st.metric("Total Organizations", org_count)
        if "spiritual_community" in df.columns:
            spiritual_count = df["spiritual_community"].nunique()
            st.metric("Spiritual Communities", spiritual_count)
    else:
        st.info("⬅️ Upload a dataset to see dashboard metrics.")

# ========================
# MEMBERS
# ========================
elif nav == "Members":
    st.title("🧑‍🎓 Members Directory")
    if df is not None:
        st.dataframe(df, use_container_width=True)
        search_name = st.text_input("Search Member by Name")
        if search_name:
            st.dataframe(df[df['name'].str.contains(search_name, case=False)])
    else:
        st.info("⬅️ Upload a dataset to view members.")

# ========================
# ATTENDANCE
# ========================
elif nav == "Attendance":
    st.title("🗓️ Member Attendance")
    if df is not None and "attendance" in df.columns:
        st.dataframe(df[["name","attendance"]].sort_values(by="attendance", ascending=False))
        att_chart = px.bar(df, x="name", y="attendance", color="organization",
                           title="Attendance per Member")
        st.plotly_chart(att_chart, use_container_width=True)
    else:
        st.warning("⚠️ Dataset must include an 'attendance' column.")

# ========================
# ORGANIZATIONS
# ========================
elif nav == "Organizations":
    st.title("🏢 Organizations Overview")
    if df is not None and "organization" in df.columns:
        org_summary = df["organization"].value_counts().reset_index()
        org_summary.columns = ["Organization", "Members"]
        st.dataframe(org_summary)
        st.plotly_chart(px.pie(org_summary, names="Organization", values="Members", title="Members per Organization"), use_container_width=True)
    else:
        st.warning("⚠️ Dataset must include an 'organization' column.")

# ========================
# ANALYTICS
# ========================
elif nav == "Analytics":
    st.title("📈 Analytics Overview")
    if df is not None:
        if "attendance" in df.columns and "organization" in df.columns:
            fig = px.bar(df, x="organization", y="attendance", color="organization", 
                         title="Average Attendance per Organization")
            st.plotly_chart(fig, use_container_width=True)
        if "spiritual_community" in df.columns:
            sp_count = df["spiritual_community"].value_counts().reset_index()
            sp_count.columns = ["Spiritual Community", "Members"]
            st.plotly_chart(px.bar(sp_count, x="Spiritual Community", y="Members", color="Spiritual Community",
                                   title="Members per Spiritual Community"), use_container_width=True)
    else:
        st.info("⬅️ Upload a dataset to see analytics.")
