"""FastAPI service for PredictGuard AI phase-1 inference."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from src.analytics import get_dashboard_snapshot
from src.config import MODEL_BUNDLE_PATH
from src.predict import load_artifact, predict_and_log, predict_batch_and_log


app = FastAPI(
    title="PredictGuard AI",
    version="1.0.0",
    description="Predictive maintenance inference API.",
)

BASE_DIR = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = BASE_DIR / "dashboard"

if DASHBOARD_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DASHBOARD_DIR), name="assets")


class MachineReading(BaseModel):
    type: str = Field(..., description="Machine type: L, M, or H")
    air_temperature: float = Field(..., gt=0, description="Air temperature in Kelvin")
    process_temperature: float = Field(..., gt=0, description="Process temperature in Kelvin")
    rotational_speed: float = Field(..., gt=0, description="Rotational speed in rpm")
    torque: float = Field(..., gt=0, description="Torque in Nm")
    tool_wear: float = Field(..., ge=0, description="Tool wear in minutes")

    @field_validator("type")
    @classmethod
    def normalize_type(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in {"L", "M", "H"}:
            raise ValueError("type must be one of: L, M, H")
        return normalized


class PredictionResponse(BaseModel):
    failure_prediction: int
    risk_probability: float
    risk_level: str
    action: str


class BatchPredictionRequest(BaseModel):
    samples: list[MachineReading] = Field(..., min_length=1)


class BatchPredictionResponse(BaseModel):
    count: int
    predictions: list[PredictionResponse]


@lru_cache(maxsize=1)
def get_artifact() -> dict:
    return load_artifact(MODEL_BUNDLE_PATH)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/", include_in_schema=False)
def dashboard_home() -> FileResponse:
    return FileResponse(DASHBOARD_DIR / "index.html")


@app.get("/dashboard", include_in_schema=False)
def dashboard_page() -> FileResponse:
    return FileResponse(DASHBOARD_DIR / "index.html")


@app.get("/api/dashboard-data")
def dashboard_data() -> dict:
    return get_dashboard_snapshot()


@app.post("/predict", response_model=PredictionResponse)
def predict_endpoint(payload: MachineReading) -> PredictionResponse:
    try:
        result = predict_and_log(payload.model_dump(), artifact=get_artifact())
        return PredictionResponse(**result)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/predict/batch", response_model=BatchPredictionResponse)
@app.post("/predict-batch", include_in_schema=False, response_model=BatchPredictionResponse)
def predict_batch_endpoint(payload: BatchPredictionRequest) -> BatchPredictionResponse:
    try:
        artifact = get_artifact()
        results = predict_batch_and_log(
            [sample.model_dump() for sample in payload.samples],
            artifact=artifact,
        )
        return BatchPredictionResponse(count=len(results), predictions=[PredictionResponse(**item) for item in results])
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/model-info")
def model_info() -> dict:
    """Return a quick summary of the trained artifact, if available."""

    try:
        artifact = get_artifact()
        return {
            "model_name": artifact["model_name"],
            "threshold": round(float(artifact["threshold"]), 4),
            "trained_at_utc": artifact["trained_at_utc"],
            "validation_metrics": artifact["validation_metrics"],
            "test_metrics": artifact["test_metrics"],
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
