from pathlib import Path

import pandas as pd
import requests


API_URL = "http://127.0.0.1:8000/predict"
DATA_PATH = Path("data/UNSW_test.csv")


def main():
    df = pd.read_csv(DATA_PATH).head(5)
    payload = {"records": df.to_dict(orient="records")}
    response = requests.post(API_URL, json=payload, timeout=30)
    response.raise_for_status()
    print(response.json())


if __name__ == "__main__":
    main()

