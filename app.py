import streamlit as st
import pandas as pd
import random
import string
import plotly.express as px
from datetime import datetime

# -----------------------------
# 1. Page Config & Styling
# -----------------------------
st.set_page_config(page_title="Recycle Rewards - Local Waste and Recycling Incentive System", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f9fbf9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #2e7d32; color: white; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------
# 2. Helper Functions & Data Initialization
# -----------------------------
def generate_user_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Initialize DataFrames in Session State
if 'users_df' not in st.session_state:
    st.session_state['users_df'] = pd.DataFrame(columns=['user_id','name','mobile','area','total_points','improper_count'])

if 'collectors_df' not in st.session_state:
    data = [
        {'collector_id': 101, 'name': 'Officer Rajesh', 'assigned_area': 'Market', 'total_points': 0},
        {'collector_id': 102, 'name': 'Officer Anita', 'assigned_area': 'Residential Apartment Complex', 'total_points': 0},
        {'collector_id': 103, 'name': 'Officer Sam', 'assigned_area': 'Hospital', 'total_points': 0},
        {'collector_id': 104, 'name': 'Officer Priya', 'assigned_area': 'Office Complex', 'total_points': 0},
        {'collector_id': 105, 'name': 'Officer Vikram', 'assigned_area': 'Industrial Area', 'total_points': 0}
    ]
    st.session_state['collectors_df'] = pd.DataFrame(data)

if 'submissions_df' not in st.session_state:
    st.session_state['submissions_df'] = pd.DataFrame(columns=[
        'submission_id','user_id','collector_id','waste_type','quantity','points','status','category','timestamp','area'
    ])

# -----------------------------
# 3. Sidebar Navigation
# -----------------------------
st.sidebar.title("🌿 Recycle Rewards System")
page = st.sidebar.radio("Navigation", ["Login & Submit Waste", "User Dashboard", "Leaderboard"])

# -----------------------------
# 4. PAGE: Login & Waste Submission
# -----------------------------
if page == "Login & Submit Waste":
    st.title("♻️ Recycle Rewards - Local Waste and Recycling Incentive System")

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

        # ---------------- LOGIN ----------------
        with tab1:
            st.subheader("Login")
            login_mobile = st.text_input("Enter Mobile Number", key="login_mobile")

            if st.button("Login"):
                users = st.session_state['users_df']
                if login_mobile in users['mobile'].values:
                    user_data = users[users['mobile'] == login_mobile].iloc[0]
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = {
                        'name': user_data['name'],
                        'mobile': user_data['mobile'],
                        'area': user_data['area']
                    }
                    st.success("Login successful!")

                    # Display assigned collector
                    collectors = st.session_state['collectors_df']
                    assigned = collectors[collectors['assigned_area'] == user_data['area']]
                    if not assigned.empty:
                        collector_name = assigned.iloc[0]['name']
                        st.info(f"Your Collector Assigned: **{collector_name}**")

                    st.experimental_rerun()
                else:
                    st.error("User not found. Please register first.")

        # ---------------- REGISTER ----------------
        with tab2:
            st.subheader("Register New User")
            col1, col2 = st.columns(2)

            with col1:
                u_name = st.text_input("Full Name", key="reg_name")
                u_mobile = st.text_input("Mobile Number", key="reg_mobile")

            with col2:
                u_area = st.selectbox("Your Location Area", [
                    "--Select area--",
                    'Residential Apartment Complex','Hospital','Shopping Mall',
                    'Office Complex','Market','Industrial Area'
                ], key="reg_area")

            # Show assigned collector if area selected
            if u_area != "--Select area--":
                collectors = st.session_state['collectors_df']
                assigned = collectors[collectors['assigned_area'] == u_area]
                if not assigned.empty:
                    collector_name = assigned.iloc[0]['name']
                    st.info(f"Your Collector Assigned: **{collector_name}**")

            if st.button("Register"):
                users = st.session_state['users_df']

                if not u_name or not u_mobile or u_area == "--Select area--":
                    st.error("Please fill all details properly.")
                elif u_mobile in users['mobile'].values:
                    st.warning("User already exists. Please login.")
                else:
                    new_user = {
                        'user_id': generate_user_id(),
                        'name': u_name,
                        'mobile': u_mobile,
                        'area': u_area,
                        'total_points': 0,
                        'improper_count': 0
                    }
                    st.session_state['users_df'] = pd.concat(
                        [users, pd.DataFrame([new_user])],
                        ignore_index=True
                    )
                    st.success("Registration successful! Please login.")

    else:
        user = st.session_state['current_user']
        st.success(f"Logged in as: **{user['name']}** | Area: **{user['area']}**")

        # Show assigned collector
        collectors = st.session_state['collectors_df']
        assigned = collectors[collectors['assigned_area'] == user['area']]
        if not assigned.empty:
            collector_name = assigned.iloc[0]['name']
            st.info(f"Your Collector Assigned: **{collector_name}**")

        # ----------------- Submission Form -----------------
        with st.form("waste_form"):
            st.subheader("Log New Disposal")
            w_type = st.selectbox("Waste Type", ['Plastic', 'Paper', 'Organic', 'Metal', 'Glass'])
            w_qty = st.number_input("Quantity (kg)", min_value=0.1, step=0.1)
            is_segregated = st.radio("Is it properly segregated?", ["Yes", "No"])
            submitted = st.form_submit_button("Submit to Collector")

            if submitted:
                # Point calculation
                points_map = {'Plastic': 10, 'Paper': 5, 'Organic': 2, 'Metal': 12, 'Glass': 8}
                category = "Wet" if w_type == 'Organic' else "Dry"
                earned = (w_qty * points_map[w_type]) if is_segregated == "Yes" else 0

                # Assign collector
                area_match = collectors[collectors['assigned_area'] == user['area']]
                if not area_match.empty:
                    selected_collector = area_match.sort_values('total_points').iloc[0]
                    c_id, c_name = selected_collector['collector_id'], selected_collector['name']
                    idx = collectors[collectors['collector_id'] == c_id].index[0]
                    st.session_state['collectors_df'].at[idx, 'total_points'] += earned
                else:
                    c_id, c_name = None, "Unassigned"

                # Update user info
                users = st.session_state['users_df']
                if user['mobile'] not in users['mobile'].values:
                    new_u = {'user_id': generate_user_id(), 'name': user['name'], 'mobile': user['mobile'],
                             'area': user['area'], 'total_points': earned,
                             'improper_count': 0 if is_segregated=="Yes" else 1}
                    st.session_state['users_df'] = pd.concat([users, pd.DataFrame([new_u])], ignore_index=True)
                else:
                    u_idx = users[users['mobile'] == user['mobile']].index[0]
                    st.session_state['users_df'].at[u_idx, 'total_points'] += earned
                    if is_segregated == "No":
                        st.session_state['users_df'].at[u_idx, 'improper_count'] += 1

                # Log submission
                new_sub = {
                    'submission_id': len(st.session_state['submissions_df'])+1,
                    'user_id': user['mobile'], 'collector_id': c_id,
                    'waste_type': w_type, 'quantity': w_qty, 'points': earned,
                    'status': "Proper" if is_segregated=="Yes" else "Improper",
                    'category': category, 'timestamp': datetime.now(), 'area': user['area']
                }
                st.session_state['submissions_df'] = pd.concat([st.session_state['submissions_df'], pd.DataFrame([new_sub])], ignore_index=True)
                
                st.balloons()
                st.success(f"Successfully submitted! Collector **{c_name}** notified. You earned **{earned}** points.")

# -----------------------------
# 5. PAGE: User Dashboard (Optimized 4 graphs)
# -----------------------------
elif page == "User Dashboard":
    st.title("📊 Waste Analytics Dashboard")
    df = st.session_state['submissions_df']

    if df.empty:
        st.info("No data available. Submit waste to see analytics!")
    else:
        df['date'] = pd.to_datetime(df['timestamp']).dt.date

        # Row 1: Donut & Bar
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("♻️ Waste Composition by Type")
            fig_donut = px.pie(df, names='waste_type', values='quantity', hole=0.5,
                               color_discrete_sequence=px.colors.qualitative.Safe,
                               title="Waste Composition")
            st.plotly_chart(fig_donut, use_container_width=True)

        with col2:
            st.subheader("📍 Area-wise Total Waste (kg)")
            area_waste = df.groupby('area')['quantity'].sum().reset_index()
            fig_area_bar = px.bar(area_waste, x='area', y='quantity',
                                  labels={'quantity': 'Total Waste (kg)', 'area': 'Area'},
                                  title='Total Waste Collected by Area',
                                  color='quantity', color_continuous_scale='Viridis')
            st.plotly_chart(fig_area_bar, use_container_width=True)

        # Row 2: Segregation Pie & Line Chart
        col3, col4 = st.columns(2)

        with col3:
            st.subheader("✅ Segregation Status")
            seg_status = df['status'].value_counts().reset_index()
            seg_status.columns = ['status', 'count']
            fig_seg = px.pie(seg_status, names='status', values='count',
                             color_discrete_map={'Proper':'#27ae60', 'Improper':'#c0392b'},
                             title='Proper vs Improper Segregation')
            st.plotly_chart(fig_seg, use_container_width=True)

        with col4:
            st.subheader("📈 Daily Waste Collection Trends")
            line_df = df.groupby(['date', 'area'])['quantity'].sum().reset_index()
            fig_line = px.line(line_df, x='date', y='quantity', color='area', markers=True,
                               labels={'quantity': 'Total Waste (kg)', 'date': 'Date', 'area': 'Area'},
                               title="Daily Collection Trends by Area")
            st.plotly_chart(fig_line, use_container_width=True)

# -----------------------------
# 6. PAGE: Leaderboard
# -----------------------------
elif page == "Leaderboard":
    st.title("🏆 Community Leaderboard")
    u_df = st.session_state['users_df']

    if not u_df.empty:
        top_users = u_df.sort_values(by='total_points', ascending=False).head(10)
        st.table(top_users[['name', 'area', 'total_points']])
    else:
        st.write("The race hasn't started yet!")
