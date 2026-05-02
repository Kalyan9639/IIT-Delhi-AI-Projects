import pandas as pd
import joblib
import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # Added for image serving

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChurnSentinel AI API",
    description="Backend scoring service for FinSolve Technologies churn prediction.",
    version="1.2.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STATIC ASSET SERVING ---
# This line maps the 'eda_assets' local folder to the '/assets' URL path
# Ensure the folder 'eda_assets' exists in the same directory as main.py
if os.path.exists("eda_assets"):
    app.mount("/assets", StaticFiles(directory="eda_assets"), name="assets")
    logger.info("Successfully mounted eda_assets directory.")
else:
    logger.error("Directory 'eda_assets' not found. Visual assets will not be served.")

# Load model and metrics from the 'model' subfolder
MODEL_PATH = os.path.join('model', 'churn_model.joblib')
METRICS_PATH = os.path.join('model', 'model_metrics.json')

model = None
if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.error(f"Error loading model: {e}")
else:
    logger.warning(f"Model file {MODEL_PATH} not found.")

# --- Pydantic Models for Input Validation ---

class CustomerData(BaseModel):
    gender: str
    SeniorCitizen: int
    Partner: str
    Dependents: str
    tenure: int
    PhoneService: str
    MultipleLines: str
    InternetService: str
    OnlineSecurity: str
    OnlineBackup: str
    DeviceProtection: str
    TechSupport: str
    StreamingTV: str
    StreamingMovies: str
    Contract: str
    PaperlessBilling: str
    PaymentMethod: str
    MonthlyCharges: float
    TotalCharges: float

class PredictionResponse(BaseModel):
    churn_probability: float
    is_high_risk: bool
    recommendation: str

# --- Utility Functions ---

def apply_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Replicates the feature engineering used during model training."""
    # Create Tenure Bins
    df['tenure_group'] = pd.cut(
        df['tenure'], 
        bins=[0, 12, 24, 48, 60, 100], 
        labels=['0-1yr', '1-2yr', '2-4yr', '4-5yr', '5yr+'],
        include_lowest=True
    )
    
    # Total Services Count
    service_cols = ['OnlineSecurity', 'OnlineBackup', 'DeviceProtection', 
                    'TechSupport', 'StreamingTV', 'StreamingMovies']
    df['TotalServices'] = (df[service_cols] == 'Yes').sum(axis=1)
    
    return df

def get_recommendation(probability: float, contract: str) -> str:
    """Logic-based recommendation engine for ChurnSentinel."""
    if probability > 0.7:
        if contract == 'Month-to-month':
            return "Critical Risk: High probability of exit. Immediate intervention required with 12-month contract incentive."
        return "Critical Risk: Account health failing. Deploy dedicated success agent for manual review."
    elif probability > 0.4:
        return "Moderate Risk: Behavioral signals indicate instability. Send targeted loyalty promotion."
    return "Minimal Risk: Account stable. Continue standard communication protocols."

# --- API Endpoints ---

@app.get("/")
async def root():
    return {
        "status": "online", 
        "engine": "ChurnSentinel_v1.2",
        "model_loaded": model is not None,
        "assets_mounted": os.path.exists("eda_assets")
    }

@app.get("/metrics")
async def get_metrics():
    """Returns the latest training metrics for the dashboard."""
    if not os.path.exists(METRICS_PATH):
        raise HTTPException(status_code=404, detail="Metrics file not found in /model directory.")
    
    try:
        with open(METRICS_PATH, 'r') as f:
            metrics = json.load(f)
        return metrics
    except Exception as e:
        logger.error(f"Error reading metrics: {e}")
        raise HTTPException(status_code=500, detail="Could not read metrics file.")

@app.post("/predict", response_model=PredictionResponse)
async def predict(customer: CustomerData):
    if model is None:
        raise HTTPException(status_code=500, detail="Model engine offline.")
    
    try:
        # 1. Convert input to DataFrame
        input_dict = customer.dict()
        df = pd.DataFrame([input_dict])
        
        # 2. Apply feature engineering
        df = apply_feature_engineering(df)
        
        # 3. Predict probability
        prob = model.predict_proba(df)[0][1]
        
        return {
            "churn_probability": round(float(prob), 4),
            "is_high_risk": prob > 0.5,
            "recommendation": get_recommendation(prob, customer.Contract)
        }
        
    except Exception as e:
        logger.error(f"Inference error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Launching with port 8000 to match frontend API_BASE_URL
    uvicorn.run(app, host="0.0.0.0", port=8000)