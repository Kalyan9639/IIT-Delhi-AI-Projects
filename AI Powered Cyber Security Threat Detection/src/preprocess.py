from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import (
    ATTACK_CATEGORY_COLUMN,
    BASE_NUMERIC_COLUMNS,
    CATEGORICAL_COLUMNS,
    ENGINEERED_COLUMNS,
    ID_COLUMN,
    TARGET_COLUMN,
)


def load_data(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()

    for column in CATEGORICAL_COLUMNS:
        if column in frame.columns:
            frame[column] = frame[column].astype("string").fillna("unknown")

    for column in BASE_NUMERIC_COLUMNS:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    if "sbytes" in frame.columns and "dbytes" in frame.columns:
        frame["total_bytes"] = frame["sbytes"].fillna(0) + frame["dbytes"].fillna(0)
        frame["byte_ratio"] = frame["sbytes"].fillna(0) / (frame["dbytes"].fillna(0) + 1.0)
    else:
        frame["total_bytes"] = 0.0
        frame["byte_ratio"] = 0.0

    if "spkts" in frame.columns and "dpkts" in frame.columns:
        frame["total_packets"] = frame["spkts"].fillna(0) + frame["dpkts"].fillna(0)
    else:
        frame["total_packets"] = 0.0

    if "dur" in frame.columns:
        frame["packet_rate"] = frame["total_packets"] / (frame["dur"].fillna(0) + 1e-6)
    else:
        frame["packet_rate"] = 0.0

    if "sload" in frame.columns and "dload" in frame.columns:
        frame["load_diff"] = frame["sload"].fillna(0) - frame["dload"].fillna(0)
    else:
        frame["load_diff"] = 0.0

    if "stcpb" in frame.columns and "dtcpb" in frame.columns:
        frame["tcp_diff"] = frame["stcpb"].fillna(0) - frame["dtcpb"].fillna(0)
    else:
        frame["tcp_diff"] = 0.0

    return frame.replace([np.inf, -np.inf], np.nan)


def split_features_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series | None]:
    frame = df.copy()

    if ID_COLUMN in frame.columns:
        frame = frame.drop(columns=[ID_COLUMN])

    target = None
    if TARGET_COLUMN in frame.columns:
        target = frame[TARGET_COLUMN].astype(int)
        frame = frame.drop(columns=[TARGET_COLUMN])

    if ATTACK_CATEGORY_COLUMN in frame.columns:
        frame = frame.drop(columns=[ATTACK_CATEGORY_COLUMN])

    return frame, target


def build_preprocessor() -> ColumnTransformer:
    numeric_columns = BASE_NUMERIC_COLUMNS + ENGINEERED_COLUMNS

    try:
        categorical_encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        categorical_encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", categorical_encoder),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_columns),
            ("categorical", categorical_pipeline, CATEGORICAL_COLUMNS),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )

