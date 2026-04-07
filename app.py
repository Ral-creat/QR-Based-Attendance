"""
Scholar Attendance Tracker - QR Code + Excel System
Deployed on Streamlit Cloud
"""

import streamlit as st
import pandas as pd
import qrcode
from PIL import Image
import io
import base64
from datetime import datetime, timedelta
import numpy as np
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go

# Page config for GitHub deployment
st.set_page_config(
    page_title="📚 Scholar Tracker",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .stButton > button {
        border-radius: 10px;
        height: 45px;
        font-weight: bold;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
@st.cache_data
def init_session_state():
    if 'students_df' not in st.session_state:
        st.session_state.students_df = pd.DataFrame(columns=['student_id', 'name', 'phone', 'classes_attended', 'total_classes', 'attendance_pct'])
    if 'attendance_df' not in st.session_state:
        st.session_state.attendance_df = pd.DataFrame()
    if 'classes' not in st.session_state:
        st.session_state.classes = []
    return True

init_session_state()

@st.cache_data
def generate_class_schedule(months=6):
    """Generate 2nd & 3rd Saturdays for next X months"""
    today = datetime.now()
    classes = []
    
    for month_offset in range(months):
        # Month start (1st of month)
        month_start = datetime(today.year, today.month + month_offset, 1)
        
        # Find first Saturday
        days_to_first_sat = (5 - month_start.weekday()) % 7
        first_sat = month_start + timedelta(days=days_to_first_sat)
        
        # 2nd Saturday
        second_sat = first_sat + timedelta(days=7)
        if second_sat.date() >= today.date():
            classes.append({
                'class_id': f"C{len(classes)+1:02d}",
                'date': second_sat.strftime('%Y-%m-%d'),
                'name': f"Class {len(classes)+1} (2nd Sat)",
                'full_date': second_sat
            })
        
        # 3rd Saturday
        third_sat = second_sat + timedelta(days=7)
        if third_sat.date() >= today.date():
            classes.append({
                'class_id': f"C{len(classes)+1:02d}",
                'date': third_sat.strftime('%Y-%m-%d'),
                'name': f"Class {len(classes)+1} (3rd Sat)",
                'full_date': third_sat
            })
    return pd.DataFrame(classes)

def create_student_qr(student_id, student_name, phone=""):
    """Generate QR code with student details"""
    qr_data = f"ID:{student_id}|NAME:{student_name}|PHONE:{phone}|SCHOLAR:2024"
    qr = qrcode.QRCode(version=1, box_size=8, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1f77b4", back_color="white")
    return img

# Header
st.markdown("""
# 📚 **Scholar Attendance Tracker**
*QR Code System | Excel Upload | Auto 2nd/3rd Saturday Classes*
""")

# Sidebar Controls
st.sidebar.title("⚙️ Dashboard Controls")
page_mode = st.sidebar.selectbox("Select Page:", 
                                ["📱 QR Attendance", "📊 Excel Upload", "📈 Reports", "🎫 QR Generator"])

# Generate Schedule Button (Always available)
if st.sidebar.button("🔄 Generate Next 6 Months Schedule", use_container_width=True):
    st.session_state.classes = generate_class_schedule()
    st.rerun()

# Main Pages
if page_mode == "📱 QR Attendance":
    st.header("🎫 Live QR Code Attendance")
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.subheader("👥 Quick Student Add")
        with st.form("quick_add"):
            name = st.text_input("Student Name")
            phone = st.text_input("Phone (optional)")
            if st.form_submit_button("➕ Add Student"):
                if name:
                    new_id = f"S{len(st.session_state.students_df) + 1:03d}"
                    new_student = pd.DataFrame([{
                        'student_id': new_id,
                        'name': name,
                        'phone': phone,
                        'classes_attended': 0,
                        'total_classes': len(st.session_state.classes),
                        'attendance_pct': 0
                    }])
                    st.session_state.students_df = pd.concat([
                        st.session_state.students_df, new_student
                    ], ignore_index=True)
                    st.success(f"✅ Added {name} (ID: {new_id})")
                    st.rerun()
    
    with col2:
        st.subheader("📱 Scan QR Code")
        uploaded_file = st.file_uploader("Upload QR Image", type=['png','jpg','jpeg'])
        
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="📷 Scanned QR", use_column_width=True)
            
            # Check today's class
            today_str = datetime.now().strftime('%Y-%m-%d')
            today_class = st.session_state.classes[
                st.session_state.classes['date'] == today_str
            ]
            
            if not today_class.empty:
                class_info = today_class.iloc[0]
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("📅 Today's Class", class_info['name'])
                with col_b:
                    if st.button("✅ MARK PRESENT", use_container_width=True):
                        # Simulate QR parsing - REPLACE WITH REAL QR SCANNER
                        student_id = f"S{np.random.randint(1,10):03d}"
                        student = st.session_state.students_df[
                            st.session_state.students_df['student_id'] == student_id
                        ]
                        
                        if not student.empty:
                            st.session_state.students_df.loc[
                                st.session_state.students_df['student_id'] == student_id, 
                                'classes_attended'
                            ] += 1
                            st.balloons()
                            st.success(f"✅ {student_id} marked present for {class_info['name']}!")
                            st.rerun()
                        else:
                            st.error("❌ Student ID not found!")
            else:
                st.warning("⚠️ No class scheduled for today")

elif page_mode == "📊 Excel Upload":
    st.header("📁 Bulk Excel Attendance Upload")
    
    # Excel template download
    with open("data/attendance_template.xlsx", "rb") as f:
        st.download_button(
            "📥 Download Template",
            f.read(),
            "attendance_template.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    uploaded_file = st.file_uploader("📤 Upload Excel File", type=['xlsx'])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write("**Uploaded Data Preview:**")
        st.dataframe(df.head(10))
        
        if st.button("🚀 Process Attendance Data", type="primary", use_container_width=True):
            # Process and update main dataframe
            for _, row in df.iterrows():
                student_id = row.get('student_id', '')
                student_row = st.session_state.students_df[
                    st.session_state.students_df['student_id'] == student_id
                ]
                
                if not student_row.empty:
                    idx = student_row.index[0]
                    st.session_state.students_df.at[idx, 'classes_attended'] += 1
            
            # Update percentages
            st.session_state.students_df['attendance_pct'] = (
                st.session_state.students_df['classes_attended'] / 
                st.session_state.students_df['total_classes'] * 100
            ).fillna(0)
            
            st.success(f"✅ Processed {len(df)} records!")
            st.rerun()

elif page_mode == "🎫 QR Generator":
    st.header("🎨 Bulk QR Code Generator")
    
    if st.session_state.students_df.empty:
        st.warning("👆 Add students first from QR Attendance page!")
    else:
        st.dataframe(st.session_state.students_df[['student_id', 'name', 'phone']])
        
        if st.button("🖨️ Generate All QR Codes", use_container_width=True):
            for idx, student in st.session_state.students_df.iterrows():
                qr_img = create_student_qr(student['student_id'], student['name'], student['phone'])
                
                st.markdown(f"### {student['name']} (ID: {student['student_id']})")
                st.image(qr_img, use_column_width=True)
                
                # Individual download
                buf = BytesIO()
                qr_img.save(buf, format='PNG')
                st.download_button(
                    f"💾 Download {student['student_id']}",
                    buf.getvalue(),
                    f"QR_{student['student_id']}.png",
                    "image/png",
                    use_container_width=True
                )

elif page_mode == "📈 Reports":
    st.header("📊 Complete Analytics Dashboard")
    
    # Metrics Row
    if not st.session_state.students_df.empty:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="font-size: 2.5rem;">{len(st.session_state.students_df)}</h2>
                <p>Total Students</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="font-size: 2.5rem;">{len(st.session_state.classes)}</h2>
                <p>Scheduled Classes</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            avg_pct = st.session_state.students_df['attendance_pct'].mean()
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="font-size: 2.5rem;">{avg_pct:.1f}%</h2>
                <p>Avg Attendance</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            perfect = len(st.session_state.students_df[
                st.session_state.students_df['attendance_pct'] == 100
            ])
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="font-size: 2.5rem;">{perfect}</h2>
                <p>Perfect Score</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            total_attended = st.session_state.students_df['classes_attended'].sum()
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="font-size: 2.5rem;">{int(total_attended)}</h2>
                <p>Total Attendances</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Charts
        col1, col2 = st.columns(2)
        with col1:
            fig = px.histogram(
                st.session_state.students_df, 
                x='attendance_pct',
                nbins=20,
                title="Attendance Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            top10 = st.session_state.students_df.nlargest(10, 'attendance_pct')
            fig = px.bar(
                top10, x='name', y='attendance_pct',
                title="🏆 Top 10 Students",
                color='attendance_pct',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed Table
        st.subheader("📋 Complete Student Report")
        st.dataframe(
            st.session_state.students_df.sort_values('attendance_pct', ascending=False),
            use_container_width=True
        )
        
        # Download Reports
        col1, col2 = st.columns(2)
        with col1:
            csv_buffer = BytesIO()
            st.session_state.students_df.to_csv(csv_buffer, index=False)
            st.download_button(
                "📥 Download CSV Report",
                csv_buffer.getvalue(),
                "scholar_report.csv",
                "text/csv"
            )
        
        with col2:
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                st.session_state.students_df.to_excel(writer, sheet_name='Students', index=False)
                if not st.session_state.classes.empty:
                    st.session_state.classes.to_excel(writer, sheet_name='Schedule', index=False)
            st.download_button(
                "📥 Download Excel Report",
                excel_buffer.getvalue(),
                "scholar_complete_report.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Show Schedule
if not st.session_state.classes.empty:
    st.sidebar.markdown("### 📅 Upcoming Classes")
    st.sidebar.dataframe(st.session_state.classes[['class_id', 'name', 'date']].head())

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    🚀 Powered by <a href='https://streamlit.io' target='_blank'>Streamlit</a> | 
    📱 QR Attendance System | 
    Deployed on Streamlit Cloud
</div>
""", unsafe_allow_html=True)
