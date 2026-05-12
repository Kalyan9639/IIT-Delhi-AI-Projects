# 📈 Retail Sales Forecasting and Inventory Optimization

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=for-the-badge&logo=streamlit)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-ML-F7B6D2?style=for-the-badge&logo=scikit-learn)
![Pandas](https://img.shields.io/badge/Pandas-Data-150458?style=for-the-badge&logo=pandas)


## 🌟 Overview
This project implements an end-to-end pipeline for **Retail Sales Forecasting** and **Inventory Optimization**. By leveraging machine learning, the system predicts future demand to optimize stock levels, reducing both overstock and stockout risks.

The core of the project is a data-driven approach that transforms historical sales data into actionable inventory insights, presented through an interactive Streamlit dashboard.

## 🚀 Key Features
- **Demand Forecasting**: Uses a `RandomForestRegressor` to predict future sales based on historical trends and engineered features.
- **Inventory Optimization**: Calculates optimal safety stock and reorder points to maintain a balance between service levels and holding costs.
- **Interactive Dashboard**: A professional Streamlit UI to visualize forecasts, track inventory metrics, and analyze model performance.
- **Automated Pipeline**: Integrated data loading, cleaning, feature engineering, and evaluation.

## 🛠️ Tech Stack
- **Language**: Python
- **Libraries**: 
  - `Pandas` & `NumPy` (Data Manipulation)
  - `Scikit-Learn` (Machine Learning)
  - `Plotly` (Interactive Visualizations)
  - `Streamlit` (Frontend Dashboard)
- **Environment**: Virtualenv / Conda

## 📂 Project Structure
```bash
├── data_loader.py       # Data ingestion and preprocessing
├── model.py             # ML model architecture and training
├── inventory.py         # Inventory optimization logic
├── evaluate.py          # Model performance metrics (MAPE, RMSE)
├── dashboard.py         # Streamlit interactive UI
├── main.py              # Pipeline orchestration
├── config.py            # Project configurations
└── demand_forecasting.csv # Dataset
```

## ⚙️ Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Kalyan9639/IIT-Delhi-AI-Projects.git
   cd "Data Science - Retail Sales Forecasting and Inventory Optimization"
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   # Activate on Windows:
   .\venv\Scripts\activate
   # Activate on Mac/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   ```bash
   streamlit run dashboard.py
   ```

## 📊 How it Works
1. **Data Loading**: The system reads historical sales from `demand_forecasting.csv`.
2. **Feature Engineering**: Lag features and rolling averages are created to capture seasonality and trends.
3. **Forecasting**: The model predicts demand for the next period.
4. **Optimization**: Based on the forecast and a target service level, the system recommends the ideal inventory level.

## 📈 Results & Evaluation
The model is evaluated using metrics such as **Mean Absolute Percentage Error (MAPE)** and **Root Mean Squared Error (RMSE)** to ensure high forecasting accuracy.

## 🤝 Contributing
Contributions are welcome! Please fork the repository and create a pull request.

---
**Developed as part of the IIT Delhi AI Projects series.**
