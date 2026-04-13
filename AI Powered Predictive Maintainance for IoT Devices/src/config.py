"""Shared configuration for phase-1 model training and inference."""

from __future__ import annotations

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

DATASET_PATH = DATA_DIR / "ai4i2020.csv"
MODEL_BUNDLE_PATH = MODELS_DIR / "predictguard_phase1.joblib"
TRAINING_METRICS_PATH = MODELS_DIR / "training_metrics.json"
PREDICTIONS_LOG_PATH = LOGS_DIR / "predictions_log.csv"

RANDOM_STATE = 42
TEST_SIZE = 0.20
VALIDATION_SIZE = 0.20
DECISION_THRESHOLD = 0.45


# Raw CSV columns are normalized to these canonical names.
COLUMN_RENAME_MAP = {
    "UDI": "udi",
    "Product ID": "product_id",
    "Type": "type",
    "Air temperature [K]": "air_temperature",
    "Process temperature [K]": "process_temperature",
    "Rotational speed [rpm]": "rotational_speed",
    "Torque [Nm]": "torque",
    "Tool wear [min]": "tool_wear",
    "Machine failure": "machine_failure",
    "TWF": "twf",
    "HDF": "hdf",
    "PWF": "pwf",
    "OSF": "osf",
    "RNF": "rnf",
}

RAW_COLUMNS = list(COLUMN_RENAME_MAP.keys())
CANONICAL_COLUMNS = list(COLUMN_RENAME_MAP.values())

TARGET_COLUMN = "machine_failure"

BASE_FEATURE_COLUMNS = [
    "type",
    "air_temperature",
    "process_temperature",
    "rotational_speed",
    "torque",
    "tool_wear",
]

ENGINEERED_FEATURE_COLUMNS = [
    "temperature_delta",
    "power_proxy",
    "wear_per_speed",
]

MODEL_FEATURE_COLUMNS = BASE_FEATURE_COLUMNS + ENGINEERED_FEATURE_COLUMNS

LEAKAGE_COLUMNS = ["udi", "product_id", "twf", "hdf", "pwf", "osf", "rnf"]
EXPECTED_PREDICTION_FIELDS = BASE_FEATURE_COLUMNS
