import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from src.data_processor import (
    load_expenses, load_income, get_summary_stats,
    get_monthly_summary, get_category_breakdown, get_account_breakdown,
    get_daily_trend, filter_by_date_range, filter_by_category, filter_by_account
)

st.set_page_config(
    page_title="Expense Tracker - Financial Intelligence Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stApp {
        background-color: #0e1117;
    }
    .metric-card {
        background-color: #1a1f2e;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }
    .stMetric label {
        color: #a0a0a0 !important;
    }
    .stMetric value {
        color: #ffffff !important;
    }
    div[data-testid="stSidebar"] {
        background-color: #161b22;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    expenses_df = load_expenses()
    income_df = load_income()
    return expenses_df, income_df

expenses_df, income_df = load_data()

st.sidebar.title("💰 Expense Tracker")
st.sidebar.markdown("---")

st.sidebar.header("📅 Date Filter")
min_date = expenses_df['date_time'].min().date()
max_date = expenses_df['date_time'].max().date()

start_date = st.sidebar.date_input(
    "Start Date",
    value=min_date,
    min_value=min_date,
    max_value=max_date
)
end_date = st.sidebar.date_input(
    "End Date",
    value=max_date,
    min_value=min_date,
    max_value=max_date
)

st.sidebar.header("📂 Category Filter")
all_expense_categories = sorted(expenses_df['category'].unique().tolist())
selected_expense_categories = st.sidebar.multiselect(
    "Expense Categories",
    all_expense_categories,
    default=all_expense_categories
)

all_income_categories = sorted(income_df['category'].unique().tolist())
selected_income_categories = st.sidebar.multiselect(
    "Income Categories",
    all_income_categories,
    default=all_income_categories
)

st.sidebar.header("🏦 Account Filter")
all_accounts = sorted(set(expenses_df['account'].unique()) | set(income_df['account'].unique()))
selected_accounts = st.sidebar.multiselect(
    "Accounts",
    all_accounts,
    default=all_accounts
)

expenses_filtered = filter_by_date_range(expenses_df, start_date, end_date)
expenses_filtered = filter_by_category(expenses_filtered, selected_expense_categories)
expenses_filtered = filter_by_account(expenses_filtered, selected_accounts)

income_filtered = filter_by_date_range(income_df, start_date, end_date)
income_filtered = filter_by_category(income_filtered, selected_income_categories)
income_filtered = filter_by_account(income_filtered, selected_accounts)

st.title("📊 Financial Intelligence Dashboard")
st.markdown(f"**Period:** {start_date} to {end_date}")
st.markdown("---")

stats = get_summary_stats(expenses_filtered, income_filtered)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="💵 Total Income",
        value=f"{stats['total_income']:,.2f} BYN",
        delta=f"{stats['income_count']} transactions"
    )

with col2:
    st.metric(
        label="💸 Total Expenses",
        value=f"{stats['total_expenses']:,.2f} BYN",
        delta=f"{stats['expense_count']} transactions",
        delta_color="inverse"
    )

with col3:
    balance_color = "normal" if stats['balance'] >= 0 else "inverse"
    st.metric(
        label="💰 Net Balance",
        value=f"{stats['balance']:,.2f} BYN",
        delta=None
    )

with col4:
    savings_rate = (stats['balance'] / stats['total_income'] * 100) if stats['total_income'] > 0 else 0
    st.metric(
        label="📈 Savings Rate",
        value=f"{savings_rate:.1f}%",
        delta=None
    )

st.markdown("---")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Expense Breakdown by Category")
    if not expenses_filtered.empty:
        expense_categories = get_category_breakdown(expenses_filtered)

        fig_pie = px.pie(
            expense_categories,
            values='total',
            names='category',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label',
            marker=dict(line=dict(color='#0e1117', width=2))
        )
        fig_pie.update_layout(
            paper_bgcolor='#0e1117',
            plot_bgcolor='#0e1117',
            font=dict(color='white'),
            showlegend=True,
            height=400
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        st.dataframe(
            expense_categories[['category', 'total', 'count', 'percentage']]
            .style.format({'total': '{:.2f}', 'percentage': '{:.1f}%'}),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No expense data for selected filters.")

with col_right:
    st.subheader("💵 Income Breakdown by Category")
    if not income_filtered.empty:
        income_categories = get_category_breakdown(income_filtered)

        fig_pie_income = px.pie(
            income_categories,
            values='total',
            names='category',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie_income.update_traces(
            textposition='inside',
            textinfo='percent+label',
            marker=dict(line=dict(color='#0e1117', width=2))
        )
        fig_pie_income.update_layout(
            paper_bgcolor='#0e1117',
            plot_bgcolor='#0e1117',
            font=dict(color='white'),
            showlegend=True,
            height=400
        )
        st.plotly_chart(fig_pie_income, use_container_width=True)

        st.dataframe(
            income_categories[['category', 'total', 'count', 'percentage']]
            .style.format({'total': '{:.2f}', 'percentage': '{:.1f}%'}),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No income data for selected filters.")

st.markdown("---")

st.subheader("📈 Monthly Trends")

monthly_summary = get_monthly_summary(expenses_filtered, income_filtered)

if not monthly_summary.empty:
    fig_monthly = go.Figure()

    fig_monthly.add_trace(go.Bar(
        x=monthly_summary['month_str'],
        y=monthly_summary['income'],
        name='Income',
        marker_color='#2ecc71',
        opacity=0.8
    ))

    fig_monthly.add_trace(go.Bar(
        x=monthly_summary['month_str'],
        y=monthly_summary['expenses'],
        name='Expenses',
        marker_color='#e74c3c',
        opacity=0.8
    ))

    fig_monthly.add_trace(go.Scatter(
        x=monthly_summary['month_str'],
        y=monthly_summary['savings'],
        name='Savings',
        mode='lines+markers',
        line=dict(color='#3498db', width=3),
        marker=dict(size=10)
    ))

    fig_monthly.update_layout(
        barmode='group',
        paper_bgcolor='#0e1117',
        plot_bgcolor='#0e1117',
        font=dict(color='white'),
        xaxis=dict(gridcolor='#333', title='Month'),
        yaxis=dict(gridcolor='#333', title='Amount (BYN)'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=400
    )

    st.plotly_chart(fig_monthly, use_container_width=True)
else:
    st.info("No monthly data available for selected filters.")

col_daily_left, col_daily_right = st.columns(2)

with col_daily_left:
    st.subheader("📅 Daily Expense Trend")
    if not expenses_filtered.empty:
        daily_expenses = get_daily_trend(expenses_filtered)

        fig_daily_exp = px.area(
            daily_expenses,
            x='date',
            y='amount',
            color_discrete_sequence=['#e74c3c']
        )
        fig_daily_exp.update_traces(fill='tozeroy', opacity=0.6)
        fig_daily_exp.update_layout(
            paper_bgcolor='#0e1117',
            plot_bgcolor='#0e1117',
            font=dict(color='white'),
            xaxis=dict(gridcolor='#333'),
            yaxis=dict(gridcolor='#333', title='Amount (BYN)'),
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig_daily_exp, use_container_width=True)

with col_daily_right:
    st.subheader("📅 Daily Income Trend")
    if not income_filtered.empty:
        daily_income = get_daily_trend(income_filtered)

        fig_daily_inc = px.area(
            daily_income,
            x='date',
            y='amount',
            color_discrete_sequence=['#2ecc71']
        )
        fig_daily_inc.update_traces(fill='tozeroy', opacity=0.6)
        fig_daily_inc.update_layout(
            paper_bgcolor='#0e1117',
            plot_bgcolor='#0e1117',
            font=dict(color='white'),
            xaxis=dict(gridcolor='#333'),
            yaxis=dict(gridcolor='#333', title='Amount (BYN)'),
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig_daily_inc, use_container_width=True)

st.markdown("---")

st.subheader("🏦 Account Distribution")

col_acc1, col_acc2 = st.columns(2)

with col_acc1:
    if not expenses_filtered.empty:
        expense_accounts = get_account_breakdown(expenses_filtered)
        fig_acc_exp = px.bar(
            expense_accounts,
            x='account',
            y='total',
            color='total',
            color_continuous_scale='Reds',
            text_auto=True
        )
        fig_acc_exp.update_traces(texttemplate='%{y:.2f}', textposition='outside')
        fig_acc_exp.update_layout(
            paper_bgcolor='#0e1117',
            plot_bgcolor='#0e1117',
            font=dict(color='white'),
            xaxis=dict(gridcolor='#333'),
            yaxis=dict(gridcolor='#333', title='Amount (BYN)'),
            title='Expenses by Account',
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig_acc_exp, use_container_width=True)

with col_acc2:
    if not income_filtered.empty:
        income_accounts = get_account_breakdown(income_filtered)
        fig_acc_inc = px.bar(
            income_accounts,
            x='account',
            y='total',
            color='total',
            color_continuous_scale='Greens',
            text_auto=True
        )
        fig_acc_inc.update_traces(texttemplate='%{y:.2f}', textposition='outside')
        fig_acc_inc.update_layout(
            paper_bgcolor='#0e1117',
            plot_bgcolor='#0e1117',
            font=dict(color='white'),
            xaxis=dict(gridcolor='#333'),
            yaxis=dict(gridcolor='#333', title='Amount (BYN)'),
            title='Income by Account',
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig_acc_inc, use_container_width=True)

st.markdown("---")

st.subheader("📋 Transaction Details")

tab1, tab2 = st.tabs(["💸 Expenses", "💵 Income"])

with tab1:
    if not expenses_filtered.empty:
        st.dataframe(
            expenses_filtered[['date_time', 'category', 'account', 'amount', 'currency', 'tags']]
            .sort_values('date_time', ascending=False)
            .reset_index(drop=True),
            use_container_width=True
        )
    else:
        st.info("No expense transactions found.")

with tab2:
    if not income_filtered.empty:
        st.dataframe(
            income_filtered[['date_time', 'category', 'account', 'amount', 'currency', 'tags']]
            .sort_values('date_time', ascending=False)
            .reset_index(drop=True),
            use_container_width=True
        )
    else:
        st.info("No income transactions found.")

st.markdown("---")

st.subheader("💾 Export Data")

def prepare_for_export(df):
    """Convert datetime/period columns to strings for safe export."""
    export_cols = ['date_time', 'category', 'account', 'amount', 'currency', 'tags']
    df_export = df[export_cols].copy()
    df_export['date_time'] = df_export['date_time'].astype(str)
    return df_export

col_exp1, col_exp2 = st.columns(2)

with col_exp1:
    exp_df = prepare_for_export(expenses_filtered)
    csv_exp = exp_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Expenses CSV",
        data=csv_exp,
        file_name=f"expenses_{start_date}_{end_date}.csv",
        mime='text/csv'
    )

with col_exp2:
    inc_df = prepare_for_export(income_filtered)
    csv_inc = inc_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Income CSV",
        data=csv_inc,
        file_name=f"income_{start_date}_{end_date}.csv",
        mime='text/csv'
    )

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>💰 Expense Tracker - Financial Intelligence Dashboard</p>
    <p>Built with Streamlit, Pandas & Plotly</p>
</div>
""", unsafe_allow_html=True)