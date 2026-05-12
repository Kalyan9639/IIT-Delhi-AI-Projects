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

# Feature descriptions dictionary
feature_descriptions = {
    'Age': 'Employee age in years. Younger employees may show different performance patterns compared to experienced ones.',
    'Attrition': 'Whether the employee has left the company (Yes/No). Indicates employee retention.',
    'DailyRate': 'Daily wage rate in dollars. Reflects compensation structure for the employee.',
    'Department': 'Department where the employee works (e.g., HR, IT, Sales). Different departments may have varying performance metrics.',
    'DistanceFromHome': 'Distance from home to workplace in miles. Commute distance may affect work-life balance and performance.',
    'Education': 'Level of formal education achieved (1=Below College, 2=College, 3=Bachelor, 4=Master, 5=Doctor).',
    'EducationField': 'Field of study for the employee. Technical background may correlate with performance in technical roles.',
    'EnvironmentSatisfaction': 'Satisfaction level with work environment (1=Low, 2=Medium, 3=High, 4=Very High). Highly influences performance.',
    'Gender': 'Employee gender (Male/Female). Used as a demographic feature.',
    'HourlyRate': 'Hourly wage rate in dollars. Reflects compensation structure.',
    'JobInvolvement': 'Level of job involvement (1=Low, 2=Medium, 3=High, 4=Very High). Strong indicator of performance.',
    'JobLevel': 'Job level/seniority (1-5). Higher levels typically have different performance expectations.',
    'JobRole': 'Specific job role (e.g., Manager, Developer, Analyst). Different roles have different performance criteria.',
    'JobSatisfaction': 'Satisfaction with the job itself (1=Low, 2=Medium, 3=High, 4=Very High). Directly impacts performance.',
    'MaritalStatus': 'Marital status (Single/Married/Divorced). May correlate with stability and performance.',
    'MonthlyIncome': 'Monthly salary in dollars. Higher income may indicate seniority and capability.',
    'MonthlyRate': 'Monthly rate in dollars. Part of compensation structure.',
    'NumCompaniesWorked': 'Number of companies where the employee has worked. Indicates career stability.',
    'OverTime': 'Whether the employee works overtime (Yes/No). Indicates workload and commitment.',
    'PercentSalaryHike': 'Percentage salary increase in recent review. Reflects past performance recognition.',
    'PerformanceRating': 'Previous performance rating. Strong predictor of future performance.',
    'RelationshipSatisfaction': 'Satisfaction with relationships at work (1=Low, 2=Medium, 3=High, 4=Very High).',
    'StockOptionLevel': 'Level of stock options granted (0-3). Indicates company confidence in the employee.',
    'TotalWorkingYears': 'Total years of work experience. More experience often correlates with better performance.',
    'TrainingTimesLastYear': 'Number of training programs attended in the last year. Indicates investment in skill development.',
    'WorkLifeBalance': 'Work-life balance satisfaction (1=Bad, 2=Good, 3=Better, 4=Best). Affects overall performance.',
    'YearsAtCompany': 'Number of years employed at current company. Tenure affects familiarity and performance.',
    'YearsInCurrentRole': 'Years in current role. Time to master the role impacts performance.',
    'YearsSinceLastPromotion': 'Years since last promotion. May indicate stagnation or steady progression.',
}

# Main Dashboard Content with tabs
tab1, tab2, tab3 = st.tabs(["Company Analytics", "Prediction", "Prediction Guide"])

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
    st.header("Employee Performance Prediction")
    st.markdown("Enter employee details below to predict their performance level.")
    
    # Categorical Inputs
    st.subheader("Categorical Features")
    for col in categorical_cols:
        options = le_dict[col].classes_
        input_data[col] = st.selectbox(f"{col}", options=options)
    
    # Numerical Inputs with sliders
    st.subheader("Numerical Features")
    for col in numerical_cols:
        min_val = 0
        max_val = 100
        default_val = 50
        input_data[col] = st.slider(f"{col}", min_value=min_val, max_value=max_val, value=default_val)
    
    # Predict Button
    if st.button("Predict Performance"):
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

        # --- Prescriptive Insights Section (without SHAP plot) ---
        st.markdown("### 🎯 Prescriptive Recommendations")
        feat_importances = pd.Series(current_sv, index=feature_cols)
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

        st.info(f"**Why this prediction?** The top contributing factors are: {', '.join(top_features)}.")

with tab3:
    st.header("📖 Prediction Guide - Feature Descriptions")
    st.markdown("Learn about each input feature and how it influences employee performance prediction.")
    
    # Create tabs for categorical and numerical features
    guide_tab1, guide_tab2 = st.tabs(["Categorical Features", "Numerical Features"])
    
    with guide_tab1:
        st.subheader("Categorical Features")
        st.markdown("These are features that represent categories or groups:")
        
        categorical_info = {}
        for col in categorical_cols:
            if col in feature_descriptions:
                categorical_info[col] = feature_descriptions[col]
        
        for feature, description in categorical_info.items():
            with st.expander(f"📌 {feature}"):
                st.write(description)
                if feature in le_dict:
                    options = le_dict[feature].classes_
                    st.write(f"**Possible values:** {', '.join(options)}")
    
    with guide_tab2:
        st.subheader("Numerical Features")
        st.markdown("These are features that represent numerical values:")
        
        numerical_info = {}
        for col in numerical_cols:
            if col in feature_descriptions:
                numerical_info[col] = feature_descriptions[col]
        
        for feature, description in numerical_info.items():
            with st.expander(f"📊 {feature}"):
                st.write(description)
                st.write("**Input type:** Slider (0-100)")
    
    st.markdown("---")
    st.markdown("### 💡 How to Use This Guide")
    st.write("""
    1. **Categorical Features Tab**: Explore features like Department, Job Role, and Marital Status. These have predefined categories you'll select from.
    2. **Numerical Features Tab**: Learn about features like Age, Monthly Income, and Years at Company. These are entered using sliders.
    3. **Understanding Impact**: Features like Job Satisfaction, Environment Satisfaction, and Job Involvement tend to have high impact on performance predictions.
    4. **Tips for Better Predictions**: 
       - Be accurate with employee data
       - Consider recent changes in the employee's circumstances
       - Use actual values from HR records
    """)
