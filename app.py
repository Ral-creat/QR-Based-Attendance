import streamlit as st
import cv2
import pandas as pd
import numpy as np
from datetime import datetime, time
from PIL import Image
import sqlite3
import plotly.express as px

# ✅ Must be first Streamlit command
st.set_page_config(page_title="QR Attendance System", layout="wide")

# --- Database setup ---
conn = sqlite3.connect("attendance.db", check_same_thread=False)
c = conn.cursor()

# Create tables if not exist
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    group_name TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS attendance (
    user_id TEXT,
    name TEXT,
    group_name TEXT,
    date TEXT,
    time_in TEXT,
    status TEXT
)
''')
conn.commit()

# --- Layout ---
st.title("📷 QR Code Attendance Monitoring System")
st.write("I-scan ang imong QR code aron ma-record ang imong attendance sa database.")

tab1, tab2, tab3 = st.tabs(["📸 Attendance", "👥 Manage Members", "📊 Summary Dashboard"])

# --- Attendance Tab ---
with tab1:
    st.subheader("Real-Time QR Scanning")
    camera_input = st.camera_input("📷 I-scan ang imong QR code diri")

    official_time = time(8, 0, 0)  # 8:00 AM cutoff

    if camera_input:
        img = Image.open(camera_input)
        img_np = np.array(img)

        qr_detector = cv2.QRCodeDetector()
        data, points, _ = qr_detector.detectAndDecode(img_np)

        if data:
            user_id = data.strip()
            now = datetime.now()
            date_today = now.strftime("%Y-%m-%d")
            time_in = now.strftime("%H:%M:%S")
            status = "On Time" if now.time() <= official_time else "Late"

            c.execute("SELECT name, group_name FROM users WHERE user_id=?", (user_id,))
            result = c.fetchone()

            if result:
                name, group_name = result
                c.execute("SELECT * FROM attendance WHERE user_id=? AND date=?", (user_id, date_today))
                if not c.fetchone():
                    c.execute("INSERT INTO attendance VALUES (?, ?, ?, ?, ?, ?)",
                              (user_id, name, group_name, date_today, time_in, status))
                    conn.commit()
                    st.success(f"✅ {name} ({group_name}) na-record as {status} at {time_in}")
                else:
                    st.info(f"🕒 {name} naka-scan na karon adlawa.")
            else:
                st.error("❌ Wala sa listahan ang QR code nga gi-scan.")
        else:
            st.warning("😅 Wala nakit-an nga QR code. Sulayi balik.")

# --- Manage Members Tab ---
with tab2:
    st.subheader("👥 I-manage ang mga miyembro")

    with st.form("add_member"):
        st.write("➕ Add new member")
        user_id = st.text_input("User ID (QR content)")
        name = st.text_input("Full Name")
        group_name = st.text_input("Group / Section")
        submitted = st.form_submit_button("Save")

        if submitted:
            if user_id and name and group_name:
                try:
                    c.execute("INSERT INTO users VALUES (?, ?, ?)", (user_id, name, group_name))
                    conn.commit()
                    st.success(f"✅ Successfully added {name}")
                except:
                    st.warning("⚠️ User ID already exists.")
            else:
                st.error("❌ Please fill out all fields.")

    st.divider()
    st.write("📋 Registered Members:")
    members = pd.read_sql("SELECT * FROM users", conn)
    st.dataframe(members)

# --- Summary Dashboard Tab ---
with tab3:
    st.subheader("📊 Attendance Summary")

    data = pd.read_sql("SELECT * FROM attendance", conn)
    if not data.empty:
        st.write("📅 Attendance Records:")
        st.dataframe(data)

        # Count status
        count_df = data.groupby("status").size().reset_index(name="count")
        fig = px.pie(count_df, names="status", values="count", title="Attendance Status Summary")
        st.plotly_chart(fig, use_container_width=True)

        # Daily summary
        daily = data.groupby("date").size().reset_index(name="scans")
        fig2 = px.bar(daily, x="date", y="scans", title="Daily Attendance Count")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No attendance records yet. Scan QR codes to start.")
