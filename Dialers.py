import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import calendar 
import plotly.express as px
import warnings
import math


# Page config MUST be called before any other Streamlit command
st.set_page_config(layout="wide", page_title="Dialers Performance Dashboard")

# Suppress the Plotly deprecation banner Streamlit surfaces about keyword arguments
warnings.filterwarnings("ignore", message="The keyword arguments have been deprecated and will be removed in a future release.*", category=Warning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Also hide Streamlit 'alert' boxes
#st.markdown("<style>div[role='alert']{display:none !important;}</style>", unsafe_allow_html=True)

# Page title
st.title("Dialers Performance")

# --- PATH CONFIGURATION (ADJUSTED FOR DEPLOYMENT) ---
# Use relative path './' to work on both Windows local and Linux servers (Streamlit Cloud)
# IMPORTANT: Ensure the image file is in the same folder as this script.
logo_filename = 'Screenshot 2025-11-26 174333.png'
logo_path = os.path.join(os.getcwd(), logo_filename) 

# Fallback: try looking in current directory if absolute path fails
if not os.path.exists(logo_path):
    logo_path = logo_filename

if os.path.exists(logo_path):
    try:
        import base64
        with open(logo_path, 'rb') as _f:
            _b64 = base64.b64encode(_f.read()).decode()
        # Use explicit CSS width + max-width to ensure the image scales in the sidebar
        st.sidebar.markdown(
            F"<div style='display:flex;justify-content:center;align-items:center;padding:2px 0;margin:0;'><img src='data:image/png;base64,{_b64}' style='width:200px !important;height:auto !important;max-width:100%;border-radius:8px;margin:4px 0;'></div>",
            unsafe_allow_html=True
        )
    except Exception:
        # Fallback to Streamlit image if embedding fails
        st.sidebar.image(logo_path, width=200, use_column_width=False)
        

# --- Configuration for Column Naming ---
DATE_COLUMN_SALES = 'created time'
DATE_COLUMN_SALES_VARIATIONS = ['created time', 'Created Time', 'Created time', 'Date', 'date', 'Timestamp']
DIALER_COLUMN = 'dialer'
# ADDED 'Other Leads Dialer' as requested for the Others page
DIALER_COLUMN_VARIATIONS = ['dialer', 'Dialer', 'Agent', 'agent', 'sales_rep', 'Other Leads Dialer']


# --- 2. DATA LOADING FUNCTION AND EXECUTION (Runs once) ---

@st.cache_data
def load_raw_data():
    """Loads all files from the current directory (relative path)."""
    
    # CHANGE: Use relative path './' for deployment compatibility
    BASE_PATH = "./" 
    
    try:
        # XLSX Files (Attendance is the source for all dialer names)
        df_attendance = pd.read_excel(F"{BASE_PATH}Dialers Attendance.xlsx")
        df_sheet2 = pd.read_excel(F"{BASE_PATH}sheet2.xlsx") 
        # CSV Files
        df_sales = pd.read_csv(F"{BASE_PATH}sales.csv")
        df_oplans = pd.read_csv(F"{BASE_PATH}O_Plan_Leads.csv")
        df_others = pd.read_csv(F"{BASE_PATH}Other_Leads.csv") # Load the Others file
        
        return df_attendance, df_sales, df_oplans, df_others, df_sheet2
        
    except FileNotFoundError as E:
        st.error(F"Error loading file: {E}. Please ensure all data files (xlsx/csv) are uploaded to the root directory of your repository.")
        st.stop()
    except Exception as E:
        st.error(F"An error occurred during file loading: {E}. If reading Excel files, ensure you have 'openpyxl' installed in requirements.txt.")
        st.stop()

# Load data once
df_attendance, df_sales, df_oplans, df_others, df_sheet2 = load_raw_data()

# --- 3. CUSTOM STYLING (Dark Theme and Red KPI Cards) ---

st.markdown("""
<style>
    /* Color variables for easy tuning */
    :root{
        --bg-main: #000000;         /* page background */
        --panel-bg: #2b2a2a;        /* panels / dashboard container */
        --sidebar-bg: #2a2929;      /* sidebar background */
        --accent-orange: #ff5a1f;   /* main accent (buttons, borders) */
        --accent-dark: #111010;     /* very dark for inner panels */
        --kpi-orange: #ff6a3d;      /* KPI card background */
        --muted-light: #bfb7b3;     /* muted text */
    }

    /* Main body background to a deep dark gray */
    .stApp {
        background-color: var(--bg-main);
    }
    
    /* Target the main sidebar container for background color and a left orange accent */
    section[data-testid="stSidebar"] {
        background-color: var(--sidebar-bg);
        border-right: 1px solid var(--accent-orange);
        padding-top: 6px !important;
        padding-bottom: 6pt !important;
        position: relative;
        overflow: visible;
    }

    /* Decorative rounded orange stripe on the left of the app (like the mock) */
    section[data-testid="stSidebar"]::before {
        content: '';
        position: absolute;
        left: -28px;
        top: 40px;
        width: 56px;
        height: 220px;
        background: var(--accent-orange);
        border-radius: 28px 0 0 28px;
        box-shadow: 0 0 0 6px var(--panel-bg) inset;
        z-index: 0;
    }

    /* Reduce internal container spacing inside the sidebar */
    section[data-testid="stSidebar"] > div {
        padding-top: 2px !important;
        padding-bottom: 2px !important;
        z-index: 10; /* place content above decorative stripe */
    }

    /* Force images in the sidebar to have no extra margins and sit above the stripe */
    section[data-testid="stSidebar"] img {
        margin: 0 !important;
        padding: 0 !important;
        display: block !important;
        max-width: 100% !important;
        height: auto !important;
        z-index: 10;
    }

    /* Reduce spacing around sidebar headings/markdown */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] h5,
    section[data-testid="stSidebar"] h6,
    section[data-testid="stSidebar"] .stMarkdown {
        margin-top: 2px !important;
        margin-bottom: 2px !important;
        padding: 0 !important;
        color: #ffffff;
    }

    /* Overall container for the dashboard content */
    .dashboard-container {
        background-color: var(--panel-bg);
        padding: 18px;
        border-radius: 18px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.6);
        border: 1px solid rgba(255,255,255,0.02);
    }

    /* Style for the Orange KPI Cards */
    .kpi-card-red {
        background-color: var(--kpi-orange);
        padding: 18px; /* increased padding */
        border-radius: 18px;
        text-align: center;
        color: white;
        margin: 12px auto; /* center horizontally */
        font-weight: bold;
        height: 140px; /* increased from 100px to make cards bigger */
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        gap: 8px; /* slightly larger gap */
        box-shadow: 0 8px 18px rgba(0,0,0,0.55);
        border: 2px solid rgba(0,0,0,0.12);
        width: 92%; /* allow responsive width while centering */
        max-width: 280px; /* keeps cards a consistent size */
    }
    .kpi-card-red h3 {
        color: white !important;
        font-size: 20px;
        margin: 0;
        line-height: 1.1;
        text-align: center; /* ensure label is centered */
    }
    .kpi-card-red p {
        font-size: 34px; 
        margin: 0; /* controlled by gap */
        line-height: 1.0;
        text-decoration: underline;
        text-underline-offset: 6px;
        font-weight: 800;
        text-align: center; /* ensure number is centered */
    }
    
    /* Chart title styling (slightly larger and centered feel) */
    .chart-title-p {
        color: #ffffff; 
        font-size: 22px;
        font-weight: 700;
        margin-top: 0px;
        margin-bottom: 12px;
        letter-spacing: 0.2px;
        text-align: center; /* center the chart title */
    }

    /* Make plotly dark panels match background */
    .js-plotly-plot .plotly {
        background-color: var(--panel-bg) !important;
    }

    /* Style for selectbox/dropdown labels */
    .stSelectbox > label, .stMarkdown p {
        color: #ffffff !important;
        font-weight: bold;
    }

    /* Muted table text and small widgets */
    .stDataFrame, table {
        color: var(--muted-light) !important;
    }

    /* Sidebar link color */
    .st-emotion-cache-1c9v6d9 a {
        color: #ffffff !important;
    }

    /* Tweak the legend and axis colors for plotly charts */
    .legendtext, .xtick, .ytick, .gtitle {
        fill: #ffffff !important;
        color: #ffffff !important;
    }

</style>
""", unsafe_allow_html=True)


# --- 4. DATA PROCESSING AND KPI CALCULATION FUNCTIONS (Moved out of the main block) ---

# Define the years and months for the filter (includes 2024 as per last feedback)
YEARS = [2025, 2026] 
MONTH_NAMES = ["November"]

# Helper function to find the weeks (Mon-Fri) in a selected month/year
def get_weeks_in_month(year, month_name):
    """Calculates weeks (Mon-Fri) for a given month/year, excluding Sat/Sun."""
    try:
        month_index = MONTH_NAMES.index(month_name) + 1
    except ValueError:
        return ["All Weeks"] 

    num_days = calendar.monthrange(year, month_index)[1]
    
    weeks = []
    week_counter = 1
    week_start_date = None
    
    for day in range(1, num_days + 1):
        date = datetime(year, month_index, day).date()
        day_of_week = date.weekday() # Monday is 0, Sunday is 6
        
        if day_of_week == 0:
            week_start_date = date
        
        if day_of_week == 4 and week_start_date:
            week_end_date = date
            weeks.append(F"Week {week_counter} ({week_start_date.strftime('%Y-%m-%d')} to {week_end_date.strftime('%Y-%m-%d')})")
            week_counter += 1
            week_start_date = None
            
        elif day == num_days and week_start_date and day_of_week in [0, 1, 2, 3]: 
            weeks.append(F"Week {week_counter} ({week_start_date.strftime('%Y-%m-%d')} to {date.strftime('%Y-%m-%d')})")
            
    return ["All Weeks"] + weeks

# NEW HELPER: Get all working days in a selected month or week
def get_days_in_period(year, month_name, week_str):
    """Calculates all working days (Mon-Fri) for a given month or selected week."""
    try:
        month_index = MONTH_NAMES.index(month_name) + 1
    except ValueError:
        return ["All Days"] 
        
    days = []
    
    if week_str != "All Weeks":
        # Specific Week selected: derive days from the week string
        try:
            start_date_str = week_str.split('(')[1].split(' to ')[0]
            end_date_str = week_str.split(' to ')[1].replace(')', '')
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            current_date = start_date
            while current_date <= end_date:
                # Check if it's a working day (Monday=0 to Friday=4)
                if current_date.weekday() < 5:
                    days.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
        except Exception:
            # Fallback if parsing fails
            return ["All Days"] 

    else:
        # All Weeks selected: derive all working days for the whole month
        num_days = calendar.monthrange(year, month_index)[1]
        for day in range(1, num_days + 1):
            date = datetime(year, month_index, day).date()
            # Check if it's a working day (Monday=0 to Friday=4)
            if date.weekday() < 5:
                days.append(date.strftime('%Y-%m-%d'))
                
    return ["All Days"] + days


# Helper function: Get dialers who attended during the selected month/year
@st.cache_data
def get_attended_dialers(df_attendance, selected_year, selected_month_index):
    df_attendance_copy = df_attendance.copy()
    return ["SA2"]

    # --- Standardize Dialer Column ---
    found_dialer_col = None
    for variation in DIALER_COLUMN_VARIATIONS:
        if variation in df_attendance_copy.columns:
            found_dialer_col = variation
            break
            
    if found_dialer_col:
        df_attendance_copy = df_attendance_copy.rename(columns={found_dialer_col: DIALER_COLUMN})

    # --- Standardize Date Column (Must be named 'date' for filtering below) ---
    found_date_col = None
    for variation in DATE_COLUMN_SALES_VARIATIONS:
        # Use lower() on column names for robust matching
        if variation.lower() in [c.lower() for c in df_attendance_copy.columns]:
            # Find the original name of the column that matched the variation
            found_date_col = next((c for c in df_attendance_copy.columns if c.lower() == variation.lower()), None)
            break
            
    if found_date_col and found_date_col != 'date':
        df_attendance_copy = df_attendance_copy.rename(columns={found_date_col: 'date'})
    # --- END Date FIX ---
    
    if DIALER_COLUMN not in df_attendance_copy.columns or 'date' not in df_attendance_copy.columns:
        return ["All Dialers"]
        
    # --- CRITICAL FIX: Clean and standardize dialer names to ensure consistent grouping ---
    df_attendance_copy[DIALER_COLUMN] = df_attendance_copy[DIALER_COLUMN].astype(str).str.strip().str.upper()
    # --- END CRITICAL FIX ---
    
    df_attendance_copy['date'] = pd.to_datetime(df_attendance_copy['date'], errors='coerce')
    df_filtered = df_attendance_copy.dropna(subset=['date'])

    # selected_month_index may be an int or an iterable of ints
    if isinstance(selected_month_index, (list, tuple, set)):
        df_filtered = df_filtered[(df_filtered['date'].dt.year == selected_year) & (df_filtered['date'].dt.month.isin(selected_month_index))]
    else:
        df_filtered = df_filtered[(df_filtered['date'].dt.year == selected_year) & (df_filtered['date'].dt.month == selected_month_index)]
    
    dialers = sorted(df_filtered[DIALER_COLUMN].unique().astype(str).tolist())
    
    # Remove any empty or 'NAN' dialer names from the list of options
    dialers = [d for d in dialers if d.strip() and d.upper() != 'NAN' and d.upper() != 'NONE']
    
    return ["All Dialers"] + dialers


@st.cache_data
def process_and_calculate_data(year, month_index, dialer, week_str, day_str, df_sales, df_oplans, df_attendance): 
    """
    Core function for Sales Performance page data processing and KPI calculation.
    """
    
    # Standardize column names
    df_sales = _standardize_df(df_sales, DATE_COLUMN_SALES, DIALER_COLUMN)
    df_oplans = _standardize_df(df_oplans, DATE_COLUMN_SALES, DIALER_COLUMN)
    df_attendance = _standardize_df(df_attendance, 'date', DIALER_COLUMN)

    # 1. FILTER BY MONTH/YEAR
    df_sales_filtered = _filter_by_date_local(df_sales, DATE_COLUMN_SALES, year, month_index)
    df_oplans_filtered = _filter_by_date_local(df_oplans, DATE_COLUMN_SALES, year, month_index)
    df_att_filtered = _filter_by_date_local(df_attendance, 'date', year, month_index)

    # 2. WEEK FILTERING
    df_sales_filtered = _apply_week_filter_local(df_sales_filtered, DATE_COLUMN_SALES, week_str)
    df_oplans_filtered = _apply_week_filter_local(df_oplans_filtered, DATE_COLUMN_SALES, week_str)
    df_att_filtered = _apply_week_filter_local(df_att_filtered, 'date', week_str)
    
    # 2b. DAY FILTERING 
    df_sales_filtered = _apply_day_filter_local(df_sales_filtered, DATE_COLUMN_SALES, day_str)
    df_oplans_filtered = _apply_day_filter_local(df_oplans_filtered, DATE_COLUMN_SALES, day_str)
    df_att_filtered = _apply_day_filter_local(df_att_filtered, 'date', day_str)

    # 3. DIALER FILTERING
    df_sales_filtered = _apply_dialer_filter_local(df_sales_filtered, DIALER_COLUMN, dialer)
    df_oplans_filtered = _apply_dialer_filter_local(df_oplans_filtered, DIALER_COLUMN, dialer)
    df_att_filtered = _apply_dialer_filter_local(df_att_filtered, DIALER_COLUMN, dialer)


    # --- 3a. EXCLUDE UNWANTED SALES ROWS (CLIENT / CLOSING STATUS) ---
    if not df_sales_filtered.empty:
        # find a reasonable Client column (case-insensitive match)
        client_col = next((C for C in df_sales_filtered.columns if 'client' in C.lower()), None)
        if client_col is not None:
            df_sales_filtered = df_sales_filtered[~df_sales_filtered[client_col].astype(str).str.contains('PPO-Braces chasing', case=False, na=False)]

        # find a Closing Status column (common variations)
        closing_col = next((C for C in df_sales_filtered.columns if 'closing' in C.lower() and 'status' in C.lower()), None)
        if closing_col is None:
            closing_col = next((C for C in df_sales_filtered.columns if C.lower().strip() in ['closing status', 'closing_status', 'status', 'closingstatus']), None)

        if closing_col is not None:
            exclude_statuses = {S.lower() for S in ['Retransfer to client', 'Rejected by client']}
            df_sales_filtered = df_sales_filtered[~df_sales_filtered[closing_col].astype(str).str.lower().isin(exclude_statuses)]
    

    # 4. KPI CALCULATION
    total_sales_count = df_sales_filtered.shape[0]
    total_transfers_count = df_oplans_filtered.shape[0]
    
    # Sales Percentage (Kept for calculation, even if not displayed)
    sales_percentage = round((total_sales_count / total_transfers_count) * 100) if total_transfers_count > 0 else 0
    
    # Check if sales data is available and has date column
    if not df_sales_filtered.empty and DATE_COLUMN_SALES in df_sales_filtered.columns:
        # NOTE: Date column was converted to datetime inside filter_by_date (Line 315)
        days_with_sales = df_sales_filtered[DATE_COLUMN_SALES].dt.date.nunique()
        avg_sales_per_day = round(total_sales_count / days_with_sales) if days_with_sales > 0 else 0
    else:
        days_with_sales = 0
        avg_sales_per_day = 0
    
    # Attendance KPIs
    dialers_present = df_att_filtered[DIALER_COLUMN].nunique() if DIALER_COLUMN in df_att_filtered.columns else 0
    # Average attendance per dialer (mean of the 'attendance' column)
    avg_att_per_dialer = round(df_att_filtered['attendance'].mean()) if dialers_present > 0 and 'attendance' in df_att_filtered.columns else 0
    
    # Total attendance for the period
    total_att_count = df_att_filtered['attendance'].sum() if 'attendance' in df_att_filtered.columns else 0
    # Days with attendance
    days_with_att = df_att_filtered['date'].dt.date.nunique() if 'date' in df_att_filtered.columns else 0
    # Average attendance per day
    avg_att_per_day = round(total_att_count / days_with_att) if days_with_att > 0 else 0

    
    # 5. LINE CHART DATA PREPARATION
    if not df_sales_filtered.empty and DATE_COLUMN_SALES in df_sales_filtered.columns and DIALER_COLUMN in df_sales_filtered.columns:
        # Group by a normalized datetime Date (no time) and keep as datetime dtype for proper chronological plotting
        df_sales_trend = df_sales_filtered.groupby([
            df_sales_filtered[DATE_COLUMN_SALES].dt.normalize().rename('Date'), 
            DIALER_COLUMN 
        ]).size().reset_index(name='Sales_Count')
        # Ensure the Date column is datetime and sort chronologically to avoid zig-zag lines when Plotly connects points
        df_sales_trend['Date'] = pd.to_datetime(df_sales_trend['Date'])
        df_sales_trend = df_sales_trend.sort_values(['Date', DIALER_COLUMN])
    else:
        df_sales_trend = pd.DataFrame(columns=['Date', DIALER_COLUMN, 'Sales_Count'])
    
    
    return df_sales_trend, sales_percentage, avg_sales_per_day, avg_att_per_dialer, avg_att_per_day, total_sales_count

# --- 5. PAGE FUNCTIONS ---

# Helper function to standardize columns (used by multiple pages)
def _standardize_df(df, date_col_na
