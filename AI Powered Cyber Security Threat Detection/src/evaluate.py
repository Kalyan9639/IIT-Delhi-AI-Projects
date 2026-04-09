from __future__ import annotations

import json
from pathlib import Path

import joblib
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score

from .config import CONFUSION_MATRIX_PATH, MODEL_PATH, TARGET_COLUMN, TEST_DATA_PATH
from .preprocess import load_data, split_features_target
from .visualize import plot_confusion_matrix


def evaluate_model(test_path: str | Path = TEST_DATA_PATH, model_path: str | Path = MODEL_PATH):
    df = load_data(test_path)
    features, target = split_features_target(df)
    if target is None:
        raise ValueError(f"{test_path} must contain the '{TARGET_COLUMN}' column.")

    model = joblib.load(model_path)
    predictions = model.predict(features)

    metrics = {
        "accuracy": float(accuracy_score(target, predictions)),
        "precision": float(precision_score(target, predictions, zero_division=0)),
        "recall": float(recall_score(target, predictions, zero_division=0)),
        "f1": float(f1_score(target, predictions, zero_division=0)),
        "classification_report": classification_report(target, predictions, zero_division=0, output_dict=True),
        "confusion_matrix_path": str(plot_confusion_matrix(target, predictions, CONFUSION_MATRIX_PATH)),
    }

    return metrics


if __name__ == "__main__":
    report = evaluate_model()
    print(json.dumps(report, indent=2))

