"""
Configuration module for Bangalore Real Estate Intelligence System.
Contains all configuration parameters, paths, and settings.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data paths
DATA_DIR = BASE_DIR / 'data'
RAW_DATA_PATH = BASE_DIR / 'Bengaluru_House_Data.csv'
PROCESSED_DATA_PATH = DATA_DIR / 'processed_data.csv'
FEATURED_DATA_PATH = DATA_DIR / 'featured_data.csv'

# Model paths
MODEL_DIR = BASE_DIR / 'models'
MODEL_PATH = MODEL_DIR / 'best_model.pkl'
PREPROCESSOR_PATH = MODEL_DIR / 'preprocessor.pkl'
ANOMALY_MODEL_PATH = MODEL_DIR / 'anomaly_detector.pkl'
INVESTMENT_SCORER_PATH = MODEL_DIR / 'investment_scorer.pkl'

# Logging configuration
LOG_DIR = BASE_DIR / 'logs'
LOG_FILE = LOG_DIR / 'app.log'

# Streamlit app path
STREAMLIT_APP_PATH = BASE_DIR / 'streamlit_app' / 'main.py'

# Feature configuration
FEATURE_CONFIG = {
    'price_per_sqft': True,
    'bhk_extraction': True,
    'total_rooms': True,
    'luxury_indicators': True,
    'area_density': True,
    'locality_frequency': True,
    'locality_popularity': True,
    'property_segmentation': True,
    'premium_area': True,
    'affordability_metrics': True
}

# Model configuration
MODEL_CONFIG = {
    'models_to_try': ['linear', 'random_forest', 'xgboost', 'lightgbm', 'catboost'],
    'hyperparameter_tuning': 'randomized',
    'cv_folds': 5,
    'test_size': 0.2,
    'random_state': 42
}

# Anomaly detection configuration
ANOMALY_CONFIG = {
    'method': 'isolation_forest',
    'contamination': 0.05,
    'random_state': 42
}

# Heatmap configuration
HEATMAP_CONFIG = {
    'zoom_level': 12,
    'cluster_radius': 50,
    'gradient': {
        0.4: 'blue',
        0.6: 'cyan',
        0.7: 'lime',
        0.8: 'yellow',
        1.0: 'red'
    }
}

# Investment scoring configuration
INVESTMENT_CONFIG = {
    'weight_demand': 0.25,
    'weight_pricing': 0.20,
    'weight_consistency': 0.15,
    'weight_popularity': 0.15,
    'weight_affordability': 0.15,
    'weight_premium': 0.10
}

# Create directories if they don't exist
for directory in [DATA_DIR, MODEL_DIR, LOG_DIR, STREAMLIT_APP_PATH.parent]:
    directory.mkdir(parents=True, exist_ok=True)
