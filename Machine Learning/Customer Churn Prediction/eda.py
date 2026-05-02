import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import shap
from sklearn.metrics import precision_recall_curve, roc_curve, auc, confusion_matrix
import os

# Create a directory for assets if it doesn't exist
os.makedirs('eda_assets', exist_ok=True)

def load_and_preprocess_local():
    """Helper to load data and apply minimal cleaning for EDA."""
    df = pd.read_csv('Telco-Customer-Churn.csv')
    df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce').fillna(0)
    return df

def generate_eda_plots(df):
    """Saves standard statistical visualizations with fixed Seaborn syntax."""
    print("Generating EDA plots...")
    sns.set_theme(style="whitegrid")
    
    # 1. Churn Distribution
    # Fixed FutureWaring: Added hue and legend=False
    plt.figure(figsize=(6, 4))
    sns.countplot(x='Churn', data=df, palette='viridis', hue='Churn', legend=False)
    plt.title('Distribution of Customer Churn')
    plt.savefig('eda_assets/churn_distribution.png')
    plt.close()

    # 2. Tenure vs Churn
    plt.figure(figsize=(10, 6))
    sns.kdeplot(data=df, x="tenure", hue="Churn", fill=True, common_norm=False, palette='magma')
    plt.title('Customer Tenure Distribution by Churn Status')
    plt.savefig('eda_assets/tenure_vs_churn.png')
    plt.close()

    # 3. Monthly Charges vs Churn
    # Fixed FutureWaring: Added hue and legend=False
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='Churn', y='MonthlyCharges', data=df, palette='Set2', hue='Churn', legend=False)
    plt.title('Monthly Charges vs Churn')
    plt.savefig('eda_assets/monthly_charges_boxplot.png')
    plt.close()

def plot_model_performance(model, X_test, y_test):
    """Saves Precision-Recall and ROC curves."""
    print("Generating model performance curves...")
    y_score = model.predict_proba(X_test)[:, 1]
    
    # Precision-Recall Curve
    precision, recall, _ = precision_recall_curve(y_test, y_score)
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, color='blue', lw=2)
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve')
    plt.grid(True)
    plt.savefig('eda_assets/precision_recall_curve.png')
    plt.close()

    # ROC Curve
    fpr, tpr, _ = roc_curve(y_test, y_score)
    roc_auc = auc(fpr, tpr)
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC)')
    plt.legend(loc="lower right")
    plt.savefig('eda_assets/roc_curve.png')
    plt.close()

def explain_with_shap(model, X_df):
    """
    Uses SHAP to explain the model features. 
    Since the model is a pipeline, we need to transform the data first to see the 
    actual encoded feature names.
    """
    print("Calculating SHAP values (this may take a moment)...")
    
    # 1. Extract the preprocessor and the classifier from the pipeline
    preprocessor = model.named_steps['preprocessor']
    classifier = model.named_steps['classifier']
    
    # 2. Transform the data to get the numerical/one-hot representation
    X_transformed = preprocessor.transform(X_df)
    
    # 3. Get feature names after transformation
    feature_names = preprocessor.get_feature_names_out()
    
    # 4. Use SHAP TreeExplainer on the Random Forest component
    explainer = shap.TreeExplainer(classifier)
    
    # We use a subset for the summary plot to keep it fast
    sample_size = min(500, X_transformed.shape[0])
    sample_idx = np.random.choice(X_transformed.shape[0], sample_size, replace=False)
    shap_values = explainer.shap_values(X_transformed[sample_idx])
    
    # For binary classification, shap_values is a list of two arrays [prob_no, prob_yes]
    # We care about index 1 (Churn=Yes)
    if isinstance(shap_values, list):
        target_shap_values = shap_values[1]
    else:
        # Handling different SHAP versions
        target_shap_values = shap_values[..., 1] if len(shap_values.shape) > 2 else shap_values

    # Plot SHAP Summary
    plt.figure(figsize=(12, 8))
    shap.summary_plot(target_shap_values, X_transformed[sample_idx], 
                      feature_names=feature_names, show=False)
    plt.title('SHAP Feature Importance (Impact on Churn Probability)')
    plt.tight_layout()
    plt.savefig('eda_assets/shap_summary_plot.png')
    plt.close()

if __name__ == "__main__":
    # Load raw data for EDA
    df = load_and_preprocess_local()
    generate_eda_plots(df)
    
    # Prepare data for model-based analysis
    df['tenure_group'] = pd.cut(df['tenure'], bins=[0, 12, 24, 48, 60, 100], 
                                labels=['0-1yr', '1-2yr', '2-4yr', '4-5yr', '5yr+'], include_lowest=True)
    service_cols = ['OnlineSecurity', 'OnlineBackup', 'DeviceProtection', 
                    'TechSupport', 'StreamingTV', 'StreamingMovies']
    df['TotalServices'] = (df[service_cols] == 'Yes').sum(axis=1)
    df['Churn_Binary'] = df['Churn'].map({'Yes': 1, 'No': 0})
    
    X = df.drop(['customerID', 'Churn', 'Churn_Binary'], axis=1, errors='ignore')
    y = df['Churn_Binary']
    
    # Load the trained model
    try:
        pipeline = joblib.load('churn_model.joblib')
        
        # Performance Curves
        plot_model_performance(pipeline, X, y)
        
        # SHAP Analysis
        explain_with_shap(pipeline, X)
        
        print("\nEDA and Model Interpretation complete. All files saved in 'eda_assets/'.")
    except FileNotFoundError:
        print("Error: 'churn_model.joblib' not found. Please run the training script first.")