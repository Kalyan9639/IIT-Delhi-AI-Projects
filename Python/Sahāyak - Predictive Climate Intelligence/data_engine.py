import requests
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # CRITICAL: Prevents server crashes when generating plots in the background
import matplotlib.pyplot as plt
import io
import base64
import math
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
WAQI_API_TOKEN = "30c0c4c323048a276c918cbfbf543135543619a1" 
DEFAULT_CITY = "Hyderabad"
DEFAULT_LAT = 17.3850
DEFAULT_LON = 78.4867

REQUEST_TIMEOUT = 10  # seconds

def get_coordinates_from_zip(zipcode):
    """Converts a PIN code or City to Latitude and Longitude."""
    try:
        # Check if input is a 6-digit Indian PIN code
        if zipcode.isdigit() and len(zipcode) == 6:
            url = f"https://api.zippopotam.us/IN/{zipcode}"
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                if data.get('places'):
                    place = data['places'][0]
                    return {
                        "lat": float(place['latitude']),
                        "lon": float(place['longitude']),
                        "name": place['place name'],
                        "admin": place['state']
                    }
        
        # Fallback to Open-Meteo Geocoding
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={zipcode}&count=1&language=en&format=json"
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200 and response.json().get('results'):
            result = response.json()['results'][0]
            return {
                "lat": result['latitude'],
                "lon": result['longitude'],
                "name": result.get('name', 'Unknown'),
                "admin": result.get('admin1', 'Unknown')
            }
        return None
    except Exception as e:
        logger.error(f"Error fetching coordinates for {zipcode}: {e}")
        return None

def calculate_wet_bulb(temp, rh):
    """Stull Formula for Wet Bulb Temperature calculation safely."""
    try:
        if temp is None or rh is None:
            return 0.0
        temp = float(temp)
        rh = max(0.0, min(100.0, float(rh))) # Ensure RH is between 0 and 100
        tw = temp * math.atan(0.151977 * (rh + 8.313659)**0.5) + \
             math.atan(temp + rh) - math.atan(rh - 1.676331) + \
             0.00391838 * (rh**1.5) * math.atan(0.023101 * rh) - 4.686035
        return round(tw, 2)
    except Exception as e:
        logger.error(f"Math error in WBT calc: {e}")
        return float(temp)

def fetch_weather_and_elevation(lat, lon):
    """Pulls current weather, 24h history, and extracts elevation from the response."""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        
        # PARAMETERS CONFIGURED STRICTLY TO API DOCS
        params = {
            "latitude": lat,                                            # Floating point
            "longitude": lon,                                           # Floating point
            "current": "temperature_2m,relative_humidity_2m,precipitation", # String array
            "hourly": "temperature_2m,relative_humidity_2m",            # String array
            "past_days": 1,                                             # Integer
            "forecast_days": 1,                                         # Integer
            "timezone": "auto"                                          # String
            # NOTE: 'elevation' parameter omitted entirely to avoid 400 Error.
            # The API will return the default 90m digital elevation model in the JSON response.
        }
        
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        
        # Robust Error Logging
        if response.status_code != 200:
            logger.error(f"Open-Meteo API Error [{response.status_code}]: {response.text}")
            
        response.raise_for_status() 
        data = response.json()
        
        # Safely extract current metrics
        curr = data.get('current', {})
        curr_temp = curr.get('temperature_2m', 0.0)
        curr_rh = curr.get('relative_humidity_2m', 0.0)
        curr_precip = curr.get('precipitation', 0.0)
        
        wbt = calculate_wet_bulb(curr_temp, curr_rh)
        
        weather_data = {
            "current": {
                "temperature": curr_temp,
                "precipitation": curr_precip,
                "time": curr.get('time', '')
            },
            "wbt": wbt,
            "elevation": data.get('elevation', 0), # Extracting the default elevation returned by the API
            "hourly": data.get('hourly', {}),
            "unit": data.get('hourly_units', {})
        }
        return weather_data
        
    except Exception as e:
        logger.error(f"Error fetching weather for ({lat}, {lon}): {e}")
        return None

def fetch_aqi(lat, lon):
    """Fetches real-time AQI from WAQI (AQICN)."""
    try:
        url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_API_TOKEN}"
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        data = response.json()
        
        if data.get('status') == 'ok' and data.get('data'):
            return {
                "aqi": data['data'].get('aqi', 'N/A'),
                "station": data['data'].get('city', {}).get('name', 'Unknown')
            }
        return {"aqi": "N/A", "station": "Unknown"}
    except Exception as e:
        return {"aqi": "N/A", "station": "Unknown"}

def generate_24h_plot(hourly_data):
    """Generates a base64 encoded plot."""
    try:
        if not hourly_data:
            return None
            
        df = pd.DataFrame({
            'time': pd.to_datetime(hourly_data.get('time', [])),
            'temp': hourly_data.get('temperature_2m', []),
            'humidity': hourly_data.get('relative_humidity_2m', [])
        })
        
        df = df.tail(24)
        if len(df) == 0:
            return None
        
        plt.figure(figsize=(10, 5))
        plt.style.use('seaborn-v0_8-darkgrid')
        
        ax1 = plt.gca()
        ax2 = ax1.twinx()
        
        ax1.plot(df['time'], df['temp'], color='tab:red', label='Temp (°C)', linewidth=2)
        ax2.plot(df['time'], df['humidity'], color='tab:blue', label='Humidity (%)', linestyle='--')
        
        ax1.set_xlabel('Time (Last 24 hrs)')
        ax1.set_ylabel('Temperature (°C)', color='tab:red')
        ax2.set_ylabel('Relative Humidity (%)', color='tab:blue')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        return img_str
    except Exception as e:
        logger.error(f"Error generating plot: {e}")
        return None