# 🛡️ Retention Radar

[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009485?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933?logo=node.js&logoColor=white)](https://nodejs.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?logo=next.js&logoColor=white)](https://nextjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-3.x-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![ML Model](https://img.shields.io/badge/ML%20Model-Random%20Forest-orange?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](README.md)

**Enterprise-grade Customer Retention Intelligence System** built for FinSolve Technologies.

Retention Radar is a high-performance machine learning system designed to predict customer churn in real-time. By combining a robust Random Forest backend with a high-fidelity Next.js dashboard, it empowers success teams to identify at-risk accounts and trigger automated retention protocols before they exit.

## 🏗️ System Architecture

The project is divided into three core pillars:

- **The Research Layer** (`eda_and_explain.py`): Performs deep statistical analysis and generates SHAP (SHapley Additive exPlanations) values to identify global churn drivers.

- **The Scoring Engine** (`main.py`): A high-throughput FastAPI service that handles feature engineering pipelines and real-time model inference.

- **The Intelligence Hub** (Next.js Dashboard): A premium "Success-Ops" interface for real-time risk assessment, tactical recommendations, and model health monitoring.

## 🚀 Key Features

- **Real-time Inference**: Sub-100ms churn probability scoring for individual customer vectors.
- **Explainable AI (XAI)**: Integrated SHAP analysis to visualize feature importance and decision-making logic.
- **Automated Feature Engineering**: On-the-fly tenure binning and service stack aggregation to maintain data consistency.
- **Risk Strategy Engine**: Generates tailored retention recommendations based on risk severity and contract types.
- **Visual EDA Suite**: Direct access to precision-recall curves, ROC performance, and population distributions within the dashboard.

## 🛠️ Tech Stack

### Backend
| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.9+ |
| **Framework** | FastAPI |
| **ML Library** | Scikit-Learn (Random Forest) |
| **Serialization** | Joblib |
| **Data Processing** | Pandas, NumPy |

### Frontend
| Component | Technology |
|-----------|-----------|
| **Framework** | Next.js 15 (App Router) |
| **Styling** | Tailwind CSS (Cyber-Noir Theme) |
| **Animation** | Framer Motion |
| **Icons** | Lucide-React |

## 📦 Installation & Setup

### Prerequisites

Ensure you have the following installed:
- Python 3.9 or higher
- Node.js 18 or higher
- npm or yarn package manager

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/Kalyan9639/IIT-Delhi-AI-Projects/tree/main/Machine%20Learning/Customer%20Churn%20Prediction.git
cd "IIT-Delhi-AI-Projects/Machine Learning/Customer Churn Prediction"

# Create a virtual environment
python -m venv cp
source cp/bin/activate  # On Windows: cp\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Train the model (generates artifacts in /model and /eda_assets)
python model_training.py
python eda.py

# Start the Scoring Engine
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd churn-dashboard

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend will be available at `http://localhost:3000` and the backend API at `http://localhost:8000`.

## 📊 Model Performance

Our current champion model is calibrated for **Maximum Recall** to ensure zero missed churn events.

| Metric | Score |
|--------|-------|
| **Accuracy** | 78.1% |
| **ROC-AUC** | 0.859 |
| **Churn Recall** | 72.4% |
| **Churn Precision** | 56.8% |

**Note**: Precision is lower due to a deliberate bias toward identifying risk (Recall), allowing for proactive success management.

## 📁 Project Structure

```
customer churn prediction/
├── main.py                 # FastAPI Backend Service
├── model_training.py       # ML Pipeline & Training Script
├── eda.py                  # SHAP & Asset Generation Script
├── requirements.txt        # Backend Dependencies
├── model/                  # Persistent Model Artifacts (.joblib, .json)
├── eda_assets/             # Visual Intelligence Assets (.png)
└── churn-dashboard/        # Next.js Frontend Project
    ├── src/app/page.js     # Main Dashboard Logic
    └── package.json        # Frontend Dependencies
```


## 🔌 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Check API health status |
| `GET` | `/metrics` | Retrieve model performance metrics |
| `POST` | `/predict` | Get churn prediction for a customer |

### Example Request

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "tenure": 12,
    "MonthlyCharges": 65.5,
    "TotalCharges": 786.0,
    "Contract": "Month-to-month",
    "InternetService": "Fiber optic"
  }'
```

## 🤝 Contributing

We welcome contributions! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## ❓ Troubleshooting

### Backend Issues

- **Port 8000 already in use**: Change the port with `uvicorn main:app --reload --port 8001`
- **Model not found**: Run `python model_training.py` to train the model first
- **CORS errors**: Ensure the frontend URL is properly configured in the API

### Frontend Issues

- **Port 3000 already in use**: Change the port with `npm run dev -- -p 3001`
- **API connection refused**: Verify the backend is running at `http://localhost:8000`
- **Styling issues**: Clear Next.js cache with `rm -rf .next` and restart

## Support

For issues, feature requests, or questions:
- Create an [Issue](https://github.com/Kalyan9639/IIT-Delhi-AI-Projects/Machine%20Learning/Customer%20Churn%20Prediction/issues)
- Documentation: [Full API Docs](http://localhost:8000/docs)



Distributed under the **MIT License**.

---

**Developed with ❤️ by the FinSolve Technologies Intelligence Team**
