"""
Visualization Module
Creates professional visualizations for survey insights
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 7)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12


class Visualizer:
    """Creates visualizations for survey data analysis."""

    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.figures: Dict[str, plt.Figure] = {}

        # Color palette
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'accent': '#F18F01',
            'success': '#C73E1D',
            'neutral': '#3B1F2B',
            'palette': ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B', '#45B7D1']
        }

    def plot_brand_distribution(self, save_path: Optional[str] = None) -> plt.Figure:
        """Plot overall brand preference distribution."""
        fig, ax = plt.subplots(figsize=(10, 6))

        brand_counts = self.data['brand_label'].value_counts()
        colors = [self.colors['primary'], self.colors['secondary']]

        bars = ax.bar(brand_counts.index, brand_counts.values, color=colors, edgecolor='white', linewidth=2)

        ax.set_xlabel('Computer Brand', fontweight='bold')
        ax.set_ylabel('Number of Respondents', fontweight='bold')
        ax.set_title('Computer Brand Preference Distribution', fontweight='bold', fontsize=14)

        for bar, count in zip(bars, brand_counts.values):
            pct = count / len(self.data) * 100
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                    f'{count:,}\n({pct:.1f}%)', ha='center', va='bottom', fontweight='bold')

        plt.tight_layout()
        self.figures['brand_distribution'] = fig

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    def plot_brand_pie(self, save_path: Optional[str] = None) -> plt.Figure:
        """Plot brand preference as pie chart."""
        fig, ax = plt.subplots(figsize=(10, 8))

        brand_counts = self.data['brand_label'].value_counts()
        colors = [self.colors['primary'], self.colors['secondary']]
        explode = (0.02, 0.02)

        wedges, texts, autotexts = ax.pie(
            brand_counts.values,
            labels=brand_counts.index,
            autopct='%1.1f%%',
            colors=colors,
            explode=explode,
            startangle=90,
            shadow=True
        )

        for autotext in autotexts:
            autotext.set_fontweight('bold')
            autotext.set_fontsize(14)

        ax.set_title('Market Share: Computer Brand Preference', fontweight='bold', fontsize=16)

        plt.tight_layout()
        self.figures['brand_pie'] = fig

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    def plot_preference_by_age(self, save_path: Optional[str] = None) -> plt.Figure:
        """Plot brand preference by age group."""
        fig, ax = plt.subplots(figsize=(12, 7))

        cross_tab = pd.crosstab(self.data['age_group'], self.data['brand_label'], normalize='index') * 100

        x = np.arange(len(cross_tab.index))
        width = 0.35

        bars1 = ax.bar(x - width/2, cross_tab['Acer'], width, label='Acer', color=self.colors['primary'])
        bars2 = ax.bar(x + width/2, cross_tab['Sony'], width, label='Sony', color=self.colors['secondary'])

        ax.set_xlabel('Age Group', fontweight='bold')
        ax.set_ylabel('Percentage (%)', fontweight='bold')
        ax.set_title('Brand Preference by Age Group', fontweight='bold', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(cross_tab.index, rotation=15)
        ax.legend(title='Brand', loc='upper right')
        ax.set_ylim(0, 70)

        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'{height:.1f}%', ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        self.figures['preference_by_age'] = fig

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    def plot_preference_by_region(self, save_path: Optional[str] = None) -> plt.Figure:
        """Plot brand preference by region."""
        fig, ax = plt.subplots(figsize=(14, 8))

        cross_tab = pd.crosstab(self.data['region_label'], self.data['brand_label'], normalize='index') * 100

        x = np.arange(len(cross_tab.index))
        width = 0.35

        bars1 = ax.bar(x - width/2, cross_tab['Acer'], width, label='Acer', color=self.colors['primary'])
        bars2 = ax.bar(x + width/2, cross_tab['Sony'], width, label='Sony', color=self.colors['secondary'])

        ax.set_xlabel('Region', fontweight='bold')
        ax.set_ylabel('Percentage (%)', fontweight='bold')
        ax.set_title('Brand Preference by Region', fontweight='bold', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(cross_tab.index, rotation=45, ha='right')
        ax.legend(title='Brand', loc='upper right')
        ax.set_ylim(0, 70)

        plt.tight_layout()
        self.figures['preference_by_region'] = fig

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    def plot_preference_by_education(self, save_path: Optional[str] = None) -> plt.Figure:
        """Plot brand preference by education level."""
        fig, ax = plt.subplots(figsize=(12, 7))

        cross_tab = pd.crosstab(self.data['education_label'], self.data['brand_label'], normalize='index') * 100

        x = np.arange(len(cross_tab.index))
        width = 0.35

        bars1 = ax.bar(x - width/2, cross_tab['Acer'], width, label='Acer', color=self.colors['primary'])
        bars2 = ax.bar(x + width/2, cross_tab['Sony'], width, label='Sony', color=self.colors['secondary'])

        ax.set_xlabel('Education Level', fontweight='bold')
        ax.set_ylabel('Percentage (%)', fontweight='bold')
        ax.set_title('Brand Preference by Education Level', fontweight='bold', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(cross_tab.index, rotation=30, ha='right')
        ax.legend(title='Brand', loc='upper right')

        plt.tight_layout()
        self.figures['preference_by_education'] = fig

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    def plot_salary_distribution(self, save_path: Optional[str] = None) -> plt.Figure:
        """Plot salary distribution by brand preference."""
        fig, ax = plt.subplots(figsize=(12, 7))

        self.data.boxplot(column='salary', by='brand_label', ax=ax, patch_artist=True,
                          boxprops=dict(facecolor=self.colors['primary'], alpha=0.7))

        ax.set_xlabel('Computer Brand', fontweight='bold')
        ax.set_ylabel('Salary ($)', fontweight='bold')
        ax.set_title('Salary Distribution by Brand Preference', fontweight='bold')
        fig.suptitle('')  # Remove automatic title

        plt.tight_layout()
        self.figures['salary_distribution'] = fig

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    def plot_car_brand_distribution(self, save_path: Optional[str] = None) -> plt.Figure:
        """Plot car brand distribution."""
        fig, ax = plt.subplots(figsize=(14, 8))

        car_counts = self.data['car_label'].value_counts().head(10)
        colors = plt.cm.viridis(np.linspace(0, 0.8, len(car_counts)))

        bars = ax.barh(car_counts.index[::-1], car_counts.values[::-1], color=colors)

        ax.set_xlabel('Number of Respondents', fontweight='bold')
        ax.set_ylabel('Car Brand', fontweight='bold')
        ax.set_title('Top 10 Car Brands Among Respondents', fontweight='bold', fontsize=14)

        for bar, count in zip(bars, car_counts.values[::-1]):
            ax.text(bar.get_width() + 20, bar.get_y() + bar.get_height()/2,
                    f'{count:,}', ha='left', va='center')

        plt.tight_layout()
        self.figures['car_distribution'] = fig

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    def plot_correlation_heatmap(self, save_path: Optional[str] = None) -> plt.Figure:
        """Plot correlation heatmap for numeric variables."""
        fig, ax = plt.subplots(figsize=(10, 8))

        numeric_cols = ['salary', 'age', 'credit', 'brand']
        corr_matrix = self.data[numeric_cols].corr()

        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='coolwarm', center=0,
                    square=True, linewidths=2, ax=ax, fmt='.3f')

        ax.set_title('Correlation Heatmap: Survey Variables', fontweight='bold', fontsize=14)

        plt.tight_layout()
        self.figures['correlation_heatmap'] = fig

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    def plot_preference_by_salary_bracket(self, save_path: Optional[str] = None) -> plt.Figure:
        """Plot brand preference by salary bracket."""
        fig, ax = plt.subplots(figsize=(12, 7))

        cross_tab = pd.crosstab(self.data['salary_bracket'], self.data['brand_label'], normalize='index') * 100

        bracket_order = ['Low (<$50K)', 'Medium ($50K-$100K)', 'High ($100K-$150K)', 'Premium (>$150K)']
        cross_tab = cross_tab.reindex([b for b in bracket_order if b in cross_tab.index])

        x = np.arange(len(cross_tab.index))
        width = 0.35

        bars1 = ax.bar(x - width/2, cross_tab['Acer'], width, label='Acer', color=self.colors['primary'])
        bars2 = ax.bar(x + width/2, cross_tab['Sony'], width, label='Sony', color=self.colors['secondary'])

        ax.set_xlabel('Salary Bracket', fontweight='bold')
        ax.set_ylabel('Percentage (%)', fontweight='bold')
        ax.set_title('Brand Preference by Salary Bracket', fontweight='bold', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(cross_tab.index, rotation=15)
        ax.legend(title='Brand', loc='upper right')

        plt.tight_layout()
        self.figures['preference_by_salary'] = fig

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    def plot_age_distribution(self, save_path: Optional[str] = None) -> plt.Figure:
        """Plot age distribution."""
        fig, ax = plt.subplots(figsize=(12, 7))

        ax.hist(self.data['age'], bins=30, color=self.colors['primary'], edgecolor='white', alpha=0.8)

        ax.axvline(self.data['age'].mean(), color=self.colors['secondary'], linestyle='--', linewidth=2,
                   label=f'Mean: {self.data["age"].mean():.1f}')
        ax.axvline(self.data['age'].median(), color=self.colors['accent'], linestyle='--', linewidth=2,
                   label=f'Median: {self.data["age"].median():.1f}')

        ax.set_xlabel('Age', fontweight='bold')
        ax.set_ylabel('Number of Respondents', fontweight='bold')
        ax.set_title('Age Distribution of Respondents', fontweight='bold', fontsize=14)
        ax.legend()

        plt.tight_layout()
        self.figures['age_distribution'] = fig

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    def create_dashboard_summary(self, save_dir: str = 'output'):
        """Create a multi-plot dashboard summary."""
        import os
        os.makedirs(save_dir, exist_ok=True)

        fig = plt.figure(figsize=(20, 16))

        # Create grid
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

        # Plot 1: Brand distribution
        ax1 = fig.add_subplot(gs[0, 0])
        brand_counts = self.data['brand_label'].value_counts()
        ax1.bar(brand_counts.index, brand_counts.values, color=[self.colors['primary'], self.colors['secondary']])
        ax1.set_title('Brand Preference Distribution', fontweight='bold')
        ax1.set_ylabel('Count')

        # Plot 2: Age distribution
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.hist(self.data['age'], bins=25, color=self.colors['primary'], edgecolor='white')
        ax2.set_title('Age Distribution', fontweight='bold')
        ax2.set_xlabel('Age')
        ax2.set_ylabel('Count')

        # Plot 3: Salary distribution
        ax3 = fig.add_subplot(gs[0, 2])
        ax3.hist(self.data['salary'], bins=25, color=self.colors['secondary'], edgecolor='white')
        ax3.set_title('Salary Distribution', fontweight='bold')
        ax3.set_xlabel('Salary')
        ax3.set_ylabel('Count')

        # Plot 4: Preference by Age
        ax4 = fig.add_subplot(gs[1, 0])
        cross_tab = pd.crosstab(self.data['age_group'], self.data['brand_label'], normalize='index') * 100
        cross_tab.plot(kind='bar', ax=ax4, color=[self.colors['primary'], self.colors['secondary']])
        ax4.set_title('Brand by Age Group', fontweight='bold')
        ax4.set_xlabel('Age Group')
        ax4.set_ylabel('%')
        ax4.tick_params(axis='x', rotation=45)
        ax4.legend(title='Brand')

        # Plot 5: Preference by Region
        ax5 = fig.add_subplot(gs[1, 1])
        cross_tab = pd.crosstab(self.data['region_label'], self.data['brand_label'], normalize='index') * 100
        cross_tab.plot(kind='bar', ax=ax5, color=[self.colors['primary'], self.colors['secondary']])
        ax5.set_title('Brand by Region', fontweight='bold')
        ax5.set_xlabel('Region')
        ax5.set_ylabel('%')
        ax5.tick_params(axis='x', rotation=45)
        ax5.legend(title='Brand')

        # Plot 6: Education distribution
        ax6 = fig.add_subplot(gs[1, 2])
        edu_counts = self.data['education_label'].value_counts()
        ax6.barh(edu_counts.index, edu_counts.values, color=self.colors['palette'])
        ax6.set_title('Education Level Distribution', fontweight='bold')
        ax6.set_xlabel('Count')

        # Plot 7: Car brand distribution
        ax7 = fig.add_subplot(gs[2, 0])
        car_counts = self.data['car_label'].value_counts().head(8)
        ax7.barh(car_counts.index[::-1], car_counts.values[::-1], color=self.colors['primary'])
        ax7.set_title('Top Car Brands', fontweight='bold')
        ax7.set_xlabel('Count')

        # Plot 8: Region distribution
        ax8 = fig.add_subplot(gs[2, 1])
        region_counts = self.data['region_label'].value_counts()
        ax8.barh(region_counts.index, region_counts.values, color=self.colors['secondary'])
        ax8.set_title('Regional Distribution', fontweight='bold')
        ax8.set_xlabel('Count')

        # Plot 9: Brand by Salary
        ax9 = fig.add_subplot(gs[2, 2])
        cross_tab = pd.crosstab(self.data['salary_bracket'], self.data['brand_label'], normalize='index') * 100
        cross_tab.plot(kind='bar', ax=ax9, color=[self.colors['primary'], self.colors['secondary']])
        ax9.set_title('Brand by Salary', fontweight='bold')
        ax9.set_xlabel('Salary Bracket')
        ax9.set_ylabel('%')
        ax9.tick_params(axis='x', rotation=45)
        ax9.legend(title='Brand')

        fig.suptitle('Survey Analytics Dashboard', fontsize=20, fontweight='bold', y=1.02)

        plt.savefig(f'{save_dir}/dashboard_summary.png', dpi=150, bbox_inches='tight')
        self.figures['dashboard'] = fig

        return fig

    def save_all_figures(self, output_dir: str = 'output'):
        """Save all generated figures."""
        import os
        os.makedirs(output_dir, exist_ok=True)

        for name, fig in self.figures.items():
            fig.savefig(f'{output_dir}/{name}.png', dpi=150, bbox_inches='tight')
            print(f"Saved: {output_dir}/{name}.png")