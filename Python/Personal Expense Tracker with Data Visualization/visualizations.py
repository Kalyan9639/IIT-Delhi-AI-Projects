import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

DB_NAME = "financial_audit.db"

def get_data():
    """Fetches all data from the SQLite database into a Pandas DataFrame."""
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM transactions", conn)
        conn.close()
        # Convert date to datetime object for time-series analysis
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        print(f"Database error: {e}")
        return pd.DataFrame()

def plot_spending_by_category(df):
    """Creates a pie chart of expenses by AI-generated category."""
    # Filter only Debits (expenses) and exclude cash withdrawals/transfers for true 'spending'
    expenses = df[(df['type'] == 'Db') & (~df['category'].isin(['Cash Withdrawal', 'Personal Transfer']))]
    
    category_sums = expenses.groupby('category')['amount'].sum().reset_index()
    
    fig = px.pie(
        category_sums, 
        values='amount', 
        names='category', 
        hole=0.4,
        title="AI Categorized Spend Distribution",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def plot_cashflow_trend(df):
    """Line chart showing the bank balance over time."""
    fig = px.line(
        df.sort_values('date'), 
        x='date', 
        y='balance', 
        title="Account Balance Burn Rate",
        markers=True
    )
    fig.update_layout(xaxis_title="Date", yaxis_title="Balance (₹)")
    return fig

def plot_transaction_velocity(df):
    """Bar chart showing the number of UPI transactions per day (Impulse detector)."""
    # Filter for UPI Debits
    upi_tx = df[(df['mode'] == 'UPI') & (df['type'] == 'Db')]
    velocity = upi_tx.groupby('date').size().reset_index(name='tx_count')
    
    fig = px.bar(
        velocity, 
        x='date', 
        y='tx_count',
        title="UPI Transaction Velocity (Impulse Sprints)",
        color='tx_count',
        color_continuous_scale="Reds"
    )
    fig.add_hline(y=velocity['tx_count'].mean(), line_dash="dash", annotation_text="Average Daily UPI Tx")
    return fig

def get_bank_fees_summary(df):
    """Returns the total amount lost to hidden bank fees."""
    fees_df = df[df['is_bank_fee'] == 1]
    total_fees = fees_df['amount'].sum()
    return total_fees, fees_df

def plot_income_vs_expense(df):
    """Bar chart comparing total Credit vs Debit per month."""
    df['month_year'] = df['date'].dt.to_period('M').astype(str)
    summary = df.groupby(['month_year', 'type'])['amount'].sum().reset_index()
    
    # Rename types for readability
    summary['type'] = summary['type'].replace({'Db': 'Money Out', 'Cr': 'Money In'})
    
    fig = px.bar(
        summary, 
        x='month_year', 
        y='amount', 
        color='type', 
        barmode='group',
        title="Money In vs. Money Out",
        color_discrete_map={'Money In': '#2ecc71', 'Money Out': '#e74c3c'}
    )
    return fig

def plot_spending_pie(df):
    """High-level distribution of categorized spending."""
    expenses = df[df['type'] == 'Db']
    data = expenses.groupby('category')['amount'].sum().reset_index()
    fig = px.pie(data, values='amount', names='category', hole=0.5, 
                 title="Semantic Spend Distribution",
                 color_discrete_sequence=px.colors.qualitative.Prism)
    fig.update_layout(showlegend=True, margin=dict(t=40, b=0, l=0, r=0))
    return fig

def plot_velocity_chart(df):
    """Analyzes 'Transaction Velocity' to detect impulsive behavior."""
    upi_only = df[(df['mode'] == 'UPI') & (df['type'] == 'Db')]
    velocity = upi_only.groupby('date').size().reset_index(name='count')
    
    fig = px.area(velocity, x='date', y='count', 
                  title="Daily UPI Velocity (Impulse Detector)",
                  line_shape='spline', color_discrete_sequence=['#FF4B4B'])
    fig.add_hline(y=velocity['count'].mean(), line_dash="dash", annotation_text="Avg Velocity")
    return fig

def plot_cash_flow(df):
    """Time-series comparison of Inflow vs Outflow."""
    df['month'] = df['date'].dt.to_period('M').astype(str)
    flow = df.groupby(['month', 'type'])['amount'].sum().reset_index()
    
    fig = px.bar(flow, x='month', y='amount', color='type', barmode='group',
                 title="Monthly Inflow vs Outflow",
                 color_discrete_map={'Db': '#EF553B', 'Cr': '#00CC96'})
    return fig