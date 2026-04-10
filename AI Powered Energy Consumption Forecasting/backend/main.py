from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import (  # noqa: E402
    forecast_all_regions,
    forecast_region,
    get_available_regions,
    load_artifact,
    load_canonical_data,
)


app = FastAPI(title="PJM Hourly Forecast API", version="1.0.0")


class ForecastRequest(BaseModel):
    region: Optional[str] = None
    horizon: int = Field(default=24, ge=1, le=168)


def _serialize_forecast(frame: pd.DataFrame) -> list[dict]:
    payload = frame.copy()
    payload["Datetime"] = pd.to_datetime(payload["Datetime"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    return payload.to_dict(orient="records")


@lru_cache(maxsize=1)
def _cached_history() -> pd.DataFrame:
    return load_canonical_data()


@lru_cache(maxsize=1)
def _cached_artifact() -> dict:
    return load_artifact()


@app.get("/")
def home():
    history = _cached_history()
    try:
        artifact = _cached_artifact()
        feature_count = len(artifact["feature_columns"])
    except Exception:
        feature_count = 0
    return {
        "message": "PJM Hourly Forecast API Running",
        "rows": int(len(history)),
        "regions": get_available_regions(history),
        "feature_count": feature_count,
    }


@app.get("/regions")
def regions():
    return {"regions": get_available_regions(_cached_history())}


@app.post("/forecast")
def forecast(request: ForecastRequest):
    try:
        history = _cached_history()
        artifact = _cached_artifact()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to load forecasting artifact: {exc}") from exc

    if request.region and request.region.lower() not in {"all", "all regions"}:
        if request.region not in get_available_regions(history):
            raise HTTPException(status_code=400, detail=f"Unknown region: {request.region}")
        frame = forecast_region(history, region=request.region, horizon=request.horizon, artifact=artifact)
        mode = "single"
        requested_region = request.region
    else:
        frame = forecast_all_regions(history, horizon=request.horizon, artifact=artifact)
        mode = "all"
        requested_region = "all"

    return {
        "mode": mode,
        "requested_region": requested_region,
        "horizon": request.horizon,
        "forecast_rows": _serialize_forecast(frame),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)
