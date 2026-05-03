"""
Main Training Script for Bangalore Real Estate Intelligence System.
Orchestrates the complete ML pipeline from data loading to model deployment.
"""

import pandas as pd
import numpy as np
import pickle
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from src.config import *
from src.preprocessing import DataPreprocessor
from src.feature_engineering import FeatureEngineer
from src.anomaly_detection import AnomalyDetector
from src.investment_scoring import InvestmentScorer
from src.heatmap_generator import HeatmapGenerator
from src.model_training import ModelTrainer
from src.explainability import ExplainabilityAnalyzer


def main():
    """Main function to run the complete ML pipeline."""
    print("=" * 80)
    print("BANGALORE REAL ESTATE INTELLIGENCE SYSTEM")
    print("Complete ML Pipeline Execution")
    print("=" * 80)
    
    # Initialize components
    print("\n[1/7] Initializing components...")
    preprocessor = DataPreprocessor()
    feature_engineer = FeatureEngineer()
    anomaly_detector = AnomalyDetector()
    investment_scorer = InvestmentScorer()
    heatmap_generator = HeatmapGenerator()
    model_trainer = ModelTrainer()
    explainer = ExplainabilityAnalyzer()
    
    # Step 1: Load and preprocess data
    print("\n[2/7] Loading and preprocessing data...")
    df = preprocessor.load_data(RAW_DATA_PATH)
    print(f"Original data shape: {df.shape}")
    
    # Initial preprocessing
    df = preprocessor.preprocess(df.copy())
    print(f"After preprocessing: {df.shape}")
    
    # Step 2: Feature engineering
    print("\n[3/7] Creating features...")
    df = feature_engineer.create_all_features(df.copy())
    print(f"Features created. Total columns: {len(df.columns)}")
    
    # Feature importance analysis
    feature_importance = feature_engineer.get_feature_importance(df)
    print("\nTop 10 Important Features:")
    for i, (feature, importance) in enumerate(list(feature_importance.items())[:10], 1):
        print(f"  {i}. {feature}: {importance:.4f}")
    
    # Step 3: Anomaly detection
    print("\n[4/7] Running anomaly detection...")
    df = anomaly_detector.detect_all_anomalies(df.copy())
    anomaly_summary = anomaly_detector.get_anomaly_summary(df)
    print(f"Anomalies detected: {anomaly_summary['total_anomalies']} ({anomaly_summary['anomaly_percentage']:.2f}%)")
    
    # Step 4: Investment scoring
    print("\n[5/7] Calculating investment scores...")
    df = investment_scorer.calculate_investment_score(df.copy())
    df = investment_scorer.create_composite_score(df.copy())
    df = investment_scorer.create_area_recommendations(df.copy())
    
    investment_summary = investment_scorer.get_investment_summary(df)
    print(f"Average investment score: {investment_summary['average_investment_score']:.3f}")
    
    # Step 5: Prepare data for training
    print("\n[6/7] Preparing data for model training...")
    
    # Select features for training
    feature_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    if 'price' in feature_columns:
        feature_columns.remove('price')
    
    # Prepare data
    X_train, X_test, y_train, y_test = model_trainer.prepare_data(
        df, 
        target_column='price',
        feature_columns=feature_columns
    )
    
    print(f"Training set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")
    
    # Step 6: Train models
    print("\n[7/7] Training models...")
    model_scores = model_trainer.train_all_models(X_train, X_test, y_train, y_test)
    
    # Get model summary
    model_summary = model_trainer.get_model_summary()
    
    print("\n" + "=" * 80)
    print("MODEL PERFORMANCE SUMMARY")
    print("=" * 80)
    
    for model_name, metrics in model_scores.items():
        print(f"\n{model_name}:")
        print(f"  R2 Score: {metrics['r2_score']:.4f}")
        print(f"  MAE: {metrics['mae']:.4f}")
        print(f"  RMSE: {metrics['rmse']:.4f}")
        print(f"  MAPE: {metrics['mape']:.4f}")
        print(f"  CV R2: {metrics['cv_r2_mean']:.4f} ± {metrics['cv_r2_std']:.4f}")
    
    print(f"\n🏆 Best Model: {model_summary['best_model']} with R2: {model_summary['best_r2_score']:.4f}")
    
    # Step 7: Save models and artifacts
    print("\n[8/8] Saving models and artifacts...")
    
    # Save preprocessor
    preprocessor.save_preprocessor(PREPROCESSOR_PATH)
    
    # Save anomaly detector
    anomaly_detector.save_model(ANOMALY_MODEL_PATH)
    
    # Save investment scorer
    investment_scorer.save_model(INVESTMENT_SCORER_PATH)
    
    # Save main model
    model_trainer.save_model(MODEL_PATH, PREPROCESSOR_PATH)
    
    # Save processed data
    df.to_csv(PROCESSED_DATA_PATH, index=False)
    print(f"Processed data saved to {PROCESSED_DATA_PATH}")
    
    # Generate heatmaps
    print("\n[9/9] Generating heatmaps...")
    heatmap_generator.create_price_heatmap(df, str(MODEL_DIR / 'price_heatmap.html'))
    heatmap_generator.create_investment_heatmap(df, str(MODEL_DIR / 'investment_heatmap.html'))
    heatmap_generator.create_price_concentration_map(df, str(MODEL_DIR / 'price_concentration.html'))
    print("Heatmaps generated successfully!")
    
    # Save feature engineering results
    feature_engineer_df = df.copy()
    feature_engineer_df.to_csv(FEATURED_DATA_PATH, index=False)
    print(f"Featured data saved to {FEATURED_DATA_PATH}")
    
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    
    print("\nGenerated Artifacts:")
    print(f"  - Model: {MODEL_PATH}")
    print(f"  - Preprocessor: {PREPROCESSOR_PATH}")
    print(f"  - Anomaly Detector: {ANOMALY_MODEL_PATH}")
    print(f"  - Investment Scorer: {INVESTMENT_SCORER_PATH}")
    print(f"  - Processed Data: {PROCESSED_DATA_PATH}")
    print(f"  - Featured Data: {FEATURED_DATA_PATH}")
    print(f"  - Heatmaps: {MODEL_DIR}/")
    
    print("\nTo run the Streamlit application:")
    print("  streamlit run streamlit_app/main.py")
    
    return df, model_trainer


if __name__ == "__main__":
    df, model_trainer = main()
