import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="BarangayConnect", page_icon="🏘️", layout="wide")

# --- CUSTOM STYLE ---
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- INIT CSV STORAGE ---
if "posts.csv" not in os.listdir():
    posts_df = pd.DataFrame(columns=["ID", "Name", "Anonymous", "Barangay", "Category", "Message", "Date", "Status"])
    posts_df.to_csv("posts.csv", index=False)

if "comments.csv" not in os.listdir():
    comments_df = pd.DataFrame(columns=["Post_ID", "Name", "Comment", "Date"])
    comments_df.to_csv("comments.csv", index=False)

# --- LOAD DATA ---
posts = pd.read_csv("posts.csv")
comments = pd.read_csv("comments.csv")

# --- SIDEBAR NAV ---
st.sidebar.title("🏘️ BarangayConnect")
page = st.sidebar.radio("Go to", [
    "🏠 Home",
    "📝 Post an Issue",
    "📢 View Posts",
    "📊 Analytics",
    "🔐 Admin Panel"
])

# --- PAGE 1: HOME ---
if page == "🏠 Home":
    st.title("🏘️ BarangayConnect: Community Issue & Suggestion Board")
    st.markdown("""
    Welcome to **BarangayConnect**, an online platform for residents to share  
    their **issues, feedback, or suggestions** directly with the barangay. 💬  

    - Post anonymously or with your name  
    - Share suggestions, problems, or ideas  
    - Engage with comments and official replies  
    - Admins can approve and moderate posts  
    """)

# --- PAGE 2: POST AN ISSUE ---
elif page == "📝 Post an Issue":
    st.title("📝 Share Your Concern or Suggestion")
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
                st.success("✅ Your post has been submitted and is awaiting approval!")

# --- PAGE 3: VIEW POSTS (with comments) ---
elif page == "📢 View Posts":
    st.title("📢 Community Posts & Suggestions")
    approved_posts = posts[posts["Status"] == "Approved"]
    
    if approved_posts.empty:
        st.info("No approved posts yet.")
    else:
        for _, row in approved_posts.iterrows():
            with st.container():
                st.markdown(f"""
                ### 👤 {row['Name']} ({row['Barangay']})
                🏷️ *{row['Category']}*  
                🕒 {row['Date']}  
                ---
                {row['Message']}
                """)

                # --- Display comments for this post ---
                post_comments = comments[comments["Post_ID"] == row["ID"]]
                if not post_comments.empty:
                    st.markdown("💬 **Comments:**")
                    for _, c in post_comments.iterrows():
                        st.markdown(f"- **{c['Name']}**: {c['Comment']}  ⏰ *{c['Date']}*")
                else:
                    st.caption("No comments yet. Be the first to reply!")

                # --- Comment Form ---
                with st.form(f"comment_form_{row['ID']}", clear_on_submit=True):
                    commenter = st.text_input("Your Name", key=f"name_{row['ID']}")
                    comment_text = st.text_area("Write a comment...", key=f"comment_{row['ID']}")
                    send = st.form_submit_button("💬 Post Comment")

                    if send:
                        if comment_text.strip() == "":
                            st.warning("Please write something before sending!")
                        else:
                            new_comment = pd.DataFrame([{
                                "Post_ID": row["ID"],
                                "Name": commenter if commenter else "Anonymous",
                                "Comment": comment_text,
                                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }])
                            new_comment.to_csv("comments.csv", mode="a", header=False, index=False)
                            st.success("✅ Comment added!")
                st.markdown("---")

# --- PAGE 4: ANALYTICS ---
elif page == "📊 Analytics":
    st.title("📊 Community Insights")
    approved = posts[posts["Status"] == "Approved"]

    if approved.empty:
        st.info("No data yet to analyze.")
    else:
        st.subheader("Posts by Category")
        cat_count = approved["Category"].value_counts().reset_index()
        cat_count.columns = ["Category", "Posts"]
        st.bar_chart(cat_count.set_index("Category"))

        st.subheader("Posts per Barangay")
        brgy_count = approved["Barangay"].value_counts().reset_index()
        brgy_count.columns = ["Barangay", "Posts"]
        st.bar_chart(brgy_count.set_index("Barangay"))

# --- PAGE 5: ADMIN PANEL ---
elif page == "🔐 Admin Panel":
    st.title("🔐 Admin Panel")
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
        approved = posts[posts["Status"] == "Approved"]
        st.dataframe(approved)

    elif password:
        st.error("Incorrect password ❌")
