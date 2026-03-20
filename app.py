import streamlit as st
import pandas as pd
import os
import joblib
import random
import string

st.set_page_config(page_title="Local Waste Recycling", layout="wide")

# --- Helper functions ---
def generate_user_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def send_otp_simulation():
    otp = random.randint(1000,9999)
    st.session_state['otp'] = otp
    st.info(f"OTP sent to your mobile (Simulated): {otp}")
    return otp

# --- File paths ---
data_dir = 'LocalWaste Project'
users_file = os.path.join(data_dir, 'users_large.csv')
collectors_file = os.path.join(data_dir, 'collectors_large.csv')
submissions_file = os.path.join(data_dir, 'submissions_large.csv')

# --- Load CSVs ---
users_df = pd.read_csv(users_file) if os.path.exists(users_file) else pd.DataFrame(columns=['user_id','name','mobile','area','total_points','improper_count'])
collectors_df = pd.read_csv(collectors_file) if os.path.exists(collectors_file) else pd.DataFrame(columns=['collector_id','name','assigned_area','total_points','ratings'])
submissions_df = pd.read_csv(submissions_file) if os.path.exists(submissions_file) else pd.DataFrame(columns=['submission_id','user_id','collector_id','waste_type','quantity','points','status','category'])

# --- Load ML model ---
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

# --- UI ---
st.title("⚡ Local Waste & Recycling Incentive System")

# --- Registration / Login ---
st.subheader("User Login / Registration")
mobile = st.text_input("Enter your mobile number")
name = st.text_input("Enter your name")
area_options = ['Residential Apartment Complex','Hospital','Shopping Mall','Office Complex','Market','School/College','Railway Station','Bus Terminal','Industrial Area','Hotel']
area = st.selectbox("Select your area", area_options)

if 'otp_verified' not in st.session_state:
    st.session_state['otp_verified'] = False

if st.button("Send OTP"):
    if mobile:
        send_otp_simulation()
    else:
        st.error("Enter mobile number!")

otp_input = st.text_input("Enter OTP")
if st.button("Verify OTP"):
    if 'otp' in st.session_state and otp_input:
        if str(st.session_state['otp']) == otp_input:
            st.success("OTP Verified ✅")
            st.session_state['otp_verified'] = True
        else:
            st.error("Incorrect OTP")
    else:
        st.warning("Send OTP first!")

# --- Waste Submission ---
if st.session_state['otp_verified']:
    st.subheader("Submit Waste")
    waste_types = ['Plastic','Paper','Organic','Other']
    waste_type = st.selectbox("Waste Type", waste_types)
    quantity = st.number_input("Quantity (kg)", min_value=0.0, step=0.1)
    submit_btn = st.button("Submit Waste")

    points_dict = {'Plastic':10,'Paper':5,'Organic':2,'Other':1}

    if submit_btn and quantity>0:
        # Add user if new
        existing_user = users_df[users_df['mobile']==mobile]
        if existing_user.empty:
            new_user = {
                'user_id': generate_user_id(),
                'name': name,
                'mobile': mobile,
                'area': area,
                'total_points': 0,
                'improper_count':0
            }
            users_df = pd.concat([users_df, pd.DataFrame([new_user])], ignore_index=True)
            user_row = new_user
        else:
            user_row = existing_user.iloc[0]
        user_index = users_df[users_df['mobile']==mobile].index[0]

        proper = st.radio("Is waste properly segregated?", ("Yes","No"))
        category = "Dry" if waste_type in ['Plastic','Paper','Other'] else "Wet"

        # Points & status
        if proper=="Yes":
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

        # Assign collector
        area_collectors = collectors_df[collectors_df['assigned_area']==area]
        collector_id = None
        if not area_collectors.empty:
            collector_row = area_collectors.iloc[0]
            collector_index = area_collectors.index[0]
            collectors_df.at[collector_index,'total_points'] += points_earned
            collector_id = collector_row['collector_id']

            # Rating simulation
            rating = st.slider(f"Rate collector {collector_row['name']}", 1, 5)
            prev_ratings = collector_row.get('ratings', [])
            if not isinstance(prev_ratings,list):
                prev_ratings = []
            prev_ratings.append(rating)
            collectors_df.at[collector_index,'ratings'] = prev_ratings

        # Record submission
        new_submission = {
            'submission_id': len(submissions_df)+1,
            'user_id': user_row['user_id'],
            'collector_id': collector_id,
            'waste_type': waste_type,
            'quantity': quantity,
            'points': points_earned,
            'status': status,
            'category': category
        }
        submissions_df = pd.concat([submissions_df, pd.DataFrame([new_submission])], ignore_index=True)

        # Save CSVs
        users_df.to_csv(users_file, index=False)
        collectors_df.to_csv(collectors_file, index=False)
        submissions_df.to_csv(submissions_file, index=False)

        # Real-time ML Prediction
        if clf is not None:
            try:
                user_enc = le_user.transform([user_row['user_id']])[0]
                collector_enc = le_collector.transform([collector_id if collector_id else 0])[0]
                waste_enc = le_waste.transform([waste_type])[0]
                ml_pred = clf.predict([[user_enc, collector_enc, waste_enc, quantity]])[0]
                st.info(f"AI Prediction: {'Proper ✅' if ml_pred==1 else 'Improper ❌'}")
            except:
                st.warning("ML Prediction unavailable for new user/collector.")

# --- Leaderboards ---
st.subheader("User Leaderboard")
st.table(users_df.groupby('area')[['name','total_points']].apply(lambda x: x.sort_values('total_points', ascending=False)).reset_index(drop=True))

st.subheader("Collector Leaderboard")
collectors_df['avg_rating'] = collectors_df['ratings'].apply(lambda x: sum(x)/len(x) if isinstance(x,list) and len(x)>0 else 0)
st.table(collectors_df.sort_values('total_points', ascending=False)[['name','assigned_area','total_points','avg_rating']])
