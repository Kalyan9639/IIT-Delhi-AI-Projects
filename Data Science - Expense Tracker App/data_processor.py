import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent

def load_expenses():
    """Load expenses data from CSV file."""
    df = pd.read_csv(DATA_DIR / "Expenses_clean.csv")
    df['date_time'] = pd.to_datetime(df['date_time'])
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    df['month'] = df['date_time'].dt.to_period('M')
    df['week'] = df['date_time'].dt.isocalendar().week
    df['day_of_week'] = df['date_time'].dt.day_name()
    return df

def load_income():
    """Load income data from CSV file."""
    df = pd.read_csv(DATA_DIR / "Income_clean.csv")
    df['date_time'] = pd.to_datetime(df['date_time'])
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    df['month'] = df['date_time'].dt.to_period('M')
    df['week'] = df['date_time'].dt.isocalendar().week
    df['day_of_week'] = df['date_time'].dt.day_name()
    return df

def get_summary_stats(expenses_df, income_df):
    """Calculate summary statistics."""
    total_expenses = expenses_df['amount'].sum()
    total_income = income_df['amount'].sum()
    balance = total_income - total_expenses

    return {
        'total_expenses': total_expenses,
        'total_income': total_income,
        'balance': balance,
        'expense_count': len(expenses_df),
        'income_count': len(income_df),
        'avg_expense': expenses_df['amount'].mean(),
        'avg_income': income_df['amount'].mean()
    }

def get_monthly_summary(expenses_df, income_df):
    """Get monthly breakdown of expenses and income."""
    expense_monthly = expenses_df.groupby('month')['amount'].sum().reset_index()
    expense_monthly.columns = ['month', 'expenses']

    income_monthly = income_df.groupby('month')['amount'].sum().reset_index()
    income_monthly.columns = ['month', 'income']

    monthly = pd.merge(expense_monthly, income_monthly, on='month', how='outer').fillna(0)
    monthly['savings'] = monthly['income'] - monthly['expenses']
    monthly['month_str'] = monthly['month'].astype(str)

    return monthly

def get_category_breakdown(df, top_n=10):
    """Get breakdown by category."""
    category_df = df.groupby('category')['amount'].agg(['sum', 'count', 'mean']).reset_index()
    category_df.columns = ['category', 'total', 'count', 'average']
    category_df = category_df.sort_values('total', ascending=False).head(top_n)
    category_df['percentage'] = (category_df['total'] / category_df['total'].sum() * 100).round(1)
    return category_df

def get_account_breakdown(df):
    """Get breakdown by account."""
    account_df = df.groupby('account')['amount'].agg(['sum', 'count']).reset_index()
    account_df.columns = ['account', 'total', 'count']
    return account_df

def get_daily_trend(df):
    """Get daily spending/earning trend."""
    daily = df.groupby(df['date_time'].dt.date)['amount'].sum().reset_index()
    daily.columns = ['date', 'amount']
    daily = daily.sort_values('date')
    return daily

def filter_by_date_range(df, start_date, end_date):
    """Filter dataframe by date range."""
    mask = (df['date_time'].dt.date >= start_date) & (df['date_time'].dt.date <= end_date)
    return df[mask]

def filter_by_category(df, categories):
    """Filter dataframe by categories."""
    if not categories:
        return df
    return df[df['category'].isin(categories)]

def filter_by_account(df, accounts):
    """Filter dataframe by accounts."""
    if not accounts:
        return df
    return df[df['account'].isin(accounts)]