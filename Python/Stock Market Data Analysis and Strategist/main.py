from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from market_sensors import MarketSensors
from govt_and_news_sensors import GovtNewsSensors
from intelligence_engine import IntelligenceEngine
import uvicorn
import time

app = FastAPI(title="Bharat-Risk Pulse API")

# --- FIX: ADD CORS MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize our components (Now heavily focused on TCS & Tech Sector)
market_svc = MarketSensors(ticker="TCS.NS")
govt_svc = GovtNewsSensors()
intel_svc = IntelligenceEngine()

@app.get("/api/v1/health-check")
async def health():
    """Verifies API and Local SLM status."""
    return {
        "status": "online", 
        "engine": "Gemma 3 1B", 
        "focus_asset": "TCS.NS"
    }

@app.get("/api/v1/risk-profile")
async def get_risk_profile():
    """
    Standard aggregate endpoint for a full dashboard load.
    Guaranteed not to throw a 500 KeyError due to strict schemas.
    """
    try:
        m_data = market_svc.get_market_snapshot()
        g_data = govt_svc.get_govt_indicators()
        headlines = govt_svc.get_latest_headlines()
        ai_analysis = intel_svc.generate_risk_report(m_data, g_data, headlines)
        
        return {
            "summary": ai_analysis,
            "market_metrics": m_data,
            "macro_indicators": g_data,
            "recent_news": headlines,
            "timestamp": time.time()
        }
    except Exception as e:
        print(f"CRITICAL Error in risk-profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/curve")
async def get_curve_data(ticker: str = Query("TCS.NS", description="Ticker symbol for the normal distribution")):
    """
    Specific endpoint for the Normal Distribution (Bell Curve) graph.
    Defaults directly to our focused problem: TCS.NS.
    """
    try:
        m_data = market_svc.get_market_snapshot()
        if ticker not in m_data:
            # Failsafe if frontend requests an unavailable ticker
            ticker = "TCS.NS" 
            
        return {
            "ticker": ticker,
            "curve": m_data[ticker]["curve_data"],
            "is_anomaly": m_data[ticker]["is_anomaly"],
            "z_score": m_data[ticker]["z_score"]
        }
    except Exception as e:
        print(f"Error in curve-data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/intelligence/refresh")
async def refresh_a2ui():
    """
    Triggers the SLM (Gemma 3) to re-evaluate the current situation.
    """
    try:
        m_data = market_svc.get_market_snapshot()
        g_data = govt_svc.get_govt_indicators()
        headlines = govt_svc.get_latest_headlines(limit=3)
        
        ai_analysis = intel_svc.generate_risk_report(m_data, g_data, headlines)
        return ai_analysis
    except Exception as e:
        print(f"Error in refresh-a2ui: {e}")
        raise HTTPException(status_code=500, detail=f"SLM Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)