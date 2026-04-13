"""Model construction, evaluation, and serialization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from src.config import ENGINEERED_FEATURE_COLUMNS, RANDOM_STATE
from src.data import feature_engineering


try:  # Optional dependency.
    from xgboost import XGBClassifier

    XGBOOST_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency.
    XGBClassifier = None  # type: ignore[assignment]
    XGBOOST_AVAILABLE = False


@dataclass
class ModelCandidate:
    """A fitted candidate model with validation metrics and threshold."""

    name: str
    pipeline: Pipeline
    threshold: float
    validation_metrics: dict[str, float]


def make_preprocessor() -> ColumnTransformer:
    """Build the preprocessing pipeline used by all model candidates."""

    numeric_features = [
        "air_temperature",
        "process_temperature",
        "rotational_speed",
        "torque",
        "tool_wear",
        *ENGINEERED_FEATURE_COLUMNS,
    ]

    categorical_features = ["type"]

    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            ),
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "encoder",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        ),
                    ]
                ),
                categorical_features,
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def make_pipeline(estimator) -> Pipeline:
    """Assemble the full training/inference pipeline."""

    return Pipeline(
        steps=[
            ("feature_engineering", FunctionTransformer(feature_engineering, validate=False)),
            ("preprocess", make_preprocessor()),
            ("classifier", estimator),
        ]
    )


def build_candidate_estimators(y_train: pd.Series, random_state: int = RANDOM_STATE) -> dict[str, Any]:
    """Return the model candidates requested by the PRD."""

    positive_count = max(int((y_train == 1).sum()), 1)
    negative_count = max(int((y_train == 0).sum()), 1)
    scale_pos_weight = negative_count / positive_count

    candidates: dict[str, Any] = {
        "random_forest": RandomForestClassifier(
            n_estimators=70,
            max_depth=None,
            min_samples_split=2,
            min_samples_leaf=1,
            class_weight="balanced_subsample",
            random_state=random_state,
            n_jobs=-1,
        ),
    }

    if XGBOOST_AVAILABLE:
        candidates["xgboost"] = XGBClassifier(
            n_estimators=80,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.0,
            reg_alpha=0.0,
            min_child_weight=1,
            gamma=0.0,
            objective="binary:logistic",
            eval_metric="logloss",
            scale_pos_weight=scale_pos_weight,
            random_state=random_state,
            n_jobs=-1,
            tree_method="hist",
        )

    return candidates


def find_best_threshold(y_true: pd.Series, y_proba: np.ndarray) -> tuple[float, dict[str, float]]:
    """Find the threshold that maximizes validation F1 score."""

    best_threshold = 0.5
    best_metrics: dict[str, float] = {}
    best_score = -1.0

    thresholds = np.linspace(0.05, 0.95, 181)
    for threshold in thresholds:
        predictions = (y_proba >= threshold).astype(int)
        metrics = classification_metrics(y_true, predictions, y_proba)
        score = metrics["f1"]
        if score > best_score or (
            np.isclose(score, best_score) and metrics["recall"] > best_metrics.get("recall", -1.0)
        ):
            best_score = score
            best_threshold = float(threshold)
            best_metrics = metrics

    return best_threshold, best_metrics


def classification_metrics(y_true: pd.Series, y_pred: np.ndarray, y_proba: np.ndarray) -> dict[str, float]:
    """Compute standard binary classification metrics."""

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_proba)),
        "average_precision": float(average_precision_score(y_true, y_proba)),
        "tn": float(tn),
        "fp": float(fp),
        "fn": float(fn),
        "tp": float(tp),
    }


def evaluate_candidate(
    name: str,
    pipeline: Pipeline,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_validation: pd.DataFrame,
    y_validation: pd.Series,
) -> ModelCandidate:
    """Fit one model candidate and score it on the validation split."""

    fitted = pipeline.fit(X_train, y_train)
    validation_proba = fitted.predict_proba(X_validation)[:, 1]
    threshold, threshold_metrics = find_best_threshold(y_validation, validation_proba)
    validation_predictions = (validation_proba >= threshold).astype(int)
    metrics = classification_metrics(y_validation, validation_predictions, validation_proba)
    metrics.update({"validation_threshold": float(threshold)})
    metrics.update({f"threshold_{key}": float(value) for key, value in threshold_metrics.items() if key not in metrics})
    return ModelCandidate(name=name, pipeline=fitted, threshold=threshold, validation_metrics=metrics)


def choose_best_candidate(candidates: list[ModelCandidate]) -> ModelCandidate:
    """Select the best-performing candidate using F1, then recall, then PR-AUC."""

    if not candidates:
        raise ValueError("No model candidates were provided.")

    return max(
        candidates,
        key=lambda candidate: (
            candidate.validation_metrics["f1"],
            candidate.validation_metrics["recall"],
            candidate.validation_metrics["average_precision"],
        ),
    )


def predict_with_pipeline(pipeline: Pipeline, threshold: float, frame: pd.DataFrame) -> tuple[int, float]:
    """Return the class prediction and probability for a single input row."""

    probability = float(pipeline.predict_proba(frame)[:, 1][0])
    prediction = int(probability >= threshold)
    return prediction, probability
