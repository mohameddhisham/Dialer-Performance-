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
MONTH_NAMES = list(calendar.month_name)[1:]

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
def _standardize_df(df, date_col_name, dialer_col_name):
    df_local = df.copy()
    
    # Standardize Date Column
    found_date = next((c for c in df_local.columns if c.lower() in [v.lower() for v in DATE_COLUMN_SALES_VARIATIONS]), None)
    if found_date and found_date != date_col_name:
        df_local = df_local.rename(columns={found_date: date_col_name})

    # Standardize Dialer Column
    found_dialer = next((c for c in df_local.columns if c in DIALER_COLUMN_VARIATIONS), None) # Use direct match for Dialer Variations
    
    if found_dialer and found_dialer != dialer_col_name:
        df_local = df_local.rename(columns={found_dialer: dialer_col_name})
    
    # CRITICAL FIX: Robust Data Cleaning (Strip/Uppercase)
    if dialer_col_name in df_local.columns:
        df_local[dialer_col_name] = df_local[dialer_col_name].astype(str).str.strip().str.upper().replace('NAN', np.nan)
        
    return df_local

# Helper function to filter by date (used by multiple pages)
def _filter_by_date_local(df, date_col, year, months):
    if date_col not in df.columns:
        return pd.DataFrame()
    df_local = df.copy()
    # Try parsing with dayfirst=True to handle European date formats (common in spreadsheets)
    df_local[date_col] = pd.to_datetime(df_local[date_col], errors='coerce',dayfirst=True)
    df_local = df_local.dropna(subset=[date_col])
    try:
        year = int(year)
    except Exception:
        pass
    if isinstance(months, (list, tuple, set)):
        months_list = [int(m) for m in months]
        df_local = df_local[(df_local[date_col].dt.year == year) & (df_local[date_col].dt.month.isin(months_list))]
    else:
        df_local = df_local[(df_local[date_col].dt.year == year) & (df_local[date_col].dt.month == int(months))]
    return df_local

# Helper function to apply week filter (used by multiple pages)
def _apply_week_filter_local(df, date_col, week_str):
    if week_str != "All Weeks" and not df.empty and date_col in df.columns:
        try:
            start_date_str = week_str.split('(')[1].split(' to ')[0]
            end_date_str = week_str.split(' to ')[1].replace(')', '')
            start_date = pd.to_datetime(start_date_str).date()
            end_date = pd.to_datetime(end_date_str).date()

            # Must convert to date type for comparison
            df['DateOnly'] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True).dt.date
            # Filter for dates within the week range (Mon=0 to Fri=4)
            df['Weekday'] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True).dt.weekday
            df_out = df[(df['DateOnly'] >= start_date) & (df['DateOnly'] <= end_date) & (df['Weekday'] <= 4)].copy()
            df_out.drop(columns=['DateOnly', 'Weekday'], inplace=True, errors='ignore')
            return df_out
        except Exception:
            return df
    return df

# NEW HELPER: Helper function to apply day filter
def _apply_day_filter_local(df, date_col, selected_day_str):
    if selected_day_str != "All Days" and not df.empty and date_col in df.columns:
        try:
            target_date = pd.to_datetime(selected_day_str).date()
            
            # Ensure the date column is clean and converted to date part only
            df['DateOnly'] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True).dt.date
            df_out = df[df['DateOnly'] == target_date].copy()
            df_out.drop(columns=['DateOnly'], inplace=True, errors='ignore')
            return df_out
        except Exception:
            return df
    return df

# Helper function to apply dialer filter (used by multiple pages)
def _apply_dialer_filter_local(df, dialer_col, selected_dialer):
    if df.empty or dialer_col not in df.columns:
        return df

    if isinstance(selected_dialer, (list, tuple, set)):
        if len(selected_dialer) == 0 or 'All Dialers' in selected_dialer:
            pass
        else:
            cleaned_selected_dialers = [d.strip().upper() for d in selected_dialer if d != "All Dialers"]
            df = df[df[dialer_col].isin(cleaned_selected_dialers)].copy()
    elif selected_dialer != "All Dialers":
        cleaned_dialer = selected_dialer.strip().upper()
        df = df[df[dialer_col] == cleaned_dialer].copy()
    
    return df

def show_sales_dashboard(df_attendance, df_sales, df_oplans):
    """
    Renders the Sales Performance Dashboard (the original content).
    """
    # --- FILTER WIDGETS MOVED TO SIDEBAR ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filter Sales Data")

    # 4a. Year Selector
    selected_year = st.sidebar.selectbox("Select Year", options=YEARS, index=YEARS.index(2025) if 2025 in YEARS else 0, key="year_sales")

    # 4b. Month Selector (multi-select)
    default_month_name = "November"
    selected_month_names = st.sidebar.multiselect(
        "Select Month (you may choose multiple)",
        options=MONTH_NAMES,
        default=[default_month_name],
        key="month_sales"
    )
    # Ensure at least one month is selected
    if not selected_month_names:
        selected_month_names = [default_month_name]
    # Convert month names to month indices (1-12)
    selected_month_index = [MONTH_NAMES.index(M) + 1 for M in selected_month_names]

    # 4c. Week Selector (Dynamic). Disabled when multiple months selected.
    if len(selected_month_index) == 1:
        single_month_name = selected_month_names[0]
        weeks_list = get_weeks_in_month(selected_year, single_month_name)
        selected_week = st.sidebar.selectbox("Select Week", options=weeks_list, key="week_sales")
        
        # 4d. Day Selector (Dynamic). Enabled only when a single month is selected.
        days_list = get_days_in_period(selected_year, single_month_name, selected_week)
        selected_day = st.sidebar.selectbox("Select Day", options=days_list, key="day_sales")
    else:
        selected_week = "All Weeks"
        selected_day = "All Days"
        st.sidebar.markdown("_Week and Day selection disabled for multiple months._")


    # 4e. Dialer Selector (NOW MULTI-SELECT - Dialers returned are already Uppercase/Cleaned)
    dialers_list = get_attended_dialers(df_attendance, selected_year, selected_month_index)
    selected_dialer = st.sidebar.multiselect("Select Dialer (multiple)", options=dialers_list, default=["All Dialers"], key="dialer_sales")

    # --- EXECUTE CORE FUNCTION ---
    df_sales_trend, sales_percentage, avg_sales_per_day, avg_att_per_dialer, avg_att_per_day, total_sales_count = \
        process_and_calculate_data(
            selected_year, selected_month_index, selected_dialer, selected_week, selected_day, 
            df_sales.copy(), df_oplans.copy(), df_attendance.copy()
        )

    # --- DISPLAY DASHBOARD LAYOUT (KPI Cards and Chart) ---
    with st.container():
        st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)

        # Ensure only the Chart (col2) and KPIs (col3) columns are present.
        main_body_col2, main_body_col3 = st.columns([5, 1])
        
        # --- Determine Period Label for Titles ---
        if selected_day != "All Days":
            period_label = selected_day
        elif selected_week != "All Weeks":
            period_label = selected_week
        else:
            period_label = ", ".join(selected_month_names)


        # --- Column 2: Main Content Area (Chart) ---
        with main_body_col2:
            # Row 2: Line Chart (Daily sales trend)
            st.markdown(f'<p class="chart-title-p">Daily Sales Count Trend in {period_label} {selected_year}</p>', unsafe_allow_html=True)

            if not df_sales_trend.empty:
                # Color map for consistency
                color_map_sales = {
                    'SA2': '#8C1007',
                    'SA3': '#EB5A3C',
                    'SA4': '#DF9755',
                    'HU1': "#83CBE7"
                }
                
                # Determine if we should color by Dialer (if multiple selected or All)
                if DIALER_COLUMN in df_sales_trend.columns:
                    unique_dialers_in_chart = df_sales_trend[DIALER_COLUMN].unique()
                    chart_color_col = DIALER_COLUMN
                else:
                    unique_dialers_in_chart = []
                    chart_color_col = None

                # Plot the line chart
                fig = px.line(
                    df_sales_trend, 
                    x='Date', 
                    y='Sales_Count', 
                    color=chart_color_col,
                    color_discrete_map=color_map_sales if chart_color_col else None,
                    title='', 
                    line_shape='spline'
                )

                # Style the traces
                fig.update_traces(line=dict(smoothing=1.3, width=2.5), marker=dict(size=8))
                
                # Y-axis range logic
                max_sales_val = df_sales_trend['Sales_Count'].max() if not df_sales_trend.empty else None
                # Add a small buffer so the top of the chart is above the highest point
                buffer = 3
                top_range = (max_sales_val + buffer) if (max_sales_val is not None and max_sales_val > 0) else 1

                # Customize the chart appearance for the dark theme
                fig.update_layout(
                    height=520, # make the chart taller so it fills the page
                    plot_bgcolor='#1e1e1e',
                    paper_bgcolor='#1e1e1e',
                    font_color='white',
                    legend_title_text='Dialer' if chart_color_col else None,
                    xaxis_title='Date',
                    yaxis_title='Sales Count',
                    margin=dict(l=10, r=10, t=20, b=40),
                    # Use a date x-axis so Plotly plots lines chronologically
                    xaxis={'type': 'date'},
                    # Expand the top of the y-axis by `buffer` and remove thousand separators
                    yaxis={'range': [0, top_range], 'tickformat': '.0f'}
                )
                # Ensure x-axis is treated as dates
                fig.update_xaxes(type='date')

                # Add labels (numbers) to the data points
                # Limit labels per series to avoid clutter: sample up to `max_labels` evenly
                max_labels = 8
                def add_labels_to_trace(df_to_label):
                    n = len(df_to_label)
                    if n == 0: return
                    step = max(1, math.ceil(n / max_labels))
                    sampled_idx = list(range(0, n, step))
                    
                    x_sample = df_to_label['Date'].iloc[sampled_idx]
                    y_sample = df_to_label['Sales_Count'].iloc[sampled_idx]
                    labels = y_sample.astype(int).astype(str)

                    fig.add_scatter(
                        x=x_sample, y=y_sample, 
                        mode='text', 
                        text=labels, 
                        textposition="top center", 
                        showlegend=False, 
                        textfont=dict(color='white', size=11)
                    )

                if chart_color_col:
                    for D in unique_dialers_in_chart:
                        df_subset = df_sales_trend[df_sales_trend[DIALER_COLUMN] == D].sort_values('Date')
                        add_labels_to_trace(df_subset)
                else:
                    add_labels_to_trace(df_sales_trend)


                # Render the chart with an explicit height so Streamlit reserves vertical space
                st.plotly_chart(fig, use_container_width=True, height=800, config={'displayModeBar': False})
            else:
                st.info(f"No sales data found for the selected period ({period_label}).")


        # --- Column 3: KPI Cards (Right Side) ---
        with main_body_col3:
            # --- Title for the KPI Cards ---
            st.markdown(f'<p class="chart-title-p">KPI calculations in {period_label} {selected_year}</p>', unsafe_allow_html=True)
            
            # KPI 1: Sales Count
            st.markdown(f'<div class="kpi-card-red"><h3>Total Sales Count</h3><p>{total_sales_count}</p></div>', unsafe_allow_html=True)
            
            # KPI 2: Sales % (Commented out as requested previously)
            # st.markdown(f'<div class="kpi-card-red"><h3>Sales %</h3><p>{sales_percentage}%</p></div>', unsafe_allow_html=True)
            
            # KPI 3: Average Sales per day
            st.markdown(f'<div class="kpi-card-red"><h3>Average Sales per day</h3><p>{avg_sales_per_day}</p></div>', unsafe_allow_html=True)

            # KPI 4: Average Attendance per Dialer
            st.markdown(f'<div class="kpi-card-red"><h3>Avg Attendance per Dialer</h3><p>{avg_att_per_dialer}</p></div>', unsafe_allow_html=True)

            # KPI 5: Average Attendance per day
            st.markdown(f'<div class="kpi-card-red"><h3>Avg Attendance per day</h3><p>{avg_att_per_day}</p></div>', unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)


def show_oplans_dashboard(df_attendance, df_oplans):
    """
    Renders the Oplans Performance Dashboard.
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filter Oplans Data")
    
    # Year selector
    selected_year_op = st.sidebar.selectbox("Select Year (Oplans)", options=YEARS, index=YEARS.index(2025) if 2025 in YEARS else 0, key="year_oplans")

    # Month multiselect
    default_month_name = "November"
    selected_month_names_op = st.sidebar.multiselect(
        "Select Month (you may choose multiple)",
        options=MONTH_NAMES,
        default=[default_month_name],
        key="month_oplans"
    )
    if not selected_month_names_op:
        selected_month_names_op = [default_month_name]
    selected_month_indices_op = [MONTH_NAMES.index(m) + 1 for m in selected_month_names_op]

    # Week selection disabled for multi-month selection
    if len(selected_month_indices_op) == 1:
        single_month_name_op = selected_month_names_op[0]
        weeks_list_op = get_weeks_in_month(selected_year_op, single_month_name_op)
        selected_week_op = st.sidebar.selectbox("Select Week (Oplans)", options=weeks_list_op, key="week_oplans")
        
        # Day Selector (Dynamic). Enabled only when a single month is selected.
        days_list_op = get_days_in_period(selected_year_op, single_month_name_op, selected_week_op)
        selected_day_op = st.sidebar.selectbox("Select Day (Oplans)", options=days_list_op, key="day_oplans")
    else:
        selected_week_op = "All Weeks"
        selected_day_op = "All Days"
        st.sidebar.markdown("_Week and Day selection disabled for multiple months._")

    # Dialer selector for Oplans (multi-select - Dialers returned are already Uppercase/Cleaned)
    dialers_list_op = get_attended_dialers(df_attendance, selected_year_op, selected_month_indices_op)
    selected_dialer_op = st.sidebar.multiselect("Select Dialer (Oplans)", options=dialers_list_op, default=["All Dialers"], key="dialer_oplans")

    # --- Normalize column names and CLEAN data ---
    df_oplans_local = _standardize_df(df_oplans, DATE_COLUMN_SALES, DIALER_COLUMN)
    df_attendance_local = _standardize_df(df_attendance, 'date', DIALER_COLUMN)

    # Filter oplans by selected year/month(s)
    df_oplans_filtered = _filter_by_date_local(df_oplans_local, DATE_COLUMN_SALES, selected_year_op, selected_month_indices_op)
    # Apply week filter
    df_oplans_filtered = _apply_week_filter_local(df_oplans_filtered, DATE_COLUMN_SALES, selected_week_op)
    # Apply day filter (NEW)
    df_oplans_filtered = _apply_day_filter_local(df_oplans_filtered, DATE_COLUMN_SALES, selected_day_op)
    # Apply dialer filter from the Oplans sidebar selector
    df_oplans_filtered = _apply_dialer_filter_local(df_oplans_filtered, DIALER_COLUMN, selected_dialer_op)
    
    # KPI calculations for Oplans
    total_oplans_count = df_oplans_filtered.shape[0]

    days_with_oplans_df = df_oplans_filtered[pd.to_datetime(df_oplans_filtered[DATE_COLUMN_SALES], errors='coerce').notna()]
    if not days_with_oplans_df.empty:
        unique_days = pd.to_datetime(days_with_oplans_df[DATE_COLUMN_SALES], errors='coerce').dt.date.nunique()
    else:
        unique_days = 0
    avg_oplans_per_day = round(total_oplans_count / unique_days) if unique_days > 0 else 0

    # Opener status ratio: try to find a sensible status column
    status_col = next((c for c in df_oplans_filtered.columns if 'opener' in c.lower() and 'status' in c.lower()), None)
    if status_col is None:
        status_col = next((c for c in df_oplans_filtered.columns if 'opener' in c.lower()), None)
    if status_col is None:
        status_col = next((c for c in df_oplans_filtered.columns if 'status' in c.lower()), None)


    # MODIFIED LOGIC HERE: Calculate Transfer Ratio based on explicit status list
    transfer_ratio_pct = 0
    if not df_oplans_filtered.empty and status_col in df_oplans_filtered.columns:
        df_oplans_filtered['_status_clean'] = df_oplans_filtered[status_col].astype(str).str.strip().str.upper()
        
        # Define the statuses that count as a 'transfer' (numerator) as requested by the user
        # Values confirmed by user: 'Transferred', 'Green Flag', 'Red Flags' (must be uppercase to match cleaning)
        transfer_statuses = {'TRANSFERRED', 'GREEN FLAG', 'RED FLAGS'} 
        
        # Count only the desired statuses
        transfer_count = df_oplans_filtered[
            df_oplans_filtered['_status_clean'].isin(transfer_statuses)
        ].shape[0]
        
        # Denominator is total Oplans count (already calculated)
        transfer_ratio_pct = round((transfer_count / total_oplans_count) * 100) if total_oplans_count > 0 else 0
    
    # Attendance KPIs for Oplans page
    df_att_local_filtered = _filter_by_date_local(df_attendance_local, 'date', selected_year_op, selected_month_indices_op)
    df_att_local_filtered = _apply_week_filter_local(df_att_local_filtered, 'date', selected_week_op)
    df_att_local_filtered = _apply_day_filter_local(df_att_local_filtered, 'date', selected_day_op) # Apply day filter
    df_att_local_filtered = _apply_dialer_filter_local(df_att_local_filtered, DIALER_COLUMN, selected_dialer_op)
    total_att_count_op = df_att_local_filtered['attendance'].sum() if 'attendance' in df_att_local_filtered.columns and not df_att_local_filtered.empty else 0
    days_with_att_op = df_att_local_filtered['date'].dt.date.nunique() if 'date' in df_att_local_filtered.columns and not df_att_local_filtered.empty else 0
    avg_att_per_day_op = round(total_att_count_op / days_with_att_op) if days_with_att_op > 0 else 0
    
    # --- Oplans Trend Calculation Block ---
    df_oplans_trend = pd.DataFrame(columns=['Date', DIALER_COLUMN, 'Oplan_Count'])
    if not df_oplans_filtered.empty and DATE_COLUMN_SALES in df_oplans_filtered.columns:
        df_temp = df_oplans_filtered.copy()
        
        # Use a temporary column for cleaned dialer names to handle multi-index reset later
        if DIALER_COLUMN in df_temp.columns:
            df_temp['_DialerClean'] = df_temp[DIALER_COLUMN]
        else:
            df_temp['_DialerClean'] = 'UNKNOWN'

        df_temp['Date'] = pd.to_datetime(df_temp[DATE_COLUMN_SALES], errors='coerce').dt.normalize()
        df_temp = df_temp.dropna(subset=['Date'])
        
        if DIALER_COLUMN in df_oplans_filtered.columns:
            df_oplans_trend = (
                df_temp
                .groupby(['Date', '_DialerClean'])
                .size()
                .reset_index(name='Oplan_Count')
                .rename(columns={'_DialerClean': DIALER_COLUMN})
            )
        else:
            df_oplans_trend = (
                df_temp
                .groupby('Date')
                .size()
                .reset_index(name='Oplan_Count')
            )
            df_oplans_trend[DIALER_COLUMN] = 'TOTAL' # Use a single label when no dialer column is found

        df_oplans_trend['Date'] = pd.to_datetime(df_oplans_trend['Date'])
        df_oplans_trend = df_oplans_trend.sort_values(['Date', DIALER_COLUMN])
        
        # Remove the 'UNKNOWN' group if a specific dialer was selected
        if isinstance(selected_dialer_op, (list, tuple, set)):
            if 'All Dialers' not in selected_dialer_op:
                df_oplans_trend = df_oplans_trend[df_oplans_trend[DIALER_COLUMN] != 'UNKNOWN']
        elif selected_dialer_op != 'All Dialers':
            df_oplans_trend = df_oplans_trend[df_oplans_trend[DIALER_COLUMN] != 'UNKNOWN']
            
    # --- END Oplans Trend Block ---

    # --- Determine Period Label for Titles ---
    if selected_day_op != "All Days":
        period_label = selected_day_op
    elif selected_week_op != "All Weeks":
        period_label = selected_week_op
    else:
        period_label = ", ".join(selected_month_names_op)

    # --- REMAINDER OF OPLANS PAGE DISPLAY (CHART & KPI CARDS) ---
    with st.container():
        st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)

        main_body_col2, main_body_col3 = st.columns([5, 1])

        # --- Column 2: Main Content Area (Chart) ---
        with main_body_col2:
            st.markdown(f'<p class="chart-title-p">Daily Oplans Count Trend in {period_label} {selected_year_op}</p>', unsafe_allow_html=True)
            
            if not df_oplans_trend.empty:
                # Color map can be reused or defined specifically for Oplans
                color_map_oplans = {
                    'SA2': '#8C1007',
                    'SA3': '#EB5A3C',
                    'SA4': '#DF9755',
                    'HU1': "#83CBE7"
                }

                # CHECK MODIFIED: Use the DIALER_COLUMN for color if it exists, regardless of unique count
                if DIALER_COLUMN in df_oplans_trend.columns:
                    unique_dialers_in_chart = df_oplans_trend[DIALER_COLUMN].unique()
                    chart_color_col = DIALER_COLUMN
                else:
                    unique_dialers_in_chart = []
                    chart_color_col = None

                fig = px.line(
                    df_oplans_trend, 
                    x='Date', 
                    y='Oplan_Count', 
                    color=chart_color_col,
                    color_discrete_map=color_map_oplans if chart_color_col else None,
                    title='', 
                    line_shape='spline'
                )

                fig.update_traces(line=dict(smoothing=1.3, width=2.5), marker=dict(size=8))
                
                # Y-axis range logic
                max_oplans_val = df_oplans_trend['Oplan_Count'].max() if not df_oplans_trend.empty else None
                buffer = 3
                top_range = (max_oplans_val + buffer) if (max_oplans_val is not None and max_oplans_val > 0) else 1
                
                fig.update_layout(
                    height=520,
                    plot_bgcolor='#1e1e1e',
                    paper_bgcolor='#1e1e1e',
                    font_color='white',
                    legend_title_text='Dialer' if chart_color_col else None,
                    xaxis_title='Date',
                    yaxis_title='Oplans Count',
                    margin=dict(l=10, r=10, t=20, b=40),
                    xaxis={'type': 'date'},
                    yaxis={'range': [0, top_range], 'tickformat': '.0f'}
                )
                fig.update_xaxes(type='date')

                # Add labels (numbers) to the data points
                max_labels = 8
                def add_labels_to_trace(df_to_label, color='white'):
                    n = len(df_to_label)
                    if n == 0: return
                    step = max(1, math.ceil(n / max_labels))
                    sampled_idx = list(range(0, n, step))
                    
                    x_sample = df_to_label['Date'].iloc[sampled_idx]
                    y_sample = df_to_label['Oplan_Count'].iloc[sampled_idx]
                    labels = y_sample.astype(int).astype(str)

                    fig.add_scatter(
                        x=x_sample, y=y_sample, 
                        mode='text', 
                        text=labels, 
                        textposition="top center", 
                        showlegend=False, 
                        textfont=dict(color=color, size=11)
                    )

                if chart_color_col:
                    for D in unique_dialers_in_chart:
                        df_subset = df_oplans_trend[df_oplans_trend[DIALER_COLUMN] == D].sort_values('Date')
                        text_color = color_map_oplans.get(D, 'white')
                        add_labels_to_trace(df_subset, text_color)
                else:
                    # Single line chart
                    add_labels_to_trace(df_oplans_trend)
                
                st.plotly_chart(fig, use_container_width=True, height=800, config={'displayModeBar': False})
            else:
                st.info(f"No Oplans data found for the selected period ({period_label}).")

        # --- Column 3: KPI Cards (Right Side) ---
        with main_body_col3:
            st.markdown(f'<p class="chart-title-p">KPI calculations in {period_label} {selected_year_op}</p>', unsafe_allow_html=True)
            
            # KPI 1: Average Oplans count per day
            st.markdown(f'<div class="kpi-card-red"><h3>Average Oplans per day</h3><p>{avg_oplans_per_day}</p></div>', unsafe_allow_html=True)

            # KPI 2: Transfer Ratio (%) (NOW CORRECTLY CALCULATED)
            st.markdown(f'<div class="kpi-card-red"><h3>Transfer Ratio</h3><p>{transfer_ratio_pct}%</p></div>', unsafe_allow_html=True)

            # KPI 3: Total Oplans Count
            st.markdown(f'<div class="kpi-card-red"><h3>Total Oplans Count</h3><p>{total_oplans_count}</p></div>', unsafe_allow_html=True)

            # KPI 4: Average Attendance per day
            st.markdown(f'<div class="kpi-card-red"><h3>Average Attendance per day</h3><p>{avg_att_per_day_op}</p></div>', unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)


# --- NEW PAGE FUNCTION: OTHERS PERFORMANCE ---
def show_others_page(df_others, df_oplans, df_attendance, df_sheet2):
    """
    Renders the Others page dashboard.
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filter Others Data")

    # Year selector
    selected_year_oth = st.sidebar.selectbox("Select Year (Others)", options=YEARS, index=YEARS.index(2025) if 2025 in YEARS else 0, key="year_others")

    # Month multiselect
    default_month_name = "November"
    selected_month_names_oth = st.sidebar.multiselect(
        "Select Month (you may choose multiple)",
        options=MONTH_NAMES,
        default=[default_month_name],
        key="month_others"
    )
    if not selected_month_names_oth:
        selected_month_names_oth = [default_month_name]
    selected_month_indices_oth = [MONTH_NAMES.index(m) + 1 for m in selected_month_names_oth]

    # Week selection disabled for multi-month selection
    if len(selected_month_indices_oth) == 1:
        single_month_name_oth = selected_month_names_oth[0]
        weeks_list_oth = get_weeks_in_month(selected_year_oth, single_month_name_oth)
        selected_week_oth = st.sidebar.selectbox("Select Week (Others)", options=weeks_list_oth, key="week_others")

        # Day Selector (Dynamic). Enabled only when a single month is selected.
        days_list_oth = get_days_in_period(selected_year_oth, single_month_name_oth, selected_week_oth)
        selected_day_oth = st.sidebar.selectbox("Select Day (Others)", options=days_list_oth, key="day_others")
    else:
        selected_week_oth = "All Weeks"
        selected_day_oth = "All Days"
        st.sidebar.markdown("_Week and Day selection disabled for multiple months._")


    # Dialer selector (multi-select)
    dialers_list_oth = get_attended_dialers(df_attendance, selected_year_oth, selected_month_indices_oth)
    selected_dialer_oth = st.sidebar.multiselect("Select Dialer (Others)", options=dialers_list_oth, default=["All Dialers"], key="dialer_others")

    # --- Normalize column names and CLEAN data ---
    df_others_local = _standardize_df(df_others, DATE_COLUMN_SALES, DIALER_COLUMN)
    df_oplans_local = _standardize_df(df_oplans, DATE_COLUMN_SALES, DIALER_COLUMN)
    df_attendance_local = _standardize_df(df_attendance, 'date', DIALER_COLUMN)
    df_sheet2_local = _standardize_df(df_sheet2, DATE_COLUMN_SALES, DIALER_COLUMN) # STANDARDIZE df_sheet2


    # Filter dataframes by selected year/month(s)/week/dialer
    # NUMERATOR: Total Leads (Others + Oplans)
    df_others_filtered = _filter_by_date_local(df_others_local, DATE_COLUMN_SALES, selected_year_oth, selected_month_indices_oth)
    df_others_filtered = _apply_week_filter_local(df_others_filtered, DATE_COLUMN_SALES, selected_week_oth)
    df_others_filtered = _apply_day_filter_local(df_others_filtered, DATE_COLUMN_SALES, selected_day_oth) # Apply day filter
    df_others_filtered = _apply_dialer_filter_local(df_others_filtered, DIALER_COLUMN, selected_dialer_oth)

    df_oplans_filtered = _filter_by_date_local(df_oplans_local, DATE_COLUMN_SALES, selected_year_oth, selected_month_indices_oth)
    df_oplans_filtered = _apply_week_filter_local(df_oplans_filtered, DATE_COLUMN_SALES, selected_week_oth)
    df_oplans_filtered = _apply_day_filter_local(df_oplans_filtered, DATE_COLUMN_SALES, selected_day_oth) # Apply day filter
    df_oplans_filtered = _apply_dialer_filter_local(df_oplans_filtered, DIALER_COLUMN, selected_dialer_oth)
    
    # KPI calculations for Others page
    total_others_count = df_others_filtered.shape[0]
    total_oplans_count = df_oplans_filtered.shape[0]
    total_combined_count = total_others_count + total_oplans_count # This is the NUMERATOR

    # KPI 1: Others % (Others leads / Total Leads)
    others_percentage = round((total_others_count / total_combined_count) * 100, 1) if total_combined_count > 0 else 0

    # KPI 2: Average Others per day
    days_with_others_df = df_others_filtered[pd.to_datetime(df_others_filtered[DATE_COLUMN_SALES], errors='coerce').notna()]
    if not days_with_others_df.empty:
        unique_days = pd.to_datetime(days_with_others_df[DATE_COLUMN_SALES], errors='coerce').dt.date.nunique()
    else:
        unique_days = 0
    avg_others_per_day = round(total_others_count / unique_days) if unique_days > 0 else 0

    # KPI 3: Average attendance per day (from attendance sheet)
    df_att_local_filtered = _filter_by_date_local(df_attendance_local, 'date', selected_year_oth, selected_month_indices_oth)
    df_att_local_filtered = _apply_week_filter_local(df_att_local_filtered, 'date', selected_week_oth)
    df_att_local_filtered = _apply_day_filter_local(df_att_local_filtered, 'date', selected_day_oth) # Apply day filter
    df_att_local_filtered = _apply_dialer_filter_local(df_att_local_filtered, DIALER_COLUMN, selected_dialer_oth)
    total_att_count = df_att_local_filtered['attendance'].sum() if 'attendance' in df_att_local_filtered.columns and not df_att_local_filtered.empty else 0
    days_with_att = df_att_local_filtered['date'].dt.date.nunique() if 'date' in df_att_local_filtered.columns and not df_att_local_filtered.empty else 0
    avg_att_per_day_oth = round(total_att_count / days_with_att) if days_with_att > 0 else 0

    # KPI 4: Average checks per agent (MUST BE DECIMAL)
    df_sheet2_filtered = _filter_by_date_local(df_sheet2_local, DATE_COLUMN_SALES, selected_year_oth, selected_month_indices_oth)
    df_sheet2_filtered = _apply_week_filter_local(df_sheet2_filtered, DATE_COLUMN_SALES, selected_week_oth)
    df_sheet2_filtered = _apply_day_filter_local(df_sheet2_filtered, DATE_COLUMN_SALES, selected_day_oth) # Apply day filter
    df_sheet2_filtered = _apply_dialer_filter_local(df_sheet2_filtered, DIALER_COLUMN, selected_dialer_oth)
    

    attendance_sum_sheet2 = 0
    att_col = next((c for c in df_sheet2_filtered.columns if c.lower() == 'att'), None)
    if att_col is None:
        att_col = next((c for c in df_sheet2_filtered.columns if 'attendance' in c.lower()), None)
        
    if att_col is not None:
        try:
            numeric_vals = pd.to_numeric(df_sheet2_filtered[att_col], errors='coerce').dropna()
            attendance_sum_sheet2 = numeric_vals.sum()
        except Exception:
            pass
        
    if attendance_sum_sheet2 > 0:
        avg_checks_per_agent = total_combined_count / total_att_count
        # Use f-string formatting to enforce two decimal places
        avg_checks_per_agent_display = f"{avg_checks_per_agent:.2f}" 
    else:
        avg_checks_per_agent = 0 
        avg_checks_per_agent_display = "0.00"
    
    # --- Others Trend Calculation Block (NO CHANGE) ---
    df_others_trend = pd.DataFrame(columns=['Date', DIALER_COLUMN, 'Others_Count'])
    if not df_others_filtered.empty and DATE_COLUMN_SALES in df_others_filtered.columns:
        df_temp = df_others_filtered.copy()
        
        if DIALER_COLUMN in df_temp.columns:
            df_temp['_DialerClean'] = df_temp[DIALER_COLUMN]
        else:
            df_temp['_DialerClean'] = 'UNKNOWN'

        df_temp['Date'] = pd.to_datetime(df_temp[DATE_COLUMN_SALES], errors='coerce').dt.normalize()
        df_temp = df_temp.dropna(subset=['Date'])
        
        if DIALER_COLUMN in df_others_filtered.columns:
            df_others_trend = (
                df_temp
                .groupby(['Date', '_DialerClean'])
                .size()
                .reset_index(name='Others_Count')
                .rename(columns={'_DialerClean': DIALER_COLUMN})
            )
        else:
            df_others_trend = (
                df_temp
                .groupby('Date')
                .size()
                .reset_index(name='Others_Count')
            )
            df_others_trend[DIALER_COLUMN] = 'TOTAL'

        df_others_trend['Date'] = pd.to_datetime(df_others_trend['Date'])
        df_others_trend = df_others_trend.sort_values(['Date', DIALER_COLUMN])
        
        if isinstance(selected_dialer_oth, (list, tuple, set)):
            if 'All Dialers' not in selected_dialer_oth:
                df_others_trend = df_others_trend[df_others_trend[DIALER_COLUMN] != 'UNKNOWN']
        elif selected_dialer_oth != 'All Dialers':
            df_others_trend = df_others_trend[df_others_trend[DIALER_COLUMN] != 'UNKNOWN']
            

    # --- Determine Period Label for Titles ---
    if selected_day_oth != "All Days":
        period_label = selected_day_oth
    elif selected_week_oth != "All Weeks":
        period_label = selected_week_oth
    else:
        period_label = ", ".join(selected_month_names_oth)

    # --- DISPLAY DASHBOARD LAYOUT (KPI Cards and Chart) ---
    with st.container():
        st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)

        # Chart and KPIs side-by-side
        main_body_col2, main_body_col3 = st.columns([5, 1])

        # --- Column 2: Main Content Area (Chart) ---
        with main_body_col2:
            st.markdown(f'<p class="chart-title-p">Daily Others Count Trend in {period_label} {selected_year_oth}</p>', unsafe_allow_html=True)
            
            if not df_others_trend.empty:
                # Color map can be reused or defined specifically for Others
                color_map_others = {
                    'SA2': '#8C1007',
                    'SA3': '#EB5A3C',
                    'SA4': '#DF9755',
                    'HU1': "#83CBE7"
                }

                if DIALER_COLUMN in df_others_trend.columns:
                    unique_dialers_in_chart = df_others_trend[DIALER_COLUMN].unique()
                    chart_color_col = DIALER_COLUMN
                else:
                    unique_dialers_in_chart = []
                    chart_color_col = None

                fig = px.line(
                    df_others_trend, 
                    x='Date', 
                    y='Others_Count', # Use the new count column
                    color=chart_color_col,
                    color_discrete_map=color_map_others if chart_color_col else None,
                    title='', 
                    line_shape='spline'
                )

                fig.update_traces(line=dict(smoothing=1.3, width=2.5), marker=dict(size=8))
                
                # Y-axis range logic
                max_others_val = df_others_trend['Others_Count'].max() if not df_others_trend.empty else None
                buffer = 3
                top_range = (max_others_val + buffer) if (max_others_val is not None and max_others_val > 0) else 1
                
                fig.update_layout(
                    height=520,
                    plot_bgcolor='#1e1e1e',
                    paper_bgcolor='#1e1e1e',
                    font_color='white',
                    legend_title_text='Dialer' if chart_color_col else None,
                    xaxis_title='Date',
                    yaxis_title='Others Count',
                    margin=dict(l=10, r=10, t=20, b=40),
                    xaxis={'type': 'date'},
                    yaxis={'range': [0, top_range], 'tickformat': '.0f'}
                )
                fig.update_xaxes(type='date')
                
                # Add labels (numbers) to the data points
                max_labels = 8
                # Simplified trace function: forces the text color to white
                def add_labels_to_trace(df_to_label): 
                    n = len(df_to_label)
                    if n == 0: return
                    step = max(1, math.ceil(n / max_labels))
                    sampled_idx = list(range(0, n, step))
                    
                    x_sample = df_to_label['Date'].iloc[sampled_idx]
                    y_sample = df_to_label['Others_Count'].iloc[sampled_idx]
                    labels = y_sample.astype(int).astype(str)

                    fig.add_scatter(
                        x=x_sample, y=y_sample, 
                        mode='text', 
                        text=labels, 
                        textposition="top center", 
                        showlegend=False, 
                        textfont=dict(color='white', size=11) # <-- FORCED TO WHITE
                    )

                if chart_color_col:
                    for D in unique_dialers_in_chart:
                        df_subset = df_others_trend[df_others_trend[DIALER_COLUMN] == D].sort_values('Date')
                        add_labels_to_trace(df_subset)
                else:
                    add_labels_to_trace(df_others_trend)

                st.plotly_chart(fig, use_container_width=True, height=800, config={'displayModeBar': False})
            else:
                st.info(f"No Others data found for the selected period ({period_label}).")

        # --- Column 3: KPI Cards (Right Side) ---
        with main_body_col3:
            st.markdown(f'<p class="chart-title-p">KPI calculations in {period_label} {selected_year_oth}</p>', unsafe_allow_html=True) 
            
            # KPI 1: Others %
            st.markdown(f'<div class="kpi-card-red"><h3>Others %</h3><p>{others_percentage}%</p></div>', unsafe_allow_html=True)

            # KPI 2: Average Others count per day
            st.markdown(f'<div class="kpi-card-red"><h3>Average Others per day</h3><p>{avg_others_per_day}</p></div>', unsafe_allow_html=True)
            
            # KPI 3 (MODIFIED TO DECIMAL): Average checks per agent
            st.markdown(f'<div class="kpi-card-red"><h3>Average checks per agent</h3><p>{avg_checks_per_agent_display}</p></div>', unsafe_allow_html=True)

            # KPI 4: Average Attendance per day
            st.markdown(f'<div class="kpi-card-red"><h3>Average Attendance per day</h3><p>{avg_att_per_day_oth}</p></div>', unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)


# --- 6. MAIN APP EXECUTION ---

# Create a simple radio selector in the sidebar for page navigation
page = st.sidebar.radio(
    "Select Dashboard View",
    ("Sales Performance", "Oplans Performance", "Others Performance"), 
    index=0
)

# Call the selected function
if page == "Sales Performance":
    show_sales_dashboard(df_attendance, df_sales, df_oplans)
elif page == "Oplans Performance":
    show_oplans_dashboard(df_attendance, df_oplans)
elif page == "Others Performance":
    # PASS df_sheet2 to the others page function
    show_others_page(df_others, df_oplans, df_attendance, df_sheet2)

