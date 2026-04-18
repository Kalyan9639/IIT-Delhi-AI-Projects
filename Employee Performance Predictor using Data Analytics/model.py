import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import shap
import matplotlib.pyplot as plt

def train_model():
    # Load data splits
    X_train, X_test, y_train, y_test = joblib.load('data_splits.joblib')

    # We use XGBClassifier for high performance and interpretability
    model = XGBClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=6,
        objective='multi:softprob',
        random_state=42,
        use_label_encoder=False,
        eval_metric='mlogloss'
    )

    model.fit(X_train, y_train)

    # Evaluation
    y_pred = model.predict(X_test)
    print("\nModel Accuracy:", accuracy_score(y_test, y_pred))
    print("\nClassification Report:\n", classification_report(y_test, y_pred))

    # Save the model
    joblib.dump(model, 'model.joblib')
    print("\nModel saved as model.joblib")

    # Generate SHAP values for global feature importance
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)

    # Save SHAP values and explainer for the dashboard
    # Since shap objects are complex, we save the shap_values (numpy array)
    joblib.dump(shap_values, 'shap_values.joblib')

    return model, X_test, y_test

if __name__ == "__main__":
    train_model()
