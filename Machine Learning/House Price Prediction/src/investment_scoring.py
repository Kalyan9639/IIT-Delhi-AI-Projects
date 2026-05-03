"""
Investment Scoring Module for Bangalore Real Estate Intelligence System.
Creates area-wise investment scores and recommendations.
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from .config import INVESTMENT_CONFIG
from .logging_utils import log_info, log_error, log_warning


class InvestmentScorer:
    """
    Investment scoring class for real estate data.
    Creates comprehensive investment scores and recommendations.
    """
    
    def __init__(self):
        self.weights = INVESTMENT_CONFIG
        self.investment_scores = {}
        self.area_recommendations = {}

    def _safe_qcut(self, series, q, labels):
        """Safely apply qcut even when there are too few unique values."""
        try:
            return pd.qcut(series, q=q, labels=labels, duplicates='drop')
        except ValueError:
            return pd.Series([labels[len(labels) // 2]] * len(series), index=series.index)

    def _minmax(self, series):
        """Normalize a series to 0-1 safely."""
        span = series.max() - series.min()
        if pd.isna(span) or span == 0:
            return pd.Series([0.5] * len(series), index=series.index)
        return (series - series.min()) / (span + 1e-6)
        
    def calculate_investment_score(self, df):
        """Calculate investment score for each location."""
        log_info('calculate_investment_score', 'Starting investment score calculation')
        
        if 'location' not in df.columns:
            log_error('calculate_investment_score', 'Location column not found')
            return df
        
        # Calculate location-level statistics
        location_stats = df.groupby('location').agg({
            'price_per_sqft': ['mean', 'std', 'min', 'max'],
            'price': ['mean', 'std'],
            'total_sqft': ['mean', 'std'],
            'bhk': 'mean',
            'bath': 'mean'
        }).reset_index()
        
        location_stats.columns = [
            'location', 'avg_price_per_sqft', 'std_price_per_sqft',
            'min_price_per_sqft', 'max_price_per_sqft',
            'avg_price', 'std_price', 'avg_area', 'std_area',
            'avg_bhk', 'avg_bath'
        ]
        
        # Calculate demand score (based on frequency and average price)
        location_freq = df.groupby('location').size().reset_index(name='listing_count')
        location_stats = location_stats.merge(location_freq, on='location')
        
        # Normalize features
        location_stats['price_per_sqft_norm'] = 1 - self._minmax(location_stats['avg_price_per_sqft'])
        location_stats['price_norm'] = 1 - self._minmax(location_stats['avg_price'])
        location_stats['demand_norm'] = self._minmax(location_stats['listing_count'])
        location_stats['consistency_score'] = 1 - self._minmax(location_stats['std_price_per_sqft'])
        location_stats['affordability_norm'] = 1 - self._minmax(location_stats['avg_price_per_sqft'])
        
        # Calculate weighted investment score
        location_stats['investment_score'] = (
            location_stats['price_per_sqft_norm'] * self.weights['weight_pricing'] +
            location_stats['price_norm'] * 0.2 +
            location_stats['demand_norm'] * self.weights['weight_demand'] +
            location_stats['consistency_score'] * self.weights['weight_consistency'] +
            location_stats['affordability_norm'] * self.weights['weight_affordability'] +
            (location_stats['avg_bhk'] / location_stats['avg_bhk'].max()) * 0.1
        )
        
        # Create investment category
        location_stats['investment_category'] = self._safe_qcut(
            location_stats['investment_score'],
            q=5,
            labels=['Poor_Investment', 'Below_Avg', 'Average', 'Good_Investment', 'Excellent_Investment']
        )
        
        # Create risk category
        location_stats['risk_category'] = self._safe_qcut(
            location_stats['std_price_per_sqft'],
            q=5,
            labels=['Low_Risk', 'Below_Avg_Risk', 'Average_Risk', 'High_Risk', 'Very_High_Risk']
        )
        
        # Store for later use
        self.investment_scores = location_stats.set_index('location')['investment_score'].to_dict()
        
        # Merge back to main dataframe
        df = df.merge(
            location_stats[['location', 'investment_score', 'investment_category', 'risk_category']],
            on='location',
            how='left'
        )
        
        log_info('calculate_investment_score', f'Investment scores calculated. Range: {location_stats["investment_score"].min():.3f} - {location_stats["investment_score"].max():.3f}')
        
        return df
    
    def calculate_area_popularity(self, df):
        """Calculate area popularity score."""
        log_info('calculate_area_popularity', 'Calculating area popularity')
        
        if 'location' not in df.columns:
            return df
        
        # Popularity based on multiple factors
        location_popularity = df.groupby('location').agg({
            'total_sqft': 'mean',
            'price': 'mean',
            'bhk': 'mean'
        }).reset_index()
        
        location_freq = df.groupby('location').size().reset_index(name='frequency')
        location_popularity = location_popularity.merge(location_freq, on='location')
        
        # Normalize
        location_popularity['area_norm'] = self._minmax(location_popularity['total_sqft'])
        location_popularity['price_norm'] = 1 - self._minmax(location_popularity['price'])
        location_popularity['bhk_norm'] = self._minmax(location_popularity['bhk'])
        
        # Combined popularity score
        location_popularity['popularity_score'] = (
            location_popularity['frequency'] / location_popularity['frequency'].max() * 0.4 +
            location_popularity['area_norm'] * 0.2 +
            location_popularity['price_norm'] * 0.2 +
            location_popularity['bhk_norm'] * 0.2
        )
        
        # Merge back
        df = df.merge(
            location_popularity[['location', 'popularity_score']],
            on='location',
            how='left'
        )
        
        log_info('calculate_area_popularity', f'Popularity scores calculated. Range: {location_popularity["popularity_score"].min():.3f} - {location_popularity["popularity_score"].max():.3f}')
        
        return df
    
    def create_area_recommendations(self, df):
        """Create area-wise investment recommendations."""
        log_info('create_area_recommendations', 'Creating area recommendations')
        
        if 'location' not in df.columns or 'investment_score' not in df.columns:
            return df
        
        # Get top areas by investment score
        top_areas = df.groupby('location')['investment_score'].mean().sort_values(ascending=False).head(10)
        
        # Get areas with best price appreciation potential
        price_trend = df.groupby('location')['price'].mean().sort_values().head(10)
        
        # Get areas with best affordability
        affordability = df.groupby('location')['price_per_sqft'].mean().sort_values().head(10)
        
        # Create recommendations
        self.area_recommendations = {
            'top_investment_areas': top_areas.index.tolist(),
            'best_price_appreciation': price_trend.index.tolist(),
            'most_affordable_areas': affordability.index.tolist(),
            'premium_areas': df[df['investment_score'] > df['investment_score'].quantile(0.75)]['location'].unique().tolist()
        }
        
        log_info('create_area_recommendations', f'Top investment areas: {self.area_recommendations["top_investment_areas"][:5]}')
        
        return df
    
    def calculate_price_appreciation_potential(self, df):
        """Calculate price appreciation potential for each area."""
        log_info('calculate_price_appreciation_potential', 'Calculating price appreciation potential')
        
        if 'location' not in df.columns:
            return df
        
        # Calculate price per sqft trend indicators
        location_stats = df.groupby('location').agg({
            'price_per_sqft': ['mean', 'std', 'min', 'max'],
            'total_sqft': 'mean'
        }).reset_index()
        
        location_stats.columns = ['location', 'avg_price_per_sqft', 'std_price_per_sqft',
                                  'min_price_per_sqft', 'max_price_per_sqft', 'avg_area']
        
        # Calculate appreciation potential score
        location_stats['appreciation_potential'] = (
            (location_stats['max_price_per_sqft'] - location_stats['min_price_per_sqft']) / 
            (location_stats['min_price_per_sqft'] + 1e-6)
        ) * (1 / (location_stats['std_price_per_sqft'] + 1e-6))
        
        # Normalize
        max_potential = location_stats['appreciation_potential'].max()
        location_stats['appreciation_score'] = location_stats['appreciation_potential'] / (max_potential + 1e-6)
        
        # Merge back
        df = df.merge(
            location_stats[['location', 'appreciation_score']],
            on='location',
            how='left'
        )
        
        log_info('calculate_price_appreciation_potential', f'Appreciation scores calculated. Range: {location_stats["appreciation_score"].min():.3f} - {location_stats["appreciation_score"].max():.3f}')
        
        return df
    
    def create_affordability_index(self, df):
        """Create affordability index for each area."""
        log_info('create_affordability_index', 'Creating affordability index')
        
        if 'location' not in df.columns:
            return df
        
        # Calculate affordability metrics
        location_affordability = df.groupby('location').agg({
            'price_per_sqft': 'mean',
            'total_sqft': 'mean',
            'bhk': 'mean'
        }).reset_index()
        
        # affordability score (lower price = higher score)
        location_affordability['affordability_index'] = 1 - self._minmax(location_affordability['price_per_sqft'])
        
        # Adjust for area and BHK
        location_affordability['affordability_index'] *= self._minmax(location_affordability['total_sqft']) * 0.3 + 0.7
        
        # Merge back
        df = df.merge(
            location_affordability[['location', 'affordability_index']],
            on='location',
            how='left'
        )
        
        log_info('create_affordability_index', f'Affordability indices calculated. Range: {location_affordability["affordability_index"].min():.3f} - {location_affordability["affordability_index"].max():.3f}')
        
        return df
    
    def create_risk_score(self, df):
        """Create risk score for each area."""
        log_info('create_risk_score', 'Creating risk score')
        
        if 'location' not in df.columns:
            return df
        
        # Risk based on price volatility
        location_risk = df.groupby('location').agg({
            'price_per_sqft': 'std',
            'total_sqft': 'std',
            'price': 'std'
        }).reset_index()
        
        location_risk.columns = ['location', 'price_volatility', 'area_volatility', 'price_std']
        
        # Normalize volatility
        location_risk['risk_score'] = self._minmax(location_risk['price_volatility'])
        
        # Merge back
        df = df.merge(
            location_risk[['location', 'risk_score']],
            on='location',
            how='left'
        )
        
        log_info('create_risk_score', f'Risk scores calculated. Range: {location_risk["risk_score"].min():.3f} - {location_risk["risk_score"].max():.3f}')
        
        return df
    
    def create_composite_score(self, df):
        """Create composite investment score."""
        log_info('create_composite_score', 'Creating composite score')
        
        # Ensure all required columns exist
        required_cols = ['investment_score', 'popularity_score', 'appreciation_score', 
                        'affordability_index', 'risk_score']
        
        for col in required_cols:
            if col not in df.columns:
                log_warning('create_composite_score', f'Missing column: {col}')
                df[col] = 0.5  # Default neutral score
        
        # Normalize all scores
        for col in required_cols:
            df[f'{col}_norm'] = self._minmax(df[col])
        
        # Create composite score (weighted average)
        df['composite_score'] = (
            df['investment_score_norm'] * 0.35 +
            df['popularity_score_norm'] * 0.25 +
            df['appreciation_score_norm'] * 0.20 +
            df['affordability_index_norm'] * 0.15 +
            (1 - df['risk_score_norm']) * 0.05  # Lower risk = higher score
        )
        
        # Create composite category
        df['composite_category'] = self._safe_qcut(
            df['composite_score'],
            q=5,
            labels=['Poor', 'Below_Avg', 'Average', 'Good', 'Excellent']
        )
        
        log_info('create_composite_score', f'Composite scores calculated. Range: {df["composite_score"].min():.3f} - {df["composite_score"].max():.3f}')
        
        return df
    
    def get_investment_summary(self, df):
        """Get investment summary for all areas."""
        log_info('get_investment_summary', 'Generating investment summary')
        
        summary = {
            'total_locations': df['location'].nunique(),
            'top_investment_areas': df.groupby('location')['investment_score'].mean().sort_values(ascending=False).head(10).to_dict(),
            'bottom_investment_areas': df.groupby('location')['investment_score'].mean().sort_values().head(10).to_dict(),
            'average_investment_score': float(df['investment_score'].mean()),
            'investment_score_std': float(df['investment_score'].std()),
            'risk_distribution': df['risk_category'].value_counts().to_dict() if 'risk_category' in df.columns else {},
            'affordability_distribution': df['affordability_category'].value_counts().to_dict() if 'affordability_category' in df.columns else {}
        }
        
        return summary
    
    def save_model(self, path):
        """Save investment scorer model."""
        import pickle
        
        model_data = {
            'weights': self.weights,
            'investment_scores': self.investment_scores,
            'area_recommendations': self.area_recommendations
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        
        log_info('save_model', f'Investment scorer saved to {path}')
    
    def load_model(self, path):
        """Load investment scorer model."""
        import pickle
        
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
            
            self.weights = model_data['weights']
            self.investment_scores = model_data['investment_scores']
            self.area_recommendations = model_data['area_recommendations']
        
        log_info('load_model', f'Investment scorer loaded from {path}')
