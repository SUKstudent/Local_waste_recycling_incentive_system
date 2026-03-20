import streamlit as st
import pandas as pd
import joblib
import os

st.set_page_config(page_title="Local Waste Recycling", layout="wide")

# --- Load CSVs ---
users_file = os.path.join('LocalWaste Project','users_large.csv')
collectors_file = os.path.join('LocalWaste Project','collectors_large.csv')
submissions_file = os.path.join('LocalWaste Project','submissions_large.csv')

users_df = pd.read_csv(users_file)
collectors_df = pd.read_csv(collectors_file)
submissions_df = pd.read_csv(submissions_file)

# --- Load model & encoders ---
clf_path = os.path.join('LocalWaste Project','waste_model.pkl')
le_user_path = os.path.join('LocalWaste Project','encoder_user.pkl')
le_collector_path = os.path.join('LocalWaste Project','encoder_collector.pkl')
le_waste_path = os.path.join('LocalWaste Project','encoder_waste.pkl')

if all(os.path.exists(p) for p in [clf_path, le_user_path, le_collector_path, le_waste_path]):
    clf = joblib.load(clf_path)
    le_user = joblib.load(le_user_path)
    le_collector = joblib.load(le_collector_path)
    le_waste = joblib.load(le_waste_path)
else:
    st.warning("ML model not trained yet. Run train_model.py first.")
    clf = None

# --- UI ---
st.title("⚡ Local Waste & Recycling Incentive System")

areas = users_df['area'].unique().tolist()
waste_types = ['Plastic', 'Paper', 'Organic', 'Other']
points_dict = {'Plastic':10, 'Paper':5, 'Organic':2, 'Other':1}

st.subheader("Submit Waste")
user_name = st.text_input("Enter your name")
user_area = st.selectbox("Select your area", areas)
waste_type = st.selectbox("Waste Type", waste_types)
quantity = st.number_input("Quantity (kg)", min_value=0.0, step=0.1)
submit_btn = st.button("Submit Waste")

if submit_btn and user_name and quantity>0:
    # Add user if new
    if user_name not in users_df['name'].values:
        new_user = {'user_id': len(users_df)+1, 'name': user_name, 'area': user_area,
                    'total_points': 0, 'improper_count':0}
        users_df = pd.concat([users_df, pd.DataFrame([new_user])], ignore_index=True)

    user_row = users_df[users_df['name']==user_name].iloc[0]
    user_index = users_df[users_df['name']==user_name].index[0]

    proper = st.radio("Is waste properly segregated?", ("Yes","No"))
    category = "Dry" if waste_type in ['Plastic','Paper','Other'] else "Wet"

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
    area_collectors = collectors_df[collectors_df['assigned_area']==user_area]
    collector_id = None
    if not area_collectors.empty:
        collector_row = area_collectors.iloc[0]
        collector_index = area_collectors.index[0]
        collectors_df.at[collector_index,'total_points'] += points_earned
        collector_id = collector_row['collector_id']

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
        except Exception as e:
            st.warning("ML Prediction unavailable for new user or collector.")

# --- Leaderboards ---
st.subheader("User Leaderboard")
st.table(users_df.sort_values(by='total_points', ascending=False)[['name','area','total_points']])

st.subheader("Collector Leaderboard")
st.table(collectors_df.sort_values(by='total_points', ascending=False)[['name','assigned_area','total_points']])
