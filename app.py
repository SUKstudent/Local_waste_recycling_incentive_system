import streamlit as st
import pandas as pd
import random, string
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# ----------------------------- Page Config -----------------------------
st.set_page_config(page_title="Recycle Rewards", layout="wide", page_icon="♻️")

# ----------------------------- Sidebar Logo + Logout -----------------------------
st.sidebar.image("GreenBin.jpg", width=150)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['current_user'] = {}

if st.session_state['logged_in']:
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['current_user'] = {}
        st.experimental_rerun()

# ----------------------------- Session State -----------------------------
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

points_map = {'Plastic':10, 'Paper':5, 'Organic':2, 'Metal':12, 'Glass':8, 'Hazardous':20}
area_multiplier = {"Hospital":1.2,"Industrial Area":1.3}

# ----------------------------- Login/Register -----------------------------
if not st.session_state['logged_in']:
    st.subheader("User Portal")
    tab1, tab2 = st.tabs(["Login","Register"])
    
    # ----- Login -----
    with tab1:
        login_mobile = st.text_input("Mobile Number", key="login_mobile")
        if st.button("Login"):
            users = st.session_state['users_df']
            matched_users = users[users['mobile']==login_mobile]
            if not matched_users.empty:
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = matched_users.iloc[0].to_dict()
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("User not found. Please register first.")
    
    # ----- Register -----
    with tab2:
        u_name = st.text_input("Full Name", key="reg_name")
        u_mobile = st.text_input("Mobile Number", key="reg_mobile")
        u_area = st.selectbox("Your Area", ["Residential Apartment Complex","Hospital","Shopping Mall",
                                            "Office Complex","Market","Industrial Area"])
        if st.button("Register"):
            if not u_name or not u_mobile:
                st.error("Fill all details")
            else:
                new_user = {'user_id': ''.join(random.choices(string.ascii_letters+string.digits,k=8)),
                            'name': u_name, 'mobile': u_mobile, 'area': u_area,
                            'total_points':0, 'improper_count':0}
                st.session_state['users_df'] = pd.concat([st.session_state['users_df'], pd.DataFrame([new_user])], ignore_index=True)
                st.success("Registered successfully! Please login.")

# ----------------------------- Logged In Portal -----------------------------
else:
    user = st.session_state['current_user']
    st.success(f"Logged in as: {user['name']} | Area: {user['area']}")
    
    # Default area-wise wastes
    area_waste_default = {
        "Residential Apartment Complex":["Plastic","Paper","Organic","Metal","Glass"],
        "Hospital":["Plastic","Paper","Organic","Metal","Glass","Hazardous"],
        "Shopping Mall":["Plastic","Paper","Organic","Metal","Glass"],
        "Office Complex":["Plastic","Paper","Metal","Glass"],
        "Market":["Plastic","Paper","Organic","Glass"],
        "Industrial Area":["Plastic","Paper","Organic","Metal","Glass","Hazardous"]
    }
    st.subheader("🗂 Area-wise Waste Types")
    default_df = pd.DataFrame([{"Area":a,"Waste Types":", ".join(ws)} for a,ws in area_waste_default.items()])
    st.table(default_df)
    
    # ----------------- Multi-Waste Submission -----------------
    st.subheader("Submit Your Wastes")
    wastes_for_area = area_waste_default[user['area']]
    submitted_wastes = {}
    for w in wastes_for_area:
        qty = st.number_input(f"Quantity of {w} (kg)", min_value=0.0, step=0.1)
        if qty>0: submitted_wastes[w] = qty

    if st.button("Submit All"):
        if submitted_wastes:
            collector = st.session_state['collectors_df'][st.session_state['collectors_df']['assigned_area']==user['area']].iloc[0]
            for w_type, w_qty in submitted_wastes.items():
                category = "Wet" if w_type=="Organic" else "Special" if w_type=="Hazardous" else "Dry"
                points = w_qty * points_map[w_type] * area_multiplier.get(user['area'],1.0)
                new_sub = {'submission_id':len(st.session_state['submissions_df'])+1,
                           'user_id':user['mobile'],'collector_id':collector['collector_id'],
                           'waste_type':w_type,'quantity':w_qty,'points':points,
                           'status':"Proper",'category':category,
                           'timestamp':datetime.now(),'area':user['area']}
                st.session_state['submissions_df'] = pd.concat([st.session_state['submissions_df'], pd.DataFrame([new_sub])], ignore_index=True)
                idx = st.session_state['users_df'][st.session_state['users_df']['mobile']==user['mobile']].index[0]
                st.session_state['users_df'].at[idx,'total_points'] += points
            st.success(f"Submitted {len(submitted_wastes)} waste types! Points updated.")

    # ----------------- Sidebar Filters -----------------
    st.sidebar.subheader("Filters")
    df = st.session_state['submissions_df']
    area_filter = st.sidebar.multiselect("Select Area", options=df['area'].unique() if not df.empty else [], default=df['area'].unique() if not df.empty else [])
    selected_date = st.sidebar.date_input("Select Date", value=pd.to_datetime(df['timestamp']).max().date() if not df.empty else datetime.today().date())
    filtered_df = df[(df['area'].isin(area_filter)) & (pd.to_datetime(df['timestamp']).dt.date==selected_date)] if not df.empty else df

    # ----------------- Dashboard -----------------
    st.header("📊 Recycling Dashboard")
    if not filtered_df.empty:
        # Waste distribution pie
        waste_dist = filtered_df.groupby('waste_type')['quantity'].sum().reset_index()
        fig1 = px.pie(waste_dist, names='waste_type', values='quantity', title="Waste Composition")
        fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
        st.plotly_chart(fig1, use_container_width=True)
        
        # Area-wise bar
        area_df = filtered_df.groupby('area')['quantity'].sum().reset_index()
        fig2 = px.bar(area_df, x='area', y='quantity', color='area', labels={'quantity':'Total Waste (kg)'})
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
        st.plotly_chart(fig2, use_container_width=True)
        
        # Leaderboard
        st.subheader("Leaderboard")
        leaderboard = st.session_state['users_df'].sort_values('total_points', ascending=False)
        st.table(leaderboard[['name','area','total_points']].reset_index(drop=True))
