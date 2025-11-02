import streamlit as st
import qrcode
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
camera_input = st.camera_input("📷 I-scan ang imong QR code diri")

if camera_input:
    img = Image.open(camera_input)
    img_np = np.array(img)

    # Use OpenCV’s built-in QR decoder
    qr_detector = cv2.QRCodeDetector()
    data, points, _ = qr_detector.detectAndDecode(img_np)

    if data:
        user_id = data.strip()
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time_in = now.strftime("%H:%M:%S")

        rating = "On Time" if now.time() <= official_time else "Late"

        # Get user info
        c.execute("SELECT name, group_name FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()

        if result:
            name, group_name = result
            c.execute("SELECT * FROM attendance WHERE user_id=? AND date=?", (user_id, date))
            if not c.fetchone():
                c.execute("INSERT INTO attendance VALUES (?, ?, ?, ?, ?, ?)",
                          (user_id, name, group_name, date, time_in, rating))
                conn.commit()
                st.success(f"✅ {name} ({group_name}) marked {rating} at {time_in}")
            else:
                st.info(f"🕒 {name} already scanned today.")
        else:
            st.error("❌ QR not registered.")
    else:
        st.warning("No QR code detected. Try again.")

from PIL import Image
import io
import os
import plotly.express as px

# ---------- DATABASE ----------
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()

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
    rating TEXT
)
''')

conn.commit()

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="QR Attendance System", layout="wide")
st.title("📸 QR Code Attendance Monitoring System")

menu = ["🏠 Home", "🧍 Register User", "📱 Scan Attendance", "📊 Dashboard"]
choice = st.sidebar.radio("Navigate", menu)

# ---------- HOME ----------
if choice == "🏠 Home":
    st.subheader("Welcome 👋")
    st.write("""
        This system tracks attendance using **QR codes**,  
        automatically rates each scan as **On Time** or **Late**,  
        and provides analytics per group and overall attendance trends.
    """)
    st.info("Use the sidebar to navigate between pages.")

# ---------- REGISTER USER ----------
elif choice == "🧍 Register User":
    st.subheader("Register New User")

    name = st.text_input("Full Name")
    user_id = st.text_input("User ID (e.g., STUD001)")
    group_name = st.text_input("Group / Section (e.g., BSIS 3A)")

    if st.button("Generate QR Code"):
        if name and user_id and group_name:
            c.execute("INSERT OR REPLACE INTO users (user_id, name, group_name) VALUES (?, ?, ?)",
                      (user_id, name, group_name))
            conn.commit()

            # Generate QR
            os.makedirs("qr_codes", exist_ok=True)
            qr_img = qrcode.make(user_id)
            qr_path = f"qr_codes/{user_id}.png"
            qr_img.save(qr_path)

            st.image(qr_path, caption=f"QR Code for {name}", width=200)
            st.success(f"✅ {name} registered under {group_name}")
            st.download_button("📥 Download QR Code", data=open(qr_path, "rb"),
                               file_name=f"{user_id}.png")
        else:
            st.warning("Please fill out all fields before generating QR.")

# ---------- SCAN ATTENDANCE ----------
elif choice == "📱 Scan Attendance":
    st.subheader("Scan QR Code to Log Attendance")
    st.info("Align your QR code with the camera below 👇")

    official_time = st.time_input("Set Official Time-In", value=datetime.strptime("08:00", "%H:%M").time())

    camera_input = st.camera_input("Scan your QR Code")

    if camera_input:
        img = Image.open(camera_input)
        img_np = np.array(img)
        codes = decode(img_np)

        if codes:
            for code in codes:
                user_id = code.data.decode('utf-8')
                now = datetime.now()
                date = now.strftime("%Y-%m-%d")
                time_in = now.strftime("%H:%M:%S")

                # Compare time
                rating = "On Time" if now.time() <= official_time else "Late"

                # Get name + group
                c.execute("SELECT name, group_name FROM users WHERE user_id = ?", (user_id,))
                result = c.fetchone()

                if result:
                    name, group_name = result
                    # Prevent multiple scans in a day
                    c.execute("SELECT * FROM attendance WHERE user_id=? AND date=?", (user_id, date))
                    if not c.fetchone():
                        c.execute("INSERT INTO attendance VALUES (?, ?, ?, ?, ?, ?)",
                                  (user_id, name, group_name, date, time_in, rating))
                        conn.commit()
                        st.success(f"✅ {name} ({group_name}) marked {rating} at {time_in}")
                    else:
                        st.info(f"🕒 {name} already scanned today.")
                else:
                    st.error("❌ QR not registered.")
        else:
            st.warning("No QR code detected. Try again.")

# ---------- DASHBOARD ----------
elif choice == "📊 Dashboard":
    st.subheader("📊 Attendance Dashboard")

    df = pd.read_sql_query("SELECT * FROM attendance", conn)
    if df.empty:
        st.info("No attendance records yet.")
    else:
        # Show raw data
        with st.expander("📋 View Attendance Records"):
            st.dataframe(df)

        # --- Chart 1: Attendance Count by Group ---
        group_count = df.groupby("group_name")["user_id"].nunique().reset_index()
        group_count.columns = ["Group", "Unique Attendees"]
        fig1 = px.bar(group_count, x="Group", y="Unique Attendees",
                      title="Attendance Count by Group", color="Group")
        st.plotly_chart(fig1, use_container_width=True)

        # --- Chart 2: On Time vs Late ---
        rating_count = df["rating"].value_counts().reset_index()
        rating_count.columns = ["Rating", "Count"]
        fig2 = px.pie(rating_count, names="Rating", values="Count",
                      title="On-Time vs Late Attendance", color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig2, use_container_width=True)

        # --- Chart 3: Attendance Trend ---
        trend = df.groupby("date")["user_id"].count().reset_index()
        trend.columns = ["Date", "Total Attendance"]
        fig3 = px.line(trend, x="Date", y="Total Attendance",
                       title="Attendance Trend Over Time", markers=True)
        st.plotly_chart(fig3, use_container_width=True)

        # --- Download CSV ---
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Attendance CSV", data=csv, file_name="attendance_logs.csv")
