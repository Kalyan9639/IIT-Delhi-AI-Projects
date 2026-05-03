"""
Bangalore Real Estate Intelligence System - Main Streamlit Application.
A comprehensive multi-page application for real estate price prediction and analysis.
"""

import streamlit as st
import pandas as pd
import os
import sys
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')
import plotly.express as px

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.config import *
from src.preprocessing import DataPreprocessor
from src.feature_engineering import FeatureEngineer
from src.anomaly_detection import AnomalyDetector
from src.investment_scoring import InvestmentScorer
from src.heatmap_generator import HeatmapGenerator
from src.model_training import ModelTrainer
from src.explainability import ExplainabilityAnalyzer

# Page configuration
st.set_page_config(
    page_title="Bangalore Real Estate Intelligence System",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-top: 20px;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    </style>
""", unsafe_allow_html=True)


class RealEstateApp:
    """Main application class for Bangalore Real Estate Intelligence System."""
    
    def __init__(self):
        self.data = None
        self.preprocessor = DataPreprocessor()
        self.feature_engineer = FeatureEngineer()
        self.anomaly_detector = AnomalyDetector()
        self.investment_scorer = InvestmentScorer()
        self.heatmap_generator = HeatmapGenerator()
        self.model_trainer = ModelTrainer()
        self.explainer = ExplainabilityAnalyzer()
        
        self.models_loaded = False
        self.data_loaded = False
        
    def load_data(self):
        """Load and preprocess data."""
        if self.data is not None:
            return self.data
        
        try:
            st.info("Loading data...")
            self.data = self.preprocessor.load_data(RAW_DATA_PATH)
            
            # Initial preprocessing
            self.data = self.preprocessor.preprocess(self.data.copy())
            
            # Feature engineering
            self.data = self.feature_engineer.create_all_features(self.data.copy())
            
            # Anomaly detection
            self.data = self.anomaly_detector.detect_all_anomalies(self.data.copy())
            
            # Investment scoring
            self.data = self.investment_scorer.calculate_investment_score(self.data.copy())
            self.data = self.investment_scorer.create_composite_score(self.data.copy())
            
            self.data_loaded = True
            st.success("Data loaded and preprocessed successfully!")
            
            return self.data
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return None
    
    def load_models(self):
        """Load trained models."""
        if self.models_loaded:
            return True
        
        try:
            loaded_any = False

            # Load preprocessor
            if os.path.exists(PREPROCESSOR_PATH):
                try:
                    self.preprocessor.load_preprocessor(PREPROCESSOR_PATH)
                    loaded_any = True
                except Exception as exc:
                    st.warning(f"Preprocessor artifact could not be loaded and will be ignored: {exc}")
            
            # Load anomaly detector
            if os.path.exists(ANOMALY_MODEL_PATH):
                try:
                    self.anomaly_detector.load_model(ANOMALY_MODEL_PATH)
                    loaded_any = True
                except Exception as exc:
                    st.warning(f"Anomaly detector could not be loaded and will be ignored: {exc}")
            
            # Load investment scorer
            if os.path.exists(INVESTMENT_SCORER_PATH):
                try:
                    self.investment_scorer.load_model(INVESTMENT_SCORER_PATH)
                    loaded_any = True
                except Exception as exc:
                    st.warning(f"Investment scorer could not be loaded and will be ignored: {exc}")
            
            # Load main model
            if os.path.exists(MODEL_PATH):
                try:
                    self.model_trainer.load_model(MODEL_PATH)
                    loaded_any = True
                except Exception as exc:
                    st.warning(f"Main model could not be loaded and will be ignored: {exc}")
            
            self.models_loaded = loaded_any
            if loaded_any:
                st.success("Models loaded successfully!")
            else:
                st.warning("No trained model artifacts were found. Prediction features will stay disabled until you run the training pipeline.")
            return loaded_any
            
        except Exception as e:
            st.error(f"Error loading models: {str(e)}")
            return False
    
    def run(self):
        """Run the Streamlit application."""
        st.title("🏠 Bangalore Real Estate Intelligence System")
        st.markdown("### AI-Powered Real Estate Analytics & Price Prediction Platform")
        
        # Sidebar navigation
        page = st.sidebar.selectbox(
            "Select Page",
            [
                "Dashboard",
                "House Price Prediction",
                "Location Analytics",
                "Feature Importance",
                "Investment Insights",
                "Fraud Detection",
                "Price Heatmaps",
                "Model Performance",
                "About Project"
            ]
        )
        
        # Load data if not loaded
        if not self.data_loaded:
            self.load_data()
        
        # Load models if not loaded
        if not self.models_loaded:
            self.load_models()
        
        # Render selected page
        if page == "Dashboard":
            self.render_dashboard()
        elif page == "House Price Prediction":
            self.render_price_prediction()
        elif page == "Location Analytics":
            self.render_location_analytics()
        elif page == "Feature Importance":
            self.render_feature_importance()
        elif page == "Investment Insights":
            self.render_investment_insights()
        elif page == "Fraud Detection":
            self.render_fraud_detection()
        elif page == "Price Heatmaps":
            self.render_price_heatmaps()
        elif page == "Model Performance":
            self.render_model_performance()
        elif page == "About Project":
            self.render_about()
    
    def render_dashboard(self):
        """Render dashboard page."""
        st.header("📊 Dashboard")
        
        if self.data is None:
            st.warning("Please wait while data is being loaded...")
            return
        
        # Calculate key metrics
        total_properties = len(self.data)
        avg_price = self.data['price'].mean()
        avg_price_per_sqft = self.data['price_per_sqft'].mean()
        total_anomalies = self.data['is_any_anomaly'].sum()
        avg_investment_score = self.data['investment_score'].mean()
        
        # Display metrics in cards
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">{:,}</div>
                    <div class="metric-label">Total Properties</div>
                </div>
            """.format(total_properties), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">₹{:.1f}L</div>
                    <div class="metric-label">Avg Price</div>
                </div>
            """.format(avg_price), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">₹{:.0f}</div>
                    <div class="metric-label">Avg Price/Sqft</div>
                </div>
            """.format(avg_price_per_sqft), unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">{:,}</div>
                    <div class="metric-label">Anomalies Detected</div>
                </div>
            """.format(int(total_anomalies)), unsafe_allow_html=True)
        
        with col5:
            st.markdown("""
                <div class="metric-card">
                    <div class="metric-value"> {:.2f}</div>
                    <div class="metric-label">Avg Investment Score</div>
                </div>
            """.format(avg_investment_score), unsafe_allow_html=True)
        
        # Quick statistics
        st.subheader("Quick Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("BHK Distribution")
            bhk_dist = self.data['bhk'].value_counts().sort_index()
            st.bar_chart(bhk_dist)
        
        with col2:
            st.subheader("Area Type Distribution")
            area_dist = self.data['area_type'].value_counts()
            st.bar_chart(area_dist)
        
        # Price distribution
        st.subheader("Price Distribution")
        fig = self.heatmap_generator.create_price_distribution_plot(self.data)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        # Top locations by price
        st.subheader("Top 10 Locations by Average Price")
        top_locations = self.data.groupby('location')['price'].mean().sort_values(ascending=False).head(10)
        st.bar_chart(top_locations)
    
    def render_price_prediction(self):
        """Render price prediction page."""
        st.header("💰 House Price Prediction")
        
        if self.data is None or not self.models_loaded:
            st.warning("Please wait while data and models are being loaded, or train the models first.")
            return
        
        st.subheader("Enter Property Details")
        
        # Input form
        col1, col2 = st.columns(2)
        
        with col1:
            area_type = st.selectbox("Area Type", self.data['area_type'].unique())
            bhk = st.slider("BHK", 1, 10, 2)
            total_sqft = st.number_input("Total Square Feet", min_value=300, max_value=10000, value=1000)
            bath = st.slider("Bathrooms", 1, 10, 2)
        
        with col2:
            location = st.selectbox("Location", sorted(self.data['location'].unique()))
            society = st.text_input("Society (Optional)", "")
            balcony = st.slider("Balcony", 0, 5, 1)
        
        # Prepare features
        if st.button("Predict Price"):
            with st.spinner("Predicting price..."):
                try:
                    # Create input dataframe
                    input_data = pd.DataFrame({
                        'area_type': [area_type],
                        'location': [location],
                        'society': [society if society else 'Unknown'],
                        'bhk': [bhk],
                        'total_sqft': [total_sqft],
                        'bath': [bath],
                        'balcony': [balcony]
                    })
                    
                    # Preprocess input
                    input_data = self.preprocessor.preprocess(input_data.copy(), 
                                                              remove_outliers=False, 
                                                              encode=False, scale=False)
                    
                    # Feature engineering
                    input_data = self.feature_engineer.create_all_features(input_data.copy())
                    
                    # Align with training features
                    if not self.model_trainer.best_model or not hasattr(self.model_trainer, "feature_columns"):
                        st.warning("No trained model is available yet. Run `python train_pipeline.py` first.")
                        return

                    feature_cols = self.model_trainer.feature_columns
                    input_features = pd.DataFrame([{col: input_data.iloc[0][col] if col in input_data.columns else 0 for col in feature_cols}])

                    # Make prediction
                    prediction = self.model_trainer.best_model.predict(input_features)[0]
                    
                    # Display result
                    st.success(f"Predicted Price: ₹{prediction:.2f} Lakhs")
                    
                    # Confidence interval
                    st.info("Note: This is an AI-powered prediction based on historical data patterns.")
                    
                    # Show feature importance for this prediction
                    st.subheader("Prediction Insights")
                    
                    # Create explanation
                    if self.data_loaded:
                        # Get similar properties
                        similar = self.data[
                            (self.data['location'] == location) &
                            (self.data['bhk'] == bhk)
                        ]
                        
                        if len(similar) > 0:
                            avg_similar_price = similar['price'].mean()
                            st.write(f"Average price for similar properties in {location}: ₹{avg_similar_price:.2f} Lakhs")
                            st.write(f"Price difference: ₹{prediction - avg_similar_price:.2f} Lakhs")
                    
                except Exception as e:
                    st.error(f"Error making prediction: {str(e)}")
    
    def render_location_analytics(self):
        """Render location analytics page."""
        st.header("📍 Location Analytics")
        
        if self.data is None:
            st.warning("Please wait while data is being loaded...")
            return
        
        # Location selection
        location = st.selectbox("Select Location", sorted(self.data['location'].unique()))
        
        if location:
            location_data = self.data[self.data['location'] == location]
            
            st.subheader(f"Analytics for {location}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Average Price", f"₹{location_data['price'].mean():.2f} Lakhs")
                st.metric("Average Area", f"{location_data['total_sqft'].mean():.0f} sqft")
            
            with col2:
                st.metric("Avg Price/Sqft", f"₹{location_data['price_per_sqft'].mean():.0f}")
                st.metric("Number of Properties", len(location_data))
            
            with col3:
                st.metric("Average BHK", f"{location_data['bhk'].mean():.1f}")
                st.metric("Average Bathrooms", f"{location_data['bath'].mean():.1f}")
            
            # Price distribution for location
            st.subheader("Price Distribution")
            fig = px.histogram(location_data, x='price', title=f'Price Distribution in {location}')
            st.plotly_chart(fig, use_container_width=True)
            
            # BHK distribution
            st.subheader("BHK Distribution")
            bhk_dist = location_data['bhk'].value_counts()
            st.bar_chart(bhk_dist)
    
    def render_feature_importance(self):
        """Render feature importance page."""
        st.header("📈 Feature Importance Analysis")
        
        if not self.models_loaded:
            st.warning("No trained model is available yet. Run the training pipeline first.")
            return
        
        st.subheader("Global Feature Importance")
        
        # Get feature importance
        if self.model_trainer.feature_importance:
            best_model_name = self.model_trainer.best_model_name
            if best_model_name in self.model_trainer.feature_importance:
                importance = self.model_trainer.feature_importance[best_model_name]
                
                # Create DataFrame
                importance_df = pd.DataFrame({
                    'Feature': list(importance.keys()),
                    'Importance': list(importance.values())
                }).sort_values('Importance', ascending=True)
                
                # Plot
                fig = px.bar(importance_df, x='Importance', y='Feature', 
                            title=f'Feature Importance - {best_model_name}',
                            orientation='h')
                st.plotly_chart(fig, use_container_width=True)
        
        # SHAP analysis
        st.subheader("SHAP Analysis")
        
        if self.data_loaded:
            # Sample data for SHAP
            sample_size = min(100, len(self.data))
            X_sample = self.data[self.model_trainer.feature_columns].sample(n=sample_size, random_state=42)
            
            # Calculate SHAP values
            try:
                self.explainer.create_explainer(self.model_trainer.best_model, X_sample)
                self.explainer.calculate_shap_values(X_sample, self.model_trainer.best_model)
                
                # Plot global importance
                fig = self.explainer.plot_global_feature_importance()
                if fig:
                    st.pyplot(fig)
                
                # Top features
                top_features = self.explainer.get_top_features(10)
                st.write("Top 10 Important Features:")
                for i, feature in enumerate(top_features, 1):
                    st.write(f"{i}. {feature}")
                    
            except Exception as e:
                st.error(f"Error in SHAP analysis: {str(e)}")
    
    def render_investment_insights(self):
        """Render investment insights page."""
        st.header("📊 Investment Insights")
        
        if self.data is None:
            st.warning("Please wait while data is being loaded...")
            return
        
        # Investment summary
        st.subheader("Investment Summary")
        
        investment_summary = self.investment_scorer.get_investment_summary(self.data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Average Investment Score", f"{investment_summary['average_investment_score']:.3f}")
            st.metric("Investment Score Std", f"{investment_summary['investment_score_std']:.3f}")
        
        with col2:
            st.metric("Total Locations", investment_summary['total_locations'])
        
        # Top investment areas
        st.subheader("Top 10 Investment Areas")
        top_areas = investment_summary['top_investment_areas']
        
        for i, (area, score) in enumerate(top_areas.items(), 1):
            st.write(f"{i}. **{area}** - Score: {score:.3f}")
        
        # Bottom investment areas
        st.subheader("Bottom 10 Investment Areas")
        bottom_areas = investment_summary['bottom_investment_areas']
        
        for i, (area, score) in enumerate(bottom_areas.items(), 1):
            st.write(f"{i}. **{area}** - Score: {score:.3f}")
        
        # Investment heatmap
        st.subheader("Investment Heatmap")
        heatmap_path = MODEL_DIR / 'investment_heatmap.html'
        self.heatmap_generator.create_investment_heatmap(self.data, str(heatmap_path))
        
        # Display heatmap
        with open(heatmap_path, 'r') as f:
            heatmap_html = f.read()
        
        st.components.v1.html(heatmap_html, height=600)
    
    def render_fraud_detection(self):
        """Render fraud detection page."""
        st.header("⚠️ Fraud & Anomaly Detection")
        
        if self.data is None:
            st.warning("Please wait while data is being loaded...")
            return
        
        # Anomaly summary
        anomaly_summary = self.anomaly_detector.get_anomaly_summary(self.data)
        
        st.subheader("Anomaly Detection Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Properties", anomaly_summary['total_properties'])
            st.metric("Total Anomalies", anomaly_summary['total_anomalies'])
        
        with col2:
            st.metric("Overpriced Properties", anomaly_summary['overpriced_count'])
            st.metric("Underpriced Properties", anomaly_summary['underpriced_count'])
        
        with col3:
            st.metric("Suspicious Listings", anomaly_summary['suspicious_count'])
        
        # Display anomalies
        st.subheader("Detected Anomalies")
        
        anomaly_properties = self.data[self.data['is_any_anomaly'] == True]
        
        if len(anomaly_properties) > 0:
            st.write(f"Found {len(anomaly_properties)} anomalous properties")
            
            # Show sample of anomalies
            st.dataframe(anomaly_properties.head(10)[['location', 'price', 'total_sqft', 'bhk', 
                                                      'overpriced', 'underpriced', 'is_suspicious']])
            
            # Filter options
            filter_type = st.selectbox("Filter by Anomaly Type", 
                                      ['All', 'Overpriced', 'Underpriced', 'Suspicious'])
            
            if filter_type == 'Overpriced':
                filtered = anomaly_properties[anomaly_properties['overpriced'] == True]
            elif filter_type == 'Underpriced':
                filtered = anomaly_properties[anomaly_properties['underpriced'] == True]
            elif filter_type == 'Suspicious':
                filtered = anomaly_properties[anomaly_properties['is_suspicious'] == True]
            else:
                filtered = anomaly_properties
            
            st.dataframe(filtered.head(20))
        else:
            st.info("No anomalies detected in the dataset.")
    
    def render_price_heatmaps(self):
        """Render price heatmaps page."""
        st.header("🗺️ Price Heatmaps")
        
        if self.data is None:
            st.warning("Please wait while data is being loaded...")
            return
        
        # Generate heatmaps
        st.subheader("Interactive Heatmaps")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Generate Price Heatmap"):
                with st.spinner("Generating price heatmap..."):
                    heatmap_path = MODEL_DIR / 'price_heatmap.html'
                    self.heatmap_generator.create_price_heatmap(self.data, str(heatmap_path))
                    st.success("Price heatmap generated!")
        
        with col2:
            if st.button("Generate Investment Heatmap"):
                with st.spinner("Generating investment heatmap..."):
                    heatmap_path = MODEL_DIR / 'investment_heatmap.html'
                    self.heatmap_generator.create_investment_heatmap(self.data, str(heatmap_path))
                    st.success("Investment heatmap generated!")
        
        with col3:
            if st.button("Generate Price Concentration Map"):
                with st.spinner("Generating concentration map..."):
                    heatmap_path = MODEL_DIR / 'price_concentration.html'
                    self.heatmap_generator.create_price_concentration_map(self.data, str(heatmap_path))
                    st.success("Concentration map generated!")
        
        # Display heatmaps
        st.subheader("Heatmap Viewer")
        
        heatmap_type = st.selectbox("Select Heatmap Type", 
                                   ['Price Heatmap', 'Investment Heatmap', 'Price Concentration'])
        
        if heatmap_type == 'Price Heatmap':
            heatmap_path = MODEL_DIR / 'price_heatmap.html'
            if os.path.exists(heatmap_path):
                with open(heatmap_path, 'r') as f:
                    heatmap_html = f.read()
                st.components.v1.html(heatmap_html, height=600)
            else:
                st.info("Please generate the heatmap first.")
        
        elif heatmap_type == 'Investment Heatmap':
            heatmap_path = MODEL_DIR / 'investment_heatmap.html'
            if os.path.exists(heatmap_path):
                with open(heatmap_path, 'r') as f:
                    heatmap_html = f.read()
                st.components.v1.html(heatmap_html, height=600)
            else:
                st.info("Please generate the heatmap first.")
        
        elif heatmap_type == 'Price Concentration':
            heatmap_path = MODEL_DIR / 'price_concentration.html'
            if os.path.exists(heatmap_path):
                with open(heatmap_path, 'r') as f:
                    heatmap_html = f.read()
                st.components.v1.html(heatmap_html, height=600)
            else:
                st.info("Please generate the heatmap first.")
    
    def render_model_performance(self):
        """Render model performance page."""
        st.header("🏆 Model Performance")
        
        if not self.models_loaded:
            st.warning("No trained model is available yet. Run the training pipeline first.")
            return
        
        # Model summary
        model_summary = self.model_trainer.get_model_summary()
        
        st.subheader("Model Comparison")
        
        # Create comparison table
        comparison_data = []
        for model_name, metrics in model_summary['all_models'].items():
            comparison_data.append({
                'Model': model_name,
                'R2 Score': metrics['r2_score'],
                'MAE': metrics['mae'],
                'RMSE': metrics['rmse'],
                'MAPE': metrics['mape'],
                'CV R2 Mean': metrics['cv_r2_mean']
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df)
        
        # Best model
        st.subheader(f"Best Model: {model_summary['best_model']}")
        st.metric("Best R2 Score", f"{model_summary['best_r2_score']:.4f}")
        
        # Feature importance
        st.subheader("Feature Importance")
        if model_summary['feature_importance']:
            best_model_name = model_summary['best_model']
            if best_model_name in model_summary['feature_importance']:
                importance = model_summary['feature_importance'][best_model_name]
                
                importance_df = pd.DataFrame({
                    'Feature': list(importance.keys()),
                    'Importance': list(importance.values())
                }).sort_values('Importance', ascending=True)
                
                fig = px.bar(importance_df, x='Importance', y='Feature', 
                            title=f'Feature Importance - {best_model_name}',
                            orientation='h')
                st.plotly_chart(fig, use_container_width=True)
    
    def render_about(self):
        """Render about page."""
        st.header("ℹ️ About Project")
        
        st.markdown("""
        ### Bangalore Real Estate Intelligence System
        
        A comprehensive AI-powered platform for real estate price prediction and analytics in Bangalore.
        
        #### Features
        
        - **Price Prediction**: AI-powered house price prediction using multiple machine learning models
        - **Location Analytics**: Detailed analytics for different locations in Bangalore
        - **Investment Insights**: Area-wise investment scoring and recommendations
        - **Fraud Detection**: Anomaly detection for suspicious listings
        - **Price Heatmaps**: Interactive visualizations of price distribution
        - **Feature Importance**: SHAP-based explainability for model predictions
        
        #### Technologies Used
        
        - **Machine Learning**: XGBoost, LightGBM, CatBoost, Random Forest
        - **Explainability**: SHAP (SHapley Additive exPlanations)
        - **Visualization**: Plotly, Folium, Streamlit
        - **Data Processing**: Pandas, Scikit-learn
        
        #### Project Structure
        
        ```
        House Price Prediction/
        ├── src/
        │   ├── config.py              # Configuration settings
        │   ├── logging_utils.py       # Logging utilities
        │   ├── preprocessing.py       # Data preprocessing
        │   ├── feature_engineering.py # Feature engineering
        │   ├── anomaly_detection.py   # Anomaly detection
        │   ├── investment_scoring.py  # Investment scoring
        │   ├── heatmap_generator.py   # Heatmap generation
        │   ├── model_training.py      # Model training pipeline
        │   └── explainability.py      # SHAP explainability
        ├── streamlit_app/
        │   └── main.py                # Main Streamlit application
        ├── models/                    # Trained models
        ├── data/                      # Processed data
        └── logs/                      # Application logs
        ```
        
        #### Usage
        
        1. Run the Streamlit application:
           ```bash
           streamlit run streamlit_app/main.py
           ```
        
        2. Navigate through different pages using the sidebar
        
        3. Use the prediction page to get house price estimates
        
        #### Disclaimer
        
        This is an AI-powered prediction system based on historical data. 
        Actual market prices may vary based on various factors.
        """)
        
        # Project team
        st.subheader("Project Team")
        st.markdown("""
        - **AI Engineer**: Model development and pipeline
        - **Data Scientist**: Feature engineering and analysis
        - **ML Architect**: System design and architecture
        """)
        
        # Contact
        st.subheader("Contact")
        st.markdown("""
        For questions or support, please contact the development team.
        """)


if __name__ == "__main__":
    app = RealEstateApp()
    app.run()
