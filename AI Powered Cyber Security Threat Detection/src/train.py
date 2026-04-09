from __future__ import annotations

import json
from pathlib import Path

import joblib
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from .config import METRICS_PATH, MODEL_PATH, TARGET_COLUMN, TRAIN_DATA_PATH, ensure_directories
from .model import build_model
from .preprocess import load_data, split_features_target


def train_model(train_path: str | Path = TRAIN_DATA_PATH):
    ensure_directories()

    df = load_data(train_path)
    features, target = split_features_target(df)
    if target is None:
        raise ValueError(f"{train_path} must contain the '{TARGET_COLUMN}' column.")

    x_train, x_valid, y_train, y_valid = train_test_split(
        features,
        target,
        test_size=0.2,
        random_state=42,
        stratify=target,
    )

    model = build_model()
    model.fit(x_train, y_train)

    predictions = model.predict(x_valid)

    metrics = {
        "accuracy": float(accuracy_score(y_valid, predictions)),
        "precision": float(precision_score(y_valid, predictions, zero_division=0)),
        "recall": float(recall_score(y_valid, predictions, zero_division=0)),
        "f1": float(f1_score(y_valid, predictions, zero_division=0)),
        "classification_report": classification_report(y_valid, predictions, zero_division=0, output_dict=True),
    }

    joblib.dump(model, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    return model, metrics


if __name__ == "__main__":
    trained_model, metrics = train_model()
    print(f"Model saved to {MODEL_PATH}")
    print(json.dumps(metrics, indent=2))

