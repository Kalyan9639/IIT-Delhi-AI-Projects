"""
Anomaly Detection Module for Bangalore Real Estate Intelligence System.
Detects fraudulent, overpriced, underpriced, and suspicious listings.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

from .logging_utils import log_info, log_error


class AnomalyDetector:
    """
    Advanced anomaly detection class for real estate data.
    Detects various types of anomalies in property listings.
    """
    
    def __init__(self, method='isolation_forest', contamination=0.05, random_state=42):
        self.method = method
        self.contamination = contamination
        self.random_state = random_state
        
        self.isolation_forest = None
        self.lof = None
        self.scaler = StandardScaler()
        self.anomaly_statistics = {}
        
    def detect_anomalies_isolation_forest(self, df, features=None):
        """Detect anomalies using Isolation Forest."""
        log_info('detect_anomalies_isolation_forest', 'Starting Isolation Forest anomaly detection')
        
        if features is None:
            features = ['total_sqft', 'price', 'bhk', 'bath', 'balcony', 'price_per_sqft']
        
        # Select features
        X = df[features].copy()
        X = X.fillna(X.median())
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Isolation Forest
        self.isolation_forest = IsolationForest(
            n_estimators=100,
            contamination=self.contamination,
            random_state=self.random_state,
            n_jobs=-1
        )
        
        predictions = self.isolation_forest.fit_predict(X_scaled)
        scores = -self.isolation_forest.score_samples(X_scaled)  # Higher score = more anomalous
        
        # Store results
        df['anomaly_score_if'] = scores
        df['is_anomaly_if'] = predictions == -1
        
        # Calculate anomaly statistics
        anomaly_count = df['is_anomaly_if'].sum()
        anomaly_percentage = (anomaly_count / len(df)) * 100
        
        self.anomaly_statistics['isolation_forest'] = {
            'total_anomalies': int(anomaly_count),
            'anomaly_percentage': float(anomaly_percentage),
            'normal_count': int(len(df) - anomaly_count)
        }
        
        log_info('detect_anomalies_isolation_forest', 
                f'Found {anomaly_count} anomalies ({anomaly_percentage:.2f}%)')
        
        return df
    
    def detect_anomalies_lof(self, df, features=None):
        """Detect anomalies using Local Outlier Factor."""
        log_info('detect_anomalies_lof', 'Starting LOF anomaly detection')
        
        if features is None:
            features = ['total_sqft', 'price', 'bhk', 'bath', 'balcony', 'price_per_sqft']
        
        # Select features
        X = df[features].copy()
        X = X.fillna(X.median())

        # Scale features
        X_scaled = self.scaler.fit_transform(X) if not hasattr(self.scaler, 'scale_') else self.scaler.transform(X)
        
        # Train LOF
        self.lof = LocalOutlierFactor(
            n_neighbors=20,
            contamination=self.contamination,
            n_jobs=-1
        )

        predictions = self.lof.fit_predict(X_scaled)
        scores = -self.lof.negative_outlier_factor_
        
        # Store results
        df['anomaly_score_lof'] = scores
        df['is_anomaly_lof'] = predictions == -1
        
        # Calculate anomaly statistics
        anomaly_count = df['is_anomaly_lof'].sum()
        anomaly_percentage = (anomaly_count / len(df)) * 100
        
        self.anomaly_statistics['lof'] = {
            'total_anomalies': int(anomaly_count),
            'anomaly_percentage': float(anomaly_percentage),
            'normal_count': int(len(df) - anomaly_count)
        }
        
        log_info('detect_anomalies_lof', f'Found {anomaly_count} anomalies ({anomaly_percentage:.2f}%)')
        
        return df
    
    def detect_overpriced_properties(self, df):
        """Detect overpriced properties based on price per sqft."""
        log_info('detect_overpriced_properties', 'Detecting overpriced properties')
        
        if 'price_per_sqft' not in df.columns:
            df['price_per_sqft'] = (df['price'] * 100000) / df['total_sqft']
        
        # Calculate statistics by location and BHK
        df['overpriced'] = False
        df['overpriced_reason'] = ''
        
        for location in df['location'].unique():
            location_mask = df['location'] == location
            
            for bhk in df['bhk'].unique():
                bhk_mask = df['bhk'] == bhk
                mask = location_mask & bhk_mask
                
                if mask.sum() < 5:
                    continue
                
                location_bhk_data = df.loc[mask, 'price_per_sqft']
                
                # Calculate threshold (mean + 2*std)
                threshold = location_bhk_data.mean() + 2 * location_bhk_data.std()
                
                # Mark overpriced
                overpriced_mask = mask & (df['price_per_sqft'] > threshold)
                df.loc[overpriced_mask, 'overpriced'] = True
                df.loc[overpriced_mask, 'overpriced_reason'] = f'Overpriced for {location} {bhk}BHK'
        
        overpriced_count = df['overpriced'].sum()
        log_info('detect_overpriced_properties', f'Found {overpriced_count} overpriced properties')
        
        return df
    
    def detect_underpriced_properties(self, df):
        """Detect underpriced properties based on price per sqft."""
        log_info('detect_underpriced_properties', 'Detecting underpriced properties')
        
        if 'price_per_sqft' not in df.columns:
            df['price_per_sqft'] = (df['price'] * 100000) / df['total_sqft']
        
        df['underpriced'] = False
        df['underpriced_reason'] = ''
        
        for location in df['location'].unique():
            location_mask = df['location'] == location
            
            for bhk in df['bhk'].unique():
                bhk_mask = df['bhk'] == bhk
                mask = location_mask & bhk_mask
                
                if mask.sum() < 5:
                    continue
                
                location_bhk_data = df.loc[mask, 'price_per_sqft']
                
                # Calculate threshold (mean - 2*std)
                threshold = location_bhk_data.mean() - 2 * location_bhk_data.std()
                
                # Mark underpriced
                underpriced_mask = mask & (df['price_per_sqft'] < threshold)
                df.loc[underpriced_mask, 'underpriced'] = True
                df.loc[underpriced_mask, 'underpriced_reason'] = f'Underpriced for {location} {bhk}BHK'
        
        underpriced_count = df['underpriced'].sum()
        log_info('detect_underpriced_properties', f'Found {underpriced_count} underpriced properties')
        
        return df
    
    def detect_suspicious_listings(self, df):
        """Detect suspicious listings based on various criteria."""
        log_info('detect_suspicious_listings', 'Detecting suspicious listings')
        
        df['is_suspicious'] = False
        df['suspicious_reasons'] = ''
        
        # Criterion 1: Unrealistic price per sqft (too low or too high)
        if 'price_per_sqft' in df.columns:
            lower_threshold = df['price_per_sqft'].quantile(0.01)
            upper_threshold = df['price_per_sqft'].quantile(0.99)
            
            suspicious_mask = (df['price_per_sqft'] < lower_threshold) | \
                             (df['price_per_sqft'] > upper_threshold)
            
            df.loc[suspicious_mask, 'is_suspicious'] = True
            df.loc[suspicious_mask, 'suspicious_reasons'] += 'Unrealistic price/sqft; '
        
        # Criterion 2: Impossible BHK configurations
        if 'bhk' in df.columns and 'total_sqft' in df.columns:
            # Very small area for high BHK
            suspicious_mask = (df['bhk'] >= 4) & (df['total_sqft'] < 800)
            df.loc[suspicious_mask, 'is_suspicious'] = True
            df.loc[suspicious_mask, 'suspicious_reasons'] += 'Small area for high BHK; '
            
            # Very large area for low BHK
            suspicious_mask = (df['bhk'] <= 1) & (df['total_sqft'] > 2000)
            df.loc[suspicious_mask, 'is_suspicious'] = True
            df.loc[suspicious_mask, 'suspicious_reasons'] += 'Large area for low BHK; '
        
        # Criterion 3: Too many bathrooms for BHK
        if 'bhk' in df.columns and 'bath' in df.columns:
            suspicious_mask = df['bath'] > df['bhk'] + 2
            df.loc[suspicious_mask, 'is_suspicious'] = True
            df.loc[suspicious_mask, 'suspicious_reasons'] += 'Excessive bathrooms; '
        
        # Remove trailing semicolon
        df['suspicious_reasons'] = df['suspicious_reasons'].str.rstrip('; ')
        
        suspicious_count = df['is_suspicious'].sum()
        log_info('detect_suspicious_listings', f'Found {suspicious_count} suspicious listings')
        
        return df
    
    def detect_anomalies_statistical(self, df, features=None):
        """Detect anomalies with a lightweight statistical score."""
        log_info('detect_anomalies_statistical', 'Starting statistical anomaly detection')

        if features is None:
            features = ['total_sqft', 'price', 'bhk', 'bath', 'balcony', 'price_per_sqft']

        available = [feature for feature in features if feature in df.columns]
        if not available:
            df['anomaly_score_stat'] = 0.0
            df['is_anomaly_stat'] = False
            return df

        X = df[available].copy().fillna(df[available].median())
        z_scores = ((X - X.mean()) / (X.std(ddof=0) + 1e-6)).abs()
        score = z_scores.mean(axis=1)
        threshold = score.mean() + 2 * score.std()

        df['anomaly_score_stat'] = score
        df['is_anomaly_stat'] = score > threshold

        anomaly_count = int(df['is_anomaly_stat'].sum())
        anomaly_percentage = (anomaly_count / len(df)) * 100
        self.anomaly_statistics['statistical'] = {
            'total_anomalies': anomaly_count,
            'anomaly_percentage': float(anomaly_percentage),
            'normal_count': int(len(df) - anomaly_count)
        }

        return df
    
    def detect_all_anomalies(self, df):
        """Run all anomaly detection methods."""
        log_info('detect_all_anomalies', 'Starting complete anomaly detection')
        
        # Run all methods
        df = self.detect_anomalies_isolation_forest(df)
        df = self.detect_anomalies_lof(df)
        df = self.detect_overpriced_properties(df)
        df = self.detect_underpriced_properties(df)
        df = self.detect_suspicious_listings(df)
        df = self.detect_anomalies_statistical(df)

        # Combine anomaly indicators
        anomaly_columns = ['is_anomaly_if', 'is_anomaly_lof', 'is_anomaly_stat',
                          'overpriced', 'underpriced', 'is_suspicious']
        df['is_any_anomaly'] = df[anomaly_columns].any(axis=1)
        
        # Count total anomalies
        total_anomalies = df['is_any_anomaly'].sum()
        total_percentage = (total_anomalies / len(df)) * 100
        
        self.anomaly_statistics['combined'] = {
            'total_anomalies': int(total_anomalies),
            'anomaly_percentage': float(total_percentage),
            'normal_count': int(len(df) - total_anomalies)
        }
        
        log_info('detect_all_anomalies', f'Combined: {total_anomalies} anomalies ({total_percentage:.2f}%)')
        
        return df
    
    def get_anomaly_summary(self, df):
        """Get summary of all anomalies detected."""
        log_info('get_anomaly_summary', 'Generating anomaly summary')
        
        summary = {
            'total_properties': len(df),
            'anomaly_methods': self.anomaly_statistics,
            'overpriced_count': int(df['overpriced'].sum()),
            'underpriced_count': int(df['underpriced'].sum()),
            'suspicious_count': int(df['is_suspicious'].sum()),
            'total_anomalies': int(df['is_any_anomaly'].sum()),
            'anomaly_percentage': float((df['is_any_anomaly'].sum() / len(df)) * 100)
        }
        
        return summary
    
    def save_model(self, path):
        """Save anomaly detection model."""
        import pickle
        
        model_data = {
            'method': self.method,
            'contamination': self.contamination,
            'scaler': self.scaler,
            'isolation_forest': self.isolation_forest,
            'lof': self.lof,
            'anomaly_statistics': self.anomaly_statistics
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        
        log_info('save_model', f'Anomaly detection model saved to {path}')
    
    def load_model(self, path):
        """Load anomaly detection model."""
        import pickle
        
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
            
            self.method = model_data['method']
            self.contamination = model_data['contamination']
            self.scaler = model_data['scaler']
            self.isolation_forest = model_data['isolation_forest']
            self.lof = model_data['lof']
            self.anomaly_statistics = model_data['anomaly_statistics']
        
        log_info('load_model', f'Anomaly detection model loaded from {path}')
