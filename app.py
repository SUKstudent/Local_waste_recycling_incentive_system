import streamlit as st
import pandas as pd
import os
import random
import string
import plotly.express as px
from datetime import datetime

# -----------------------------
# Page config and theme
# -----------------------------
st.set_page_config(page_title="Local Waste Recycling", layout="wide")
st.markdown("""
<style>
.css-18ni7ap.e8zbici2 {background-color: #e6f7e6;}
.stButton button {background-color: #4CAF50; color: white;}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Helper functions
# -----------------------------
def generate_user_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def send_otp_simulation():
    otp = str(random.randint(1000, 9999))
    st.session_state['otp'] = otp
    st.session_state['otp_sent'] = True
    st.session_state['otp_input'] = otp
    st.info(f"OTP sent and auto-filled (Simulated): {otp}")
    return otp

# -----------------------------
# Initialize in-memory data
# -----------------------------
if 'users_df' not in st.session_state:
    st.session_state['users_df'] = pd.DataFrame(
        columns=['user_id','name','mobile','area','total_points','improper_count']
    )

if 'collectors_df' not in st.session_state:
    st.session_state['collectors_df'] = pd.DataFrame([
        {'collector_id':1,'name':'Collector A','assigned_area':'Residential Apartment Complex','total_points':0,'ratings':[]},
        {'collector_id':2,'name':'Collector B','assigned_area':'Market','total_points':0,'ratings':[]}
    ])

if 'submissions_df' not in st.session_state:
    st.session_state['submissions_df'] = pd.DataFrame(
        columns=['submission_id','user_id','collector_id','waste_type','quantity','points','status','category','timestamp']
    )

# -----------------------------
# Sidebar logo
# -----------------------------
logo_path = "GreenBin.jpg"
fallback_logo_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Recycle_symbol.svg/600px-Recycle_symbol.svg.png"

if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=180)
else:
    st.sidebar.image(fallback_logo_url, width=180)
    st.sidebar.warning("Local logo not found! Using fallback logo.")

# -----------------------------
# Sidebar navigation
# -----------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", [
    "Login / Waste Submission",
    "User Leaderboard",
    "User Dashboard"
])

# -----------------------------
# Session state defaults
# -----------------------------
for key in ['otp_sent','otp_verified','otp_input','logged_in','current_user']:
    if key not in st.session_state:
        st.session_state[key] = False if 'otp' not in key and 'logged_in' not in key else ""

# -----------------------------
# Page: Login / Waste Submission
# -----------------------------
if page == "Login / Waste Submission":
    st.title("⚡ Local Waste & Recycling Incentive System")

    st.subheader("User Login / Registration")
    mobile = st.text_input("Mobile Number")
    name = st.text_input("Name")
    area_options = ['--Select your area--','Residential Apartment Complex','Hospital','Shopping Mall','Office Complex',
                    'Market','School/College','Railway Station','Bus Terminal','Industrial Area','Hotel']
    area = st.selectbox("Select your area", area_options)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Send/Resend OTP"):
            if mobile:
                send_otp_simulation()
            else:
                st.error("Enter mobile number!")

    with col2:
        otp_input = st.text_input("Enter OTP")
        if st.session_state.get('otp_sent', False) and st.session_state.get('otp_input'):
            if st.session_state['otp_input'] == st.session_state.get('otp'):
                st.session_state['otp_verified'] = True
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = {'mobile': mobile, 'name': name, 'area': area}
                st.success("OTP Verified ✅")
            else:
                st.warning("Incorrect OTP")

    # -----------------------------
    # Welcome message and submission
    # -----------------------------
    if st.session_state.get('logged_in', False):
        user = st.session_state['current_user']
        st.subheader(f"🎉 Welcome, {user['name']}!")
        st.write(f"You are logged in from {user['area']}.")

        waste_types = ['Plastic','Paper','Organic','Other']
        waste_type = st.selectbox("Waste Type", waste_types)
        quantity = st.number_input("Quantity (kg)", min_value=0.0, step=0.01, format="%.2f")
        submit_btn = st.button("Submit Waste")
        points_dict = {'Plastic':10,'Paper':5,'Organic':2,'Other':1}

        if submit_btn and quantity>0 and area != '--Select your area--':
            # Check or create user
            users_df = st.session_state['users_df']
            existing_user = users_df[users_df['mobile']==mobile]
            if existing_user.empty:
                new_user = {'user_id': generate_user_id(), 'name': name, 'mobile': mobile,
                            'area': area, 'total_points':0, 'improper_count':0}
                st.session_state['users_df'] = pd.concat([users_df, pd.DataFrame([new_user])], ignore_index=True)
                user_row = new_user
            else:
                user_row = existing_user.iloc[0]
            user_index = st.session_state['users_df'][st.session_state['users_df']['mobile']==mobile].index[0]

            proper = st.radio("Is waste properly segregated?", ["Yes","No"])
            category = "Dry" if waste_type in ['Plastic','Paper','Other'] else "Wet"

            if proper == "Yes":
                points_earned = quantity * points_dict[waste_type]
                st.session_state['users_df'].at[user_index,'total_points'] += points_earned
                status = "Proper"
                st.success(f"Points Earned: {points_earned} | Category: {category}")
            else:
                st.session_state['users_df'].at[user_index,'improper_count'] += 1
                improper_count = st.session_state['users_df'].at[user_index,'improper_count']
                points_earned = 0
                status = "Improper"
                st.warning(f"Submission Improper | Category: {category}")
                if improper_count > 2:
                    st.error("Third improper submission: 1 point deducted!")
                    st.session_state['users_df'].at[user_index,'total_points'] -= 1

            # -----------------------------
            # Auto-assign collector based on area with least points
            # -----------------------------
            collectors_df = st.session_state['collectors_df']
            area_collectors = collectors_df[collectors_df['assigned_area']==area]

            collector_name = None
            collector_id = None

            if not area_collectors.empty:
                collector_row = area_collectors.sort_values('total_points').iloc[0]
                collector_id = collector_row['collector_id']
                collector_name = collector_row['name']
                idx = collectors_df[collectors_df['collector_id']==collector_id].index[0]
                st.session_state['collectors_df'].at[idx,'total_points'] += points_earned

            # Save submission
            submissions_df = st.session_state['submissions_df']
            new_submission = {'submission_id': len(submissions_df)+1, 'user_id': user_row['user_id'],
                              'collector_id': collector_id, 'waste_type': waste_type, 'quantity': quantity,
                              'points': points_earned, 'status': status, 'category': category,
                              'timestamp': datetime.now()}
            st.session_state['submissions_df'] = pd.concat([submissions_df, pd.DataFrame([new_submission])], ignore_index=True)

            st.info(f"Collector Assigned: {collector_name if collector_name else 'No collector assigned'}")

# -----------------------------
# User Leaderboard
# -----------------------------
elif page == "User Leaderboard":
    st.subheader("🏆 User Leaderboard")
    users_df = st.session_state['users_df']
    if users_df.empty:
        st.table(pd.DataFrame(columns=['name','area','total_points']))
    else:
        user_board = users_df.sort_values('total_points', ascending=False)[['name','area','total_points']]
        st.table(user_board)

# -----------------------------
# User Dashboard by Area with Daily Totals
# -----------------------------
elif page == "User Dashboard":
    st.subheader("📊 User Dashboard by Area")

    submissions_df = st.session_state['submissions_df']
    users_df = st.session_state['users_df']

    if submissions_df.empty:
        st.warning("No submissions available yet.")
    else:
        # Merge area info
        submissions_with_area = submissions_df.merge(
            users_df[['user_id','area']], on='user_id', how='left'
        )

        # All-time total
        area_summary = submissions_with_area.groupby('area')['quantity'].sum().reset_index()
        fig_area = px.bar(
            area_summary,
            x='area',
            y='quantity',
            color='area',
            text='quantity',
            title="Total Waste Collected per Area (All Time)"
        )
        fig_area.update_traces(texttemplate='%{text:.2f} kg', textposition='outside')
        fig_area.update_layout(yaxis_title="Weight (kg)", xaxis_title="Area")
        st.plotly_chart(fig_area, use_container_width=True)

        # Daily totals (today)
        today = pd.Timestamp.now().normalize()
        today_submissions = submissions_with_area[
            submissions_with_area['timestamp'] >= today
        ]
        if not today_submissions.empty:
            daily_summary = today_submissions.groupby('area')['quantity'].sum().reset_index()
            fig_daily = px.bar(
                daily_summary,
                x='area',
                y='quantity',
                color='area',
                text='quantity',
                title="Today's Waste Collected per Area"
            )
            fig_daily.update_traces(texttemplate='%{text:.2f} kg', textposition='outside')
            fig_daily.update_layout(yaxis_title="Weight (kg)", xaxis_title="Area")
            st.plotly_chart(fig_daily, use_container_width=True)
        else:
            st.info("No submissions for today yet.")
