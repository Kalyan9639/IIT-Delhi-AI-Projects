from __future__ import annotations

from typing import Any

import pandas as pd

from .config import ATTACK_CATEGORY_COLUMN


def _severity_from_probability(probability: float) -> str:
    if probability >= 0.9:
        return "critical"
    if probability >= 0.75:
        return "high"
    if probability >= 0.5:
        return "medium"
    return "low"


def generate_alerts(
    df: pd.DataFrame,
    predictions: Any,
    probabilities: Any | None = None,
    include_normal: bool = False,
) -> list[dict[str, Any]]:
    frame = df.reset_index(drop=True).copy()
    alerts: list[dict[str, Any]] = []

    for index, prediction in enumerate(predictions):
        is_threat = int(prediction) == 1
        if not is_threat and not include_normal:
            continue

        confidence = None
        if probabilities is not None:
            confidence = float(probabilities[index][1] if probabilities.ndim == 2 else probabilities[index])

        attack_category = None
        if ATTACK_CATEGORY_COLUMN in frame.columns:
            raw_category = frame.loc[index, ATTACK_CATEGORY_COLUMN]
            if pd.notna(raw_category) and str(raw_category).strip().lower() != "normal":
                attack_category = str(raw_category)

        alerts.append(
            {
                "row_index": index,
                "severity": _severity_from_probability(confidence or 0.0) if is_threat else "info",
                "prediction": "threat" if is_threat else "normal",
                "attack_category": attack_category or "unknown",
                "confidence": confidence,
                "message": "Suspicious traffic detected" if is_threat else "No threat detected",
            }
        )

    return alerts

