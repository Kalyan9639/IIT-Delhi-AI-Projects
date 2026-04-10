from __future__ import annotations

from src.data_loader import load_all_data
from src.forecast import forecast_next
from src.train import train_model


def main() -> None:
    df = load_all_data()
    print(f"Loaded canonical dataset with {len(df):,} rows across {df['Region'].nunique()} regions.")

    rmse, r2, preds, y_test = train_model(df)
    print(f"Walk-forward backtest complete. RMSE: {rmse:.2f} | R2: {r2:.4f}")
    print(f"Backtest samples evaluated: {len(preds):,}")

    forecasts = forecast_next(df, horizon=24)
    if isinstance(forecasts, dict) and forecasts:
        first_region = next(iter(forecasts))
        print(f"Sample next-24-hour forecast for {first_region}:")
        print(forecasts[first_region].head().to_string(index=False))
        print(f"Generated forecasts for {len(forecasts)} regions.")
    else:
        print("Forecast generation completed.")


if __name__ == "__main__":
    main()
