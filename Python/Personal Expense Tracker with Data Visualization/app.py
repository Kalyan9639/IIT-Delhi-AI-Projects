import streamlit as st
import pandas as pd
import datetime
import visualizations as vz

# --- UI & PAGE CONFIGURATION ---
st.set_page_config(page_title="FinAudit Pro", page_icon="🏦", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for a premium financial dashboard look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 4px solid #4CAF50;}
    [data-testid="stMetricValue"] { color: #22c55e; }
    </style>
    """, unsafe_allow_html=True)

# --- LOAD & PREPARE DATA ---
@st.cache_data
def load_and_prep_data():
    return vz.get_data()

df = load_and_prep_data()

if df.empty:
    st.error("⚠️ No data found! Please run the `data_pipeline.py` pipeline first to generate the financial_audit.db database.")
    st.stop()

# Ensure strict datetime format to prevent jump-to-current-year (2026) bugs
df['date'] = pd.to_datetime(df['date'])

# --- SIDEBAR & FILTERING ---
st.sidebar.image("https://img.icons8.com/fluency/96/000000/bank-building.png", width=60)
st.sidebar.title("TransactAudit AI")
st.sidebar.markdown("Powered by **Advanced Statistical Pipelines** & **SLM**")

# Date filtering safely handled
min_date = df['date'].min().date()
max_date = df['date'].max().date()

st.sidebar.markdown("### 🗓️ Filter Audit Period")

# FIX: Replaced the buggy range dropdown with two distinct, stable calendar pickers
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
with col2:
    end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)

# Add invisible spacing below the date pickers in the sidebar. 
# This provides scrollable space, forcing the calendar popup to render DOWNWARDS instead of getting clipped at the top.
st.sidebar.markdown("<br>" * 15, unsafe_allow_html=True)

# Apply Date Filter based on the two separate calendar inputs
if start_date <= end_date:
    filtered_df = df[(df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)].copy()
else:
    st.sidebar.error("Start Date must be before End Date.")
    filtered_df = df.copy()

# --- HEADER & EXECUTIVE METRICS ---
st.title("🏦 Personal Financial Audit Dashboard")
st.markdown("Deep dive into your cash flows, identify anomalies, and track impulsive behavior.")

# Calculate Metrics
total_out = filtered_df[filtered_df['type'] == 'Db']['amount'].sum()
total_in = filtered_df[filtered_df['type'] == 'Cr']['amount'].sum()
# SQLite booleans are 0/1, so we check against 1 to be safe
anomalies = filtered_df[filtered_df['is_anomaly'] == 1].shape[0] 
bank_fees = filtered_df[filtered_df['is_bank_fee'] == 1]['amount'].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("📉 Total Outflow", f"₹{total_out:,.2f}", delta="- Expense", delta_color="inverse")
col2.metric("📈 Total Inflow", f"₹{total_in:,.2f}", delta="+ Income", delta_color="normal")
col3.metric("🚨 Statistical Anomalies", int(anomalies), delta="Outliers", delta_color="off")
col4.metric("🏦 Hidden Bank Fees", f"₹{bank_fees:,.2f}", delta="- Leaks", delta_color="inverse")

st.markdown("---")

# --- VISUALIZATION TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Executive Summary", "🏃‍♂️ Behavioral Velocity", "🕵️‍♂️ Audit Ledger"])

with tab1:
    st.markdown("### AI Categorized Spending & Cash Flow")
    row1_col1, row1_col2 = st.columns([1, 1])
    
    with row1_col1:
        st.plotly_chart(vz.plot_spending_pie(filtered_df), use_container_width=True)
    
    with row1_col2:
        st.plotly_chart(vz.plot_cash_flow(filtered_df), use_container_width=True)

with tab2:
    st.markdown("### Impulse Spending Sprints")
    st.info("💡 **Insight:** This tracks the sheer volume of UPI transactions per day. High peaks indicate 'impulse days' where micro-transactions accumulate.")
    st.plotly_chart(vz.plot_velocity_chart(filtered_df), use_container_width=True)

with tab3:
    st.markdown("### Deep-Dive Transaction Ledger")
    
    # Quick filter
    fee_only = st.checkbox("🔍 Show Hidden Bank Fees Only")
    display_df = filtered_df.copy()
    
    if fee_only:
        display_df = display_df[display_df['is_bank_fee'] == 1]
    
    # --- BULLETPROOF DATA SANITIZATION ---
    # Sort and filter columns
    display_df = display_df.sort_values('date', ascending=False)
    cols_to_show = ['date', 'name', 'category', 'mode', 'type', 'amount', 'balance', 'is_anomaly']
    display_df = display_df[cols_to_show]
    
    # 1. Force Text Columns
    text_columns = ['mode', 'name', 'category', 'type']
    for col in text_columns:
        display_df[col] = display_df[col].fillna("Unknown").astype(str)
            
    # 2. Force Date Format (string prevents PyArrow datetime bounds errors)
    display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
    
    # 3. Force Numeric Data
    for col in ['amount', 'balance']:
        display_df[col] = pd.to_numeric(display_df[col], errors='coerce').fillna(0.0)
        
    # 4. Force Boolean Data
    display_df['is_anomaly'] = display_df['is_anomaly'].astype(bool)
    
    # Render table with fixed height to prevent dropdown clipping
    st.dataframe(
        display_df, 
        use_container_width=True,
        hide_index=True,
        height=500 
    )
    
    # Add whitespace at the bottom of the page to ensure dropdown menus can open downwards
    st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)