from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import ollama
import logging
from data_engine import (
    get_coordinates_from_zip, 
    fetch_weather_and_elevation, 
    fetch_aqi, 
    generate_24h_plot,
    DEFAULT_LAT,
    DEFAULT_LON
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sahāyak API", description="Edge-AI Climate Resilience Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

latest_data = {
    "location": {"lat": DEFAULT_LAT, "lon": DEFAULT_LON, "name": "Hyderabad"},
    "weather": None,
    "aqi": {"aqi": "N/A"},
    "advisory": "System Initializing...",
    "plot_base64": None
}

async def trigger_data_update(coords):
    """Core function to fetch data and run Ollama."""
    weather_data = fetch_weather_and_elevation(coords["lat"], coords["lon"])
    aqi_data = fetch_aqi(coords["lat"], coords["lon"])
    
    # Decouple failures: Update whatever succeeds
    if weather_data:
        latest_data["weather"] = weather_data
        latest_data["plot_base64"] = generate_24h_plot(weather_data["hourly"])
    if aqi_data:
        latest_data["aqi"] = aqi_data

    if weather_data:
        try:
            current_temp = weather_data['current']['temperature']
            wbt = weather_data['wbt']
            aqi_val = latest_data["aqi"].get("aqi", "N/A")
            
            prompt = (
                f"Location: {coords['name']}. Conditions: Temp {current_temp}°C, "
                f"Wet Bulb {wbt}°C, AQI {aqi_val}. "
                "Provide a brief, 3-sentence non-authoritative advisory for local residents."
            )
            
            response = ollama.chat(
                model='gpt-oss:20b-cloud',
                messages=[
                    {'role': 'system', 'content': 'You are Sahāyak, a helpful, scientific climate safety advisor for India.'},
                    {'role': 'user', 'content': prompt},
                ]
            )
            latest_data["advisory"] = response['message']['content']
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            latest_data["advisory"] = "AI Advisory generation temporarily unavailable."

async def background_loop():
    while True:
        await asyncio.sleep(1800) # Update every 30 mins
        await trigger_data_update(latest_data["location"])

@app.on_event("startup")
async def startup_event():
    await trigger_data_update(latest_data["location"])
    asyncio.create_task(background_loop())

@app.get("/")
def read_root(): return {"status": "Online"}

@app.get("/geocoding/{zipcode}")
def resolve_zip(zipcode: str): return get_coordinates_from_zip(zipcode)

@app.post("/update-location")
async def update_location(zipcode: str):
    coords = get_coordinates_from_zip(zipcode)
    if not coords:
        raise HTTPException(status_code=404, detail="Location not found")
        
    latest_data["location"] = coords
    latest_data["advisory"] = "Analyzing location parameters... (Waiting for AI)"
    
    # Fetch data synchronously so the UI sees it immediately
    await trigger_data_update(coords)
    return {"status": "success"}

@app.get("/dashboard-data")
def get_dashboard(): return latest_data