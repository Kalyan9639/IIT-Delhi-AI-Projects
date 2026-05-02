import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from imblearn.combine import SMOTETomek
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, average_precision_score, precision_recall_curve, fbeta_score
import joblib

# Ensure Images directory exists
os.makedirs('Images', exist_ok=True)
os.makedirs('backend/model', exist_ok=True)

def analyze_and_train():
    print("Loading dataset...")
    df = pd.read_csv('creditcard.csv')
    
    # 1. Data Cleaning
    print("Checking for null values...")
    null_counts = df.isnull().sum().sum()
    if null_counts > 0:
        print(f"Found {null_counts} null values. Dropping them...")
        df.dropna(inplace=True)
    else:
        print("No null values found.")
        
    # 2. EDA - Class Distribution
    plt.figure(figsize=(8, 6))
    sns.countplot(x='Class', data=df, palette='viridis')
    plt.title('Class Distribution (0: Normal, 1: Fraud)')
    plt.savefig('Images/class_distribution.png')
    plt.close()
    
    # 3. Feature Engineering
    print("Performing feature engineering...")
    # Time is in seconds. Convert to hour of day (0-23)
    df['hour'] = (df['Time'] // 3600) % 24
    # Amount is heavily skewed, let's look at its distribution
    
    # 4. EDA - Amount Distribution
    plt.figure(figsize=(10, 6))
    sns.kdeplot(df[df['Class'] == 0]['Amount'], label='Normal', fill=True)
    sns.kdeplot(df[df['Class'] == 1]['Amount'], label='Fraud', fill=True)
    plt.title('Distribution of Transaction Amount')
    plt.xlim(0, 2000) # Most transactions are in this range
    plt.legend()
    plt.savefig('Images/amount_distribution.png')
    plt.close()

    # 5. EDA - Time (Hour) vs Fraud
    plt.figure(figsize=(12, 6))
    sns.histplot(data=df, x='hour', hue='Class', multiple='stack', bins=24)
    plt.title('Transactions by Hour of Day')
    plt.savefig('Images/hour_distribution.png')
    plt.close()

    # 6. Correlation Heatmap
    plt.figure(figsize=(20, 15))
    sns.heatmap(df.corr(), cmap='coolwarm', annot=False)
    plt.title('Feature Correlation Heatmap')
    plt.savefig('Images/correlation_heatmap.png')
    plt.close()

    # 7. Preprocessing
    print("Preprocessing data...")
    # Scaling Amount and Time
    scaler = StandardScaler()
    df['Amount'] = scaler.fit_transform(df[['Amount']])
    # We'll drop original Time but keep the engineered hour
    X = df.drop(['Class', 'Time'], axis=1)
    y = df['Class']

    # 8. Train-Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # 9. Handle Imbalance (Class Weights)
    print("Handling class imbalance using class weights (scale_pos_weight)...")
    scale_pos_weight = y_train.value_counts()[0] / y_train.value_counts()[1]
    print(f"Calculated scale_pos_weight: {scale_pos_weight:.2f}")

    # 10. Model Training (XGBoost)
    print("Training XGBoost model...")
    model = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        use_label_encoder=False,
        eval_metric='logloss',
        scale_pos_weight=scale_pos_weight
    )
    # Using the original X_train, y_train with class weights
    model.fit(X_train, y_train)

    # 11. Evaluation
    print("Evaluating model...")
    y_pred = model.predict(X_test)
    y_probs = model.predict_proba(X_test)[:, 1]
    
    print("\nClassification Report:")
    report = classification_report(y_test, y_pred, output_dict=True)
    print(classification_report(y_test, y_pred))
    
    auprc = average_precision_score(y_test, y_probs)
    print(f"AUPRC: {auprc:.4f}")
    
    f2 = fbeta_score(y_test, y_pred, beta=2)
    print(f"F2-Score: {f2:.4f}")
    
    from sklearn.metrics import roc_auc_score
    roc_auc = roc_auc_score(y_test, y_probs)
    print(f"ROC-AUC: {roc_auc:.4f}")
    
    import json
    metrics = {
        "classification_report": report,
        "AUPRC": auprc,
        "F2-Score": f2,
        "ROC-AUC": roc_auc
    }
    with open('metrics.json', 'w') as f:
        json.dump(metrics, f, indent=4)
    print("Metrics saved to metrics.json")

    # Precision-Recall Curve Plot
    precision, recall, thresholds = precision_recall_curve(y_test, y_probs)
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, label=f'AUPRC = {auprc:.4f}')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve')
    plt.legend()
    plt.savefig('Images/precision_recall_curve.png')
    plt.close()

    # 12. Save Model and Scaler
    print("Saving model and scaler...")
    joblib.dump(model, 'backend/model/model.joblib')
    joblib.dump(scaler, 'backend/model/scaler.joblib')
    # Save feature names for inference
    joblib.dump(X.columns.tolist(), 'backend/model/features.joblib')
    print("Done!")

if __name__ == "__main__":
    analyze_and_train()
