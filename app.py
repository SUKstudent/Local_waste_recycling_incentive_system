import streamlit as st
import pandas as pd
import os
from sklearn.model_selection import train_test_split
import random

# --- File paths ---
users_file = 'users_large.csv'
collectors_file = 'collectors_large.csv'
submissions_file = 'submissions_large.csv'

# --- Load CSVs or generate if not exists ---
areas = [
    'Residential Apartment Complex',
    'Hospital',
    'Shopping Mall',
    'Office Complex',
    'Market',
    'School/College',
    'Railway Station',
    'Bus Terminal',
    'Industrial Area',
    'Hotel'
]

def generate_files():
    # Users
    users_list = [{'user_id': i, 'name': f'User{i}', 'area': random.choice(areas),
                   'total_points': 0, 'improper_count': 0} for i in range(1, 51)]
    users_df = pd.DataFrame(users_list)
    
    # Collectors
    collectors_list = [{'collector_id': i, 'name': f'Collector{i}', 'assigned_area': random.choice(areas),
                        'total_points': 0} for i in range(1, 11)]
    collectors_df = pd.DataFrame(collectors_list)
    
    # Submissions
    waste_types = ['Plastic', 'Paper', 'Organic', 'Other']
    waste_category = {'Plastic': 'Dry', 'Paper': 'Dry', 'Organic': 'Wet', 'Other': 'Dry'}
    submissions_list = []
    for i in range(1, 201):
        user = random.choice(users_list)
        collector_candidates = [c for c in collectors_list if c['assigned_area']==user['area']]
        collector = random.choice(collector_candidates) if collector_candidates else random.choice(collectors_list)
        waste_type = random.choice(waste_types)
        quantity = round(random.uniform(0.5, 5.0), 1)
        proper = random.choices(['Proper','Improper'], weights=[0.8,0.2])[0]
        points = quantity * (10 if waste_type=='Plastic' else 5 if waste_type=='Paper' else 2 if waste_type=='Organic' else 1) if proper=='Proper' else 0
        submissions_list.append({
            'submission_id': i,
            'user_id': user['user_id'],
            'collector_id': collector['collector_id'],
            'waste_type': waste_type,
            'quantity': quantity,
            'points': points,
            'status': proper,
            'category': waste_category[waste_type]
        })
    submissions_df = pd.DataFrame(submissions_list)
    
    # Save
    users_df.to_csv(users_file, index=False)
    collectors_df.to_csv(collectors_file, index=False)
    submissions_df.to_csv(submissions_file, index=False)

# Check files
if not (os.path.exists(users_file) and os.path.exists(collectors_file) and os.path.exists(submissions_file)):
    generate_files()

# Load
users_df = pd.read_csv(users_file)
collectors_df = pd.read_csv(collectors_file)
submissions_df = pd.read_csv(submissions_file)

# --- Streamlit UI ---
st.title("⚡ Local Waste & Recycling Incentive System")

# Waste options
waste_types = ['Plastic', 'Paper', 'Organic', 'Other']
waste_category = {'Plastic': 'Dry', 'Paper': 'Dry', 'Organic': 'Wet', 'Other': 'Dry'}
points_dict = {'Plastic':10, 'Paper':5, 'Organic':2, 'Other':1}

st.subheader("## Submit Waste")
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
    category = waste_category[waste_type]

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

# --- Leaderboards ---
st.subheader("## User Leaderboard")
st.table(users_df.sort_values(by='total_points', ascending=False)[['name','area','total_points']])

st.subheader("## Collector Leaderboard")
st.table(collectors_df.sort_values(by='total_points', ascending=False)[['name','assigned_area','total_points']])

# --- Train/Test Split ---
if st.button("Generate Train/Test CSVs"):
    train_df, test_df = train_test_split(submissions_df, test_size=0.2, random_state=42)
    train_df.to_csv('submissions_train.csv', index=False)
    test_df.to_csv('submissions_test.csv', index=False)
    st.success(f"Train/Test CSVs generated! Train: {train_df.shape[0]}, Test: {test_df.shape[0]}")