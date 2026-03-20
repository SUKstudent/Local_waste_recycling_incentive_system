import streamlit as st
import pandas as pd
import os
import joblib
import random
import string

# --- Page configuration ---
st.set_page_config(page_title="Local Waste Recycling", layout="wide", page_icon="♻️")

# --- Helper functions ---
def generate_user_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def send_otp_simulation():
    otp = random.randint(1000, 9999)
    st.session_state['otp'] = otp
    st.session_state['otp_verified'] = True  # Auto verify for demo
    st.success(f"OTP auto-filled (Simulated): {otp}")
    return otp

# --- File paths ---
data_dir = '.'
users_file = os.path.join(data_dir, 'users_large.csv')
collectors_file = os.path.join(data_dir, 'collectors_large.csv')
submissions_file = os.path.join(data_dir, 'submissions_large.csv')
logo_path = os.path.join(data_dir, "GreenBin.jpg")

# --- Load CSVs ---
users_df = pd.read_csv(users_file) if os.path.exists(users_file) else pd.DataFrame(
    columns=['user_id','name','mobile','area','total_points','improper_count'])
collectors_df = pd.read_csv(collectors_file) if os.path.exists(collectors_file) else pd.DataFrame(
    columns=['collector_id','name','assigned_area','total_points','ratings'])
submissions_df = pd.read_csv(submissions_file) if os.path.exists(submissions_file) else pd.DataFrame(
    columns=['submission_id','user_id','collector_id','waste_type','quantity','points','status','category','degradable','bio_type'])

# --- Sidebar Logo and navigation ---
st.sidebar.markdown("<h2 style='color:green'>♻️ GreenBin</h2>", unsafe_allow_html=True)
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=180)
else:
    st.sidebar.warning("Logo GreenBin.jpg not found!")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Page", ["Login / Waste Submission", "User Leaderboard", "Collector Leaderboard"])

# --- OTP session ---
if 'otp_sent' not in st.session_state:
    st.session_state['otp_sent'] = False
if 'otp_verified' not in st.session_state:
    st.session_state['otp_verified'] = False

# --- Page 1: Login / Waste Submission ---
if page == "Login / Waste Submission":
    st.title("⚡ Local Waste & Recycling Incentive System")
    
    with st.form(key="login_form"):
        st.subheader("User Login / Registration")
        mobile = st.text_input("Enter your mobile number")
        name = st.text_input("Enter your name")
        area_options = ["--Select your area--",'Residential Apartment Complex','Hospital','Shopping Mall','Office Complex',
                        'Market','School/College','Railway Station','Bus Terminal','Industrial Area','Hotel']
        area = st.selectbox("Select your area", area_options)
        send_otp = st.form_submit_button("Send/Resend OTP")
        
        if send_otp:
            if mobile:
                send_otp_simulation()
            else:
                st.error("Enter mobile number!")

    if st.session_state.get('otp_verified', False):
        st.success("OTP Verified ✅")
        with st.form(key="waste_form"):
            st.subheader("Submit Waste")
            waste_types = ['Plastic','Paper','Organic','Other']
            waste_type = st.selectbox("Waste Type", waste_types)
            quantity = st.number_input("Quantity (kg)", min_value=0.0, step=0.1)
            degradable = st.radio("Is the waste degradable?", ("Yes", "No"))
            bio_type = None
            if degradable == "Yes":
                bio_type = st.selectbox("Type of degradable waste", ["Biodegradable", "Non-biodegradable"])
            proper = st.radio("Is waste properly segregated?", ("Yes", "No"))
            submit_waste = st.form_submit_button("Submit Waste")

            if submit_waste and quantity > 0 and area != "--Select your area--":
                points_dict = {'Plastic':10,'Paper':5,'Organic':2,'Other':1}
                # Add or get user
                existing_user = users_df[users_df['mobile'] == mobile]
                if existing_user.empty:
                    new_user = {
                        'user_id': generate_user_id(),
                        'name': name,
                        'mobile': mobile,
                        'area': area,
                        'total_points': 0,
                        'improper_count': 0
                    }
                    users_df = pd.concat([users_df, pd.DataFrame([new_user])], ignore_index=True)
                    user_row = new_user
                else:
                    user_row = existing_user.iloc[0]
                user_index = users_df[users_df['mobile'] == mobile].index[0]

                category = "Dry" if waste_type in ['Plastic', 'Paper', 'Other'] else "Wet"
                if proper == "Yes":
                    points_earned = quantity * points_dict[waste_type]
                    users_df.at[user_index, 'total_points'] += points_earned
                    status = "Proper"
                    st.success(f"Points Earned: {points_earned} | Category: {category}")
                else:
                    users_df.at[user_index, 'improper_count'] += 1
                    improper_count = users_df.at[user_index, 'improper_count']
                    points_earned = 0
                    status = "Improper"
                    st.warning(f"Submission Improper | Category: {category}")
                    if improper_count > 2:
                        st.error("Third improper submission: 1 point deducted!")
                        users_df.at[user_index, 'total_points'] -= 1

                # Assign collector
                area_collectors = collectors_df[collectors_df['assigned_area'] == area]
                collector_id = None
                if not area_collectors.empty:
                    collector_row = area_collectors.iloc[0]
                    collector_index = area_collectors.index[0]
                    collectors_df.at[collector_index, 'total_points'] += points_earned
                    collector_id = collector_row['collector_id']
                    rating = st.slider(f"Rate collector {collector_row['name']}", 1, 5)
                    prev_ratings = collector_row.get('ratings', [])
                    if not isinstance(prev_ratings, list):
                        prev_ratings = []
                    prev_ratings.append(rating)
                    collectors_df.at[collector_index, 'ratings'] = prev_ratings

                # Record submission
                new_submission = {
                    'submission_id': len(submissions_df) + 1,
                    'user_id': user_row['user_id'],
                    'collector_id': collector_id,
                    'waste_type': waste_type,
                    'quantity': quantity,
                    'points': points_earned,
                    'status': status,
                    'category': category,
                    'degradable': degradable,
                    'bio_type': bio_type
                }
                submissions_df = pd.concat([submissions_df, pd.DataFrame([new_submission])], ignore_index=True)

                # Save CSVs
                users_df.to_csv(users_file, index=False)
                collectors_df.to_csv(collectors_file, index=False)
                submissions_df.to_csv(submissions_file, index=False)

# --- Page 2: User Leaderboard ---
elif page == "User Leaderboard":
    st.subheader("🏆 User Leaderboard")
    if not users_df.empty and {'area', 'name', 'total_points'}.issubset(users_df.columns):
        user_board = users_df.groupby('area')[['name','total_points']].apply(lambda x: x.sort_values('total_points', ascending=False)).reset_index(drop=True)
        st.table(user_board)
    else:
        st.warning("User Leaderboard unavailable: no data or missing columns")

# --- Page 3: Collector Leaderboard ---
elif page == "Collector Leaderboard":
    st.subheader("🏅 Collector Leaderboard")
    if not collectors_df.empty and {'name','assigned_area','total_points','ratings'}.issubset(collectors_df.columns):
        collectors_df['avg_rating'] = collectors_df['ratings'].apply(lambda x: sum(x)/len(x) if isinstance(x,list) and len(x)>0 else 0)
        collector_board = collectors_df.sort_values('total_points', ascending=False)[['name','assigned_area','total_points','avg_rating']]
        st.table(collector_board)
    else:
        st.warning("Collector Leaderboard unavailable: no data or missing columns")
