"""Phase-1 training entrypoint for PredictGuard AI."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import train_test_split

from src.config import (
    DATASET_PATH,
    DECISION_THRESHOLD,
    MODEL_BUNDLE_PATH,
    MODELS_DIR,
    RANDOM_STATE,
    TARGET_COLUMN,
    TEST_SIZE,
    TRAINING_METRICS_PATH,
    VALIDATION_SIZE,
)
from src.data import (
    assert_no_missing_values,
    build_training_frame,
    dataset_summary,
    load_raw_dataset,
)
from src.modeling import (
    build_candidate_estimators,
    choose_best_candidate,
    classification_metrics,
    evaluate_candidate,
    make_pipeline,
    XGBOOST_AVAILABLE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train PredictGuard AI phase-1 models.")
    parser.add_argument("--data", type=Path, default=DATASET_PATH, help="Path to ai4i2020.csv")
    parser.add_argument("--model-dir", type=Path, default=MODELS_DIR, help="Directory for model artifacts")
    parser.add_argument("--random-state", type=int, default=RANDOM_STATE, help="Seed for deterministic splits")
    parser.add_argument("--test-size", type=float, default=TEST_SIZE, help="Fraction of data reserved for the final test split")
    parser.add_argument("--validation-size", type=float, default=VALIDATION_SIZE, help="Fraction of total data reserved for validation")
    parser.add_argument(
        "--include-xgboost",
        action="store_true",
        help="Force XGBoost candidate if the dependency is installed.",
    )
    return parser.parse_args()


def prepare_candidate_list(y_train: pd.Series, include_xgboost: bool, random_state: int):
    candidates = build_candidate_estimators(y_train=y_train, random_state=random_state)
    if not include_xgboost and "xgboost" in candidates:
        candidates.pop("xgboost")
    return candidates


def train_phase_one(
    data_path: Path,
    model_dir: Path,
    random_state: int,
    test_size: float,
    validation_size: float,
    include_xgboost: bool,
) -> dict:
    """Train, select, and persist the best model candidate."""

    if not 0.0 < test_size < 1.0:
        raise ValueError("test_size must be between 0 and 1.")
    if not 0.0 < validation_size < 1.0:
        raise ValueError("validation_size must be between 0 and 1.")
    if test_size + validation_size >= 1.0:
        raise ValueError("test_size + validation_size must be less than 1.")

    normalized_df = load_raw_dataset(data_path)
    assert_no_missing_values(normalized_df, normalized_df.columns)
    summary = dataset_summary(normalized_df)

    X, y = build_training_frame(normalized_df)

    # First hold out a final test set. The remaining data is split again into
    # train/validation for model selection and threshold tuning.
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        stratify=y,
        random_state=random_state,
    )

    validation_fraction = validation_size / (1.0 - test_size)
    X_train, X_validation, y_train, y_validation = train_test_split(
        X_train_val,
        y_train_val,
        test_size=validation_fraction,
        stratify=y_train_val,
        random_state=random_state,
    )

    candidate_estimators = prepare_candidate_list(y_train, include_xgboost, random_state)
    if include_xgboost and not XGBOOST_AVAILABLE:
        print("XGBoost is not installed in this environment, so the XGBoost candidate was skipped.")
    candidate_results = []

    print(f"Loaded {summary['rows']:,} rows with target failure rate {summary['target_rate']:.2%}")
    print(f"Training split: {len(X_train):,} rows")
    print(f"Validation split: {len(X_validation):,} rows")
    print(f"Test split: {len(X_test):,} rows")
    print("Evaluating model candidates...")

    for name, estimator in candidate_estimators.items():
        pipeline = make_pipeline(estimator)
        candidate = evaluate_candidate(
            name=name,
            pipeline=pipeline,
            X_train=X_train,
            y_train=y_train,
            X_validation=X_validation,
            y_validation=y_validation,
        )
        candidate_results.append(candidate)

        metrics = candidate.validation_metrics
        print(
            f"  - {name}: "
            f"F1={metrics['f1']:.4f}, "
            f"Recall={metrics['recall']:.4f}, "
            f"Precision={metrics['precision']:.4f}, "
            f"PR-AUC={metrics['average_precision']:.4f}, "
            f"Threshold={candidate.threshold:.3f}"
        )

    best_candidate = choose_best_candidate(candidate_results)
    print(f"Selected model: {best_candidate.name}")

    # Refit the selected pipeline on the combined train + validation data.
    final_pipeline = clone(best_candidate.pipeline)
    final_pipeline.fit(X_train_val, y_train_val)

    test_proba = final_pipeline.predict_proba(X_test)[:, 1]
    test_pred = (test_proba >= best_candidate.threshold)

    test_metrics = classification_metrics(y_test, test_pred, test_proba)
    print(
        f"Test metrics: F1={test_metrics['f1']:.4f}, "
        f"Recall={test_metrics['recall']:.4f}, "
        f"Precision={test_metrics['precision']:.4f}, "
        f"ROC-AUC={test_metrics['roc_auc']:.4f}, "
        f"PR-AUC={test_metrics['average_precision']:.4f}"
    )

    model_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = model_dir / MODEL_BUNDLE_PATH.name
    metrics_path = model_dir / TRAINING_METRICS_PATH.name
    artifact = {
        "pipeline": final_pipeline,
        "threshold": float(best_candidate.threshold),
        "model_name": best_candidate.name,
        "feature_columns": X.columns.tolist(),
        "target_column": TARGET_COLUMN,
        "random_state": random_state,
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(data_path),
        "validation_metrics": best_candidate.validation_metrics,
        "test_metrics": test_metrics,
        "dataset_summary": summary,
    }

    joblib.dump(artifact, bundle_path)

    metrics_payload = {
        "selected_model": best_candidate.name,
        "threshold": float(best_candidate.threshold),
        "validation_metrics": best_candidate.validation_metrics,
        "test_metrics": test_metrics,
        "dataset_summary": summary,
        "trained_at_utc": artifact["trained_at_utc"],
    }

    with metrics_path.open("w", encoding="utf-8") as handle:
        json.dump(metrics_payload, handle, indent=2)

    print(f"Saved model bundle to {bundle_path}")
    print(f"Saved metrics to {metrics_path}")

    return metrics_payload


def main() -> int:
    args = parse_args()
    train_phase_one(
        data_path=args.data,
        model_dir=args.model_dir,
        random_state=args.random_state,
        test_size=args.test_size,
        validation_size=args.validation_size,
        include_xgboost=args.include_xgboost,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
