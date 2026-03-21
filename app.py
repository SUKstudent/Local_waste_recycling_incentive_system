import streamlit as st
import pandas as pd
import random, string
from datetime import datetime
import plotly.express as px

# ----------------- Page Setup -----------------
st.set_page_config(page_title="Recycle Rewards", layout="wide", page_icon="♻️")
st.markdown("<h1 style='color:#2e7d32;'>♻️ Local Waste Recycling Incentive System</h1>", unsafe_allow_html=True)

# ----------------- Helper Functions -----------------
def generate_user_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

points_map = {'Plastic':8,'Paper':6,'Organic':2,'Metal':15,'Glass':10,'Hazardous':20}
area_multiplier = {"Hospital":1.2,"Industrial Area":1.3}

# ----------------- Session State -----------------
if 'users_df' not in st.session_state:
    st.session_state['users_df'] = pd.DataFrame(columns=['user_id','name','mobile','area','total_points'])
if 'collectors_df' not in st.session_state:
    st.session_state['collectors_df'] = pd.DataFrame([
        {'collector_id':101,'name':'Rajesh','assigned_area':'Market','total_points':0},
        {'collector_id':102,'name':'Anita','assigned_area':'Residential Apartment Complex','total_points':0},
        {'collector_id':103,'name':'Sam','assigned_area':'Hospital','total_points':0},
        {'collector_id':104,'name':'Priya','assigned_area':'Office Complex','total_points':0},
        {'collector_id':105,'name':'Vikram','assigned_area':'Industrial Area','total_points':0}
    ])
if 'submissions_df' not in st.session_state:
    st.session_state['submissions_df'] = pd.DataFrame(columns=[
        'submission_id','user_id','collector_id','waste_type','quantity','points','status','category','timestamp','area'
    ])
st.session_state.setdefault('logged_in', False)
st.session_state.setdefault('current_user', {})

# ----------------- Login/Register -----------------
if not st.session_state['logged_in']:
    tab1, tab2 = st.tabs(["Login","Register"])
    
    with tab1:
        mobile = st.text_input("Mobile Number")
        if st.button("Login"):
            u = st.session_state['users_df'][st.session_state['users_df']['mobile']==mobile]
            if not u.empty:
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = u.iloc[0].to_dict()
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("User not found. Please register first.")

    with tab2:
        name = st.text_input("Full Name")
        mobile = st.text_input("Mobile Number")
        area = st.selectbox("Area", ["Residential Apartment Complex","Hospital","Shopping Mall","Office Complex","Market","Industrial Area"])
        if st.button("Register"):
            new_user = {'user_id':generate_user_id(),'name':name,'mobile':mobile,'area':area,'total_points':0}
            st.session_state['users_df'] = pd.concat([st.session_state['users_df'], pd.DataFrame([new_user])], ignore_index=True)
            st.success("Registered successfully! Please login.")

# ----------------- Logged In Portal -----------------
else:
    user = st.session_state['current_user']
    st.success(f"Welcome {user['name']} | Area: {user['area']}")

    # ----------------- Default Area-wise Waste Types -----------------
    st.subheader("🗂 Area-wise Waste Types")
    area_waste_default = {
        "Residential Apartment Complex": ["Plastic","Paper","Organic","Metal","Glass"],
        "Hospital": ["Plastic","Paper","Organic","Metal","Glass","Hazardous"],
        "Shopping Mall": ["Plastic","Paper","Organic","Metal","Glass"],
        "Office Complex": ["Plastic","Paper","Metal","Glass"],
        "Market": ["Plastic","Paper","Organic","Glass"],
        "Industrial Area": ["Plastic","Paper","Organic","Metal","Glass","Hazardous"]
    }
    default_df = pd.DataFrame([{"Area":a, "Waste Types":", ".join(ws)} for a,ws in area_waste_default.items()])
    st.table(default_df)

    # ----------------- Multi-Waste Submission Form -----------------
    st.subheader("Submit Your Wastes")
    wastes_for_area = area_waste_default[user['area']]
    submitted_wastes = {}
    for w in wastes_for_area:
        qty = st.number_input(f"Quantity of {w} (kg)", min_value=0.0, step=0.1)
        if qty > 0: submitted_wastes[w] = qty

    if st.button("Submit All"):
        if submitted_wastes:
            collector = st.session_state['collectors_df'][st.session_state['collectors_df']['assigned_area']==user['area']].iloc[0]
            for w_type, w_qty in submitted_wastes.items():
                category = "Wet" if w_type=="Organic" else "Special" if w_type=="Hazardous" else "Dry"
                points = w_qty * points_map[w_type] * area_multiplier.get(user['area'],1.0)
                new_sub = {
                    'submission_id': len(st.session_state['submissions_df'])+1,
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
                st.session_state['submissions_df'] = pd.concat([st.session_state['submissions_df'], pd.DataFrame([new_sub])], ignore_index=True)
                # Update user points
                idx = st.session_state['users_df'][st.session_state['users_df']['mobile']==user['mobile']].index[0]
                st.session_state['users_df'].at[idx, 'total_points'] += points
            st.success(f"Submitted {len(submitted_wastes)} waste types successfully! Points updated.")

    # ----------------- Sidebar Filters -----------------
    st.sidebar.subheader("📌 Filter by Area & Date")
    df = st.session_state['submissions_df']
    area_filter = st.sidebar.multiselect("Select Area", options=df['area'].unique() if not df.empty else [], default=df['area'].unique() if not df.empty else [])
    selected_date = st.sidebar.date_input("Select Date", value=pd.to_datetime(df['timestamp']).max().date() if not df.empty else datetime.today().date())
    filtered_df = df[(df['area'].isin(area_filter)) & (pd.to_datetime(df['timestamp']).dt.date==selected_date)] if not df.empty else df

    # ----------------- Dashboard -----------------
    if not filtered_df.empty:
        st.subheader("Waste Distribution")
        waste_dist = filtered_df.groupby('waste_type')['quantity'].sum().reset_index()
        fig1 = px.pie(waste_dist, names='waste_type', values='quantity', title="Waste Composition")
        fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader("Area-wise Waste Collection")
        area_df = filtered_df.groupby('area')['quantity'].sum().reset_index()
        fig2 = px.bar(area_df, x='area', y='quantity', color='area', labels={'quantity':'Total Waste (kg)'})
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Leaderboard")
        leaderboard = st.session_state['users_df'].sort_values('total_points', ascending=False)
        st.table(leaderboard[['name','area','total_points']].reset_index(drop=True))
