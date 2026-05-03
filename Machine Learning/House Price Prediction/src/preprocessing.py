"""
Data Preprocessing Module for Bangalore Real Estate Intelligence System.
Handles data cleaning, missing value imputation, outlier detection, and preprocessing.
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from .logging_utils import log_info, log_error, log_warning


class DataPreprocessor:
    """
    Advanced data preprocessing class for real estate data.
    Handles all data cleaning and preprocessing tasks.
    """
    
    def __init__(self, random_state=42):
        self.random_state = random_state
        self.feature_stats = {}
        self.outlier_bounds = {}
        
    def load_data(self, file_path):
        """Load data from CSV file."""
        try:
            log_info('load_data', f'Loading data from {file_path}')
            df = pd.read_csv(file_path)
            log_info('load_data', f'Data loaded successfully. Shape: {df.shape}')
            return df
        except Exception as e:
            log_error('load_data', f'Error loading data: {str(e)}')
            raise
    
    def initial_analysis(self, df):
        """Perform initial data analysis."""
        log_info('initial_analysis', 'Starting initial data analysis')
        
        analysis = {
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'missing_percentage': (df.isnull().sum() / len(df) * 100).to_dict(),
            'duplicates': df.duplicated().sum(),
            'numeric_stats': df.describe().to_dict() if len(df.select_dtypes(include=np.number).columns) > 0 else {}
        }
        
        log_info('initial_analysis', f'Analysis complete. Missing values: {df.isnull().sum().sum()}')
        return analysis
    
    def clean_column_names(self, df):
        """Clean column names - remove extra spaces."""
        log_info('clean_column_names', 'Cleaning column names')
        
        df.columns = df.columns.str.strip().str.lower().str.replace('  ', ' ').str.replace('  ', ' ')
        
        # Specific cleaning for this dataset
        df.columns = df.columns.str.replace('  ', ' ')
        
        log_info('clean_column_names', 'Column names cleaned')
        return df
    
    def handle_missing_values(self, df):
        """Handle missing values intelligently."""
        log_info('handle_missing_values', 'Starting missing value handling')

        missing_before = df.isnull().sum().sum()

        categorical_defaults = {
            'society': 'Unknown',
            'location': 'Unknown',
            'area_type': 'Unknown',
            'availability': 'Unknown'
        }

        for column, default_value in categorical_defaults.items():
            if column in df.columns:
                df[column] = df[column].fillna(default_value)

        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        for column in numeric_columns:
            median_value = df[column].median()
            if pd.isna(median_value):
                median_value = 0
            df[column] = df[column].fillna(median_value)

        missing_after = df.isnull().sum().sum()
        log_info('handle_missing_values', f'Missing values reduced from {missing_before} to {missing_after}')
        
        return df
    
    def handle_duplicates(self, df):
        """Handle duplicate rows."""
        log_info('handle_duplicates', 'Checking for duplicates')
        
        duplicates_before = df.duplicated().sum()
        
        # Remove exact duplicates
        df = df.drop_duplicates()
        
        duplicates_after = df.duplicated().sum()
        log_info('handle_duplicates', f'Removed {duplicates_before} duplicate rows')
        
        return df
    
    def clean_square_footage(self, df):
        """Clean and standardize square footage values."""
        log_info('clean_square_footage', 'Starting square footage cleaning')
        
        if 'total_sqft' not in df.columns:
            log_warning('clean_square_footage', 'total_sqft column not found')
            return df
        
        def parse_sqft(value):
            """Parse various square footage formats."""
            if pd.isna(value):
                return np.nan
            
            value = str(value).strip()
            
            # Handle ranges (e.g., "2100 - 2850")
            if '-' in value:
                parts = value.split('-')
                try:
                    return (float(parts[0].strip()) + float(parts[1].strip())) / 2
                except:
                    return np.nan
            
            # Handle "Sq. Meter" conversion
            if 'Sq. Meter' in value or 'Sq.Meter' in value:
                try:
                    num = float(value.replace('Sq. Meter', '').replace('Sq.Meter', '').strip())
                    return num * 10.7639  # Convert to sq ft
                except:
                    return np.nan
            
            # Handle "Sq. Yards" conversion
            if 'Sq. Yards' in value or 'Sq.Yards' in value:
                try:
                    num = float(value.replace('Sq. Yards', '').replace('Sq.Yards', '').strip())
                    return num * 9  # Convert to sq ft
                except:
                    return np.nan
            
            # Handle "Acres" conversion
            if 'Acres' in value:
                try:
                    num = float(value.replace('Acres', '').strip())
                    return num * 43560  # Convert to sq ft
                except:
                    return np.nan
            
            # Handle "Sq. Feet" or just numbers
            try:
                return float(value.replace('Sq. Feet', '').replace('Sq.Feet', '').strip())
            except:
                return np.nan
        
        # Apply parsing
        df['total_sqft'] = df['total_sqft'].apply(parse_sqft)
        
        # Remove rows with invalid sqft
        df = df[df['total_sqft'].notna()]
        
        log_info('clean_square_footage', f'Square footage cleaned. Rows remaining: {len(df)}')
        
        return df
    
    def extract_bhk(self, df):
        """Extract BHK (Bedroom count) from size column."""
        log_info('extract_bhk', 'Extracting BHK values')
        
        if 'size' not in df.columns:
            log_warning('extract_bhk', 'size column not found')
            return df
        
        def extract_bhk_value(size):
            """Extract BHK number from size string."""
            if pd.isna(size):
                return np.nan
            
            size = str(size).upper().strip()
            
            # Extract number from various formats
            import re
            match = re.search(r'(\d+)\s*(BHK|BEDROOM)', size)
            if match:
                return int(match.group(1))
            
            # Handle "1 RK" format
            if 'RK' in size:
                return 1
            
            return np.nan
        
        df['bhk'] = df['size'].apply(extract_bhk_value)
        
        # Remove rows with invalid BHK
        df = df[df['bhk'].notna()]
        
        log_info('extract_bhk', f'BHK extracted. BHK distribution: {df["bhk"].value_counts().to_dict()}')
        
        return df
    
    def calculate_price_per_sqft(self, df):
        """Calculate price per square foot."""
        log_info('calculate_price_per_sqft', 'Calculating price per sqft')
        
        if 'price' in df.columns and 'total_sqft' in df.columns:
            # Price is in lakhs, convert to rupees for per sqft calculation
            df['price_per_sqft'] = (df['price'] * 100000) / df['total_sqft']
            df['price_per_sqft'] = df['price_per_sqft'].round(2)
            
            log_info('calculate_price_per_sqft', f'Price per sqft calculated. Range: {df["price_per_sqft"].min():.2f} - {df["price_per_sqft"].max():.2f}')
        
        return df
    
    def calculate_total_rooms(self, df):
        """Calculate total rooms (BHK + bathrooms)."""
        log_info('calculate_total_rooms', 'Calculating total rooms')
        
        if 'bhk' in df.columns and 'bath' in df.columns:
            df['total_rooms'] = df['bhk'] + df['bath']
            df['total_rooms'] = df['total_rooms'].astype(int)
            
            log_info('calculate_total_rooms', f'Total rooms calculated. Range: {df["total_rooms"].min()} - {df["total_rooms"].max()}')
        
        return df
    
    def detect_outliers(self, df, columns=None, method='iqr', threshold=1.5):
        """Detect outliers using IQR or Z-score method."""
        log_info('detect_outliers', f'Detecting outliers using {method} method')
        
        if columns is None:
            columns = ['total_sqft', 'price', 'bhk', 'bath', 'balcony']
        
        outlier_mask = pd.Series([True] * len(df), index=df.index)
        
        for col in columns:
            if col not in df.columns:
                continue
            
            col_data = df[col].dropna()
            
            if method == 'iqr':
                Q1 = col_data.quantile(0.25)
                Q3 = col_data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
            else:  # z-score
                mean = col_data.mean()
                std = col_data.std()
                lower_bound = mean - threshold * std
                upper_bound = mean + threshold * std
            
            # Store bounds for later use
            self.outlier_bounds[col] = {'lower': lower_bound, 'upper': upper_bound}
            
            # Update outlier mask
            col_outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
            outlier_mask = outlier_mask & ~col_outliers
        
        outliers_removed = (~outlier_mask).sum()
        df_clean = df[outlier_mask].copy()
        
        log_info('detect_outliers', f'Removed {outliers_removed} outliers. Rows remaining: {len(df_clean)}')
        
        return df_clean, outlier_mask
    
    def preprocess(self, df, remove_outliers=True, encode=True, scale=True):
        """Run complete preprocessing pipeline."""
        log_info('preprocess', 'Starting complete preprocessing pipeline')
        
        original_rows = len(df)
        
        # Step 1: Clean column names
        df = self.clean_column_names(df)
        
        # Step 2: Handle missing values
        df = self.handle_missing_values(df)
        
        # Step 3: Handle duplicates
        df = self.handle_duplicates(df)
        
        # Step 4: Clean square footage
        df = self.clean_square_footage(df)
        
        # Step 5: Extract BHK
        df = self.extract_bhk(df)
        
        # Step 6: Calculate derived features
        df = self.calculate_price_per_sqft(df)
        df = self.calculate_total_rooms(df)

        # Step 7: Remove outliers
        if remove_outliers:
            df, _ = self.detect_outliers(df)

        log_info('preprocess', f'Preprocessing complete. Rows: {original_rows} -> {len(df)}')

        return df
    
    def save_preprocessor(self, path):
        """Save preprocessor state."""
        import pickle
        with open(path, 'wb') as f:
            pickle.dump({
                'version': 2,
                'outlier_bounds': self.outlier_bounds,
                'feature_stats': self.feature_stats
            }, f)
        log_info('save_preprocessor', f'Preprocessor saved to {path}')
    
    def load_preprocessor(self, path):
        """Load preprocessor state."""
        import pickle
        needs_upgrade = False
        with open(path, 'rb') as f:
            data = pickle.load(f)

        if isinstance(data, dict):
            # Backward-compatible with older preprocessor.pkl files.
            self.outlier_bounds = data.get('outlier_bounds') or {}
            self.feature_stats = data.get('feature_stats') or {}
            needs_upgrade = 'outlier_bounds' not in data or 'feature_stats' not in data or data.get('version') != 2
        else:
            self.outlier_bounds = getattr(data, 'outlier_bounds', {}) or {}
            self.feature_stats = getattr(data, 'feature_stats', {}) or {}

        if needs_upgrade:
            # Rewrite legacy artifacts into the current format so future app starts are clean.
            self.save_preprocessor(path)

        log_info('load_preprocessor', f'Preprocessor loaded from {path}')
