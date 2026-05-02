import pandas as pd
import numpy as np
import joblib
import json
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
import os

def load_and_clean_data(filepath):
    """Loads the dataset and performs initial cleaning."""
    df = pd.read_csv(filepath)
    
    # 1. Handle TotalCharges (convert to numeric, fix empty strings)
    df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
    # Fill missing TotalCharges with 0 for new customers (tenure=0)
    df['TotalCharges'] = df['TotalCharges'].fillna(0)
    
    # 2. Drop unique identifiers
    df.drop('customerID', axis=1, inplace=True)
    
    return df

def engineer_features(df):
    """Performs feature engineering to improve model performance."""
    # Create Tenure Bins
    df['tenure_group'] = pd.cut(df['tenure'], bins=[0, 12, 24, 48, 60, 100], 
                                labels=['0-1yr', '1-2yr', '2-4yr', '4-5yr', '5yr+'], include_lowest=True)
    
    # Total Services Count (Proxy for customer engagement)
    service_cols = ['OnlineSecurity', 'OnlineBackup', 'DeviceProtection', 
                    'TechSupport', 'StreamingTV', 'StreamingMovies']
    # Explicitly check for 'Yes' to handle potential 'No internet service' strings correctly
    df['TotalServices'] = (df[service_cols] == 'Yes').sum(axis=1)
    
    # Convert Churn to binary
    df['Churn'] = df['Churn'].map({'Yes': 1, 'No': 0})
    
    return df

def train_pipeline(df):
    """Trains the model and saves metrics for both classes to JSON."""
    X = df.drop('Churn', axis=1)
    y = df['Churn']
    
    # Identify column types
    numeric_features = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_features = X.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Define Preprocessing
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])
    
    # ML Engineering: Using class_weight='balanced' to handle the 74/26 imbalance
    # Increasing n_estimators to 100 as a stable default for Random Forest
    model = RandomForestClassifier(
        n_estimators=100, 
        max_depth=10, 
        random_state=42, 
        class_weight='balanced' 
    )
    
    # Final Pipeline (Includes preprocessing + model)
    clf = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', model)
    ])
    
    # Split data (stratified split is preferred for imbalance)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Train
    print("Training the model...")
    clf.fit(X_train, y_train)
    
    # Evaluate
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]
    
    report = classification_report(y_test, y_pred, output_dict=True)
    roc_auc = roc_auc_score(y_test, y_prob)
    
    # Prepare metrics for JSON - explicitly saving both classes
    metrics = {
        "overall_accuracy": report['accuracy'],
        "roc_auc": roc_auc,
        "class_metrics": {
            "no_churn": report['0'],
            "churn": report['1']
        },
        "macro_avg": report['macro avg'],
        "weighted_avg": report['weighted avg']
    }
    
    # Save metrics to JSON
    with open(os.path.join('model', 'model_metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=4)
    print("Classification metrics for both classes saved to 'model_metrics.json'")
    
    return clf

if __name__ == "__main__":
    # 1. Load and Clean
    data_path = 'Telco-Customer-Churn.csv'
    raw_df = load_and_clean_data(data_path)
    
    # 2. Feature Engineering
    processed_df = engineer_features(raw_df)
    
    # 3. Train Model and export metrics
    final_model = train_pipeline(processed_df)
    
    # 4. Save model (Pipeline handles everything)
    os.makedirs('model', exist_ok=True) # Ensure folder exists
    joblib.dump(final_model, os.path.join('model', 'churn_model.joblib'))