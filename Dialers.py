import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
import plotly.express as px
import warnings
import math
import base64

# --- INITIAL CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Dialers Performance Dashboard")
warnings.filterwarnings("ignore")

# --- CUSTOM STYLING (Dark Theme & Red/Orange KPI Cards) ---
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
        padding: 20px;
        border-radius: 18px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.6);
    }
    .kpi-card-red {
        background-color: var(--kpi-orange);
        padding: 15px;
        border-radius: 18px;
        text-align: center;
        color: white;
        margin-bottom: 15px;
        height: 130px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .kpi-card-red h3 { font-size: 16px; margin: 0; color: white !important; }
    .kpi-card-red p { font-size: 28px; font-weight: 800; margin: 5px 0 0 0; text-decoration: underline; }
    .chart-title-p { color: white; font-size: 22px; font-weight: 700; text-align: center; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- CONSTANTS & HELPERS ---
DATE_COLUMN = 'created time'
DATE_VARIATIONS = ['created time', 'Created Time', 'Date', 'date', 'Timestamp']
DIALER_COLUMN = 'dialer'
DIALER_VARIATIONS = ['dialer', 'Dialer', 'Agent', 'agent', 'sales_rep', 'Other Leads Dialer']
TARGET_DIALERS = ["All Dialers", "SA2", "SA3", "SA4", "HU1"]
COLOR_MAP = {'SA2': '#8C1007', 'SA3': '#EB5A3C', 'SA4': '#DF9755', 'HU1': "#83CBE7"}

@st.cache_data
def load_data():
    try:
        df_att = pd.read_excel("Dialers Attendance.xlsx")
        df_s2 = pd.read_excel("sheet2.xlsx") 
        df_sls = pd.read_csv("sales.csv")
        df_op = pd.read_csv("O_Plan_Leads.csv")
        df_oth = pd.read_csv("Other_Leads.csv")
        return df_att, df_sls, df_op, df_oth, df_s2
    except Exception as e:
        st.error(f"File Loading Error: {e}")
        st.stop()

def standardize_df(df, date_col_name):
    df_c = df.copy()
    # Standardize Date
    found_date = next((c for c in df_c.columns if c.lower() in [v.lower() for v in DATE_VARIATIONS]), None)
    if found_date: df_c = df_c.rename(columns={found_date: date_col_name})
    # Standardize Dialer
    found_dialer = next((c for c in df_c.columns if c in DIALER_VARIATIONS), None)
    if found_dialer: df_c = df_c.rename(columns={found_dialer: DIALER_COLUMN})
    
    if DIALER_COLUMN in df_c.columns:
        df_c[DIALER_COLUMN] = df_c[DIALER_COLUMN].astype(str).str.strip().str.upper()
    if date_col_name in df_c.columns:
        df_c[date_col_name] = pd.to_datetime(df_c[date_col_name], errors='coerce', dayfirst=True)
        df_c = df_c.dropna(subset=[date_col_name])
    return df_c

def filter_data(df, year, dialer):
    if df.empty: return df
    # Filter Year
    df = df[df[DATE_COLUMN].dt.year == year]
    # Filter Dialer
    if dialer != "All Dialers":
        df = df[df[DIALER_COLUMN] == dialer.upper()]
    return df

# --- PAGE RENDERING FUNCTIONS ---

def render_dashboard(df_main, title, kpi_label, year, dialer):
    df_f = filter_data(df_main, year, dialer)
    total_count = len(df_f)
    
    # Calculate Trend
    if not df_f.empty:
        df_trend = df_f.groupby([df_f[DATE_COLUMN].dt.normalize().rename('Date'), DIALER_COLUMN]).size().reset_index(name='Count')
    else:
        df_trend = pd.DataFrame(columns=['Date', DIALER_COLUMN, 'Count'])

    with st.container():
        st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
        col_chart, col_kpi = st.columns([5, 1])
        
        with col_chart:
            st.markdown(f'<p class="chart-title-p">{title} - Full Year {year}</p>', unsafe_allow_html=True)
            if not df_trend.empty:
                fig = px.line(df_trend, x='Date', y='Count', color=DIALER_COLUMN, 
                             line_shape='spline', color_discrete_map=COLOR_MAP)
                fig.update_layout(plot_bgcolor='#1e1e1e', paper_bgcolor='#1e1e1e', 
                                 font_color='white', height=550, margin=dict(t=10))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data available for the selected year/dialer.")
        
        with col_kpi:
            st.markdown(f'<p class="chart-title-p">KPIs</p>', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-card-red"><h3>Total {kpi_label}</h3><p>{total_count}</p></div>', unsafe_allow_html=True)
            
            # Monthly Average KPI
            avg_monthly = round(total_count / 12, 1)
            st.markdown(f'<div class="kpi-card-red"><h3>Monthly Average</h3><p>{avg_monthly}</p></div>', unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

# --- MAIN EXECUTION ---

df_att, df_sls, df_op, df_oth, df_s2 = load_data()

# Logo Handling
logo_filename = 'Screenshot 2025-11-26 174333.png'
if os.path.exists(logo_filename):
    with open(logo_filename, "rb") as f:
        data = base64.b64encode(f.read()).decode()
        st.sidebar.markdown(f'<div style="text-align:center"><img src="data:image/png;base64,{data}" width="200" style="border-radius:8px; margin-bottom:20px;"></div>', unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select View", ["Sales Performance", "Oplans Performance", "Others Performance"])

st.sidebar.markdown("---")
selected_year = st.sidebar.selectbox("Select Year", [2025, 2026], index=0)
selected_dialer = st.sidebar.radio("Select Dialer", TARGET_DIALERS)

# Data Processing
df_sls_proc = standardize_df(df_sls, DATE_COLUMN)
df_op_proc = standardize_df(df_op, DATE_COLUMN)
df_oth_proc = standardize_df(df_oth, DATE_COLUMN)

if page == "Sales Performance":
    # Apply sales-specific filter (exclude retransfers/rejected if columns exist)
    render_dashboard(df_sls_proc, "Daily Sales Count Trend", "Sales", selected_year, selected_dialer)

elif page == "Oplans Performance":
    render_dashboard(df_op_proc, "Daily Oplans Count Trend", "Oplans", selected_year, selected_dialer)

elif page == "Others Performance":
    render_dashboard(df_oth_proc, "Daily Others Count Trend", "Others", selected_year, selected_dialer)

st.sidebar.markdown("---")
st.sidebar.write(f"Displaying data for: **{selected_dialer}**")
st.sidebar.write(f"Period: **Whole Year {selected_year}**")
