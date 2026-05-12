import pandas as pd
import numpy as np
from scipy.stats import norm
from config import *

def calc_safety_stock(demand_mean, demand_std, lead_time, service_level=SERVICE_LEVEL):
    z = norm.ppf(service_level)
    ss = z * demand_std * np.sqrt(lead_time)
    return max(0, round(ss))

def generate_inventory_reco(forecast_df, raw_df, lead_time=DEFAULT_LEAD_TIME):
    # Get latest inventory snapshot
    inv_snapshot = raw_df.sort_values(DATE_COL).groupby([STORE_COL, PRODUCT_COL]).tail(1)
    inv_snapshot = inv_snapshot[[STORE_COL, PRODUCT_COL, 'Inventory Level', 'Units Ordered']]
    
    # Aggregate forecast stats per SKU
    forecast_stats = forecast_df.groupby([STORE_COL, PRODUCT_COL]).agg({
        'Forecast': ['mean', 'std'],
        'Actual': 'mean'
    })
    forecast_stats.columns = ['Forecast_Mean', 'Forecast_Std', 'Actual_Mean']
    forecast_stats = forecast_stats.reset_index()
    
    merged = inv_snapshot.merge(forecast_stats, on=[STORE_COL, PRODUCT_COL], how='inner')
    
    merged['Lead_Time'] = lead_time
    merged['Demand_LT'] = merged['Forecast_Mean'] * merged['Lead_Time']
    merged['Safety_Stock'] = merged.apply(
        lambda x: calc_safety_stock(x['Forecast_Mean'], x['Forecast_Std'], x['Lead_Time']), axis=1
    )
    merged['Reorder_Point'] = merged['Demand_LT'] + merged['Safety_Stock']
    merged['Stockout_Risk'] = merged['Inventory Level'] < merged['Reorder_Point']
    merged['Suggested_Order_Qty'] = np.where(
        merged['Stockout_Risk'],
        (merged['Reorder_Point'] - merged['Inventory Level'] + merged['Forecast_Mean'] * 7).clip(lower=0),
        0
    ).round(0)
    
    merged['Days_of_Supply'] = merged['Inventory Level'] / merged['Forecast_Mean'].replace(0, np.nan)
    return merged