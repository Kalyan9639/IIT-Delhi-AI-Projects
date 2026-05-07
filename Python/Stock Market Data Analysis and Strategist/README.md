# BHARAT-RISK PULSE: Stock Market Data Analysis and Strategist

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![IIT Delhi](https://img.shields.io/badge/IIT%20Delhi-AI%20Projects-004687?style=for-the-badge)](https://www.iitd.ac.in/)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)](https://github.com/Kalyan9639/IIT-Delhi-AI-Projects)

---

## 📋 Overview

**Bharat-Risk Pulse** is an intelligent stock market analysis system that leverages AI-driven insights to monitor and analyze Indian tech sector dynamics, with a primary focus on **TCS (Tata Consultancy Services)** as a proxy indicator. This system integrates real-time market data, government economic indicators, and news sentiment analysis to generate actionable risk profiles and strategic recommendations.

### 🎯 Key Highlights

- **Real-time Market Monitoring**: Tracks hourly price movements and volatility using statistical Z-scores
- **Government Indicators Integration**: Incorporates CPI, IIP, and WPI data from official sources
- **News Sentiment Analysis**: Aggregates and analyzes financial news headlines
- **AI-Powered Intelligence**: Uses gpt-oss:20b-cloud language model for risk assessment
- **FastAPI Backend**: High-performance REST API for dashboard integration
- **Professional Dashboard UI**: Interactive HTML interface for data visualization

---

## 🚀 Features

### Market Sensors
- Real-time stock price tracking with intraday volatility analysis
- Statistical Z-score calculations for anomaly detection
- Probability density visualization of price movements
- Multi-period technical analysis

### Government & News Sensors
- Integration with official government economic data (MOSPI, ESANKHYIKI)
- Real-time financial news aggregation via RSS feeds
- Macro indicator monitoring (Inflation, Industrial Production, Commodity Prices)
- Sentiment-aware headline analysis

### Intelligence Engine
- Natural language processing with cloud-based LLM (gpt-oss:20b-cloud)
- Multi-modal data fusion (market + macro + news)
- Automated risk level classification
- Context-aware strategic recommendations

### REST API
- Health check endpoints for system status
- Comprehensive risk profile aggregation
- CORS-enabled for frontend integration
- Structured response schemas for reliability

---

## 📦 Prerequisites

- **Python**: 3.8 or higher
- **Ollama**: Local inference engine with Gemma 3 1B model installed
- **pip**: Python package manager

---

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Kalyan9639/IIT-Delhi-AI-Projects/Python.git
cd "Stock Market Data Analysis and Strategist"
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install & Setup Ollama

Download and install [Ollama](https://ollama.ai) from the official website, then pull the gpt-oss:20b-cloud model:

```bash
ollama pull gpt-oss:20b-cloud
```

---

## 📝 Configuration

### Environment Setup

Before running the application, ensure Ollama is running:

```bash
# Start Ollama service
ollama serve
```

### Customizing the Target Asset

The default focus is **TCS.NS**. To monitor a different stock, modify `main.py`:

```python
market_svc = MarketSensors(ticker="YOUR_TICKER_HERE")
```

---

## 🎬 Usage

### Start the API Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Access the Interactive Dashboard

Open your browser and navigate to:

```
http://localhost:8000/index.html
```

### API Endpoints

#### Health Check
```bash
GET /api/v1/health-check
```

**Response:**
```json
{
  "status": "online",
  "engine": "gpt-oss:20b-cloud",
  "focus_asset": "TCS.NS"
}
```

#### Risk Profile
```bash
GET /api/v1/risk-profile
```

**Response:**
```json
{
  "summary": {
    "analysis": "Tech sector showing resilience...",
    "action": "Maintain current positions...",
    "risk_level": "MODERATE"
  },
  "market_metrics": { ... },
  "macro_indicators": { ... },
  "recent_news": [ ... ]
}
```

---

## 📂 Project Structure

```
├── main.py                          # FastAPI application & API routes
├── market_sensors.py                # Market data collection & analysis
├── govt_and_news_sensors.py         # Government indicators & news aggregation
├── intelligence_engine.py           # AI-powered analysis & recommendations
├── index.html                       # Interactive dashboard UI
├── requirements.txt                 # Project dependencies
└── README.md                        # This file
```

### File Descriptions

| File | Purpose |
|------|---------|
| `main.py` | REST API server, route handlers, component orchestration |
| `market_sensors.py` | Real-time market data fetching, volatility calculation, Z-score analysis |
| `govt_and_news_sensors.py` | Government economic data integration, RSS feed parsing, news aggregation |
| `intelligence_engine.py` | LLM integration, multi-modal analysis, risk scoring, recommendation generation |
| `index.html` | Web-based dashboard for visualization and monitoring |
| `requirements.txt` | Python package dependencies |

---

## 📊 Key Components

### MarketSensors
Monitors stock price movements using statistical analysis:
- **Return Calculation**: Hourly percentage changes
- **Volatility**: Standard deviation of returns
- **Z-Score**: Anomaly detection for price movements
- **PDF Visualization**: Normal distribution representation

### GovtNewsSensors
Aggregates macroeconomic data and news:
- **Economic Indicators**: CPI, IIP, WPI indices
- **News Feed**: Real-time financial news from RSS feeds
- **Data Cleaning**: Normalized and standardized metrics

### IntelligenceEngine
AI-driven analysis using local LLM:
- **Risk Assessment**: Multi-factor analysis
- **Contextual Recommendations**: Action-oriented insights
- **Risk Classification**: HIGH, MODERATE, LOW levels
- **Summary Generation**: 2-line concise analysis

---

## 🔐 Technical Stack

| Component | Technology |
|-----------|-----------|
| **Backend Framework** | FastAPI 0.104+ |
| **Server** | Uvicorn |
| **Data Processing** | Pandas, NumPy, SciPy |
| **Market Data** | YFinance |
| **LLM Engine** | Ollama + gpt-oss:20b-cloud |
| **News Aggregation** | FeedParser |
| **Government Data** | MOSPI, ESANKHYIKI |
| **Frontend** | HTML5 + JavaScript |
| **API Standards** | REST, JSON |

---

## 🤖 AI Model

This project uses **gpt-oss:20b-cloud**, a powerful 20-billion parameter language model:
- **Cloud-Based Inference**: Optimized performance and reliability
- **Advanced NLP**: State-of-the-art language understanding capabilities
- **Fast Response**: Optimized for real-time analysis
- **Customizable**: Easy to switch to alternative models in the `intelligence_engine.py` file

---

## 🎓 Educational Value

This project demonstrates:
- Real-time data pipeline architecture
- Integration of multiple heterogeneous data sources
- Statistical analysis for financial applications
- AI model orchestration and prompting
- REST API design with FastAPI
- Frontend-backend communication
- Macroeconomic indicator analysis

---

## 📈 Future Enhancements

- [ ] Multi-asset portfolio analysis
- [ ] Advanced backtesting framework
- [ ] Machine learning-based risk prediction
- [ ] Real-time alert notifications
- [ ] Database integration for historical analysis
- [ ] Advanced charting and technical indicators
- [ ] User authentication and multi-tenant support
- [ ] Deployment to cloud platforms (AWS, Azure, GCP)

---

## ⚠️ Disclaimer

This tool is for **educational and research purposes only**. It should not be used as the sole basis for investment decisions. Always conduct thorough research and consult with financial advisors before making investment decisions. Past performance does not guarantee future results.

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👤 Author

**Kalyan** - IIT Delhi AI Projects
- GitHub: [Kalyan9639](https://github.com/Kalyan9639)
- Project Repository: [Stock Market Data Analysis and Strategist](https://github.com/Kalyan9639/IIT-Delhi-AI-Projects/tree/main/Python/Stock%20Market%20Data%20Analysis%20and%20Strategist)

---

## 📞 Support

For issues, questions, or suggestions, please:
- Open an [Issue](https://github.com/Kalyan9639/IIT-Delhi-AI-Projects/issues) on GitHub
- Check existing documentation and examples
- Review API response schemas for troubleshooting

---

## 🙏 Acknowledgments

- **IIT Delhi** - Academic institution providing research platform
- **FastAPI Community** - Excellent documentation and support
- **Ollama Project** - Local LLM inference technology
- **Yahoo Finance** - Market data API
- **Open Source Community** - Tools and libraries used in this project

---

**Last Updated**: May 2026 | **Status**: ✅ Active Development
