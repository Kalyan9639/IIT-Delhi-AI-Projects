"""
Insight Engine Module
Generates actionable business insights from survey data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class Insight:
    """Container for a single insight."""
    category: str  # e.g., "Brand Preference", "Demographics"
    title: str
    finding: str
    implication: str
    confidence: str  # High, Medium, Low
    segment: str = "Overall"


class InsightEngine:
    """Generates actionable business insights from survey data."""

    def __init__(self, data: pd.DataFrame, analyzer):
        self.data = data
        self.analyzer = analyzer
        self.insights: List[Insight] = []

    def generate_all_insights(self) -> List[Insight]:
        """Generate all insights from the data."""
        self.insights = []

        # Generate various insight categories
        self._analyze_brand_dominance()
        self._analyze_demographic_patterns()
        self._analyze_regional_differences()
        self._analyze_economic_factors()
        self._analyze_car_preferences()
        self._identify_opportunities()
        self._identify_strengths_weaknesses()

        return self.insights

    def _analyze_brand_dominance(self):
        """Analyze overall brand preference patterns."""
        brand_dist = self.data['brand_label'].value_counts(normalize=True) * 100
        dominant = brand_dist.idxmax()
        dominant_share = brand_dist.max()

        if dominant_share > 55:
            confidence = "High"
            implication = f"The market shows clear preference for {dominant}. Marketing efforts should reinforce this position."
        elif dominant_share > 52:
            confidence = "Medium"
            implication = f"{dominant} has a slight edge. Consider targeted campaigns to expand market share."
        else:
            confidence = "Low"
            implication = "The market is nearly evenly split. Both brands have equal opportunity for growth."

        self.insights.append(Insight(
            category="Brand Preference",
            title="Overall Market Share",
            finding=f"{dominant} dominates with {dominant_share:.1f}% market share",
            implication=implication,
            confidence=confidence,
            segment="Overall"
        ))

    def _analyze_demographic_patterns(self):
        """Analyze brand preference by demographic segments."""
        # Age group analysis
        age_analysis = self.analyzer.segment_analysis('age_group')

        young_pref = None
        young_share = 0
        senior_pref = None
        senior_share = 0

        for seg in age_analysis:
            if 'Young' in seg.segment_name:
                young_pref = seg.dominant_brand
                young_share = seg.dominant_share
            elif 'Senior' in seg.segment_name or 'Elderly' in seg.segment_name:
                senior_pref = seg.dominant_brand
                senior_share = seg.dominant_share

        if young_pref and senior_pref and young_pref != senior_pref:
            self.insights.append(Insight(
                category="Demographics",
                title="Age-Based Preference Shift",
                finding=f"Young users prefer {young_pref} ({young_share:.1f}%), while seniors prefer {senior_pref} ({senior_share:.1f}%)",
                implication="Age-specific marketing strategies recommended. Target youth with modern messaging.",
                confidence="High" if abs(young_share - senior_share) > 10 else "Medium",
                segment="Age Groups"
            ))

        # Education level analysis
        edu_analysis = self.analyzer.segment_analysis('education_label')
        edu_insights = []

        for seg in edu_analysis:
            if seg.segment_size > 100:  # Only consider significant segments
                edu_insights.append(f"{seg.segment_name}: {seg.dominant_brand} ({seg.dominant_share:.1f}%)")

        if len(edu_insights) >= 2:
            self.insights.append(Insight(
                category="Demographics",
                title="Education-Based Preferences",
                finding=" | ".join(edu_insights[:3]),
                implication="Tailor messaging based on education level. Higher education segments may respond to technical specs.",
                confidence="Medium",
                segment="Education Level"
            ))

    def _analyze_regional_differences(self):
        """Analyze regional preference patterns."""
        region_analysis = self.analyzer.segment_analysis('region_label')

        # Find strongest and weakest regions
        strongest_region = None
        strongest_share = 0
        weakest_region = None
        weakest_share = 100

        for seg in region_analysis:
            if seg.dominant_share > strongest_share:
                strongest_share = seg.dominant_share
                strongest_region = seg.segment_name
            if seg.dominant_share < weakest_share and seg.segment_size > 50:
                weakest_share = seg.dominant_share
                weakest_region = seg.segment_name

        if strongest_region and weakest_region:
            self.insights.append(Insight(
                category="Geography",
                title="Regional Market Strength",
                finding=f"Strongest region: {strongest_region} ({strongest_share:.1f}%), Weakest: {weakest_region} ({weakest_share:.1f}%)",
                implication=f"Focus expansion efforts in {weakest_region}. Maintain dominance in {strongest_region}.",
                confidence="High",
                segment="Regions"
            ))

        # Identify regional patterns
        regions_by_pref = {}
        for seg in region_analysis:
            brand = seg.dominant_brand
            if brand not in regions_by_pref:
                regions_by_pref[brand] = []
            regions_by_pref[brand].append(seg.segment_name)

        if len(regions_by_pref) > 1:
            self.insights.append(Insight(
                category="Geography",
                title="Regional Brand Affinity",
                finding=f"Geographic split detected across regions",
                implication="Regional marketing strategies recommended. Consider local partnerships.",
                confidence="Medium",
                segment="Regions"
            ))

    def _analyze_economic_factors(self):
        """Analyze relationship between economic factors and preferences."""
        salary_analysis = self.analyzer.segment_analysis('salary_bracket')

        low_pref = None
        high_pref = None

        for seg in salary_analysis:
            if 'Low' in seg.segment_name:
                low_pref = seg.dominant_brand
            elif 'Premium' in seg.segment_name or 'High' in seg.segment_name:
                high_pref = seg.dominant_brand

        if low_pref and high_pref and low_pref != high_pref:
            self.insights.append(Insight(
                category="Economics",
                title="Income-Based Preference",
                finding=f"Lower income groups prefer {low_pref}, higher income prefer {high_pref}",
                implication="Price positioning strategy differs by segment. Consider tiered product offerings.",
                confidence="High",
                segment="Income Levels"
            ))
        elif low_pref and high_pref:
            self.insights.append(Insight(
                category="Economics",
                title="Income-Neutral Preference",
                finding="Brand preference is consistent across income levels",
                implication="Value proposition resonates equally across economic segments.",
                confidence="Medium",
                segment="Income Levels"
            ))

        # Credit analysis
        high_credit = self.data[self.data['credit'] > self.data['credit'].median()]
        low_credit = self.data[self.data['credit'] <= self.data['credit'].median()]

        high_credit_pref = high_credit['brand_label'].value_counts(normalize=True).idxmax()
        low_credit_pref = low_credit['brand_label'].value_counts(normalize=True).idxmax()

        self.insights.append(Insight(
            category="Economics",
            title="Credit Availability Impact",
            finding=f"High credit users prefer {high_credit_pref}, low credit users prefer {low_credit_pref}",
            implication="Financing options may influence purchase decisions.",
            confidence="Medium",
            segment="Credit Levels"
        ))

    def _analyze_car_preferences(self):
        """Analyze relationship between car ownership and brand preference."""
        # Top 5 car brands
        top_cars = self.data['car_label'].value_counts().head(5)

        car_brand_pref = {}
        for car in top_cars.index:
            car_users = self.data[self.data['car_label'] == car]
            pref_brand = car_users['brand_label'].value_counts(normalize=True).idxmax()
            share = car_users['brand_label'].value_counts(normalize=True).max() * 100
            car_brand_pref[car] = (pref_brand, share)

        insights_text = [f"{car}: {pref} ({share:.1f}%)" for car, (pref, share) in list(car_brand_pref.items())[:3]]

        self.insights.append(Insight(
            category="Lifestyle",
            title="Car-Computer Brand Correlation",
            finding=" | ".join(insights_text),
            implication="Car brand preferences may indicate lifestyle segments for targeted marketing.",
            confidence="Medium",
            segment="Car Owners"
        ))

    def _identify_opportunities(self):
        """Identify market opportunities."""
        # Find underserved segments
        region_analysis = self.analyzer.segment_analysis('region_label')

        opportunities = []
        for seg in region_analysis:
            if seg.dominant_share < 52 and seg.segment_size > 100:
                opportunities.append(seg.segment_name)

        if opportunities:
            self.insights.append(Insight(
                category="Opportunities",
                title="Expansion Opportunities",
                finding=f"Regions with competitive market: {', '.join(opportunities[:3])}",
                implication="These markets are not yet dominated. Investment could yield high returns.",
                confidence="High",
                segment="Regions"
            ))

        # Age group opportunities
        age_analysis = self.analyzer.segment_analysis('age_group')
        for seg in age_analysis:
            if seg.segment_size > 500 and seg.dominant_share < 48:
                self.insights.append(Insight(
                    category="Opportunities",
                    title="Age Segment Opportunity",
                    finding=f"{seg.segment_name} segment is highly competitive ({seg.dominant_share:.1f}%)",
                    implication="Targeted campaigns for this age group could shift market share.",
                    confidence="Medium",
                    segment=seg.segment_name
                ))
                break

    def _identify_strengths_weaknesses(self):
        """Identify strengths and weaknesses in market position."""
        brand_dist = self.data['brand_label'].value_counts(normalize=True) * 100

        # Overall market position
        for brand in brand_dist.index:
            share = brand_dist[brand]
            if share > 55:
                self.insights.append(Insight(
                    category="Market Position",
                    title=f"{brand} Strength",
                    finding=f"{brand} holds dominant market position at {share:.1f}%",
                    implication="Focus on retention and expansion. Maintain competitive advantage.",
                    confidence="High",
                    segment="Overall"
                ))
            elif share < 45:
                self.insights.append(Insight(
                    category="Market Position",
                    title=f"{brand} Challenge",
                    finding=f"{brand} trails market leader with {share:.1f}% share",
                    implication="Aggressive marketing needed. Identify unique value propositions.",
                    confidence="High",
                    segment="Overall"
                ))

    def get_insights_summary(self) -> str:
        """Generate a text summary of all insights."""
        summary_parts = []
        for insight in self.insights:
            summary_parts.append(f"[{insight.category}] {insight.title}: {insight.finding}")

        return "\n".join(summary_parts)

    def export_insights(self) -> pd.DataFrame:
        """Export insights to DataFrame."""
        data = []
        for insight in self.insights:
            data.append({
                'Category': insight.category,
                'Title': insight.title,
                'Finding': insight.finding,
                'Implication': insight.implication,
                'Confidence': insight.confidence,
                'Segment': insight.segment
            })
        return pd.DataFrame(data)