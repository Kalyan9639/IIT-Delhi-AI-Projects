import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from config import *

def load_and_clean():
    df = pd.read_csv(DATA_PATH, parse_dates=[DATE_COL])
    df = df.sort_values([STORE_COL, PRODUCT_COL, DATE_COL])

    df = df[df[TARGET_COL] >= 0]
    df['DayOfWeek'] = df[DATE_COL].dt.dayofweek
    df['Month'] = df[DATE_COL].dt.month
    df['Week'] = df[DATE_COL].dt.isocalendar().week
    df['IsWeekend'] = df['DayOfWeek'].isin([5,6]).astype(int)

    # Use Label Encoding instead of get_dummies
    # This keeps 1 column per category, no sparsity
    cat_cols = ['Category', 'Region', 'Weather Condition', 'Seasonality']
    for col in cat_cols:
        le = LabelEncoder()
        df[col + '_encoded'] = le.fit_transform(df[col].astype(str))

    # Drop original text columns to avoid issues
    df = df.drop(columns=cat_cols)
    df = df.fillna(0)
    return df

def create_time_features(group):
    group = group.copy()
    for lag in [1, 7, 14, 28]:
        group[f'Lag_{lag}'] = group[TARGET_COL].shift(lag)
    for w in [7, 14, 28]:
        group[f'RollingMean_{w}'] = group[TARGET_COL].shift(1).rolling(w).mean()
        group[f'RollingStd_{w}'] = group[TARGET_COL].shift(1).rolling(w).std()
    group['Price_Diff'] = group['Price'].diff()
    group['Price_Ratio'] = group['Price'] / group['Competitor Pricing'].replace(0, np.nan)
    return group

def add_features(df):
    df = df.groupby([STORE_COL, PRODUCT_COL], group_keys=True).apply(create_time_features)
    # Reset index to restore Store ID and Product ID as columns
    df = df.reset_index()
    # Drop the 'level_2' column if it exists (from the original index)
    if 'level_2' in df.columns:
        df = df.drop(columns=['level_2'])
    return df