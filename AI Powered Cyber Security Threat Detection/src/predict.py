from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from .config import MODEL_PATH, TARGET_COLUMN


def load_model(model_path: str | Path = MODEL_PATH):
    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model artifact not found at {model_path}. Run src/train.py first to train the pipeline."
        )
    return joblib.load(model_path)


def _prepare_frame(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    if TARGET_COLUMN in frame.columns:
        frame = frame.drop(columns=[TARGET_COLUMN])
    return frame


def predict_from_dataframe(
    df: pd.DataFrame,
    model: Any | None = None,
    return_proba: bool = False,
):
    frame = _prepare_frame(df)
    model = model or load_model()

    predictions = model.predict(frame)

    if not return_proba or not hasattr(model, "predict_proba"):
        return predictions

    probabilities = model.predict_proba(frame)
    return predictions, probabilities


def predict_from_records(records: list[dict[str, Any]], return_proba: bool = False):
    df = pd.DataFrame(records)
    return predict_from_dataframe(df, return_proba=return_proba)

