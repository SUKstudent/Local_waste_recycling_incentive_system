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
st.set_page_config(page_title="Recycle Rewards", layout="wide", page_icon="♻️")

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.markdown("""
<style>
.sidebar .sidebar-content img { width: 250px !important; display:block; margin:auto; }
.sidebar .sidebar-content { font-size:16px !important; line-height:1.5 !important; }
</style>
""", unsafe_allow_html=True)

st.sidebar.image("GreenBin.jpg", width=250)
st.sidebar.markdown("""
# ♻️ Recycle Rewards
Local waste recycling incentive system. Submit waste, earn points, and unlock badges!
""")

# -----------------------------
# Project Title (Pastel Green)
# -----------------------------
st.markdown("""
<h1 style="background-color:#A8E6CF; color:#2e7d32; padding:15px; border-radius:12px; text-align:center;">
♻️ Local Waste Recycling Incentive System
</h1>
""", unsafe_allow_html=True)

# -----------------------------
# Helper Functions
# -----------------------------
def generate_user_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_otp(length=4):
    return ''.join(random.choices(string.digits, k=length))

def get_progressive_badge(points):
    milestones = [5, 10, 20, 40, 80, 120, 160, 200]
    badges = ["♻️ Newbie Recycler", "🌱 Green Starter", "🌿 Eco Warrior", "🌳 Eco Hero",
              "🏆 Recycling Master", "🌟 Recycling Legend", "🏅 Recycling Champion", "⚡ Eco Titan"]
    last_badge = "🎉 Welcome Recycler"
    for milestone, badge in zip(milestones, badges):
        if points >= milestone:
            last_badge = badge
        else:
            break
    return last_badge

# -----------------------------
# Session State Init
# -----------------------------
if 'users_df' not in st.session_state:
    st.session_state['users_df'] = pd.DataFrame(columns=['user_id','name','mobile','area','total_points','badge'])
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
st.session_state.setdefault('current_badge', '🎉 Welcome Recycler')

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
                st.session_state['current_user'] = {'name': user_data['name'], 'mobile': user_data['mobile'], 'area': user_data['area']}
                st.session_state['current_badge'] = user_data['badge']
                st.success("Login successful!")
                st.experimental_rerun()
            else: st.error("User not found. Please register first.")
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
                new_user = {'user_id': generate_user_id(), 'name': u_name, 'mobile': u_mobile, 'area': u_area, 'total_points':0, 'badge':"🎉 Welcome Recycler"}
                st.session_state['users_df'] = pd.concat([st.session_state['users_df'], pd.DataFrame([new_user])], ignore_index=True)
            st.success("Registration successful! 🎉 You earned a Welcome Badge! You can now login.")
            st.session_state['otp_sent'] = False

# -----------------------------
# Logged In User
# -----------------------------
else:
    user = st.session_state['current_user']
    st.success(f"Logged in as: {user['name']} | Area: {user['area']}")
    page = st.sidebar.radio("Navigate", ["Submit Waste", "Dashboard & Leaderboard"])

    # -----------------------------
    # Submit Waste
    # -----------------------------
    if page=="Submit Waste":
        assigned = st.session_state['collectors_df'][st.session_state['collectors_df']['assigned_area']==user['area']]
        if not assigned.empty: st.info(f"Your Collector Assigned: **{assigned.iloc[0]['name']}** 🚚 En route...")
        with st.form("waste_form"):
            waste_types = ['Plastic','Paper','Organic','Metal','Glass']
            quantities = {}
            for w in waste_types: quantities[w] = st.number_input(f"{w} (kg)", min_value=0.0, step=0.1, key=w)
            submitted = st.form_submit_button("Submit All Waste")
            if submitted:
                points_map = {'Plastic':2,'Paper':2,'Organic':2,'Metal':2,'Glass':2}
                daily_cap = 10
                today = date.today()
                df = st.session_state['submissions_df']
                points_today = df[(df['user_id']==user['mobile']) & (pd.to_datetime(df['timestamp']).dt.date==today)]['points'].sum()
                total_points_earned = 0
                timestamp = datetime.now()
                for w in waste_types:
                    if quantities[w]>0:
                        status = "Proper"
                        if w=="Plastic" and quantities.get("Organic",0)>0: status="Contaminated"
                        elif w=="Organic" and quantities.get("Plastic",0)>0: status="Improper"
                        base_points = points_map[w]
                        remaining_points = max(0,daily_cap-points_today-total_points_earned)
                        points_awarded = min(base_points, remaining_points)
                        total_points_earned += points_awarded
                        if not assigned.empty:
                            c_id = assigned.iloc[0]['collector_id']
                            idx = st.session_state['collectors_df'].loc[st.session_state['collectors_df']['collector_id']==c_id].index[0]
                            st.session_state['collectors_df'].at[idx,'total_points'] += points_awarded
                        u_idx = st.session_state['users_df'].loc[st.session_state['users_df']['mobile']==user['mobile']].index[0]
                        st.session_state['users_df'].at[u_idx,'total_points'] += points_awarded
                        # Deduction
                        if status=="Improper": st.session_state['users_df'].at[u_idx,'total_points']=max(0,st.session_state['users_df'].at[u_idx,'total_points']-2)
                        if status=="Contaminated": st.session_state['users_df'].at[u_idx,'total_points']=max(0,st.session_state['users_df'].at[u_idx,'total_points']-3)
                        new_sub={'submission_id':len(st.session_state['submissions_df'])+1,'user_id':user['mobile'],
                                 'collector_id':c_id if not assigned.empty else 0,'waste_type':w,'quantity':quantities[w],
                                 'points':points_awarded,'status':status,'category':"Wet" if w=="Organic" else "Dry",
                                 'timestamp':timestamp,'area':user['area']}
                        st.session_state['submissions_df']=pd.concat([st.session_state['submissions_df'],pd.DataFrame([new_sub])],ignore_index=True)
                # Badge update
                u_idx = st.session_state['users_df'].loc[st.session_state['users_df']['mobile']==user['mobile']].index[0]
                total_user_points = st.session_state['users_df'].at[u_idx,'total_points']
                badge = get_progressive_badge(total_user_points)
                st.session_state['users_df'].at[u_idx,'badge']=badge
                st.session_state['current_badge']=badge
                st.success(f"Total Points Today: {total_points_earned} ✅ Current Badge: {badge}")
                st.balloons()
                st.experimental_rerun()

    # -----------------------------
    # Dashboard & Leaderboard (Donut + Bubble + Area KPI)
    # -----------------------------
    elif page=="Dashboard & Leaderboard":
        st.header("📊 Recycling Dashboard")
        df = st.session_state['submissions_df']
        users = st.session_state['users_df']

        # 1️⃣ Donut: Waste Type %
        if not df.empty:
            waste_df = df.groupby('waste_type')['quantity'].sum().reset_index()
            fig_waste = go.Figure(data=[go.Pie(labels=waste_df['waste_type'], values=waste_df['quantity'],
                                               hole=0.5, textinfo='label+percent')])
            st.subheader("Waste Type Distribution (%)")
            st.plotly_chart(fig_waste, use_container_width=True)

        # 2️⃣ Total Waste by Area (KPI Cards)
        if not df.empty:
            st.subheader("🟢 Total Waste Collected by Area (kg)")
            total_area_df = df.groupby('area')['quantity'].sum().reset_index()
            cols = st.columns(len(total_area_df))
            for col, (_, row) in zip(cols, total_area_df.iterrows()):
                col.metric(label=row['area'], value=f"{row['quantity']} kg")

        # 3️⃣ Segregation Status (Bubble Chart)
        if not df.empty:
            status_df = df['status'].value_counts().reset_index()
            status_df.columns = ['status','count']
            fig_status = px.scatter(status_df, x='status', y='count', size='count', color='status',
                                    size_max=100, title="Segregation Status Overview")
            st.subheader("Segregation Status Bubble Chart")
            st.plotly_chart(fig_status, use_container_width=True)

        # 4️⃣ Current User Points & Badge
        st.subheader("🏅 Your Points & Badge")
        u_idx = users.loc[users['mobile']==user['mobile']].index[0]
        user_points = users.at[u_idx,'total_points']
        user_badge = users.at[u_idx,'badge']
        st.markdown(f"""
**Name:** {user['name']}  
**Area:** {user['area']}  
**Total Points:** {user_points}  
**Badge:** {user_badge}  
""")
