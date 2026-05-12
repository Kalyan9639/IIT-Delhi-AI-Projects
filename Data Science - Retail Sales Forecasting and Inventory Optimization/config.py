DATA_PATH = 'demand_forecasting.csv'
RANDOM_STATE = 42
TEST_SIZE = 0.2  # Last 20% of time for backtest
FORECAST_HORIZON = 30  # days
SERVICE_LEVEL = 0.95  # 95% target
DEFAULT_LEAD_TIME = 7  # days, override if you have actual data
N_JOBS = -1

TARGET_COL = 'Units Sold'
DATE_COL = 'Date'
STORE_COL = 'Store ID'
PRODUCT_COL = 'Product ID'