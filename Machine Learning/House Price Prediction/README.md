# 🏠 Bangalore Real Estate Intelligence System

A comprehensive, production-grade AI-powered real estate intelligence platform for Bangalore property price prediction, investment analysis, and anomaly detection.

## 🚀 Features

### Core Features
- **House Price Prediction**: AI-powered price estimation using multiple machine learning models (Linear Regression, Random Forest, XGBoost, LightGBM, CatBoost)
- **Location-Based Valuation**: Detailed analytics for different Bangalore locations
- **Feature Importance Analysis**: SHAP-based explainability for model predictions, providing both global and local insights

### Advanced Features
- **Price Heatmaps**: Interactive Folium-based visualizations of price distribution and concentration across Bangalore
- **Area-Wise Investment Scoring**: Data-driven investment recommendations based on demand, pricing, consistency, and affordability
- **Fraud/Anomaly Detection**: Multi-method detection (Isolation Forest, Local Outlier Factor) of overpriced, underpriced, and suspicious listings

## 📋 Project Structure

```
House Price Prediction/
├── src/
│   ├── __init__.py              # Package initialization
│   ├── config.py                # Configuration settings
│   ├── logging_utils.py         # Logging utilities
│   ├── preprocessing.py         # Data preprocessing pipeline
│   ├── feature_engineering.py   # Advanced feature engineering
│   ├── anomaly_detection.py     # Anomaly detection module
│   ├── investment_scoring.py    # Investment scoring system
│   ├── heatmap_generator.py     # Interactive heatmap generation
│   ├── model_training.py        # Model training pipeline
│   └── explainability.py        # SHAP explainability
├── streamlit_app/
│   └── main.py                  # Main Streamlit application
├── models/                      # Trained models and artifacts
├── data/                        # Processed data
├── logs/                        # Application logs
├── train_pipeline.py            # Main training script
├── Bengaluru_House_Data.csv     # Original dataset
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

## 🛠️ Technologies Used

### Machine Learning
- **XGBoost**: Gradient boosting regressor
- **LightGBM**: Fast gradient boosting
- **CatBoost**: Categorical feature handling
- **Random Forest**: Ensemble learning
- **Linear Regression**: Baseline model

### Explainability
- **SHAP**: SHapley Additive exPlanations for model interpretability

### Visualization
- **Plotly**: Interactive charts and dashboards
- **Folium**: Interactive maps and heatmaps
- **Streamlit**: Web application framework

### Data Processing
- **Pandas**: Data manipulation
- **NumPy**: Numerical computing
- **Scikit-learn**: Machine learning utilities

## 📊 Dataset

The system uses the Bengaluru House Price Dataset from Kaggle (99acres dataset) containing:
- **13,320 property listings**
- **9 features**: area_type, availability, location, size, society, total_sqft, bath, balcony, price
- **Multiple area types**: Super built-up, Built-up, Plot, Carpet
- **High-cardinality locations**: 1,300+ unique locations

## 🚀 Quick Start

### Installation

1. Clone the repository:
```bash
cd "e:\Jupyter Notebook\IIT Delhi AI Projects\Machine Learning\House Price Prediction"
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Activate virtual environment (if using):
```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

### Running the Pipeline

Train the models and generate all artifacts:
```bash
python train_pipeline.py
```

This will:
- Load and preprocess the data
- Create advanced features
- Run anomaly detection
- Calculate investment scores
- Train multiple models
- Generate heatmaps
- Save all artifacts

### Running the Streamlit Application

Start the web application:
```bash
streamlit run streamlit_app/main.py
```

The application will be available at `http://localhost:8501`

## 📖 Usage Guide

### Dashboard
- View key metrics and statistics
- Explore price distributions
- Check BHK and area type distributions

### House Price Prediction
- Enter property details (BHK, area, location, etc.)
- Get AI-powered price estimates
- View prediction insights

### Location Analytics
- Analyze specific locations
- View price distributions
- Explore BHK and bathroom distributions

### Feature Importance
- View global feature importance
- SHAP-based explanations
- Top contributing features

### Investment Insights
- View investment scores by location
- Identify top investment areas
- Analyze risk categories

### Fraud Detection
- View detected anomalies
- Filter by anomaly type
- Analyze suspicious listings

### Price Heatmaps
- Interactive price heatmaps
- Investment opportunity maps
- Price concentration maps

### Model Performance
- Compare model metrics
- View feature importance
- Cross-validation results

## 🔧 Configuration

Edit `src/config.py` to customize:
- Model training parameters
- Anomaly detection settings
- Heatmap configurations
- Investment scoring weights
- Feature engineering options

## 📈 Model Performance

The system trains and compares multiple models:
- **Linear Regression**: Baseline performance
- **Random Forest**: Ensemble learning
- **XGBoost**: Gradient boosting
- **LightGBM**: Fast gradient boosting
- **CatBoost**: Categorical feature handling

Best model is automatically selected based on R² score.

## 🎯 Key Features

### Data Preprocessing
- Missing value imputation
- Duplicate detection and removal
- Square footage cleaning (handles ranges, units)
- BHK extraction
- Outlier detection and removal

### Feature Engineering
- Price per square foot
- BHK categories
- Total rooms calculation
- Luxury indicators
- Area density features
- Locality frequency encoding
- Investment scoring
- Time-based features

### Anomaly Detection
- Isolation Forest
- Local Outlier Factor
- Overpriced property detection
- Underpriced property detection
- Suspicious listing detection

### Investment Scoring
- Area-wise investment scores
- Risk assessment
- Affordability index
- Price appreciation potential
- Composite investment score

## 📝 License

This project is for educational and demonstration purposes.

## 👥 Team

- **AI Engineer**: Model development and pipeline
- **Data Scientist**: Feature engineering and analysis
- **ML Architect**: System design and architecture

## 🙏 Acknowledgments

- Dataset source: Kaggle (99acres)
- Libraries: Scikit-learn, XGBoost, LightGBM, CatBoost, SHAP, Plotly, Streamlit

## 📞 Support

For questions or support, please contact the development team.

---

**Built with ❤️ by AI Engineering Team**
