from data_loader import load_and_clean, add_features
from model import run_forecasting
from inventory import generate_inventory_reco
from evaluate import calc_metrics
import pandas as pd
from config import DATA_PATH

if __name__ == "__main__":
    print("1. Loading data...")
    df = load_and_clean()
    print("Shape after load:", df.shape)
    
    print("2. Feature engineering...")
    df = add_features(df)
    print("Shape after FE:", df.shape)
    
    print("3. Running forecasting models...")
    forecast_df = run_forecasting(df)
    forecast_df.to_csv('forecast_results.csv', index=False)
    print("Forecast saved to forecast_results.csv")
    
    print("4. Calculating metrics...")
    calc_metrics(forecast_df)
    
    print("5. Generating inventory recommendations...")
    raw_df = pd.read_csv(DATA_PATH, parse_dates=['Date'])
    reco_df = generate_inventory_reco(forecast_df, raw_df)
    reco_df.to_csv('inventory_recommendations.csv', index=False)
    print("Recommendations saved to inventory_recommendations.csv")
    print("\nSample recommendations:")
    print(reco_df[reco_df['Stockout_Risk']].head())