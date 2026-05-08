# Sahāyak - Predictive Climate Intelligence 🌍

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Framework-green)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-red)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Contributions](https://img.shields.io/badge/Contributions-Welcome-brightgreen)](https://github.com/Kalyan9639/IIT-Delhi-AI-Projects/pulls)

---

## 🌟 Overview

**Sahāyak** is an AI-powered climate intelligence system designed to provide real-time weather updates, air quality insights, and actionable climate safety advisories for Indian cities. It combines cutting-edge technologies like FastAPI, Streamlit, and Ollama's local LLM to deliver a seamless and interactive experience for users.

---

## 🚀 Features

- **Real-Time Weather Data**: Fetches current weather and 24-hour history using Open-Meteo API.
- **Air Quality Index (AQI)**: Retrieves real-time AQI data from WAQI API.
- **AI-Powered Advisory**: Generates climate safety advisories using Ollama's local LLM.
- **Interactive Dashboard**: Built with Streamlit for visualizing weather trends, AQI, and advisories.
- **24-Hour Climate Trajectory**: Generates temperature vs. humidity plots.
- **Location-Based Insights**: Supports geocoding for Indian PIN codes and city names.
- **Error Handling**: Graceful degradation with robust logging and fallback mechanisms.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI
- **Frontend**: Streamlit
- **AI**: Ollama LLM (local model)
- **APIs**: Open-Meteo, WAQI, Zippopotam
- **Visualization**: Matplotlib, Pandas
- **Deployment**: Uvicorn, Docker-ready

---

## 📂 Project Structure

```
Sahāyak - Predictive Climate Intelligence
│
├── app.py                # Streamlit frontend for interactive dashboard
├── main.py               # FastAPI backend for data fetching and API endpoints
├── data_engine.py        # Core data processing and API integration
├── requirements.txt      # Python dependencies
├── README.md             # Project documentation
└── wf/                   # Virtual environment folder
```

---

## 🌐 Live Demo

[Visit the Repository](https://github.com/Kalyan9639/IIT-Delhi-AI-Projects/tree/main/Python/Sah%C4%81yak%20-%20Predictive%20Climate%20Intelligence)

---

## 🖥️ How to Run

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- Ollama installed and running locally
- Internet connection

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Kalyan9639/IIT-Delhi-AI-Projects.git
   cd Python/Sahāyak - Predictive Climate Intelligence
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv wf
   source wf/bin/activate  # On Windows: wf\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start Ollama in a separate terminal:
   ```bash
   ollama serve
   ```

5. Start the backend:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

6. Start the frontend:
   ```bash
   streamlit run app.py
   ```

7. Open your browser and navigate to:
   ```
   http://localhost:8501
   ```

---

## 📊 API Endpoints

| Endpoint              | Method | Description                          |
|-----------------------|--------|--------------------------------------|
| `/`                  | GET    | Health check                         |
| `/dashboard-data`    | GET    | Returns all data for the dashboard   |
| `/weather`           | GET    | Returns weather data only            |
| `/aqi`               | GET    | Returns AQI data only                |
| `/advisory`          | GET    | Returns advisory text only           |
| `/update-location`   | POST   | Updates location and fetches data    |
| `/geocoding/{zip}`   | GET    | Resolves coordinates for a location  |

---

## 🧪 Testing

### Unit Tests

- Test weather API:
  ```bash
  python -c "from data_engine import fetch_weather_and_elevation; print(fetch_weather_and_elevation(17.385, 78.4867))"
  ```

- Test AQI API:
  ```bash
  python -c "from data_engine import fetch_aqi; print(fetch_aqi(17.385, 78.4867))"
  ```

- Test geocoding:
  ```bash
  python -c "from data_engine import get_coordinates_from_zip; print(get_coordinates_from_zip('500001'))"
  ```

### Integration Tests

- Test `/dashboard-data` endpoint:
  ```bash
  curl http://localhost:8000/dashboard-data
  ```

- Test location update:
  ```bash
  curl -X POST "http://localhost:8000/update-location?zipcode=500001"
  ```

---

## 🛡️ License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please fork this repository, make your changes, and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

---

## 📬 Contact

For any inquiries, please reach out to [Kalyan9639](https://github.com/Kalyan9639).

---

## 🌟 Acknowledgments

- **FastAPI** for the backend framework
- **Streamlit** for the interactive frontend
- **Ollama** for the local AI model
- **Open-Meteo** for weather data
- **WAQI** for air quality data
- **Zippopotam** for geocoding Indian PIN codes

---

**Star the repository if you find it useful! ⭐**