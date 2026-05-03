"""
Data Loading and Initial Analysis Script.
Provides comprehensive data exploration and analysis.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Add src to path
import sys
sys.path.append(str(Path(__file__).parent / 'src'))

from config import RAW_DATA_PATH


def load_data():
    """Load the Bengaluru house price dataset."""
    print("Loading data...")
    df = pd.read_csv(RAW_DATA_PATH)
    print(f"Data loaded successfully! Shape: {df.shape}")
    return df


def initial_analysis(df):
    """Perform initial data analysis."""
    print("\n" + "=" * 80)
    print("INITIAL DATA ANALYSIS")
    print("=" * 80)
    
    # Basic information
    print("\n1. Dataset Overview:")
    print(f"   Total Rows: {df.shape[0]}")
    print(f"   Total Columns: {df.shape[1]}")
    
    # Column names
    print("\n2. Column Names:")
    for i, col in enumerate(df.columns, 1):
        print(f"   {i}. {col}")
    
    # Data types
    print("\n3. Data Types:")
    print(df.dtypes.to_string())
    
    # Missing values
    print("\n4. Missing Values:")
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    missing_df = pd.DataFrame({
        'Missing Count': missing,
        'Percentage': missing_pct
    })
    print(missing_df.to_string())
    
    # Duplicate rows
    print(f"\n5. Duplicate Rows: {df.duplicated().sum()}")
    
    return df


def categorical_analysis(df):
    """Analyze categorical variables."""
    print("\n" + "=" * 80)
    print("CATEGORICAL VARIABLE ANALYSIS")
    print("=" * 80)
    
    categorical_cols = df.select_dtypes(include=['object']).columns
    
    for col in categorical_cols:
        print(f"\n{col.upper()}:")
        print(f"   Unique Values: {df[col].nunique()}")
        print(f"   Top 5 Values:")
        
        value_counts = df[col].value_counts().head(5)
        for value, count in value_counts.items():
            pct = (count / len(df) * 100).round(2)
            print(f"      {value}: {count} ({pct}%)")


def numerical_analysis(df):
    """Analyze numerical variables."""
    print("\n" + "=" * 80)
    print("NUMERICAL VARIABLE ANALYSIS")
    print("=" * 80)
    
    numerical_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numerical_cols:
        print(f"\n{col.upper()}:")
        stats = df[col].describe()
        print(f"   Mean: {stats['mean']:.2f}")
        print(f"   Median: {stats['50%']:.2f}")
        print(f"   Std: {stats['std']:.2f}")
        print(f"   Min: {stats['min']:.2f}")
        print(f"   Max: {stats['max']:.2f}")
        print(f"   25th Percentile: {stats['25%']:.2f}")
        print(f"   75th Percentile: {stats['75%']:.2f}")


def square_footage_analysis(df):
    """Analyze square footage data."""
    print("\n" + "=" * 80)
    print("SQUARE FOOTAGE ANALYSIS")
    print("=" * 80)
    
    if 'total_sqft' not in df.columns:
        print("total_sqft column not found!")
        return
    
    print("\nSquare Footage Statistics:")
    print(df['total_sqft'].describe().to_string())
    
    # Check for ranges
    range_count = df['total_sqft'].astype(str).str.contains('-').sum()
    print(f"\nProperties with range values: {range_count}")
    
    # Sample ranges
    if range_count > 0:
        print("\nSample range values:")
        range_values = df[df['total_sqft'].astype(str).str.contains('-')]['total_sqft'].head(10)
        for val in range_values:
            print(f"   {val}")
    
    # Check for unit conversions
    unit_values = df[df['total_sqft'].astype(str).str.contains('Sq. Meter|Sq. Yards|Acres', case=False, na=False)]
    if len(unit_values) > 0:
        print(f"\nProperties with unit conversions: {len(unit_values)}")


def price_analysis(df):
    """Analyze price data."""
    print("\n" + "=" * 80)
    print("PRICE ANALYSIS")
    print("=" * 80)
    
    if 'price' not in df.columns:
        print("price column not found!")
        return
    
    print("\nPrice Statistics:")
    print(df['price'].describe().to_string())
    
    # Price distribution
    print("\nPrice Distribution:")
    print(f"   Skewness: {df['price'].skew():.2f}")
    print(f"   Kurtosis: {df['price'].kurtosis():.2f}")
    
    # Price ranges
    print("\nPrice Ranges:")
    bins = [0, 50, 100, 200, 500, 1000, 5000]
    labels = ['<50L', '50-100L', '100-200L', '200-500L', '500L-1Cr', '>1Cr']
    df['price_range'] = pd.cut(df['price'], bins=bins, labels=labels)
    print(df['price_range'].value_counts().to_string())


def location_analysis(df):
    """Analyze location data."""
    print("\n" + "=" * 80)
    print("LOCATION ANALYSIS")
    print("=" * 80)
    
    if 'location' not in df.columns:
        print("location column not found!")
        return
    
    print(f"\nTotal Unique Locations: {df['location'].nunique()}")
    
    print("\nTop 20 Locations by Property Count:")
    top_locations = df['location'].value_counts().head(20)
    for location, count in top_locations.items():
        pct = (count / len(df) * 100).round(2)
        print(f"   {location}: {count} ({pct}%)")


def size_analysis(df):
    """Analyze size (BHK) data."""
    print("\n" + "=" * 80)
    print("SIZE (BHK) ANALYSIS")
    print("=" * 80)
    
    if 'size' not in df.columns:
        print("size column not found!")
        return
    
    print("\nBHK Distribution:")
    size_counts = df['size'].value_counts()
    for size, count in size_counts.items():
        pct = (count / len(df) * 100).round(2)
        print(f"   {size}: {count} ({pct}%)")


def area_type_analysis(df):
    """Analyze area type data."""
    print("\n" + "=" * 80)
    print("AREA TYPE ANALYSIS")
    print("=" * 80)
    
    if 'area_type' not in df.columns:
        print("area_type column not found!")
        return
    
    print("\nArea Type Distribution:")
    area_counts = df['area_type'].value_counts()
    for area_type, count in area_counts.items():
        pct = (count / len(df) * 100).round(2)
        print(f"   {area_type}: {count} ({pct}%)")


def correlation_analysis(df):
    """Perform correlation analysis."""
    print("\n" + "=" * 80)
    print("CORRELATION ANALYSIS")
    print("=" * 80)
    
    # Select numerical columns
    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Calculate correlation matrix
    corr_matrix = df[numerical_cols].corr()
    
    print("\nCorrelation with Price:")
    price_corr = corr_matrix['price'].sort_values(ascending=False)
    print(price_corr.to_string())


def data_quality_report(df):
    """Generate comprehensive data quality report."""
    print("\n" + "=" * 80)
    print("DATA QUALITY REPORT")
    print("=" * 80)
    
    report = {
        'Total Rows': len(df),
        'Total Columns': len(df.columns),
        'Missing Values': df.isnull().sum().sum(),
        'Missing Percentage': (df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100).round(2),
        'Duplicate Rows': df.duplicated().sum(),
        'Duplicate Percentage': (df.duplicated().sum() / len(df) * 100).round(2)
    }
    
    print("\nData Quality Metrics:")
    for metric, value in report.items():
        print(f"   {metric}: {value}")


def main():
    """Main function."""
    print("\n" + "=" * 80)
    print("BANGALORE REAL ESTATE - DATA EXPLORATION")
    print("=" * 80)
    
    # Load data
    df = load_data()
    
    # Run all analyses
    initial_analysis(df)
    categorical_analysis(df)
    numerical_analysis(df)
    square_footage_analysis(df)
    price_analysis(df)
    location_analysis(df)
    size_analysis(df)
    area_type_analysis(df)
    correlation_analysis(df)
    data_quality_report(df)
    
    print("\n" + "=" * 80)
    print("DATA EXPLORATION COMPLETE!")
    print("=" * 80)
    
    return df


if __name__ == "__main__":
    df = main()
