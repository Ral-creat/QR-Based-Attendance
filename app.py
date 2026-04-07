import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
import qrcode
from PIL import Image

# Page config FIRST
st.set_page_config(page_title="📚 Scholar Tracker", layout="wide")

# PROPER Session State - SAFE INITIALIZATION
def init_session_state():
    defaults = {
        'students': [],
        'classes': [],
        'attendance': []
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

init_session_state()

@st.cache_data
def generate_classes():
    """Generate 2nd & 3rd Saturdays"""
    today = datetime.now()
    classes = []
    cid = 1
    for m in range(6):
        month_start = datetime(today.year, today.month + m, 1)
        # 2nd Saturday
        days_to_2nd = (5 - month_start.weekday()) % 7 + 7
        date2 = month_start + timedelta(days=days_to_2nd)
        if date2.date() >= today.date():
            classes.append({
                'id': f'C{cid:02d}',
                'date': date2.strftime('%Y-%m-%d'),
                'name': f'Class {cid} (2nd Sat)'
            })
            cid += 1
        # 3rd Saturday
        date3 = date2 + timedelta(days=7)
        if date3.date() >= today.date():
            classes.append({
                'id': f'C{cid:02d}',
                'date': date3.strftime('%Y-%m-%d'),
                'name': f'Class {cid} (3rd Sat)'
            })
            cid += 1
    return classes

def create_qr(student_id, name):
    """QR Code generator"""
    data = f"SCHOLAR:{student_id}|{name}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")

# Header
st.title("📚 Scholar Attendance System")
st.markdown("**QR Scanner | Excel Upload | Auto Schedule**")

# Sidebar
st.sidebar.title("🔧 Controls")
if st.sidebar.button("📅 Generate Schedule (2nd/3rd Sat)"):
    st.session_state.classes = generate_classes()
    st.rerun()

# Main Tabs
tab1, tab2, tab3 = st.tabs(["📱 QR Attendance", "📊 Excel Upload", "📈 Dashboard"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("👥 Manage Students")
        
        # Add student form
        with st.form(key="add_student"):
            name = st.text_input("Student Name")
            submitted = st.form_submit_button("➕ Add Student")
            if submitted and name:
                sid = f"S{len(st.session_state.students) + 1:03d}"
                st.session_state.students.append({
                    'id': sid,
                    'name': name,
                    'attended': 0,
                    'total_classes': len(st.session_state.classes)
                })
                st.success(f"✅ Added {name} (ID: {sid})")
                st.rerun()
        
        # Student list
        if st.session_state.students:
            st.subheader("🎫 Generate QR")
            selected = st.selectbox(
                "Select Student:",
                [s['name'] for s in st.session_state.students]
            )
            student = next(s for s in st.session_state.students if s['name'] == selected)
            
            if st.button("🎨 Create QR Code"):
                qr_image = create_qr(student['id'], student['name'])
                st.image(qr_image, caption=f"QR for {student['name']}", use_container_width=True)
                
                # Download
                buf = BytesIO()
                qr_image.save(buf, format='PNG')
                st.download_button(
                    label="💾 Download QR",
                    data=buf.getvalue(),
                    file_name=f"QR_{student['id']}_{student['name'].replace(' ', '_')}.png",
                    mime="image/png"
                )
    
    with col2:
        st.subheader("📷 QR Scanner")
        uploaded_file = st.file_uploader("📁 Upload QR Image", type=['png', 'jpg', 'jpeg'])
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Scanned QR", use_container_width=True)
            
            # Check today's class
            today = datetime.now().strftime('%Y-%m-%d')
            today_class = next((c for c in st.session_state.classes if c['date'] == today), None)
            
            if today_class:
                col1, col2 = st.columns(2)
                col1.metric("📅 Today", today_class['name'])
                
                if col2.button("✅ Mark Present", use_container_width=True):
                    # Simulate QR parsing (replace with real QR reader)
                    demo_id = f"S{len(st.session_state.students) % 3 + 1:03d}"
                    student = next((s for s in st.session_state.students if s['id'] == demo_id), None)
                    
                    if student:
                        student['attended'] += 1
                        st.success(f"✅ {demo_id} marked present for {today_class['name']}!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Student not found")
            else:
                st.warning("⚠️ No class today")

with tab2:
    st.subheader("📁 Excel Attendance Upload")
    
    # Download template
    template_data = {
        'student_id': ['S001', 'S002', 'S003'],
        'name': ['John Doe', 'Jane Smith', 'Bob Wilson'],
        'class_date': ['2024-01-13', '2024-01-13', '2024-01-20'],
        'status': ['present', 'present', 'absent']
    }
    template_df = pd.DataFrame(template_data)
    csv_buffer = BytesIO()
    template_df.to_csv(csv_buffer, index=False)
    st.download_button(
        "📥 Download Template",
        csv_buffer.getvalue(),
        "attendance_template.csv",
        "text/csv"
    )
    
    # Upload
    uploaded_file = st.file_uploader("📤 Upload CSV/Excel", type=['csv', 'xlsx'])
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.write("**Preview:**")
            st.dataframe(df.head())
            
            if st.button("🚀 Process Attendance", use_container_width=True):
                processed = 0
                for _, row in df.iterrows():
                    sid = str(row.get('student_id', ''))
                    for student in st.session_state.students:
                        if student['id'] == sid:
                            student['attended'] += 1
                            processed += 1
                
                st.success(f"✅ Processed {processed} records!")
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Upload error: {str(e)}")

with tab3:
    st.subheader("📊 Dashboard")
    
    # Update stats
    if st.session_state.students:
        df = pd.DataFrame(st.session_state.students)
        if st.session_state.classes:
            df['total_classes'] = len(st.session_state.classes)
            df['pct'] = (df['attended'] / df['total_classes'] * 100).fillna(0)
        else:
            df['pct'] = 0
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("👥 Students", len(df))
        col2.metric("📚 Classes", len(st.session_state.classes))
        avg_pct = df['pct'].mean()
        col3.metric("📈 Avg Attendance", f"{avg_pct:.1f}%")
        perfect = len(df[df['pct'] >= 95])
        col4.metric("🏆 Perfect", perfect)
        
        # Top performers
        st.subheader("🏆 Top Students")
        top_df = df.nlargest(10, 'pct')
        st.bar_chart(top_df.set_index('name')['pct'])
        
        # Full table
        st.subheader("📋 Complete Report")
        st.dataframe(df.sort_values('pct', ascending=False), use_container_width=True)
        
        # Downloads
        col1, col2 = st.columns(2)
        with col1:
            csv_data = df.to_csv(index=False)
            st.download_button(
                "📥 CSV Report",
                csv_data,
                "students_report.csv",
                "text/csv"
            )
        with col2:
            excel_data = BytesIO()
            with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Students', index=False)
                pd.DataFrame(st.session_state.classes).to_excel(writer, sheet_name='Classes', index=False)
            st.download_button(
                "📥 Excel Report",
                excel_data.getvalue(),
                "complete_report.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Show schedule
if st.session_state.classes:
    with st.expander("📅 Class Schedule"):
        schedule_df = pd.DataFrame(st.session_state.classes)
        st.dataframe(schedule_df)

# Footer
st.markdown("---")
st.markdown("*✅ QR Attendance System | Deployed on Streamlit Cloud*")
