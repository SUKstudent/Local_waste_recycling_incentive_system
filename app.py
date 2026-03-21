import streamlit as st
import pandas as pd
import random
import string
from datetime import datetime
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
# Project Title
# -----------------------------
st.markdown("""
<h1 style="color:#2e7d32; margin-bottom: 0; font-weight: 900; text-align:center;">
♻️ Local Waste Recycling Incentive System
</h1>
<hr>
""", unsafe_allow_html=True)

# -----------------------------
# Sidebar: Logo + Description + Logout
# -----------------------------
st.sidebar.image("GreenBin.jpg", width=250)  # Increased width

st.sidebar.markdown("""
### ♻️ Recycle Rewards
Encouraging recycling and proper segregation.
Earn points for your contributions and climb the leaderboard!
""")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['current_user'] = {}

if st.session_state['logged_in']:
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['current_user'] = {}
        st.experimental_rerun()

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
    st.session_state['users_df'] = pd.DataFrame(columns=['user_id','name','mobile','area','total_points','improper_count'])
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

# -----------------------------
# Default Area-wise Wastes
# -----------------------------
area_waste_default = {
    "Residential Apartment Complex":["Plastic","Paper","Organic","Metal","Glass"],
    "Hospital":["Plastic","Paper","Organic","Metal","Glass"],
    "Shopping Mall":["Plastic","Paper","Organic","Metal","Glass"],
    "Office Complex":["Plastic","Paper","Metal","Glass"],
    "Market":["Plastic","Paper","Organic","Glass"],
    "Industrial Area":["Plastic","Paper","Organic","Metal","Glass"]
}

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
            if not users.empty:
                matched_users = users[users['mobile'] == login_mobile]
                if not matched_users.empty:
                    user_data = matched_users.iloc[0]
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
            else:
                st.error("No users registered yet. Please register first.")

    # REGISTER
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            u_name = st.text_input("Full Name", key="reg_name")
            u_mobile = st.text_input("Mobile Number", key="reg_mobile")
        with col2:
            u_area = st.selectbox("Your Area", ["--Select area--"] + list(area_waste_default.keys()))
        if u_area != "--Select area--":
            st.info("Collector will be assigned after registration.")

        if st.button("Send OTP"):
            if not u_name or not u_mobile or u_area == "--Select area--":
                st.error("Fill all details before sending OTP")
            else:
                st.session_state['otp_value'] = generate_otp()
                st.session_state['otp_sent'] = True
                st.success(f"OTP sent to {u_mobile} ✅ (Auto verified for demo)")

        if st.session_state.get('otp_sent', False):
            st.info(f"OTP **{st.session_state['otp_value']}** auto-verified ✅")
            if u_mobile not in st.session_state['users_df']['mobile'].values:
                new_user = {'user_id': generate_user_id(), 'name': u_name, 'mobile': u_mobile,
                            'area': u_area, 'total_points': 0, 'improper_count': 0}
                st.session_state['users_df'] = pd.concat([st.session_state['users_df'], pd.DataFrame([new_user])], ignore_index=True)
            st.success("Registration successful! You can now login.")
            st.session_state['otp_sent'] = False

else:
    user = st.session_state['current_user']
    st.success(f"Logged in as: {user['name']} | Area: {user['area']}")
    
    # Show area-wise default wastes
    st.subheader("Waste Types in Your Area")
    st.table(pd.DataFrame([{"Waste Types":", ".join(area_waste_default[user['area']])}]))

    # Multi-waste submission
    st.subheader("Submit Your Wastes")
    submitted_wastes = {}
    for w_type in area_waste_default[user['area']]:
        qty = st.number_input(f"Quantity of {w_type} (kg)", min_value=0.0, step=0.1)
        if qty > 0:
            submitted_wastes[w_type] = qty

    if st.button("Submit All Wastes"):
        if submitted_wastes:
            collector_row = st.session_state['collectors_df'][st.session_state['collectors_df']['assigned_area'] == user['area']].iloc[0]
            total_points = 0
            for w_type, w_qty in submitted_wastes.items():
                category = "Wet" if w_type=="Organic" else "Dry"
                points_map = {'Plastic':10, 'Paper':5, 'Organic':2, 'Metal':12, 'Glass':8}
                earned = w_qty * points_map[w_type]
                total_points += earned
                new_sub = {'submission_id': len(st.session_state['submissions_df'])+1,
                           'user_id': user['mobile'], 'collector_id': collector_row['collector_id'],
                           'waste_type': w_type, 'quantity': w_qty, 'points': earned,
                           'status': "Proper", 'category': category,
                           'timestamp': datetime.now(), 'area': user['area']}
                st.session_state['submissions_df'] = pd.concat([st.session_state['submissions_df'], pd.DataFrame([new_sub])], ignore_index=True)
            # Update user & collector points
            user_idx = st.session_state['users_df'][st.session_state['users_df']['mobile']==user['mobile']].index[0]
            st.session_state['users_df'].at[user_idx, 'total_points'] += total_points
            collector_idx = st.session_state['collectors_df'][st.session_state['collectors_df']['collector_id']==collector_row['collector_id']].index[0]
            st.session_state['collectors_df'].at[collector_idx, 'total_points'] += total_points
            st.success(f"Submitted {len(submitted_wastes)} waste types! Total Points Earned: {total_points}")
