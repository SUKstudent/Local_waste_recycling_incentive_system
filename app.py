import streamlit as st
import pandas as pd
import os
import joblib
import random
import string
import plotly.express as px
from datetime import datetime

# -----------------------------
# Page config and light theme
# -----------------------------
st.set_page_config(page_title="Local Waste Recycling", layout="wide")
st.markdown(
    """
    <style>
    .css-18ni7ap.e8zbici2 {background-color: #e6f7e6;}  /* Light green background */
    .stButton button {background-color: #4CAF50; color: white;}
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# Helper functions
# -----------------------------
def generate_user_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def send_otp_simulation():
    otp = random.randint(1000, 9999)
    st.session_state['otp'] = otp
    st.session_state['otp_sent'] = True
    st.info(f"OTP sent to your mobile (Simulated): {otp}")
    return otp

# -----------------------------
# File paths
# -----------------------------
data_dir = '.'  # Current folder
users_file = os.path.join(data_dir, 'users_large.csv')
collectors_file = os.path.join(data_dir, 'collectors_large.csv')
submissions_file = os.path.join(data_dir, 'submissions_large.csv')
logo_path = os.path.join(data_dir, "GreenBin.jpg")

# -----------------------------
# Load CSVs safely
# -----------------------------
users_df = pd.read_csv(users_file) if os.path.exists(users_file) else pd.DataFrame(
    columns=['user_id','name','mobile','area','total_points','improper_count'])
collectors_df = pd.read_csv(collectors_file) if os.path.exists(collectors_file) else pd.DataFrame(
    columns=['collector_id','name','assigned_area','total_points','ratings'])
submissions_df = pd.read_csv(submissions_file) if os.path.exists(submissions_file) else pd.DataFrame(
    columns=['submission_id','user_id','collector_id','waste_type','quantity','points','status','category','timestamp'])

# -----------------------------
# Add timestamp column if missing
# -----------------------------
if 'timestamp' not in submissions_df.columns:
    submissions_df['timestamp'] = pd.to_datetime('now')
submissions_df['timestamp'] = pd.to_datetime(submissions_df['timestamp'])

# -----------------------------
# Load ML models if exist
# -----------------------------
clf_path = os.path.join(data_dir,'waste_model.pkl')
le_user_path = os.path.join(data_dir,'encoder_user.pkl')
le_collector_path = os.path.join(data_dir,'encoder_collector.pkl')
le_waste_path = os.path.join(data_dir,'encoder_waste.pkl')

if all(os.path.exists(p) for p in [clf_path, le_user_path, le_collector_path, le_waste_path]):
    clf = joblib.load(clf_path)
    le_user = joblib.load(le_user_path)
    le_collector = joblib.load(le_collector_path)
    le_waste = joblib.load(le_waste_path)
else:
    clf = None

# -----------------------------
# Sidebar Logo and Navigation
# -----------------------------
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=180)
else:
    st.sidebar.warning(f"Logo {logo_path} not found!")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Login / Waste Submission", "User Leaderboard", "Collector Leaderboard", "User Dashboard", "Collector Dashboard"])

# -----------------------------
# Session state defaults
# -----------------------------
if 'otp_sent' not in st.session_state:
    st.session_state['otp_sent'] = False
if 'otp_verified' not in st.session_state:
    st.session_state['otp_verified'] = False
if 'otp_input' not in st.session_state:
    st.session_state['otp_input'] = ""

# -----------------------------
# Page: Login / Waste Submission
# -----------------------------
if page == "Login / Waste Submission":
    st.title("⚡ Local Waste & Recycling Incentive System")

    st.subheader("User Login / Registration")
    mobile = st.text_input("Mobile Number", key="mobile_input")
    name = st.text_input("Name", key="name_input")
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
        otp_input = st.text_input("Enter OTP", key="otp_input")
        # Auto verification
        if st.session_state.get('otp_sent', False) and otp_input:
            if str(st.session_state.get('otp')) == otp_input:
                st.session_state['otp_verified'] = True
                st.success("OTP Verified ✅")
            else:
                st.session_state['otp_verified'] = False
                st.warning("Incorrect OTP")

    # -----------------------------
    # Waste Submission Section
    # -----------------------------
    if st.session_state.get('otp_verified', False):
        st.subheader("Submit Waste")
        waste_types = ['Plastic','Paper','Organic','Other']
        waste_type = st.selectbox("Waste Type", waste_types)
        quantity = st.number_input("Quantity (kg)", min_value=0.0, step=0.1)
        submit_btn = st.button("Submit Waste")
        points_dict = {'Plastic':10,'Paper':5,'Organic':2,'Other':1}

        if submit_btn and quantity>0 and area != '--Select your area--':
            existing_user = users_df[users_df['mobile']==mobile]
            if existing_user.empty:
                new_user = {'user_id': generate_user_id(), 'name': name, 'mobile': mobile,
                            'area': area, 'total_points':0, 'improper_count':0}
                users_df = pd.concat([users_df, pd.DataFrame([new_user])], ignore_index=True)
                user_row = new_user
            else:
                user_row = existing_user.iloc[0]
            user_index = users_df[users_df['mobile']==mobile].index[0]

            proper = st.radio("Is waste properly segregated?", ["Yes","No"])
            category = "Dry" if waste_type in ['Plastic','Paper','Other'] else "Wet"

            if proper == "Yes":
                points_earned = quantity * points_dict[waste_type]
                users_df.at[user_index,'total_points'] += points_earned
                status = "Proper"
                st.success(f"Points Earned: {points_earned} | Category: {category}")
            else:
                users_df.at[user_index,'improper_count'] += 1
                improper_count = users_df.at[user_index,'improper_count']
                points_earned = 0
                status = "Improper"
                st.warning(f"Submission Improper | Category: {category}")
                if improper_count > 2:
                    st.error("Third improper submission: 1 point deducted!")
                    users_df.at[user_index,'total_points'] -= 1

            area_collectors = collectors_df[collectors_df['assigned_area']==area]
            collector_id = None
            if not area_collectors.empty:
                collector_row = area_collectors.iloc[0]
                collector_index = area_collectors.index[0]
                collectors_df.at[collector_index,'total_points'] += points_earned
                collector_id = collector_row['collector_id']

                rating = st.slider(f"Rate collector {collector_row['name']}", 1, 5)
                prev_ratings = collector_row.get('ratings', [])
                if not isinstance(prev_ratings,list):
                    prev_ratings = []
                prev_ratings.append(rating)
                collectors_df.at[collector_index,'ratings'] = prev_ratings

            new_submission = {'submission_id': len(submissions_df)+1, 'user_id': user_row['user_id'],
                              'collector_id': collector_id, 'waste_type': waste_type, 'quantity': quantity,
                              'points': points_earned, 'status': status, 'category': category,
                              'timestamp': datetime.now()}
            submissions_df = pd.concat([submissions_df, pd.DataFrame([new_submission])], ignore_index=True)

            # Save CSVs
            users_df.to_csv(users_file, index=False)
            collectors_df.to_csv(collectors_file, index=False)
            submissions_df.to_csv(submissions_file, index=False)

            # ML prediction
            if clf is not None:
                try:
                    user_enc = le_user.transform([user_row['user_id']])[0]
                    collector_enc = le_collector.transform([collector_id if collector_id else 0])[0]
                    waste_enc = le_waste.transform([waste_type])[0]
                    ml_pred = clf.predict([[user_enc, collector_enc, waste_enc, quantity]])[0]
                    st.info(f"AI Prediction: {'Proper ✅' if ml_pred==1 else 'Improper ❌'}")
                except:
                    st.warning("ML Prediction unavailable for new user/collector.")
