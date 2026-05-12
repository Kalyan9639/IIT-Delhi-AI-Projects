import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_percentage_error, mean_absolute_error
from config import *

FEATURES = [
    'DayOfWeek', 'Month', 'Week', 'IsWeekend', 'Price', 'Discount', 'Promotion',
    'Competitor Pricing', 'Epidemic', 'Lag_1', 'Lag_7', 'Lag_14', 'Lag_28',
    'RollingMean_7', 'RollingMean_14', 'RollingMean_28', 'RollingStd_7',
    'Price_Diff', 'Price_Ratio',
    'Category_encoded', 'Region_encoded', 'Weather Condition_encoded', 'Seasonality_encoded'
]

def time_train_test_split(group):
    group = group.sort_values(DATE_COL)
    split_idx = int(len(group) * (1 - TEST_SIZE))
    train = group.iloc[:split_idx]
    test = group.iloc[split_idx:]
    return train, test

def train_single_model(train_df):
    X = train_df[FEATURES]
    y = train_df[TARGET_COL]
    model = RandomForestRegressor(
        n_estimators=20, max_depth=12, min_samples_split=5,
        random_state=RANDOM_STATE, n_jobs=N_JOBS
    )
    model.fit(X, y)
    return model

def forecast_group(df_group):
    train, test = time_train_test_split(df_group)
    if len(train) < 50:  # need min history
        return pd.DataFrame()
    
    model = train_single_model(train)
    X_test = test[FEATURES]
    preds = model.predict(X_test)
    
    out = test[[DATE_COL, STORE_COL, PRODUCT_COL]].copy()
    out['Actual'] = test[TARGET_COL].values
    out['Forecast'] = preds
    out['Abs_Error'] = np.abs(out['Actual'] - out['Forecast'])
    out['APE'] = out['Abs_Error'] / out['Actual'].replace(0, np.nan)
    return out

def run_forecasting(df):
    results = []
    for (store, product), group in df.groupby([STORE_COL, PRODUCT_COL]):
        res = forecast_group(group)
        if not res.empty:
            results.append(res)
    forecast_df = pd.concat(results, ignore_index=True)
    return forecast_df