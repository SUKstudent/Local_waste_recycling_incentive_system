import streamlit as st
import pandas as pd
import random
import string
from datetime import datetime, date

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="Recycle Rewards", layout="wide", page_icon="♻️")

# -----------------------------
# Sidebar Logo + Description
# -----------------------------
st.sidebar.image("GreenBin.jpg", width=200)
st.sidebar.markdown("""
# ♻️ Recycle Rewards
Local waste recycling incentive system. Submit waste, earn points, and unlock badges!
""")

# -----------------------------
# Dark Theme CSS
# -----------------------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #121212; color: #ffffff; }
input, textarea, select { background-color: #333 !important; color: #fff !important; border-radius:5px !important; border:1px solid #555 !important; padding:0.5em !important;}
.stButton>button { background-color:#2e7d32 !important; color:white !important; width:100% !important; height:3em !important; border-radius:5px !important; font-weight:bold !important;}
.stAlert {background-color:#2a2a2a !important; color:#fff !important;}
hr {border-color:#2e7d32; margin-top:0.5rem; margin-bottom:1rem;}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Project Title
# -----------------------------
st.markdown("""
<h1 style="color:#2e7d32; margin-bottom:0; font-weight:900;">
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

def get_badge(points):
    if points <= 10:
        return "♻️ Newbie Recycler"
    elif points <= 20:
        return "🌱 Green Starter"
    elif points <= 50:
        return "🌿 Eco Warrior"
    elif points <= 100:
        return "🌳 Eco Hero"
    else:
        return "🏆 Recycling Master"

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

    # -----------------------------
    # Waste Submission Form
    # -----------------------------
    with st.form("waste_form"):
        waste_types = ['Plastic','Paper','Organic','Metal','Glass']
        quantities = {}
        improper_types = []
        contaminated_types = []
        for w in waste_types:
            quantities[w] = st.number_input(f"{w} (kg)", min_value=0.0, step=0.1, key=w)

        submitted = st.form_submit_button("Submit All Waste")
        if submitted:
            points_map = {'Plastic':2,'Paper':2,'Organic':2,'Metal':2,'Glass':2}
            daily_cap = 10
            today = date.today()
            # Points already earned today
            df = st.session_state['submissions_df']
            points_today = df[(df['user_id']==user['mobile']) & (pd.to_datetime(df['timestamp']).dt.date==today)]['points'].sum()
            total_points_earned = 0
            timestamp = datetime.now()

            # Simulate improper / contaminated for demo (optional)
            for w in waste_types:
                if quantities[w] > 0:
                    status = "Proper"
                    # Simple rule: Organic in Plastic → Contaminated
                    if w=="Plastic" and quantities.get("Organic",0)>0:
                        status = "Contaminated"
                        contaminated_types.append(w)
                    elif w=="Organic" and quantities.get("Plastic",0)>0:
                        status = "Improper"
                        improper_types.append(w)

                    base_points = points_map[w]
                    # Apply daily cap
                    remaining_points = max(0, daily_cap - points_today - total_points_earned)
                    points_awarded = min(base_points, remaining_points)
                    total_points_earned += points_awarded

                    # Update collector & user points
                    if not assigned.empty:
                        c_id = assigned.iloc[0]['collector_id']
                        idx = st.session_state['collectors_df'].loc[st.session_state['collectors_df']['collector_id']==c_id].index[0]
                        st.session_state['collectors_df'].at[idx,'total_points'] += points_awarded
                    u_idx = st.session_state['users_df'].loc[st.session_state['users_df']['mobile']==user['mobile']].index[0]
                    st.session_state['users_df'].at[u_idx,'total_points'] += points_awarded

                    # Deduct points for improper / contaminated
                    if status=="Improper":
                        st.session_state['users_df'].at[u_idx,'total_points'] = max(0, st.session_state['users_df'].at[u_idx,'total_points'] -2)
                    if status=="Contaminated":
                        st.session_state['users_df'].at[u_idx,'total_points'] = max(0, st.session_state['users_df'].at[u_idx,'total_points'] -3)

                    # Record submission
                    new_sub = {'submission_id': len(st.session_state['submissions_df'])+1,
                               'user_id': user['mobile'], 'collector_id': c_id if not assigned.empty else 0,
                               'waste_type': w, 'quantity': quantities[w], 'points': points_awarded,
                               'status':status, 'category': "Wet" if w=="Organic" else "Dry",
                               'timestamp': timestamp, 'area': user['area']}
                    st.session_state['submissions_df'] = pd.concat([st.session_state['submissions_df'], pd.DataFrame([new_sub])], ignore_index=True)

            # Show points earned + badge
            u_idx = st.session_state['users_df'].loc[st.session_state['users_df']['mobile']==user['mobile']].index[0]
            total_user_points = st.session_state['users_df'].at[u_idx,'total_points']
            badge = get_badge(total_user_points)
            st.success(f"Total Points Earned Today: {total_points_earned} ✅ Badge: {badge}")
            st.balloons()
            st.experimental_rerun()

    # -----------------------------
    # Dashboard
    # -----------------------------
    st.markdown("---")
    st.header("📊 Recycling Dashboard")
    df = st.session_state['submissions_df']
    users = st.session_state['users_df']

    # Leaderboard
    if not users.empty:
        st.subheader("Community Leaderboard")
        top_users = users.sort_values('total_points', ascending=False).head(10)
        st.table(top_users[['name','area','total_points']].reset_index(drop=True))

    # Show User Badge
    st.subheader("🏅 Your Badge")
    st.markdown(f"<h2 style='color:#2e7d32;'>{badge}</h2>", unsafe_allow_html=True)
