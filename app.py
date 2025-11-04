import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="BarangayConnect", page_icon="🏘️", layout="wide")

# --- LOAD CSS ---
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- INIT STORAGE ---
if "posts.csv" not in os.listdir():
    posts_df = pd.DataFrame(columns=["ID", "Name", "Anonymous", "Barangay", "Category", "Message", "Date", "Status"])
    posts_df.to_csv("posts.csv", index=False)

if "comments.csv" not in os.listdir():
    comments_df = pd.DataFrame(columns=["Post_ID", "Name", "Comment", "Date"])
    comments_df.to_csv("comments.csv", index=False)

posts = pd.read_csv("posts.csv")
comments = pd.read_csv("comments.csv")

# --- NAVIGATION BAR ---
st.markdown("""
<div class='navbar'>
    <h1>🏘️ BarangayConnect</h1>
    <div class='nav-links'>
        <a href='/?nav=home'>Home</a>
        <a href='/?nav=post'>Post Issue</a>
        <a href='/?nav=view'>Community Wall</a>
        <a href='/?nav=analytics'>Analytics</a>
        <a href='/?nav=admin'>Admin</a>
    </div>
</div>
""", unsafe_allow_html=True)

# --- SIMPLE NAV SYSTEM ---
nav = st.query_params.get("nav", ["home"])[0]

# --- HOME ---
if nav == "home":
    st.markdown("""
    <div class='page'>
        <h2>Welcome to BarangayConnect 🌸</h2>
        <p>A safe digital space for residents to <b>share issues, ideas, or suggestions</b> 
        directly with their barangay. Connect, report, and be heard — all in one place.</p>
        <ul>
            <li>📮 Submit reports or suggestions</li>
            <li>🕵️ Post anonymously if you prefer</li>
            <li>💬 Comment or reply to others</li>
            <li>📊 See analytics of community concerns</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# --- POST ISSUE ---
elif nav == "post":
    st.markdown("<div class='page'><h2>📝 Submit a Community Concern</h2>", unsafe_allow_html=True)
    with st.form("post_form", clear_on_submit=True):
        name = st.text_input("Name (optional)")
        anonymous = st.checkbox("Post anonymously")
        brgy = st.text_input("Barangay / Area")
        category = st.selectbox("Category", [
            "Infrastructure", "Waste Management", "Peace & Order", "Health", 
            "Youth", "Environment", "Suggestion", "Other"
        ])
        msg = st.text_area("Describe your issue or suggestion")
        submitted = st.form_submit_button("📨 Submit Post")

        if submitted:
            if msg.strip() == "":
                st.warning("Please write something before submitting!")
            else:
                new_post = pd.DataFrame([{
                    "ID": int(datetime.now().timestamp()),
                    "Name": "Anonymous" if anonymous else name if name else "Anonymous",
                    "Anonymous": "Yes" if anonymous else "No",
                    "Barangay": brgy,
                    "Category": category,
                    "Message": msg,
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Status": "Pending"
                }])
                new_post.to_csv("posts.csv", mode="a", header=False, index=False)
                st.success("✅ Your post has been submitted for admin approval!")
    st.markdown("</div>", unsafe_allow_html=True)

# --- VIEW POSTS ---
elif nav == "view":
    st.markdown("<div class='page'><h2>📢 Community Wall</h2>", unsafe_allow_html=True)
    approved = posts[posts["Status"] == "Approved"]

    if approved.empty:
        st.info("No approved posts yet.")
    else:
        for _, row in approved.iterrows():
            st.markdown(f"""
            <div class='post-card'>
                <h4>👤 {row['Name']} <span class='brgy'>({row['Barangay']})</span></h4>
                <p class='category'>🏷️ {row['Category']} | 🕒 {row['Date']}</p>
                <p>{row['Message']}</p>
            </div>
            """, unsafe_allow_html=True)

            # comments
            post_comments = comments[comments["Post_ID"] == row["ID"]]
            if not post_comments.empty:
                for _, c in post_comments.iterrows():
                    st.markdown(f"<p class='comment'><b>{c['Name']}:</b> {c['Comment']} <span>🕒 {c['Date']}</span></p>", unsafe_allow_html=True)

            with st.form(f"comment_form_{row['ID']}", clear_on_submit=True):
                commenter = st.text_input("Your Name", key=f"name_{row['ID']}")
                comment_text = st.text_area("Write a comment...", key=f"comment_{row['ID']}")
                send = st.form_submit_button("💬 Comment")
                if send and comment_text.strip():
                    new_comment = pd.DataFrame([{
                        "Post_ID": row["ID"],
                        "Name": commenter if commenter else "Anonymous",
                        "Comment": comment_text,
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }])
                    new_comment.to_csv("comments.csv", mode="a", header=False, index=False)
                    st.success("✅ Comment added!")

# --- ANALYTICS ---
elif nav == "analytics":
    st.markdown("<div class='page'><h2>📊 Barangay Insights</h2>", unsafe_allow_html=True)
    approved = posts[posts["Status"] == "Approved"]
    if approved.empty:
        st.info("No data yet.")
    else:
        st.subheader("Posts by Category")
        cat_count = approved["Category"].value_counts().reset_index()
        cat_count.columns = ["Category", "Posts"]
        st.bar_chart(cat_count.set_index("Category"))

        st.subheader("Posts by Barangay")
        brgy_count = approved["Barangay"].value_counts().reset_index()
        brgy_count.columns = ["Barangay", "Posts"]
        st.bar_chart(brgy_count.set_index("Barangay"))
    st.markdown("</div>", unsafe_allow_html=True)

# --- ADMIN PANEL ---
elif nav == "admin":
    st.markdown("<div class='page'><h2>🔐 Admin Panel</h2>", unsafe_allow_html=True)
    password = st.text_input("Enter Admin Password:", type="password")
    if password == "admin123":
        st.success("Access granted ✅")
        st.subheader("Pending Posts")
        pending = posts[posts["Status"] == "Pending"]
        if pending.empty:
            st.info("No pending posts.")
        else:
            st.dataframe(pending)
            post_id = st.number_input("Enter Post ID to Approve/Delete:", min_value=0, step=1)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve Post"):
                    posts.loc[posts["ID"] == post_id, "Status"] = "Approved"
                    posts.to_csv("posts.csv", index=False)
                    st.success("Post approved successfully!")
            with col2:
                if st.button("🗑️ Delete Post"):
                    posts = posts[posts["ID"] != post_id]
                    posts.to_csv("posts.csv", index=False)
                    st.warning("Post deleted successfully!")
        st.subheader("Approved Posts")
        st.dataframe(posts[posts["Status"] == "Approved"])
    elif password:
        st.error("Incorrect password ❌")
    st.markdown("</div>", unsafe_allow_html=True)
