"""Dataset loading, validation, and feature engineering."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from src.config import (
    BASE_FEATURE_COLUMNS,
    COLUMN_RENAME_MAP,
    ENGINEERED_FEATURE_COLUMNS,
    LEAKAGE_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    RAW_COLUMNS,
    TARGET_COLUMN,
)


def load_raw_dataset(csv_path: str | Path) -> pd.DataFrame:
    """Load the AI4I 2020 CSV file and normalize column names.

    The dataset ships with human-readable column labels. For code and API
    consistency, we normalize them to snake_case here.
    """

    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path)
    validate_raw_schema(df)
    return df.rename(columns=COLUMN_RENAME_MAP)


def validate_raw_schema(df: pd.DataFrame) -> None:
    """Ensure the CSV contains the expected AI4I 2020 columns."""

    missing = [column for column in RAW_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(
            "Dataset schema is missing required columns: " + ", ".join(missing)
        )


def feature_engineering(frame: pd.DataFrame) -> pd.DataFrame:
    """Create leakage-safe derived features used by phase-1 models."""

    data = frame.copy()
    data["type"] = data["type"].astype(str).str.strip().str.upper()

    # These engineered features are available at inference time because they are
    # derived only from sensor telemetry, not from labels or future information.
    data["temperature_delta"] = data["process_temperature"] - data["air_temperature"]
    data["power_proxy"] = data["rotational_speed"] * data["torque"]
    data["wear_per_speed"] = data["tool_wear"] / (data["rotational_speed"].abs() + 1.0)

    return data


def build_training_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Return the feature matrix and target vector for model training."""

    normalized = df.copy()

    missing = [column for column in BASE_FEATURE_COLUMNS + [TARGET_COLUMN] if column not in normalized.columns]
    if missing:
        raise ValueError("Training frame is missing required columns: " + ", ".join(missing))

    X = normalized[BASE_FEATURE_COLUMNS].copy()
    y = normalized[TARGET_COLUMN].astype(int).copy()
    return X, y


def build_inference_frame(payload: dict) -> pd.DataFrame:
    """Convert a prediction payload into the model's canonical DataFrame format."""

    normalized = {}
    for key, value in payload.items():
        normalized[key] = value

    missing = [column for column in BASE_FEATURE_COLUMNS if column not in normalized]
    if missing:
        raise ValueError("Prediction payload is missing fields: " + ", ".join(missing))

    return pd.DataFrame([normalized], columns=BASE_FEATURE_COLUMNS)


def dataset_summary(df: pd.DataFrame) -> dict[str, object]:
    """Return a compact dataset summary for logging or JSON output."""

    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "target_rate": float(df[TARGET_COLUMN].mean()),
        "failure_count": int(df[TARGET_COLUMN].sum()),
        "leakage_columns_present": [column for column in LEAKAGE_COLUMNS if column in df.columns],
        "feature_columns": MODEL_FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
    }


def assert_no_missing_values(df: pd.DataFrame, columns: Iterable[str]) -> None:
    """Raise an error if any selected columns contain missing values."""

    missing_columns = [column for column in columns if df[column].isna().any()]
    if missing_columns:
        raise ValueError("Missing values detected in columns: " + ", ".join(missing_columns))
