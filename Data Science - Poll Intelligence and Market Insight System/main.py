"""
Poll Intelligence & Market Insight System
Main Entry Point

This script runs the complete analytics pipeline.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_processor import DataProcessor
from src.analyzer import Analyzer
from src.insight_engine import InsightEngine
from src.visualizer import Visualizer


def main():
    """Run the complete analytics pipeline."""
    print("=" * 60)
    print("  POLL INTELLIGENCE & MARKET INSIGHT SYSTEM")
    print("=" * 60)

    # Initialize data processor
    data_path = 'CompleteResponses.csv'
    print(f"\n[1/5] Loading data from {data_path}...")

    processor = DataProcessor(data_path)
    processor.load_data()

    # Clean and process data
    print("\n[2/5] Processing and cleaning data...")
    processed_data = processor.clean_data()

    # Get data summary
    print("\n[3/5] Generating data summary...")
    summary = processor.get_data_summary()

    print(f"\n  Total Responses: {summary['total_responses']:,}")
    print(f"\n  Salary Statistics:")
    print(f"    Mean: ${summary['salary_stats']['mean']:,.2f}")
    print(f"    Median: ${summary['salary_stats']['median']:,.2f}")
    print(f"    Range: ${summary['salary_stats']['min']:,.2f} - ${summary['salary_stats']['max']:,.2f}")

    print(f"\n  Age Statistics:")
    print(f"    Mean: {summary['age_stats']['mean']:.1f} years")
    print(f"    Range: {summary['age_stats']['min']} - {summary['age_stats']['max']} years")

    print(f"\n  Brand Preference:")
    for brand, count in summary['brand_preference'].items():
        pct = count / summary['total_responses'] * 100
        print(f"    {brand}: {count:,} ({pct:.1f}%)")

    # Initialize analyzer
    print("\n[4/5] Running analytical engine...")
    analyzer = Analyzer(processed_data)

    # Generate insights
    print("\n[5/5] Generating business insights...")
    insight_engine = InsightEngine(processed_data, analyzer)
    insights = insight_engine.generate_all_insights()

    print(f"\n{'='*60}")
    print("  KEY INSIGHTS")
    print("=" * 60)

    for i, insight in enumerate(insights[:10], 1):
        print(f"\n  [{insight.category}] {insight.title}")
        print(f"    Finding: {insight.finding}")
        print(f"    Implication: {insight.implication}")
        print(f"    Confidence: {insight.confidence}")

    # Generate visualizations
    print(f"\n{'='*60}")
    print("  GENERATING VISUALIZATIONS")
    print("=" * 60)

    visualizer = Visualizer(processed_data)
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)

    # Create and save visualizations
    print("\n  Creating brand distribution chart...")
    visualizer.plot_brand_distribution(f'{output_dir}/brand_distribution.png')

    print("  Creating brand pie chart...")
    visualizer.plot_brand_pie(f'{output_dir}/brand_pie.png')

    print("  Creating preference by age chart...")
    visualizer.plot_preference_by_age(f'{output_dir}/preference_by_age.png')

    print("  Creating preference by region chart...")
    visualizer.plot_preference_by_region(f'{output_dir}/preference_by_region.png')

    print("  Creating preference by education chart...")
    visualizer.plot_preference_by_education(f'{output_dir}/preference_by_education.png')

    print("  Creating preference by salary chart...")
    visualizer.plot_preference_by_salary_bracket(f'{output_dir}/preference_by_salary.png')

    print("  Creating car distribution chart...")
    visualizer.plot_car_brand_distribution(f'{output_dir}/car_distribution.png')

    print("  Creating age distribution chart...")
    visualizer.plot_age_distribution(f'{output_dir}/age_distribution.png')

    print("  Creating correlation heatmap...")
    visualizer.plot_correlation_heatmap(f'{output_dir}/correlation_heatmap.png')

    print("  Creating dashboard summary...")
    visualizer.create_dashboard_summary(output_dir)

    # Export insights to CSV
    print("\n  Exporting insights to CSV...")
    insights_df = insight_engine.export_insights()
    insights_df.to_csv(f'{output_dir}/insights.csv', index=False)

    print(f"\n{'='*60}")
    print("  ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"\n  Output files saved to: {output_dir}/")
    print("    - brand_distribution.png")
    print("    - brand_pie.png")
    print("    - preference_by_age.png")
    print("    - preference_by_region.png")
    print("    - preference_by_education.png")
    print("    - preference_by_salary.png")
    print("    - car_distribution.png")
    print("    - age_distribution.png")
    print("    - correlation_heatmap.png")
    print("    - dashboard_summary.png")
    print("    - insights.csv")

    print(f"\n  Run 'streamlit run app.py' for interactive dashboard")

    return processed_data, insights, visualizer


if __name__ == "__main__":
    data, insights, viz = main()