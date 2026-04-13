"""Inference helpers for the phase-1 model artifact."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from threading import Lock
from pathlib import Path
from typing import Any
from uuid import uuid4

import joblib

from src.config import MODEL_BUNDLE_PATH, PREDICTIONS_LOG_PATH
from src.data import build_inference_frame
from src.modeling import predict_with_pipeline


PAYLOAD_ALIASES = {
    "air_temperature_k": "air_temperature",
    "process_temperature_k": "process_temperature",
    "rotational_speed_rpm": "rotational_speed",
    "torque_nm": "torque",
    "tool_wear_min": "tool_wear",
}

PREDICTION_LOG_FIELDS = [
    "prediction_id",
    "timestamp_utc",
    "batch_id",
    "sample_index",
    "type",
    "air_temperature",
    "process_temperature",
    "rotational_speed",
    "torque",
    "tool_wear",
    "failure_prediction",
    "risk_probability",
    "risk_level",
    "action",
    "decision_threshold",
    "model_name",
]

_LOG_LOCK = Lock()


def load_artifact(path: str | Path = MODEL_BUNDLE_PATH) -> dict[str, Any]:
    """Load the serialized phase-1 model bundle."""

    bundle_path = Path(path)
    if not bundle_path.exists():
        raise FileNotFoundError(
            f"Model bundle not found at {bundle_path}. Run src.train first to create it."
        )
    return joblib.load(bundle_path)


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Accept both API-friendly aliases and canonical field names."""

    normalized: dict[str, Any] = {}
    for key, value in payload.items():
        normalized[PAYLOAD_ALIASES.get(key, key)] = value
    return normalized


def classify_risk_level(probability: float) -> tuple[str, str]:
    """Map model probability to an operational risk label and next action."""

    if probability < 0.20:
        return "LOW", "No immediate maintenance required"
    if probability < 0.50:
        return "MEDIUM", "Inspect machine soon and monitor sensor drift"
    return "HIGH", "Schedule maintenance immediately"


def predict_with_metadata(
    payload: dict[str, Any],
    artifact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return prediction output plus model metadata for logging and APIs."""

    bundle = artifact or load_artifact()
    normalized_payload = normalize_payload(payload)
    frame = build_inference_frame(normalized_payload)
    prediction, probability = predict_with_pipeline(
        bundle["pipeline"], bundle["threshold"], frame
    )
    risk_level, action = classify_risk_level(probability)
    return {
        "failure_prediction": prediction,
        "risk_probability": round(probability, 4),
        "risk_level": risk_level,
        "action": action,
        "decision_threshold": round(float(bundle["threshold"]), 4),
        "model_name": bundle["model_name"],
        "normalized_payload": normalized_payload,
    }


def append_prediction_log(
    payload: dict[str, Any],
    prediction: dict[str, Any],
    *,
    batch_id: str | None = None,
    sample_index: int | None = None,
    log_path: str | Path = PREDICTIONS_LOG_PATH,
) -> None:
    """Append one prediction event to the CSV log."""

    row = {
        "prediction_id": str(uuid4()),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "batch_id": batch_id or "",
        "sample_index": "" if sample_index is None else sample_index,
        "type": payload["type"],
        "air_temperature": payload["air_temperature"],
        "process_temperature": payload["process_temperature"],
        "rotational_speed": payload["rotational_speed"],
        "torque": payload["torque"],
        "tool_wear": payload["tool_wear"],
        "failure_prediction": prediction["failure_prediction"],
        "risk_probability": prediction["risk_probability"],
        "risk_level": prediction["risk_level"],
        "action": prediction["action"],
        "decision_threshold": prediction["decision_threshold"],
        "model_name": prediction["model_name"],
    }

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with _LOG_LOCK:
        file_exists = path.exists() and path.stat().st_size > 0
        with path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=PREDICTION_LOG_FIELDS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)


def predict_and_log(
    payload: dict[str, Any],
    artifact: dict[str, Any] | None = None,
    *,
    batch_id: str | None = None,
    sample_index: int | None = None,
) -> dict[str, Any]:
    """Run inference and persist the event to the predictions log."""

    prediction = predict_with_metadata(payload, artifact=artifact)
    append_prediction_log(
        prediction["normalized_payload"],
        prediction,
        batch_id=batch_id,
        sample_index=sample_index,
    )
    return {
        "failure_prediction": prediction["failure_prediction"],
        "risk_probability": prediction["risk_probability"],
        "risk_level": prediction["risk_level"],
        "action": prediction["action"],
    }


def predict_batch_and_log(
    payloads: list[dict[str, Any]],
    artifact: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Run inference for a batch of payloads and log each result."""

    batch_id = str(uuid4())
    results: list[dict[str, Any]] = []
    for index, payload in enumerate(payloads):
        result = predict_with_metadata(payload, artifact=artifact)
        append_prediction_log(
            result["normalized_payload"],
            result,
            batch_id=batch_id,
            sample_index=index,
        )
        results.append(
            {
                "failure_prediction": result["failure_prediction"],
                "risk_probability": result["risk_probability"],
                "risk_level": result["risk_level"],
                "action": result["action"],
            }
        )
    return results


def predict(payload: dict[str, Any], artifact: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a structured prediction response for one machine sample."""

    return predict_and_log(payload, artifact=artifact)
