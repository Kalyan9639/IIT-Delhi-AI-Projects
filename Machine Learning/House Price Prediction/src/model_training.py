"""
Model Training Pipeline for Bangalore Real Estate Intelligence System.
Trains and evaluates multiple regression models with hyperparameter tuning.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, RandomizedSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
import xgboost as xgb
import lightgbm as lgb
import catboost as cb
import warnings
warnings.filterwarnings('ignore')

from .config import MODEL_CONFIG
from .logging_utils import log_info, log_error, log_warning


class ModelTrainer:
    """
    Model training class for real estate data.
    Trains multiple regression models and selects the best one.
    """
    
    def __init__(self, random_state=42):
        self.random_state = random_state
        self.models = {}
        self.best_model = None
        self.best_model_name = None
        self.best_score = -np.inf
        self.model_scores = {}
        self.feature_importance = {}
        self.training_feature_blacklist = {
            'price',
            'price_per_sqft',
            'price_per_sqft_norm',
            'location_frequency',
            'location_frequency_norm',
            'locality_avg_price_per_sqft',
            'locality_count',
            'locality_popularity',
            'investment_score',
            'investment_category',
            'affordability_score',
            'affordability_category',
            'is_premium_pricing',
            'is_premium_area',
            'luxury_score',
            'bhk_price_interaction',
            'rooms_price_interaction',
            'anomaly_score_if',
            'anomaly_score_lof',
            'anomaly_score_stat',
            'is_anomaly_if',
            'is_anomaly_lof',
            'is_anomaly_stat',
            'is_any_anomaly',
            'overpriced',
            'underpriced',
            'is_suspicious',
            'composite_score',
            'composite_category',
        }
        
    def prepare_data(self, df, target_column='price', feature_columns=None):
        """Prepare data for training."""
        log_info('prepare_data', 'Preparing data for training')
        
        if feature_columns is None:
            # Use all numeric columns except target
            feature_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        feature_columns = [column for column in feature_columns if column not in self.training_feature_blacklist and column != target_column]
        
        X = df[feature_columns].copy()
        y = df[target_column].copy()

        # Handle missing values
        X = X.fillna(X.median())
        y = y.fillna(y.median())
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=MODEL_CONFIG['test_size'],
            random_state=self.random_state,
            shuffle=True
        )

        self.feature_columns = feature_columns

        log_info('prepare_data', f'Data prepared. Train size: {len(X_train)}, Test size: {len(X_test)}')

        return X_train, X_test, y_train, y_test
    
    def train_linear_regression(self, X_train, y_train):
        """Train Linear Regression model."""
        log_info('train_linear_regression', 'Training Linear Regression')
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        return model
    
    def train_random_forest(self, X_train, y_train):
        """Train Random Forest model with hyperparameter tuning."""
        log_info('train_random_forest', 'Training Random Forest')
        
        # Define parameter grid
        param_grid = {
            'n_estimators': [30, 20, 40],
            'max_depth': [10, 20, 30, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['sqrt', 'log2', 0.8, 1.0]
        }
        
        # Randomized search
        rf = RandomForestRegressor(random_state=self.random_state, n_jobs=-1)
        random_search = RandomizedSearchCV(
            rf, param_grid, n_iter=10,
            cv=MODEL_CONFIG['cv_folds'],
            scoring='r2', random_state=self.random_state, n_jobs=-1
        )
        
        random_search.fit(X_train, y_train)
        
        log_info('train_random_forest', f'Best parameters: {random_search.best_params_}')
        
        return random_search.best_estimator_
    
    def train_xgboost(self, X_train, y_train):
        """Train XGBoost model with hyperparameter tuning."""
        log_info('train_xgboost', 'Training XGBoost')
        
        # Define parameter grid
        param_grid = {
            'n_estimators': [20, 30, 35],
            'max_depth': [3, 5, 7, 9],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'subsample': [0.8, 0.9, 1.0],
            'colsample_bytree': [0.8, 0.9, 1.0],
            'gamma': [0, 0.1, 0.2],
            'reg_alpha': [0, 0.1, 1],
            'reg_lambda': [1, 1.1, 1.2]
        }
        
        # Randomized search
        xgb_model = xgb.XGBRegressor(random_state=self.random_state, n_jobs=-1, verbosity=0)
        random_search = RandomizedSearchCV(
            xgb_model, param_grid, n_iter=10,
            cv=MODEL_CONFIG['cv_folds'],
            scoring='r2', random_state=self.random_state, n_jobs=-1
        )
        
        random_search.fit(X_train, y_train)
        
        log_info('train_xgboost', f'Best parameters: {random_search.best_params_}')
        
        return random_search.best_estimator_
    
    def train_lightgbm(self, X_train, y_train):
        """Train LightGBM model with hyperparameter tuning."""
        log_info('train_lightgbm', 'Training LightGBM')
        
        # Define parameter grid
        param_grid = {
            'n_estimators': [30, 20, 40],
            'max_depth': [3, 5, 7, 9, -1],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'num_leaves': [20, 31, 50, 100],
            'subsample': [0.8, 0.9, 1.0],
            'colsample_bytree': [0.8, 0.9, 1.0],
            'reg_alpha': [0, 0.1, 1],
            'reg_lambda': [0, 0.1, 1]
        }
        
        # Randomized search
        lgb_model = lgb.LGBMRegressor(random_state=self.random_state, n_jobs=-1, verbosity=-1)
        random_search = RandomizedSearchCV(
            lgb_model, param_grid, n_iter=10,
            cv=MODEL_CONFIG['cv_folds'],
            scoring='r2', random_state=self.random_state, n_jobs=-1
        )
        
        random_search.fit(X_train, y_train)
        
        log_info('train_lightgbm', f'Best parameters: {random_search.best_params_}')
        
        return random_search.best_estimator_
    
    def train_catboost(self, X_train, y_train):
        """Train CatBoost model with hyperparameter tuning."""
        log_info('train_catboost', 'Training CatBoost')
        
        # Define parameter grid
        param_grid = {
            'iterations': [30, 20, 40],
            'depth': [4, 6, 8, 10],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'l2_leaf_reg': [1, 3, 5, 7],
            'border_count': [32, 64, 128],
            'bagging_temperature': [0, 0.5, 1]
        }
        
        # Randomized search
        cb_model = cb.CatBoostRegressor(random_state=self.random_state, verbose=0)
        random_search = RandomizedSearchCV(
            cb_model, param_grid, n_iter=10,
            cv=MODEL_CONFIG['cv_folds'],
            scoring='r2', random_state=self.random_state, n_jobs=-1
        )
        
        random_search.fit(X_train, y_train)
        
        log_info('train_catboost', f'Best parameters: {random_search.best_params_}')
        
        return random_search.best_estimator_
    
    def train_extra_trees(self, X_train, y_train):
        """Train Extra Trees model."""
        log_info('train_extra_trees', 'Training Extra Trees')
        
        param_grid = {
            'n_estimators': [20, 30, 40],
            'max_depth': [10, 20, 30, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['sqrt', 'log2', 0.8, 1.0]
        }
        
        et = ExtraTreesRegressor(random_state=self.random_state, n_jobs=-1)
        random_search = RandomizedSearchCV(
            et, param_grid, n_iter=10,
            cv=MODEL_CONFIG['cv_folds'],
            scoring='r2', random_state=self.random_state, n_jobs=-1
        )
        
        random_search.fit(X_train, y_train)
        
        log_info('train_extra_trees', f'Best parameters: {random_search.best_params_}')
        
        return random_search.best_estimator_
    
    def train_gradient_boosting(self, X_train, y_train):
        """Train Gradient Boosting model."""
        log_info('train_gradient_boosting', 'Training Gradient Boosting')
        
        param_grid = {
            'n_estimators': [30, 20, 40],
            'max_depth': [3, 5, 7, 9],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'subsample': [0.8, 0.9, 1.0]
        }
        
        gb = GradientBoostingRegressor(random_state=self.random_state)
        random_search = RandomizedSearchCV(
            gb, param_grid, n_iter=10,
            cv=MODEL_CONFIG['cv_folds'],
            scoring='r2', random_state=self.random_state
        )
        
        random_search.fit(X_train, y_train)
        
        log_info('train_gradient_boosting', f'Best parameters: {random_search.best_params_}')
        
        return random_search.best_estimator_
    
    def evaluate_model(self, model, X_test, y_test, model_name, X_train=None, y_train=None):
        """Evaluate model performance."""
        log_info('evaluate_model', f'Evaluating {model_name}')
        
        # Predictions
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mape = mean_absolute_percentage_error(y_test, y_pred)
        
        # Cross-validation on the training split when available
        if X_train is not None and y_train is not None and len(X_train) >= MODEL_CONFIG['cv_folds']:
            cv_scores = cross_val_score(model, X_train, y_train, cv=MODEL_CONFIG['cv_folds'], scoring='r2')
            cv_mean = float(cv_scores.mean())
            cv_std = float(cv_scores.std())
        else:
            cv_mean = float('nan')
            cv_std = float('nan')

        metrics = {
            'r2_score': float(r2),
            'mae': float(mae),
            'rmse': float(rmse),
            'mape': float(mape),
            'cv_r2_mean': cv_mean,
            'cv_r2_std': cv_std
        }
        
        log_info('evaluate_model', f'{model_name} - R2: {r2:.4f}, MAE: {mae:.4f}, RMSE: {rmse:.4f}')
        
        return metrics
    
    def get_feature_importance(self, model, model_name):
        """Get feature importance from model."""
        log_info('get_feature_importance', f'Getting feature importance for {model_name}')
        
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
            feature_importance = dict(zip(self.feature_columns, importance))
            feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
            self.feature_importance[model_name] = feature_importance
            return feature_importance
        elif hasattr(model, 'coef_'):
            importance = np.abs(model.coef_)
            feature_importance = dict(zip(self.feature_columns, importance))
            feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
            self.feature_importance[model_name] = feature_importance
            return feature_importance
        
        return {}
    
    def train_all_models(self, X_train, X_test, y_train, y_test):
        """Train all models and compare performance."""
        log_info('train_all_models', 'Starting model training pipeline')
        
        models_to_train = MODEL_CONFIG['models_to_try']
        
        # Train each model
        if 'linear' in models_to_train:
            self.models['Linear Regression'] = self.train_linear_regression(X_train, y_train)
        
        if 'random_forest' in models_to_train:
            self.models['Random Forest'] = self.train_random_forest(X_train, y_train)
        
        if 'xgboost' in models_to_train:
            self.models['XGBoost'] = self.train_xgboost(X_train, y_train)
        
        if 'lightgbm' in models_to_train:
            self.models['LightGBM'] = self.train_lightgbm(X_train, y_train)
        
        if 'catboost' in models_to_train:
            self.models['CatBoost'] = self.train_catboost(X_train, y_train)
        
        if 'extra_trees' in models_to_train:
            self.models['Extra Trees'] = self.train_extra_trees(X_train, y_train)
        
        if 'gradient_boosting' in models_to_train:
            self.models['Gradient Boosting'] = self.train_gradient_boosting(X_train, y_train)
        
        # Evaluate each model
        for name, model in self.models.items():
            metrics = self.evaluate_model(model, X_test, y_test, name, X_train=X_train, y_train=y_train)
            self.model_scores[name] = metrics
            
            # Get feature importance
            self.get_feature_importance(model, name)
            
            # Update best model
            if metrics['r2_score'] > self.best_score:
                self.best_score = metrics['r2_score']
                self.best_model = model
                self.best_model_name = name
        
        log_info('train_all_models', f'Best model: {self.best_model_name} with R2: {self.best_score:.4f}')
        
        return self.model_scores
    
    def select_best_model(self):
        """Select the best model based on R2 score."""
        log_info('select_best_model', 'Selecting best model')
        
        if not self.model_scores:
            log_error('select_best_model', 'No models trained yet')
            return None
        
        best_model_name = max(self.model_scores, key=lambda x: self.model_scores[x]['r2_score'])
        self.best_model = self.models[best_model_name]
        self.best_model_name = best_model_name
        self.best_score = self.model_scores[best_model_name]['r2_score']
        
        log_info('select_best_model', f'Best model: {best_model_name} with R2: {self.best_score:.4f}')
        
        return self.best_model
    
    def save_model(self, model_path, preprocessor_path=None):
        """Save the best model and preprocessor."""
        import pickle
        
        # Save model
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': self.best_model,
                'model_name': self.best_model_name,
                'feature_columns': self.feature_columns,
            }, f)
        
        log_info('save_model', f'Best model saved to {model_path}')
        
        # Save preprocessor if provided
        if preprocessor_path:
            with open(preprocessor_path, 'wb') as f:
                pickle.dump({
                    'feature_columns': self.feature_columns,
                }, f)
            log_info('save_model', f'Preprocessor saved to {preprocessor_path}')
    
    def load_model(self, model_path):
        """Load a trained model."""
        import pickle
        
        with open(model_path, 'rb') as f:
            data = pickle.load(f)
            self.best_model = data['model']
            self.best_model_name = data['model_name']
            self.feature_columns = data['feature_columns']
        
        log_info('load_model', f'Model loaded from {model_path}')
    
    def get_model_summary(self):
        """Get summary of all models."""
        log_info('get_model_summary', 'Generating model summary')
        
        summary = {
            'best_model': self.best_model_name,
            'best_r2_score': float(self.best_score),
            'all_models': self.model_scores,
            'feature_importance': self.feature_importance
        }
        
        return summary
