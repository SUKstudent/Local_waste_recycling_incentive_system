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
# Sidebar Logo & Description
# -----------------------------
st.sidebar.image("GreenBin.jpg", width=150)
st.sidebar.markdown("""
# ♻️ Recycle Rewards
Encouraging recycling with points and rewards.
Register or login to start contributing!
""")

# -----------------------------
# Dark Theme CSS
# -----------------------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #121212; color: #ffffff; }
input, textarea, select { background-color: #333333 !important; color: #ffffff !important; }
.stButton>button { background-color: #2e7d32 !important; color: white !important; width: 100% !important; height: 3em !important; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Title
# -----------------------------
st.markdown("<h1 style='color:#2e7d32;'>♻️ Local Waste Recycling Incentive System</h1>", unsafe_allow_html=True)

# -----------------------------
# Helper Functions
# -----------------------------
def generate_user_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_otp(length=4):
    return ''.join(random.choices(string.digits, k=length))

# -----------------------------
# Session State Initialization
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

st.session_state.setdefault('logged_in', False)
st.session_state.setdefault('current_user', {})

# -----------------------------
# User Portal: Login/Register
# -----------------------------
st.subheader("User Portal")

if not st.session_state['logged_in']:
    tab1, tab2 = st.tabs(["Login", "Register"])

    # ----- LOGIN -----
    with tab1:
        login_mobile = st.text_input("Mobile Number")
        if st.button("Login"):
            users = st.session_state['users_df']
            matched = users[users['mobile'] == login_mobile]
            if not matched.empty:
                user_data = matched.iloc[0]
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = user_data.to_dict()
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("User not found")

    # ----- REGISTER -----
    with tab2:
        name = st.text_input("Full Name")
        mobile = st.text_input("Mobile Number")
        area = st.selectbox("Area", ["Residential Apartment Complex","Hospital","Shopping Mall","Office Complex","Market","Industrial Area"])

        if st.button("Register"):
            new_user = {
                'user_id': generate_user_id(),
                'name': name,
                'mobile': mobile,
                'area': area,
                'total_points': 0
            }
            st.session_state['users_df'] = pd.concat([st.session_state['users_df'], pd.DataFrame([new_user])], ignore_index=True)
            st.success("Registered! You can now login.")

# -----------------------------
# Logged In Portal
# -----------------------------
else:
    user = st.session_state['current_user']
    st.success(f"Welcome {user['name']} ({user['area']})")

    # ----- Waste Submission -----
    with st.form("waste_form"):

        w_type = st.selectbox("Waste Type", [
            'Plastic', 'Paper', 'Organic', 'Metal', 'Glass', 'Hazardous'
        ])

        w_qty = st.number_input("Quantity (kg)", min_value=0.1, step=0.1)

        submit = st.form_submit_button("Submit")

        if submit:

            # Restrict hazardous waste
            if w_type == "Hazardous" and user['area'] not in ["Hospital", "Industrial Area"]:
                st.error("⚠️ Hazardous waste allowed only for Hospital or Industrial Area")
                st.stop()

            # Category logic
            if w_type == "Organic":
                category = "Wet"
            elif w_type == "Hazardous":
                category = "Special"
            else:
                category = "Dry"

            # Points system with area multiplier
            points_map = {
                'Plastic': 8,
                'Paper': 6,
                'Organic': 2,
                'Metal': 15,
                'Glass': 10,
                'Hazardous': 20
            }

            multiplier = 1.0
            if user['area'] == "Hospital":
                multiplier = 1.2
            elif user['area'] == "Industrial Area":
                multiplier = 1.3

            points = w_qty * points_map[w_type] * multiplier

            # Assign collector
            collector = st.session_state['collectors_df'][
                st.session_state['collectors_df']['assigned_area'] == user['area']
            ].iloc[0]

            # Save submission
            new_sub = {
                'submission_id': len(st.session_state['submissions_df']) + 1,
                'user_id': user['mobile'],
                'collector_id': collector['collector_id'],
                'waste_type': w_type,
                'quantity': w_qty,
                'points': points,
                'status': "Proper",
                'category': category,
                'timestamp': datetime.now(),
                'area': user['area']
            }

            st.session_state['submissions_df'] = pd.concat(
                [st.session_state['submissions_df'], pd.DataFrame([new_sub])], ignore_index=True
            )

            # Update user points
            idx = st.session_state['users_df'].loc[
                st.session_state['users_df']['mobile'] == user['mobile']
            ].index[0]
            st.session_state['users_df'].at[idx, 'total_points'] += points

            st.success(f"✅ Submitted! Points earned: {points:.2f}")

    # -----------------------------
    # Dashboard
    # -----------------------------
    st.header("📊 Dashboard")
    df = st.session_state['submissions_df']

    # ----- Sidebar Single-Date Filter -----
    st.sidebar.subheader("📌 Filter by Date & Area")

    if not df.empty:
        area_filter = st.sidebar.multiselect(
            "Select Area",
            options=df['area'].unique(),
            default=df['area'].unique()
        )

        selected_date = st.sidebar.date_input(
            "Select Date",
            value=pd.to_datetime(df['timestamp']).max().date()
        )

        filtered_df = df[
            (df['area'].isin(area_filter)) &
            (pd.to_datetime(df['timestamp']).dt.date == selected_date)
        ]
    else:
        filtered_df = df

    # ----- Waste Distribution Pie Chart -----
    if not filtered_df.empty:
        st.subheader("Waste Distribution")
        waste_dist = filtered_df.groupby('waste_type')['quantity'].sum().reset_index()
        fig1 = px.pie(
            waste_dist,
            names='waste_type',
            values='quantity',
            title="Waste Composition"
        )
        fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
        st.plotly_chart(fig1, use_container_width=True)

        # ----- Area-wise Bar Chart -----
        st.subheader("Area-wise Waste Collection")
        area_df = filtered_df.groupby('area')['quantity'].sum().reset_index()
        fig2 = px.bar(
            area_df,
            x='area',
            y='quantity',
            color='area',
            labels={'quantity':'Total Waste (kg)', 'area':'Area'}
        )
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
        st.plotly_chart(fig2, use_container_width=True)
