"""
Data Processing Module
Handles data loading, cleaning, and preprocessing
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


# Survey data mappings
EDUCATION_LEVELS = {
    0: "Less than High School",
    1: "High School Degree",
    2: "Some College",
    3: "4-Year College Degree",
    4: "Master's/Doctoral/Professional"
}

CAR_MAKES = {
    1: "BMW", 2: "Buick", 3: "Cadillac", 4: "Chevrolet", 5: "Chrysler",
    6: "Dodge", 7: "Ford", 8: "Honda", 9: "Hyundai", 10: "Jeep",
    11: "Kia", 12: "Lincoln", 13: "Mazda", 14: "Mercedes Benz", 15: "Mitsubishi",
    16: "Nissan", 17: "Ram", 18: "Subaru", 19: "Toyota", 20: "None of the above"
}

REGIONS = {
    0: "New England",
    1: "Mid-Atlantic",
    2: "East North Central",
    3: "West North Central",
    4: "South Atlantic",
    5: "East South Central",
    6: "West South Central",
    7: "Mountain",
    8: "Pacific"
}

COMPUTER_BRANDS = {
    0: "Acer",
    1: "Sony"
}

AGE_GROUPS = {
    "Young (18-30)": (18, 30),
    "Middle-aged (31-50)": (31, 50),
    "Senior (51-65)": (51, 65),
    "Elderly (65+)": (65, 100)
}

SALARY_BRACKETS = {
    "Low (<$50K)": (0, 50000),
    "Medium ($50K-$100K)": (50000, 100000),
    "High ($100K-$150K)": (100000, 150000),
    "Premium (>$150K)": (150000, float('inf'))
}


class DataProcessor:
    """Handles survey data loading, cleaning, and preprocessing."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.raw_data: Optional[pd.DataFrame] = None
        self.processed_data: Optional[pd.DataFrame] = None
        self.data_quality_report: Dict = {}

    def load_data(self) -> pd.DataFrame:
        """Load survey data from CSV file."""
        self.raw_data = pd.read_csv(self.filepath)
        return self.raw_data

    def clean_data(self) -> pd.DataFrame:
        """Clean and preprocess the data."""
        if self.raw_data is None:
            self.load_data()

        df = self.raw_data.copy()

        # Check for missing values
        self.data_quality_report['missing_values'] = df.isnull().sum().to_dict()
        self.data_quality_report['total_rows'] = len(df)
        self.data_quality_report['total_columns'] = len(df.columns)

        # Remove duplicates
        duplicates = df.duplicated().sum()
        self.data_quality_report['duplicates_removed'] = duplicates
        df = df.drop_duplicates()

        # Map categorical values to readable names
        df['education_label'] = df['elevel'].map(EDUCATION_LEVELS)
        df['car_label'] = df['car'].map(CAR_MAKES)
        df['region_label'] = df['zipcode'].map(REGIONS)
        df['brand_label'] = df['brand'].map(COMPUTER_BRANDS)

        # Create age groups
        def get_age_group(age):
            for group, (low, high) in AGE_GROUPS.items():
                if low <= age <= high:
                    return group
            return "Unknown"

        df['age_group'] = df['age'].apply(get_age_group)

        # Create salary brackets
        def get_salary_bracket(salary):
            for bracket, (low, high) in SALARY_BRACKETS.items():
                if low <= salary < high:
                    return bracket
            return "Unknown"

        df['salary_bracket'] = df['salary'].apply(get_salary_bracket)

        self.processed_data = df
        return self.processed_data

    def get_data_summary(self) -> Dict:
        """Generate summary statistics of the processed data."""
        if self.processed_data is None:
            self.clean_data()

        df = self.processed_data
        summary = {
            'total_responses': len(df),
            'salary_stats': {
                'mean': df['salary'].mean(),
                'median': df['salary'].median(),
                'min': df['salary'].min(),
                'max': df['salary'].max(),
                'std': df['salary'].std()
            },
            'age_stats': {
                'mean': df['age'].mean(),
                'median': df['age'].median(),
                'min': df['age'].min(),
                'max': df['age'].max()
            },
            'education_distribution': df['education_label'].value_counts().to_dict(),
            'region_distribution': df['region_label'].value_counts().to_dict(),
            'car_distribution': df['car_label'].value_counts().to_dict(),
            'brand_preference': df['brand_label'].value_counts().to_dict(),
            'credit_stats': {
                'mean': df['credit'].mean(),
                'median': df['credit'].median(),
                'min': df['credit'].min(),
                'max': df['credit'].max()
            }
        }
        return summary

    def get_quality_report(self) -> Dict:
        """Return data quality report."""
        return self.data_quality_report

    def segment_data(self, segment_by: str) -> Dict[str, pd.DataFrame]:
        """Segment data by a specific column."""
        if self.processed_data is None:
            self.clean_data()

        segments = {}
        for value in self.processed_data[segment_by].unique():
            segments[str(value)] = self.processed_data[self.processed_data[segment_by] == value]
        return segments