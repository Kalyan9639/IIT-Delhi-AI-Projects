# Sentinel-ML Fraud Engine 🛡️

Sentinel-ML is a high-performance, end-to-end machine learning system designed to detect fraudulent credit card transactions. Built with a focus on **explainability**, **low latency**, and **real-time pattern analysis**, it provides a comprehensive suite for fraud investigators and data scientists.

## 🚀 Overview

The system addresses the "Needle in a Haystack" problem inherent in fraud detection. Sentinel-ML uses advanced sampling techniques and gradient-boosted trees to maintain high recall, ensuring that fraudulent activity is identified instantly while minimizing false positives.

## 🛠️ Tech Stack

- **Frontend:** [Next.js 14](https://nextjs.org/), [Tailwind CSS](https://tailwindcss.com/), [Lucide React](https://lucide.dev/), [Framer Motion](https://www.framer.com/motion/), [Recharts](https://recharts.org/)
- **Backend:** [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/)
- **Machine Learning:** XGBoost, Scikit-Learn, Joblib, SHAP, Pandas, NumPy
- **Styling:** Premium Dark Mode UI with Glassmorphism and Dynamic Scanning Animations

## 🌟 Key Features

- **Real-time Scoring:** API endpoints for single transaction inference using a JSON-based manual entry engine.
- **Batch Processing:** Upload large CSV datasets for bulk analysis with real-time hourly trend calculations.
- **Advanced Scanning Animation:** Visual "Radar Scan" feedback during data processing to simulate deep pattern analysis.
- **Multi-Tab Dashboard:**
    - **Overview:** Executive summaries, real-time hourly trends, and top fraud alerts.
    - **Alert Engine:** Manual prediction tool for testing individual transaction records.
    - **Analytics:** Comprehensive gallery of EDA (Exploratory Data Analysis) charts.
    - **Configurations:** Dynamic probability thresholding and dataset schema requirements.
- **Explainable AI (XAI):** Visual representation of feature importance driving model decisions.

## 📂 Project Structure

```text
├── backend/            # FastAPI application
│   ├── model/          # Serialized model, scaler, and features (.joblib)
│   └── main.py         # API endpoints and logic
├── frontend/           # Next.js 14 Dashboard
│   └── src/app/        # Dashboard UI, Components, and Logic
├── eda_and_train.py    # ML Training pipeline & EDA generation
├── prd.md              # Product Requirements Document
└── GUIDE.md            # Detailed User Guide
```

## ⚙️ Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

### 1. Backend Setup
```bash
cd backend
pip install -r ../requirements.txt
uvicorn main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The dashboard will be available at `http://localhost:3000`.

## 📈 Model Performance
The model is optimized for **Recall** to ensure maximum fraud capture.
- **Target Recall:** > 85%
- **Target Precision:** > 40%
- **Avg. Latency:** < 100ms
- **Coverage:** Trained on 48 hours of transaction data (Kaggle Credit Card Fraud Dataset).

---
Developed with ❤️ for Advanced Fraud Analytics.
