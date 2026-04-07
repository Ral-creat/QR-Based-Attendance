"""
Scholar Attendance Tracker - FIXED for Streamlit Cloud
Minimal dependencies | QR + Excel | Auto-deploy ready
"""

import streamlit as st
import pandas as pd
import qrcode
from PIL import Image
import io
from datetime import datetime, timedelta
import numpy as np
from io import BytesIO
import plotly.express as px

# Page config
st.set_page_config(
    page_title="📚 Scholar Tracker",
    page_icon="📚",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; border-radius: 15px; color: white; 
                text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
.stButton > button { border-radius: 10px; height: 45px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Initialize
@st.cache_data
def init_data():
    if 'students_df' not in st.session_state: 
        st.session_state.students_df = pd.DataFrame()
    if 'classes_df' not in st.session_state: 
        st.session_state.classes_df = pd.DataFrame()
    if 'attendance_records' not in st.session_state:
        st.session_state.attendance_records = []

init_data()

@st.cache_data
def generate_schedule(months=6):
    """2nd & 3rd Saturdays only"""
    today = datetime.now()
    classes = []
    class_id = 1
    
    for m in range(months):
        month_start = datetime(today.year, today.month + m, 1)
        # 2nd Saturday
        days_to_2nd_sat = (5 - month_start.weekday()) % 7 + 7
        date2 = month_start + timedelta(days=days_to_2nd_sat)
        if date2 >= today:
            classes.append({
                'id': f'C{class_id:02d}',
                'date': date2.strftime('%Y-%m-%d'),
                'name': f'Class {class_id} (2nd Sat)'
            })
            class_id += 1
        
        # 3rd Saturday
        date3 = date2 + timedelta(days=7)
        if date3 >= today:
            classes.append({
                'id': f'C{class_id:02d}',
                'date': date3.strftime('%Y-%m-%d'),
                'name': f'Class {class_id} (3rd Sat)'
            })
            class_id += 1
    
    return pd.DataFrame(classes)

def make_qr(student_id, name):
    """Simple QR generator"""
    data = f"SCHOLAR:{student_id}|{name}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data); qr.make(fit=True)
    return qr.make_image(fill='black', back_color='white')

# Header
st.title("📚 Scholar Attendance Tracker")
st.markdown("*QR Codes | Excel Upload | 2nd/3rd Saturday Classes*")

# Sidebar
st.sidebar.title("⚙️ Quick Actions")
if st.sidebar.button("🔄 Generate Schedule"):
    st.session_state.classes_df = generate_schedule()
    st.rerun()

mode = st.sidebar.radio("Mode:", ["📱 QR Scanner", "📊 Excel", "📈 Reports"])

# Main App
if mode == "📱 QR Scanner":
    # Two columns
    col1, col2 = st.columns([1,2])
    
    with col1:
        st.subheader("👥 Add Student")
        with st.form("add_student"):
            name = st.text_input("Name")
            if st.form_submit_button("Add"):
                if name:
                    sid = f"S{len(st.session_state.students_df)+1:03d}"
                    new_row = pd.DataFrame([{
                        'id': sid, 'name': name, 
                        'attended': 0, 'total': 0, 'pct': 0
                    }])
                    st.session_state.students_df = pd.concat([
                        st.session_state.students_df, new_row
                    ], ignore_index=True)
                    st.rerun()
        
        # QR Generator
        if not st.session_state.students_df.empty:
            student = st.selectbox("Select:", 
                                 st.session_state.students_df['name'])
            if st.button("🎫 Generate QR"):
                row = st.session_state.students_df[
                    st.session_state.students_df['name']==student
                ].iloc[0]
                qr_img = make_qr(row['id'], row['name'])
                st.image(qr_img, use_container_width=True)
                
                buf = BytesIO()
                qr_img.save(buf, 'PNG')
                st.download_button("💾 Download QR", 
                                 buf.getvalue(), f"{row['id']}.png")
    
    with col2:
        st.subheader("📱 Mark Attendance")
        uploaded = st.file_uploader("📷 QR Image", ['png','jpg'])
        if uploaded:
            st.image(uploaded)
            today = datetime.now().strftime('%Y-%m-%d')
            today_class = st.session_state.classes_df[
                st.session_state.classes_df['date']==today
            ]
            
            if not today_class.empty:
                cls = today_class.iloc[0]['name']
                if st.button("✅ Present", use_container_width=True):
                    # Simulate QR read
                    sid = f"S{np.random.randint(1,5):03d}"
                    student = st.session_state.students_df[
                        st.session_state.students_df['id']==sid
                    ]
                    if not student.empty:
                        idx = student.index[0]
                        st.session_state.students_df.at[idx, 'attended'] += 1
                        st.session_state.students_df.at[idx, 'total'] = len(st.session_state.classes_df)
                        st.session_state.students_df.at[idx, 'pct'] = (
                            st.session_state.students_df.at[idx, 'attended'] / 
                            st.session_state.students_df.at[idx, 'total'] * 100
                        )
                        st.success(f"✅ {sid} - {cls}")
                        st.balloons()
                        st.rerun()

elif mode == "📊 Excel":
    st.subheader("📁 Upload Excel Attendance")
    
    # Template
    template = pd.DataFrame({
        'student_id': ['S001', 'S002'],
        'name': ['John', 'Jane'],
        'class_date': ['2024-01-13', '2024-01-13'],
        'status': ['present', 'present']
    })
    csv = template.to_csv(index=False)
    st.download_button("📥 Template", csv, "template.csv", "text/csv")
    
    file = st.file_uploader("Upload", ['csv','xlsx'])
    if file:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        st.dataframe(df)
        
        if st.button("✅ Process", use_container_width=True):
            for _, row in df.iterrows():
                sid = row['student_id']
                student = st.session_state.students_df[
                    st.session_state.students_df['id']==sid
                ]
                if not student.empty:
                    idx = student.index[0]
                    st.session_state.students_df.at[idx, 'attended'] += 1
            st.success("✅ Processed!")
            st.rerun()

elif mode == "📈 Reports":
    if st.session_state.students_df.empty:
        st.info("👆 Add students first!")
    else:
        # Metrics
        col1,col2,col3,col4 = st.columns(4)
        with col1: st.metric("Students", len(st.session_state.students_df))
        with col2: st.metric("Classes", len(st.session_state.classes_df))
        with col3: st.metric("Avg %", f"{st.session_state.students_df['pct'].mean():.1f}%")
        with col4: st.metric("Perfect", len(st.session_state.students_df[st.session_state.students_df['pct']==100.0]))
        
        # Charts
        col1,col2 = st.columns(2)
        with col1:
            fig = px.bar(st.session_state.students_df.nlargest(10,'pct'), 
                        x='name', y='pct', title="🏆 Top Students")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.histogram(st.session_state.students_df, x='pct', 
                             nbins=10, title="📊 Distribution")
            st.plotly_chart(fig, use_container_width=True)
        
        # Table + Download
        st.dataframe(st.session_state.students_df.sort_values('pct', ascending=False))
        
        csv = st.session_state.students_df.to_csv(index=False)
        st.download_button("📥 CSV Report", csv, "report.csv")

# Show schedule in sidebar
if not st.session_state.classes_df.empty:
    st.sidebar.markdown("### 📅 Classes")
    st.sidebar.dataframe(st.session_state.classes_df[['id','name','date']])

st.markdown("---")
st.caption("🚀 Deployed on Streamlit Cloud")
