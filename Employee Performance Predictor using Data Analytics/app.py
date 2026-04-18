import streamlit as st
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import shap

# Page Configuration
st.set_page_config(page_title="Employee Performance Predictor", layout="wide")

# Load Artifacts
@st.cache_resource
def load_artifacts():
    model = joblib.load('model.joblib')
    le_dict = joblib.load('encoder.joblib')
    target_le = joblib.load('target_encoder.joblib')
    scaler = joblib.load('scaler.joblib')
    shap_values = joblib.load('shap_values.joblib')
    return model, le_dict, target_le, scaler, shap_values

model, le_dict, target_le, scaler, shap_values = load_artifacts()

# Titles and Layout
st.title("🚀 Employee Performance Prediction Dashboard")
st.markdown("Analyze and predict employee performance levels using HR data to drive strategic decisions.")

# Sidebar for Inputs
st.sidebar.header("Employee Details")

def get_input_widget(col_name, options=None):
    if options is not None:
        return st.sidebar.selectbox(f"{col_name}", options=options)
    else:
        return st.sidebar.number_input(f"{col_name}", value=0)

# Dynamic Input Generation based on encoders
input_data = {}
# We need the original column names from the dataset to know what to ask
# I'll load the CSV headers to maintain order
df_headers = pd.read_csv('IBM_Employee_Attrition.csv', nrows=0).columns.tolist()
# Remove columns we dropped in preprocessing
cols_to_drop = ['EmployeeCount', 'EmployeeNumber', 'Over18', 'StandardHours', 'PerformanceRating']
feature_cols = [c for c in df_headers if c not in cols_to_drop]

# Separate categorical and numerical
categorical_cols = list(le_dict.keys())
numerical_cols = [c for c in feature_cols if c not in categorical_cols]

# Categorical Inputs
st.sidebar.subheader("Categorical Features")
for col in categorical_cols:
    options = le_dict[col].classes_
    input_data[col] = get_input_widget(col, options=options)

# Numerical Inputs
st.sidebar.subheader("Numerical Features")
for col in numerical_cols:
    input_data[col] = get_input_widget(col)

# Predict Button
if st.sidebar.button("Predict Performance"):
    # Prepare input for model
    input_df = pd.DataFrame([input_data])

    # Ensure column order matches the training set by using the feature_cols list
    input_df = input_df[feature_cols]

    # Encode categorical values
    for col, le in le_dict.items():
        input_df[col] = le.transform(input_df[col])

    # Scale features
    input_scaled = scaler.transform(input_df)

    # Prediction
    prediction = model.predict(input_scaled)
    prediction_idx = int(prediction[0])
    prediction_label = target_le.inverse_transform([prediction_idx])[0]

    # Display Result
    st.subheader("Prediction Result")
    color = "green" if prediction_label == "High" else "orange" if prediction_label == "Medium" else "red"
    st.markdown(f"### The predicted performance level is: <span style='color:{color}'>{prediction_label}</span>", unsafe_allow_html=True)

    # Explain the prediction using SHAP
    st.subheader("Detailed Explanation & Prescriptive Insights")

    # Generate SHAP values for this specific input
    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(input_scaled)

    # SHAP for multi-class returns a list of arrays. We pick the array for the predicted class.
    class_idx = int(prediction_idx)
    current_sv = sv[class_idx][0] if isinstance(sv, list) else sv[0, :, class_idx]

    # Plot SHAP values
    fig, ax = plt.subplots()
    feat_importances = pd.Series(current_sv, index=feature_cols)
    feat_importances.nlargest(10).plot(kind='barh', ax=ax, color='skyblue')
    ax.set_title(f"Top Factors contributing to {prediction_label} Prediction")
    ax.set_xlabel("SHAP Value (Impact on Model Output)")
    st.pyplot(fig)

    # --- Prescriptive Insights Section ---
    st.markdown("### 🎯 Prescriptive Recommendations")
    top_features = feat_importances.nlargest(3).index.tolist()

    recommendations = []
    if prediction_label == "Low":
        recommendations.append("**Training Plan**: Enroll in a specialized skill-up program based on the top missing competencies.")
        recommendations.append("**Mentorship**: Assign a high-performing mentor to improve job satisfaction and role clarity.")
        recommendations.append("**Performance Review**: Schedule bi-weekly syncs to identify specific blockers.")
    elif prediction_label == "Medium":
        recommendations.append("**Growth Opportunity**: Identify a 'stretch project' to push the employee toward 'High' performance.")
        recommendations.append("**Upskilling**: Focus on the top 2 features that are currently dragging down the score.")
    else: # High
        recommendations.append("**Promotion Track**: Evaluate the employee for a leadership or senior-level role.")
        recommendations.append("**Retention Strategy**: Ensure competitive compensation and high-impact projects to prevent attrition.")
        recommendations.append("**Knowledge Sharing**: Encourage them to lead workshops for Medium/Low performers.")

    for rec in recommendations:
        st.write(rec)

    st.info(f"**Why this prediction?** The factors shown in the chart above most heavily influenced the model's decision. For example, {top_features[0]} had the strongest impact.")


# Main Dashboard Content
tab1, tab2 = st.tabs(["Company Analytics", "Prediction Guide"])

with tab1:
    st.header("Global Performance Insights")
    # Load original data for analytics
    df = pd.read_csv('IBM_Employee_Attrition.csv')

    # Synthetic target for analytics (same logic as preprocessing)
    df['PerformanceCategory'] = 'Medium'
    df.loc[df['PerformanceRating'] == 4, 'PerformanceCategory'] = 'High'
    df.loc[(df['PerformanceRating'] == 3) & (df['EnvironmentSatisfaction'] == 1), 'PerformanceCategory'] = 'Low'

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Performance Distribution")
        plt.figure(figsize=(6,4))
        sns.countplot(data=df, x='PerformanceCategory', order=['Low', 'Medium', 'High'], palette='viridis')
        plt.title("Employee Performance Distribution")
        st.pyplot(plt)

    with col2:
        st.subheader("Role vs Performance")
        plt.figure(figsize=(6,4))
        sns.countplot(data=df, x='JobRole', hue='PerformanceCategory', palette='viridis')
        plt.xticks(rotation=45)
        plt.title("Performance by Job Role")
        st.pyplot(plt)

with tab2:
    st.header("How to use this tool")
    st.write("""
    1. **Fill the Sidebar**: Enter the specific details of an employee in the sidebar.
    2. **Predict**: Click the 'Predict Performance' button.
    3. **Analyze**: The dashboard will show the predicted category (High, Medium, Low).
    4. **Interpret**: Review the SHAP plot to understand which features (e.g., Training, Income, Job Level) most heavily influenced the prediction.
    """)
