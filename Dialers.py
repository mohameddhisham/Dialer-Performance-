import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
import plotly.express as px
import warnings
import math
import base64

# Page config MUST be called before any other Streamlit command
st.set_page_config(layout="wide", page_title="Dialers Performance Dashboard")

# Suppress warnings
warnings.filterwarnings("ignore")

# --- PATH CONFIGURATION ---
logo_filename = 'Screenshot 2025-11-26 174333.png'
logo_path = os.path.join(os.getcwd(), logo_filename) 

if not os.path.exists(logo_path):
    logo_path = logo_filename

# --- 2. DATA LOADING FUNCTION ---
@st.cache_data
def load_raw_data():
    BASE_PATH = "./" 
    try:
        df_attendance = pd.read_excel(f"{BASE_PATH}Dialers Attendance.xlsx")
        df_sheet2 = pd.read_excel(f"{BASE_PATH}sheet2.xlsx") 
        df_sales = pd.read_csv(f"{BASE_PATH}sales.csv")
        df_oplans = pd.read_csv(f"{BASE_PATH}O_Plan_Leads.csv")
        df_others = pd.read_csv(f"{BASE_PATH}Other_Leads.csv")
        return df_attendance, df_sales, df_oplans, df_others, df_sheet2
    except Exception as e:
        st.error(f"Error loading files: {e}")
        st.stop()

df_attendance, df_sales, df_oplans, df_others, df_sheet2 = load_raw_data()

# --- 3. CUSTOM STYLING ---
st.markdown("""
<style>
    :root{
        --bg-main: #000000;
        --panel-bg: #2b2a2a;
        --sidebar-bg: #2a2929;
        --accent-orange: #ff5a1f;
        --kpi-orange: #ff6a3d;
    }
    .stApp { background-color: var(--bg-main); }
    section[data-testid="stSidebar"] {
        background-color: var(--sidebar-bg);
        border-right: 1px solid var(--accent-orange);
    }
    .dashboard-container {
        background-color: var(--panel-bg);
        padding: 18px;
        border-radius: 18px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.6);
    }
    .kpi-card-red {
        background-color: var(--kpi-orange);
        padding: 18px;
        border-radius: 18px;
        text-align: center;
        color: white;
        margin: 12px auto;
        font-weight: bold;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-shadow: 0 8px 18px rgba(0,0,0,0.55);
        width: 92%;
    }
    .kpi-card-red h3 { color: white !important; font-size: 18px; margin: 0; }
    .kpi-card-red p { font-size: 34px; margin: 0; text-decoration: underline; font-weight: 800; }
    .chart-title-p { color: #ffffff; font-size: 22px; font-weight: 700; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 4. GLOBAL CONFIG & HELPERS ---
DATE_COLUMN_SALES = 'created time'
DATE_VARIATIONS = ['created time', 'Created Time', 'Date', 'date', 'Timestamp']
DIALER_COLUMN = 'dialer'
DIALER_VARIATIONS = ['dialer', 'Dialer', 'Agent', 'agent', 'sales_rep', 'Other Leads Dialer']
# HARDCODED DIALERS AS REQUESTED
TARGET_DIALERS = ["All Dialers", "SA2", "SA3", "SA4", "HU1"]
DIALER_COLORS = {'SA2': '#8C1007', 'SA3': '#EB5A3C', 'SA4': '#DF9755', 'HU1': "#83CBE7"}

def _standardize_df(df, date_col_name, dialer_col_name):
    df_local = df.copy()
    found_date = next((c for c in df_local.columns if c.lower() in [v.lower() for v in DATE_VARIATIONS]), None)
    if found_date: df_local = df_local.rename(columns={found_date: date_col_name})
    found_dialer = next((c for c in df_local.columns if c in DIALER_VARIATIONS), None)
    if found_dialer: df_local = df_local.rename(columns={found_dialer: dialer_col_name})
    if dialer_col_name in df_local.columns:
        df_local[dialer_col_name] = df_local[dialer_col_name].astype(str).str.strip().str.upper()
    if date_col_name in df_local.columns:
        df_local[date_col_name] = pd.to_datetime(df_local[date_col_name], errors='coerce', dayfirst=True)
        df_local = df_local.dropna(subset=[date_col_name])
    return df_local

def _apply_filters(df, date_col, dialer_col, year, selected_dialer):
    if df.empty: return df
    df = df[df[date_col].dt.year == year]
    if selected_dialer != "All Dialers":
        df = df[df[dialer_col] == selected_dialer.upper()]
    return df

# --- SIDEBAR GLOBAL FILTERS ---
if os.path.exists(logo_path):
    with open(logo_path, "rb") as f:
        _b64 = base64.b64encode(f.read()).decode()
    st.sidebar.markdown(f"<div style='text-align:center;'><img src='data:image/png;base64,{_b64}' style='width:180px;border-radius:8px;'></div>", unsafe_allow_html=True)

st.sidebar.markdown("---")
page = st.sidebar.radio("Select Dashboard View", ["Sales Performance", "Oplans Performance", "Others Performance"])

st.sidebar.markdown("---")
st.sidebar.subheader("Annual Filters")
selected_year = st.sidebar.selectbox("Select Year", options=[2025, 2026], index=0)
selected_dialer = st.sidebar.radio("Select Dialer", options=TARGET_DIALERS)

# --- PAGE FUNCTIONS ---

def show_sales_dashboard():
    df_s = _standardize_df(df_sales, DATE_COLUMN_SALES, DIALER_COLUMN)
    df_o = _standardize_df(df_oplans, DATE_COLUMN_SALES, DIALER_COLUMN)
    
    df_s_f = _apply_filters(df_s, DATE_COLUMN_SALES, DIALER_COLUMN, selected_year, selected_dialer)
    
    # Exclude unwanted rows
    client_col = next((C for C in df_s_f.columns if 'client' in C.lower()), None)
    if client_col:
        df_s_f = df_s_f[~df_s_f[client_col].astype(str).str.contains('PPO-Braces chasing', case=False, na=False)]

    total_sales = len(df_s_f)
    avg_per_month = round(total_sales / 12, 1)

    with st.container():
        st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f'<p class="chart-title-p">Annual Sales Trend - {selected_year}</p>', unsafe_allow_html=True)
            df_trend = df_s_f.groupby([df_s_f[DATE_COLUMN_SALES].dt.normalize().rename('Date'), DIALER_COLUMN]).size().reset_index(name='Count')
            fig = px.line(df_trend, x='Date', y='Count', color=DIALER_COLUMN, color_discrete_map=DIALER_COLORS, line_shape='spline')
            fig.update_layout(plot_bgcolor='#1e1e1e', paper_bgcolor='#1e1e1e', font_color='white', height=500)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown(f'<div class="kpi-card-red"><h3>Total Sales</h3><p>{total_sales}</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-card-red"><h3>Avg / Month</h3><p>{avg_per_month}</p></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def show_oplans_dashboard():
    df_o = _standardize_df(df_oplans, DATE_COLUMN_SALES, DIALER_COLUMN)
    df_f = _apply_filters(df_o, DATE_COLUMN_SALES, DIALER_COLUMN, selected_year, selected_dialer)
    
    total_op = len(df_f)
    
    with st.container():
        st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f'<p class="chart-title-p">Annual Oplans Trend - {selected_year}</p>', unsafe_allow_html=True)
            df_trend = df_f.groupby([df_f[DATE_COLUMN_SALES].dt.normalize().rename('Date'), DIALER_COLUMN]).size().reset_index(name='Count')
            fig = px.line(df_trend, x='Date', y='Count', color=DIALER_COLUMN, color_discrete_map=DIALER_COLORS, line_shape='spline')
            fig.update_layout(plot_bgcolor='#1e1e1e', paper_bgcolor='#1e1e1e', font_color='white', height=500)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown(f'<div class="kpi-card-red"><h3>Total Oplans</h3><p>{total_op}</p></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def show_others_page():
    df_oth = _standardize_df(df_others, DATE_COLUMN_SALES, DIALER_COLUMN)
    df_f = _apply_filters(df_oth, DATE_COLUMN_SALES, DIALER_COLUMN, selected_year, selected_dialer)
    
    total_oth = len(df_f)

    with st.container():
        st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f'<p class="chart-title-p">Annual Others Trend - {selected_year}</p>', unsafe_allow_html=True)
            df_trend = df_f.groupby([df_f[DATE_COLUMN_SALES].dt.normalize().rename('Date'), DIALER_COLUMN]).size().reset_index(name='Count')
            fig = px.line(df_trend, x='Date', y='Count', color=DIALER_COLUMN, color_discrete_map=DIALER_COLORS, line_shape='spline')
            fig.update_layout(plot_bgcolor='#1e1e1e', paper_bgcolor='#1e1e1e', font_color='white', height=500)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown(f'<div class="kpi-card-red"><h3>Total Others</h3><p>{total_oth}</p></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Main Navigation Logic
if page == "Sales Performance":
    show_sales_dashboard()
elif page == "Oplans Performance":
    show_oplans_dashboard()
elif page == "Others Performance":
    show_others_page()
