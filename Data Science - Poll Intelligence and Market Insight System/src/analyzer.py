"""
Analytical Engine Module
Performs statistical analysis and segmentation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SegmentAnalysis:
    """Container for segment analysis results."""
    segment_name: str
    segment_size: int
    brand_preference: Dict[str, float]
    dominant_brand: str
    dominant_share: float
    avg_salary: float
    avg_age: float
    top_car: str


class Analyzer:
    """Analytical engine for survey data."""

    def __init__(self, processed_data: pd.DataFrame):
        self.data = processed_data
        self.analysis_results: Dict = {}

    def compute_distribution(self, column: str) -> Dict[str, float]:
        """Compute percentage distribution for a column."""
        counts = self.data[column].value_counts()
        percentages = (counts / counts.sum() * 100).round(2)
        return percentages.to_dict()

    def segment_analysis(self, segment_column: str, target_column: str = 'brand_label') -> List[SegmentAnalysis]:
        """Analyze preferences by segment."""
        results = []

        for segment_value in self.data[segment_column].unique():
            segment_data = self.data[self.data[segment_column] == segment_value]
            segment_size = len(segment_data)

            # Brand preference distribution
            brand_counts = segment_data[target_column].value_counts()
            brand_pcts = (brand_counts / segment_size * 100).round(2).to_dict()

            # Find dominant brand
            dominant_brand = brand_counts.idxmax() if len(brand_counts) > 0 else "N/A"
            dominant_share = brand_pcts.get(dominant_brand, 0)

            # Stats
            avg_salary = segment_data['salary'].mean()
            avg_age = segment_data['age'].mean()
            top_car = segment_data['car_label'].value_counts().idxmax() if len(segment_data) > 0 else "N/A"

            results.append(SegmentAnalysis(
                segment_name=str(segment_value),
                segment_size=segment_size,
                brand_preference=brand_pcts,
                dominant_brand=dominant_brand,
                dominant_share=dominant_share,
                avg_salary=avg_salary,
                avg_age=avg_age,
                top_car=top_car
            ))

        return results

    def compare_segments(self, segment_column: str, target_column: str = 'brand_label') -> Dict:
        """Compare preferences across segments."""
        segment_results = self.segment_analysis(segment_column, target_column)

        comparison = {
            'segments': [],
            'preferences': {},
            'insights': []
        }

        for seg in segment_results:
            comparison['segments'].append({
                'name': seg.segment_name,
                'size': seg.segment_size,
                'dominant_brand': seg.dominant_brand,
                'dominant_share': seg.dominant_share
            })

            for brand, share in seg.brand_preference.items():
                if brand not in comparison['preferences']:
                    comparison['preferences'][brand] = []
                comparison['preferences'][brand].append({
                    'segment': seg.segment_name,
                    'share': share
                })

        return comparison

    def correlation_analysis(self, col1: str, col2: str) -> float:
        """Compute correlation between two columns."""
        if self.data[col1].dtype in ['int64', 'float64'] and self.data[col2].dtype in ['int64', 'float64']:
            return self.data[col1].corr(self.data[col2])
        return 0.0

    def get_top_performers(self, column: str, n: int = 5) -> pd.DataFrame:
        """Get top n categories by count."""
        return self.data[column].value_counts().head(n)

    def compute_statistics(self, column: str) -> Dict:
        """Compute basic statistics for a numeric column."""
        if column not in self.data.columns:
            return {}

        series = self.data[column]
        if series.dtype not in ['int64', 'float64']:
            return {'count': series.value_counts().to_dict()}

        return {
            'mean': series.mean(),
            'median': series.median(),
            'std': series.std(),
            'min': series.min(),
            'max': series.max(),
            'q25': series.quantile(0.25),
            'q75': series.quantile(0.75)
        }

    def cross_tabulation(self, col1: str, col2: str, normalize: bool = True) -> pd.DataFrame:
        """Create cross-tabulation between two columns."""
        crosstab = pd.crosstab(self.data[col1], self.data[col2])
        if normalize:
            crosstab = crosstab.div(crosstab.sum(axis=1), axis=0) * 100
        return crosstab.round(2)

    def preference_by_segment(self, segment_col: str, preference_col: str) -> pd.DataFrame:
        """Compute preference distribution by segment."""
        grouped = self.data.groupby(segment_col)[preference_col].value_counts(normalize=True) * 100
        return grouped.round(2).unstack(fill_value=0)