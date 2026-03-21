import streamlit as st
import pandas as pd
import random
import string
from datetime import datetime

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
st.sidebar.image("GreenBin.jpg", width=150)
st.sidebar.markdown("""
# ♻️ Recycle Rewards

This app encourages recycling by awarding points for waste submissions.

Register or login to start contributing!
""")

# -----------------------------
# Dark Theme CSS for main content
# -----------------------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background-color: #121212;
    color: #ffffff;
}
input, textarea, select {
    background-color: #333333 !important;
    color: #ffffff !important;
    border-radius: 5px !important;
    border: 1px solid #555555 !important;
    padding: 0.5em !important;
}
.stButton>button {
    background-color: #2e7d32 !important;
    color: white !important;
    width: 100% !important;
    height: 3em !important;
    border-radius: 5px !important;
    font-weight: bold !important;
}
.stAlert {
    background-color: #2a2a2a !important;
    color: #fff !important;
}
hr {
    border-color: #2e7d32;
    margin-top: 0.5rem;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Project Title above user portal
# -----------------------------
st.markdown("""
    <h1 style="color:#2e7d32; margin-bottom: 0; font-weight: 900;">
        ♻️ Local Waste Recycling Incentive System
    </h1>
    <hr>
""", unsafe_allow_html=True)

# -----------------------------
# Helper functions
# -----------------------------
def generate_user_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_otp(length=4):
    return ''.join(random.choices(string.digits, k=length))

# -----------------------------
# Initialize session state
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
st.session_state.setdefault('logged_in', False)
st.session_state.setdefault('current_user', {})

# -----------------------------
# Logout button
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

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            u_name = st.text_input("Full Name", key="reg_name")
            u_mobile = st.text_input("Mobile Number", key="reg_mobile")
        with col2:
            u_area = st.selectbox("Your Area", ["--Select area--",
                "Residential Apartment Complex", "Hospital", "Shopping Mall",
                "Office Complex", "Market", "Industrial Area"])
        if u_area != "--Select area--":
            st.info("Collector will be assigned after registration.")

        if st.button("Send OTP"):
            if not u_name or not u_mobile or u_area == "--Select area--":
                st.error("Fill all details before sending OTP")
            else:
                st.session_state['otp_value'] = generate_otp()
                st.session_state['otp_sent'] = True
                st.success(f"OTP sent to {u_mobile} ✅ (Auto verified for demo)")

        if st.session_state['otp_sent']:
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
    assigned = st.session_state['collectors_df'][st.session_state['collectors_df']['assigned_area'] == user['area']]
    if not assigned.empty:
        st.info(f"Your Collector Assigned: **{assigned.iloc[0]['name']}** 🚚 En route...")

    with st.form("waste_form"):
        w_type = st.selectbox("Waste Type", ['Plastic', 'Paper', 'Organic', 'Metal', 'Glass'])
        w_qty = st.number_input("Quantity (kg)", min_value=0.1, step=0.1)
        submitted = st.form_submit_button("Submit")
        if submitted:
            points_map = {'Plastic': 10, 'Paper': 5, 'Organic': 2, 'Metal': 12, 'Glass': 8}
            category = "Wet" if w_type == "Organic" else "Dry"
            earned = w_qty * points_map[w_type]

            area_match = st.session_state['collectors_df'][st.session_state['collectors_df']['assigned_area'] == user['area']]
            if not area_match.empty:
                selected = area_match.sort_values('total_points').iloc[0]
                c_id, c_name = selected['collector_id'], selected['name']
                idx = st.session_state['collectors_df'].loc[st.session_state['collectors_df']['collector_id'] == c_id].index[0]
                st.session_state['collectors_df'].at[idx, 'total_points'] += earned
            else:
                c_id, c_name = None, "Unassigned"

            u_idx = st.session_state['users_df'][st.session_state['users_df']['mobile'] == user['mobile']].index[0]
            st.session_state['users_df'].at[u_idx, 'total_points'] += earned

            new_sub = {'submission_id': len(st.session_state['submissions_df']) + 1,
                       'user_id': user['mobile'], 'collector_id': c_id, 'waste_type': w_type,
                       'quantity': w_qty, 'points': earned, 'status': "Proper",
                       'category': category, 'timestamp': datetime.now(), 'area': user['area']}
            st.session_state['submissions_df'] = pd.concat([st.session_state['submissions_df'], pd.DataFrame([new_sub])], ignore_index=True)

            st.balloons()
            st.success(f"Submitted! Collector **{c_name}** notified. Points earned: **{earned}**")
            st.experimental_rerun()
