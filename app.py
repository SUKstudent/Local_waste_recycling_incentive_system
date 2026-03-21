import streamlit as st
import pandas as pd
import random
import string
import plotly.express as px
from datetime import datetime, date, timedelta

# -----------------------------
# Page Config & Styling
# -----------------------------
st.set_page_config(page_title="Recycle Rewards - Daily Updates", layout="wide")
st.markdown("""
<style>
.main { background-color: #f9fbf9; }
.stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #2e7d32; color: white; }
.stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Helper Functions
# -----------------------------
def generate_user_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_otp(length=4):
    return ''.join(random.choices(string.digits, k=length))

def update_daily_points():
    """Update total_points daily for all users based on today's submissions"""
    df_sub = st.session_state['submissions_df']
    users = st.session_state['users_df']
    today = date.today()
    recent_subs = df_sub[pd.to_datetime(df_sub['timestamp']).dt.date==today]
    if recent_subs.empty:
        return
    for _, row in recent_subs.iterrows():
        u_idx = users[users['mobile']==row['user_id']].index[0]
        st.session_state['users_df'].at[u_idx,'total_points'] = users.at[u_idx,'total_points'] + row['points']
    st.session_state['last_points_update'] = today

# -----------------------------
# Initialize Session State
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
if 'otp_sent' not in st.session_state: st.session_state['otp_sent'] = False
if 'otp_value' not in st.session_state: st.session_state['otp_value'] = ''
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'current_user' not in st.session_state: st.session_state['current_user'] = {}
if 'last_points_update' not in st.session_state: st.session_state['last_points_update'] = None

# -----------------------------
# Role Selection
# -----------------------------
role = st.sidebar.selectbox("Login as", ["User", "Admin"])

# -----------------------------
# USER / CITIZEN FLOW
# -----------------------------
if role == "User":
    st.title("♻️ Recycle Rewards - User Portal")

    if not st.session_state['logged_in']:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

        # --- LOGIN ---
        with tab1:
            login_mobile = st.text_input("Enter Mobile Number", key="login_mobile")
            if st.button("Login"):
                users = st.session_state['users_df']
                if login_mobile in users['mobile'].values:
                    user_data = users[users['mobile']==login_mobile].iloc[0]
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

        # --- REGISTER ---
        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                u_name = st.text_input("Full Name", key="reg_name")
                u_mobile = st.text_input("Mobile Number", key="reg_mobile")
            with col2:
                u_area = st.selectbox("Your Location Area", [
                    "--Select area--",'Residential Apartment Complex','Hospital','Shopping Mall',
                    'Office Complex','Market','Industrial Area'], key="reg_area")

            # Show collector if selected
            if u_area != "--Select area--":
                assigned = st.session_state['collectors_df'][st.session_state['collectors_df']['assigned_area']==u_area]
                if not assigned.empty:
                    st.info(f"Your Collector Assigned: **{assigned.iloc[0]['name']}**")

            # Auto OTP
            if st.button("Send OTP"):
                if not u_name or not u_mobile or u_area=="--Select area--":
                    st.error("Fill all details before sending OTP")
                else:
                    st.session_state['otp_value'] = generate_otp()
                    st.session_state['otp_sent'] = True
                    st.success(f"OTP sent to {u_mobile} ✅ (Auto verified for demo)")

            if st.session_state['otp_sent']:
                st.info(f"OTP **{st.session_state['otp_value']}** auto-verified ✅")
                st.success("Registration successful! You can now login.")
                # Save user
                if u_mobile not in st.session_state['users_df']['mobile'].values:
                    new_user = {'user_id': generate_user_id(),'name': u_name,'mobile': u_mobile,
                                'area': u_area,'total_points':0,'improper_count':0}
                    st.session_state['users_df'] = pd.concat([st.session_state['users_df'], pd.DataFrame([new_user])], ignore_index=True)
                st.session_state['otp_sent'] = False

    else:
        # --- AFTER LOGIN ---
        user = st.session_state['current_user']
        st.success(f"Logged in as: **{user['name']}** | Area: **{user['area']}**")
        # Show assigned collector
        assigned = st.session_state['collectors_df'][st.session_state['collectors_df']['assigned_area']==user['area']]
        if not assigned.empty: st.info(f"Your Collector Assigned: **{assigned.iloc[0]['name']}**")

        # Waste Submission
        with st.form("waste_form"):
            w_type = st.selectbox("Waste Type", ['Plastic','Paper','Organic','Metal','Glass'])
            w_qty = st.number_input("Quantity (kg)", min_value=0.1, step=0.1)
            is_segregated = st.radio("Is it properly segregated?", ["Yes","No"])
            submitted = st.form_submit_button("Submit")
            if submitted:
                points_map = {'Plastic':10,'Paper':5,'Organic':2,'Metal':12,'Glass':8}
                category = "Wet" if w_type=="Organic" else "Dry"
                earned = w_qty*points_map[w_type] if is_segregated=="Yes" else 0

                # Assign collector
                area_match = st.session_state['collectors_df'][st.session_state['collectors_df']['assigned_area']==user['area']]
                if not area_match.empty:
                    selected = area_match.sort_values('total_points').iloc[0]
                    c_id, c_name = selected['collector_id'], selected['name']
                    idx = st.session_state['collectors_df'][st.session_state['collectors_df']['collector_id']==c_id].index[0]
                    st.session_state['collectors_df'].at[idx,'total_points'] += earned
                else: c_id, c_name = None,"Unassigned"

                # Update user points immediately for daily points
                u_idx = st.session_state['users_df'][st.session_state['users_df']['mobile']==user['mobile']].index[0]
                st.session_state['users_df'].at[u_idx,'total_points'] += earned
                if is_segregated=="No": st.session_state['users_df'].at[u_idx,'improper_count'] += 1

                # Log submission
                new_sub = {'submission_id':len(st.session_state['submissions_df'])+1,
                           'user_id':user['mobile'],'collector_id':c_id,'waste_type':w_type,
                           'quantity':w_qty,'points':earned,'status':"Proper" if is_segregated=="Yes" else "Improper",
                           'category':category,'timestamp':datetime.now(),'area':user['area']}
                st.session_state['submissions_df'] = pd.concat([st.session_state['submissions_df'], pd.DataFrame([new_sub])], ignore_index=True)
                st.balloons()
                st.success(f"Submitted! Collector **{c_name}** notified. Points earned: **{earned}**")
                st.experimental_rerun()  # real-time refresh

# -----------------------------
# ADMIN FLOW
# -----------------------------
elif role == "Admin":
    st.title("🏛️ Municipal Admin Dashboard")
    st.subheader("Login with admin credentials")
    admin_user = st.text_input("Username")
    admin_pass = st.text_input("Password", type="password")
    if st.button("Admin Login"):
        if admin_user=="admin" and admin_pass=="admin123":
            st.success("Admin login successful!")

            # Automatically update daily points if not updated today
            if st.session_state['last_points_update'] != date.today():
                update_daily_points()
                st.info(f"Daily points updated for {date.today()} ✅")

            df = st.session_state['submissions_df']
            collectors = st.session_state['collectors_df']
            users = st.session_state['users_df']

            # Collector Performance
            st.subheader("Collector Performance")
            st.table(collectors[['name','assigned_area','total_points']])

            # Area-wise Waste
            st.subheader("Area-wise Waste Collection")
            if not df.empty:
                area_waste = df.groupby('area')['quantity'].sum().reset_index()
                fig = px.bar(area_waste,x='area',y='quantity',title="Waste Collected per Area", labels={'quantity':'Total Waste (kg)'})
                st.plotly_chart(fig,use_container_width=True)

            # Segregation Pie
            st.subheader("Segregation Status")
            if not df.empty:
                status_df = df['status'].value_counts().reset_index()
                status_df.columns=['status','count']
                fig2 = px.pie(status_df,names='status',values='count',color_discrete_map={'Proper':'#27ae60','Improper':'#c0392b'})
                st.plotly_chart(fig2,use_container_width=True)

            # Daily Trends Line Chart
            st.subheader("Daily Collection Trends")
            if not df.empty:
                df['date'] = pd.to_datetime(df['timestamp']).dt.date
                line_df = df.groupby(['date','area'])['quantity'].sum().reset_index()
                fig3 = px.line(line_df,x='date',y='quantity',color='area',markers=True,
                               labels={'quantity':'Total Waste (kg)','date':'Date','area':'Area'})
                st.plotly_chart(fig3,use_container_width=True)

            # Leaderboard
            st.subheader("Community Leaderboard")
            if not users.empty:
                top_users = users.sort_values('total_points',ascending=False).head(10)
                st.table(top_users[['name','area','total_points']])
        else:
            st.error("Invalid admin credentials")
