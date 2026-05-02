from fastapi import FastAPI, UploadFile, File, HTTPException
import os
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
import io
import shap
from typing import List, Dict

app = FastAPI(title="Sentinel-ML Fraud Engine API")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model, scaler, and features
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model', 'model.joblib')
SCALER_PATH = os.path.join(BASE_DIR, 'model', 'scaler.joblib')
FEATURES_PATH = os.path.join(BASE_DIR, 'model', 'features.joblib')

try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    feature_names = joblib.load(FEATURES_PATH)
    explainer = shap.TreeExplainer(model)
except Exception as e:
    print(f"Error loading model files: {e}")
    model = None

class Transaction(BaseModel):
    Time: float
    V1: float
    V2: float
    V3: float
    V4: float
    V5: float
    V6: float
    V7: float
    V8: float
    V9: float
    V10: float
    V11: float
    V12: float
    V13: float
    V14: float
    V15: float
    V16: float
    V17: float
    V18: float
    V19: float
    V20: float
    V21: float
    V22: float
    V23: float
    V24: float
    V25: float
    V26: float
    V27: float
    V28: float
    Amount: float

@app.get("/")
def read_root():
    return {"message": "Sentinel-ML API is running"}

@app.post("/score/streaming")
async def score_streaming(tx: Transaction):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    # Preprocess
    tx_dict = tx.dict()
    # Feature engineering: hour
    hour = (tx_dict['Time'] // 3600) % 24
    
    # Scale Amount
    amount_scaled = scaler.transform([[tx_dict['Amount']]])[0][0]
    
    # Prepare input vector (must match feature_names order)
    input_data = []
    for col in feature_names:
        if col == 'hour':
            input_data.append(hour)
        elif col == 'Amount':
            input_data.append(amount_scaled)
        else:
            input_data.append(tx_dict[col])
            
    input_array = np.array([input_data])
    
    # Predict
    prob = float(model.predict_proba(input_array)[0][1])
    is_fraud = prob > 0.5 # Default threshold
    
    return {
        "probability": prob,
        "is_fraud": is_fraud,
        "status": "flagged" if is_fraud else "safe"
    }

@app.post("/score/batch")
async def score_batch(file: UploadFile = File(...), threshold: float = 0.5):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded. Check server logs.")
    
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Validation: Check for required columns for preprocessing
        if 'Time' not in df.columns or 'Amount' not in df.columns:
            raise HTTPException(
                status_code=400, 
                detail="CSV must contain 'Time' and 'Amount' columns."
            )
        
        # Preprocess
        df['hour'] = (df['Time'] // 3600) % 24
        df['Amount'] = scaler.transform(df[['Amount']])
        
        # Ensure all model features are present
        missing_cols = [col for col in feature_names if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(missing_cols)}"
            )
        
        X = df[feature_names]
        probs = model.predict_proba(X)[:, 1]
        
        df['fraud_probability'] = probs
        df['is_fraud'] = (probs > threshold).astype(int)
        
        total_tx = len(df)
        fraud_flags = int(df['is_fraud'].sum())
        
        # Get top 50 frauds for alert feed
        alerts_df = df[df['is_fraud'] == 1].sort_values(by='fraud_probability', ascending=False).head(50)
        
        alert_list = []
        for idx, row in alerts_df.iterrows():
            # unscale amount for display
            original_amount = scaler.inverse_transform([[row['Amount']]])[0][0]
            alert_list.append({
                "id": f"TX-{idx}",
                "amount": f"${original_amount:,.2f}",
                "probability": float(row['fraud_probability']),
                "status": "High" if row['fraud_probability'] > 0.9 else "Medium",
                "time": "Just now"
            })
            
        # Calculate hourly trends
        df['hour_raw'] = (df['Time'] // 3600) % 24
        hourly_counts = df.groupby('hour_raw').size().reset_index(name='volume')
        hourly_fraud = df[df['is_fraud'] == 1].groupby('hour_raw').size().reset_index(name='fraud')
        
        # Merge and fill missing hours
        trends_df = pd.merge(
            pd.DataFrame({'hour_raw': range(24)}),
            hourly_counts, on='hour_raw', how='left'
        ).merge(hourly_fraud, on='hour_raw', how='left').fillna(0)
        
        trend_list = []
        for _, row in trends_df.iterrows():
            trend_list.append({
                "time": f"{int(row['hour_raw']):02d}:00",
                "volume": int(row['volume']),
                "fraud": int(row['fraud'])
            })
            
        return {
            "summary": {
                "total_transactions": total_tx,
                "fraud_flags": fraud_flags
            },
            "alerts": alert_list,
            "trends": trend_list
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        print(f"Batch processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/explain/{transaction_index}")
async def explain(transaction_index: int):
    # This is a simplified version. Ideally, you'd pass the transaction data.
    # For demo, we'll just say we need the data to explain.
    return {"message": "SHAP explanation logic here"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
