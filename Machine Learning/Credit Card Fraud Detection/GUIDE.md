# Sentinel-ML User Guide 📖

Welcome to the Sentinel-ML Fraud Engine. This guide provides a detailed walkthrough of the dashboard's features and how to effectively use the platform to monitor and detect fraudulent activities.

---

## 1. Upload Dataset & Scanning Animation
**What it is:** The primary entry point for analyzing bulk transaction files.
**How to use:**
- Click the **"Upload Dataset"** button in the header.
- Select a `.csv` file. The system will immediately trigger a **Scanning Animation**.
- This animation represents the real-time processing of your data by the Sentinel-ML engine. As soon as the backend finishes analysis, the animation will fade out and the dashboard will update.

## 2. Executive Dashboard (Overview)
**What it is:** A high-level control center for current data.
- **Stats Cards:** Monitor Total Transactions, Fraud Flags, Model Precision, and Response Time.
- **Fraud Detection Trends:** A real-time **24-hour chart** showing transaction volume (Blue) vs. detected fraud (Red) for every hour of the day.
- **Alert Stream (Top 50):** A table showing the most suspicious transactions from your upload, including their raw probability and risk level.

## 3. Alert Engine (Manual Prediction)
**What it is:** A tool for manually testing specific transaction records.
**How to use:**
- Navigate to the **Alert Engine** tab in the sidebar.
- Input transaction data in the JSON editor (a template is provided).
- Click **"Predict Fraud"** to get an instant result from the live model.

## 4. Analytics (EDA Gallery)
**What it is:** A deep dive into the data patterns found during model training.
**How to use:**
- Navigate to the **Analytics** tab.
- View charts such as Class Distribution, Amount Distribution, and the Correlation Heatmap. 
- These insights help you understand the statistical "landscape" the model was built upon.

## 5. Configurations & Thresholds
**What it is:** Tuning the model's sensitivity.
**How to use:**
- Navigate to the **Configurations** tab.
- **Probability Threshold Slider:** Adjust this to change how aggressive the model is.
    - *Lowering (e.g. 0.3):* Catches more fraud but increases false positives.
    - *Raising (e.g. 0.8):* Decreases false positives but may miss subtle fraud cases.
- **Schema Requirements:** Check the table at the bottom to ensure your CSV files match the required column structure (Time, V1-V28, Amount).

---

## 🛠️ Troubleshooting

- **"Failed to process":** Ensure your CSV contains the `Time` and `Amount` columns.
- **"Model not loaded":** Ensure the backend server was started correctly and can find the `.joblib` files in the `model/` folder.
- **Animation doesn't disappear:** Check the backend console for 500 errors or network timeouts.

---

*For technical support or feature requests, contact the Sentinel-ML Development Team.*
