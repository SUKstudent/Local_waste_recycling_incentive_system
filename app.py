import streamlit as st
import pandas as pd
import random
import string
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="Recycle Rewards",
    layout="wide",
    page_icon="♻️"
)

# -----------------------------
# Sidebar: Logo + Description
# -----------------------------
st.sidebar.image("GreenBin.jpg", width=200)
st.sidebar.markdown("""
# ♻️ Recycle Rewards
Ek local waste recycling incentive system. 
Submit karo apna waste aur earn points!  
""")

# -----------------------------
# Dark Theme CSS
# -----------------------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #121212; color: #ffffff; }
input, textarea, select { background-color: #333333 !important; color: #ffffff !important; border-radius: 5px !important; border: 1px solid #555555 !important; padding: 0.5em !important; }
.stButton>button { background-color: #2e7d32 !important; color: white !important; width: 100% !important; height: 3em !important; border-radius: 5px !important; font-weight: bold !important; }
.stAlert { background-color: #2a2a2a !important; color: #fff !important; }
hr { border-color: #2e7d32; margin-top: 0.5rem; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Project Title
# -----------------------------
st.markdown("""
<h1 style="color:#2e7d32; margin-bottom: 0; font-weight: 900;">
♻️ Local Waste Recycling Incentive System
</h1>
<hr>
""", unsafe_allow_html=True)

# -----------------------------
# Helper Functions
# -----------------------------
def generate_user_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_otp(length=4):
    return ''.join(random.choices(string.digits, k=length))

# -----------------------------
# Session State Init
# -----------------------------
if 'users_df' not in st.session_state:
    st.session_state['users_df'] = pd.DataFrame(columns=['user_id','name','mobile','area','total_points'])
if 'collectors_df' not in st.session_state:
    st.session_state['collectors_df'] = pd.DataFrame([
        {'collector_id':101,'name':'Officer Rajesh','assigned_area':'Market','total_points':0},
        {'collector_id':102,'name':'Officer Anita','assigned_area':'Residential Apartment Complex','total_points':0},
        {'collector_id':103,'name':'Officer Sam','assigned_area':'Hospital','total_points':0},
        {'collector_id':104,'name':'Officer Priya','assigned_area':'Office Complex','total_points':0},
        {'collector_id':105,'name':'Officer Vikram','assigned_area':'Industrial Area','total_points':0}
    ])
if 'submissions_df' not in st.session_state:
    st.session_state['submissions_df'] = pd.DataFrame(columns=[
        'submission_id','user_id','collector_id','waste_type','quantity','points','status','category','timestamp','area'
    ])
st.session_state.setdefault('otp_sent', False)
st.session_state.setdefault('otp_value', '')
st.session_state.setdefault('logged_in', False)
st.session_state.setdefault('current_user', {})

# -----------------------------
# Logout
# -----------------------------
if st.session_state['logged_in']:
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['current_user'] = {}
        st.experimental_rerun()

# -----------------------------
# User Portal
# -----------------------------
st.subheader("User Portal")

# Login / Register
if not st.session_state['logged_in']:
    tab1, tab2 = st.tabs(["Login", "Register"])

    # LOGIN
    with tab1:
        login_mobile = st.text_input("Mobile Number", placeholder="e.g. 9876543210")
        if st.button("Login"):
            users = st.session_state['users_df']
            if not users.empty and login_mobile in users['mobile'].values:
                user_data = users[users['mobile'] == login_mobile].iloc[0]
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = {
                    'name': user_data['name'],
                    'mobile': user_data['mobile'],
                    'area': user_data['area']
                }
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("User not found. Please register first.")

    # REGISTER
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            u_name = st.text_input("Full Name", key="reg_name")
            u_mobile = st.text_input("Mobile Number", key="reg_mobile")
        with col2:
            u_area = st.selectbox("Your Area", ["--Select area--",
                "Residential Apartment Complex", "Hospital", "Shopping Mall",
                "Office Complex", "Market", "Industrial Area"])
        if st.button("Send OTP"):
            if not u_name or not u_mobile or u_area=="--Select area--":
                st.error("Fill all details before sending OTP")
            else:
                st.session_state['otp_value'] = generate_otp()
                st.session_state['otp_sent'] = True
                st.success(f"OTP sent to {u_mobile} ✅ (Auto verified for demo)")

        if st.session_state['otp_sent']:
            st.info(f"OTP **{st.session_state['otp_value']}** auto-verified ✅")
            if u_mobile not in st.session_state['users_df']['mobile'].values:
                new_user = {'user_id': generate_user_id(), 'name': u_name, 'mobile': u_mobile,
                            'area': u_area, 'total_points': 0}
                st.session_state['users_df'] = pd.concat([st.session_state['users_df'], pd.DataFrame([new_user])], ignore_index=True)
            st.success("Registration successful! You can now login.")
            st.session_state['otp_sent'] = False

# -----------------------------
# Logged In User
# -----------------------------
else:
    user = st.session_state['current_user']
    st.success(f"Logged in as: {user['name']} | Area: {user['area']}")

    assigned = st.session_state['collectors_df'][st.session_state['collectors_df']['assigned_area'] == user['area']]
    if not assigned.empty:
        st.info(f"Your Collector Assigned: **{assigned.iloc[0]['name']}** 🚚 En route...")

    # Waste Submission Form (All 5 types at once)
    with st.form("waste_form"):
        waste_types = ['Plastic','Paper','Organic','Metal','Glass']
        quantities = {}
        for w in waste_types:
            quantities[w] = st.number_input(f"{w} (kg)", min_value=0.0, step=0.1, key=w)
        submitted = st.form_submit_button("Submit All Waste")
        if submitted:
            points_map = {'Plastic':2,'Paper':2,'Organic':2,'Metal':2,'Glass':2}  # realistic points
            total_points = sum(points_map[w] for w in waste_types if quantities[w]>0)
            timestamp = datetime.now()
            for w in waste_types:
                if quantities[w]>0:
                    category = "Wet" if w=="Organic" else "Dry"
                    area_match = assigned.sort_values('total_points').iloc[0]
                    c_id, c_name = area_match['collector_id'], area_match['name']
                    idx = st.session_state['collectors_df'].loc[st.session_state['collectors_df']['collector_id']==c_id].index[0]
                    st.session_state['collectors_df'].at[idx,'total_points'] += points_map[w]

                    u_idx = st.session_state['users_df'].loc[st.session_state['users_df']['mobile']==user['mobile']].index[0]
                    st.session_state['users_df'].at[u_idx,'total_points'] += points_map[w]

                    new_sub = {'submission_id': len(st.session_state['submissions_df'])+1,
                               'user_id': user['mobile'], 'collector_id': c_id, 'waste_type': w,
                               'quantity': quantities[w], 'points': points_map[w], 'status':"Proper",
                               'category': category, 'timestamp': timestamp, 'area': user['area']}
                    st.session_state['submissions_df'] = pd.concat([st.session_state['submissions_df'], pd.DataFrame([new_sub])], ignore_index=True)
            st.success(f"Submitted 5 waste types! Total Points Earned: {total_points}")
            st.balloons()
            st.experimental_rerun()

    # -----------------------------
    # Dashboard
    # -----------------------------
    st.markdown("---")
    st.header("📊 Recycling Dashboard")
    df = st.session_state['submissions_df']
    collectors = st.session_state['collectors_df']
    users = st.session_state['users_df']

    # Filters
    st.sidebar.subheader("Filters")
    area_filter = st.sidebar.multiselect("Select Area", options=df['area'].unique() if not df.empty else [], default=None)
    day_filter = st.sidebar.date_input("Select Date", value=date.today())

    filtered_df = df.copy()
    if area_filter:
        filtered_df = filtered_df[filtered_df['area'].isin(area_filter)]
    filtered_df = filtered_df[pd.to_datetime(filtered_df['timestamp']).dt.date == day_filter]

    tabs = st.tabs(["Metrics","Collector Table","Area-wise Waste","Segregation Status","Daily Trends","Leaderboard"])

    # 1️⃣ Metrics
    with tabs[0]:
        total_waste = filtered_df['quantity'].sum() if not filtered_df.empty else 0
        total_points = filtered_df['points'].sum() if not filtered_df.empty else 0
        total_submissions = len(filtered_df)
        proper_count = filtered_df[filtered_df['status']=="Proper"].shape[0] if not filtered_df.empty else 0
        improper_count = filtered_df[filtered_df['status']=="Improper"].shape[0] if not filtered_df.empty else 0
        proper_pct = (proper_count/(proper_count+improper_count)*100) if (proper_count+improper_count)>0 else 0
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Waste (kg)", f"{total_waste:.2f}")
        col2.metric("Total Points", f"{total_points}")
        col3.metric("Submissions", f"{total_submissions}")
        col4.metric("Proper Segregation %", f"{proper_pct:.1f}%")

    # 2️⃣ Collector Table
    with tabs[1]:
        st.subheader("Collector Performance")
        st.table(collectors[['name','assigned_area','total_points']].sort_values('total_points', ascending=False).reset_index(drop=True))

    # 3️⃣ Area-wise Waste (Bar)
    with tabs[2]:
        if not filtered_df.empty:
            area_waste = filtered_df.groupby('area')['quantity'].sum().reset_index()
            fig_area = px.bar(area_waste, x='area', y='quantity', text='quantity', color='area', title="Waste Collected per Area")
            fig_area.update_traces(texttemplate='%{text:.2f} kg', textposition='outside')
            st.plotly_chart(fig_area, use_container_width=True)

    # 4️⃣ Segregation Donut
    with tabs[3]:
        if not filtered_df.empty:
            status_df = filtered_df['status'].value_counts().reset_index()
            status_df.columns=['status','count']
            fig_status = go.Figure(data=[go.Pie(labels=status_df['status'], values=status_df['count'], hole=0.5)])
            fig_status.update_traces(marker=dict(colors=['#27ae60','#c0392b']), textinfo='label+percent')
            st.plotly_chart(fig_status, use_container_width=True)

    # 5️⃣ Daily Trends (Line)
    with tabs[4]:
        if not filtered_df.empty:
            filtered_df['date'] = pd.to_datetime(filtered_df['timestamp']).dt.date
            line_df = filtered_df.groupby(['date','area'])['quantity'].sum().reset_index()
            fig_trends = px.line(line_df, x='date', y='quantity', color='area', markers=True, title="Daily Collection Trends")
            st.plotly_chart(fig_trends, use_container_width=True)

    # 6️⃣ Leaderboard
    with tabs[5]:
        if not users.empty:
            st.subheader("Community Leaderboard")
            top_users = users.sort_values('total_points', ascending=False).head(10)
            st.table(top_users[['name','area','total_points']].reset_index(drop=True))
