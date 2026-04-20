"""
Poll Intelligence & Market Insight System
Streamlit Dashboard Application

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_processor import DataProcessor, EDUCATION_LEVELS, CAR_MAKES, REGIONS, COMPUTER_BRANDS
from src.analyzer import Analyzer
from src.insight_engine import InsightEngine

# Page configuration
st.set_page_config(
    page_title="Poll Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E86AB;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .insight-card {
        background-color: rgba(46, 134, 171, 0.1);
        border-left: 4px solid #2E86AB;
        padding: 15px;
        margin: 10px 0;
        border-radius: 8px;
    }
    .insight-card strong {
        color: #1a5276;
    }
    .insight-card em {
        color: #34495e;
    }
    .insight-card {
        color: #2c3e50;
    }
    @media (prefers-color-scheme: dark) {
        .insight-card {
            background-color: rgba(46, 134, 171, 0.15);
            color: #ecf0f1;
        }
        .insight-card strong {
            color: #5dade2;
        }
        .insight-card em {
            color: #bdc3c7;
        }
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_and_process_data():
    """Load and process data with caching."""
    processor = DataProcessor('CompleteResponses.csv')
    processor.load_data()
    processor.clean_data()
    return processor


@st.cache_resource
def get_analyzer(_processor):
    """Get analyzer instance."""
    return Analyzer(_processor.processed_data)


@st.cache_resource
def get_insights(_processor, _analyzer):
    """Generate insights."""
    engine = InsightEngine(_processor.processed_data, _analyzer)
    return engine.generate_all_insights()


def main():
    # Load data
    with st.spinner("Loading and processing data..."):
        processor = load_and_process_data()
        analyzer = get_analyzer(processor)
        insights = get_insights(processor, analyzer)

    data = processor.processed_data
    summary = processor.get_data_summary()

    # Header
    st.markdown('<p class="main-header">📊 Poll Intelligence Dashboard</p>', unsafe_allow_html=True)
    st.markdown("### Market Insight & Decision Support System")
    st.markdown("---")

    # Sidebar
    st.sidebar.header("🔍 Filter Options")

    # Age filter
    age_range = st.sidebar.slider(
        "Age Range",
        min_value=int(data['age'].min()),
        max_value=int(data['age'].max()),
        value=(int(data['age'].min()), int(data['age'].max()))
    )

    # Region filter
    all_regions = ['All'] + list(REGIONS.values())
    selected_region = st.sidebar.selectbox("Region", all_regions)

    # Education filter
    all_education = ['All'] + list(EDUCATION_LEVELS.values())
    selected_education = st.sidebar.selectbox("Education Level", all_education)

    # Salary filter
    salary_range = st.sidebar.slider(
        "Salary Range ($)",
        min_value=0,
        max_value=int(data['salary'].max()),
        value=(0, int(data['salary'].max())),
        step=10000
    )

    # Apply filters
    filtered_data = data.copy()
    filtered_data = filtered_data[
        (filtered_data['age'] >= age_range[0]) &
        (filtered_data['age'] <= age_range[1])
    ]
    if selected_region != 'All':
        filtered_data = filtered_data[filtered_data['region_label'] == selected_region]
    if selected_education != 'All':
        filtered_data = filtered_data[filtered_data['education_label'] == selected_education]
    filtered_data = filtered_data[
        (filtered_data['salary'] >= salary_range[0]) &
        (filtered_data['salary'] <= salary_range[1])
    ]

    # Key Metrics
    st.header("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Responses", f"{len(filtered_data):,}")

    with col2:
        dominant_brand = filtered_data['brand_label'].value_counts().idxmax()
        dominant_share = filtered_data['brand_label'].value_counts(normalize=True).max() * 100
        st.metric("Leading Brand", f"{dominant_brand}", f"{dominant_share:.1f}%")

    with col3:
        avg_salary = filtered_data['salary'].mean()
        st.metric("Avg Salary", f"${avg_salary:,.0f}")

    with col4:
        avg_age = filtered_data['age'].mean()
        st.metric("Avg Age", f"{avg_age:.1f}")

    st.markdown("---")

    # Charts Row 1
    st.header("📊 Brand Analysis")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Brand Distribution")
        fig, ax = plt.subplots(figsize=(10, 6))
        brand_counts = filtered_data['brand_label'].value_counts()
        colors = ['#2E86AB', '#A23B72']
        bars = ax.bar(brand_counts.index, brand_counts.values, color=colors)
        ax.set_ylabel('Count')
        ax.set_title('Computer Brand Preference')
        for bar, count in zip(bars, brand_counts.values):
            pct = count / len(filtered_data) * 100
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
                    f'{pct:.1f}%', ha='center')
        st.pyplot(fig)

    with col2:
        st.subheader("Market Share")
        fig, ax = plt.subplots(figsize=(10, 6))
        brand_counts = filtered_data['brand_label'].value_counts()
        colors = ['#2E86AB', '#A23B72']
        ax.pie(brand_counts.values, labels=brand_counts.index, autopct='%1.1f%%',
               colors=colors, startangle=90)
        ax.set_title('Brand Market Share')
        st.pyplot(fig)

    # Charts Row 2
    st.header("👥 Demographic Analysis")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Preference by Age Group")
        fig, ax = plt.subplots(figsize=(10, 6))
        cross_tab = pd.crosstab(filtered_data['age_group'], filtered_data['brand_label'], normalize='index') * 100
        cross_tab.plot(kind='bar', ax=ax, color=['#2E86AB', '#A23B72'])
        ax.set_ylabel('Percentage (%)')
        ax.set_xlabel('Age Group')
        ax.legend(title='Brand')
        ax.tick_params(axis='x', rotation=15)
        st.pyplot(fig)

    with col2:
        st.subheader("Preference by Region")
        fig, ax = plt.subplots(figsize=(12, 6))
        cross_tab = pd.crosstab(filtered_data['region_label'], filtered_data['brand_label'], normalize='index') * 100
        cross_tab.plot(kind='bar', ax=ax, color=['#2E86AB', '#A23B72'])
        ax.set_ylabel('Percentage (%)')
        ax.set_xlabel('Region')
        ax.legend(title='Brand')
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)

    # Charts Row 3
    st.header("💰 Economic Analysis")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Preference by Salary Bracket")
        fig, ax = plt.subplots(figsize=(10, 6))
        cross_tab = pd.crosstab(filtered_data['salary_bracket'], filtered_data['brand_label'], normalize='index') * 100
        bracket_order = ['Low (<$50K)', 'Medium ($50K-$100K)', 'High ($100K-$150K)', 'Premium (>$150K)']
        cross_tab = cross_tab.reindex([b for b in bracket_order if b in cross_tab.index])
        cross_tab.plot(kind='bar', ax=ax, color=['#2E86AB', '#A23B72'])
        ax.set_ylabel('Percentage (%)')
        ax.set_xlabel('Salary Bracket')
        ax.legend(title='Brand')
        ax.tick_params(axis='x', rotation=15)
        st.pyplot(fig)

    with col2:
        st.subheader("Education Distribution")
        fig, ax = plt.subplots(figsize=(10, 6))
        edu_counts = filtered_data['education_label'].value_counts()
        ax.barh(edu_counts.index, edu_counts.values, color='#2E86AB')
        ax.set_xlabel('Count')
        st.pyplot(fig)

    # Insights Section
    st.markdown("---")
    st.header("🧠 Business Insights")

    insight_tabs = st.tabs(["All Insights", "Brand Preference", "Demographics", "Geography", "Economics"])

    with insight_tabs[0]:
        for insight in insights:
            st.markdown(f"""
            <div class="insight-card">
                <strong>[{insight.category}] {insight.title}</strong><br>
                <em>Finding:</em> {insight.finding}<br>
                <em>Implication:</em> {insight.implication}<br>
                <em>Confidence:</em> <span style="color: {'green' if insight.confidence=='High' else 'orange'}">{insight.confidence}</span>
            </div>
            """, unsafe_allow_html=True)

    with insight_tabs[1]:
        for insight in insights:
            if insight.category == "Brand Preference":
                st.markdown(f"""
                <div class="insight-card">
                    <strong>{insight.title}</strong><br>
                    <em>Finding:</em> {insight.finding}<br>
                    <em>Implication:</em> {insight.implication}
                </div>
                """, unsafe_allow_html=True)

    with insight_tabs[2]:
        for insight in insights:
            if insight.category == "Demographics":
                st.markdown(f"""
                <div class="insight-card">
                    <strong>{insight.title}</strong><br>
                    <em>Finding:</em> {insight.finding}<br>
                    <em>Implication:</em> {insight.implication}
                </div>
                """, unsafe_allow_html=True)

    with insight_tabs[3]:
        for insight in insights:
            if insight.category == "Geography":
                st.markdown(f"""
                <div class="insight-card">
                    <strong>{insight.title}</strong><br>
                    <em>Finding:</em> {insight.finding}<br>
                    <em>Implication:</em> {insight.implication}
                </div>
                """, unsafe_allow_html=True)

    with insight_tabs[4]:
        for insight in insights:
            if insight.category == "Economics":
                st.markdown(f"""
                <div class="insight-card">
                    <strong>{insight.title}</strong><br>
                    <em>Finding:</em> {insight.finding}<br>
                    <em>Implication:</em> {insight.implication}
                </div>
                """, unsafe_allow_html=True)

    # Additional Analysis
    st.markdown("---")
    st.header("📉 Additional Analysis")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Correlation Heatmap")
        fig, ax = plt.subplots(figsize=(8, 6))
        numeric_cols = ['salary', 'age', 'credit', 'brand']
        corr = filtered_data[numeric_cols].corr()
        sns.heatmap(corr, annot=True, cmap='coolwarm', center=0, ax=ax)
        st.pyplot(fig)

    with col2:
        st.subheader("Top Car Brands")
        fig, ax = plt.subplots(figsize=(10, 6))
        car_counts = filtered_data['car_label'].value_counts().head(8)
        ax.barh(car_counts.index[::-1], car_counts.values[::-1], color='#2E86AB')
        ax.set_xlabel('Count')
        st.pyplot(fig)

    # Data Summary
    st.markdown("---")
    with st.expander("📋 View Data Summary"):
        st.write(f"**Total Responses:** {summary['total_responses']:,}")
        st.write(f"**Salary Range:** ${summary['salary_stats']['min']:,.0f} - ${summary['salary_stats']['max']:,.0f}")
        st.write(f"**Average Salary:** ${summary['salary_stats']['mean']:,.0f}")
        st.write(f"**Age Range:** {summary['age_stats']['min']} - {summary['age_stats']['max']}")
        st.write(f"**Average Age:** {summary['age_stats']['mean']:.1f}")

        st.subheader("Brand Distribution")
        st.dataframe(pd.DataFrame({
            'Brand': list(summary['brand_preference'].keys()),
            'Count': list(summary['brand_preference'].values()),
            'Percentage': [f"{v/summary['total_responses']*100:.1f}%" for v in summary['brand_preference'].values()]
        }))

    # Export Options
    st.markdown("---")
    st.header("📥 Export Data")

    col1, col2, col3 = st.columns(3)

    with col1:
        csv = filtered_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Filtered Data (CSV)",
            data=csv,
            file_name='survey_data_filtered.csv',
            mime='text/csv'
        )

    with col2:
        insights_df = pd.DataFrame([{
            'Category': i.category,
            'Title': i.title,
            'Finding': i.finding,
            'Implication': i.implication,
            'Confidence': i.confidence
        } for i in insights])
        insights_csv = insights_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Insights (CSV)",
            data=insights_csv,
            file_name='survey_insights.csv',
            mime='text/csv'
        )

    with col3:
        summary_df = pd.DataFrame(summary['brand_preference'].items(), columns=['Brand', 'Count'])
        summary_csv = summary_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Summary (CSV)",
            data=summary_csv,
            file_name='survey_summary.csv',
            mime='text/csv'
        )

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: gray;">
        <p>Poll Intelligence & Market Insight System | Built with Streamlit</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()