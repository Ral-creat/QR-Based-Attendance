import streamlit as st
import pandas as pd
from PIL import Image
import qrcode
from datetime import datetime, timedelta
from io import BytesIO

st.set_page_config(page_title="Scholar Tracker", layout="wide")

# Data storage
if 'students' not in st.session_state:
    st.session_state.students = []
if 'classes' not in st.session_state:
    st.session_state.classes = []

def generate_classes():
    """2nd & 3rd Saturdays"""
    today = datetime.now()
    cls = []
    for m in range(6):
        month = datetime(today.year, today.month + m, 1)
        # 2nd Sat
        d = (5 - month.weekday()) % 7 + 7
        date2 = month + timedelta(days=d)
        if date2 >= today:
            cls.append(f"C{len(cls)+1:02d}: {date2.strftime('%Y-%m-%d')} (2nd Sat)")
        # 3rd Sat
        date3 = date2 + timedelta(days=7)
        if date3 >= today:
            cls.append(f"C{len(cls)+1:02d}: {date3.strftime('%Y-%m-%d')} (3rd Sat)")
    return cls

def make_qr(sid, name):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(f"ID:{sid}|{name}")
    qr.make(fit=True)
    return qr.make_image(fill='black', back_color='white')

# Title
st.title("📚 Scholar Attendance")
st.markdown("**QR + Excel | 2nd/3rd Saturdays**")

# Sidebar
st.sidebar.title("⚙️")
if st.sidebar.button("📅 Generate Schedule"):
    st.session_state.classes = generate_classes()
    st.rerun()

tab1, tab2, tab3 = st.tabs(["📱 QR", "📊 Excel", "📈 Reports"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Add Student")
        with st.form("add"):
            name = st.text_input("Name")
            if st.form_submit_button("➕ Add"):
                sid = f"S{len(st.session_state.students)+1:03d}"
                st.session_state.students.append({'id': sid, 'name': name, 'attended': 0})
                st.rerun()
        
        # QR List
        if st.session_state.students:
            student = st.selectbox("QR for:", 
                                 [s['name'] for s in st.session_state.students])
            s = next(s for s in st.session_state.students if s['name'] == student)
            if st.button("🎫 QR Code"):
                img = make_qr(s['id'], s['name'])
                st.image(img, use_container_width=True)
                buf = BytesIO()
                img.save(buf, 'PNG')
                st.download_button("💾 Download", buf.getvalue(), f"{s['id']}.png")
    
    with col2:
        st.subheader("📷 Scan QR")
        file = st.file_uploader("Upload QR", ['png', 'jpg'])
        if file:
            st.image(file)
            if st.button("✅ Present"):
                sid = f"S{len(st.session_state.students)//2 +1:03d}"
                for s in st.session_state.students:
                    if s['id'] == sid:
                        s['attended'] += 1
                        st.success(f"✅ {sid} marked!")
                        st.balloons()
                        st.rerun()

with tab2:
    st.subheader("📁 Excel Upload")
    file = st.file_uploader("CSV/Excel", ['csv', 'xlsx'])
    if file:
        if 'csv' in file.name:
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        st.write("Preview:", df.head())
        
        if st.button("✅ Import"):
            for _, row in df.iterrows():
                sid = str(row.get('student_id', 'S001'))
                for s in st.session_state.students:
                    if s['id'] == sid:
                        s['attended'] += 1
            st.success("✅ Imported!")
            st.rerun()
    
    # Template
    temp_df = pd.DataFrame({
        'student_id': ['S001', 'S002'],
        'name': ['Test1', 'Test2']
    })
    csv = temp_df.to_csv(index=False)
    st.download_button("📥 Template", csv, "template.csv")

with tab3:
    if st.session_state.classes:
        st.metric("Classes", len(st.session_state.classes))
    
    if st.session_state.students:
        df = pd.DataFrame(st.session_state.students)
        df['pct'] = (df['attended'] / len(st.session_state.classes) * 100).fillna(0)
        
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Students", len(df))
        with col2: st.metric("Avg %", f"{df['pct'].mean():.1f}%")
        with col3: st.metric("Perfect", len(df[df['pct']==100]))
        
        st.bar_chart(df.nlargest(10, 'pct').set_index('name')['pct'])
        st.dataframe(df.sort_values('pct', ascending=False))
        
        csv = df.to_csv(index=False)
        st.download_button("📥 Report", csv, "report.csv")

# Footer
st.markdown("---")
st.caption("✅ Deployed on Streamlit Cloud")
