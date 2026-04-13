"""Dashboard analytics for PredictGuard AI."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from src.config import DATASET_PATH, MODEL_BUNDLE_PATH, PREDICTIONS_LOG_PATH, TRAINING_METRICS_PATH
from src.data import load_raw_dataset
from src.predict import load_artifact


NUMERIC_FEATURES = [
    "air_temperature",
    "process_temperature",
    "rotational_speed",
    "torque",
    "tool_wear",
]


def _safe_percent(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((part / total) * 100.0, 2)


def _normalise_profile(means: pd.Series, frame: pd.DataFrame) -> dict[str, float]:
    normalized: dict[str, float] = {}
    for feature in NUMERIC_FEATURES:
        minimum = float(frame[feature].min())
        maximum = float(frame[feature].max())
        span = maximum - minimum
        if span <= 0:
            normalized[feature] = 50.0
        else:
            normalized[feature] = round(((float(means[feature]) - minimum) / span) * 100.0, 2)
    return normalized


def _feature_importance_to_records(pipeline: Any, limit: int = 8) -> list[dict[str, float | str]]:
    preprocess = pipeline.named_steps.get("preprocess")
    classifier = pipeline.named_steps.get("classifier")
    if preprocess is None or classifier is None:
        return []

    if hasattr(classifier, "feature_importances_"):
        values = np.asarray(classifier.feature_importances_, dtype=float)
    elif hasattr(classifier, "coef_"):
        values = np.abs(np.asarray(classifier.coef_, dtype=float)).ravel()
    else:
        return []

    feature_names = list(preprocess.get_feature_names_out())
    if len(feature_names) != len(values):
        return []

    ranked = sorted(zip(feature_names, values, strict=False), key=lambda item: item[1], reverse=True)[:limit]
    return [{"feature": feature, "importance": round(float(score), 4)} for feature, score in ranked]


def _load_prediction_log(limit: int = 15) -> dict[str, Any]:
    if not PREDICTIONS_LOG_PATH.exists():
        return {
            "total": 0,
            "recent": [],
            "risk_distribution": [
                {"label": "LOW", "count": 0},
                {"label": "MEDIUM", "count": 0},
                {"label": "HIGH", "count": 0},
            ],
        }

    log_frame = pd.read_csv(PREDICTIONS_LOG_PATH)
    if log_frame.empty:
        return {
            "total": 0,
            "recent": [],
            "risk_distribution": [
                {"label": "LOW", "count": 0},
                {"label": "MEDIUM", "count": 0},
                {"label": "HIGH", "count": 0},
            ],
        }

    if "risk_level" not in log_frame.columns:
        log_frame["risk_level"] = "LOW"

    risk_counts = log_frame["risk_level"].value_counts().reindex(["LOW", "MEDIUM", "HIGH"], fill_value=0)
    outcome_counts = log_frame["failure_prediction"].value_counts().reindex([0, 1], fill_value=0)
    recent = log_frame.tail(limit).iloc[::-1].copy()
    if "timestamp_utc" in recent.columns:
        recent["timestamp_utc"] = recent["timestamp_utc"].astype(str)
    if "batch_id" in recent.columns:
        recent["batch_id"] = recent["batch_id"].fillna("").astype(str)

    return {
        "total": int(len(log_frame)),
        "recent": recent[[
            "timestamp_utc",
            "batch_id",
            "sample_index",
            "type",
            "risk_probability",
            "risk_level",
            "failure_prediction",
            "action",
        ]].fillna("").to_dict(orient="records"),
        "risk_distribution": [
            {"label": label, "count": int(risk_counts[label])}
            for label in ["LOW", "MEDIUM", "HIGH"]
        ],
        "outcome_distribution": {
            "healthy": int(outcome_counts.get(0, 0)),
            "failure": int(outcome_counts.get(1, 0)),
        },
    }


def get_dashboard_snapshot() -> dict[str, Any]:
    frame = load_raw_dataset(DATASET_PATH)
    artifact = load_artifact(MODEL_BUNDLE_PATH)

    training_metrics: dict[str, Any] = {}
    if TRAINING_METRICS_PATH.exists():
        with TRAINING_METRICS_PATH.open("r", encoding="utf-8") as handle:
            training_metrics = json.load(handle)

    target_counts = frame["machine_failure"].value_counts().sort_index()
    type_counts = frame["type"].value_counts().reindex(["L", "M", "H"], fill_value=0)

    healthy_frame = frame[frame["machine_failure"] == 0]
    failure_frame = frame[frame["machine_failure"] == 1]
    healthy_means = healthy_frame[NUMERIC_FEATURES].mean()
    failure_means = failure_frame[NUMERIC_FEATURES].mean()

    scatter_sample = frame.sample(n=min(250, len(frame)), random_state=42)[
        ["air_temperature", "torque", "machine_failure", "type"]
    ]
    scatter_points = [
        {
            "x": round(float(row.air_temperature), 2),
            "y": round(float(row.torque), 2),
            "label": int(row.machine_failure),
            "type": row.type,
        }
        for row in scatter_sample.itertuples(index=False)
    ]

    validation_metrics = training_metrics.get("validation_metrics", artifact.get("validation_metrics", {}))
    test_metrics = training_metrics.get("test_metrics", artifact.get("test_metrics", {}))
    prediction_log = _load_prediction_log()

    logged_healthy = int(prediction_log["outcome_distribution"]["healthy"])
    logged_failure = int(prediction_log["outcome_distribution"]["failure"])
    alert_healthy = int(target_counts.get(0, 0))
    alert_failure = int(target_counts.get(1, 0)) + logged_failure
    alert_total = alert_healthy + alert_failure
    alert_failure_rate = round((alert_failure / alert_total) * 100.0, 2) if alert_total else 0.0

    return {
        "model": {
            "name": artifact.get("model_name", "unknown"),
            "threshold": round(float(artifact.get("threshold", 0.45)), 4),
            "trained_at_utc": artifact.get("trained_at_utc"),
        },
        "dataset": {
            "rows": int(len(frame)),
            "healthy_count": int(target_counts.get(0, 0)),
            "failure_count": int(target_counts.get(1, 0)),
            "failure_rate": round(float(frame["machine_failure"].mean()) * 100.0, 2),
            "alert_target_distribution": [
                {"label": "Healthy", "count": alert_healthy, "share": _safe_percent(alert_healthy, alert_total)},
                {"label": "Failure", "count": alert_failure, "share": _safe_percent(alert_failure, alert_total)},
            ],
            "alert_total": alert_total,
            "alert_failure_rate": alert_failure_rate,
            "logged_healthy_predictions": logged_healthy,
            "logged_failure_alerts": logged_failure,
            "type_distribution": [
                {"label": label, "count": int(type_counts[label]), "share": _safe_percent(int(type_counts[label]), len(frame))}
                for label in ["L", "M", "H"]
            ],
            "target_distribution": [
                {"label": "Healthy", "count": int(target_counts.get(0, 0)), "share": _safe_percent(int(target_counts.get(0, 0)), len(frame))},
                {"label": "Failure", "count": int(target_counts.get(1, 0)), "share": _safe_percent(int(target_counts.get(1, 0)), len(frame))},
            ],
            "sensor_means": {
                "healthy": {k: round(float(v), 2) for k, v in healthy_means.to_dict().items()},
                "failure": {k: round(float(v), 2) for k, v in failure_means.to_dict().items()},
            },
            "normalized_sensor_profiles": {
                "healthy": _normalise_profile(healthy_means, frame),
                "failure": _normalise_profile(failure_means, frame),
            },
            "scatter_points": scatter_points,
        },
        "metrics": {
            "labels": ["Accuracy", "Precision", "Recall", "F1", "PR-AUC"],
            "validation": [
                round(float(validation_metrics.get("accuracy", 0.0)), 4),
                round(float(validation_metrics.get("precision", 0.0)), 4),
                round(float(validation_metrics.get("recall", 0.0)), 4),
                round(float(validation_metrics.get("f1", 0.0)), 4),
                round(float(validation_metrics.get("average_precision", 0.0)), 4),
            ],
            "test": [
                round(float(test_metrics.get("accuracy", 0.0)), 4),
                round(float(test_metrics.get("precision", 0.0)), 4),
                round(float(test_metrics.get("recall", 0.0)), 4),
                round(float(test_metrics.get("f1", 0.0)), 4),
                round(float(test_metrics.get("average_precision", 0.0)), 4),
            ],
            "validation_details": validation_metrics,
            "test_details": test_metrics,
        },
        "feature_importance": _feature_importance_to_records(artifact["pipeline"]),
        "prediction_log": prediction_log,
        "insights": [
            f"Failure rate is {round(float(frame['machine_failure'].mean()) * 100.0, 2)}% across {len(frame):,} samples.",
            f"Machine type L is the most common group with {int(type_counts['L']):,} records.",
            f"Selected model: {artifact.get('model_name', 'unknown')} with threshold {round(float(artifact.get('threshold', 0.45)), 2)}.",
        ],
    }
