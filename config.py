import mysql.connector
import streamlit as st

def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",        # change if needed
            password="",        # your MySQL password
            database="floodalert_db"
        )
        return conn
    except mysql.connector.Error as e:
        st.error(f"Database connection failed: {e}")
        return None
