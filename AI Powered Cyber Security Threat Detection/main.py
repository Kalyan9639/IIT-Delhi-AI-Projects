from src.alerts import generate_alerts
from src.config import TEST_DATA_PATH
from src.predict import predict_from_dataframe
from src.preprocess import load_data


def main():
    df = load_data(TEST_DATA_PATH)
    predictions, probabilities = predict_from_dataframe(df, return_proba=True)
    alerts = generate_alerts(df, predictions, probabilities)

    print("Sample predictions:")
    print(f"Rows processed: {len(df)}")
    print(f"Threats detected: {int(sum(predictions))}")
    print()
    print("Sample alerts:")
    for alert in alerts[:10]:
        print(alert)


raise SystemExit(main())

from src.preprocess import load_data
from src.predict import predict_from_dataframe
from src.alerts import generate_alerts

# Load test data
df = load_data("data/UNSW_test.csv")

# Predict
predictions = predict_from_dataframe(df)

# Generate alerts
alerts = generate_alerts(predictions)

print("\n🚨 SAMPLE ALERTS:\n")
for alert in alerts[:10]:
    print(alert)
