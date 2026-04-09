from __future__ import annotations

from typing import Any

from .runtime import assert_expected_interpreter


assert_expected_interpreter()

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .alerts import generate_alerts
from .config import MODEL_PATH
from .predict import load_model, predict_from_dataframe


app = FastAPI(
    title="AI Cybersecurity Threat Detection API",
    version="1.0.0",
    description="Predicts malicious network activity using the UNSW-NB15 dataset.",
)


class PredictionRequest(BaseModel):
    records: list[dict[str, Any]] = Field(..., min_length=1)


class PredictionResponse(BaseModel):
    predictions: list[int]
    threats_detected: int
    alerts: list[dict[str, Any]]


@app.get("/health")
def health():
    return {"status": "ok", "model_path": str(MODEL_PATH)}


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest):
    try:
        model = load_model()
        df = pd.DataFrame(payload.records)
        predictions, probabilities = predict_from_dataframe(df, model=model, return_proba=True)
        alerts = generate_alerts(df, predictions, probabilities)
        return {
            "predictions": [int(pred) for pred in predictions],
            "threats_detected": int(sum(predictions)),
            "alerts": alerts,
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
