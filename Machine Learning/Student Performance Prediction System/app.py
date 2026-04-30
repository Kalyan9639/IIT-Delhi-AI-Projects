import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Load the trained model
MODEL_PATH = 'student_model.joblib'
model = joblib.load(MODEL_PATH)

# Load train data for EDA
TRAIN_CSV = 'data/train_input.csv'
df = pd.read_csv(TRAIN_CSV)

# Feature engineering function (same as in notebook)
def add_combined_features(df):
    df = df.copy()
    df['Extracurricular_bin'] = df['Extracurricular Activities'].map({'Yes':1, 'No':0})
    df['Study_Effort'] = df['Hours Studied'] * (df['Sample Question Papers Practiced'] + 1)
    df['Prev_norm'] = (df['Previous Scores'] - df['Previous Scores'].min()) / (df['Previous Scores'].max() - df['Previous Scores'].min())
    df['Pract_norm'] = (df['Sample Question Papers Practiced'] - df['Sample Question Papers Practiced'].min()) / (df['Sample Question Papers Practiced'].max() - df['Sample Question Papers Practiced'].min())
    df['Academic_Backup'] = 0.7 * df['Prev_norm'] + 0.3 * df['Pract_norm']
    for col in ['Prev_norm','Pract_norm']:
        if col in df.columns: df.drop(columns=[col], inplace=True)
    return df

df = add_combined_features(df)

# Features list
FEATURES = ['Hours Studied', 'Previous Scores', 'Sleep Hours', 'Sample Question Papers Practiced', 'Extracurricular_bin', 'Study_Effort', 'Academic_Backup']

# Streamlit app
st.title("Student Performance Prediction System")

# Sidebar for navigation
page = st.sidebar.selectbox("Choose a page", ["EDA", "Prediction"])

if page == "EDA":
    st.header("Exploratory Data Analysis")

    # Basic stats
    st.subheader("Dataset Overview")
    st.write(f"Shape: {df.shape}")
    st.write(df.describe())

    # Histograms
    st.subheader("Feature Distributions")
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    for i, col in enumerate(FEATURES + ['Performance Index']):
        ax = axes.flat[i]
        sns.histplot(df[col], ax=ax, kde=True)
        ax.set_title(col)
    plt.tight_layout()
    st.pyplot(fig)

    # Convert categorical to numeric for correlation
    if 'Extracurricular Activities' in df.columns:
        df['Extracurricular Activities'] = df['Extracurricular Activities'].map({'Yes': 1, 'No': 0})
    # Correlation heatmap
    st.subheader("Correlation Heatmap")
    corr = df.corr()
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap='coolwarm', ax=ax)
    st.pyplot(fig)

    # Scatter plots for key features
    st.subheader("Key Feature Relationships")
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    sns.scatterplot(data=df, x='Previous Scores', y='Performance Index', ax=axes[0])
    axes[0].set_title('Previous Scores vs Performance Index')
    sns.scatterplot(data=df, x='Hours Studied', y='Performance Index', ax=axes[1])
    axes[1].set_title('Hours Studied vs Performance Index')
    sns.scatterplot(data=df, x='Study_Effort', y='Performance Index', ax=axes[2])
    axes[2].set_title('Study Effort vs Performance Index')
    plt.tight_layout()
    st.pyplot(fig)

elif page == "Prediction":
    st.header("Predict Student Performance")

    # Input widgets
    hours_studied = st.slider("Hours Studied", 1, 9, 5)
    previous_scores = st.slider("Previous Scores", 40, 100, 70)
    sleep_hours = st.slider("Sleep Hours", 4, 10, 7)
    sample_papers = st.slider("Sample Question Papers Practiced", 0, 9, 3)
    extracurricular = st.selectbox("Extracurricular Activities", ["Yes", "No"])
    extracurricular_bin = 1 if extracurricular == "Yes" else 0

    # Calculate combined features
    study_effort = hours_studied * (sample_papers + 1)
    prev_norm = (previous_scores - df['Previous Scores'].min()) / (df['Previous Scores'].max() - df['Previous Scores'].min())
    pract_norm = (sample_papers - df['Sample Question Papers Practiced'].min()) / (df['Sample Question Papers Practiced'].max() - df['Sample Question Papers Practiced'].min())
    academic_backup = 0.7 * prev_norm + 0.3 * pract_norm

    # Prepare input
    input_data = pd.DataFrame({
        'Hours Studied': [hours_studied],
        'Previous Scores': [previous_scores],
        'Sleep Hours': [sleep_hours],
        'Sample Question Papers Practiced': [sample_papers],
        'Extracurricular_bin': [extracurricular_bin],
        'Study_Effort': [study_effort],
        'Academic_Backup': [academic_backup]
    })

    # Predict
    if st.button("Predict Performance Index"):
        prediction = model.predict(input_data)[0]
        st.success(f"Predicted Performance Index: {prediction:.2f}")

        # Show input summary
        st.subheader("Input Summary")
        st.write(input_data.T)
    prev_norm = (previous_scores - df['Previous Scores'].min()) / (df['Previous Scores'].max() - df['Previous Scores'].min())
    pract_norm = (sample_papers - df['Sample Question Papers Practiced'].min()) / (df['Sample Question Papers Practiced'].max() - df['Sample Question Papers Practiced'].min())
    academic_backup = 0.7 * prev_norm + 0.3 * pract_norm
    
    # Prepare input for model
    input_data = pd.DataFrame({
        'Hours Studied': [hours_studied],
        'Previous Scores': [previous_scores],
        'Sleep Hours': [sleep_hours],
        'Sample Question Papers Practiced': [sample_papers],
        'Extracurricular_bin': [extracurricular_bin],
        'Study_Effort': [study_effort],
        'Academic_Backup': [academic_backup]
    })
    
    if st.button("Predict"):
        prediction = model.predict(input_data)[0]
        st.success(f"Predicted Performance Index: {prediction:.2f}")
        
        # Interpretation
        if prediction >= 80:
            st.write("Excellent performance! Keep it up.")
        elif prediction >= 60:
            st.write("Good performance. Room for improvement.")
        else:
            st.write("Needs improvement. Focus on study habits.")

elif page == "EDA":
    st.header("Exploratory Data Analysis")
    
    # Summary stats
    st.subheader("Data Summary")
    st.write(df.describe())
    
    # Correlation heatmap
    st.subheader("Correlation Heatmap")
    corr = df[['Hours Studied', 'Previous Scores', 'Sleep Hours', 'Sample Question Papers Practiced', 'Extracurricular_bin', 'Study_Effort', 'Academic_Backup', 'Performance Index']].corr()
    fig, ax = plt.subplots()
    sns.heatmap(corr, annot=True, ax=ax)
    st.pyplot(fig)
    
    # Distribution of target
    st.subheader("Distribution of Performance Index")
    fig, ax = plt.subplots()
    sns.histplot(df['Performance Index'], kde=True, ax=ax)
    st.pyplot(fig)
    
    # Feature importance (from model)
    st.subheader("Feature Importance")
    if hasattr(model.named_steps['rf'], 'feature_importances_'):
        importances = model.named_steps['rf'].feature_importances_
        feature_imp = pd.Series(importances, index=FEATURES).sort_values(ascending=False)
        fig, ax = plt.subplots()
        feature_imp.plot(kind='bar', ax=ax)
        st.pyplot(fig)
    
    # Scatter plot: Hours Studied vs Performance Index
    st.subheader("Hours Studied vs Performance Index")
    fig, ax = plt.subplots()
    sns.scatterplot(data=df, x='Hours Studied', y='Performance Index', ax=ax)
    st.pyplot(fig)

    # Box plot: Extracurricular vs Performance Index
    st.subheader("Extracurricular Activities vs Performance Index")
    fig, ax = plt.subplots()
    sns.boxplot(data=df, x='Extracurricular Activities', y='Performance Index', ax=ax)
    st.pyplot(fig)

# Footer
st.sidebar.markdown("---")
st.sidebar.write("Built with Streamlit")
st.sidebar.write("Model: Random Forest Regressor")