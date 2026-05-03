"""
Bangalore Real Estate Intelligence System - Main Execution Script.
This script orchestrates the complete AI-powered real estate analysis pipeline.
"""

import pandas as pd
import numpy as np
import pickle
import warnings
warnings.filterwarnings('ignore')

# Import custom modules
from .config import (
    RAW_DATA_PATH, PROCESSED_DATA_PATH, FEATURED_DATA_PATH,
    MODEL_PATH, PREPROCESSOR_PATH, ANOMALY_MODEL_PATH, INVESTMENT_SCORER_PATH,
    MODEL_CONFIG, ANOMALY_CONFIG
)
from .preprocessing import DataPreprocessor
from .feature_engineering import FeatureEngineer
from .anomaly_detection import AnomalyDetector
from .investment_scoring import InvestmentScorer
from .heatmap_generator import HeatmapGenerator
from .model_training import ModelTrainer
from .explainability import ExplainabilityAnalyzer
from .logging_utils import log_info, log_error, log_warning


def load_data():
    """Load the raw dataset."""
    log_info('main', 'Loading raw data')
    
    try:
        df = pd.read_csv(RAW_DATA_PATH)
        log_info('main', f'Data loaded successfully. Shape: {df.shape}')
        return df
    except Exception as e:
        log_error('main', f'Error loading data: {str(e)}')
        raise


def run_preprocessing(df):
    """Run the preprocessing pipeline."""
    log_info('main', 'Starting preprocessing pipeline')
    
    preprocessor = DataPreprocessor(random_state=42)
    
    # Preprocess data
    df_processed = preprocessor.preprocess(df, remove_outliers=True, encode=True, scale=True)
    
    # Save preprocessor
    preprocessor.save_preprocessor(PREPROCESSOR_PATH)
    
    # Save processed data
    df_processed.to_csv(PROCESSED_DATA_PATH, index=False)
    
    log_info('main', f'Preprocessing complete. Processed data shape: {df_processed.shape}')
    
    return df_processed, preprocessor


def run_feature_engineering(df):
    """Run the feature engineering pipeline."""
    log_info('main', 'Starting feature engineering pipeline')
    
    engineer = FeatureEngineer()
    
    # Create all features
    df_featured = engineer.create_all_features(df)
    
    # Get feature importance
    feature_importance = engineer.get_feature_importance(df_featured)
    
    # Save featured data
    df_featured.to_csv(FEATURED_DATA_PATH, index=False)
    
    log_info('main', f'Feature engineering complete. Featured data shape: {df_featured.shape}')
    log_info('main', f'Top features: {list(feature_importance.keys())[:5]}')
    
    return df_featured, engineer


def run_anomaly_detection(df):
    """Run the anomaly detection pipeline."""
    log_info('main', 'Starting anomaly detection pipeline')
    
    detector = AnomalyDetector(
        method=ANOMALY_CONFIG['method'],
        contamination=ANOMALY_CONFIG['contamination'],
        random_state=ANOMALY_CONFIG['random_state']
    )
    
    # Detect all anomalies
    df_anomalies = detector.detect_all_anomalies(df)
    
    # Get anomaly summary
    anomaly_summary = detector.get_anomaly_summary(df_anomalies)
    
    # Save anomaly detector
    detector.save_model(ANOMALY_MODEL_PATH)
    
    log_info('main', f'Anomaly detection complete. Summary: {anomaly_summary}')
    
    return df_anomalies, detector, anomaly_summary


def run_investment_scoring(df):
    """Run the investment scoring pipeline."""
    log_info('main', 'Starting investment scoring pipeline')
    
    scorer = InvestmentScorer()
    
    # Calculate investment scores
    df_investment = scorer.calculate_investment_score(df)
    df_investment = scorer.calculate_area_popularity(df_investment)
    df_investment = scorer.create_area_recommendations(df_investment)
    df_investment = scorer.calculate_price_appreciation_potential(df_investment)
    df_investment = scorer.create_affordability_index(df_investment)
    df_investment = scorer.create_risk_score(df_investment)
    df_investment = scorer.create_composite_score(df_investment)
    
    # Get investment summary
    investment_summary = scorer.get_investment_summary(df_investment)
    
    # Save investment scorer
    scorer.save_model(INVESTMENT_SCORER_PATH)
    
    log_info('main', f'Investment scoring complete. Summary: {investment_summary}')
    
    return df_investment, scorer, investment_summary


def run_model_training(df):
    """Run the model training pipeline."""
    log_info('main', 'Starting model training pipeline')
    
    trainer = ModelTrainer(random_state=42)
    
    # Prepare data
    X_train, X_test, y_train, y_test = trainer.prepare_data(df, target_column='price')
    
    # Train all models
    trainer.train_all_models(X_train, X_test, y_train, y_test)
    
    # Select best model
    trainer.select_best_model()
    
    # Save best model
    trainer.save_model(MODEL_PATH)
    
    log_info('main', f'Model training complete. Best model: {trainer.best_model_name}')
    log_info('main', f'Best model score: {trainer.best_score:.4f}')
    
    return trainer


def run_explainability(df, trainer):
    """Run the explainability analysis."""
    log_info('main', 'Starting explainability analysis')
    
    analyzer = ExplainabilityAnalyzer()
    
    # Create explainer
    X_train, X_test, y_train, y_test = trainer.prepare_data(df, target_column='price')
    analyzer.create_explainer(trainer.best_model, X_train[:100])
    
    # Calculate SHAP values
    analyzer.calculate_shap_values(X_test, trainer.best_model)
    
    # Get feature importance
    global_importance = analyzer.get_global_feature_importance()
    
    log_info('main', f'Explainability analysis complete. Top features: {list(global_importance.keys())[:5]}')
    
    return analyzer, global_importance


def run_heatmap_generation(df):
    """Run the heatmap generation."""
    log_info('main', 'Starting heatmap generation')
    
    generator = HeatmapGenerator()
    
    # Create price heatmap
    heatmap_path = 'price_heatmap.html'
    generator.create_price_heatmap(df, output_path=heatmap_path)
    
    log_info('main', f'Heatmap generated: {heatmap_path}')
    
    return generator


def run_full_pipeline():
    """Run the complete AI pipeline."""
    log_info('main', '='*80)
    log_info('main', 'BANGALORE REAL ESTATE INTELLIGENCE SYSTEM - PIPELINE STARTED')
    log_info('main', '='*80)
    
    try:
        # Step 1: Load data
        df = load_data()
        
        # Step 2: Preprocessing
        df_processed, preprocessor = run_preprocessing(df)
        
        # Step 3: Feature Engineering
        df_featured, engineer = run_feature_engineering(df_processed)
        
        # Step 4: Anomaly Detection
        df_anomalies, detector, anomaly_summary = run_anomaly_detection(df_featured)
        
        # Step 5: Investment Scoring
        df_investment, scorer, investment_summary = run_investment_scoring(df_anomalies)
        
        # Step 6: Model Training
        trainer = run_model_training(df_investment)
        
        # Step 7: Explainability
        analyzer, global_importance = run_explainability(df_investment, trainer)
        
        # Step 8: Heatmap Generation
        generator = run_heatmap_generation(df_investment)
        
        # Print summary
        print("\n" + "="*80)
        print("PIPELINE EXECUTION COMPLETED SUCCESSFULLY")
        print("="*80)
        
        print("\n📊 ANALYSIS SUMMARY:")
        print(f"   Total Properties Analyzed: {len(df)}")
        print(f"   Anomalies Detected: {anomaly_summary['total_anomalies']} ({anomaly_summary['anomaly_percentage']:.2f}%)")
        print(f"   Top Investment Areas: {list(investment_summary['top_investment_areas'].keys())[:5]}")
        print(f"   Best Model: {trainer.best_model_name} (R² = {trainer.best_score:.4f})")
        print(f"   Top Features: {list(global_importance.keys())[:5]}")
        
        print("\n📁 OUTPUT FILES:")
        print(f"   - Processed Data: {PROCESSED_DATA_PATH}")
        print(f"   - Featured Data: {FEATURED_DATA_PATH}")
        print(f"   - Best Model: {MODEL_PATH}")
        print(f"   - Preprocessor: {PREPROCESSOR_PATH}")
        print(f"   - Anomaly Detector: {ANOMALY_MODEL_PATH}")
        print(f"   - Investment Scorer: {INVESTMENT_SCORER_PATH}")
        print(f"   - Price Heatmap: price_heatmap.html")
        
        print("\n🚀 To run the Streamlit application:")
        print("   streamlit run streamlit_app/main.py")
        
        log_info('main', 'PIPELINE EXECUTION COMPLETED SUCCESSFULLY')
        
        return {
            'preprocessor': preprocessor,
            'engineer': engineer,
            'detector': detector,
            'scorer': scorer,
            'trainer': trainer,
            'analyzer': analyzer,
            'anomaly_summary': anomaly_summary,
            'investment_summary': investment_summary,
            'global_importance': global_importance
        }
        
    except Exception as e:
        log_error('main', f'Pipeline execution failed: {str(e)}')
        raise


if __name__ == '__main__':
    run_full_pipeline()
