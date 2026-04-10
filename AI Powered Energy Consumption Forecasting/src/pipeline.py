from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
ARTIFACT_PATH = MODELS_DIR / "pjm_forecasting_artifact.joblib"
METRICS_PATH = OUTPUTS_DIR / "training_metrics.json"
FEATURE_IMPORTANCE_PATH = OUTPUTS_DIR / "feature_importance.csv"
EVALUATION_PLOT_PATH = OUTPUTS_DIR / "evaluation_plot.png"
BACKTEST_PREDICTIONS_PATH = OUTPUTS_DIR / "walk_forward_backtest_predictions.csv"

LAGS = (1, 2, 3, 24, 48, 168)
ROLLING_WINDOWS = (3, 24, 168)
EPSILON = 1e-6


@dataclass(frozen=True)
class Artifact:
    model: object
    feature_columns: list[str]
    metadata: dict


class RidgeRegressor:
    def __init__(self, alpha: float = 5.0):
        self.alpha = float(alpha)
        self.intercept_: float = 0.0
        self.coef_: np.ndarray | None = None
        self.feature_means_: np.ndarray | None = None
        self.feature_scales_: np.ndarray | None = None
        self.feature_importances_: np.ndarray | None = None

    def fit(self, X: pd.DataFrame | np.ndarray, y: pd.Series | np.ndarray) -> "RidgeRegressor":
        X_array = np.asarray(X, dtype=float)
        y_array = np.asarray(y, dtype=float).reshape(-1)

        self.feature_means_ = X_array.mean(axis=0)
        self.feature_scales_ = X_array.std(axis=0)
        self.feature_scales_[self.feature_scales_ == 0] = 1.0

        X_scaled = (X_array - self.feature_means_) / self.feature_scales_
        X_design = np.column_stack([np.ones(len(X_scaled)), X_scaled])

        regularizer = np.eye(X_design.shape[1])
        regularizer[0, 0] = 0.0

        beta = np.linalg.solve(
            X_design.T @ X_design + self.alpha * regularizer,
            X_design.T @ y_array,
        )
        self.intercept_ = float(beta[0])
        self.coef_ = beta[1:]
        importance = np.abs(self.coef_)
        self.feature_importances_ = importance / importance.sum() if importance.sum() else importance
        return self

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        if self.coef_ is None or self.feature_means_ is None or self.feature_scales_ is None:
            raise ValueError("The model must be fit before calling predict().")

        X_array = np.asarray(X, dtype=float)
        X_scaled = (X_array - self.feature_means_) / self.feature_scales_
        return X_scaled @ self.coef_ + self.intercept_


def _ensure_output_dirs() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def _is_wide_frame(frame: pd.DataFrame) -> bool:
    columns = [str(column) for column in frame.columns]
    return "Datetime" in columns and len(columns) > 2


def _read_frame(path: Path) -> Optional[pd.DataFrame]:
    try:
        if path.suffix.lower() in {".parquet", ".pq", ".paruqet"}:
            frame = pd.read_parquet(path)
        else:
            frame = pd.read_csv(path)
        if isinstance(frame.index, pd.DatetimeIndex) or frame.index.name == "Datetime":
            frame = frame.reset_index()
        return frame
    except Exception as exc:  # pragma: no cover - defensive file handling
        warnings.warn(f"Skipping {path.name}: {exc}")
        return None


def _to_naive_datetime(values: pd.Series | pd.Index) -> pd.Series:
    datetimes = pd.to_datetime(values, errors="coerce", utc=True)
    if isinstance(datetimes, pd.Series):
        return datetimes.dt.tz_convert(None)
    return pd.Series(datetimes.tz_convert(None), index=getattr(values, "index", None))


def _normalize_long_frame(frame: pd.DataFrame, source_name: str) -> pd.DataFrame:
    frame = frame.copy()
    frame.columns = [str(column).strip() for column in frame.columns]

    if "Datetime" not in frame.columns:
        if len(frame.columns) < 2:
            raise ValueError(f"Source {source_name} does not contain enough columns to normalize")
        frame = frame.iloc[:, :2].copy()
        frame.columns = ["Datetime", "Load"]
    elif len(frame.columns) == 2:
        second_column = [column for column in frame.columns if column != "Datetime"][0]
        frame = frame[["Datetime", second_column]].copy()
        frame.columns = ["Datetime", "Load"]

    if _is_wide_frame(frame):
        return _normalize_wide_frame(frame)

    frame = frame.rename(columns={frame.columns[0]: "Datetime", frame.columns[1]: "Load"})
    frame["Datetime"] = _to_naive_datetime(frame["Datetime"])
    frame["Load"] = pd.to_numeric(frame["Load"], errors="coerce")
    frame["Region"] = source_name.replace("_hourly", "").replace(".csv", "").replace(".parquet", "")
    return frame[["Datetime", "Region", "Load"]]


def _normalize_wide_frame(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame.columns = [str(column).strip() for column in frame.columns]
    frame["Datetime"] = _to_naive_datetime(frame["Datetime"])
    melted = frame.melt(id_vars="Datetime", var_name="Region", value_name="Load")
    melted["Load"] = pd.to_numeric(melted["Load"], errors="coerce")
    return melted[["Datetime", "Region", "Load"]]


def load_canonical_data(data_dir: str | Path = DATA_DIR) -> pd.DataFrame:
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_path}")

    frames: list[pd.DataFrame] = []
    for path in sorted(data_path.iterdir(), key=lambda item: (item.suffix.lower() in {".parquet", ".pq", ".paruqet"}, item.name.lower())):
        if path.is_dir():
            continue

        if path.suffix.lower() not in {".csv", ".parquet", ".pq", ".paruqet"}:
            continue

        frame = _read_frame(path)
        if frame is None or frame.empty:
            continue

        if _is_wide_frame(frame):
            normalized = _normalize_wide_frame(frame)
        else:
            normalized = _normalize_long_frame(frame, path.stem)

        frames.append(normalized)

    if not frames:
        raise ValueError(f"No usable energy datasets found in {data_path}")

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.dropna(subset=["Datetime", "Region", "Load"])
    combined["Datetime"] = _to_naive_datetime(combined["Datetime"])
    combined["Region"] = combined["Region"].astype(str).str.strip()
    combined["Load"] = pd.to_numeric(combined["Load"], errors="coerce")
    combined = combined.dropna(subset=["Datetime", "Region", "Load"])
    combined = combined.drop_duplicates(subset=["Datetime", "Region"], keep="first")
    combined = combined.sort_values(["Region", "Datetime"]).reset_index(drop=True)
    return combined


def load_all_data(data_path: str | Path = DATA_DIR) -> pd.DataFrame:
    return load_canonical_data(data_path)


def _calendar_holidays(datetimes: pd.Series) -> pd.Series:
    normalized_dates = pd.to_datetime(datetimes).dt.normalize()
    if normalized_dates.empty:
        return pd.Series(dtype=int, index=normalized_dates.index)

    start = normalized_dates.min()
    end = normalized_dates.max()
    holidays = USFederalHolidayCalendar().holidays(start=start, end=end).normalize()
    return normalized_dates.isin(holidays).astype(int)


def _cyclical_encode(values: pd.Series, period: int, prefix: str) -> pd.DataFrame:
    angle = 2.0 * np.pi * values.astype(float) / float(period)
    return pd.DataFrame(
        {
            f"{prefix}_sin": np.sin(angle),
            f"{prefix}_cos": np.cos(angle),
        },
        index=values.index,
    )


def create_feature_frame(df: pd.DataFrame, drop_na: bool = True) -> pd.DataFrame:
    frame = df.copy()
    frame["Datetime"] = pd.to_datetime(frame["Datetime"], errors="coerce")
    frame["Region"] = frame["Region"].astype(str)
    frame["Load"] = pd.to_numeric(frame["Load"], errors="coerce")
    frame = frame.dropna(subset=["Datetime", "Region"])
    frame = frame.sort_values(["Region", "Datetime"]).reset_index(drop=True)

    dt = frame["Datetime"]
    frame["hour"] = dt.dt.hour
    frame["day"] = dt.dt.day
    frame["dayofweek"] = dt.dt.dayofweek
    frame["dayofyear"] = dt.dt.dayofyear
    frame["weekofyear"] = dt.dt.isocalendar().week.astype(int)
    frame["month"] = dt.dt.month
    frame["quarter"] = dt.dt.quarter
    frame["year"] = dt.dt.year
    frame["is_weekend"] = (frame["dayofweek"] >= 5).astype(int)
    frame["is_month_start"] = dt.dt.is_month_start.astype(int)
    frame["is_month_end"] = dt.dt.is_month_end.astype(int)
    frame["is_quarter_start"] = dt.dt.is_quarter_start.astype(int)
    frame["is_quarter_end"] = dt.dt.is_quarter_end.astype(int)
    frame["is_peak_hour"] = frame["hour"].isin([7, 8, 9, 10, 17, 18, 19, 20]).astype(int)
    frame["is_holiday"] = _calendar_holidays(frame["Datetime"])
    frame["is_business_day"] = ((frame["is_weekend"] == 0) & (frame["is_holiday"] == 0)).astype(int)

    cyclic_parts = [
        _cyclical_encode(frame["hour"], 24, "hour"),
        _cyclical_encode(frame["dayofweek"], 7, "dayofweek"),
        _cyclical_encode(frame["month"], 12, "month"),
        _cyclical_encode(frame["dayofyear"], 366, "dayofyear"),
        _cyclical_encode(frame["weekofyear"], 53, "weekofyear"),
    ]
    for part in cyclic_parts:
        frame = pd.concat([frame, part], axis=1)

    grouped = frame.groupby("Region", sort=False)
    for lag in LAGS:
        frame[f"lag_{lag}"] = grouped["Load"].shift(lag)

    for window in ROLLING_WINDOWS:
        shifted = grouped["Load"].transform(lambda s: s.shift(1))
        frame[f"rolling_mean_{window}"] = frame.groupby("Region", sort=False)["Load"].transform(
            lambda s, w=window: s.shift(1).rolling(window=w, min_periods=1).mean()
        )
        frame[f"rolling_std_{window}"] = frame.groupby("Region", sort=False)["Load"].transform(
            lambda s, w=window: s.shift(1).rolling(window=w, min_periods=1).std(ddof=0)
        )
        frame[f"rolling_min_{window}"] = frame.groupby("Region", sort=False)["Load"].transform(
            lambda s, w=window: s.shift(1).rolling(window=w, min_periods=1).min()
        )
        frame[f"rolling_max_{window}"] = frame.groupby("Region", sort=False)["Load"].transform(
            lambda s, w=window: s.shift(1).rolling(window=w, min_periods=1).max()
        )

    frame["trend_lag_1_24"] = frame["lag_1"] - frame["lag_24"]
    frame["trend_lag_1_48"] = frame["lag_1"] - frame["lag_48"]
    frame["trend_lag_1_168"] = frame["lag_1"] - frame["lag_168"]
    frame["trend_lag_24_168"] = frame["lag_24"] - frame["lag_168"]
    frame["trend_rolling_24_168"] = frame["rolling_mean_24"] - frame["rolling_mean_168"]
    frame["trend_rolling_std_24_168"] = frame["rolling_std_24"] - frame["rolling_std_168"]
    frame["ratio_lag_1_24"] = frame["lag_1"] / (frame["lag_24"] + EPSILON)
    frame["ratio_lag_24_168"] = frame["lag_24"] / (frame["lag_168"] + EPSILON)
    frame["ratio_roll_24_168"] = frame["rolling_mean_24"] / (frame["rolling_mean_168"] + EPSILON)

    region_dummies = pd.get_dummies(frame["Region"], prefix="region", dtype=int)
    frame = pd.concat([frame, region_dummies], axis=1)

    if drop_na:
        feature_columns = [column for column in frame.columns if column not in {"Datetime", "Region", "Load"}]
        frame = frame.dropna(subset=feature_columns + ["Load"])

    return frame.reset_index(drop=True)


def create_features(df: pd.DataFrame, drop_na: bool = True) -> pd.DataFrame:
    return create_feature_frame(df, drop_na=drop_na)


def get_feature_columns(frame: pd.DataFrame) -> list[str]:
    return [column for column in frame.columns if column not in {"Datetime", "Region", "Load"}]


def _score_arrays(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    y_true = np.asarray(y_true, dtype=float).reshape(-1)
    y_pred = np.asarray(y_pred, dtype=float).reshape(-1)
    residuals = y_true - y_pred
    total = np.sum((y_true - y_true.mean()) ** 2)
    return {
        "mae": float(np.mean(np.abs(residuals))),
        "rmse": float(np.sqrt(np.mean(residuals ** 2))),
        "r2": float(1.0 - (np.sum(residuals ** 2) / total if total else 0.0)),
    }


def _chronological_split(frame: pd.DataFrame, train_fraction: float = 0.8) -> tuple[pd.DataFrame, pd.DataFrame]:
    unique_dates = np.sort(frame["Datetime"].dropna().unique())
    if len(unique_dates) < 2:
        raise ValueError("Need at least two distinct timestamps to perform a chronological split")

    split_index = int(len(unique_dates) * train_fraction)
    split_index = min(max(split_index, 1), len(unique_dates) - 1)
    cutoff = pd.Timestamp(unique_dates[split_index])

    train = frame[frame["Datetime"] < cutoff].copy()
    test = frame[frame["Datetime"] >= cutoff].copy()
    if train.empty or test.empty:
        raise ValueError("Chronological split produced an empty train or test partition")
    return train, test


def _walk_forward_origins(df: pd.DataFrame, folds: int, horizon_hours: int, training_window_days: int) -> list[pd.Timestamp]:
    unique_dates = pd.Index(pd.to_datetime(df["Datetime"].dropna().unique())).sort_values()
    if len(unique_dates) <= horizon_hours + 1:
        raise ValueError("Not enough timestamps for walk-forward validation")

    first_complete_start = df.groupby("Region")["Datetime"].min().max() + pd.Timedelta(days=int(training_window_days))
    candidate_dates = unique_dates[(unique_dates >= first_complete_start) & (unique_dates <= unique_dates[-(horizon_hours + 1)])]
    candidate_dates = candidate_dates[:: max(1, int(horizon_hours))]
    if len(candidate_dates) == 0:
        raise ValueError("No valid walk-forward origins were found")

    folds = max(1, min(int(folds), len(candidate_dates)))
    positions = np.linspace(0, len(candidate_dates) - 1, num=folds, dtype=int)
    origins = [pd.Timestamp(candidate_dates[pos]) for pos in positions]
    return origins


def _recursive_persistence_forecast(region_history: pd.DataFrame, horizon: int) -> np.ndarray:
    if region_history.empty:
        return np.array([], dtype=float)
    last_value = float(pd.to_numeric(region_history["Load"], errors="coerce").dropna().iloc[-1])
    return np.repeat(last_value, horizon)


def walk_forward_backtest(df: pd.DataFrame, horizon: int = 24, folds: int = 2, training_window_days: int = 365) -> tuple[pd.DataFrame, dict]:
    origins = _walk_forward_origins(df, folds=folds, horizon_hours=horizon, training_window_days=training_window_days)
    all_predictions: list[pd.DataFrame] = []
    all_naive_predictions: list[pd.DataFrame] = []
    fold_summaries: list[dict] = []

    for fold_number, origin in enumerate(origins, start=1):
        train_window_start = origin - pd.Timedelta(days=int(training_window_days))
        train_raw = df[(df["Datetime"] > train_window_start) & (df["Datetime"] <= origin)].copy()
        if train_raw.empty:
            continue

        train_features = create_feature_frame(train_raw, drop_na=True)
        feature_columns = get_feature_columns(train_features)
        model = _train_estimator()
        model.fit(train_features[feature_columns], train_features["Load"])
        artifact = {"model": model, "feature_columns": feature_columns}

        fold_frames: list[pd.DataFrame] = []
        fold_naive: list[pd.DataFrame] = []
        forecast_end = origin + pd.Timedelta(hours=horizon)

        for region in sorted(train_raw["Region"].dropna().astype(str).unique().tolist()):
            region_history = train_raw[train_raw["Region"].astype(str) == region].copy()
            if len(pd.to_numeric(region_history["Load"], errors="coerce").dropna()) < max(LAGS):
                continue

            forecast_frame = forecast_region(region_history, region=region, horizon=horizon, artifact=artifact)
            actual_future = df[
                (df["Region"].astype(str) == region)
                & (df["Datetime"] > origin)
                & (df["Datetime"] <= forecast_end)
            ][["Datetime", "Region", "Load"]].copy()

            merged = forecast_frame.merge(actual_future, on=["Datetime", "Region"], how="inner")
            if merged.empty:
                continue

            merged["Fold"] = fold_number
            merged["Origin"] = origin
            merged["Error"] = merged["Load"] - merged["Predicted_Load"]
            fold_frames.append(merged)

            naive_preds = _recursive_persistence_forecast(region_history, len(merged))
            fold_naive.append(
                pd.DataFrame(
                    {
                        "Datetime": merged["Datetime"].values,
                        "Region": merged["Region"].values,
                        "Load": merged["Load"].values,
                        "Naive_Prediction": naive_preds[: len(merged)],
                        "Fold": fold_number,
                        "Origin": origin,
                    }
                )
            )

        if not fold_frames:
            continue

        fold_result = pd.concat(fold_frames, ignore_index=True)
        fold_naive_frame = pd.concat(fold_naive, ignore_index=True) if fold_naive else pd.DataFrame()
        fold_scores = _score_arrays(fold_result["Load"].to_numpy(), fold_result["Predicted_Load"].to_numpy())
        naive_scores = _score_arrays(fold_naive_frame["Load"].to_numpy(), fold_naive_frame["Naive_Prediction"].to_numpy()) if not fold_naive_frame.empty else {"mae": np.nan, "rmse": np.nan, "r2": np.nan}

        fold_summaries.append(
            {
                "fold": fold_number,
                "origin": origin.isoformat(),
                "rows": int(len(fold_result)),
                "mae": float(fold_scores["mae"]),
                "rmse": float(fold_scores["rmse"]),
                "r2": float(fold_scores["r2"]),
                "naive_mae": float(naive_scores["mae"]),
                "naive_rmse": float(naive_scores["rmse"]),
                "naive_r2": float(naive_scores["r2"]),
            }
        )
        all_predictions.append(fold_result)
        if not fold_naive_frame.empty:
            all_naive_predictions.append(fold_naive_frame)

    if not all_predictions:
        raise ValueError("Walk-forward validation did not produce any predictions")

    backtest_df = pd.concat(all_predictions, ignore_index=True)
    backtest_naive_df = pd.concat(all_naive_predictions, ignore_index=True) if all_naive_predictions else pd.DataFrame()
    backtest_scores = _score_arrays(backtest_df["Load"].to_numpy(), backtest_df["Predicted_Load"].to_numpy())
    persistence_scores = _score_arrays(backtest_naive_df["Load"].to_numpy(), backtest_naive_df["Naive_Prediction"].to_numpy()) if not backtest_naive_df.empty else {"mae": np.nan, "rmse": np.nan, "r2": np.nan}
    return backtest_df, {
        "forecast_horizon_hours": int(horizon),
        "training_window_days": int(training_window_days),
        "fold_count": int(len(fold_summaries)),
        "folds": fold_summaries,
        "mae": backtest_scores["mae"],
        "rmse": backtest_scores["rmse"],
        "r2": backtest_scores["r2"],
        "persistence_mae": persistence_scores["mae"],
        "persistence_rmse": persistence_scores["rmse"],
        "persistence_r2": persistence_scores["r2"],
    }


def _train_estimator() -> RidgeRegressor:
    return RidgeRegressor(alpha=10.0)


def _save_final_outputs(
    model: RidgeRegressor,
    feature_columns: list[str],
    backtest_df: pd.DataFrame,
    backtest_metrics: dict,
    final_fit_rows: int,
) -> dict:
    metrics = dict(backtest_metrics)
    metrics.update(
        {
            "final_fit_rows": int(final_fit_rows),
            "feature_count": int(len(feature_columns)),
            "regions": sorted(backtest_df["Region"].dropna().astype(str).unique().tolist()),
            "model_type": "RidgeRegressor",
        }
    )

    artifact = Artifact(
        model=model,
        feature_columns=feature_columns,
        metadata=metrics,
    )
    joblib.dump(artifact.__dict__, ARTIFACT_PATH)

    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    importance = pd.DataFrame(
        {
            "feature": feature_columns,
            "importance": model.feature_importances_ if model.feature_importances_ is not None else np.zeros(len(feature_columns)),
        }
    ).sort_values("importance", ascending=False)
    importance.to_csv(FEATURE_IMPORTANCE_PATH, index=False)

    backtest_df.to_csv(BACKTEST_PREDICTIONS_PATH, index=False)

    evaluation = backtest_df[["Origin", "Datetime", "Region", "Load", "Predicted_Load"]].copy()
    evaluation = evaluation.sort_values(["Origin", "Datetime", "Region"]).reset_index(drop=True)

    plt.figure(figsize=(14, 6))
    sample = evaluation.head(min(len(evaluation), 800))
    plt.plot(sample["Load"].to_numpy(), label="Actual", linewidth=1.5)
    plt.plot(sample["Predicted_Load"].to_numpy(), label="Predicted", linewidth=1.5)
    plt.title("PJM Walk-Forward Backtest")
    plt.xlabel("Backtest samples")
    plt.ylabel("Load (MW)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(EVALUATION_PLOT_PATH, dpi=160)
    plt.close()

    return metrics


def train_model(df: pd.DataFrame):
    _ensure_output_dirs()

    backtest_df, backtest_metrics = walk_forward_backtest(df, horizon=24, folds=2, training_window_days=365)

    full_feature_frame = create_feature_frame(df, drop_na=True)
    feature_columns = get_feature_columns(full_feature_frame)
    X_full = full_feature_frame[feature_columns]
    y_full = full_feature_frame["Load"]

    model = _train_estimator()
    model.fit(X_full, y_full)
    _save_final_outputs(model, feature_columns, backtest_df, backtest_metrics, final_fit_rows=len(full_feature_frame))

    return (
        float(backtest_metrics["rmse"]),
        float(backtest_metrics["r2"]),
        backtest_df["Predicted_Load"].to_numpy(),
        backtest_df["Load"].to_numpy(),
    )


def load_artifact(path: str | Path = ARTIFACT_PATH) -> dict:
    artifact_path = Path(path)
    if not artifact_path.exists():
        raise FileNotFoundError(
            f"Model artifact not found at {artifact_path}. Run the training script first to create it."
        )
    artifact = joblib.load(artifact_path)
    if not isinstance(artifact, dict) or "model" not in artifact or "feature_columns" not in artifact:
        raise ValueError("Stored artifact is malformed. Retrain the model to regenerate it.")
    return artifact


def get_available_regions(df: pd.DataFrame | None = None) -> list[str]:
    if df is None:
        df = load_canonical_data()
    return sorted(df["Region"].dropna().astype(str).unique().tolist())


def _build_future_feature_row(history: pd.DataFrame, region: str, next_timestamp: pd.Timestamp, feature_columns: list[str]) -> pd.DataFrame:
    future_history = pd.concat(
        [
            history,
            pd.DataFrame(
                {
                    "Datetime": [next_timestamp],
                    "Region": [region],
                    "Load": [np.nan],
                }
            ),
        ],
        ignore_index=True,
    )

    feature_frame = create_feature_frame(future_history, drop_na=False)
    feature_row = feature_frame.iloc[[-1]].copy()
    feature_row = feature_row.reindex(columns=feature_columns, fill_value=0)
    return feature_row


def forecast_region(
    history: pd.DataFrame,
    region: str,
    horizon: int = 24,
    artifact: Optional[dict] = None,
) -> pd.DataFrame:
    if artifact is None:
        artifact = load_artifact()

    model = artifact["model"]
    feature_columns = artifact["feature_columns"]

    region_history = history[history["Region"].astype(str) == str(region)].copy()
    region_history = region_history.sort_values("Datetime").reset_index(drop=True)
    if region_history.empty:
        raise ValueError(f"No historical rows available for region {region}")

    latest_known = region_history["Load"].dropna()
    if len(latest_known) < max(LAGS):
        raise ValueError(f"Region {region} does not have enough history for the configured lag features")

    working_history = region_history.copy()
    results: list[dict] = []

    for _ in range(horizon):
        next_timestamp = pd.to_datetime(working_history["Datetime"].iloc[-1]) + pd.Timedelta(hours=1)
        feature_row = _build_future_feature_row(working_history, region, next_timestamp, feature_columns)
        prediction = float(model.predict(feature_row)[0])
        results.append(
            {
                "Datetime": next_timestamp,
                "Region": region,
                "Predicted_Load": prediction,
            }
        )
        working_history = pd.concat(
            [
                working_history,
                pd.DataFrame(
                    {
                        "Datetime": [next_timestamp],
                        "Region": [region],
                        "Load": [prediction],
                    }
                ),
            ],
            ignore_index=True,
        )

    return pd.DataFrame(results)


def forecast_all_regions(
    history: pd.DataFrame,
    horizon: int = 24,
    artifact: Optional[dict] = None,
) -> pd.DataFrame:
    if artifact is None:
        artifact = load_artifact()

    regions = get_available_regions(history)
    forecasts = []
    for region in regions:
        region_forecast = forecast_region(history, region=region, horizon=horizon, artifact=artifact)
        forecasts.append(region_forecast)

    return pd.concat(forecasts, ignore_index=True).sort_values(["Datetime", "Region"]).reset_index(drop=True)


def forecast_next(
    df: pd.DataFrame,
    region: Optional[str] = None,
    horizon: int = 24,
    artifact: Optional[dict] = None,
):
    history = df.copy()
    if artifact is None:
        artifact = load_artifact()

    if region:
        return forecast_region(history, region=region, horizon=horizon, artifact=artifact)

    return {
        selected_region: forecast_region(history, region=selected_region, horizon=horizon, artifact=artifact)
        for selected_region in get_available_regions(history)
    }
