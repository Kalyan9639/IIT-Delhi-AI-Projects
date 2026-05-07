import feedparser
import esankhyiki
import requests

class GovtNewsSensors:
    """
    Focused strictly on the IT vs Energy problem.
    Guarantees a consistent dictionary schema to prevent KeyErrors.
    """
    def __init__(self):
        # ALTERNATIVE FIX: Switched to Google News India (Business segment).
        # Google RSS aggregates from ET, Mint, etc., but rarely blocks Python scripts.
        self.news_url = "https://news.google.com/rss/headlines/section/topic/BUSINESS?ned=in&hl=en-IN"

    def get_govt_indicators(self):
        """
        Fetches CPI, WPI (Fuel), and IIP (Tech). 
        Includes a strict fallback schema to prevent 500 Server Errors.
        """
        # Strict Fallback Schema (Guarantees the app won't crash if MOSPI is down)
        default_data = {
            "cpi_inflation": 5.1,
            "wpi_fuel_index": 150.2,
            "iip_tech_growth": -2.1,
            "status": "Fallback/Mocked"
        }

        try:
            # In a real scenario, this tries to fetch live data.
            # If esankhyiki fails or isn't installed properly, it jumps to except.
            cpi_data = esankhyiki.get_data("CPI", {"base_year": 2012, "series": "Urban"}) 
            wpi_fuel = esankhyiki.get_data("WPI", {"base_year": 2012, "series": "Fuel & Power"})
            iip_electronics = esankhyiki.get_data("IIP", {"base_year": 2012, "series": "Computer & Electronics"})
            
            return {
                "cpi_inflation": cpi_data.get('latest_val', default_data["cpi_inflation"]),
                "wpi_fuel_index": wpi_fuel.get('latest_val', default_data["wpi_fuel_index"]),
                "iip_tech_growth": iip_electronics.get('yoy_growth', default_data["iip_tech_growth"]),
                "status": "Live"
            }
        except Exception as e:
            print(f"MOSPI Sensor Error: {e}. Using Fallback Schema.")
            return default_data

    def get_latest_headlines(self, limit=3):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            response = requests.get(self.news_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            headlines = [{"title": e.title, "link": e.link} for e in feed.entries[:limit]]
            
            return headlines
        except Exception as e:
            print(f"Headlines Fetch Error: {e}")
            # FIXED: Returning 3 fallback items instead of 1
            return [
                {"title": "Network Error: Unable to fetch live news.", "link": "#"},
                {"title": "System falling back to default risk assessment.", "link": "#"},
                {"title": "Check firewall settings for RSS feed access.", "link": "#"}
            ]