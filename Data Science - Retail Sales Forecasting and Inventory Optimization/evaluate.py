import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_percentage_error

def calc_metrics(forecast_df):
    forecast_df = forecast_df.dropna(subset=['Actual', 'Forecast'])
    mape = mean_absolute_percentage_error(forecast_df['Actual'], forecast_df['Forecast'])
    wmape = (forecast_df['Abs_Error'].sum() / forecast_df['Actual'].sum()) * 100
    bias = ((forecast_df['Forecast'] - forecast_df['Actual']).sum() / forecast_df['Actual'].sum()) * 100
    
    print(f"Overall MAPE: {mape:.2%}")
    print(f"Weighted MAPE: {wmape:.2f}%")
    print(f"Bias: {bias:.2f}%")
    
    by_sku = forecast_df.groupby([forecast_df['Store ID'], forecast_df['Product ID']]).apply(
        lambda x: mean_absolute_percentage_error(x['Actual'], x['Forecast'])
    ).reset_index(name='MAPE')
    print("\nTop 5 Worst SKUs by MAPE:")
    print(by_sku.sort_values('MAPE', ascending=False).head())
    return by_sku