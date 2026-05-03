"""
Feature engineering module for Bangalore Real Estate Intelligence System.
Creates domain-specific numeric and categorical features.
"""

import warnings

import numpy as np
import pandas as pd

from .config import INVESTMENT_CONFIG
from .logging_utils import log_info, log_warning

warnings.filterwarnings("ignore")


class FeatureEngineer:
    """Feature engineering helper for real estate data."""

    def __init__(self):
        self.locality_stats = {}
        self.area_density_stats = {}
        self.premium_areas = []
        self.feature_importance = {}

    def _safe_qcut(self, series, q, labels):
        """Bin a series safely even when there are too few unique values."""
        try:
            return pd.qcut(series, q=q, labels=labels, duplicates="drop")
        except ValueError:
            return pd.Series([labels[len(labels) // 2]] * len(series), index=series.index)

    def create_price_per_sqft_feature(self, df):
        log_info("create_price_per_sqft_feature", "Creating price per sqft feature")
        if "price" in df.columns and "total_sqft" in df.columns:
            df["price_per_sqft"] = ((df["price"] * 100000) / df["total_sqft"]).replace([np.inf, -np.inf], np.nan)
            df["price_per_sqft"] = df["price_per_sqft"].fillna(0)
        return df

    def create_bhk_category(self, df):
        log_info("create_bhk_category", "Creating BHK category feature")
        if "bhk" in df.columns:
            def categorize_bhk(bhk):
                if bhk <= 2:
                    return "2BHK_or_Less"
                if bhk == 3:
                    return "3BHK"
                return "4BHK_Plus"

            df["bhk_category"] = df["bhk"].apply(categorize_bhk)
            df["is_luxury"] = (df["bhk"] >= 4).astype(int)
        return df

    def create_total_rooms(self, df):
        log_info("create_total_rooms", "Creating total rooms feature")
        if "bhk" in df.columns and "bath" in df.columns:
            df["total_rooms"] = (df["bhk"] + df["bath"]).astype(int)
            df["room_category"] = self._safe_qcut(
                df["total_rooms"],
                q=4,
                labels=["Small", "Medium", "Large", "Extra_Large"],
            )
        return df

    def create_luxury_indicators(self, df):
        log_info("create_luxury_indicators", "Creating luxury indicators")
        if "price_per_sqft" in df.columns and "total_sqft" in df.columns:
            median_price_per_sqft = df["price_per_sqft"].median()
            df["is_premium_pricing"] = (df["price_per_sqft"] > median_price_per_sqft).astype(int)
            df["is_large_property"] = (df["total_sqft"] > df["total_sqft"].quantile(0.75)).astype(int)
            df["luxury_score"] = df["is_premium_pricing"] + df["is_large_property"]
        return df

    def create_area_density_features(self, df):
        log_info("create_area_density_features", "Creating area density features")
        if "location" in df.columns and "total_sqft" in df.columns and "price_per_sqft" in df.columns:
            self.locality_stats = (
                df.groupby("location")
                .agg(
                    locality_avg_price_per_sqft=("price_per_sqft", "mean"),
                    locality_std_price_per_sqft=("price_per_sqft", "std"),
                    locality_count=("price_per_sqft", "count"),
                    locality_avg_price=("price", "mean"),
                )
                .reset_index()
            )

            df = df.merge(
                self.locality_stats[["location", "locality_avg_price_per_sqft", "locality_count"]],
                on="location",
                how="left",
            )
            df["locality_avg_price_per_sqft"] = df["locality_avg_price_per_sqft"].fillna(df["price_per_sqft"].median())
            df["locality_count"] = df["locality_count"].fillna(0)
            df["area_density"] = self._safe_qcut(
                df["total_sqft"],
                q=4,
                labels=["Low_Density", "Medium_Low", "Medium_High", "High_Density"],
            )
        return df

    def create_locality_frequency_encoding(self, df):
        log_info("create_locality_frequency_encoding", "Creating frequency encoding")
        if "location" in df.columns:
            freq_encoding = df["location"].value_counts()
            df["location_frequency"] = df["location"].map(freq_encoding)
            df["location_frequency_norm"] = df["location_frequency"] / (df["location_frequency"].max() + 1e-6)
            df["location_frequency_category"] = self._safe_qcut(
                df["location_frequency"],
                q=5,
                labels=["Rare", "Low", "Medium", "High", "Very_High"],
            )
        return df

    def create_locality_popularity(self, df):
        log_info("create_locality_popularity", "Creating popularity score")
        if "location" in df.columns and "price" in df.columns:
            freq = df["location"].map(df["location"].value_counts())
            avg_price = df["location"].map(df.groupby("location")["price"].mean())
            freq_norm = (freq - freq.min()) / (freq.max() - freq.min() + 1e-6)
            price_norm = (avg_price - avg_price.min()) / (avg_price.max() - avg_price.min() + 1e-6)
            df["locality_popularity"] = (freq_norm * 0.6 + price_norm * 0.4).fillna(0)
            df["popularity_category"] = self._safe_qcut(
                df["locality_popularity"],
                q=5,
                labels=["Low_Popularity", "Below_Avg", "Average", "High", "Very_High"],
            )
        return df

    def create_property_segmentation(self, df):
        log_info("create_property_segmentation", "Creating property segmentation")
        if "price" in df.columns and "total_sqft" in df.columns:
            df["price_segment"] = self._safe_qcut(
                df["price"],
                q=5,
                labels=["Budget", "Economy", "Mid_Range", "Premium", "Luxury"],
            )
            df["area_segment"] = self._safe_qcut(
                df["total_sqft"],
                q=5,
                labels=["Small", "Medium_Small", "Medium", "Medium_Large", "Large"],
            )
        return df

    def create_premium_area_classification(self, df):
        log_info("create_premium_area_classification", "Creating premium area classification")
        if "location" in df.columns and "price" in df.columns:
            median_price = df["price"].median()
            location_means = df.groupby("location")["price"].mean()
            self.premium_areas = location_means[location_means > median_price].index.tolist()
            df["is_premium_area"] = df["location"].isin(self.premium_areas).astype(int)
        return df

    def create_affordability_metrics(self, df):
        log_info("create_affordability_metrics", "Creating affordability metrics")
        if "price_per_sqft" in df.columns:
            median_price_per_sqft = df["price_per_sqft"].median()
            df["affordability_score"] = (median_price_per_sqft / (df["price_per_sqft"] + 1e-6)).clip(0, 10)
            df["affordability_category"] = self._safe_qcut(
                df["affordability_score"],
                q=5,
                labels=["Not_Affordable", "Below_Avg", "Average", "Affordable", "Very_Affordable"],
            )
        return df

    def create_investment_score(self, df):
        log_info("create_investment_score", "Creating investment score")
        if "location" not in df.columns or "price_per_sqft" not in df.columns:
            return df

        location_scores = (
            df.groupby("location")
            .agg(
                avg_price_per_sqft=("price_per_sqft", "mean"),
                std_price_per_sqft=("price_per_sqft", "std"),
                avg_price=("price", "mean"),
                avg_area=("total_sqft", "mean"),
            )
            .reset_index()
        )

        location_scores["price_per_sqft_norm"] = 1 - self._minmax(location_scores["avg_price_per_sqft"])
        location_scores["price_norm"] = 1 - self._minmax(location_scores["avg_price"])
        location_scores["consistency_score"] = 1 - self._minmax(location_scores["std_price_per_sqft"].fillna(0))

        location_scores["investment_score"] = (
            location_scores["price_per_sqft_norm"] * INVESTMENT_CONFIG["weight_pricing"]
            + location_scores["price_norm"] * 0.2
            + location_scores["consistency_score"] * INVESTMENT_CONFIG["weight_consistency"]
            + (1 / (location_scores["avg_area"] + 1)) * 0.15
        )

        df = df.merge(location_scores[["location", "investment_score"]], on="location", how="left")
        df["investment_score"] = df["investment_score"].fillna(0)
        df["investment_category"] = self._safe_qcut(
            df["investment_score"],
            q=5,
            labels=["Poor_Investment", "Below_Avg", "Average", "Good_Investment", "Excellent_Investment"],
        )
        return df

    def create_time_features(self, df):
        log_info("create_time_features", "Creating time features")
        if "availability" in df.columns:
            availability = df["availability"].astype(str)
            df["is_ready_to_move"] = (availability == "Ready To Move").astype(int)
            df["availability_month"] = availability.apply(lambda value: value.split("-")[1] if len(value.split("-")) > 1 else "00")
            df["availability_year"] = availability.apply(
                lambda value: f"20{value.split('-')[0]}" if len(value.split("-")) > 0 and len(value.split("-")[0]) == 2 else "2020"
            )
            df["availability_month"] = pd.to_numeric(df["availability_month"], errors="coerce").fillna(0).astype(int)
            df["availability_year"] = pd.to_numeric(df["availability_year"], errors="coerce").fillna(2020).astype(int)
        return df

    def create_interaction_features(self, df):
        log_info("create_interaction_features", "Creating interaction features")
        if "bhk" in df.columns and "price_per_sqft" in df.columns:
            df["bhk_price_interaction"] = df["bhk"] * df["price_per_sqft"]
        if "total_rooms" in df.columns and "price" in df.columns:
            df["rooms_price_interaction"] = df["total_rooms"] * df["price"]
        if "total_sqft" in df.columns and "bhk" in df.columns:
            df["area_per_room"] = df["total_sqft"] / (df["bhk"] + 1)
        return df

    def create_all_features(self, df):
        log_info("create_all_features", "Starting complete feature engineering")
        df = self.create_price_per_sqft_feature(df)
        df = self.create_bhk_category(df)
        df = self.create_total_rooms(df)
        df = self.create_luxury_indicators(df)
        df = self.create_area_density_features(df)
        df = self.create_locality_frequency_encoding(df)
        df = self.create_locality_popularity(df)
        df = self.create_property_segmentation(df)
        df = self.create_premium_area_classification(df)
        df = self.create_affordability_metrics(df)
        df = self.create_investment_score(df)
        df = self.create_time_features(df)
        df = self.create_interaction_features(df)
        return df

    def get_feature_importance(self, df, target_column="price"):
        log_info("get_feature_importance", "Calculating feature importance")
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        if target_column not in numeric_columns:
            log_warning("get_feature_importance", f"Target column {target_column} not found")
            return {}

        correlations = {}
        for column in numeric_columns:
            if column != target_column:
                corr = df[[column, target_column]].corr().iloc[0, 1]
                correlations[column] = abs(corr) if pd.notna(corr) else 0.0

        self.feature_importance = dict(sorted(correlations.items(), key=lambda item: item[1], reverse=True))
        return self.feature_importance

    def _minmax(self, series):
        span = series.max() - series.min()
        if pd.isna(span) or span == 0:
            return pd.Series([0.5] * len(series), index=series.index)
        return (series - series.min()) / (span + 1e-6)
